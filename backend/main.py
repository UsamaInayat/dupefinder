"""
DupeFinder Backend - Main Application Entry Point

This is the main FastAPI application entry point.
Run with: uvicorn main:app --reload
"""

from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import logging

from app.core.database import connect_to_mongo, close_mongo_connection, check_connection, db_manager
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
        # Connect async MongoDB (for async routes)
        await connect_to_mongo()
        logger.info("✅ MongoDB Atlas connected successfully (async)")
        
        # Connect sync MongoDB (for admin dashboard routes)
        db_manager.connect()
        logger.info("✅ MongoDB Atlas connected successfully (sync)")
    except Exception as e:
        logger.error(f"❌ Failed to connect to MongoDB: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down DupeFinder API...")
    await close_mongo_connection()
    if db_manager.is_connected():
        db_manager.disconnect()
    logger.info("✅ MongoDB connections closed")


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
from app.api.routes import database, admin_new, products, auth, search

# Include routers
app.include_router(database.router)
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(admin_new.router, prefix="/api/admin", tags=["Admin Dashboard"])
app.include_router(products.router, prefix="/api/products", tags=["Products"])
app.include_router(search.router, prefix="/api/search", tags=["Search"])

# Serve product images (downloaded during scrape) at /data/product_images/
_data_dir = Path(__file__).resolve().parent.parent / "data"
_data_dir.mkdir(parents=True, exist_ok=True)
(_data_dir / "product_images").mkdir(parents=True, exist_ok=True)
app.mount("/data", StaticFiles(directory=str(_data_dir)), name="data")

# TODO: Add more routers as they are implemented
# from app.api.routes import users, reviews, analytics
# app.include_router(users.router)
# app.include_router(reviews.router)
# app.include_router(analytics.router)

