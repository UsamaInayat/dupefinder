"""
DupeFinder Backend - MongoDB Service Layer

This module provides service functions for MongoDB operations.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from bson import ObjectId

from app.core.database import get_database
from app.models.mongodb_models import (
    ProductEmbedding,
    UserSearchAnalytics,
    ImageMetadata,
    AnalyticsEvent,
    MLModelLog
)


# Product Embeddings Collection
async def create_product_embedding(embedding_data: dict) -> str:
    """Create a new product embedding"""
    db = get_database()
    collection = db["product_embeddings"]
    
    embedding_data["created_at"] = datetime.utcnow()
    embedding_data["updated_at"] = datetime.utcnow()
    
    result = await collection.insert_one(embedding_data)
    return str(result.inserted_id)


async def get_product_embedding(product_id: str) -> Optional[dict]:
    """Get product embedding by product_id"""
    db = get_database()
    collection = db["product_embeddings"]
    
    embedding = await collection.find_one({"product_id": product_id})
    if embedding:
        embedding["_id"] = str(embedding["_id"])
    return embedding


async def update_product_embedding(product_id: str, update_data: dict) -> bool:
    """Update product embedding"""
    db = get_database()
    collection = db["product_embeddings"]
    
    update_data["updated_at"] = datetime.utcnow()
    result = await collection.update_one(
        {"product_id": product_id},
        {"$set": update_data}
    )
    return result.modified_count > 0


# User Search Analytics Collection
async def create_search_analytics(analytics_data: dict) -> str:
    """Create a new search analytics record"""
    db = get_database()
    collection = db["user_search_analytics"]
    
    analytics_data["timestamp"] = datetime.utcnow()
    
    result = await collection.insert_one(analytics_data)
    return str(result.inserted_id)


async def get_user_search_history(user_id: str, limit: int = 10) -> List[dict]:
    """Get user's search history"""
    db = get_database()
    collection = db["user_search_analytics"]
    
    cursor = collection.find({"user_id": user_id}).sort("timestamp", -1).limit(limit)
    results = await cursor.to_list(length=limit)
    
    for result in results:
        result["_id"] = str(result["_id"])
    
    return results


# Image Metadata Collection
async def create_image_metadata(metadata: dict) -> str:
    """Create image metadata record"""
    db = get_database()
    collection = db["image_metadata"]
    
    metadata["created_at"] = datetime.utcnow()
    
    result = await collection.insert_one(metadata)
    return str(result.inserted_id)


async def get_image_metadata(image_url: str) -> Optional[dict]:
    """Get image metadata by URL"""
    db = get_database()
    collection = db["image_metadata"]
    
    metadata = await collection.find_one({"image_url": image_url})
    if metadata:
        metadata["_id"] = str(metadata["_id"])
    return metadata


# Analytics Events Collection
async def create_analytics_event(event_data: dict) -> str:
    """Create an analytics event"""
    db = get_database()
    collection = db["analytics_events"]
    
    event_data["timestamp"] = datetime.utcnow()
    
    result = await collection.insert_one(event_data)
    return str(result.inserted_id)


async def get_analytics_events(
    event_type: Optional[str] = None,
    user_id: Optional[str] = None,
    limit: int = 100
) -> List[dict]:
    """Get analytics events with optional filters"""
    db = get_database()
    collection = db["analytics_events"]
    
    query = {}
    if event_type:
        query["event_type"] = event_type
    if user_id:
        query["user_id"] = user_id
    
    cursor = collection.find(query).sort("timestamp", -1).limit(limit)
    results = await cursor.to_list(length=limit)
    
    for result in results:
        result["_id"] = str(result["_id"])
    
    return results


# ML Model Logs Collection
async def create_ml_model_log(log_data: dict) -> str:
    """Create ML model performance log"""
    db = get_database()
    collection = db["ml_model_logs"]
    
    log_data["timestamp"] = datetime.utcnow()
    
    result = await collection.insert_one(log_data)
    return str(result.inserted_id)


# Database Statistics
async def get_database_stats() -> dict:
    """Get database statistics"""
    db = get_database()
    
    stats = {
        "product_embeddings": await db["product_embeddings"].count_documents({}),
        "user_search_analytics": await db["user_search_analytics"].count_documents({}),
        "image_metadata": await db["image_metadata"].count_documents({}),
        "analytics_events": await db["analytics_events"].count_documents({}),
        "ml_model_logs": await db["ml_model_logs"].count_documents({}),
    }
    
    return stats

