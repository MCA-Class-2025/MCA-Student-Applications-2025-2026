import httpx
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.config import settings
from app.database.session import get_db
from app.schemas.health import SystemHealthResponse
from app.services.student_service import student_service
from app.utils.logger import logger

router = APIRouter(prefix="/health", tags=["Health"])

@router.get("", response_model=SystemHealthResponse)
async def check_health(db: Session = Depends(get_db)):
    # DB Check
    db_connected = False
    try:
        db.execute(text("SELECT 1"))
        db_connected = True
    except Exception as e:
        logger.error(f"Database health check failed: {e}")

    # Ollama Check
    ollama_connected = False
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.get(f"{settings.OLLAMA_BASE_URL}/api/tags")
            if resp.status_code == 200:
                ollama_connected = True
    except Exception as e:
        logger.warning(f"Ollama health check warning: {e}")

    return SystemHealthResponse(
        status="healthy" if (db_connected and student_service.is_loaded()) else "degraded",
        app_name=settings.APP_NAME,
        version="1.0.0",
        database_connected=db_connected,
        ollama_connected=ollama_connected,
        ollama_model=settings.OLLAMA_MODEL,
        system_info={
            "environment": settings.APP_ENV,
            "max_upload_size_mb": settings.MAX_UPLOAD_SIZE_MB,
            "allowed_extensions": settings.ALLOWED_EXTENSIONS,
            "student_dataset_loaded": student_service.is_loaded(),
            "student_records_count": student_service.get_total_count(),
        }
    )
