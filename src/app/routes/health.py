"""Health check endpoints."""

from fastapi import APIRouter

from app.schema.health import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Check application health.

    Returns status of the application.
    """
    return HealthResponse(status="ok")
