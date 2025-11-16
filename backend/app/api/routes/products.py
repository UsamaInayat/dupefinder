"""
Products API endpoints
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from bson import ObjectId

from app.models.schemas import Product, ProductList, ProductFilter
from app.core.database import get_products_collection

router = APIRouter()


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






