

from fastapi import APIRouter, Request
from datetime import datetime
from models.schemas import HealthResponse

router = APIRouter()

@router.get("/health", response_model=HealthResponse)
async def health_check(request: Request):

    try:

        vector_service = getattr(request.app.state, 'vector_service', None)
        chat_service = getattr(request.app.state, 'chat_service', None)

        services = {
            "vector_store": "healthy" if vector_service else "unavailable",
            "chat_service": "healthy" if chat_service else "unavailable",
            "database": "healthy"
        }

        status = "healthy" if all(s == "healthy" for s in services.values()) else "degraded"

        return HealthResponse(
            status=status,
            timestamp=datetime.utcnow(),
            version="1.0.0",
            services=services
        )
    except Exception as e:
        return HealthResponse(
            status="unhealthy",
            timestamp=datetime.utcnow(),
            version="1.0.0",
            services={"error": str(e)}
        )