"""
Tests — Evaluation Schemas & Retrieval Metrics
"""

import math
import pytest

from app.evaluation.metrics import (
    aggregate_retrieval_metrics,
    evaluate_retrieval_query,
    hit_rate_at_k,
    ndcg_at_k,
    precision_at_k,
    recall_at_k,
    reciprocal_rank_at_k,
)
from app.evaluation.schemas import (
    DatasetIntegrityError,
    DatasetProvenance,
    DatasetSourceType,
    EvalDataset,
    EvalDocument,
    EvalQuery,
    RelevanceJudgment,
)


def test_recall_precision_mrr_hit_rate_exact():
    # Relevant docs: d1, d3, d5 (3 total relevant)
    relevant = {"d1": 1, "d3": 1, "d5": 2}
    # Retrieved order: d2 (miss), d3 (hit @ rank 2), d1 (hit @ rank 3), d4 (miss)
    retrieved = ["d2", "d3", "d1", "d4"]

    assert recall_at_k(retrieved, relevant, k=1) == pytest.approx(0.0)
    assert recall_at_k(retrieved, relevant, k=2) == pytest.approx(1 / 3)
    assert recall_at_k(retrieved, relevant, k=4) == pytest.approx(2 / 3)

    assert precision_at_k(retrieved, relevant, k=1) == pytest.approx(0.0)
    assert precision_at_k(retrieved, relevant, k=2) == pytest.approx(0.5)
    assert precision_at_k(retrieved, relevant, k=4) == pytest.approx(0.5)

    assert reciprocal_rank_at_k(retrieved, relevant, k=1) == pytest.approx(0.0)
    assert reciprocal_rank_at_k(retrieved, relevant, k=4) == pytest.approx(0.5)

    assert hit_rate_at_k(retrieved, relevant, k=1) == 0.0
    assert hit_rate_at_k(retrieved, relevant, k=2) == 1.0


def test_ndcg_at_k_graded_relevance():
    # Graded relevance: d1=2 (gain 3), d2=1 (gain 1)
    grades = {"d1": 2, "d2": 1}
    # Ideal order [d1, d2]: IDCG@2 = 3/log2(2) + 1/log2(3)
    idcg = 3.0 / math.log2(2) + 1.0 / math.log2(3)
    # Actual order [d2, d1]: DCG@2 = 1/log2(2) + 3/log2(3)
    dcg = 1.0 / math.log2(2) + 3.0 / math.log2(3)

    assert ndcg_at_k(["d1", "d2"], grades, k=2) == pytest.approx(1.0)
    assert ndcg_at_k(["d2", "d1"], grades, k=2) == pytest.approx(dcg / idcg)
    assert ndcg_at_k(["d9"], grades, k=2) == pytest.approx(0.0)


def test_duplicate_retrieved_ids_cannot_inflate_metrics():
    relevant = {"d1": 1, "d2": 1}
    retrieved = ["d1", "d1", "d1", "d2"]
    # After deduplication: ["d1", "d2"]
    assert recall_at_k(retrieved, relevant, k=2) == pytest.approx(1.0)
    assert precision_at_k(retrieved, relevant, k=2) == pytest.approx(1.0)
    # Only d1 twice -> unique ["d1"] -> recall@2 is 0.5, precision@2 is 0.5
    assert recall_at_k(["d1", "d1"], relevant, k=2) == pytest.approx(0.5)
    assert precision_at_k(["d1", "d1"], relevant, k=2) == pytest.approx(0.5)


def test_invalid_k_raises():
    with pytest.raises(ValueError, match="positive"):
        recall_at_k(["d1"], {"d1": 1}, k=0)


def test_aggregate_per_language_metrics():
    q1 = evaluate_retrieval_query(["d1", "d2"], {"d1": 1}, k_values=(1, 5))
    q2 = evaluate_retrieval_query(["d2", "d1"], {"d1": 1}, k_values=(1, 5))
    overall, by_lang = aggregate_retrieval_metrics([("en", q1), ("hi", q2)])

    assert overall["recall@1"] == pytest.approx(0.5)
    assert overall["recall@5"] == pytest.approx(1.0)
    assert by_lang["en"]["recall@1"] == pytest.approx(1.0)
    assert by_lang["hi"]["recall@1"] == pytest.approx(0.0)


def test_eval_dataset_integrity_checks():
    prov = DatasetProvenance(
        dataset_id="unit-test",
        source_type=DatasetSourceType.SYNTHETIC,
    )
    ds = EvalDataset(
        provenance=prov,
        documents=[EvalDocument(doc_id="d1", text="alpha", language="en")],
        queries=[EvalQuery(query_id="q1", text="what?", language="en")],
        judgments=[RelevanceJudgment(query_id="q1", doc_id="d1", relevance=1)],
    )
    ds.validate_integrity()

    bad = ds.model_copy(
        update={"judgments": [RelevanceJudgment(query_id="q1", doc_id="missing", relevance=1)]}
    )
    with pytest.raises(DatasetIntegrityError, match="unknown doc_id"):
        bad.validate_integrity()

