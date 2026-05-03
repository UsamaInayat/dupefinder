"""
Products API endpoints
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import Response
from bson import ObjectId
from urllib.parse import quote, urlparse
import httpx
import logging
from pathlib import Path

from app.models.schemas import Product, ProductList, ProductFilter
from app.core.database import get_products_collection

router = APIRouter()
logger = logging.getLogger(__name__)
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent
_DATA_DIR = _PROJECT_ROOT / "data"


def _looks_like_image_url(url: str) -> bool:
    if not url:
        return False
    ul = url.lower()
    if any(x in ul for x in ["loader", "lazyload", "placeholder.com", "via.placeholder"]):
        return False
    path_part = ul.split("?")[0]
    if any(ext in path_part for ext in [".jpg", ".jpeg", ".png", ".webp", ".gif"]):
        return True
    if any(seg in path_part for seg in [
        "/media/", "/cdn/", "/files/", "/upload", "/product/", "/shop/files/", "/uploads/",
        "/catalog/", "/img/", "/images/", "/assets/", "/static/", "/mens/", "/women/", "/womens/"
    ]):
        return True
    return False


def _resolve_shop_image(doc: dict) -> tuple[str, str]:
    """
    Returns (image_src, image_kind):
    - image_kind='local' when image_path points to an existing local file under /data
    - image_kind='proxy' when a usable external image_url is available
    - image_kind='missing' when no usable image can be resolved
    """
    image_path = (doc.get("image_path") or "").strip()
    image_url = (doc.get("image_url") or "").strip()

    if image_path:
        rel = image_path.replace("\\", "/").lstrip("/")
        if rel.startswith("data/"):
            rel = rel[len("data/"):]
        local_file = _DATA_DIR / rel
        if local_file.exists():
            return (f"/data/{rel}", "local")

    if image_url and image_url.lower().startswith(("http://", "https://")) and _looks_like_image_url(image_url):
        return (f"/api/products/image-proxy?url={quote(image_url, safe='')}", "proxy")

    return ("", "missing")


@router.get("", response_model=ProductList)
@router.get("/", response_model=ProductList)
async def get_products(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    category: Optional[str] = Query(None, description="Filter by category"),
    min_price: Optional[float] = Query(None, ge=0, description="Minimum price"),
    max_price: Optional[float] = Query(None, ge=0, description="Maximum price"),
    brand: Optional[str] = Query(None, description="Filter by brand"),
    search: Optional[str] = Query(None, description="Text search")
):
    """
    Get paginated list of products with optional filters
    
    - **page**: Page number (default: 1)
    - **page_size**: Items per page (default: 20, max: 100)
    - **category**: Filter by category (bags, shoes, watches, clothing, accessories)
    - **min_price**: Minimum price filter
    - **max_price**: Maximum price filter
    - **brand**: Filter by brand name
    - **search**: Text search in name, description, brand
    """
    collection = get_products_collection()
    
    # Build filter query
    query = {}
    
    if category:
        query["category"] = category
    
    if brand:
        query["brand"] = {"$regex": brand, "$options": "i"}  # Case-insensitive
    
    if min_price is not None or max_price is not None:
        query["price"] = {}
        if min_price is not None:
            query["price"]["$gte"] = min_price
        if max_price is not None:
            query["price"]["$lte"] = max_price
    
    if search:
        query["$text"] = {"$search": search}
    
    # Get total count
    total = collection.count_documents(query)
    
    # Calculate skip
    skip = (page - 1) * page_size
    
    # Get products
    try:
        cursor = collection.find(query).skip(skip).limit(page_size)
        products = []
        
        for doc in cursor:
            # Remove embedding from response (too large)
            if 'embedding' in doc:
                del doc['embedding']
            
            # Convert ObjectId to string
            doc['_id'] = str(doc['_id'])
            
            try:
                # Convert to dict and prepare for response
                product_dict = dict(doc)
                # Remove fields that might cause validation issues
                product_dict.pop('embedding', None)
                
                # Ensure required fields exist with defaults
                if 'product_id' not in product_dict:
                    product_dict['product_id'] = 0  # Default for scraped products
                if 'created_at' not in product_dict:
                    from datetime import datetime
                    product_dict['created_at'] = datetime.utcnow()
                if 'updated_at' not in product_dict:
                    product_dict['updated_at'] = product_dict.get('created_at', datetime.utcnow())
                if 'image_path' not in product_dict:
                    product_dict['image_path'] = product_dict.get('image_url', '') or ''
                
                # Normalize category to match schema pattern if needed
                category = product_dict.get('category', 'accessories')
                valid_categories = ['bags', 'shoes', 'watches', 'clothing', 'accessories']
                if category not in valid_categories:
                    # Map to closest valid category
                    category_lower = category.lower()
                    if any(x in category_lower for x in ['bag', 'purse', 'handbag']):
                        product_dict['category'] = 'bags'
                    elif any(x in category_lower for x in ['shoe', 'sneaker', 'boot']):
                        product_dict['category'] = 'shoes'
                    elif any(x in category_lower for x in ['watch', 'timepiece']):
                        product_dict['category'] = 'watches'
                    elif any(x in category_lower for x in ['cloth', 'dress', 'shirt', 'kurta']):
                        product_dict['category'] = 'clothing'
                    else:
                        product_dict['category'] = 'accessories'
                
                # Ensure price is valid
                if not product_dict.get('price') or product_dict['price'] <= 0:
                    product_dict['price'] = 1.0  # Minimum price
                
                # Try to create Product
                products.append(Product(**product_dict))
            except Exception as e:
                import logging
                logging.warning(f"Skipping product {doc.get('_id')}: {e}")
                continue
        
        return ProductList(
            products=products,
            total=total,
            page=page,
            page_size=page_size
        )
    except Exception as e:
        import logging
        logging.error(f"Error fetching products: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching products: {str(e)}")


def _shop_browse_query(slot: str) -> dict:
    """
    Map home 'Shop by category' slots to a broad Mongo filter (display_category + legacy category).
    """
    if slot == "dresses":
        return {
            "$or": [
                {"category": "clothing"},
                {
                    "display_category": {
                        "$regex": r"Kurta|Lawn|Dress|Frock|Western|Kurti|Suit|Bottom|Unstitched|Anarkali|Fancy",
                        "$options": "i",
                    }
                },
            ]
        }
    if slot == "bags":
        return {
            "$or": [
                {"category": "bags"},
                {"display_category": {"$regex": r"Bag", "$options": "i"}},
            ]
        }
    if slot == "accessories":
        return {
            "$or": [
                {
                    "category": "accessories",
                    "display_category": {
                        "$not": {"$regex": r"Jewel", "$options": "i"},
                    },
                },
                {
                    "display_category": {
                        "$regex": r"Accessor|Wallet|Belt|Scarf|Cap|Hat|Sunglass",
                        "$options": "i",
                    }
                },
            ]
        }
    if slot == "watches":
        return {
            "$or": [
                {"category": "watches"},
                {
                    "display_category": {
                        "$regex": r"Watch|Wrist|Timepiece",
                        "$options": "i",
                    }
                },
                {"name": {"$regex": r"\bwatch(es)?\b", "$options": "i"}},
            ]
        }
    if slot == "jewelry":
        return {
            "$or": [
                {"display_category": {"$regex": r"Jewel|Jewellery|Jewelry", "$options": "i"}},
                {
                    "category": "accessories",
                    "name": {"$regex": r"jewel|necklace|ring|earring|bracelet|pendant", "$options": "i"},
                },
            ]
        }
    raise ValueError(slot)


@router.get("/shop-browse")
async def shop_browse(
    slot: str = Query(..., pattern="^(dresses|bags|accessories|jewelry|watches)$"),
    limit: int = Query(10, ge=1, le=30),
):
    """
    Curated first page for home category chips: up to `limit` products per slot from DB.
    Returns lightweight dicts (no embeddings) for mobile list/detail rows.
    """
    collection = get_products_collection()
    q = _shop_browse_query(slot)
    try:
        # Fetch a wider candidate set, then keep only valid-image products.
        # This avoids returning broken image rows to mobile.
        scan_limit = max(int(limit) * 8, 80)
        cursor = collection.find(q).sort("created_at", -1).limit(scan_limit)
        items = []
        considered = 0
        valid_local = 0
        valid_proxy = 0
        skipped_missing = 0
        for doc in cursor:
            considered += 1
            if "embedding" in doc:
                del doc["embedding"]
            doc["_id"] = str(doc["_id"])
            image_src, image_kind = _resolve_shop_image(doc)
            if image_kind == "missing":
                skipped_missing += 1
                continue
            if image_kind == "local":
                valid_local += 1
            elif image_kind == "proxy":
                valid_proxy += 1
            items.append(
                {
                    "id": doc["_id"],
                    "_id": doc["_id"],
                    "name": doc.get("name") or "Product",
                    "brand": doc.get("brand") or "",
                    "price": float(doc.get("price") or 0),
                    "description": (doc.get("description") or "")[:800],
                    "image_path": doc.get("image_path") or doc.get("image_url") or "",
                    "image_url": doc.get("image_url") or "",
                    "image_src": image_src,
                    "product_url": doc.get("product_url") or doc.get("product_link") or "",
                    "display_category": doc.get("display_category"),
                    "category": doc.get("category"),
                }
            )
            if len(items) >= int(limit):
                break
        return {
            "slot": slot,
            "limit": limit,
            "count": len(items),
            "items": items,
            "image_stats": {
                "considered": considered,
                "valid_with_local": valid_local,
                "valid_with_proxy": valid_proxy,
                "skipped_missing_image": skipped_missing,
            },
        }
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid slot")
    except Exception as e:
        logger.error("shop_browse failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


# Inline "No image" SVG returned when URL is invalid or upstream returns 404/error (avoids 502 and broken img in UI)
_NO_IMAGE_SVG = b'<svg xmlns="http://www.w3.org/2000/svg" width="200" height="200" viewBox="0 0 200 200"><rect fill="#374151" width="200" height="200"/><text x="50%" y="50%" dominant-baseline="middle" text-anchor="middle" fill="#9ca3af" font-size="14" font-family="sans-serif">No image</text></svg>'


@router.get("/image-proxy")
async def product_image_proxy(url: str = Query(..., description="Image URL to proxy")):
    """
    Proxy external product images to avoid hotlink blocking (e.g. Junaid Jamshed).
    On 404 or fetch error, returns 200 with "No image" SVG so the UI shows placeholder instead of 502.
    """
    if not url or not url.strip().lower().startswith(("http://", "https://")):
        raise HTTPException(status_code=400, detail="Invalid image URL")
    url_lower = url.lower()
    if "loader" in url_lower or "lazyload" in url_lower or url.rstrip("/").endswith(".gif"):
        raise HTTPException(status_code=400, detail="Loader/placeholder URL not allowed")
    if "via.placeholder" in url_lower or "placeholder.com" in url_lower:
        return Response(content=_NO_IMAGE_SVG, media_type="image/svg+xml")
    try:
        parsed = urlparse(url)
        origin = f"{parsed.scheme}://{parsed.netloc}"
        async with httpx.AsyncClient(timeout=20.0, follow_redirects=True) as client:
            r = await client.get(
                url,
                headers={
                    "Referer": origin + "/",
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; rv:109.0) Gecko/20100101 Firefox/115.0",
                    "Accept": "image/webp,image/apng,image/*,*/*;q=0.8",
                },
            )
            if r.status_code == 404:
                logger.debug(f"Image proxy: upstream 404 for {url[:80]}, returning placeholder")
                return Response(content=_NO_IMAGE_SVG, media_type="image/svg+xml")
            r.raise_for_status()
            content_type = r.headers.get("content-type", "image/jpeg").split(";")[0].strip()
            if "image" not in content_type:
                content_type = "image/jpeg"
            if content_type == "image/gif" and len(r.content) < 500:
                return Response(content=_NO_IMAGE_SVG, media_type="image/svg+xml")
            return Response(content=r.content, media_type=content_type)
    except httpx.HTTPStatusError as e:
        logger.debug(f"Image proxy HTTP error for {url[:80]}: {e.response.status_code}, returning placeholder")
        return Response(content=_NO_IMAGE_SVG, media_type="image/svg+xml")
    except Exception as e:
        logger.debug(f"Image proxy error for {url[:80]}: {e}, returning placeholder")
        return Response(content=_NO_IMAGE_SVG, media_type="image/svg+xml")


@router.get("/{product_id}", response_model=Product)
async def get_product_by_id(product_id: str):
    """
    Get a single product by its MongoDB ObjectId
    
    - **product_id**: MongoDB ObjectId string
    """
    collection = get_products_collection()
    
    # Validate ObjectId
    if not ObjectId.is_valid(product_id):
        raise HTTPException(status_code=400, detail="Invalid product ID format")
    
    # Find product
    doc = collection.find_one({"_id": ObjectId(product_id)})
    
    if not doc:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Remove embedding from response
    if 'embedding' in doc:
        del doc['embedding']
    
    # Convert ObjectId to string
    doc['_id'] = str(doc['_id'])
    
    return Product(**doc)


@router.get("/by-product-id/{product_id}", response_model=Product)
async def get_product_by_product_id(product_id: int):
    """
    Get a single product by its product_id (1-100)
    
    - **product_id**: Original product ID from CSV (1-100)
    """
    collection = get_products_collection()
    
    # Find product
    doc = collection.find_one({"product_id": product_id})
    
    if not doc:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Remove embedding from response
    if 'embedding' in doc:
        del doc['embedding']
    
    # Convert ObjectId to string
    doc['_id'] = str(doc['_id'])
    
    return Product(**doc)


@router.get("/categories/list")
async def get_categories():
    """
    Get list of all available categories with product counts
    """
    collection = get_products_collection()
    
    pipeline = [
        {
            "$group": {
                "_id": "$category",
                "count": {"$sum": 1},
                "avg_price": {"$avg": "$price"},
                "min_price": {"$min": "$price"},
                "max_price": {"$max": "$price"}
            }
        },
        {
            "$sort": {"_id": 1}
        }
    ]
    
    categories = list(collection.aggregate(pipeline))
    
    return {
        "categories": [
            {
                "name": cat["_id"],
                "count": cat["count"],
                "avg_price": round(cat["avg_price"], 2),
                "price_range": {
                    "min": cat["min_price"],
                    "max": cat["max_price"]
                }
            }
            for cat in categories
        ],
        "total_categories": len(categories)
    }


@router.get("/brands/list")
async def get_brands():
    """
    Get list of all available brands with product counts
    """
    collection = get_products_collection()
    
    pipeline = [
        {
            "$group": {
                "_id": "$brand",
                "count": {"$sum": 1}
            }
        },
        {
            "$sort": {"count": -1}
        }
    ]
    
    brands = list(collection.aggregate(pipeline))
    
    return {
        "brands": [
            {
                "name": brand["_id"],
                "count": brand["count"]
            }
            for brand in brands
        ],
        "total_brands": len(brands)
    }






