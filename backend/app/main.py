"""
SAMVAD — Adaptive Voice-Enabled RAG
Main FastAPI Application

This is the entry point for the backend server.
Run with:  uvicorn app.main:app --reload
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes_analytics import router as analytics_router
from app.api.routes_documents import router as documents_router
from app.api.routes_health import router as health_router
from app.api.routes_query import router as query_router
from app.api.routes_voice import router as voice_router
from app.core.config import get_settings
from app.core.errors import register_exception_handlers
from app.core.logging import RequestIdMiddleware, get_logger, setup_logging
from app.pipeline.runtime import get_runtime

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan: startup and shutdown hooks."""
    setup_logging()
    settings = get_settings()
    logger.info(
        "SAMVAD API starting — env=%s, version=%s",
        settings.environment.value,
        settings.app_version,
    )
    await get_runtime().ensure_indexes_ready()
    yield
    logger.info("SAMVAD API shutting down.")


def create_app() -> FastAPI:
    """Application factory."""
    settings = get_settings()

    app = FastAPI(
        title="SAMVAD API",
        description="Adaptive Voice-Enabled RAG — Speak. Retrieve. Ground.",
        version=settings.app_version,
        lifespan=lifespan,
    )

    # --- Request Correlation ---
    app.add_middleware(RequestIdMiddleware)

    # --- CORS ---
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization", "X-Request-ID"],
    )

    # --- Exception handlers ---
    register_exception_handlers(app)

    # --- Routers ---
    app.include_router(health_router)
    app.include_router(query_router)
    app.include_router(voice_router)
    app.include_router(analytics_router)
    app.include_router(documents_router)

    return app


app = create_app()
