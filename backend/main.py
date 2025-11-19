"""
DupeFinder Backend - Main Application Entry Point

This is the main FastAPI application entry point.
Run with: uvicorn main:app --reload
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from app.core.database import connect_to_mongo, close_mongo_connection, check_connection
from app.core.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events
    """
    # Startup
    logger.info("🚀 Starting DupeFinder API...")
    try:
        await connect_to_mongo()
        logger.info("✅ MongoDB Atlas connected successfully")
    except Exception as e:
        logger.error(f"❌ Failed to connect to MongoDB: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down DupeFinder API...")
    await close_mongo_connection()
    logger.info("✅ MongoDB connection closed")


# Create FastAPI app instance
app = FastAPI(
    title="DupeFinder API",
    description="API for finding affordable alternatives to luxury fashion items",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "message": "DupeFinder API is running",
        "version": "1.0.0",
        "status": "healthy",
        "database": "MongoDB Atlas"
    }


@app.get("/health")
async def health_check():
    """Detailed health check"""
    db_status = "connected" if await check_connection() else "disconnected"
    
    return {
        "status": "healthy",
        "database": db_status,
        "database_type": "MongoDB Atlas",
        "ml_engine": "not_loaded"
    }

# Import and include routers
from app.api.routes import database

# Include routers
app.include_router(database.router)

# TODO: Add more routers as they are implemented
# from app.api.routes import products, search, users, reviews, analytics
# app.include_router(products.router)
# app.include_router(search.router)
# app.include_router(users.router)
# app.include_router(reviews.router)
# app.include_router(analytics.router)

