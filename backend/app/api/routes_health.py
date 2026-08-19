"""
SAMVAD API — Health Routes
"""

from __future__ import annotations

from fastapi import APIRouter

from app.core.config import get_settings
from app.schemas.response import HealthResponse

router = APIRouter(tags=["health"])


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Service health check",
)
async def health_check() -> HealthResponse:
    settings = get_settings()
    return HealthResponse(
        status="healthy",
        service=settings.app_name,
        version=settings.app_version,
        environment=settings.environment.value,
    )
