# SAMVAD-RAG — Known Limitations & Technical Risks

> Updated continuously to reflect **actual** system constraints, environment caveats, and unimplemented areas.

---

## 1. Current Implementation Limitations (As of Phase 0 Start)
- **Core AI Pipeline Unimplemented:** Retrieval (dense/BM25/hybrid), reranking, embedding generation, LLM answer generation, STT (`Sarvam`/`ElevenLabs`), document ingestion, and real guardrails are not implemented yet. `POST /api/v1/query` and `POST /api/v1/voice/query` return `status: "not_implemented"`.
- **No Evaluation Data or Benchmarks:** Zero datasets, ground-truth relevance judgments, or benchmark executions exist. Latency values in `frontend/lib/demo-data.ts` are strictly visual demo fixtures. The `sub-200ms P70` target mentioned in `backend/benchmarks/README.md` is unverified and unlikely to hold end-to-end when calling remote LLM/STT APIs without streaming/caching.
- **Ephemeral In-Memory Metrics:** `MetricsStore` (`backend/app/analytics/metrics.py`) stores records in an unbounded Python list in RAM. Data is lost on restart and is not shared across multi-worker uvicorn processes.
- **No Authentication or Rate Limiting:** API endpoints currently have no authentication or per-client rate limiting. Do **not** expose to untrusted networks with paid API keys configured.
- **Static Pipeline Visualizer:** `PipelineVisualizer` in the frontend resets stages to `pending` on query submission and does not reflect real backend stage progression (streaming/stage-result transport is not implemented yet).

---

## 2. Environment & Tooling Constraints Observed on Host
- **Host Python Versions:** Host has Python `3.14.6` (with `backend/.venv` initialized for Phase 0/1) and Python `3.10.11`. Note that Python `3.14` may lack pre-built binary wheels for ML packages (`faiss-cpu`, `torch`, `sentence-transformers`)—**Python 3.11 or 3.12** is recommended for Phases 2–5. Running `pytest-asyncio` tests on Windows requires loopback socket support (blocked inside strict sandbox isolation).
- **Host Node.js & Next.js Turbopack on Node 26:** Node.js `v26.13.1` / npm `11.20.0` are installed at `D:\`. On this host, Next.js `16.3.1` default Turbopack panics when spawning the PostCSS CSS worker (`TurbopackInternalError: node process exited before we could connect`), while `next build --webpack` and `tsc --noEmit` succeed cleanly. CI uses Node 20 LTS.
- **Docker Unavailable Locally:** `docker` is not installed/on PATH on the current host, so `docker-compose.yml`, `backend/Dockerfile`, and `frontend/Dockerfile` remain unbuilt locally.

---

## 3. Research & External Dependency Risks
- **MSMARCO-XI Dataset Verification Needed:** AI4Bharat MSMARCO-XI schema, language splits, licensing, and HuggingFace availability have not yet been verified programmatically.
- **Konkani & Low-Resource Indic Coverage:** Pre-trained multilingual embedding models and STT providers often have uneven quality for Konkani (especially Devanagari vs Roman script) and code-switched queries. Language-specific evaluation sets are required before making coverage claims.
- **Paid External APIs:** Sarvam AI, ElevenLabs, OpenAI, and Gemini require API keys and incur usage costs. Development and CI must rely on mocked providers and local open-source baselines unless explicitly authorized.

