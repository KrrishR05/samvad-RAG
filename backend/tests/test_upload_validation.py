"""
Tests — Voice Upload Validation & Security
"""

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.config import get_settings
from app.main import app


def _minimal_wav_bytes(extra_len: int = 0) -> bytes:
    header = b"RIFF\x24\x00\x00\x00WAVEfmt "
    return header + (b"\x00" * extra_len)


@pytest.mark.asyncio
async def test_voice_upload_rejects_empty_file():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/api/v1/voice/query",
            files={"audio": ("empty.wav", b"", "audio/wav")},
        )
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "INPUT_VALIDATION_ERROR"


@pytest.mark.asyncio
async def test_voice_upload_rejects_non_audio_magic_bytes():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/api/v1/voice/query",
            files={"audio": ("evil.wav", b"<html><script>alert(1)</script></html>", "audio/wav")},
        )
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "INPUT_VALIDATION_ERROR"


@pytest.mark.asyncio
async def test_voice_upload_rejects_unsupported_mime():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/api/v1/voice/query",
            files={"audio": ("bad.txt", _minimal_wav_bytes(), "text/plain")},
        )
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "INPUT_VALIDATION_ERROR"


@pytest.mark.asyncio
async def test_voice_upload_rejects_oversized_payload(monkeypatch):
    settings = get_settings()
    monkeypatch.setattr(settings, "max_audio_upload_bytes", 128)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/api/v1/voice/query",
            files={"audio": ("big.wav", _minimal_wav_bytes(256), "audio/wav")},
        )
    assert resp.status_code == 413
    assert resp.json()["error"]["code"] == "PAYLOAD_TOO_LARGE"


@pytest.mark.asyncio
async def test_voice_upload_accepts_valid_wav_and_returns_not_implemented(monkeypatch):
    from app.pipeline.runtime import get_runtime
    runtime = get_runtime()
    monkeypatch.setattr(runtime, "speech_service", None)
    monkeypatch.setattr(runtime.orchestrator, "speech_service", None)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/api/v1/voice/query",
            files={"audio": ("ok.wav", _minimal_wav_bytes(32), "audio/wav")},
        )
    assert resp.status_code == 200
    assert resp.json()["status"] == "not_implemented"

