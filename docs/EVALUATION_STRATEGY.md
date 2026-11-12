# SAMVAD-RAG — Evaluation & Benchmarking Strategy

> Evaluation is a first-class engineering subsystem. No retrieval, chunking, reranking, grounding, or multilingual claim is valid without reproducible experimental evidence.

---

## 1. Evaluation Dimensions

### A. Retrieval Metrics (Independent of Generation)
Implemented deterministically in Python and verified against hand-calculated fixtures:
- **Recall@K** ($K \in \{1, 5, 10, 20\}$): Fraction of relevant passages retrieved in top-$K$.
- **Precision@K** ($K \in \{1, 5, 10\}$): Fraction of top-$K$ retrieved passages that are relevant.
- **MRR@K** (Mean Reciprocal Rank): Average reciprocal rank of the first relevant passage.
- **nDCG@K** (Normalized Discounted Cumulative Gain): Supports graded relevance judgments (0, 1, 2, ...).
- **Hit Rate@K**: Fraction of queries with at least one relevant passage in top-$K$.

**Mandatory Baselines for Fair Comparison (identical corpus, splits, qrels):**
1. Sparse Lexical (`BM25`)
2. Dense Vector (`FAISS` + baseline embedding model)
3. Hybrid (`BM25` + `Dense` via Reciprocal Rank Fusion)
4. Hybrid + Cross-Encoder Reranking

### B. Generation & Grounding Metrics
- **Deterministic / Programmatic Checks (Primary):**
  - **Citation Existence & Format:** Every cited ID `[k]` maps to a passage actually supplied in the evidence package.
  - **Abstention Accuracy / F1:** Evaluated on a dedicated unanswerable / out-of-domain query split.
  - **Lexical/Entity Grounding & Numeric Consistency:** Checks whether numbers, named entities, and quoted facts in the answer appear in cited sources.
- **LLM-as-a-Judge (Supplementary Only):**
  - Faithfulness (claim-level support), Answer Relevance, Context Relevance, Contradiction Handling.
  - Must record exact judge model ID, temperature (0.0), prompt hash, and known biases.

### C. Multilingual & Voice Evaluation
- **Per-Language Breakdown:** Report metrics separately for English (`en`), Hindi (`hi`), Konkani (`kok`), and other tested Indic languages—never hide poor low-resource scores inside English-dominated averages.
- **Cross-Lingual & Code-Switched Splits:** Query in language $A$, corpus in language $B$; Romanized/transliterated Indic queries.
- **STT Isolation:** Measure Word Error Rate (WER) / Character Error Rate (CER) on speech datasets independently, then compare RAG Recall@K on **gold transcripts** vs **ASR transcripts** to isolate speech errors from retrieval errors.

### D. System Performance & Cost Metrics
- **Latency:** `P50`, `P70`, `P95`, `P99`, `mean`, `min`, `max` per stage and end-to-end (cold-start vs warm-request separated).
- **Resource & Cost:** Peak RSS memory, index disk size, throughput (QPS), embedding generation time, prompt/completion tokens per query, estimated USD/INR cost per 1k queries.

---

## 2. Dataset Integrity Protocol

Before adopting any dataset (including **AI4Bharat MSMARCO-XI** or custom corpora):
1. Verify source URL, license, and redistribution terms.
2. Inspect raw schema, splits, query/passage counts, and language tags—never hardcode column assumptions blindly.
3. Verify presence and format of relevance judgments (`qrels`).
4. Record dataset version/commit hash and preprocessing script parameters.
5. Clearly label any synthetic test sets as `"source_type": "synthetic"`.

---

## 3. Reproducibility & Experiment Provenance

Every benchmark execution outputs:
1. `backend/benchmarks/results/<experiment_id>/config.json` — git SHA, Python/package versions, hardware (CPU/GPU/RAM), dataset ID/split/checksum, chunking config, embedding/reranker/LLM model IDs & parameters, seed.
2. `backend/benchmarks/results/<experiment_id>/predictions.jsonl` — per-query ID, query text, language, retrieved chunk IDs & scores, generated answer, citations, abstention flag, per-stage latency, token counts, errors.
3. `backend/benchmarks/results/<experiment_id>/summary.json` (and `.md`) — aggregate retrieval, grounding, and latency metrics.

Historical experiment directories are append-only and never overwritten without explicit authorization.

