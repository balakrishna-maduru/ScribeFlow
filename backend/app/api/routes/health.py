"""Health check endpoints."""

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class HealthResponse(BaseModel):
    """Health check response model."""
    status: str
    version: str
    timestamp: str


@router.get("/", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    from datetime import datetime
    from app.core.config import get_settings
    
    settings = get_settings()
    
    return HealthResponse(
        status="healthy",
        version=settings.app_version,
        timestamp=datetime.utcnow().isoformat()
    )


@router.get("/db")
async def database_health():
    """Database health check."""
    from app.core.database import engine
    
    try:
        async with engine.begin() as conn:
            await conn.execute("SELECT 1")
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "database": "disconnected", "error": str(e)}


@router.get("/ai")
async def ai_health():
    """AI services health check."""
    from app.services.ai_service import ai_service
    
    try:
        providers = ai_service.get_available_providers()
        return {
            "status": "healthy",
            "available_providers": providers,
            "total_providers": len(providers)
        }
    except Exception as e:
        return {"status": "unhealthy", "ai_services": "unavailable", "error": str(e)}
