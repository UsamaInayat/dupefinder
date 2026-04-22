"""
DupeFinder Backend API
FastAPI application for image-based fashion search
Created: November 9, 2025
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import sys
import re
import mimetypes
from pathlib import Path
import os

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.core.database import db_manager
from app.api.routes import health, products, search, auth, admin
from app.api.routes import admin_new
from app.api.routes import community
from app.api.routes import user_data

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

    # Pre-load FashionCLIP + FAISS indices in a background thread so startup
    # never blocks the event loop — API is responsive immediately on port 8000.
    import threading

    def _load_fashionclip():
        try:
            from app.api.routes.search import init_search_resources
            print("[INFO] Background: loading FashionCLIP + FAISS indices...")
            init_search_resources()
            print("[OK] FashionCLIP search ready")
        except Exception as e:
            print(f"[WARNING] FashionCLIP pre-load failed (will lazy-load on first request): {e}")

    threading.Thread(target=_load_fashionclip, daemon=True).start()

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
# CORS configuration - allow all localhost origins for development
# In production, restrict to specific origins
def is_localhost_origin(origin: str) -> bool:
    """Check if origin is localhost or 127.0.0.1"""
    if not origin:
        return False
    pattern = r'^https?://(localhost|127\.0\.0\.1)(:\d+)?$'
    return bool(re.match(pattern, origin))

# CORS - Allow all localhost origins for development (including Flutter web dynamic ports)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ],
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1)(:\d+)?$",  # Allow any localhost port (for Flutter web)
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
    expose_headers=["*"],
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
app.include_router(community.router, prefix="/api/community", tags=["Community"])
app.include_router(user_data.router, prefix="/api/user-data", tags=["User Data"])

# Mount static files for product images
# Ensure Windows serves modern image extensions with correct MIME type.
mimetypes.add_type("image/webp", ".webp")
mimetypes.add_type("image/avif", ".avif")
# Product images and other static assets live under `/data` by default:
#   <repo>/data
# In deployed environments (Railway volume), override with DATA_DIR=/data (or any mount path).
_data_dir_env = os.getenv("DATA_DIR", "").strip()
if _data_dir_env:
    data_dir = Path(_data_dir_env)
else:
    data_dir = Path(__file__).parent.parent.parent / "data"

data_dir.mkdir(parents=True, exist_ok=True)
app.mount("/data", StaticFiles(directory=str(data_dir)), name="data")

# ============================================
# CORS Preflight Handler
# ============================================

@app.options("/{full_path:path}")
async def options_handler(request: Request, full_path: str):
    """Handle CORS preflight requests for all localhost origins (including Flutter web)"""
    origin = request.headers.get("origin", "")
    # Allow any localhost or 127.0.0.1 origin (including dynamic ports like Flutter web)
    if is_localhost_origin(origin):
        return Response(
            status_code=200,
            headers={
                "Access-Control-Allow-Origin": origin,
                "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS, PATCH",
                "Access-Control-Allow-Headers": "*",
                "Access-Control-Allow-Credentials": "true",
                "Access-Control-Max-Age": "3600",
            }
        )
    return Response(status_code=200)

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
    import traceback
    error_trace = traceback.format_exc()
    print(f"[ERROR] Unhandled exception: {exc}")
    print(f"[ERROR] Traceback: {error_trace}")
    return JSONResponse(
        status_code=500,
        headers={
            "Access-Control-Allow-Origin": request.headers.get("origin", "*"),
            "Access-Control-Allow-Credentials": "true",
        },
        content={
            "error": "Internal server error",
            "message": str(exc),
            "type": type(exc).__name__,
            "traceback": error_trace if app.debug else None
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

