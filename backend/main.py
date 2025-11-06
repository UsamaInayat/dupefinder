"""
DupeFinder Backend - Main Application Entry Point

This is the main FastAPI application entry point.
Run with: uvicorn main:app --reload
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Create FastAPI app instance
app = FastAPI(
    title="DupeFinder API",
    description="API for finding affordable alternatives to luxury fashion items",
    version="1.0.0"
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
        "status": "healthy"
    }

@app.get("/health")
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "database": "not_connected",
        "ml_engine": "not_loaded"
    }

# TODO: Import and include routers
# from app.api.routes import products, search, users, reviews, analytics
# app.include_router(products.router)
# app.include_router(search.router)
# app.include_router(users.router)
# app.include_router(reviews.router)
# app.include_router(analytics.router)

