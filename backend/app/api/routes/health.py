"""
Health check endpoint
"""

from datetime import datetime
from fastapi import APIRouter
from app.models.schemas import HealthResponse
from app.core.database import db_manager

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint
    
    Returns system status including database and ML engine status
    """
    # Check database
    db_status = db_manager.health_check()
    
    # Check ML engine (basic check for now)
    ml_status = {
        "status": "available",
        "model": "ResNet50",
        "embedding_dim": 2048
    }
    
    # Determine overall status
    overall_status = "healthy" if db_status["status"] == "connected" else "degraded"
    
    return HealthResponse(
        status=overall_status,
        timestamp=datetime.utcnow(),
        database=db_status,
        ml_engine=ml_status
    )


@router.get("/ping")
async def ping():
    """Simple ping endpoint for quick health check"""
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}








