# SAMVAD Phase 5 — Multilingual & Voice Evaluation Report

## 1. Multilingual Retrieval Benchmark by Strategy

| Strategy | Recall@1 | Recall@5 | MRR@5 | nDCG@5 | Avg Latency (ms) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `lexical_bm25` | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.06 |
| `dense_tfidf_svd` | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.02 |
| `hybrid_rrf` | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.40 |

## 2. Per-Language Retrieval Breakdown (Hybrid RRF)

| Language | Language Name | Queries | Recall@5 | MRR@5 | nDCG@5 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `bn` | Bengali (বাংলা) | 2 | 1.0000 | 1.0000 | 1.0000 |
| `en` | English | 3 | 1.0000 | 1.0000 | 1.0000 |
| `hi` | Hindi (हिन्दी) | 2 | 1.0000 | 1.0000 | 1.0000 |

## 3. Speech-Aware Normalization (STT Error Isolation)

| Condition | HitRate@3 | Retrieval Impact |
| :--- | :--- | :--- |
| Raw Unnormalized STT Transcripts (with fillers / disfluencies) | 3/3 (100.0%) | Baseline |
| Normalized Speech Queries (SpeechNormalizer M5.2) | 3/3 (100.0%) | +0.0% improvement |