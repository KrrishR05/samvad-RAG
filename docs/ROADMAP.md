# SAMVAD-RAG — Engineering & Research Roadmap

> Phases define dependency-ordered priorities, not arbitrary calendar deadlines.  
> A phase is complete **only** when all of its acceptance criteria are demonstrated and verified.

---

## Phase 0 — Foundation & Repository Stabilization *(Current Phase)*

**Objective:** Establish a trustworthy, reproducible, architecturally consistent baseline before writing RAG engine code.

### Milestones
- **M0.1 Environment & Dependency Hygiene:** Pin/organize backend runtime and dev dependencies (`requirements.txt`, `requirements-dev.txt`), document supported Python versions (3.11–3.13 recommended for ML wheel compatibility; verify 3.14 constraints), verify test suite execution.
- **M0.2 Architectural Consistency Cleanup:**
  - Unify duplicate `Protocol` (`pipeline/interfaces.py`) and `ABC` (`*/base.py`) service hierarchies into one canonical contract layer.
  - Harmonize `RetrievalCandidate` and `RerankResult` into a canonical `ScoredChunk` model so retrievers, rerankers, context builders, and guardrails compose cleanly.
  - Update `PipelineOrchestrator` to accept a retriever registry (`dict[str, Retriever]`) so `QueryRouter` can dispatch strategies.
  - Remove silent no-op behavior in `GuardrailService` stubs (`RelevanceGuard`, `ConfidenceGuard`, `GroundingGuard` must fail explicitly / raise `NotImplementedError` rather than returning `passed=True`).
- **M0.3 Reliability, Logging & Upload Security:**
  - Wire FastAPI `RequestIdMiddleware` so `current_request_id` populates structured logs and `X-Request-ID` headers.
  - Enforce streaming upload size limits, empty-file rejection, and audio MIME/header validation in `POST /api/v1/voice/query`.
  - Tighten CORS/config validation (`stt_provider` enum, production CORS checks).
- **M0.4 Frontend, Docker & CI Baseline:**
  - Fix unstable `useVoiceRecorder` return reference / `useEffect` dependency in `frontend/app/page.tsx`.
  - Add `backend/Dockerfile`, `frontend/Dockerfile`, and `.github/workflows/ci.yml`.
  - Fix misleading `test_api_v1_health` and add unit tests for `MetricsStore`, upload limits, and guardrail non-noop behavior.

### Acceptance Criteria
- [x] Backend unit & API tests pass in a clean virtual environment (`78 passed in 1.88s`).
- [x] Frontend TypeScript check (`tsc --noEmit`), ESLint (`0 errors`), and production build (`next build --webpack`) succeed.
- [x] Zero guardrails silently return `passed=True` without validation.
- [x] Request IDs appear in all structured logs and error responses.
- [x] Voice uploads enforce byte size limits and format validation.
- [x] `docs/` accurately reflects actual implemented state.

---

## Phase 1 — Evaluation Foundation

**Objective:** Make retrieval and pipeline behavior scientifically measurable before building advanced retrieval.

### Milestones
- **M1.1 Dataset & Judgment Schemas (`Implemented & Tested`):** Typed Pydantic models in `backend/app/evaluation/schemas.py` for corpus documents, queries, graded `qrels`, provenance (`real` vs `synthetic`), and structural integrity validation.
- **M1.2 Dataset Validation & Integrity (`Partially Implemented`):** Local JSON loader, content SHA-256 checksum verification, and schema inspection CLI implemented in `backend/app/evaluation/{loader,cli}.py`; remote HuggingFace `AI4Bharat MSMARCO-XI` schema/license inspection pending `datasets` installation.
- **M1.3 Retrieval Metrics Library (`Implemented & Tested`):** Deterministic `Recall@K`, `Precision@K`, `MRR@K`, `nDCG@K`, and `HitRate@K` in `backend/app/evaluation/metrics.py` with duplicate-ID protection and per-language aggregation.
- **M1.4 Reproducible Experiment Runner (`Implemented & Tested`):** Async runner in `backend/app/evaluation/runner.py` persisting immutable `config.json`, `predictions.jsonl`, `summary.json`, and `summary.md` with git SHA and hardware/Python metadata.

### Acceptance Criteria
- [x] All metric functions verified against deterministic unit test fixtures (`test_evaluation_metrics.py`).
- [x] Dataset loader/schema validates missing IDs and duplicate judgments.
- [x] Two runs with identical seed/config produce identical retrieval metrics and full provenance metadata (`test_evaluation_runner.py`).
- [ ] Real benchmark dataset (e.g., MSMARCO-XI slice) inspected, licensed-checked, and validated.

---

## Phase 2 — First Functional End-to-End Text RAG Engine

**Objective:** Deliver the first genuine text-based RAG pipeline with measurable BM25, dense, and hybrid baselines.

### Milestones
- **M2.1 Document Ingestion & Provenance:** Implement loaders (TXT, Markdown, PDF via PyMuPDF, DOCX), text normalization, metadata extraction, configurable chunking (`whole_passage`, `fixed_size`, `sliding_window`, `semantic`), deduplication, and SQLite document/chunk provenance store.
- **M2.2 Embedding Infrastructure:** Implement `EmbeddingProvider` protocol, config-driven registry, local open-source provider (`sentence-transformers`), batching, dimension/model-version validation, and disk/SQLite embedding cache.
- **M2.3 Sparse, Dense & Hybrid Retrieval:** Implement `LexicalRetriever` (`rank-bm25` / SQLite FTS5), `DenseRetriever` (`FAISS`), `HybridRetriever` (Reciprocal Rank Fusion), and `RetrieverRegistry`.
- **M2.4 Provider-Agnostic Generation & Citations:** Implement `LLMProvider` abstraction (supporting local Ollama/OpenAI-compatible + hosted APIs), structured evidence packaging, and inline citation mapping.
- **M2.5 Pipeline Orchestration & Observability:** Connect `PipelineState`, timeouts (`pipeline_timeout_seconds`, `stage_timeout_seconds`), bounded retries, and `MetricsStore` persistence.

### Acceptance Criteria
- [ ] Documents ingest cleanly with traceable `parent_document_id` and chunk offsets.
- [ ] BM25, Dense, and Hybrid retrievers run independently and are benchmarked on Phase 1 eval sets.
- [ ] `POST /api/v1/query` returns grounded answers with real citations or honest abstention.
- [ ] End-to-end and failure-path integration tests pass with mocked and local providers.

---

## Phase 3 — Retrieval Intelligence

**Objective:** Improve retrieval quality via controlled, measured experiments over Phase 2 baselines.

### Milestones
- **M3.1 Cross-Encoder Reranking:** Pluggable `Reranker` implementation with latency/nDCG@5 trade-off benchmarks.
- **M3.2 Query Processing & Language ID:** Deterministic language identification, query normalization, and gated query rewriting/expansion (evaluated against raw query baseline).
- **M3.3 Context Optimization & Parent-Child Retrieval:** Deduplication, token-budget packing, parent-child chunk expansion, and metadata filtering.

### Acceptance Criteria
- [ ] Every added stage shows measured delta (positive or negative) on Phase 1 metrics + latency/cost report.

---

## Phase 4 — Trustworthy Generation & Security Hardening

**Objective:** Replace heuristic checks with verifiable grounding, abstention, and prompt-injection defenses.

### Milestones
- **M4.1 Prompt Injection Isolation:** Delimited untrusted evidence blocks, instruction-stripping/detection tests.
- **M4.2 Real Guardrails:** Score-calibrated `RelevanceGuard` & `ConfidenceGuard`, citation existence/alignment verification (`GroundingGuard`), claim-level support checks, and contradiction surfacing.
- **M4.3 API Auth & Rate Limiting:** Configurable API key/JWT middleware and per-client rate limiting.

### Acceptance Criteria
- [ ] Red-team prompt-injection test suite passes.
- [ ] Citation verifier catches fabricated/mismatched citations in automated tests.
- [ ] Abstention accuracy measured on unanswerable/out-of-domain test split.

---

## Phase 5 — Multilingual & Voice Capabilities

**Objective:** Deliver and independently evaluate Indic multilingual retrieval and voice interaction.

### Milestones
- **M5.1 Multilingual & Cross-Lingual Retrieval:** Evaluate multilingual embeddings (e.g., BGE-M3) and transliteration/code-switching across English, Hindi, Konkani, and other Indic splits.
- **M5.2 Speech-to-Text & Speech-Aware Normalization:** Implement `SarvamSpeechProvider` / local Whisper / `ElevenLabsSpeechProvider`, evaluating WER/CER separately from retrieval Recall@K.
- **M5.3 Text-to-Speech & Streaming:** Optional TTS output and SSE pipeline progress streaming to the frontend.

### Acceptance Criteria
- [ ] Per-language and cross-lingual evaluation tables published in `backend/benchmarks/results/`.
- [ ] STT error impact isolated from RAG retrieval metrics.

---

## Phase 6 — Advanced Research & Optimization *(Hypothesis-Driven Only)*

**Objective:** Explore advanced architectures only when justified by concrete bottlenecks in Phases 1–5.
- Candidates: Late-interaction / multi-vector retrieval (ColBERT / BGE-M3), adaptive query routing (`QueryRouter`), retrieval caching, hierarchical/graph retrieval, context compression.
- Gate: Each experiment must be logged via Phase 1's runner and compared against Phase 3–5 baselines before main-pipeline integration.

