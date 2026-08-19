"""
SAMVAD Configuration System

Centralized, typed configuration using pydantic-settings.
All configuration values are loaded from environment variables
with sensible defaults for development.
"""

from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic_settings import BaseSettings
from pydantic import Field


class Environment(str, Enum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    For local development, create a `.env` file in the backend/ directory
    based on `.env.example` in the project root.
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
    backend_port: int = Field(default=8000, description="Bind port")
    cors_origins: str = Field(
        default="http://localhost:3000",
        description="Comma-separated allowed CORS origins",
    )

    # --- Speech-to-Text ---
    # TODO: Populate with real API keys when integrating Sarvam / ElevenLabs
    sarvam_api_key: Optional[str] = Field(
        default=None,
        description="Sarvam AI API key for Indic STT",
    )
    elevenlabs_api_key: Optional[str] = Field(
        default=None,
        description="ElevenLabs API key (alternative STT provider)",
    )
    stt_provider: str = Field(
        default="sarvam",
        description="Active STT provider: 'sarvam' | 'elevenlabs'",
    )

    # --- LLM ---
    # TODO: Configure when integrating the generation module
    llm_api_key: Optional[str] = Field(
        default=None,
        description="API key for the LLM provider",
    )
    llm_model: str = Field(
        default="",
        description="LLM model identifier",
    )

    # --- Embeddings ---
    # TODO: Configure when integrating the embedding module
    embedding_model: str = Field(
        default="",
        description="Embedding model identifier",
    )

    # --- Vector Database ---
    # TODO: Configure when integrating the vector index
    vector_db_path: str = Field(
        default="./data/vector_index",
        description="Path to the local vector index directory",
    )

    # --- Ingestion ---
    # TODO: Configure when integrating MSMARCO-XI ingestion
    dataset_cache_dir: str = Field(
        default="./data/datasets",
        description="Cache directory for downloaded datasets",
    )

    # --- Retrieval ---
    retrieval_top_k: int = Field(
        default=10,
        description="Number of candidates from initial retrieval",
    )
    rerank_top_k: int = Field(
        default=5,
        description="Number of candidates after reranking",
    )

    # --- Pipeline ---
    pipeline_timeout_seconds: float = Field(
        default=30.0,
        description="Maximum total pipeline execution time in seconds",
    )
    stage_timeout_seconds: float = Field(
        default=10.0,
        description="Maximum execution time per pipeline stage in seconds",
    )
    max_retries: int = Field(
        default=2,
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

    @property
    def cors_origin_list(self) -> list[str]:
        """Parse comma-separated CORS origins into a list."""
        return [origin.strip() for origin in self.cors_origins.split(",")]


# Singleton instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Return the application settings singleton."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
