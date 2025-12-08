"""
Image search API endpoints
"""

import sys
import time
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, File, UploadFile, HTTPException, Query
from bson import ObjectId

# Add ML engine to path
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "ml-engine"))

from embeddings.feature_extractor import FeatureExtractor
from app.models.schemas import SearchResponse, ProductWithSimilarity
from app.core.database import get_products_collection, get_search_history_collection
from app.core.security import get_current_user

router = APIRouter()

# Optional authentication - returns None if not authenticated
async def get_current_user_optional(credentials: Optional[any] = None):
    """Get current user if authenticated, None otherwise"""
    try:
        if credentials:
            return get_current_user(credentials)
        return None
    except:
        return None

# ============================================
# Global ML Engine (loaded once at startup)
# ============================================

feature_extractor = None
UPLOAD_DIR = Path(__file__).parent.parent.parent.parent.parent / "data" / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True, parents=True)


def get_feature_extractor():
    """
    Get or initialize feature extractor (singleton pattern)
    """
    global feature_extractor
    if feature_extractor is None:
        print("[INFO] Loading ResNet50 feature extractor...")
        feature_extractor = FeatureExtractor(device='cpu')  # Use CPU for now
        print("[OK] Feature extractor loaded")
    return feature_extractor


@router.post("/similar", response_model=SearchResponse)
@router.post("/upload", response_model=SearchResponse)
async def search_by_image(
    file: UploadFile = File(..., description="Image file to search"),
    top_k: int = Query(5, ge=1, le=20, description="Number of results to return"),
    category: Optional[str] = Query(None, description="Filter by category"),
    min_price: Optional[float] = Query(None, ge=0, description="Minimum price"),
    max_price: Optional[float] = Query(None, ge=0, description="Maximum price")
):
    """
    Search for similar products by uploading an image
    
    - **file**: Image file (JPG, PNG, WebP, etc.)
    - **top_k**: Number of similar products to return (1-20, default: 5)
    - **category**: Optional category filter
    - **min_price**: Optional minimum price filter
    - **max_price**: Optional maximum price filter
    
    Returns the top-K most similar products ranked by cosine similarity
    """
    start_time = time.time()
    
    # Validate file type
    allowed_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp', 'image/bmp']
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed types: {allowed_types}"
        )
    
    # Save uploaded file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"search_{timestamp}_{file.filename}"
    file_path = UPLOAD_DIR / filename
    
    try:
        # Read and save file
        contents = await file.read()
        with open(file_path, 'wb') as f:
            f.write(contents)
        
        print(f"[INFO] Uploaded image saved: {file_path}")
        
        # Extract embedding from uploaded image
        print("[INFO] Extracting embedding from uploaded image...")
        extractor = get_feature_extractor()
        query_embedding = extractor.extract_from_path(str(file_path))
        
        print(f"[OK] Embedding extracted, shape: {query_embedding.shape}")
        
        # Get products from database with filters
        collection = get_products_collection()
        
        # Build query
        query = {}
        if category:
            query["category"] = category
        if min_price is not None or max_price is not None:
            query["price"] = {}
            if min_price is not None:
                query["price"]["$gte"] = min_price
            if max_price is not None:
                query["price"]["$lte"] = max_price
        
        # Fetch products with embeddings
        products = list(collection.find(query))
        
        if len(products) == 0:
            raise HTTPException(
                status_code=404,
                detail="No products found matching the filters"
            )
        
        print(f"[INFO] Comparing with {len(products)} products...")
        
        # Calculate similarities
        similarities = []
        for product in products:
            if 'embedding' not in product:
                continue
            
            # Convert embedding to numpy array
            product_embedding = np.array(product['embedding'], dtype=np.float32)
            
            # Calculate cosine similarity
            similarity = np.dot(query_embedding, product_embedding) / (
                np.linalg.norm(query_embedding) * np.linalg.norm(product_embedding)
            )
            
            similarities.append({
                'product': product,
                'similarity': float(similarity)
            })
        
        # Sort by similarity (descending)
        similarities.sort(key=lambda x: x['similarity'], reverse=True)
        
        # Get top-K results
        top_results = similarities[:top_k]
        
        # Format results
        results = []
        for item in top_results:
            product = item['product']
            
            # Remove embedding from response
            if 'embedding' in product:
                del product['embedding']
            
            # Convert ObjectId to string
            product['_id'] = str(product['_id'])
            
            # Add similarity score
            product['similarity_score'] = item['similarity']
            
            results.append(ProductWithSimilarity(**product))
        
        # Calculate search time
        search_time_ms = (time.time() - start_time) * 1000
        
        print(f"[OK] Search completed in {search_time_ms:.2f}ms")
        print(f"[INFO] Top result: {results[0].name} (similarity: {results[0].similarity_score:.4f})")
        
        # Save to search history (optional)
        try:
            history_collection = get_search_history_collection()
            history_entry = {
                "uploaded_image_path": str(file_path),
                "embedding": query_embedding.tolist(),
                "results": [
                    {
                        "product_id": ObjectId(result.id),
                        "similarity_score": result.similarity_score
                    }
                    for result in results
                ],
                "timestamp": datetime.utcnow(),
                "search_time_ms": search_time_ms,
                "user_email": None  # Will be updated if user is authenticated
            }
            history_collection.insert_one(history_entry)
        except Exception as e:
            print(f"[WARNING] Failed to save search history: {e}")
        
        return SearchResponse(
            query_image=str(file_path),
            results=results,
            search_time_ms=search_time_ms,
            total_results=len(results)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] Search failed: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.get("/history")
async def get_search_history(
    limit: int = Query(10, ge=1, le=100, description="Number of history entries")
):
    """
    Get recent search history
    
    - **limit**: Number of recent searches to return (1-100, default: 10)
    """
    try:
        collection = get_search_history_collection()
        
        # Get recent searches
        cursor = collection.find().sort("timestamp", -1).limit(limit)
        history = []
        
        for doc in cursor:
            # Remove embeddings (too large)
            if 'embedding' in doc:
                del doc['embedding']
            
            # Convert ObjectId to string
            doc['_id'] = str(doc['_id'])
            
            # Convert result product_ids to strings
            for result in doc.get('results', []):
                if 'product_id' in result:
                    result['product_id'] = str(result['product_id'])
            
            history.append(doc)
        
        return {
            "history": history,
            "count": len(history)
        }
    
    except Exception as e:
        print(f"[ERROR] Failed to get search history: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get history: {str(e)}")


@router.get("/stats")
async def get_search_stats():
    """
    Get search statistics
    """
    try:
        collection = get_search_history_collection()
        
        # Total searches
        total_searches = collection.count_documents({})
        
        # Average search time
        pipeline = [
            {
                "$group": {
                    "_id": None,
                    "avg_search_time": {"$avg": "$search_time_ms"},
                    "min_search_time": {"$min": "$search_time_ms"},
                    "max_search_time": {"$max": "$search_time_ms"}
                }
            }
        ]
        
        stats = list(collection.aggregate(pipeline))
        
        if stats:
            stats_data = stats[0]
            return {
                "total_searches": total_searches,
                "avg_search_time_ms": round(stats_data.get("avg_search_time", 0), 2),
                "min_search_time_ms": round(stats_data.get("min_search_time", 0), 2),
                "max_search_time_ms": round(stats_data.get("max_search_time", 0), 2)
            }
        else:
            return {
                "total_searches": 0,
                "avg_search_time_ms": 0,
                "min_search_time_ms": 0,
                "max_search_time_ms": 0
            }
    
    except Exception as e:
        print(f"[ERROR] Failed to get search stats: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")

