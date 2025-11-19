"""
DupeFinder Backend - Database Routes

API endpoints for database operations and health checks.
"""

from fastapi import APIRouter, HTTPException
from app.core.database import check_connection, get_database
from app.services.mongodb_service import get_database_stats

router = APIRouter(prefix="/api/database", tags=["database"])


@router.get("/health")
async def database_health():
    """Check database connection health"""
    is_connected = await check_connection()
    
    if not is_connected:
        raise HTTPException(status_code=503, detail="Database connection failed")
    
    return {
        "status": "connected",
        "database": "MongoDB Atlas",
        "message": "Database is healthy"
    }


@router.get("/stats")
async def database_stats():
    """Get database statistics"""
    try:
        is_connected = await check_connection()
        if not is_connected:
            raise HTTPException(status_code=503, detail="Database not connected")
        
        stats = await get_database_stats()
        
        return {
            "status": "success",
            "database": "MongoDB Atlas",
            "collections": stats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching stats: {str(e)}")


@router.get("/collections")
async def list_collections():
    """List all collections in the database"""
    try:
        is_connected = await check_connection()
        if not is_connected:
            raise HTTPException(status_code=503, detail="Database not connected")
        
        db = get_database()
        collections = await db.list_collection_names()
        
        return {
            "status": "success",
            "collections": collections,
            "count": len(collections)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing collections: {str(e)}")

