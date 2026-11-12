# SAMVAD-RAG — Known Limitations & Technical Risks

> Updated continuously to reflect **actual** system constraints, environment caveats, and unimplemented areas.

---

## 1. Current Implementation Limitations (As of Phase 2)
- **LLM Requires External Provider or Local Ollama:** `POST /api/v1/query` runs live retrieval and returns retrieved `sources` and stage timings, but returns `status: "not_implemented"` with setup instructions whenever no LLM credentials (`LLM_PROVIDER`, `LLM_MODEL`, and `LLM_API_KEY` where applicable) are configured in `backend/.env`.
- **Voice STT, Reranking & NLI Guardrails Planned for Phases 3–4:** `POST /api/v1/voice/query` still returns `status: "not_implemented"` (`SarvamSpeechProvider` / `ElevenLabsSpeechProvider` pending Phase 4). `CrossEncoderReranker` and `RelevanceGuard` / `ConfidenceGuard` / `GroundingGuard` NLI verification remain unimplemented until Phase 3 (`grounded: true` in Phase 2 indicates inline `[n]` citation linkage, not claim-level NLI verification).
- **Default Dense Baseline Uses TF-IDF + SVD (`LocalTfidfSVDProvider`):** Without an external/Ollama neural embedding server (`EMBEDDING_PROVIDER=openai_compatible`), dense retrieval uses deterministic character n-gram TF-IDF + TruncatedSVD rather than cross-lingual semantic transformers; cross-script semantic similarity requires neural embeddings in Phase 3+.
- **Ephemeral In-Memory Metrics:** `MetricsStore` (`backend/app/analytics/metrics.py`) stores up to 10,000 latency records in RAM. Data is lost on restart and is not shared across multi-worker uvicorn processes.
- **No Authentication or Rate Limiting:** API endpoints currently have no authentication or per-client rate limiting. Do **not** expose to untrusted networks with paid API keys configured.
- **Only Synthetic Smoke Evaluation Executed Locally:** Retrieval comparisons (`synthetic_smoke_v1` in `backend/benchmarks/datasets/`) verify pipeline wiring only; large external multilingual benchmarks (`AI4Bharat MSMARCO-XI`) remain pending download & validation.

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

