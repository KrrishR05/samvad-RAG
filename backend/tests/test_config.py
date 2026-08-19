"""
Tests — Configuration
"""

from app.core.config import Settings, Environment


def test_default_settings():
    """Settings should load with sensible defaults."""
    settings = Settings()
    assert settings.environment == Environment.DEVELOPMENT
    assert settings.app_name == "samvad-api"
    assert settings.backend_port == 8000
    assert settings.retrieval_top_k == 10
    assert settings.rerank_top_k == 5


def test_cors_origins_parsed():
    settings = Settings(cors_origins="http://a.com, http://b.com")
    origins = settings.cors_origin_list
    assert origins == ["http://a.com", "http://b.com"]
