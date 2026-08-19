# SAMVAD

> **Speak. Retrieve. Ground.**

Adaptive Voice-Enabled RAG system built for [Hacker House Goa 2026](https://hhgoa.com/).

---

## Overview

SAMVAD is a voice-first retrieval-augmented generation system designed for multilingual, Indic-language-aware information retrieval. Users speak a question, and the system:

```
Voice Input → Speech-to-Text → Query Processing → Adaptive Retrieval
→ Reranking → Guardrails → Grounded Answer
```

The system is built to support:

- **Voice-first interaction** via Sarvam AI / ElevenLabs STT
- **Multilingual / Indic orientation** using MSMARCO-XI by AI4Bharat
- **Multi-strategy chunking** (whole-passage, semantic, sliding window)
- **Adaptive retrieval** (dense, lexical/BM25, hybrid with query routing)
- **Two-stage retrieval** with cross-encoder reranking
- **Structured orchestration** with retries, fallback, and abstention
- **Guardrails** for input validation, relevance, confidence, and grounding
- **Real latency benchmarking** with P50/P70/P100 metrics

---

## Current Implementation Status

### Foundation ✓

- [x] Frontend foundation (Next.js + TypeScript + Tailwind CSS)
- [x] Backend foundation (FastAPI + Pydantic)
- [x] API contracts and stable schemas
- [x] Pipeline state machine with valid transitions
- [x] Service interfaces and protocols
- [x] Configuration system (pydantic-settings + env vars)
- [x] Centralized error handling with custom exceptions
- [x] Structured logging with request_id tracing
- [x] Analytics framework with percentile calculations
- [x] Voice recording infrastructure (browser microphone)
- [x] Pipeline visualization component
- [x] Answer display component (all states)
- [x] Analytics page with empty state
- [x] Architecture page
- [x] Test suite (health, config, schemas, pipeline, percentiles, errors)

### Core AI Pipeline — Pending

- [ ] MSMARCO-XI dataset ingestion
- [ ] Multi-strategy chunking implementation
- [ ] Embedding generation
- [ ] Vector index (FAISS / Qdrant)
- [ ] Dense retrieval
- [ ] Lexical retrieval (BM25)
- [ ] Hybrid retrieval and fusion
- [ ] Adaptive query routing
- [ ] Cross-encoder reranking
- [ ] LLM-based generation
- [ ] Guardrail implementation
- [ ] Real latency benchmarks

---

## Project Structure

```
samvad-rag/
├── frontend/                    # Next.js application
│   ├── app/                     # App Router pages
│   │   ├── page.tsx             # Main query interface
│   │   ├── analytics/           # Latency analytics page
│   │   └── architecture/        # Architecture overview page
│   ├── components/
│   │   ├── layout/              # Header, navigation
│   │   ├── voice/               # Voice recording button
│   │   ├── pipeline/            # Pipeline visualizer
│   │   ├── answer/              # Answer/result display
│   │   ├── analytics/           # Latency cards
│   │   └── ui/                  # Text input, shared UI
│   ├── hooks/                   # Custom React hooks
│   ├── lib/                     # API client, demo data
│   └── types/                   # TypeScript type definitions
│
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI application entry
│   │   ├── api/                 # Route handlers
│   │   ├── core/                # Config, logging, errors
│   │   ├── schemas/             # Pydantic models
│   │   ├── pipeline/            # Orchestrator, state, interfaces
│   │   ├── speech/              # STT providers (Sarvam, ElevenLabs)
│   │   ├── retrieval/           # Dense, lexical, hybrid, router, reranker
│   │   ├── generation/          # LLM generator
│   │   ├── guardrails/          # Input, relevance, confidence, grounding
│   │   └── analytics/           # Metrics store, percentile calculations
│   ├── ingestion/               # Dataset ingestion (planned)
│   ├── benchmarks/              # Benchmark runner and results
│   ├── tests/                   # Test suite
│   └── requirements.txt
│
├── docs/
│   └── architecture.md          # Detailed architecture documentation
│
├── .env.example                 # Environment variable template
├── .gitignore
├── docker-compose.yml
└── README.md
```

---

## Setup

### Prerequisites

- Python 3.11+
- Node.js 18+
- npm

### Backend

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate
# Activate (macOS/Linux)
# source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the server
uvicorn app.main:app --reload --port 8000
```

The API will be available at `http://localhost:8000`.
Swagger docs: `http://localhost:8000/docs`

### Frontend

```bash
cd frontend

# Install dependencies
npm install

# Run the dev server
npm run dev
```

The app will be available at `http://localhost:3000`.

### Running Tests

```bash
cd backend
pytest -v
```

---

## Environment Variables

Copy `.env.example` to `.env` in the project root and fill in values:

| Variable | Description | Required |
|----------|-------------|----------|
| `ENVIRONMENT` | `development` / `staging` / `production` | No (default: development) |
| `SARVAM_API_KEY` | Sarvam AI API key for Indic STT | For voice features |
| `ELEVENLABS_API_KEY` | ElevenLabs API key (alt STT) | Optional |
| `LLM_API_KEY` | LLM provider API key | For generation |
| `LLM_MODEL` | LLM model identifier | For generation |
| `EMBEDDING_MODEL` | Embedding model identifier | For retrieval |
| `VECTOR_DB_PATH` | Path to vector index | For retrieval |
| `CORS_ORIGINS` | Allowed CORS origins | No (default: localhost:3000) |

See `.env.example` for the complete list.

---

## API Endpoints

| Method | Path | Description | Status |
|--------|------|-------------|--------|
| `GET` | `/health` | Service health check | ✅ Working |
| `POST` | `/api/v1/query` | Text query | ⏳ Returns not_implemented |
| `POST` | `/api/v1/voice/query` | Voice query (audio upload) | ⏳ Returns not_implemented |
| `GET` | `/api/v1/analytics/summary` | Analytics summary | ✅ Working (empty) |
| `GET` | `/api/v1/analytics/latency` | Latency statistics | ✅ Working (empty) |

---

## Future Integration Points

The next developer should implement the core RAG pipeline by:

1. **Implementing service protocols** in `backend/app/pipeline/interfaces.py`
2. **Wiring services** in `backend/app/pipeline/orchestrator.py → get_orchestrator()`
3. **Adding ingestion scripts** in `backend/ingestion/`
4. **Running benchmarks** and populating `backend/benchmarks/results/`

Key files to start with:

- `backend/app/pipeline/interfaces.py` — Service contracts
- `backend/app/pipeline/orchestrator.py` — Pipeline wiring point
- `backend/app/retrieval/` — Retrieval implementations
- `backend/app/generation/generator.py` — LLM integration
- `backend/app/speech/provider.py` — STT implementations
- `backend/app/guardrails/interfaces.py` — Guardrail logic

The frontend, API contracts, and schemas are designed to work without changes once the backend services are connected.

---

## License

Built for Hacker House Goa 2026.
