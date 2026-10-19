from fastapi import APIRouter
from app.core.config import settings
from app.schemas.health import HealthResponse

router = APIRouter(prefix="/api", tags=["Health"])


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Check API health status",
    description="Returns the current operational health status of the BlindPaper backend service.",
)
def get_health() -> HealthResponse:
    """Return application health status and metadata."""
    return HealthResponse(
        status="healthy",
        app_name=settings.app_name,
        version=settings.app_version,
    )
