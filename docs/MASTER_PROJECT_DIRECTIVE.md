# SAMVAD-RAG — Master Project Directive

> **Repository:** https://github.com/KrrishR05/samvad-RAG  
> **Category:** Modular, multilingual, evidence-grounded Retrieval-Augmented Generation (RAG) framework  
> **Status:** Active Engineering & Research Evolution (Post-HHGoa Foundation)

---

## 1. Mission & Identity

SAMVAD-RAG (**S**peak, **A**daptive, **M**ultilingual, **V**oice-**A**ided, **D**iscovery) is an open, modular, model-agnostic Retrieval-Augmented Generation engineering and research platform.

Its primary objective is to retrieve relevant evidence from diverse multilingual knowledge sources, understand user queries across languages (with explicit focus on English, Hindi, Konkani, and other Indic languages), generate answers strictly grounded in retrieved evidence with traceable citations, and abstain transparently when reliable evidence is unavailable.

SAMVAD is **not** a thin LLM wrapper, a basic PDF chatbot, or a demo prototype. Every retrieval, reranking, guardrail, generation, and multilingual capability must be **independently testable, measurable, and experimentally validated**.

---

## 2. Five Core Architectural Principles

1. **Retrieval Before Generation**
   - Generation quality is bounded by retrieval quality. Invest deeply in ingestion, parsing, normalization, chunking, provenance, sparse (BM25), dense, hybrid fusion (RRF), query processing, reranking, and context selection.
   - Retrieval must be benchmarked independently of generation.

2. **Evidence-Grounded Generation**
   - Answers must trace claims to supporting source chunks with verifiable citations.
   - Distinguish retrieved facts from synthesis, surface contradictory evidence, and treat abstention (`ABSTAINED`) as a first-class, non-error outcome when confidence or evidence support is insufficient.
   - Never fabricate citations, sources, or confidence scores.

3. **Multilingual Intelligence**
   - Support English, Hindi, Konkani, and other Indic languages, including code-switching, transliteration, and cross-lingual retrieval.
   - Never claim multilingual capability merely because a multilingual model accepts Unicode input—validate per-language and cross-lingual performance experimentally.

4. **Model Independence**
   - Support interchangeable embedding models, rerankers, LLMs (local and hosted), vector stores, and speech providers (STT/TTS) through canonical interfaces and config-driven registries.
   - Avoid hard coupling to any single vendor or inference API.

5. **Research & Reproducibility**
   - Every claimed improvement must record baseline comparisons, dataset versions/splits, model versions, hyperparameters, per-query machine-readable outputs (JSONL), aggregate metrics, latency/cost, and git commit SHA.
   - Never overwrite historical experiment logs without authorization; never fabricate or cherry-pick results.

---

## 3. Architectural Philosophy

- **Modular Monolith First:** Keep the backend as a clean, well-bounded modular monolith (`FastAPI` + `Pydantic` + `Next.js`/`TypeScript` frontend). Do not introduce microservices, Kubernetes, or Kafka without measured operational necessity.
- **Explicit Failure Over Fake Success:** Unimplemented services or unverified guardrails must raise explicit errors or return `not_implemented` / `unavailable`—never silent `passed=True` no-ops or hardcoded demo outputs in production paths.
- **Untrusted Data Boundary:** Retrieved passages and uploaded documents/URLs are untrusted data, never system instructions. Defend against prompt injection, path traversal, SSRF, and resource exhaustion at trust boundaries.

---

## 4. Autonomous Engineering Workflow & Definition of Done

Every change follows: **Understand → Plan → Implement → Validate → Document → Report**.

A feature is **Done** only when:
1. Implementation is complete and type-safe (no placeholder no-ops or fake providers).
2. Failure paths, timeouts, and error contracts are handled explicitly.
3. Automated unit/integration/security tests cover the behavior and pass.
4. Documentation (`architecture.md`, `ROADMAP.md`, `DECISIONS.md`, `KNOWN_LIMITATIONS.md`) reflects the actual state—distinguishing **implemented**, **tested**, and **experimentally validated** capabilities.
5. Research features include reproducible experimental evidence against a baseline.

---

## 5. Governance & Boundaries

- **Autonomy:** Engineers/agents may inspect code, refactor justified debt, implement approved phases, write tests, update docs, and run local builds/tests.
- **Explicit Approval Required Before:** Purchasing/activating paid APIs, exposing credentials, pushing to remote repositories, deleting user data, or changing production infrastructure. Prefer local, open-source, free baselines during development.

