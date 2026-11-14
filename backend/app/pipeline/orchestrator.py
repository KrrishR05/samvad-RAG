"""
SAMVAD Pipeline Orchestrator

Coordinates execution of the SAMVAD query pipeline by delegating to injected
service implementations and registered retrieval strategies. Manages state
transitions, per-stage and end-to-end timeouts, latency metrics, and honest
abstention / unconfigured reporting.
"""

from __future__ import annotations

import asyncio
import inspect
import time
from typing import Any, Optional, Sequence

from app.analytics.metrics import MetricsStore, get_metrics_store
from app.core.config import Settings, get_settings
from app.core.errors import InputValidationError, PipelineTimeoutError
from app.core.logging import get_logger, sanitize_request_id
from app.pipeline.interfaces import (
    AnalyzedQuery,
    AnswerGenerator,
    GuardrailService,
    QueryAnalyzer,
    QueryRouter,
    Reranker,
    Retriever,
    ScoredChunk,
    SpeechService,
)
from app.pipeline.state import PipelineState
from app.retrieval.context_builder import ContextOptimizer
from app.schemas.analytics import LatencyRecord
from app.schemas.pipeline import ChunkMetadata, PipelineStage, StageResult, StageStatus
from app.schemas.response import (
    Confidence,
    ConfidenceLevel,
    LatencyBreakdown,
    QueryResponse,
    QueryStatus,
    Source,
)

logger = get_logger("pipeline.orchestrator")

SAMVAD_CANONICAL_CHUNK = ScoredChunk(
    chunk_id="samvad-platform-core-overview",
    text=(
        "SAMVAD (संवाद) is an intelligent, voice-first, evidence-grounded multilingual Retrieval-Augmented Generation (RAG) platform. "
        "Key capabilities and system architecture include:\n"
        "• Multilingual Indic Voice: Native speech-to-text (STT via Sarvam AI Saaras v3) and high-quality text-to-speech (TTS via Sarvam AI Bulbul v3) across 10+ Indic languages including Hindi, Marathi, Bengali, Tamil, Telugu, Kannada, Malayalam, Gujarati, Punjabi, Odia, and English.\n"
        "• Hybrid Retrieval: Combines dense vector semantic embeddings and sparse lexical Okapi BM25 keyword matching via Reciprocal Rank Fusion (RRF).\n"
        "• Retrieval Intelligence: Deterministic Indic script identification, query intensity detection ('deep' vs 'standard') for exhaustive document synthesis, cross-encoder reranking, and Jaccard token context deduplication.\n"
        "• Knowledge Base & Ingestion: Multi-format parsing (PDF, DOCX, TXT, Markdown) with SHA-256 chunk deduplication, provenance tracking, and persistent SQLite storage.\n"
        "• Trust & Transparency: Strict verifiable citation enforcement with bracketed source numbers, honest abstention when evidence is absent from the indexed knowledge base, and full stage-by-stage pipeline latency telemetry."
    ),
    retrieval_score=1.0,
    reranker_score=1.0,
    retrieval_method="system",
    metadata=ChunkMetadata(
        chunk_id="samvad-platform-core-overview",
        parent_document_id="samvad-system-manifest",
        language="hi-en",
        extra={"title": "SAMVAD Platform Specification & System Architecture"},
    ),
)


def _score_to_level(score: Optional[float]) -> Optional[ConfidenceLevel]:
    if score is None:
        return None
    if score >= 0.75:
        return ConfidenceLevel.HIGH
    if score >= 0.45:
        return ConfidenceLevel.MEDIUM
    return ConfidenceLevel.LOW


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
        settings: Optional[Settings] = None,
    ) -> None:
        self.speech_service = speech_service
        self.query_analyzer = query_analyzer

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
        self.settings = settings
        self.context_optimizer = ContextOptimizer()

    # ------------------------------------------------------------------
    # Public entry points
    # ------------------------------------------------------------------

    async def run_voice_query(
        self,
        audio_data: bytes,
        request_id: Optional[str] = None,
        language: Optional[str] = None,
        retriever_strategy: Optional[str] = None,
        top_k: Optional[int] = None,
    ) -> QueryResponse:
        """
        Execute the full voice pipeline:
          audio_data -> STT Transcription -> Text RAG Pipeline
        """
        rid = sanitize_request_id(request_id)
        if self.speech_service is None:
            return self._not_implemented(rid, stage="speech-to-text")

        ps = PipelineState(request_id=rid)
        cfg = self.settings or get_settings()

        # 1. Listening / Ingestion
        ps.begin_stage(PipelineStage.LISTENING)
        ps.complete_stage(output={"audio_bytes": len(audio_data)})

        # 2. Transcribing
        ps.begin_stage(PipelineStage.TRANSCRIBING)
        try:
            transcription = await asyncio.wait_for(
                self.speech_service.transcribe(audio_data, language=language),
                timeout=cfg.stage_timeout_seconds,
            )
        except Exception as exc:
            ps.complete_stage(error=str(exc))
            ps.transition_to(PipelineStage.ERROR)
            raise

        stt_stage = ps.complete_stage(
            output={
                "provider": getattr(self.speech_service, "provider_name", "stt"),
                "transcript": transcription.text,
            }
        )

        transcript = transcription.text.strip()
        if not transcript:
            ps.transition_to(PipelineStage.ABSTAINED)
            return QueryResponse(
                request_id=rid,
                status=QueryStatus.ABSTAINED,
                transcript="",
                message="No speech detected in the audio recording.",
                stages=ps.results,
            )

        # 3. Proceed through query validation and text pipeline
        text_response = await self.run_text_query(
            query=transcript,
            request_id=rid,
            language=transcription.language or language,
            retriever_strategy=retriever_strategy,
            top_k=top_k,
        )

        combined_stages = [
            ps.results[0],  # LISTENING
            stt_stage,      # TRANSCRIBING
        ] + [st for st in text_response.stages if st.stage not in (PipelineStage.LISTENING, PipelineStage.TRANSCRIBING)]

        merged_latency = text_response.latency or LatencyBreakdown()
        merged_latency.stt_ms = stt_stage.duration_ms
        if merged_latency.total_ms is not None and stt_stage.duration_ms is not None:
            merged_latency.total_ms = round(merged_latency.total_ms + stt_stage.duration_ms, 2)

        return QueryResponse(
            request_id=rid,
            status=text_response.status,
            transcript=transcript,
            answer=text_response.answer,
            grounded=text_response.grounded,
            confidence=text_response.confidence,
            sources=text_response.sources,
            latency=merged_latency,
            stages=combined_stages,
            retrieval_method=text_response.retrieval_method,
            message=text_response.message,
        )

    async def run_text_query(
        self,
        query: str,
        request_id: Optional[str] = None,
        language: Optional[str] = None,
        retriever_strategy: Optional[str] = None,
        top_k: Optional[int] = None,
    ) -> QueryResponse:
        """Execute the text RAG pipeline with bounded timeouts and real metrics."""
        rid = sanitize_request_id(request_id)

        if not self.retrievers:
            return self._not_implemented(rid, stage="retrieval-and-generation")

        cfg = self.settings or get_settings()
        try:
            return await asyncio.wait_for(
                self._execute_text_pipeline(
                    query=query,
                    rid=rid,
                    language=language,
                    retriever_strategy=retriever_strategy,
                    top_k=top_k,
                    cfg=cfg,
                ),
                timeout=cfg.pipeline_timeout_seconds,
            )
        except asyncio.TimeoutError as exc:
            logger.error("Pipeline timeout after %.1fs [rid=%s]", cfg.pipeline_timeout_seconds, rid)
            raise PipelineTimeoutError(
                message=f"Pipeline exceeded timeout of {cfg.pipeline_timeout_seconds}s.",
                request_id=rid,
            ) from exc

    async def _execute_text_pipeline(
        self,
        *,
        query: str,
        rid: str,
        language: Optional[str],
        retriever_strategy: Optional[str],
        top_k: Optional[int],
        cfg: Settings,
    ) -> QueryResponse:
        t0 = time.perf_counter()
        ps = PipelineState(request_id=rid)
        stage_timeout = cfg.stage_timeout_seconds

        # Select retriever strategy
        chosen_key = (retriever_strategy or self.default_retriever_key).strip().lower()
        active_retriever = self.retrievers.get(chosen_key)
        if active_retriever is None:
            if retriever_strategy is not None:
                raise InputValidationError(
                    f"Unknown retriever strategy '{retriever_strategy}'. "
                    f"Available strategies: {', '.join(sorted(self.retrievers.keys()))}."
                )
            # Fall back to the first registered retriever when default isn't explicitly keyed
            chosen_key, active_retriever = next(iter(self.retrievers.items()))

        # 1. Validating
        ps.begin_stage(PipelineStage.VALIDATING)
        cleaned_query = query.strip()
        if not cleaned_query:
            ps.complete_stage(error="Query text cannot be blank.")
            ps.transition_to(PipelineStage.ERROR)
            raise InputValidationError("Query text cannot be blank.")

        if self.input_guard is not None:
            guard_res = await asyncio.wait_for(
                self.input_guard.check(query=cleaned_query),
                timeout=stage_timeout,
            )
            if not guard_res.passed:
                ps.complete_stage(output={"guardrail_passed": False, "reason": guard_res.reason})
                ps.transition_to(PipelineStage.ABSTAINED)
                total_ms = round((time.perf_counter() - t0) * 1000.0, 2)
                return QueryResponse(
                    request_id=rid,
                    status=QueryStatus.ABSTAINED,
                    message=guard_res.reason or "Query rejected by input guardrail.",
                    latency=LatencyBreakdown(total_ms=total_ms),
                    stages=ps.results,
                    retrieval_method=chosen_key,
                )
        ps.complete_stage(output={"query_length": len(cleaned_query)})

        # 2. Query Analysis
        ps.begin_stage(PipelineStage.QUERY_ANALYSIS)
        if self.query_analyzer is not None:
            analyzed = await asyncio.wait_for(
                self.query_analyzer.analyze(cleaned_query),
                timeout=stage_timeout,
            )
            if language and not analyzed.language:
                analyzed.language = language
        else:
            analyzed = AnalyzedQuery(
                original_text=cleaned_query,
                processed_text=cleaned_query,
                language=language,
            )
        intensity = analyzed.metadata.get("intensity", "standard")
        about_samvad = analyzed.metadata.get("about_samvad", False)
        qa_stage = ps.complete_stage(
            output={
                "language": analyzed.language,
                "intensity": intensity,
                "about_samvad": about_samvad,
            }
        )

        # 3. Retrieval
        ps.begin_stage(PipelineStage.RETRIEVING)
        if top_k is not None:
            retrieval_k = top_k
        elif intensity == "deep":
            retrieval_k = max(cfg.retrieval_top_k * 2, 16)
        else:
            retrieval_k = cfg.retrieval_top_k

        raw_chunks = list(
            await asyncio.wait_for(
                active_retriever.retrieve(
                    analyzed.processed_text,
                    top_k=retrieval_k,
                    language=analyzed.language,
                ),
                timeout=stage_timeout,
            )
        )
        if about_samvad:
            raw_chunks.insert(0, SAMVAD_CANONICAL_CHUNK)

        ret_stage = ps.complete_stage(
            output={"strategy": chosen_key, "retrieved_count": len(raw_chunks)}
        )

        # 4. Optional Reranking
        rerank_stage: Optional[StageResult] = None
        if top_k is not None:
            context_limit = top_k
        elif intensity == "deep":
            context_limit = max(cfg.rerank_top_k * 2, 8)
        else:
            context_limit = cfg.rerank_top_k

        if self.reranker is not None and raw_chunks:
            ps.begin_stage(PipelineStage.RERANKING)
            ranked_chunks = list(
                await asyncio.wait_for(
                    self.reranker.rerank(
                        analyzed.processed_text,
                        raw_chunks,
                        top_k=context_limit,
                    ),
                    timeout=stage_timeout,
                )
            )
            rerank_stage = ps.complete_stage(output={"reranked_count": len(ranked_chunks)})
        else:
            ranked_chunks = raw_chunks[:context_limit]

        # Context optimization & deduplication (Phase 3 — M3.3)
        ranked_chunks = self.context_optimizer.optimize(ranked_chunks, max_chunks=context_limit)

        # 5. Relevance & Confidence Check
        ps.begin_stage(PipelineStage.CONFIDENCE_CHECK)
        if self.relevance_guard is not None and ranked_chunks and not about_samvad:
            rel_res = await asyncio.wait_for(
                self.relevance_guard.check(query=cleaned_query, context=ranked_chunks),
                timeout=stage_timeout,
            )
            if not rel_res.passed:
                ps.complete_stage(output={"passed": False, "reason": rel_res.reason, "check": "relevance"})
                ps.transition_to(PipelineStage.ABSTAINED)
                return self._build_abstained_response(
                    rid=rid,
                    message=rel_res.reason or "Abstained due to insufficient context relevance.",
                    chunks=ranked_chunks,
                    chosen_key=chosen_key,
                    t0=t0,
                    qa_ms=qa_stage.duration_ms,
                    ret_ms=ret_stage.duration_ms,
                    rerank_ms=rerank_stage.duration_ms if rerank_stage else None,
                    stages=ps.results,
                )

        if self.confidence_guard is not None and ranked_chunks and not about_samvad:
            conf_res = await asyncio.wait_for(
                self.confidence_guard.check(query=cleaned_query, context=ranked_chunks),
                timeout=stage_timeout,
            )
            if not conf_res.passed:
                ps.complete_stage(output={"passed": False, "reason": conf_res.reason, "check": "confidence"})
                ps.transition_to(PipelineStage.ABSTAINED)
                return self._build_abstained_response(
                    rid=rid,
                    message=conf_res.reason or "Abstained due to insufficient confidence.",
                    chunks=ranked_chunks,
                    chosen_key=chosen_key,
                    t0=t0,
                    qa_ms=qa_stage.duration_ms,
                    ret_ms=ret_stage.duration_ms,
                    rerank_ms=rerank_stage.duration_ms if rerank_stage else None,
                    stages=ps.results,
                )
        ps.complete_stage(output={"context_chunks": len(ranked_chunks)})

        # Check generator configuration honestly before attempting generation
        if self.generator is None:
            total_ms = round((time.perf_counter() - t0) * 1000.0, 2)
            sources = self._to_sources(ranked_chunks, cited_ids=())
            stages = list(ps.results) + [
                StageResult(
                    stage=PipelineStage.GENERATING,
                    status=StageStatus.SKIPPED,
                    error="LLM generator is not configured.",
                )
            ]
            latency = LatencyBreakdown(
                query_processing_ms=qa_stage.duration_ms,
                retrieval_ms=ret_stage.duration_ms,
                reranking_ms=rerank_stage.duration_ms if rerank_stage else None,
                total_ms=total_ms,
            )
            hint = (
                "No LLM provider is configured. Set LLM_PROVIDER (openai, ollama, or gemini), "
                "LLM_MODEL, and LLM_API_KEY (if using OpenAI/Gemini) in backend/.env and restart."
            )
            if not ranked_chunks:
                hint += " Also note: 0 passages matched in the knowledge base — upload documents first."
            return QueryResponse(
                request_id=rid,
                status=QueryStatus.NOT_IMPLEMENTED,
                sources=sources,
                latency=latency,
                stages=stages,
                retrieval_method=chosen_key,
                message=hint,
            )

        if not ranked_chunks:
            ps.transition_to(PipelineStage.ABSTAINED)
            return self._build_abstained_response(
                rid=rid,
                message=(
                    "No matching passages were found in the indexed documents for this query. "
                    "Try uploading relevant documents or broadening your query."
                ),
                chunks=[],
                chosen_key=chosen_key,
                t0=t0,
                qa_ms=qa_stage.duration_ms,
                ret_ms=ret_stage.duration_ms,
                rerank_ms=rerank_stage.duration_ms if rerank_stage else None,
                stages=ps.results,
            )

        # 6. Answer Generation
        ps.begin_stage(PipelineStage.GENERATING)
        gen_kwargs: dict[str, Any] = {"language": analyzed.language}
        try:
            sig = inspect.signature(self.generator.generate)
            if "intensity" in sig.parameters:
                gen_kwargs["intensity"] = intensity
        except Exception:
            pass

        gen_result = await asyncio.wait_for(
            self.generator.generate(
                cleaned_query,
                ranked_chunks,
                **gen_kwargs,
            ),
            timeout=stage_timeout,
        )
        gen_stage = ps.complete_stage(
            output={
                "model": getattr(self.generator, "model_name", None),
                "cited_count": len(gen_result.sources_used),
                "intensity": intensity,
            }
        )

        # 7. Grounding Check
        ps.begin_stage(PipelineStage.GROUNDING_CHECK)
        guardrail_ms: Optional[float] = None
        grounded = gen_result.grounded
        if self.grounding_guard is not None:
            g_res = await asyncio.wait_for(
                self.grounding_guard.check(
                    query=cleaned_query,
                    answer=gen_result.answer,
                    context=ranked_chunks,
                ),
                timeout=stage_timeout,
            )
            grounded = g_res.passed
            guard_stage = ps.complete_stage(output={"passed": g_res.passed, "reason": g_res.reason})
            guardrail_ms = guard_stage.duration_ms
        else:
            ps.complete_stage(output={"citation_linked": grounded})

        ps.transition_to(PipelineStage.COMPLETE)

        total_ms = round((time.perf_counter() - t0) * 1000.0, 2)
        latency = LatencyBreakdown(
            query_processing_ms=qa_stage.duration_ms,
            retrieval_ms=ret_stage.duration_ms,
            reranking_ms=rerank_stage.duration_ms if rerank_stage else None,
            generation_ms=gen_stage.duration_ms,
            guardrail_ms=guardrail_ms,
            total_ms=total_ms,
        )
        self._record_metrics(rid, latency)

        confidence = (
            Confidence(
                score=gen_result.confidence_score,
                level=_score_to_level(gen_result.confidence_score),
            )
            if gen_result.confidence_score is not None
            else None
        )

        return QueryResponse(
            request_id=rid,
            status=QueryStatus.COMPLETED,
            answer=gen_result.answer,
            grounded=grounded,
            confidence=confidence,
            sources=self._to_sources(ranked_chunks, cited_ids=gen_result.sources_used),
            latency=latency,
            stages=ps.results,
            retrieval_method=chosen_key,
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _build_abstained_response(
        self,
        *,
        rid: str,
        message: str,
        chunks: Sequence[ScoredChunk],
        chosen_key: str,
        t0: float,
        qa_ms: Optional[float],
        ret_ms: Optional[float],
        rerank_ms: Optional[float],
        stages: list[StageResult],
    ) -> QueryResponse:
        total_ms = round((time.perf_counter() - t0) * 1000.0, 2)
        latency = LatencyBreakdown(
            query_processing_ms=qa_ms,
            retrieval_ms=ret_ms,
            reranking_ms=rerank_ms,
            total_ms=total_ms,
        )
        self._record_metrics(rid, latency)
        return QueryResponse(
            request_id=rid,
            status=QueryStatus.ABSTAINED,
            answer=message,
            grounded=False,
            sources=self._to_sources(chunks, cited_ids=()),
            latency=latency,
            stages=stages,
            retrieval_method=chosen_key,
            message=message,
        )

    def _record_metrics(self, rid: str, latency: LatencyBreakdown) -> None:
        self.metrics_store.record(
            LatencyRecord(
                request_id=rid,
                stt_ms=latency.stt_ms,
                query_processing_ms=latency.query_processing_ms,
                embedding_ms=latency.embedding_ms,
                retrieval_ms=latency.retrieval_ms,
                reranking_ms=latency.reranking_ms,
                generation_ms=latency.generation_ms,
                guardrail_ms=latency.guardrail_ms,
                total_ms=latency.total_ms,
            )
        )

    @staticmethod
    def _to_sources(chunks: Sequence[ScoredChunk], cited_ids: Sequence[str]) -> list[Source]:
        cited_set = set(cited_ids)
        sources: list[Source] = []
        for idx, chunk in enumerate(chunks, start=1):
            if chunk.metadata is not None:
                meta = chunk.metadata.model_dump(mode="json")
                passage_id = chunk.metadata.parent_document_id or chunk.chunk_id
            else:
                meta = {}
                passage_id = chunk.chunk_id
            meta["citation_index"] = idx
            meta["is_cited"] = chunk.chunk_id in cited_set
            meta["retrieval_method"] = chunk.retrieval_method
            sources.append(
                Source(
                    source_id=chunk.chunk_id,
                    passage_id=passage_id,
                    text=chunk.text,
                    metadata=meta,
                    retrieval_score=chunk.retrieval_score,
                    reranker_score=chunk.reranker_score,
                )
            )
        return sources

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
# Singleton orchestrator (delegates to runtime wiring when unconfigured)
# ---------------------------------------------------------------------------

_orchestrator: Optional[PipelineOrchestrator] = None


def set_orchestrator(orchestrator: Optional[PipelineOrchestrator]) -> None:
    """Override or reset the application-wide orchestrator singleton (e.g. in tests)."""
    global _orchestrator
    _orchestrator = orchestrator


def get_orchestrator() -> PipelineOrchestrator:
    """Return the application-wide pipeline orchestrator wired from runtime settings."""
    global _orchestrator
    if _orchestrator is None:
        from app.pipeline.runtime import get_runtime

        _orchestrator = get_runtime().orchestrator
    return _orchestrator
