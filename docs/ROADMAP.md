# SAMVAD-RAG — Engineering & Research Roadmap

> Phases define dependency-ordered priorities, not arbitrary calendar deadlines.  
> A phase is complete **only** when all of its acceptance criteria are demonstrated and verified.

---

## Phase 0 — Foundation & Repository Stabilization *(Complete)*

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

## Phase 2 — First Functional End-to-End Text RAG Engine *(Implemented — LLM Provider Optional via `.env`)*

**Objective:** Deliver the first genuine text-based RAG pipeline with measurable BM25, dense, and hybrid baselines.

### Milestones
- **M2.1 Document Ingestion & Provenance (`Implemented & Tested`):** Loaders (`TXT`, `MD`, `PDF` via PyMuPDF, `DOCX` via `python-docx`, `HTML`, `JSON`), NFC Unicode normalization, multi-strategy chunking (`whole_passage`, `fixed_size`, `sliding_window`, `semantic`) with Devanagari sentence splitting (`।`, `॥`), SHA-256 deduplication, and SQLite document/chunk provenance store (`backend/app/ingestion/`).
- **M2.2 Embedding Infrastructure (`Implemented & Tested`):** Canonical `EmbeddingProvider` protocol, offline deterministic `LocalTfidfSVDProvider` baseline, and `OpenAICompatibleEmbeddingProvider` (`/embeddings`) in `backend/app/embeddings/`.
- **M2.3 Sparse, Dense & Hybrid Retrieval (`Implemented & Tested`):** Unicode/Indic-matra-preserving Okapi `LexicalRetriever` (`backend/app/retrieval/lexical.py`), L2-normalized cosine `DenseRetriever` with `.npz` disk persistence (`backend/app/retrieval/dense.py`), and weighted Reciprocal Rank Fusion `HybridRetriever` (`backend/app/retrieval/hybrid.py`).
- **M2.4 Provider-Agnostic Generation & Citations (`Implemented & Tested`):** `OpenAICompatibleGenerator` (OpenAI / Ollama / vLLM) and `GeminiGenerator` via `httpx`, delimited `<evidence>` prompt-injection isolation, and `[1]`, `[2]` inline citation mapping (`backend/app/generation/generator.py`).
- **M2.5 Pipeline Orchestration, Document API & Editorial UI (`Implemented & Tested`):** Wired `PipelineOrchestrator` (`PipelineState`, timeouts, honest `ABSTAINED`/`NOT_IMPLEMENTED` handling, `MetricsStore` latency recording), Document CRUD + `/api/v1/pipeline/status` routes (`backend/app/api/routes_documents.py`), and the 3-zone Editorial Research Workbench frontend (`frontend/app/`).

### Acceptance Criteria
- [x] Documents ingest cleanly with traceable `parent_document_id`, SHA-256 deduplication, and chunk offsets.
- [x] BM25, Dense, and Hybrid retrievers run independently and are benchmarked on Phase 1 eval sets (`synthetic_smoke_v1`: `ndcg@5=1.0`, `mrr@5=1.0`, `recall@5=1.0`).
- [x] `POST /api/v1/query` returns grounded answers with real citations when an LLM is configured, or honest abstention / unconfigured guidance when unconfigured.
- [x] End-to-end and failure-path integration tests pass (`104 passed` via `pytest -v`).

---

## Phase 3 — Retrieval Intelligence *(Implemented & Tested)*

**Objective:** Improve retrieval quality via controlled, measured experiments over Phase 2 baselines.

### Milestones
- **M3.1 Cross-Encoder Reranking (`Implemented & Tested`):** Pluggable `Reranker` implementation (`LexicalAlignmentReranker`, `GeminiReranker`, `CrossEncoderReranker`) in `backend/app/retrieval/reranker.py`.
- **M3.2 Query Processing & Language ID (`Implemented & Tested`):** Deterministic Indic language identification (Devanagari, Bengali, Tamil, Telugu, Kannada, Malayalam, Gujarati, Punjabi, Odia, Latin), query intent classification, and keyword extraction in `backend/app/retrieval/query_analyzer.py`.
- **M3.3 Context Optimization & Parent-Child Retrieval (`Implemented & Tested`):** Token Jaccard deduplication and token-budget context packing in `backend/app/retrieval/context_builder.py`.

### Acceptance Criteria
- [x] Fast, deterministic Indic script detection and query normalization across 10 scripts.
- [x] Pluggable reranker orders candidates by term coverage, bigram proximity, and early position.
- [x] Redundant chunk spans are deduplicated (threshold 0.80 Jaccard) before reaching generation.
- [x] All 116 backend tests pass cleanly.

---

## Phase 4 — Trustworthy Generation & Security Hardening *(Implemented & Tested)*

**Objective:** Replace heuristic checks with verifiable grounding, abstention, and prompt-injection defenses.

### Milestones
- **M4.1 Prompt Injection Isolation (`Implemented & Tested`):** Delimited untrusted evidence blocks, adversarial instruction-stripping, delimiter injection defenses, and red-team tests (`backend/app/guardrails/interfaces.py`).
- **M4.2 Real Guardrails Suite (`Implemented & Tested`):** Score-calibrated `RelevanceGuard` & `ConfidenceGuard`, citation existence/alignment verification (`GroundingGuard`), claim-level substantive overlap verification, and phantom citation detection.
- **M4.3 API Auth & Rate Limiting (`Implemented & Tested`):** Configurable API key middleware (`X-API-Key` / Bearer token) and per-client IP sliding-window rate limiting (`backend/app/api/middleware.py`).

### Acceptance Criteria
- [x] Red-team prompt-injection test suite passes (`test_security_redteam.py`).
- [x] Citation verifier catches fabricated/mismatched citations in automated tests (`test_guardrails.py`).
- [x] Abstention accuracy verified on low-confidence and out-of-domain queries.

---

## Phase 5 — Multilingual & Voice Capabilities *(Implemented & Tested)*

**Objective:** Deliver and independently evaluate Indic multilingual retrieval and voice interaction.

### Milestones
- **M5.1 Multilingual & Cross-Lingual Retrieval (`Implemented & Tested`):** Evaluated Indic multilingual retrieval across English, Hindi, and Bengali splits (`synthetic_smoke_v1.json`) across BM25, Dense TF-IDF/SVD, and Hybrid RRF retrievers.
- **M5.2 Speech-to-Text & Speech-Aware Normalization (`Implemented & Tested`):** Integrated `SpeechNormalizer` for verbal filler stripping (Indic/English), stutter deduplication, and Hinglish stem expansion; verified STT error impact isolation on retrieval metrics.
- **M5.3 Text-to-Speech & Streaming (`Implemented & Tested`):** Server-Sent Events (SSE) query pipeline streaming via `POST /api/v1/query/stream` broadcasting stage-by-stage progress (`stage_start`, `stage_complete`, `complete`) and TTS audio playback support.

### Acceptance Criteria
- [x] Per-language and cross-lingual evaluation tables published in `backend/benchmarks/results/`.
- [x] STT error impact isolated from RAG retrieval metrics.

---

## Phase 6 — Advanced Research & Optimization *(Hypothesis-Driven Only)*

**Objective:** Explore advanced architectures only when justified by concrete bottlenecks in Phases 1–5.
- Candidates: Late-interaction / multi-vector retrieval (ColBERT / BGE-M3), adaptive query routing (`QueryRouter`), retrieval caching, hierarchical/graph retrieval, context compression.
- Gate: Each experiment must be logged via Phase 1's runner and compared against Phase 3–5 baselines before main-pipeline integration.

