"""
SAMVAD Configuration System

Centralized, typed configuration using pydantic-settings.
All configuration values are loaded from environment variables
with sensible defaults for development.
"""

from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings


class Environment(str, Enum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class STTProvider(str, Enum):
    SARVAM = "sarvam"
    ELEVENLABS = "elevenlabs"
    GEMINI = "gemini"


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    For local development, create a `.env` file in the project root or backend/
    directory based on `.env.example`.
    """

    # --- Application ---
    environment: Environment = Field(
        default=Environment.DEVELOPMENT,
        description="Runtime environment",
    )
    app_name: str = Field(default="samvad-api", description="Service name")
    app_version: str = Field(default="0.1.0", description="API version")
    debug: bool = Field(default=False, description="Enable debug mode")

    # --- Server ---
    backend_host: str = Field(default="0.0.0.0", description="Bind host")
    backend_port: int = Field(default=8000, ge=1, le=65535, description="Bind port")
    cors_origins: str = Field(
        default="http://localhost:3000",
        description="Comma-separated allowed CORS origins",
    )

    # --- Upload Limits ---
    max_audio_upload_bytes: int = Field(
        default=10 * 1024 * 1024,  # 10 MB
        gt=0,
        description="Maximum allowed voice audio upload size in bytes",
    )

    # --- Speech-to-Text ---
    sarvam_api_key: Optional[str] = Field(
        default=None,
        description="Sarvam AI API key for Indic STT",
    )
    elevenlabs_api_key: Optional[str] = Field(
        default=None,
        description="ElevenLabs API key (alternative STT provider)",
    )
    stt_provider: STTProvider = Field(
        default=STTProvider.SARVAM,
        description="Active STT provider: 'sarvam' | 'elevenlabs'",
    )

    # --- LLM ---
    llm_provider: str = Field(
        default="",
        description="LLM provider identifier: openai, ollama, or gemini",
    )
    llm_base_url: str = Field(
        default="",
        description="Base URL for OpenAI-compatible, vLLM, or Ollama LLM endpoints",
    )
    llm_api_key: Optional[str] = Field(
        default=None,
        description="API key for the LLM provider",
    )
    llm_model: str = Field(
        default="",
        description="LLM model identifier",
    )

    # --- Embeddings ---
    embedding_provider: str = Field(
        default="local_tfidf_svd",
        description="Embedding provider: local_tfidf_svd or openai_compatible",
    )
    embedding_base_url: str = Field(
        default="",
        description="Base URL for OpenAI-compatible or Ollama embedding endpoints",
    )
    embedding_model: str = Field(
        default="",
        description="Embedding model identifier",
    )

    # --- Storage & Vector Database ---
    sqlite_db_path: str = Field(
        default="./data/samvad.db",
        description="Path to the local SQLite database for document and chunk metadata",
    )
    vector_db_path: str = Field(
        default="./data/vector_index",
        description="Path to the local vector index directory",
    )
    max_document_upload_bytes: int = Field(
        default=10 * 1024 * 1024,
        gt=0,
        description="Maximum document upload size in bytes",
    )

    # --- Ingestion ---
    dataset_cache_dir: str = Field(
        default="./data/datasets",
        description="Cache directory for downloaded datasets",
    )

    # --- Retrieval ---
    retrieval_top_k: int = Field(
        default=10,
        ge=1,
        description="Number of candidates from initial retrieval",
    )
    rerank_top_k: int = Field(
        default=5,
        ge=1,
        description="Number of candidates after reranking",
    )

    # --- Pipeline ---
    pipeline_timeout_seconds: float = Field(
        default=30.0,
        gt=0.0,
        description="Maximum total pipeline execution time in seconds",
    )
    stage_timeout_seconds: float = Field(
        default=10.0,
        gt=0.0,
        description="Maximum execution time per pipeline stage in seconds",
    )
    max_retries: int = Field(
        default=2,
        ge=0,
        description="Maximum retries for recoverable stage failures",
    )

    # --- Logging ---
    log_level: str = Field(
        default="INFO",
        description="Logging level: DEBUG, INFO, WARNING, ERROR, CRITICAL",
    )

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
    }

    @model_validator(mode="after")
    def _validate_cross_fields(self) -> "Settings":
        if self.stage_timeout_seconds > self.pipeline_timeout_seconds:
            raise ValueError(
                "stage_timeout_seconds cannot exceed pipeline_timeout_seconds."
            )
        if self.environment == Environment.PRODUCTION and "*" in self.cors_origin_list:
            raise ValueError(
                "Wildcard CORS origin '*' is not permitted in production."
            )
        return self

    @property
    def cors_origin_list(self) -> list[str]:
        """Parse comma-separated CORS origins into a non-empty list."""
        return [
            origin.strip()
            for origin in self.cors_origins.split(",")
            if origin.strip()
        ]


# Singleton instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Return the application settings singleton."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
