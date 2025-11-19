"""
DupeFinder Backend API
FastAPI application for image-based fashion search
Created: November 9, 2025
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.core.database import db_manager
from app.api.routes import health, products, search, auth, admin
from app.api.routes import admin_new

# ============================================
# Application Lifespan Events
# ============================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events
    """
    # Startup
    print("[INFO] Starting DupeFinder API...")
    print("[INFO] Connecting to MongoDB...")
    
    try:
        db_manager.connect()
        print("[OK] MongoDB connected successfully")
        if db_manager.db is not None:
            print(f"[INFO] Database: {db_manager.db.name}")
            print(f"[INFO] Collections: {db_manager.db.list_collection_names()}")
    except Exception as e:
        print(f"[ERROR] Failed to connect to MongoDB: {e}")
        print("[WARNING] API starting without database connection")
    
    yield
    
    # Shutdown
    print("[INFO] Shutting down DupeFinder API...")
    db_manager.disconnect()
    print("[OK] MongoDB disconnected")


# ============================================
# Create FastAPI Application
# ============================================

app = FastAPI(
    title="DupeFinder API",
    description="Image-based search API for finding affordable alternatives to luxury fashion items",
    version="0.1.0 (40% Milestone)",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
    redirect_slashes=False  # Disable automatic trailing slash redirects to avoid CORS issues
)

# ============================================
# CORS Configuration
# ============================================

# Allow all origins for development (restrict in production)
# Note: Using ["*"] with allow_credentials=True is not allowed, so we list common ports
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001", 
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================
# Include Routers
# ============================================

app.include_router(health.router, tags=["Health"])
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
# Temporarily disabled to avoid route conflicts
# app.include_router(admin.router, prefix="/api/admin", tags=["Admin - Old"])
app.include_router(admin_new.router, prefix="/api/admin", tags=["Admin Dashboard"])
app.include_router(products.router, prefix="/api/products", tags=["Products"])
app.include_router(search.router, prefix="/api/search", tags=["Search"])

# Mount static files for product images
data_dir = Path(__file__).parent.parent.parent / "data"
app.mount("/data", StaticFiles(directory=str(data_dir)), name="data")

# ============================================
# Root Endpoint
# ============================================

@app.get("/")
async def root():
    """Root endpoint - API information"""
    return {
        "message": "DupeFinder API - Affordable Alternatives for Luxury Wearables",
        "version": "0.1.0",
        "status": "active",
        "docs": "/api/docs",
        "endpoints": {
            "health": "/health",
            "products": "/api/products",
            "search": "/api/search"
        }
    }

# ============================================
# Global Exception Handler
# ============================================

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Handle unexpected exceptions"""
    print(f"[ERROR] Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": str(exc),
            "type": type(exc).__name__
        }
    )


# ============================================
# Run Application
# ============================================

if __name__ == "__main__":
    import uvicorn
    
    print("=" * 60)
    print("DupeFinder API Server")
    print("=" * 60)
    print("\nStarting server...")
    print("Docs: http://localhost:8000/api/docs")
    print("API:  http://localhost:8000/api")
    print("\nPress CTRL+C to stop")
    print("=" * 60)
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # Auto-reload on code changes (dev only)
        log_level="info"
    )

