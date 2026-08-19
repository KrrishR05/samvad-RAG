"""
SAMVAD API — Analytics Routes
"""

from __future__ import annotations

from fastapi import APIRouter

from app.analytics.metrics import get_metrics_store
from app.schemas.analytics import AnalyticsSummaryResponse, LatencyStatsResponse

router = APIRouter(prefix="/api/v1", tags=["analytics"])


@router.get(
    "/analytics/summary",
    response_model=AnalyticsSummaryResponse,
    summary="Get analytics summary",
)
async def get_analytics_summary() -> AnalyticsSummaryResponse:
    """Return an aggregated analytics summary."""
    store = get_metrics_store()
    return store.get_summary()


@router.get(
    "/analytics/latency",
    response_model=LatencyStatsResponse,
    summary="Get detailed latency statistics",
)
async def get_latency_stats() -> LatencyStatsResponse:
    """Return detailed per-stage latency statistics."""
    store = get_metrics_store()
    return store.get_latency_stats()
