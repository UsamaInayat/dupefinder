"""
Admin API endpoints
User management, product management, analytics, system monitoring
"""

from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, status, Query
from bson import ObjectId

from app.models.admin import (
    AdminLogin, AdminToken, AdminResponse,
    UserManagementResponse, ProductCreate, ProductUpdate,
    SystemStats
)
from app.models.user import UserResponse
from app.core.security import (
    get_password_hash,
    verify_password,
    create_access_token,
    get_current_user
)
from app.core.database import get_db

router = APIRouter()


def _cleanup_user_related_data(db, user_id: str, email: Optional[str] = None):
    db.refresh_tokens.delete_many({"user_id": user_id})
    db.user_app_data.delete_many({"user_id": user_id})
    db.community_posts.delete_many({"author_user_id": user_id})
    db.community_posts.update_many({}, {"$pull": {"replies": {"author_user_id": user_id}}})
    db.community_reports.delete_many(
        {
            "$or": [
                {"reporter_user_id": user_id},
                {"post_author_user_id": user_id},
                {"reply_author_user_id": user_id},
            ]
        }
    )
    db.community_notifications.delete_many(
        {"$or": [{"recipient_user_id": user_id}, {"actor_user_id": user_id}]}
    )
    db.community_user_blocks.delete_many(
        {"$or": [{"blocker_user_id": user_id}, {"blocked_user_id": user_id}]}
    )
    if email:
        db.otps.delete_many({"email": email})


# Admin authentication check
def get_current_admin(current_user: dict = Depends(get_current_user)) -> dict:
    """Verify current user is an admin"""
    db = get_db()
    admin = db.admins.find_one({"email": current_user["sub"]})
    
    if not admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Admin privileges required."
        )
    
    return admin


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
    db = get_db()
    admins_collection = db.admins
    
    # Find admin
    admin = admins_collection.find_one({"email": credentials.email})
    
    if not admin:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid admin credentials"
        )
    
    # Verify password
    if not verify_password(credentials.password, admin["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid admin credentials"
        )
    
    # Create access token
    access_token = create_access_token(data={"sub": credentials.email, "role": "admin"})
    
    # Prepare admin response
    admin["_id"] = str(admin["_id"])
    del admin["hashed_password"]
    
    return AdminToken(
        access_token=access_token,
        admin=AdminResponse(**admin)
    )


# ============================================
# User Management
# ============================================

@router.get("/users", response_model=UserManagementResponse)
async def get_all_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    admin: dict = Depends(get_current_admin)
):
    """
    Get all registered users (Admin only)
    
    - **page**: Page number
    - **page_size**: Users per page
    - **search**: Search by email or name
    """
    db = get_db()
    users_collection = db.users
    
    # Build query
    query = {}
    if search:
        query["$or"] = [
            {"email": {"$regex": search, "$options": "i"}},
            {"full_name": {"$regex": search, "$options": "i"}}
        ]
    
    # Get total counts
    total = users_collection.count_documents(query)
    active_users = users_collection.count_documents({**query, "is_active": True})
    inactive_users = total - active_users
    
    # Get paginated users
    skip = (page - 1) * page_size
    users = list(
        users_collection.find(query)
        .skip(skip)
        .limit(page_size)
        .sort("created_at", -1)
    )
    
    # Format users
    for user in users:
        user["_id"] = str(user["_id"])
        if "hashed_password" in user:
            del user["hashed_password"]
    
    return UserManagementResponse(
        users=users,
        total=total,
        active_users=active_users,
        inactive_users=inactive_users
    )


@router.put("/users/{user_id}/status")
async def toggle_user_status(
    user_id: str,
    admin: dict = Depends(get_current_admin)
):
    """
    Ban/unban a user (Admin only)
    
    - **user_id**: User's MongoDB ObjectId
    """
    db = get_db()
    users_collection = db.users
    
    if not ObjectId.is_valid(user_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID"
        )
    
    # Get user
    user = users_collection.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Toggle status
    new_status = not user.get("is_active", True)
    
    users_collection.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {"is_active": new_status, "updated_at": datetime.utcnow()}}
    )
    
    return {
        "success": True,
        "user_id": user_id,
        "is_active": new_status,
        "message": f"User {'activated' if new_status else 'deactivated'} successfully"
    }


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: str,
    admin: dict = Depends(get_current_admin)
):
    """
    Delete a user (Admin only)
    
    - **user_id**: User's MongoDB ObjectId
    """
    db = get_db()
    users_collection = db.users
    
    if not ObjectId.is_valid(user_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID"
        )
    
    user = users_collection.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    result = users_collection.delete_one({"_id": ObjectId(user_id)})
    
    if result.deleted_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    _cleanup_user_related_data(db, user_id, user.get("email"))
    
    return {
        "success": True,
        "message": "User deleted successfully"
    }


# ============================================
# Product Management
# ============================================

@router.post("/products")
async def create_product(
    product: ProductCreate,
    admin: dict = Depends(get_current_admin)
):
    """
    Create a new product (Admin only)
    
    Manually add products to the catalog
    """
    db = get_db()
    products_collection = db.products
    
    # Create product document
    product_doc = {
        "product_id": products_collection.count_documents({}) + 1,
        "name": product.name,
        "category": product.category,
        "brand": product.brand,
        "price": product.price,
        "description": product.description or "",
        "image_path": product.image_url or "",
        "embedding": [],  # Will be computed separately
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "created_by": "admin"
    }
    
    result = products_collection.insert_one(product_doc)
    product_doc["_id"] = str(result.inserted_id)
    
    return {
        "success": True,
        "product": product_doc,
        "message": "Product created successfully"
    }


@router.put("/products/{product_id}")
async def update_product(
    product_id: str,
    product_data: ProductUpdate,
    admin: dict = Depends(get_current_admin)
):
    """
    Update an existing product (Admin only)
    
    - **product_id**: Product's MongoDB ObjectId
    """
    db = get_db()
    products_collection = db.products
    
    if not ObjectId.is_valid(product_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid product ID"
        )
    
    # Build update document
    update_doc = {"updated_at": datetime.utcnow()}
    
    if product_data.name:
        update_doc["name"] = product_data.name
    if product_data.category:
        update_doc["category"] = product_data.category
    if product_data.brand:
        update_doc["brand"] = product_data.brand
    if product_data.price:
        update_doc["price"] = product_data.price
    if product_data.description:
        update_doc["description"] = product_data.description
    if product_data.image_url:
        update_doc["image_path"] = product_data.image_url
    
    result = products_collection.update_one(
        {"_id": ObjectId(product_id)},
        {"$set": update_doc}
    )
    
    if result.matched_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    return {
        "success": True,
        "message": "Product updated successfully"
    }


@router.delete("/products/{product_id}")
async def delete_product(
    product_id: str,
    admin: dict = Depends(get_current_admin)
):
    """
    Delete a product (Admin only)
    
    - **product_id**: Product's MongoDB ObjectId
    """
    db = get_db()
    products_collection = db.products
    
    if not ObjectId.is_valid(product_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid product ID"
        )
    
    result = products_collection.delete_one({"_id": ObjectId(product_id)})
    
    if result.deleted_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    return {
        "success": True,
        "message": "Product deleted successfully"
    }


# ============================================
# Analytics & Statistics
# ============================================

@router.get("/stats", response_model=SystemStats)
async def get_system_stats(admin: dict = Depends(get_current_admin)):
    """
    Get comprehensive system statistics (Admin only)
    
    Returns:
    - Total users, products, searches
    - Active users today
    - Top categories
    - Recent activity
    """
    db = get_db()
    
    # Get counts
    total_users = db.users.count_documents({})
    total_products = db.products.count_documents({})
    total_searches = db.search_history.count_documents({})
    
    # Active users today
    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    active_users_today = db.users.count_documents({
        "created_at": {"$gte": today}
    })
    
    # Searches today
    searches_today = db.search_history.count_documents({
        "timestamp": {"$gte": today}
    })
    
    # Average search time
    search_stats = list(db.search_history.aggregate([
        {
            "$group": {
                "_id": None,
                "avg_time": {"$avg": "$search_time_ms"}
            }
        }
    ]))
    avg_search_time = search_stats[0]["avg_time"] if search_stats else 0
    
    # Top categories
    top_categories = list(db.products.aggregate([
        {
            "$group": {
                "_id": "$category",
                "count": {"$sum": 1}
            }
        },
        {"$sort": {"count": -1}},
        {"$limit": 5}
    ]))
    
    # Recent users
    recent_users = list(
        db.users.find()
        .sort("created_at", -1)
        .limit(5)
    )
    for user in recent_users:
        user["_id"] = str(user["_id"])
        if "hashed_password" in user:
            del user["hashed_password"]
    
    # Recent searches
    recent_searches = list(
        db.search_history.find()
        .sort("timestamp", -1)
        .limit(5)
    )
    for search in recent_searches:
        search["_id"] = str(search["_id"])
        if "embedding" in search:
            del search["embedding"]
    
    return SystemStats(
        total_users=total_users,
        total_products=total_products,
        total_searches=total_searches,
        active_users_today=active_users_today,
        searches_today=searches_today,
        avg_search_time_ms=round(avg_search_time, 2),
        top_categories=top_categories,
        recent_users=recent_users,
        recent_searches=recent_searches
    )


@router.get("/analytics/searches")
async def get_search_analytics(
    days: int = Query(7, ge=1, le=30),
    admin: dict = Depends(get_current_admin)
):
    """
    Get search analytics for specified number of days
    
    - **days**: Number of days to analyze (1-30)
    """
    db = get_db()
    
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # Searches per day
    searches_per_day = list(db.search_history.aggregate([
        {"$match": {"timestamp": {"$gte": start_date}}},
        {
            "$group": {
                "_id": {
                    "$dateToString": {"format": "%Y-%m-%d", "date": "$timestamp"}
                },
                "count": {"$sum": 1}
            }
        },
        {"$sort": {"_id": 1}}
    ]))
    
    # Top search categories
    top_categories = list(db.search_history.aggregate([
        {"$match": {"timestamp": {"$gte": start_date}}},
        {"$unwind": "$results"},
        {
            "$lookup": {
                "from": "products",
                "localField": "results.product_id",
                "foreignField": "_id",
                "as": "product"
            }
        },
        {"$unwind": "$product"},
        {
            "$group": {
                "_id": "$product.category",
                "count": {"$sum": 1}
            }
        },
        {"$sort": {"count": -1}}
    ]))
    
    return {
        "period_days": days,
        "searches_per_day": searches_per_day,
        "top_categories": top_categories,
        "total_searches": sum(day["count"] for day in searches_per_day)
    }


# ============================================
# System Health
# ============================================

@router.get("/health")
async def admin_health_check(admin: dict = Depends(get_current_admin)):
    """
    Check system health (Admin only)
    
    Returns database status, ML engine status, API health
    """
    db = get_db()
    
    try:
        # Test database connection
        db.command("ping")
        db_status = "healthy"
    except:
        db_status = "error"
    
    # Check collections
    collections = db.list_collection_names()
    
    # Get collection sizes
    collection_stats = {}
    for coll_name in ["users", "products", "search_history", "admins"]:
        if coll_name in collections:
            collection_stats[coll_name] = db[coll_name].count_documents({})
    
    return {
        "status": "healthy",
        "database": db_status,
        "collections": collection_stats,
        "timestamp": datetime.utcnow().isoformat()
    }

