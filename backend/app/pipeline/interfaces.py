"""
SAMVAD Pipeline Service Interfaces

Canonical Protocols and inter-stage data containers for the SAMVAD pipeline.
All subsystem providers implement these structural interfaces without needing
parallel ABC hierarchies.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional, Protocol, Sequence, runtime_checkable

from app.schemas.pipeline import ChunkMetadata
from app.schemas.response import Source


# ---------------------------------------------------------------------------
# Canonical data containers passed between stages
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
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ScoredChunk:
    """
    Canonical representation of a retrieved and/or reranked passage.

    Keeps retrieval and reranker scores strictly separate so incompatible
    score scales (e.g. BM25, cosine similarity, cross-encoder logits) are
    never conflated.
    """

    chunk_id: str
    text: str
    retrieval_score: Optional[float] = None
    reranker_score: Optional[float] = None
    retrieval_method: Optional[str] = None
    metadata: ChunkMetadata | None = None


@dataclass
class GenerationResult:
    """Output of the answer generation stage."""

    answer: str
    grounded: Optional[bool] = None
    confidence_score: Optional[float] = None
    sources_used: list[Source] = field(default_factory=list)


@dataclass
class GuardrailResult:
    """Output of a guardrail check."""

    passed: bool
    reason: Optional[str] = None
    action: str = "allow"  # "allow" | "abstain" | "modify"
    modified_text: Optional[str] = None


# ---------------------------------------------------------------------------
# Canonical Service Protocols
# ---------------------------------------------------------------------------

@runtime_checkable
class SpeechService(Protocol):
    """Transcribe audio input to text."""

    provider_name: str

    async def transcribe(
        self,
        audio_data: bytes,
        language: str | None = None,
    ) -> TranscriptionResult:
        """Transcribe raw audio bytes to text. Raises SpeechProcessingError on failure."""
        ...

    async def health_check(self) -> bool:
        """Return True if the speech provider is ready/reachable."""
        ...


@runtime_checkable
class QueryAnalyzer(Protocol):
    """Analyze and optionally normalize/transform the user's query before retrieval."""

    async def analyze(self, query: str) -> AnalyzedQuery:
        ...


@runtime_checkable
class Retriever(Protocol):
    """Retrieve candidate passages from an index (dense, lexical, hybrid)."""

    strategy_name: str

    async def retrieve(
        self,
        query: str,
        top_k: int = 10,
        language: str | None = None,
    ) -> Sequence[ScoredChunk]:
        """Retrieve top-K candidates for the given query. Raises RetrievalError on failure."""
        ...

    async def health_check(self) -> bool:
        """Return True if the underlying index is available."""
        ...


@runtime_checkable
class Reranker(Protocol):
    """Re-score and re-order retrieval candidates."""

    async def rerank(
        self,
        query: str,
        candidates: Sequence[ScoredChunk],
        top_k: int = 5,
    ) -> Sequence[ScoredChunk]:
        """Rerank candidates and return the top-K results. Raises RetrievalError on failure."""
        ...


@runtime_checkable
class AnswerGenerator(Protocol):
    """Generate a grounded answer given a query and evidence chunks."""

    async def generate(
        self,
        query: str,
        context: Sequence[ScoredChunk],
        language: str | None = None,
        intensity: str = "standard",
    ) -> GenerationResult:
        """Generate an answer grounded in the provided context. Raises GenerationError on failure."""
        ...


@runtime_checkable
class GuardrailService(Protocol):
    """Apply safety and quality guardrails."""

    guardrail_name: str

    async def check(
        self,
        *,
        query: str | None = None,
        answer: str | None = None,
        context: Sequence[ScoredChunk] | None = None,
        confidence: float | None = None,
    ) -> GuardrailResult:
        """Run the guardrail check. Raises GuardrailError or NotImplementedError if unavailable."""
        ...


@runtime_checkable
class QueryRouter(Protocol):
    """Decide which registered retrieval strategy key to use for a given query."""

    async def route(
        self,
        query: AnalyzedQuery,
    ) -> str:
        """Return the retrieval strategy key (e.g. 'dense', 'lexical', 'hybrid')."""
        ...
