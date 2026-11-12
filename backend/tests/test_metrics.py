"""
Tests — Analytics MetricsStore & Endpoints
"""

import pytest
from httpx import ASGITransport, AsyncClient

from app.analytics.metrics import MetricsStore
from app.main import app
from app.schemas.analytics import LatencyRecord


def test_metrics_store_bounded_capacity():
    store = MetricsStore(max_records=3)
    for i in range(5):
        store.record(LatencyRecord(request_id=f"r-{i}", total_ms=float(i * 10)))

    assert store.total_requests == 3
    stats = store.get_latency_stats()
    assert stats.overall is not None
    assert stats.overall.min == 20.0
    assert stats.overall.max == 40.0


def test_metrics_store_empty_and_clear():
    store = MetricsStore()
    assert store.get_summary().total_requests == 0
    store.record(LatencyRecord(request_id="r-1", retrieval_ms=12.0, total_ms=25.0))
    assert store.get_summary().total_requests == 1
    store.clear()
    assert store.total_requests == 0


@pytest.mark.asyncio
async def test_analytics_endpoints_empty():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        summary = await client.get("/api/v1/analytics/summary")
        latency = await client.get("/api/v1/analytics/latency")

    assert summary.status_code == 200
    assert summary.json()["total_requests"] == 0
    assert latency.status_code == 200
    assert latency.json()["total_records"] == 0

