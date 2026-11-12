"""
SAMVAD Pipeline Orchestrator

Coordinates the execution of the full query pipeline by delegating to
injected service implementations and registered retrieval strategies.

The orchestrator manages state transitions, timing, retries, and error
handling while domain logic lives in the service implementations.
"""

from __future__ import annotations

import logging
from typing import Optional

from app.analytics.metrics import MetricsStore, get_metrics_store
from app.core.logging import sanitize_request_id
from app.pipeline.interfaces import (
    AnswerGenerator,
    GuardrailService,
    QueryAnalyzer,
    QueryRouter,
    Reranker,
    Retriever,
    SpeechService,
)
from app.schemas.response import QueryResponse, QueryStatus

logger = logging.getLogger(__name__)


class PipelineOrchestrator:
    """
    Orchestrates the SAMVAD pipeline.

    All service dependencies are optional. When required services are None,
    the orchestrator returns a structured `not_implemented` response instead
    of faking functionality.
    """

    def __init__(
        self,
        *,
        speech_service: Optional[SpeechService] = None,
        query_analyzer: Optional[QueryAnalyzer] = None,
        retriever: Optional[Retriever] = None,
        retrievers: Optional[dict[str, Retriever]] = None,
        default_retriever_key: str = "hybrid",
        reranker: Optional[Reranker] = None,
        generator: Optional[AnswerGenerator] = None,
        input_guard: Optional[GuardrailService] = None,
        relevance_guard: Optional[GuardrailService] = None,
        confidence_guard: Optional[GuardrailService] = None,
        grounding_guard: Optional[GuardrailService] = None,
        query_router: Optional[QueryRouter] = None,
        metrics_store: Optional[MetricsStore] = None,
    ) -> None:
        self.speech_service = speech_service
        self.query_analyzer = query_analyzer

        # Support both single retriever injection and named retriever registry
        self.retrievers: dict[str, Retriever] = dict(retrievers) if retrievers else {}
        if retriever is not None:
            key = getattr(retriever, "strategy_name", None) or default_retriever_key
            self.retrievers.setdefault(key, retriever)
        self.default_retriever_key = default_retriever_key

        self.reranker = reranker
        self.generator = generator
        self.input_guard = input_guard
        self.relevance_guard = relevance_guard
        self.confidence_guard = confidence_guard
        self.grounding_guard = grounding_guard
        self.query_router = query_router
        self.metrics_store = metrics_store or get_metrics_store()

    # ------------------------------------------------------------------
    # Public entry points
    # ------------------------------------------------------------------

    async def run_voice_query(
        self,
        audio_data: bytes,
        request_id: Optional[str] = None,
        language: Optional[str] = None,
    ) -> QueryResponse:
        """
        Execute the full voice pipeline.

        Returns a not_implemented response until the speech service
        and downstream services are connected.
        """
        rid = sanitize_request_id(request_id)

        if self.speech_service is None:
            return self._not_implemented(rid, stage="speech-to-text")

        return self._not_implemented(rid, stage="voice-pipeline")

    async def run_text_query(
        self,
        query: str,
        request_id: Optional[str] = None,
        language: Optional[str] = None,
    ) -> QueryResponse:
        """
        Execute the text query pipeline.

        Returns a not_implemented response until retrieval and generation
        services are implemented and connected.
        """
        rid = sanitize_request_id(request_id)

        if not self.retrievers or self.generator is None:
            return self._not_implemented(rid, stage="retrieval-and-generation")

        # Phase 2 will execute PipelineState stages with timeouts, retries,
        # real guardrails, and MetricsStore recording here.
        return self._not_implemented(rid, stage="retrieval-and-generation")

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _not_implemented(request_id: str, stage: str) -> QueryResponse:
        """Return a structured placeholder response."""
        return QueryResponse(
            request_id=request_id,
            status=QueryStatus.NOT_IMPLEMENTED,
            message=(
                f"The SAMVAD {stage} pipeline has not yet been connected. "
                "This endpoint will return real results once the core "
                "RAG services are implemented."
            ),
        )


# ---------------------------------------------------------------------------
# Singleton orchestrator (services injected at startup)
# ---------------------------------------------------------------------------

_orchestrator: Optional[PipelineOrchestrator] = None


def get_orchestrator() -> PipelineOrchestrator:
    """Return the application-wide pipeline orchestrator."""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = PipelineOrchestrator()
    return _orchestrator
