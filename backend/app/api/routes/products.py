"""
Products API endpoints
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import Response
from bson import ObjectId
from urllib.parse import urlparse
import httpx
import logging

from app.models.schemas import Product, ProductList, ProductFilter
from app.core.database import get_products_collection

router = APIRouter()
logger = logging.getLogger(__name__)


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






