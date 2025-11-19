"""
DupeFinder Backend - Database Connection

This module handles MongoDB Atlas connection and database operations.
"""

from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from typing import Optional
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)

# Global database client
client: Optional[AsyncIOMotorClient] = None
database = None


async def connect_to_mongo():
    """
    Create database connection to MongoDB Atlas
    """
    global client, database
    
    try:
        # Create Motor client for async operations
        client = AsyncIOMotorClient(
            settings.MONGO_URI,
            serverSelectionTimeoutMS=5000,  # 5 second timeout
            maxPoolSize=50,
            minPoolSize=10
        )
        
        # Test connection
        await client.admin.command('ping')
        
        # Get database
        database = client[settings.MONGO_DB_NAME]
        
        logger.info(f"✅ Successfully connected to MongoDB Atlas: {settings.MONGO_DB_NAME}")
        return database
        
    except (ConnectionFailure, ServerSelectionTimeoutError) as e:
        logger.error(f"❌ Failed to connect to MongoDB Atlas: {e}")
        raise
    except Exception as e:
        logger.error(f"❌ Unexpected error connecting to MongoDB: {e}")
        raise


async def close_mongo_connection():
    """
    Close database connection
    """
    global client
    
    if client:
        client.close()
        logger.info("MongoDB connection closed")


def get_database():
    """
    Get database instance
    """
    if database is None:
        raise RuntimeError("Database not initialized. Call connect_to_mongo() first.")
    return database


async def check_connection() -> bool:
    """
    Check if database connection is active
    """
    try:
        if client is None:
            return False
        await client.admin.command('ping')
        return True
    except Exception:
        return False

