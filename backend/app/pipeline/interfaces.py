"""
SAMVAD Pipeline Service Interfaces

Abstract protocols that every pipeline service must implement.
These are the **integration points** where the core RAG
functionality will be connected by the next developer.

Each protocol defines:
  - Expected input types
  - Expected output types
  - Error behaviour (raise the appropriate SamvadError subclass)

Use Python's Protocol for structural subtyping — implementors
do not need to explicitly inherit; they just need to match the
method signatures.
"""

from __future__ import annotations

from abc import abstractmethod
from dataclasses import dataclass
from typing import Any, Optional, Protocol, Sequence

from app.schemas.pipeline import ChunkMetadata
from app.schemas.response import Source


# ---------------------------------------------------------------------------
# Data containers passed between stages
# ---------------------------------------------------------------------------

@dataclass
class TranscriptionResult:
    """Output of the Speech-to-Text stage."""

    text: str
    language: Optional[str] = None
    confidence: Optional[float] = None
    provider: Optional[str] = None


@dataclass
class AnalyzedQuery:
    """Output of the query analysis stage."""

    original_text: str
    processed_text: str
    language: Optional[str] = None
    intent: Optional[str] = None
    metadata: dict[str, Any] | None = None


@dataclass
class RetrievalCandidate:
    """A single candidate returned by a retriever."""

    chunk_id: str
    text: str
    score: float
    metadata: ChunkMetadata | None = None


@dataclass
class RerankResult:
    """A candidate after reranking."""

    chunk_id: str
    text: str
    original_score: float
    reranker_score: float
    metadata: ChunkMetadata | None = None


@dataclass
class GenerationResult:
    """Output of the answer generation stage."""

    answer: str
    grounded: Optional[bool] = None
    confidence_score: Optional[float] = None
    sources_used: list[Source] | None = None


@dataclass
class GuardrailResult:
    """Output of a guardrail check."""

    passed: bool
    reason: Optional[str] = None
    action: str = "allow"  # "allow" | "abstain" | "modify"
    modified_text: Optional[str] = None


# ---------------------------------------------------------------------------
# Service Protocols
# ---------------------------------------------------------------------------

class SpeechService(Protocol):
    """
    Transcribe audio input to text.

    TODO: Implement SarvamSpeechProvider and ElevenLabsSpeechProvider.
    """

    @abstractmethod
    async def transcribe(
        self,
        audio_data: bytes,
        language: str | None = None,
    ) -> TranscriptionResult:
        """
        Transcribe raw audio bytes to text.

        Args:
            audio_data: Raw audio bytes (WAV/WebM/OGG).
            language: Optional language hint (ISO 639-1).

        Returns:
            TranscriptionResult with transcribed text.

        Raises:
            SpeechProcessingError on failure.
        """
        ...


class QueryAnalyzer(Protocol):
    """
    Analyse and optionally transform the user's query
    before retrieval (e.g. language detection, expansion).

    TODO: Implement when query processing logic is finalised.
    """

    @abstractmethod
    async def analyze(self, query: str) -> AnalyzedQuery:
        ...


class Retriever(Protocol):
    """
    Retrieve candidate passages from the index.

    Implementations may use dense, lexical (BM25), hybrid,
    or adaptive strategies.

    TODO: Implement DenseRetriever, LexicalRetriever, HybridRetriever.
    """

    @abstractmethod
    async def retrieve(
        self,
        query: str,
        top_k: int = 10,
        language: str | None = None,
    ) -> Sequence[RetrievalCandidate]:
        """
        Retrieve top-K candidates for the given query.

        Raises:
            RetrievalError on failure.
        """
        ...


class Reranker(Protocol):
    """
    Re-score and re-order retrieval candidates.

    TODO: Implement cross-encoder or model-based reranker.
    """

    @abstractmethod
    async def rerank(
        self,
        query: str,
        candidates: Sequence[RetrievalCandidate],
        top_k: int = 5,
    ) -> Sequence[RerankResult]:
        """
        Rerank candidates and return the top-K results.

        Raises:
            RetrievalError on failure.
        """
        ...


class AnswerGenerator(Protocol):
    """
    Generate a grounded answer given a query and context.

    TODO: Implement LLM-based generator with grounding.
    """

    @abstractmethod
    async def generate(
        self,
        query: str,
        context: Sequence[RerankResult] | Sequence[RetrievalCandidate],
        language: str | None = None,
    ) -> GenerationResult:
        """
        Generate an answer grounded in the provided context.

        Raises:
            GenerationError on failure.
        """
        ...


class GuardrailService(Protocol):
    """
    Apply safety and quality guardrails.

    Implementations include:
      - InputGuard: validate input quality
      - RelevanceGuard: check retrieval relevance
      - ConfidenceGuard: check confidence threshold
      - GroundingGuard: verify answer grounding

    TODO: Implement concrete guardrails.
    """

    @abstractmethod
    async def check(
        self,
        *,
        query: str | None = None,
        answer: str | None = None,
        context: Sequence[RetrievalCandidate] | None = None,
        confidence: float | None = None,
    ) -> GuardrailResult:
        """
        Run the guardrail check.

        Returns:
            GuardrailResult indicating pass/fail and action.

        Raises:
            GuardrailError on check failure.
        """
        ...


class QueryRouter(Protocol):
    """
    Decide which retrieval strategy to use for a given query.

    TODO: Implement adaptive routing logic.
    """

    @abstractmethod
    async def route(
        self,
        query: AnalyzedQuery,
    ) -> str:
        """
        Return the retrieval strategy identifier.

        Returns:
            Strategy name, e.g. "dense", "lexical", "hybrid".
        """
        ...
