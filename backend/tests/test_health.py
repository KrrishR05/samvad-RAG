"""
Tests — Health endpoint & Request Correlation
"""

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_health_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/health")

    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"
    assert data["service"] == "samvad-api"
    assert "version" in data
    assert "environment" in data
    assert "x-request-id" in resp.headers


@pytest.mark.asyncio
async def test_health_echoes_valid_request_id():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/health", headers={"X-Request-ID": "req-abc-123"})

    assert resp.status_code == 200
    assert resp.headers.get("x-request-id") == "req-abc-123"
