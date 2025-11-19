"""
DupeFinder Backend - Database Connection

This module handles MongoDB Atlas connection and database operations.
Supports both async (Motor) and sync (PyMongo) connections.
"""

from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient
from pymongo.database import Database
from pymongo.collection import Collection
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from typing import Optional
import logging
import os
from dotenv import load_dotenv

from app.core.config import settings

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

# ============================================
# Async MongoDB Atlas Connection (Motor)
# ============================================

# Global async database client
client: Optional[AsyncIOMotorClient] = None
database = None


async def connect_to_mongo():
    """
    Create async database connection to MongoDB Atlas using Motor
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
        
        logger.info(f"Successfully connected to MongoDB Atlas: {settings.MONGO_DB_NAME}")
        return database
        
    except (ConnectionFailure, ServerSelectionTimeoutError) as e:
        logger.error(f"Failed to connect to MongoDB Atlas: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error connecting to MongoDB: {e}")
        raise


async def close_mongo_connection():
    """
    Close async database connection
    """
    global client
    
    if client:
        client.close()
        logger.info("MongoDB connection closed")


def get_database():
    """
    Get async database instance
    """
    if database is None:
        raise RuntimeError("Database not initialized. Call connect_to_mongo() first.")
    return database


async def check_connection() -> bool:
    """
    Check if async database connection is active
    """
    try:
        if client is None:
            return False
        await client.admin.command('ping')
        return True
    except Exception:
        return False


# ============================================
# Sync MongoDB Connection (PyMongo) - For Admin Dashboard
# ============================================

# Collection names
PRODUCTS_COLLECTION = "products"
SEARCH_HISTORY_COLLECTION = "search_history"
USERS_COLLECTION = "users"
OTPS_COLLECTION = "otps"
REFRESH_TOKENS_COLLECTION = "refresh_tokens"


class DatabaseManager:
    """
    Singleton database manager for sync MongoDB connections (used by admin dashboard)
    """
    
    def __init__(self):
        self.client: Optional[MongoClient] = None
        self.db: Optional[Database] = None
        self._connected = False
    
    def connect(self, uri: str = None, db_name: str = None):
        """
        Connect to MongoDB (sync connection)
        
        Args:
            uri: MongoDB connection URI (defaults to settings.MONGO_URI)
            db_name: Database name (defaults to settings.MONGO_DB_NAME)
        """
        if self._connected:
            logger.info("Already connected to MongoDB")
            return
        
        uri = uri or settings.MONGO_URI
        db_name = db_name or settings.MONGO_DB_NAME
        
        try:
            # Create client with timeout
            self.client = MongoClient(
                uri,
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=10000,
                socketTimeoutMS=10000
            )
            
            # Test connection
            self.client.admin.command('ping')
            
            # Get database
            self.db = self.client[db_name]
            self._connected = True
            
            logger.info(f"Connected to MongoDB at {uri}")
            logger.info(f"Using database: {db_name}")
            
        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            self._connected = False
            raise
    
    def disconnect(self):
        """Disconnect from MongoDB"""
        if self.client:
            self.client.close()
            self._connected = False
            logger.info("Disconnected from MongoDB")
    
    def is_connected(self) -> bool:
        """Check if connected to database"""
        return self._connected
    
    def get_collection(self, collection_name: str) -> Collection:
        """
        Get a collection from the database
        
        Args:
            collection_name: Name of the collection
            
        Returns:
            MongoDB collection object
        """
        if not self._connected or self.db is None:
            raise RuntimeError("Not connected to database. Call connect() first.")
        
        return self.db[collection_name]
    
    def get_products_collection(self) -> Collection:
        """Get the products collection"""
        return self.get_collection(PRODUCTS_COLLECTION)
    
    def get_search_history_collection(self) -> Collection:
        """Get the search history collection"""
        return self.get_collection(SEARCH_HISTORY_COLLECTION)
    
    def get_users_collection(self) -> Collection:
        """Get the users collection"""
        return self.get_collection(USERS_COLLECTION)
    
    def get_otps_collection(self) -> Collection:
        """Get the OTPs collection"""
        return self.get_collection(OTPS_COLLECTION)
    
    def get_refresh_tokens_collection(self) -> Collection:
        """Get the refresh tokens collection"""
        return self.get_collection(REFRESH_TOKENS_COLLECTION)
    
    def setup_auth_indexes(self):
        """
        Create indexes for authentication collections
        - TTL index on OTPs (expire after expiry time)
        - TTL index on refresh tokens (expire after expiry time)
        - Unique index on user emails
        """
        if not self._connected:
            raise RuntimeError("Not connected to database")
        
        try:
            # Users collection - unique email index
            users = self.get_users_collection()
            users.create_index("email", unique=True)
            logger.info("Created unique index on users.email")
            
            # OTPs collection - TTL index (auto-delete expired OTPs)
            otps = self.get_otps_collection()
            otps.create_index("expires_at", expireAfterSeconds=0)
            otps.create_index("email")
            logger.info("Created TTL index on otps.expires_at")
            
            # Refresh tokens collection - TTL index
            tokens = self.get_refresh_tokens_collection()
            tokens.create_index("expires_at", expireAfterSeconds=0)
            tokens.create_index("user_id")
            logger.info("Created TTL index on refresh_tokens.expires_at")
            
        except Exception as e:
            logger.error(f"Failed to create indexes: {e}")
            raise
    
    def health_check(self) -> dict:
        """
        Perform health check on database connection
        
        Returns:
            Dictionary with health status
        """
        if not self._connected:
            return {
                "status": "disconnected",
                "database": None,
                "products_count": 0
            }
        
        try:
            # Ping database
            self.client.admin.command('ping')
            
            # Get product count
            products = self.get_products_collection()
            product_count = products.count_documents({})
            
            return {
                "status": "connected",
                "database": self.db.name,
                "products_count": product_count,
                "collections": self.db.list_collection_names()
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "database": self.db.name if self.db else None
            }


# ============================================
# Global Database Manager Instance (Sync)
# ============================================

db_manager = DatabaseManager()


# ============================================
# Helper Functions (Sync - for Admin Dashboard)
# ============================================

def get_db() -> Database:
    """
    Dependency function to get database instance (sync)
    Use with FastAPI Depends()
    
    Returns:
        MongoDB database instance
    """
    if not db_manager.is_connected():
        raise RuntimeError("Database not connected")
    return db_manager.db


def get_products_collection() -> Collection:
    """
    Get products collection (sync)
    
    Returns:
        Products collection
    """
    return db_manager.get_products_collection()


def get_search_history_collection() -> Collection:
    """
    Get search history collection (sync)
    
    Returns:
        Search history collection
    """
    return db_manager.get_search_history_collection()


def get_users_collection() -> Collection:
    """
    Get users collection (sync)
    
    Returns:
        Users collection
    """
    return db_manager.get_users_collection()


def get_otps_collection() -> Collection:
    """
    Get OTPs collection (sync)
    
    Returns:
        OTPs collection
    """
    return db_manager.get_otps_collection()


def get_refresh_tokens_collection() -> Collection:
    """
    Get refresh tokens collection (sync)
    
    Returns:
        Refresh tokens collection
    """
    return db_manager.get_refresh_tokens_collection()
