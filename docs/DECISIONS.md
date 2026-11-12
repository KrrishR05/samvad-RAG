# SAMVAD-RAG — Architectural Decision Records (ADR)

This log records significant architectural decisions, alternatives considered, and trade-offs.

---

## ADR-001: Modular Monolith Over Microservices
- **Status:** Accepted (Phase 0)
- **Context:** SAMVAD combines ingestion, retrieval, reranking, generation, speech, and evaluation. Early-stage microservices add network serialization, service discovery, and deployment overhead without proven scale bottlenecks.
- **Decision:** Build the backend as a modular monolith in `backend/app/` with strict module boundaries and protocol interfaces. Offline ingestion and benchmark runners run as CLI/module entry points sharing core schemas and providers.
- **Trade-offs:** Simple testing, debugging, and local deployment; requires discipline to avoid circular imports or hidden global state.

## ADR-002: Honest `not_implemented` & Fail-Closed Guardrails
- **Status:** Accepted (Phase 0)
- **Context:** In the initial hackathon skeleton, `RelevanceGuard`, `ConfidenceGuard`, and `GroundingGuard` returned `GuardrailResult(passed=True)` as placeholders, creating a false sense of safety.
- **Decision:** No unimplemented service or guardrail may return a passing/success result. Unimplemented guardrails must raise `NotImplementedError` (or return an explicit unavailable/error state), and unimplemented pipeline paths return `QueryStatus.NOT_IMPLEMENTED`.
- **Trade-offs:** Prevents premature "all-green" demos; guarantees truthfulness of system behavior.

## ADR-003: Single Canonical Interface Layer (`Protocol` + `ScoredChunk`)
- **Status:** Accepted (Phase 0)
- **Context:** The original repository had duplicate `Protocol` definitions in `backend/app/pipeline/interfaces.py` and `ABC` base classes in `speech/base.py`, `retrieval/base.py`, `generation/base.py`, and `guardrails/base.py`, plus incompatible `RetrievalCandidate` vs `RerankResult` data containers.
- **Decision:** Standardize on `Protocol` interfaces in `backend/app/pipeline/interfaces.py` (removing redundant `@abstractmethod` and duplicate `Base*` ABCs where they add no shared implementation) and introduce a unified `ScoredChunk` container carrying separate `retrieval_score`, `reranker_score`, and `retrieval_method` fields.
- **Trade-offs:** Eliminates adapter boilerplate and type mismatches between retrievers, rerankers, context builders, and guardrails.

## ADR-004: Retriever Registry in `PipelineOrchestrator`
- **Status:** Accepted (Phase 0)
- **Context:** `QueryRouter.route()` returns a strategy identifier (`"dense"`, `"lexical"`, `"hybrid"`), but `PipelineOrchestrator.__init__` originally accepted only a single `retriever` instance.
- **Decision:** Allow `PipelineOrchestrator` to accept `retrievers: dict[str, Retriever]` (plus `default_retriever` key), enabling `QueryRouter` to dynamically select among registered retrieval strategies without changing orchestrator code.
- **Trade-offs:** Slightly richer constructor signature; enables A/B testing and adaptive routing cleanly.

## ADR-005: Local-First, Free Baselines Before Paid APIs
- **Status:** Accepted (Phase 0)
- **Context:** Research experimentation and automated CI must not depend on paid API credits or external network availability for unit tests.
- **Decision:** Prioritize local/open-source baselines (BM25 via `rank-bm25`, FAISS, `sentence-transformers`, local LLM via Ollama/OpenAI-compatible endpoint) while keeping hosted APIs (Sarvam, ElevenLabs, OpenAI, Gemini) behind interchangeable provider adapters.
- **Trade-offs:** Local embedding/LLM inference requires local CPU/RAM/GPU resources; hosted APIs remain optional runtime plugins.

## ADR-006: Evaluation Harness Prioritized Before Advanced RAG
- **Status:** Accepted (Phase 1 Priority)
- **Context:** Implementing advanced techniques (reranking, query rewriting, semantic chunking, multilingual models) without metrics makes it impossible to verify whether complexity helps or hurts.
- **Decision:** Build dataset validation, retrieval metrics, and reproducible experiment logging (Phase 1) immediately after Phase 0 stabilization, before Phase 2/3 retrieval experiments.
- **Trade-offs:** Delays flashy features briefly; ensures every retrieval and generation claim is backed by reproducible numbers.

