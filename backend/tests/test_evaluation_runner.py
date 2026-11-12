"""
Tests — Reproducible Evaluation Runner
"""

import json
import pytest

from app.evaluation.runner import ExperimentConfig, run_retrieval_experiment
from app.evaluation.schemas import (
    DatasetProvenance,
    DatasetSourceType,
    EvalDataset,
    EvalDocument,
    EvalQuery,
    RelevanceJudgment,
)
from app.pipeline.interfaces import ScoredChunk


class _DeterministicMockRetriever:
    strategy_name = "mock"

    async def retrieve(self, query: str, top_k: int = 10, language: str | None = None):
        if "capital" in query.lower():
            return [
                ScoredChunk(chunk_id="d1", text="Bengaluru", retrieval_score=0.9, retrieval_method="mock"),
                ScoredChunk(chunk_id="d2", text="Mumbai", retrieval_score=0.4, retrieval_method="mock"),
            ][:top_k]
        return [
            ScoredChunk(chunk_id="d2", text="Mumbai", retrieval_score=0.8, retrieval_method="mock"),
        ][:top_k]

    async def health_check(self) -> bool:
        return True


def _sample_dataset() -> EvalDataset:
    return EvalDataset(
        provenance=DatasetProvenance(
            dataset_id="test-synthetic-v1",
            version="1.0",
            source_type=DatasetSourceType.SYNTHETIC,
            split="test",
            languages=["en", "hi"],
        ),
        documents=[
            EvalDocument(doc_id="d1", text="Bengaluru is the capital of Karnataka.", language="en"),
            EvalDocument(doc_id="d2", text="भारत की राजधानी नई दिल्ली है।", language="hi"),
        ],
        queries=[
            EvalQuery(query_id="q1", text="What is the capital of Karnataka?", language="en"),
            EvalQuery(query_id="q2", text="भारत की राजधानी क्या है?", language="hi"),
        ],
        judgments=[
            RelevanceJudgment(query_id="q1", doc_id="d1", relevance=2),
            RelevanceJudgment(query_id="q2", doc_id="d2", relevance=1),
        ],
    )


@pytest.mark.asyncio
async def test_runner_produces_reproducible_artifacts(tmp_path):
    ds = _sample_dataset()
    retriever = _DeterministicMockRetriever()
    cfg = ExperimentConfig(
        experiment_name="baseline-mock",
        retriever_name="mock",
        top_k=5,
        k_values=[1, 5],
    )

    s1, dir1 = await run_retrieval_experiment(
        dataset=ds, retriever=retriever, config=cfg, output_root=tmp_path
    )
    s2, dir2 = await run_retrieval_experiment(
        dataset=ds, retriever=retriever, config=cfg, output_root=tmp_path
    )

    assert s1.overall_metrics == s2.overall_metrics
    assert s1.by_language_metrics == s2.by_language_metrics
    assert s1.num_queries == 2
    assert s1.num_errors == 0
    assert s1.overall_metrics["recall@1"] == 1.0
    assert s1.overall_metrics["ndcg@5"] == 1.0

    for fname in ("config.json", "predictions.jsonl", "summary.json", "summary.md"):
        assert (dir1 / fname).exists()
        assert (dir2 / fname).exists()

    lines = (dir1 / "predictions.jsonl").read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 2
    assert json.loads(lines[0])["query_id"] == "q1"


@pytest.mark.asyncio
async def test_runner_refuses_to_overwrite_existing_experiment_id(tmp_path):
    ds = _sample_dataset()
    retriever = _DeterministicMockRetriever()
    cfg = ExperimentConfig(experiment_name="fixed", retriever_name="mock")

    await run_retrieval_experiment(
        dataset=ds,
        retriever=retriever,
        config=cfg,
        output_root=tmp_path,
        experiment_id="exp-immutable-001",
    )
    with pytest.raises(FileExistsError):
        await run_retrieval_experiment(
            dataset=ds,
            retriever=retriever,
            config=cfg,
            output_root=tmp_path,
            experiment_id="exp-immutable-001",
        )

