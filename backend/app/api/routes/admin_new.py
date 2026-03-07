"""
Admin Dashboard API Endpoints
4 Modules: User Management, Product Catalogue, ML Training, Auto Sync/Scraping
"""

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Query, status
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import List, Optional
from datetime import datetime, timedelta
from bson import ObjectId
import pandas as pd
import io
import asyncio
import httpx

from app.dependencies.auth import get_current_user
from app.core.database import (
    get_users_collection,
    get_products_collection,
    get_scraping_history_collection,
    get_db
)
from app.services.scraper_service import scrape_from_excel_files
from app.services.category_normalizer import normalize_category, get_category_display_name
from app.models.admin import AdminLogin, AdminToken, AdminResponse
from app.core.security import verify_password
from app.utils.auth import create_access_token
import os
import logging
import hashlib
from pathlib import Path
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

# Directory for downloaded product images (served at /data/product_images/)
def _get_product_images_dir():
    base = Path(__file__).resolve().parent.parent.parent.parent.parent  # routes -> api -> app -> backend -> project root
    d = base / "data" / "product_images"
    d.mkdir(parents=True, exist_ok=True)
    return d

def _looks_like_image_url(url: str) -> bool:
    """Reject malformed URLs (e.g. junaidjamshed.com/mens/255&fit=bounds) that are not real image URLs."""
    if not url:
        return False
    ul = url.lower()
    if any(x in ul for x in ["loader", "lazyload", "placeholder.com"]):
        return False
    # Real image URLs usually have extension or path segment
    path_part = ul.split("?")[0]
    if any(ext in path_part for ext in [".jpg", ".jpeg", ".png", ".webp", ".gif"]):
        return True
    if any(seg in path_part for seg in [
        "/media/", "/cdn/", "/files/", "/upload", "/product/", "/shop/files/", "/uploads/",
        "/catalog/", "/img/", "/images/", "/assets/", "/static/",
        "/mens/", "/women/", "/womens/"  # e.g. Junaid Jamshed /mens/255&fit=bounds
    ]):
        return True
    return False


async def _download_product_image(image_url: str, product_url: str) -> Optional[str]:
    """Download image from URL and save to data/product_images. Returns relative path like 'product_images/xxx.jpg' or None. Skips if file already exists."""
    if not image_url or not image_url.strip().lower().startswith(("http://", "https://")):
        return None
    if not _looks_like_image_url(image_url):
        return None
    url_lower = image_url.lower()
    if "loader" in url_lower or "lazyload" in url_lower or image_url.rstrip("/").endswith(".gif"):
        return None
    img_dir = _get_product_images_dir()
    # Try common extensions for "already exists" check (we don't know ext before download)
    base_name = hashlib.md5(((product_url or "") + (image_url or "")).encode("utf-8")).hexdigest()[:16]
    for ext in (".jpg", ".jpeg", ".png", ".webp", ".gif"):
        if (img_dir / (base_name + ext)).exists():
            return f"product_images/{base_name}{ext}"
    try:
        parsed = urlparse(image_url)
        origin = f"{parsed.scheme}://{parsed.netloc}"
        async with httpx.AsyncClient(timeout=12.0, follow_redirects=True) as client:
            r = await client.get(
                image_url,
                headers={
                    "Referer": origin + "/",
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; rv:109.0) Gecko/20100101 Firefox/115.0",
                    "Accept": "image/webp,image/apng,image/*,*/*;q=0.8",
                },
            )
            r.raise_for_status()
            ct = r.headers.get("content-type", "").split(";")[0].strip().lower()
            if "image" not in ct:
                return None
            ext = ".jpg"
            if "png" in ct:
                ext = ".png"
            elif "webp" in ct:
                ext = ".webp"
            elif "gif" in ct and len(r.content) > 500:
                ext = ".gif"
            name = base_name + ext
            path = img_dir / name
            path.write_bytes(r.content)
            return f"product_images/{name}"
    except Exception as e:
        logger.debug(f"Could not download product image: {e}")
        return None

router = APIRouter(tags=["Admin Dashboard"])


# ============================================
# Admin Authentication
# ============================================

@router.post("/login", response_model=AdminToken)
async def admin_login(credentials: AdminLogin):
    """
    Admin login endpoint
    
    - **email**: Admin email address
    - **password**: Admin password
    
    **Default Admin Credentials:**
    - Email: admin@dupefinder.com
    - Password: admin123
    """
    try:
        db = get_db()
        if db is None:
            logger.error("Database connection is None")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database connection error"
            )
        
        admins_collection = db.admins
        
        # Find admin
        admin = admins_collection.find_one({"email": credentials.email})
        
        if not admin:
            logger.warning(f"Admin not found: {credentials.email}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid admin credentials"
            )
        
        # Verify password using verify_password from security
        try:
            password_valid = verify_password(credentials.password, admin["hashed_password"])
        except Exception as e:
            logger.error(f"Password verification error: {e}, type: {type(admin.get('hashed_password'))}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error verifying password: {str(e)}"
            )
        
        if not password_valid:
            logger.warning(f"Invalid password for admin: {credentials.email}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid admin credentials"
            )
        
        # Create access token
        access_token = create_access_token(data={"sub": credentials.email, "role": "admin"})
        
        # Prepare admin response
        admin["_id"] = str(admin["_id"])
        if "hashed_password" in admin:
            del admin["hashed_password"]
        
        return AdminToken(
            access_token=access_token,
            admin=AdminResponse(**admin)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in admin_login: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


# ============================================
# Helper: Check if user is admin
# ============================================

async def require_admin(
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer())
):
    """
    Dependency to ensure user is an admin
    Verifies admin token and returns admin data
    """
    from app.utils.auth import verify_token
    from app.core.database import get_db
    import logging
    
    logger = logging.getLogger(__name__)
    
    token = credentials.credentials
    
    # Verify token
    payload = verify_token(token, token_type="access")
    
    if not payload:
        logger.warning(f"Token verification failed for token: {token[:20]}...")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if it's an admin token (has role="admin" or sub field)
    email = payload.get("sub") or payload.get("email")
    role = payload.get("role")
    
    logger.info(f"Token payload - email: {email}, role: {role}, keys: {list(payload.keys())}")
    
    # If it has role="admin", it's an admin token
    if role == "admin" and email:
        # Get admin from admins collection
        db = get_db()
        admin = db.admins.find_one({"email": email})
        
        if not admin:
            logger.warning(f"Admin not found in database for email: {email}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Admin not found",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        admin["_id"] = str(admin["_id"])
        logger.info(f"Admin authenticated: {email}")
        return admin
    
    # If it has user_id, try to get user and check if admin
    user_id = payload.get("user_id")
    if user_id:
        # This is a regular user token - check if they're an admin
        # For now, we'll only allow admin tokens
        logger.warning(f"Regular user token used for admin endpoint: {user_id}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required. Please login as admin.",
        )
    
    logger.warning(f"Token missing required fields - email: {email}, role: {role}")
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=f"Invalid admin token. Token payload: {list(payload.keys())}",
        headers={"WWW-Authenticate": "Bearer"},
    )


# ============================================
# MODULE 1: User Management
# ============================================

@router.get("/users")
async def get_all_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    status_filter: Optional[str] = None,  # 'active', 'inactive', 'all'
    admin: dict = Depends(require_admin)
):
    """
    Get all registered users with pagination and filtering
    
    Module 1: User Management - View login data
    """
    users = get_users_collection()
    
    # Build query - only show verified users
    query = {"is_verified": True}
    if search:
        query["email"] = {"$regex": search, "$options": "i"}
    
    if status_filter == "active":
        query["is_active"] = True
    elif status_filter == "inactive":
        query["is_active"] = False
    
    # Get total count
    total = users.count_documents(query)
    
    # Get paginated users
    skip = (page - 1) * page_size
    user_list = list(
        users.find(query, {"password_hash": 0})  # Exclude password
        .skip(skip)
        .limit(page_size)
        .sort("created_at", -1)
    )
    
    # Format response
    for user in user_list:
        user["_id"] = str(user["_id"])
    
    return {
        "users": user_list,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size
    }


@router.put("/users/{user_id}/deactivate")
async def deactivate_user(
    user_id: str,
    admin: dict = Depends(require_admin)
):
    """
    Deactivate a user account permanently
    
    Module 1: User Management - Deactivate accounts
    """
    users = get_users_collection()
    
    if not ObjectId.is_valid(user_id):
        raise HTTPException(status_code=400, detail="Invalid user ID")
    
    result = users.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {"is_active": False, "deactivated_at": datetime.utcnow()}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {
        "success": True,
        "message": "User deactivated successfully",
        "user_id": user_id
    }


@router.put("/users/{user_id}/activate")
async def activate_user(
    user_id: str,
    admin: dict = Depends(require_admin)
):
    """
    Reactivate a user account
    
    Module 1: User Management
    """
    users = get_users_collection()
    
    if not ObjectId.is_valid(user_id):
        raise HTTPException(status_code=400, detail="Invalid user ID")
    
    result = users.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {"is_active": True}, "$unset": {"deactivated_at": ""}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {
        "success": True,
        "message": "User activated successfully",
        "user_id": user_id
    }


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: str,
    admin: dict = Depends(require_admin)
):
    """
    Delete a user permanently
    
    Module 1: User Management - Delete user accounts
    """
    users = get_users_collection()
    
    if not ObjectId.is_valid(user_id):
        raise HTTPException(status_code=400, detail="Invalid user ID")
    
    result = users.delete_one({"_id": ObjectId(user_id)})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {
        "success": True,
        "message": "User deleted successfully",
        "user_id": user_id
    }


# ============================================
# MODULE 2: Product Catalogue Management
# ============================================

@router.post("/products/import-csv")
async def import_products_from_csv(
    file: UploadFile = File(...),
    admin: dict = Depends(require_admin)
):
    """
    Import products from CSV file
    
    Module 2: Product Catalogue - Add products via CSV
    
    CSV Format: name, category, brand, price, image_url, description
    """
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="File must be a CSV")
    
    try:
        # Read CSV file
        contents = await file.read()
        df = pd.read_csv(io.StringIO(contents.decode('utf-8')))
        
        # Normalize column names: lowercase and strip whitespace
        df.columns = df.columns.str.strip().str.lower()
        
        # Remove completely empty rows
        df = df.dropna(how='all')
        
        logger.info(f"Processing {len(df)} rows from CSV")
        logger.info(f"CSV columns (normalized): {list(df.columns)}")
        if len(df) > 0:
            logger.info(f"First row sample: {df.iloc[0].to_dict()}")
        
        # Validate required columns (case-insensitive)
        required_cols = ['name', 'category', 'brand', 'price']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            raise HTTPException(
                status_code=400,
                detail=f"Missing required columns: {', '.join(missing_cols)}. Found columns: {', '.join(df.columns)}"
            )
        
        if len(df) == 0:
            raise HTTPException(
                status_code=400,
                detail="CSV file is empty or contains no valid data rows"
            )
        
        # Process products
        products = get_products_collection()
        success_count = 0
        error_count = 0
        errors = []
        
        for idx, row in df.iterrows():
            try:
                # Clean and validate data - handle NaN values properly
                name = None
                category = None
                brand = None
                
                # Extract name
                if 'name' in row and pd.notna(row['name']):
                    name = str(row['name']).strip()
                elif 'product_name' in row and pd.notna(row.get('product_name')):
                    name = str(row['product_name']).strip()
                elif 'product' in row and pd.notna(row.get('product')):
                    name = str(row['product']).strip()
                
                # Extract category
                if 'category' in row and pd.notna(row['category']):
                    category = str(row['category']).strip()
                elif 'cat' in row and pd.notna(row.get('cat')):
                    category = str(row['cat']).strip()
                
                # Extract brand
                if 'brand' in row and pd.notna(row['brand']):
                    brand = str(row['brand']).strip()
                elif 'brand_name' in row and pd.notna(row.get('brand_name')):
                    brand = str(row['brand_name']).strip()
                
                # Validate required fields with detailed error messages
                if not name or name == 'None' or name == '' or name == 'nan':
                    raise ValueError(f"Name is required and cannot be empty. Got: '{row.get('name', 'N/A')}'")
                if not category or category == 'None' or category == '' or category == 'nan':
                    raise ValueError(f"Category is required and cannot be empty. Got: '{row.get('category', 'N/A')}'")
                if not brand or brand == 'None' or brand == '' or brand == 'nan':
                    raise ValueError(f"Brand is required and cannot be empty. Got: '{row.get('brand', 'N/A')}'")
                
                # Handle price conversion with better error handling
                price = 0.0
                price_value = row.get('price', 0)
                if pd.notna(price_value):
                    try:
                        # Remove currency symbols and commas
                        price_str = str(price_value).replace('$', '').replace(',', '').strip()
                        price = float(price_str)
                        if price < 0:
                            price = 0.0
                    except (ValueError, TypeError) as e:
                        logger.warning(f"Row {idx + 2}: Invalid price '{price_value}', using 0.0")
                        price = 0.0
                else:
                    logger.warning(f"Row {idx + 2}: Price is missing, using 0.0")
                
                # Handle optional fields
                image_url = ''
                if 'image_url' in row and pd.notna(row.get('image_url')):
                    image_url = str(row['image_url']).strip()
                elif 'image' in row and pd.notna(row.get('image')):
                    image_url = str(row['image']).strip()
                elif 'image_path' in row and pd.notna(row.get('image_path')):
                    image_url = str(row['image_path']).strip()
                
                description = ''
                if 'description' in row and pd.notna(row.get('description')):
                    description = str(row['description']).strip()
                elif 'desc' in row and pd.notna(row.get('desc')):
                    description = str(row['desc']).strip()
                
                # Generate product_id if not present (for uniqueness)
                import hashlib
                product_id_source = f"{name}_{brand}_{category}"
                product_id = hashlib.md5(product_id_source.encode()).hexdigest()
                
                product_doc = {
                    "product_id": product_id,
                    "name": name,
                    "category": category,
                    "brand": brand,
                    "price": price,
                    "image_url": image_url,
                    "image_path": image_url,  # Keep both for compatibility
                    "description": description,
                    "embedding": [],  # Will be computed later
                    "created_at": datetime.utcnow(),
                    "created_by": "admin_csv_import",
                    "broken_link": False,
                    "scraped_at": datetime.utcnow()
                }
                
                # Check if product already exists (by product_id or name+brand combination)
                existing = products.find_one({
                    "$or": [
                        {"product_id": product_id},
                        {"name": name, "brand": brand}
                    ]
                })
                
                if existing:
                    # Update existing product
                    products.update_one(
                        {"_id": existing["_id"]},
                        {"$set": product_doc}
                    )
                    logger.info(f"Row {idx + 2}: Updated existing product: {name}")
                else:
                    # Insert new product
                    products.insert_one(product_doc)
                    logger.info(f"Row {idx + 2}: Inserted new product: {name}")
                
                success_count += 1
                
            except Exception as e:
                error_count += 1
                error_msg = f"Row {idx + 2}: {str(e)}"
                errors.append(error_msg)
                logger.error(f"CSV import error - {error_msg}")
                logger.error(f"Row {idx + 2} data: {row.to_dict()}")
                # Log the actual values for debugging
                logger.error(f"Row {idx + 2} raw values - name: '{row.get('name', 'N/A')}', category: '{row.get('category', 'N/A')}', brand: '{row.get('brand', 'N/A')}', price: '{row.get('price', 'N/A')}'")
        
        result = {
            "success": True,
            "message": f"Import completed",
            "total_rows": len(df),
            "imported": success_count,
            "failed": error_count,
            "errors": errors[:20]  # Return first 20 errors for better debugging
        }
        
        logger.info(f"CSV import result: {result}")
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process CSV: {str(e)}")


@router.post("/products/cleanup-links")
async def cleanup_broken_links(
    admin: dict = Depends(require_admin)
):
    """
    Check all product image URLs and mark broken links
    
    Module 2: Product Catalogue - Cleanup missing links
    """
    products = get_products_collection()
    
    # Get all products with image URLs
    product_list = list(products.find({"image_path": {"$ne": ""}}))
    
    checked = 0
    broken = 0
    broken_ids = []
    
    async with httpx.AsyncClient(timeout=5.0) as client:
        for product in product_list:
            image_url = product.get("image_path", "")
            if not image_url:
                continue
            
            checked += 1
            
            try:
                # Skip local file paths
                if not image_url.startswith('http'):
                    continue
                
                response = await client.head(image_url)
                if response.status_code >= 400:
                    # Mark as broken
                    products.update_one(
                        {"_id": product["_id"]},
                        {"$set": {"broken_link": True}}
                    )
                    broken += 1
                    broken_ids.append(str(product["_id"]))
                else:
                    # Mark as working
                    products.update_one(
                        {"_id": product["_id"]},
                        {"$set": {"broken_link": False}}
                    )
                    
            except Exception as e:
                # Connection error - mark as broken
                products.update_one(
                    {"_id": product["_id"]},
                    {"$set": {"broken_link": True}}
                )
                broken += 1
                broken_ids.append(str(product["_id"]))
    
    return {
        "success": True,
        "checked": checked,
        "broken": broken,
        "working": checked - broken,
        "broken_ids": broken_ids
    }


@router.post("/products/{product_id}/repair-link")
async def repair_broken_link(
    product_id: str,
    admin: dict = Depends(require_admin)
):
    """
    Repair a broken image link by re-checking it
    
    Module 2: Product Catalogue - Repair broken links
    """
    products = get_products_collection()
    
    if not ObjectId.is_valid(product_id):
        raise HTTPException(status_code=400, detail="Invalid product ID")
    
    product = products.find_one({"_id": ObjectId(product_id)})
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    image_url = product.get("image_url") or product.get("image_path", "")
    
    if not image_url:
        raise HTTPException(status_code=400, detail="Product has no image URL")
    
    # Re-check the link
    try:
        # Skip local file paths
        if not image_url.startswith('http'):
            # For local paths, just mark as working
            products.update_one(
                {"_id": ObjectId(product_id)},
                {"$set": {"broken_link": False}}
            )
            return {
                "success": True,
                "message": "Link repaired (local file)",
                "product_id": product_id,
                "broken_link": False
            }
        
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.head(image_url)
            
            if response.status_code < 400:
                # Link is working now
                products.update_one(
                    {"_id": ObjectId(product_id)},
                    {"$set": {"broken_link": False}}
                )
                return {
                    "success": True,
                    "message": "Link repaired successfully",
                    "product_id": product_id,
                    "broken_link": False
                }
            else:
                # Still broken
                return {
                    "success": False,
                    "message": f"Link still broken (HTTP {response.status_code})",
                    "product_id": product_id,
                    "broken_link": True
                }
                
    except Exception as e:
        # Still broken - connection error
        return {
            "success": False,
            "message": f"Link still broken: {str(e)}",
            "product_id": product_id,
            "broken_link": True
        }


@router.delete("/products/clear-all")
async def clear_all_products(
    admin: dict = Depends(require_admin)
):
    """
    Clear all products from the catalogue
    
    **WARNING:** This will delete ALL products from the database.
    Use with caution! This action cannot be undone.
    
    Module 2: Product Catalogue - Clear all products
    """
    try:
        products = get_products_collection()
        
        # Count products before deletion
        total_count = products.count_documents({})
        
        if total_count == 0:
            return {
                "success": True,
                "message": "Product catalogue is already empty",
                "deleted_count": 0
            }
        
        # Delete all products
        result = products.delete_many({})
        deleted_count = result.deleted_count
        
        logger.info(f"Cleared all products from catalogue. Deleted {deleted_count} products.")
        
        return {
            "success": True,
            "message": f"Successfully cleared all products from catalogue",
            "deleted_count": deleted_count
        }
        
    except Exception as e:
        logger.error(f"Error clearing products: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clear products: {str(e)}"
        )


@router.delete("/products/{product_id}")
async def delete_product(
    product_id: str,
    admin: dict = Depends(require_admin)
):
    """
    Delete a product permanently
    
    Module 2: Product Catalogue - Delete products
    """
    products = get_products_collection()
    
    if not ObjectId.is_valid(product_id):
        raise HTTPException(status_code=400, detail="Invalid product ID")
    
    result = products.delete_one({"_id": ObjectId(product_id)})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Product not found")
    
    return {
        "success": True,
        "message": "Product deleted successfully",
        "product_id": product_id
    }


@router.get("/categories")
async def get_all_categories(
    admin: dict = Depends(require_admin)
):
    """
    Get all unique product categories
    
    Module 2: Product Catalogue - View category tags
    """
    products = get_products_collection()
    
    categories = products.distinct("category")
    
    # Get count for each category
    category_stats = []
    for cat in categories:
        count = products.count_documents({"category": cat})
        category_stats.append({
            "name": cat,
            "count": count
        })
    
    return {
        "categories": category_stats,
        "total": len(categories)
    }


@router.post("/categories")
async def add_category_tag(
    category_name: str,
    admin: dict = Depends(require_admin)
):
    """
    Add a new category tag to the system
    
    Module 2: Product Catalogue - Add category tags
    """
    # For MongoDB, categories are just strings in products
    # We can validate by checking if it already exists
    products = get_products_collection()
    
    existing = products.find_one({"category": category_name})
    if existing:
        return {
            "success": True,
            "message": f"Category '{category_name}' already exists",
            "category": category_name
        }
    
    # Create a placeholder product to register the category
    # Or just return success - categories are created when products use them
    return {
        "success": True,
        "message": f"Category '{category_name}' ready to use",
        "category": category_name
    }


@router.get("/products")
async def get_products_admin(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    category: Optional[str] = None,
    brand: Optional[str] = None,
    gender: Optional[str] = None,
    broken_links_only: bool = False,
    search: Optional[str] = None,
    admin: dict = Depends(require_admin)
):
    """
    Get products with filtering for admin management
    
    Module 2: Product Catalogue - View products with filters
    """
    products = get_products_collection()
    
    # Build query
    query = {}
    
    # Filter by gender if provided (for Men's Catalogue)
    if gender:
        query["gender"] = gender
    
    if category:
        # Support filtering by category - handle "Men → Eastern" format
        # Check if category contains gender info
        category_lower = category.lower()
        if "men" in category_lower or "man" in category_lower:
            # For men's categories, filter by category field and gender
            query["$and"] = [
                {
                    "$or": [
                        {"category": category},
                        {"category": {"$regex": category.replace("→", ".*").replace("->", ".*"), "$options": "i"}},
                        {"normalized_category": category},
                        {"product_category": category}
                    ]
                },
                {"gender": "m"}  # Ensure it's a men's product
            ]
        elif "women" in category_lower or "woman" in category_lower:
            # For women's categories, filter by category field and gender
            query["$and"] = [
                {
                    "$or": [
                        {"category": category},
                        {"category": {"$regex": category.replace("→", ".*").replace("->", ".*"), "$options": "i"}},
                        {"normalized_category": category},
                        {"product_category": category}
                    ]
                },
                {"gender": "w"}  # Ensure it's a women's product
            ]
        else:
            # For other categories, just match the category field
            query["$or"] = [
                {"category": category},
                {"category": {"$regex": category.replace("→", ".*").replace("->", ".*"), "$options": "i"}},
                {"normalized_category": category},
                {"product_category": category}
            ]
    if brand:
        if "$and" in query:
            query["$and"].append({"brand": brand})
        else:
            query["brand"] = brand
    if broken_links_only:
        if "$and" in query:
            query["$and"].append({"broken_link": True})
        else:
            query["broken_link"] = True
    if search:
        search_query = {
            "$or": [
                {"name": {"$regex": search, "$options": "i"}},
                {"description": {"$regex": search, "$options": "i"}}
            ]
        }
        if "$and" in query:
            query["$and"].append(search_query)
        else:
            query["$or"] = search_query["$or"]
    
    # Get total
    total = products.count_documents(query)
    
    # Get paginated
    skip = (page - 1) * page_size
    product_list = list(
        products.find(query)
        .skip(skip)
        .limit(page_size)
        .sort("created_at", -1)
    )
    
    # Format
    for product in product_list:
        product["_id"] = str(product["_id"])
        if "embedding" in product:
            del product["embedding"]  # Don't send large embeddings
    
    return {
        "products": product_list,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size
    }


# ============================================
# MODULE 3: ML Model Training Dashboard
# ============================================

# In-memory storage for training jobs (use Redis in production)
training_jobs = {}


@router.post("/ml/train")
async def trigger_model_training(
    train_split: float = Query(0.8, ge=0.5, le=0.95),
    admin: dict = Depends(require_admin)
):
    """
    Trigger ML model retraining
    
    Module 3: ML Training - Start training with custom train/test split
    """
    import uuid
    
    job_id = str(uuid.uuid4())
    
    # Store job
    training_jobs[job_id] = {
        "job_id": job_id,
        "status": "pending",
        "progress": 0,
        "train_split": train_split,
        "started_at": datetime.utcnow(),
        "message": "Training job queued"
    }
    
    # Start training in background (simplified - use Celery in production)
    asyncio.create_task(run_training_job(job_id, train_split))
    
    return {
        "success": True,
        "job_id": job_id,
        "message": "Training started",
        "train_split": train_split
    }


async def run_training_job(job_id: str, train_split: float):
    """
    Background task to run ML training
    """
    try:
        training_jobs[job_id]["status"] = "running"
        training_jobs[job_id]["progress"] = 10
        
        # Simulate training (replace with actual ML training code)
        await asyncio.sleep(2)
        training_jobs[job_id]["progress"] = 30
        
        await asyncio.sleep(2)
        training_jobs[job_id]["progress"] = 60
        
        await asyncio.sleep(2)
        training_jobs[job_id]["progress"] = 90
        
        # Complete
        training_jobs[job_id]["status"] = "completed"
        training_jobs[job_id]["progress"] = 100
        training_jobs[job_id]["completed_at"] = datetime.utcnow()
        training_jobs[job_id]["metrics"] = {
            "accuracy": 0.92,
            "precision": 0.89,
            "recall": 0.91,
            "f1_score": 0.90
        }
        
    except Exception as e:
        training_jobs[job_id]["status"] = "failed"
        training_jobs[job_id]["error"] = str(e)


@router.get("/ml/training-status/{job_id}")
async def get_training_status(
    job_id: str,
    admin: dict = Depends(require_admin)
):
    """
    Get training job status and progress
    
    Module 3: ML Training - Check progress
    """
    if job_id not in training_jobs:
        raise HTTPException(status_code=404, detail="Training job not found")
    
    job = training_jobs[job_id]
    return job


@router.get("/ml/metrics")
async def get_training_metrics(
    limit: int = Query(10, ge=1, le=50),
    admin: dict = Depends(require_admin)
):
    """
    Get historical training metrics
    
    Module 3: ML Training - View performance metrics
    """
    # Get completed training jobs
    completed_jobs = [
        job for job in training_jobs.values()
        if job["status"] == "completed" and "metrics" in job
    ]
    
    # Sort by completed_at (most recent first)
    completed_jobs.sort(
        key=lambda x: x.get("completed_at", datetime.min),
        reverse=True
    )
    
    return {
        "metrics": completed_jobs[:limit],
        "total": len(completed_jobs)
    }


# ============================================
# MODULE 4: Auto Sync / Rescraping
# ============================================

# In-memory storage for scraping jobs
scraping_jobs = {}


@router.get("/scraping/brands")
async def get_available_brands(
    brand_type: str = Query("local", regex="^(luxury|pakistani|local)$"),
    admin: dict = Depends(require_admin)
):
    """
    Get list of brands available for rescraping from Excel files
    
    Module 4: Auto Sync - View brands
    """
    brands = []
    seen_brands = {}  # Track unique brands by (brand_name, brand_url)
    brand_names_list = []  # Collect all brand names first for batch query
    
    try:
        # Find project root: walk up until we find local_brands_links.csv (works from backend/ or repo root)
        _start = os.path.abspath(os.path.dirname(__file__))
        project_root = _start
        for _ in range(10):
            if os.path.isfile(os.path.join(project_root, "local_brands_links.csv")):
                break
            _parent = os.path.dirname(project_root)
            if _parent == project_root:
                break
            project_root = _parent
        if not os.path.isfile(os.path.join(project_root, "local_brands_links.csv")):
            project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../.."))
        logger.info(f"Brands project_root: {project_root}")
        
        # For "local" type: load ONLY from local_brands_links.csv so URLs are exact listing links (no Excel)
        if brand_type == "local":
            csv_file = os.path.join(project_root, "local_brands_links.csv")
            if os.path.isfile(csv_file):
                try:
                    df_csv = pd.read_csv(csv_file)
                    if "Brand" in df_csv.columns and "Website" in df_csv.columns:
                        for idx, row in df_csv.iterrows():
                            brand_name = str(row.get("Brand", "")).strip()
                            brand_url = row.get("Website", "")
                            if pd.notna(brand_url) and brand_url:
                                # Support multiple URLs per brand: separate with |
                                url_str = str(brand_url).strip()
                                brand_urls = [u.strip() for u in url_str.split("|") if u.strip().startswith("http")]
                                if not brand_urls:
                                    continue
                                brand_url_str = brand_urls[0]
                                brand_key = (brand_name, brand_url_str)
                                if brand_key not in seen_brands:
                                    seen_brands[brand_key] = True
                                    # ScraperType in CSV: generic (default) | shopify_json (Shopify collection JSON) | woocommerce (reserved)
                                    scraper_type = str(row.get("ScraperType", "")).strip().lower() if "ScraperType" in df_csv.columns else ""
                                    if scraper_type == "nan" or scraper_type not in ("shopify_json", "woocommerce"):
                                        scraper_type = "generic"
                                    brand_data = {
                                        "brand_name": brand_name,
                                        "brand_url": brand_url_str,
                                        "brand_urls": brand_urls,  # all URLs to scrape (multiple links per brand)
                                        "category": "Men → Eastern",
                                        "product_count": 0,
                                        "last_scraped_at": None,
                                        "gender": "m",
                                        "scraper_type": scraper_type,
                                    }
                                    brands.append(brand_data)
                                    brand_names_list.append(brand_name)
                        logger.info(f"Loaded {len(brands)} brands from local_brands_links.csv (local type)")
                except Exception as e:
                    logger.warning(f"Error reading local_brands_links.csv: {e}")
            if not brands:
                brand_type = "_local_fallback"
        
        # For local type: load women's brands from local_brands_links_women.csv (same pattern as men's CSV)
        if brand_type == "local":
            women_csv = os.path.join(project_root, "local_brands_links_women.csv")
            if os.path.isfile(women_csv):
                try:
                    df_women_csv = pd.read_csv(women_csv)
                    if "Brand" in df_women_csv.columns and "Website" in df_women_csv.columns:
                        women_added = 0
                        for idx, row in df_women_csv.iterrows():
                            brand_name = str(row.get("Brand", "")).strip()
                            brand_url = row.get("Website", "")
                            if not brand_name:
                                continue
                            if pd.notna(brand_url) and brand_url:
                                url_str = str(brand_url).strip()
                                brand_urls = [u.strip() for u in url_str.split("|") if u.strip().startswith("http")]
                                if not brand_urls:
                                    continue
                                brand_url_str = brand_urls[0]
                                brand_key = (brand_name, brand_url_str)
                                if brand_key not in seen_brands:
                                    seen_brands[brand_key] = True
                                    scraper_type = str(row.get("ScraperType", "")).strip().lower() if "ScraperType" in df_women_csv.columns else ""
                                    if scraper_type == "nan" or scraper_type not in ("shopify_json", "woocommerce"):
                                        scraper_type = "generic"
                                    brand_data = {
                                        "brand_name": brand_name,
                                        "brand_url": brand_url_str,
                                        "brand_urls": brand_urls,
                                        "category": "Women → Stitched",
                                        "product_count": 0,
                                        "last_scraped_at": None,
                                        "gender": "w",
                                        "scraper_type": scraper_type,
                                    }
                                    brands.append(brand_data)
                                    brand_names_list.append(brand_name)
                                    women_added += 1
                        if women_added:
                            logger.info(f"Loaded {women_added} women's brands from local_brands_links_women.csv (local type)")
                except Exception as e:
                    logger.warning(f"Error reading local_brands_links_women.csv: {e}")
        
        # Read women links dataset Excel (only when brand_type is NOT local; local uses CSV above)
        if brand_type != "local":
            women_file = os.path.join(project_root, "women links dataset.xlsx")
            if os.path.exists(women_file):
                df = pd.read_excel(women_file)
                logger.info(f"Reading women's dataset: {women_file}, rows: {len(df)}")
                
                # Determine which link column to use
                link_column = None
                brand_column = None
                if brand_type == "luxury":
                    link_column = "Luxury Brand Link"
                    brand_column = "Luxury / International Brand"
                elif brand_type == "pakistani":
                    link_column = "Pakistani Designer Brand Link"
                    brand_column = "Pakistani Luxury / Designer Brand"
                else:  # local
                    link_column = "Local Dupe Brand Link"
                    brand_column = "Local Affordable Brand (Dupe)"
                
                if link_column in df.columns:
                    for idx, row in df.iterrows():
                        brand_url = row.get(link_column, "")
                        if pd.notna(brand_url) and brand_url and str(brand_url).startswith("http"):
                            brand_name = row.get(brand_column, "Unknown Brand")
                            brand_url_str = str(brand_url)
                            main_category = row.get("Main Category", "")
                            
                            # Create unique key for deduplication
                            brand_key = (brand_name, brand_url_str)
                            
                            # Skip if we've already seen this brand
                            if brand_key not in seen_brands:
                                # ALL brands from women's dataset are women's brands
                                gender = "w"  # Always women for women's dataset
                                
                                brand_data = {
                                    "brand_name": brand_name,
                                    "brand_url": brand_url_str,
                                    "category": main_category,
                                    "product_count": 0,  # Will be set later in batch
                                    "last_scraped_at": None,
                                    "gender": gender  # Always "w" for women's dataset
                                }
                                
                                brands.append(brand_data)
                                seen_brands[brand_key] = True
                                if brand_name not in brand_names_list:
                                    brand_names_list.append(brand_name)
                                
                                logger.debug(f"Added women's brand: {brand_name}, gender: {gender}, category: {main_category}")
        
        # Read men dataset (skip for local - we use CSV only)
        if brand_type != "local":
            men_file = os.path.join(project_root, "men dataset.xlsx")
            if os.path.exists(men_file):
                try:
                    df_men = pd.read_excel(men_file)
                    
                    # Check if men dataset has link columns
                    men_link_column = None
                    men_brand_column = None
                    if brand_type == "luxury":
                        men_link_column = "Luxury Brand Link" if "Luxury Brand Link" in df_men.columns else None
                        men_brand_column = "Luxury / International Brand"
                    elif brand_type == "pakistani":
                        men_link_column = "Pakistani Designer Brand Link" if "Pakistani Designer Brand Link" in df_men.columns else None
                        men_brand_column = "Pakistani Luxury / Designer Brand"
                    else:  # local
                        men_link_column = "Local Dupe Brand Link" if "Local Dupe Brand Link" in df_men.columns else None
                        men_brand_column = "Local Affordable Brand (Dupe)"
                    
                    # If men dataset has links, add them to brands list
                    if men_link_column and men_link_column in df_men.columns:
                        for idx, row in df_men.iterrows():
                            brand_url = row.get(men_link_column, "")
                            if pd.notna(brand_url) and brand_url and str(brand_url).startswith("http"):
                                brand_name = row.get(men_brand_column, "Unknown Brand")
                                brand_url_str = str(brand_url)
                                main_category = row.get("Main Category", "")
                                
                                # Create unique key for deduplication
                                brand_key = (brand_name, brand_url_str)
                                
                                # Skip if we've already seen this brand
                                if brand_key not in seen_brands:
                                    # Since this is from men's dataset, explicitly set gender to "m"
                                    # Only override if category explicitly says "women"
                                    if "women" in main_category.lower() or "woman" in main_category.lower():
                                        gender = "w"
                                    else:
                                        gender = "m"  # Default to men for men's dataset
                                    
                                    brand_data = {
                                        "brand_name": brand_name,
                                        "brand_url": brand_url_str,
                                        "category": main_category,
                                        "product_count": 0,  # Will be set later in batch
                                        "last_scraped_at": None,
                                        "gender": gender
                                    }
                                    
                                    brands.append(brand_data)
                                    seen_brands[brand_key] = True
                                    if brand_name not in brand_names_list:
                                        brand_names_list.append(brand_name)
                except Exception as e:
                    logger.warning(f"Error reading men dataset: {e}")
                    # Don't fail completely if men dataset has issues
        
        # Read men's brands from local_brands_links.csv (only when local was not already loaded from CSV at top)
        if brand_type == "local" and not brands:
            csv_file = os.path.join(project_root, "local_brands_links.csv")
            logger.info(f"Local brands CSV: {csv_file}, exists: {os.path.exists(csv_file)}")
            if os.path.exists(csv_file):
                try:
                    df_csv = pd.read_csv(csv_file)
                    logger.info(f"Read {len(df_csv)} rows from local_brands_links.csv")
                    
                    # CSV has Brand and Website columns
                    if "Brand" in df_csv.columns and "Website" in df_csv.columns:
                        for idx, row in df_csv.iterrows():
                            brand_name = row.get("Brand", "")
                            brand_url = row.get("Website", "")
                            
                            if pd.notna(brand_name) and pd.notna(brand_url) and brand_url and str(brand_url).startswith("http"):
                                # Default category for men's brands from CSV
                                main_category = "Men → Eastern"
                                brand_url_str = str(brand_url)
                                
                                # Create unique key for deduplication
                                brand_key = (brand_name, brand_url_str)
                                
                                # Skip if we've already seen this brand
                                if brand_key not in seen_brands:
                                    # Men's brands from CSV
                                    gender = "m"
                                    scraper_type = str(row.get("ScraperType", "")).strip().lower() if "ScraperType" in df_csv.columns else ""
                                    if scraper_type == "nan" or scraper_type not in ("shopify_json", "woocommerce"):
                                        scraper_type = "generic"
                                    brand_data = {
                                        "brand_name": brand_name,
                                        "brand_url": brand_url_str,
                                        "category": main_category,
                                        "product_count": 0,  # Will be set later in batch
                                        "last_scraped_at": None,
                                        "gender": gender,  # Men's brands
                                        "scraper_type": scraper_type,
                                    }
                                    brands.append(brand_data)
                                    seen_brands[brand_key] = True
                                    if brand_name not in brand_names_list:
                                        brand_names_list.append(brand_name)
                                    
                                    logger.debug(f"Added men's brand from CSV: {brand_name}, gender: {gender}, category: {main_category}")
                except Exception as e:
                    logger.warning(f"Error reading local_brands_links.csv: {e}")
                    # Don't fail completely if CSV has issues
        
        # Batch query product counts for all brands at once (optimization)
        if brands and brand_names_list:
            try:
                products = get_products_collection()
                # Use aggregation pipeline to get counts for all brands in one query
                pipeline = [
                    {"$match": {"brand": {"$in": brand_names_list}}},
                    {"$group": {"_id": "$brand", "count": {"$sum": 1}}}
                ]
                brand_counts = {item["_id"]: item["count"] for item in products.aggregate(pipeline)}
                
                # Update product counts in brands list
                for brand in brands:
                    brand["product_count"] = brand_counts.get(brand["brand_name"], 0)
            except Exception as e:
                logger.warning(f"Error getting product counts: {e}")
                # If batch query fails, set all to 0 (better than failing completely)
                for brand in brands:
                    brand["product_count"] = 0
        
    except Exception as e:
        logger.error(f"Error reading brands from Excel: {e}")
        raise HTTPException(status_code=500, detail=f"Error reading brands: {str(e)}")
    
    # Log summary for debugging
    gender_counts = {}
    for brand in brands:
        gender = brand.get("gender", "unknown")
        gender_counts[gender] = gender_counts.get(gender, 0) + 1
    logger.info(f"Brand loading complete. Total: {len(brands)}, Gender breakdown: {gender_counts}")
    
    # Sort brands by product_count (descending) - brands with most products first
    brands.sort(key=lambda x: x.get("product_count", 0), reverse=True)
    
    return {
        "brands": brands,
        "total": len(brands),
        "brand_type": brand_type
    }


@router.get("/scraping/test-one")
async def test_scrape_one_brand():
    """
    Debug: run scraper on first CSV brand (Bonanza) and return product count.
    No auth - remove in production. Use to verify scraper works.
    """
    from app.services.scraper_service import ProductScraper
    _start = os.path.abspath(os.path.dirname(__file__))
    project_root = _start
    for _ in range(10):
        if os.path.isfile(os.path.join(project_root, "local_brands_links.csv")):
            break
        _parent = os.path.dirname(project_root)
        if _parent == project_root:
            break
        project_root = _parent
    csv_path = os.path.join(project_root, "local_brands_links.csv")
    csv_exists = os.path.isfile(csv_path)
    if not csv_exists:
        return {"ok": False, "error": "CSV not found", "project_root": project_root, "csv_path": csv_path}
    df = pd.read_csv(csv_path)
    if "Brand" not in df.columns or "Website" not in df.columns:
        return {"ok": False, "error": "CSV missing Brand/Website columns"}
    # Use row 2 (Bonanza Satrangi) to test the brand that was returning 0 products
    row = df.iloc[min(2, len(df) - 1)]
    brand_name = str(row.get("Brand", ""))
    brand_url = str(row.get("Website", "")).strip()
    if not brand_url.startswith("http"):
        return {"ok": False, "error": "Invalid URL", "brand_name": brand_name, "brand_url": brand_url}
    scraper = ProductScraper()
    try:
        products = await scraper.scrape_exact_listing_url(brand_url, brand_name, "Men -> Eastern", "m", None)
    except Exception as e:
        logger.exception("test_scrape_one_brand failed")
        return {"ok": False, "error": str(e), "brand_url": brand_url}
    finally:
        await scraper.close()
    return {
        "ok": True,
        "project_root": project_root,
        "csv_path": csv_path,
        "brand_name": brand_name,
        "brand_url": brand_url,
        "products_count": len(products),
        "sample": [{"name": p.get("name"), "price": p.get("price")} for p in products[:3]],
    }


@router.post("/scraping/start")
async def start_rescraping(
    request: dict,  # {brand_ids: [{"brand_name": "...", "brand_url": "...", "category": "..."}]}
    admin: dict = Depends(require_admin)
):
    """
    Start rescraping selected brands from Excel files
    
    Module 4: Auto Sync - Trigger rescraping
    """
    import uuid
    
    brand_list = request.get("brand_ids", [])
    
    if not brand_list:
        raise HTTPException(status_code=400, detail="No brands selected")
    
    job_id = str(uuid.uuid4())
    started_at = datetime.utcnow()
    
    # Prepare job data
    job_data = {
        "job_id": job_id,
        "status": "pending",
        "brands": brand_list,
        "brands_completed": 0,
        "brands_total": len(brand_list),
        "products_added": 0,
        "started_at": started_at,
        "logs": []
    }
    
    # Store job in memory for real-time status
    scraping_jobs[job_id] = job_data.copy()
    
    # Store job in MongoDB for persistence
    scraping_history = get_scraping_history_collection()
    scraping_history.insert_one(job_data)
    
    # Start scraping in background
    asyncio.create_task(run_scraping_job(job_id, brand_list))
    
    return {
        "success": True,
        "job_id": job_id,
        "message": f"Scraping started for {len(brand_list)} brand(s)"
    }


async def run_scraping_job(job_id: str, brand_list: List[dict]):
    """
    Background task to run web scraping from Excel files
    """
    from app.services.scraper_service import ProductScraper
    
    scraper = None
    scraping_history = get_scraping_history_collection()
    
    try:
        scraping_jobs[job_id]["status"] = "running"
        total_products = 0
        
        # Update status in MongoDB
        scraping_history.update_one(
            {"job_id": job_id},
            {"$set": {"status": "running"}}
        )
        
        scraper = ProductScraper()
        
        for idx, brand_info in enumerate(brand_list):
            brand_name = brand_info.get("brand_name", "Unknown")
            # Multiple URLs per brand: brand_urls (list) or single brand_url
            urls_to_scrape = brand_info.get("brand_urls") or []
            if not urls_to_scrape and brand_info.get("brand_url"):
                urls_to_scrape = [(brand_info.get("brand_url") or "").strip()]
            urls_to_scrape = [u.strip() for u in urls_to_scrape if u and u.strip().startswith("http")]
            category = brand_info.get("category", "")
            logger.info(f"Job {job_id} brand[{idx}]: name={brand_name!r} urls={len(urls_to_scrape)}")
            if not urls_to_scrape:
                scraping_jobs[job_id]["logs"].append(f"Skipping {brand_name}: no valid URL")
                continue
            # Extract gender from brand_info if available, otherwise infer from category
            gender = brand_info.get("gender")
            if not gender:
                if "men" in category.lower() or "man" in category.lower():
                    gender = "m"
                elif "women" in category.lower() or "woman" in category.lower():
                    gender = "w"
            
            try:
                scraping_jobs[job_id]["logs"].append(f"Starting scrape for {brand_name} ({len(urls_to_scrape)} link(s), Category: {category}, Gender: {gender})...")
                scraper_type = (brand_info.get("scraper_type") or "").strip().lower() or "generic"
                from urllib.parse import urlparse
                all_products = []
                seen_product_urls = set()
                for brand_url in urls_to_scrape:
                    parsed = urlparse(brand_url or "")
                    path = (parsed.path or "").strip("/")
                    url_lower = (brand_url or "").lower()
                    use_exact_listing = (
                        len(path.split("/")) >= 1 and path != ""
                        or ".html" in url_lower
                        or "/collections/" in url_lower
                        or any(x in url_lower for x in ["/shirts", "/products", "/men", "/women", "/shop/", "/category/"])
                    )
                    scraping_jobs[job_id]["logs"].append(f"Scraping: {brand_url}")
                    try:
                        timeout_seconds = 300.0 if use_exact_listing else 60.0
                        if use_exact_listing:
                            page_products = await asyncio.wait_for(
                                scraper.scrape_exact_listing_url(brand_url, brand_name, category, gender, None, scraper_type=scraper_type),
                                timeout=timeout_seconds
                            )
                        else:
                            page_products = await asyncio.wait_for(
                                scraper.scrape_brand_website(brand_url, brand_name, category, gender),
                                timeout=timeout_seconds
                            )
                    except asyncio.TimeoutError:
                        scraping_jobs[job_id]["logs"].append(f"Timeout for {brand_url}")
                        page_products = []
                    except Exception as scrape_error:
                        scraping_jobs[job_id]["logs"].append(f"Error {brand_url}: {str(scrape_error)}")
                        logger.error(f"Error scraping {brand_name} {brand_url}: {scrape_error}", exc_info=True)
                        page_products = []
                    for p in page_products:
                        purl = (p.get("product_url") or "").strip()
                        if purl and purl not in seen_product_urls:
                            seen_product_urls.add(purl)
                            all_products.append(p)
                products = all_products
                scraping_jobs[job_id]["logs"].append(
                    f"Found {len(products)} products from {brand_name} ({len(urls_to_scrape)} link(s))"
                )
                if len(products) == 0:
                    scraping_jobs[job_id]["logs"].append(
                        f"⚠ {brand_name}: 0 products extracted. Check URL(s) or site structure."
                    )
                logger.info(f"Scrape done: {brand_name} | {len(urls_to_scrape)} URL(s) | products: {len(products)}")
                
                # Store products in MongoDB
                products_collection = get_products_collection()
                stored = 0
                updated = 0
                
                def _is_valid_image_url(u):
                    if not u or not u.lower().startswith(("http://", "https://")): return False
                    ul = (u or "").lower()
                    if "loader" in ul or "lazyload" in ul or (u or "").rstrip("/").endswith(".gif"): return False
                    if not _looks_like_image_url(u): return False
                    return True
                
                # Pass 1: resolve image_url per product, skip if existing already has local file
                img_dir = _get_product_images_dir()
                to_download = []  # list of (product, image_url)
                for product in products:
                    existing = products_collection.find_one({"product_url": product.get("product_url")})
                    image_url = (product.get("image_url") or "").strip()
                    if not _is_valid_image_url(image_url) and existing:
                        image_url = (existing.get("image_url") or "").strip()
                    if existing and (existing.get("image_path") or "").startswith("product_images/"):
                        rel = (existing["image_path"] or "").replace("\\", "/")
                        if (img_dir / rel.replace("product_images/", "")).exists():
                            product["image_path"] = rel
                            to_download.append((product, None))
                            continue
                    if _is_valid_image_url(image_url):
                        to_download.append((product, image_url))
                    else:
                        to_download.append((product, None))
                
                # Pass 2: parallel image downloads (max 10 at a time)
                sem = asyncio.Semaphore(10)
                async def _download_with_sem(p, url):
                    if not url:
                        return
                    async with sem:
                        path = await _download_product_image(url, p.get("product_url") or "")
                        if path:
                            p["image_path"] = path
                await asyncio.gather(*[_download_with_sem(p, url) for p, url in to_download])
                
                # Pass 3: insert or update
                for product in products:
                    try:
                        existing = products_collection.find_one({"product_url": product.get("product_url")})
                        if not existing:
                            # Check if product_id already exists (handle hash collisions)
                            product_id = product.get("product_id")
                            if product_id:
                                id_exists = products_collection.find_one({"product_id": product_id})
                                if id_exists:
                                    # Generate new product_id by appending timestamp hash
                                    url_hash = hashlib.md5(
                                        f"{product.get('product_url')}{datetime.utcnow().isoformat()}".encode('utf-8')
                                    ).hexdigest()
                                    product['product_id'] = int(url_hash[:8], 16)
                            
                            products_collection.insert_one(product)
                            stored += 1
                        else:
                            # Update existing product (preserve existing product_id and existing image_path if we didn't get new one)
                            update_data = product.copy()
                            if 'product_id' in update_data:
                                del update_data['product_id']
                            if not update_data.get("image_path") and (existing.get("image_path") or "").startswith("product_images/"):
                                update_data["image_path"] = existing["image_path"]
                            products_collection.update_one(
                                {"product_url": product.get("product_url")},
                                {"$set": update_data}
                            )
                            updated += 1
                    except Exception as e:
                        error_msg = str(e)
                        # If it's a duplicate key error, try with a new product_id
                        if "E11000" in error_msg or "duplicate key" in error_msg.lower():
                            try:
                                url_hash = hashlib.md5(
                                    f"{product.get('product_url')}{datetime.utcnow().isoformat()}".encode('utf-8')
                                ).hexdigest()
                                product['product_id'] = int(url_hash[:8], 16)
                                products_collection.insert_one(product)
                                stored += 1
                                logger.info(f"Retried insert with new product_id for {product.get('product_url')}")
                            except Exception as retry_error:
                                logger.error(f"Error storing product (retry failed): {retry_error}")
                                scraping_jobs[job_id]["logs"].append(f"Error storing product: {str(retry_error)}")
                        else:
                            logger.error(f"Error storing product: {e}")
                            scraping_jobs[job_id]["logs"].append(f"Error storing product: {error_msg}")
                
                total_products += stored + updated  # show new + updated so user sees total processed (not 0 when only updates)
                scraping_jobs[job_id]["products_added"] = total_products
                scraping_jobs[job_id]["brands_completed"] = idx + 1
                scraping_jobs[job_id]["logs"].append(
                    f"Completed {brand_name}: {stored} new, {updated} updated, {len(products)} total found"
                )
                # Log products without image (placeholder or empty)
                without_image = [
                    p for p in products
                    if not (p.get("image_path") or "").strip()
                    or "placeholder" in (p.get("image_path") or "").lower()
                ]
                if without_image:
                    names_preview = ", ".join((p.get("name") or "?")[:30] for p in without_image[:5])
                    if len(without_image) > 5:
                        names_preview += f" ... (+{len(without_image) - 5} more)"
                    scraping_jobs[job_id]["logs"].append(
                        f"⚠ {brand_name}: {len(without_image)} product(s) without image: {names_preview}"
                    )
                else:
                    scraping_jobs[job_id]["logs"].append(
                        f"Images: all {len(products)} products have images"
                    )
                
                # Update progress in MongoDB
                scraping_history.update_one(
                    {"job_id": job_id},
                    {"$set": {
                        "products_added": total_products,
                        "brands_completed": idx + 1,
                        "logs": scraping_jobs[job_id]["logs"]
                    }}
                )
                
                # Small delay between brands
                await asyncio.sleep(2)
            
            except Exception as e:
                error_msg = f"Error processing {brand_name}: {str(e)}"
                scraping_jobs[job_id]["logs"].append(error_msg)
                logger.error(error_msg, exc_info=True)
                # Continue with next brand instead of failing completely
        
        # Complete
        completed_at = datetime.utcnow()
        scraping_jobs[job_id]["status"] = "completed"
        scraping_jobs[job_id]["completed_at"] = completed_at
        scraping_jobs[job_id]["logs"].append(f"Scraping completed! Total: {total_products} products (new + updated)")
        
        # Update in MongoDB
        scraping_history = get_scraping_history_collection()
        scraping_history.update_one(
            {"job_id": job_id},
            {"$set": {
                "status": "completed",
                "completed_at": completed_at,
                "products_added": total_products,
                "brands_completed": scraping_jobs[job_id]["brands_completed"],
                "logs": scraping_jobs[job_id]["logs"]
            }}
        )
        
    except Exception as e:
        failed_at = datetime.utcnow()
        scraping_jobs[job_id]["status"] = "failed"
        scraping_jobs[job_id]["error"] = str(e)
        scraping_jobs[job_id]["failed_at"] = failed_at
        scraping_jobs[job_id]["logs"].append(f"Scraping failed: {str(e)}")
        logger.error(f"Scraping job {job_id} failed: {e}", exc_info=True)
        
        # Update in MongoDB
        scraping_history = get_scraping_history_collection()
        scraping_history.update_one(
            {"job_id": job_id},
            {"$set": {
                "status": "failed",
                "failed_at": failed_at,
                "error": str(e),
                "logs": scraping_jobs[job_id]["logs"]
            }}
        )
    finally:
        if scraper:
            try:
                await scraper.close()
            except:
                pass


@router.get("/scraping/status/{job_id}")
async def get_scraping_status(
    job_id: str,
    admin: dict = Depends(require_admin)
):
    """
    Get scraping job status and progress
    
    Module 4: Auto Sync - Monitor progress
    """
    try:
        if job_id not in scraping_jobs:
            raise HTTPException(status_code=404, detail="Scraping job not found")
        
        # Return a copy to avoid any issues
        job = scraping_jobs[job_id].copy()
        return job
    except Exception as e:
        logger.error(f"Error getting scraping status: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting status: {str(e)}")


@router.get("/scraping/history")
async def get_scraping_history(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=50, description="Items per page"),
    admin: dict = Depends(require_admin)
):
    """
    Get scraping job history from MongoDB (persistent storage) with pagination
    
    Module 4: Auto Sync - View history
    """
    scraping_history = get_scraping_history_collection()
    
    # Calculate skip
    skip = (page - 1) * page_size
    
    # Get total count
    total = scraping_history.count_documents({})
    
    # Get paginated jobs from MongoDB sorted by start time (newest first)
    cursor = scraping_history.find().sort("started_at", -1).skip(skip).limit(page_size)
    jobs = []
    
    for doc in cursor:
        # Convert ObjectId to string
        doc["_id"] = str(doc["_id"])
        
        # Convert datetime fields to ISO format strings for JSON serialization
        if "started_at" in doc and isinstance(doc["started_at"], datetime):
            doc["started_at"] = doc["started_at"].isoformat()
        if "completed_at" in doc and isinstance(doc["completed_at"], datetime):
            doc["completed_at"] = doc["completed_at"].isoformat()
        if "failed_at" in doc and isinstance(doc["failed_at"], datetime):
            doc["failed_at"] = doc["failed_at"].isoformat()
        
        jobs.append(doc)
    
    # Calculate total pages
    total_pages = (total + page_size - 1) // page_size if total > 0 else 1
    
    return {
        "jobs": jobs,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages
    }


@router.delete("/scraping/history/{job_id}")
async def delete_scraping_history(
    job_id: str,
    admin: dict = Depends(require_admin)
):
    """
    Delete a scraping job from history
    
    Module 4: Auto Sync - Delete history entry
    """
    scraping_history = get_scraping_history_collection()
    
    result = scraping_history.delete_one({"job_id": job_id})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Scraping job not found")
    
    return {
        "success": True,
        "message": "Scraping history deleted successfully",
        "job_id": job_id
    }

