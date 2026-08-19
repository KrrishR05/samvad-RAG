"""
Tests — Error Handling
"""

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.errors import (
    SamvadError,
    SpeechProcessingError,
    RetrievalError,
    GenerationError,
    GuardrailError,
    ConfigurationError,
    PipelineTimeoutError,
    InputValidationError,
)


def test_base_error_defaults():
    err = SamvadError()
    assert err.code == "INTERNAL_ERROR"
    assert err.status_code == 500


def test_speech_error():
    err = SpeechProcessingError(request_id="r1")
    assert err.code == "SPEECH_PROCESSING_ERROR"
    assert err.status_code == 502
    assert err.request_id == "r1"


def test_retrieval_error():
    err = RetrievalError()
    assert err.code == "RETRIEVAL_ERROR"


def test_generation_error():
    err = GenerationError()
    assert err.code == "GENERATION_ERROR"


def test_guardrail_error():
    err = GuardrailError()
    assert err.code == "GUARDRAIL_ERROR"
    assert err.status_code == 422


def test_configuration_error():
    err = ConfigurationError()
    assert err.code == "CONFIGURATION_ERROR"


def test_timeout_error():
    err = PipelineTimeoutError()
    assert err.code == "PIPELINE_TIMEOUT"
    assert err.status_code == 504


def test_input_validation_error():
    err = InputValidationError()
    assert err.code == "INPUT_VALIDATION_ERROR"
    assert err.status_code == 400


@pytest.mark.asyncio
async def test_query_endpoint_returns_not_implemented():
    """Query endpoint should return not_implemented when pipeline is not wired."""
    from app.main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/api/v1/query",
            json={"query": "What is SAMVAD?"},
        )

    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "not_implemented"
    assert "request_id" in data
