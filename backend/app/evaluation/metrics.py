"""
SAMVAD Evaluation — Retrieval Metrics

Deterministic, unit-tested Information Retrieval metrics:
  - Recall@K
  - Precision@K
  - MRR@K (Mean Reciprocal Rank)
  - nDCG@K (Normalized Discounted Cumulative Gain with graded relevance)
  - Hit Rate@K

Duplicate retrieved document IDs are deduplicated while preserving the rank
of first appearance so a retriever cannot inflate metrics via duplicates.
"""

from __future__ import annotations

import math
from collections import defaultdict
from typing import Mapping, Sequence


def _dedupe_top_k(retrieved_ids: Sequence[str], k: int) -> list[str]:
    """Validate k > 0 and return up to k unique retrieved IDs in rank order."""
    if k <= 0:
        raise ValueError(f"k must be positive, got {k}.")
    seen: set[str] = set()
    unique: list[str] = []
    for doc_id in retrieved_ids:
        if doc_id not in seen:
            seen.add(doc_id)
            unique.append(doc_id)
            if len(unique) >= k:
                break
    return unique


def _positive_relevant_set(relevant: Mapping[str, int] | set[str]) -> set[str]:
    """Extract IDs with positive relevance (> 0 for graded mappings)."""
    if isinstance(relevant, Mapping):
        return {doc_id for doc_id, grade in relevant.items() if grade > 0}
    return set(relevant)


def recall_at_k(
    retrieved_ids: Sequence[str],
    relevant: Mapping[str, int] | set[str],
    k: int,
) -> float:
    """Fraction of all relevant documents appearing in the top-K results."""
    top_k = _dedupe_top_k(retrieved_ids, k)
    rel_set = _positive_relevant_set(relevant)
    if not rel_set:
        return 0.0
    hits = sum(1 for doc_id in top_k if doc_id in rel_set)
    return hits / len(rel_set)


def precision_at_k(
    retrieved_ids: Sequence[str],
    relevant: Mapping[str, int] | set[str],
    k: int,
) -> float:
    """Fraction of top-K slots containing relevant documents (divided by K)."""
    top_k = _dedupe_top_k(retrieved_ids, k)
    rel_set = _positive_relevant_set(relevant)
    if not rel_set:
        return 0.0
    hits = sum(1 for doc_id in top_k if doc_id in rel_set)
    return hits / k


def reciprocal_rank_at_k(
    retrieved_ids: Sequence[str],
    relevant: Mapping[str, int] | set[str],
    k: int,
) -> float:
    """1 / rank (1-indexed) of the first relevant document within top-K, else 0.0."""
    top_k = _dedupe_top_k(retrieved_ids, k)
    rel_set = _positive_relevant_set(relevant)
    if not rel_set:
        return 0.0
    for idx, doc_id in enumerate(top_k):
        if doc_id in rel_set:
            return 1.0 / (idx + 1)
    return 0.0


def hit_rate_at_k(
    retrieved_ids: Sequence[str],
    relevant: Mapping[str, int] | set[str],
    k: int,
) -> float:
    """1.0 if at least one relevant document appears in top-K, else 0.0."""
    top_k = _dedupe_top_k(retrieved_ids, k)
    rel_set = _positive_relevant_set(relevant)
    if not rel_set:
        return 0.0
    return 1.0 if any(doc_id in rel_set for doc_id in top_k) else 0.0


def ndcg_at_k(
    retrieved_ids: Sequence[str],
    relevance_grades: Mapping[str, int],
    k: int,
) -> float:
    """
    Normalized Discounted Cumulative Gain at K using standard exponential gain:
        DCG@K = sum_{i=0}^{min(n,k)-1} (2^{rel_i} - 1) / log2(i + 2)
    """
    top_k = _dedupe_top_k(retrieved_ids, k)
    positive_grades = sorted(
        (g for g in relevance_grades.values() if g > 0),
        reverse=True,
    )[:k]
    if not positive_grades:
        return 0.0

    idcg = sum(
        ((2**rel) - 1) / math.log2(idx + 2)
        for idx, rel in enumerate(positive_grades)
    )
    if idcg == 0.0:
        return 0.0

    dcg = 0.0
    for idx, doc_id in enumerate(top_k):
        rel = relevance_grades.get(doc_id, 0)
        if rel > 0:
            dcg += ((2**rel) - 1) / math.log2(idx + 2)

    return dcg / idcg


def evaluate_retrieval_query(
    retrieved_ids: Sequence[str],
    relevance_grades: Mapping[str, int],
    k_values: Sequence[int] = (1, 5, 10),
) -> dict[str, float]:
    """Compute all retrieval metrics across requested K cutoffs for one query."""
    metrics: dict[str, float] = {}
    for k in k_values:
        metrics[f"recall@{k}"] = round(recall_at_k(retrieved_ids, relevance_grades, k), 6)
        metrics[f"precision@{k}"] = round(precision_at_k(retrieved_ids, relevance_grades, k), 6)
        metrics[f"mrr@{k}"] = round(reciprocal_rank_at_k(retrieved_ids, relevance_grades, k), 6)
        metrics[f"ndcg@{k}"] = round(ndcg_at_k(retrieved_ids, relevance_grades, k), 6)
        metrics[f"hit_rate@{k}"] = round(hit_rate_at_k(retrieved_ids, relevance_grades, k), 6)
    return metrics


def aggregate_retrieval_metrics(
    per_query_metrics: Sequence[tuple[str, dict[str, float]]],
) -> tuple[dict[str, float], dict[str, dict[str, float]]]:
    """
    Aggregate per-query metrics into overall and per-language means.

    Args:
        per_query_metrics: Sequence of (language_code, metrics_dict) pairs.

    Returns:
        (overall_mean_metrics, by_language_mean_metrics)
    """
    if not per_query_metrics:
        return {}, {}

    overall_sums: dict[str, float] = defaultdict(float)
    by_lang_sums: dict[str, dict[str, float]] = defaultdict(lambda: defaultdict(float))
    by_lang_counts: dict[str, int] = defaultdict(int)

    for lang, m in per_query_metrics:
        lang_key = lang or "unknown"
        by_lang_counts[lang_key] += 1
        for metric_name, val in m.items():
            overall_sums[metric_name] += val
            by_lang_sums[lang_key][metric_name] += val

    n = len(per_query_metrics)
    overall = {k: round(v / n, 6) for k, v in sorted(overall_sums.items())}
    by_lang = {
        lang_key: {
            k: round(v / by_lang_counts[lang_key], 6)
            for k, v in sorted(sums.items())
        }
        for lang_key, sums in sorted(by_lang_sums.items())
    }
    return overall, by_lang

