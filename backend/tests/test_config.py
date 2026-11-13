"""
Tests — Configuration
"""

import pytest
from pydantic import ValidationError

from app.core.config import Environment, STTProvider, Settings


def test_default_settings():
    """Settings should load with sensible defaults."""
    settings = Settings(_env_file=None)
    assert settings.environment == Environment.DEVELOPMENT
    assert settings.app_name == "samvad-api"
    assert settings.backend_port == 8000
    assert settings.retrieval_top_k == 10
    assert settings.rerank_top_k == 5
    assert settings.stt_provider == STTProvider.SARVAM
    assert settings.max_audio_upload_bytes == 10 * 1024 * 1024


def test_cors_origins_parsed():
    settings = Settings(cors_origins="http://a.com, http://b.com, ")
    assert settings.cors_origin_list == ["http://a.com", "http://b.com"]


def test_stage_timeout_cannot_exceed_pipeline_timeout():
    with pytest.raises(ValidationError, match="stage_timeout_seconds"):
        Settings(pipeline_timeout_seconds=5.0, stage_timeout_seconds=10.0)


def test_wildcard_cors_rejected_in_production():
    with pytest.raises(ValidationError, match="Wildcard CORS"):
        Settings(environment=Environment.PRODUCTION, cors_origins="*")


def test_invalid_stt_provider_rejected():
    with pytest.raises(ValidationError):
        Settings(stt_provider="unknown_provider")
