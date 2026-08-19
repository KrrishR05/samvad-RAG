# SAMVAD — Architecture Documentation

## Overview

SAMVAD (**S**peak, **A**daptive, **M**ultilingual, **V**oice-**A**ided, **D**iscovery) is a voice-enabled adaptive retrieval-augmented generation system. It processes voice or text queries through a structured pipeline that retrieves relevant information from a multilingual knowledge base (MSMARCO-XI) and generates grounded, evidence-backed answers.

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  FRONTEND  (Next.js / TypeScript / Tailwind CSS)            │
│                                                             │
│  ┌──────────┐  ┌───────────┐  ┌───────────┐  ┌──────────┐  │
│  │  Query   │  │ Pipeline  │  │  Answer   │  │Analytics │  │
│  │  Page    │  │  Viz      │  │  Panel    │  │  Page    │  │
│  └────┬─────┘  └───────────┘  └───────────┘  └────┬─────┘  │
│       │              API Client (lib/api/)          │       │
└───────┼─────────────────────────────────────────────┼───────┘
        │              HTTP / REST                    │
┌───────┼─────────────────────────────────────────────┼───────┐
│  BACKEND  (Python / FastAPI / Pydantic)             │       │
│       │                                             │       │
│  ┌────▼──────────────────────────────────────┐      │       │
│  │            API Routes Layer               │      │       │
│  │  /health  /api/v1/query  /api/v1/voice/   │◄─────┘       │
│  │  /api/v1/analytics/*                      │              │
│  └────┬──────────────────────────────────────┘              │
│       │                                                     │
│  ┌────▼──────────────────────────────────────┐              │
│  │         Pipeline Orchestrator             │              │
│  │  State Machine  │  Service Injection      │              │
│  └────┬──────────────────────────────────────┘              │
│       │                                                     │
│  ┌────▼────┐  ┌──────────┐  ┌───────────┐  ┌────────────┐  │
│  │ Speech  │  │ Retrieval│  │ Generation│  │ Guardrails │  │
│  │ Service │  │ Module   │  │ Module    │  │ Module     │  │
│  │         │  │          │  │           │  │            │  │
│  │ Sarvam  │  │ Dense    │  │ LLM Gen  │  │ Input      │  │
│  │ Eleven  │  │ Lexical  │  │ Grounding │  │ Relevance  │  │
│  │ Labs    │  │ Hybrid   │  │           │  │ Confidence │  │
│  │         │  │ Router   │  │           │  │ Grounding  │  │
│  │         │  │ Reranker │  │           │  │            │  │
│  └─────────┘  └──────────┘  └───────────┘  └────────────┘  │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Core: Config │ Logging │ Errors │ Analytics         │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘

        OFFLINE (Pre-computed)
┌─────────────────────────────────────────────────────────────┐
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌───────────┐   │
│  │ MSMARCO  │  │ Chunking │  │ Embedding│  │  Vector   │   │
│  │ -XI      │→ │ Multi-   │→ │ Model    │→ │  Index    │   │
│  │ Dataset  │  │ Strategy │  │          │  │  (FAISS)  │   │
│  └──────────┘  └──────────┘  └──────────┘  └───────────┘   │
└─────────────────────────────────────────────────────────────┘
```

## Pipeline State Machine

The pipeline processes each query through a series of stages:

```
IDLE
 ├─→ LISTENING (voice only)
 │    └─→ TRANSCRIBING
 │         └─→ VALIDATING
 └─→ VALIDATING (text queries skip to here)
      └─→ QUERY_ANALYSIS
           └─→ RETRIEVING
                ├─→ RERANKING
                │    └─→ CONFIDENCE_CHECK
                └─→ CONFIDENCE_CHECK (skip reranking)
                     ├─→ GENERATING
                     │    └─→ GROUNDING_CHECK
                     │         ├─→ COMPLETE ✓
                     │         └─→ ABSTAINED
                     └─→ ABSTAINED

Error recovery:
  RETRIEVING/RERANKING → RETRYING → (retry same stage)
  RETRIEVING → FALLBACK → (alternative strategy)

Terminal states: COMPLETE, ERROR, ABSTAINED
```

## API Contracts

| Method | Endpoint                      | Description                |
|--------|-------------------------------|----------------------------|
| GET    | `/health`                     | Service health check       |
| POST   | `/api/v1/query`               | Text query                 |
| POST   | `/api/v1/voice/query`         | Voice query (audio upload) |
| GET    | `/api/v1/analytics/summary`   | Analytics summary          |
| GET    | `/api/v1/analytics/latency`   | Detailed latency stats     |

## Key Design Decisions

1. **Provider Abstraction**: STT, retrieval, and generation are behind protocols/interfaces. Swap implementations without touching the orchestrator.

2. **Dependency Injection**: The orchestrator receives all services through its constructor. No service is hard-coded.

3. **Honest Placeholders**: Unimplemented features return `not_implemented` status, never fake results.

4. **Abstention as First-Class**: The pipeline treats "I don't know" as a valid, non-error outcome.

5. **Offline/Online Split**: Corpus processing (chunking, embedding, indexing) is fully separated from request-time processing.

## Integration Points for Next Developer

See `backend/app/pipeline/interfaces.py` for the service protocols:

- `SpeechService` — STT provider implementation
- `QueryAnalyzer` — Query processing logic
- `Retriever` — Retrieval strategy implementation
- `Reranker` — Candidate reranking
- `AnswerGenerator` — LLM-based generation
- `GuardrailService` — Safety and quality checks
- `QueryRouter` — Adaptive retrieval routing

Wire implementations in `backend/app/pipeline/orchestrator.py → get_orchestrator()`.
