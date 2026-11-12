"""
Tests — Phase 2 Lexical (BM25) Retriever & Benchmark Integration
"""

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
from app.ingestion.chunker import DocumentChunk
from app.retrieval.lexical import LexicalRetriever, tokenize_unicode
from app.schemas.pipeline import ChunkMetadata


def test_unicode_tokenizer_preserves_indic_matras():
    tokens = tokenize_unicode("गोवा की राजधानी पणजी है।")
    # Must preserve full Devanagari words with matras, not split on vowel signs
    assert "गोवा" in tokens
    assert "राजधानी" in tokens
    assert "पणजी" in tokens


@pytest.mark.asyncio
async def test_lexical_bm25_retrieval_and_language_filter():
    chunks = [
        DocumentChunk(
            text="Bengaluru is the capital city of Karnataka in southern India.",
            metadata=ChunkMetadata(chunk_id="d1", parent_document_id="d1", language="en"),
        ),
        DocumentChunk(
            text="गोवा भारत के पश्चिम तट पर स्थित राज्य है और पणजी इसकी राजधानी है।",
            metadata=ChunkMetadata(chunk_id="d2", parent_document_id="d2", language="hi"),
        ),
        DocumentChunk(
            text="Panaji is the capital of Goa.",
            metadata=ChunkMetadata(chunk_id="d3", parent_document_id="d3", language="en"),
        ),
    ]

    retriever = LexicalRetriever(chunks)
    assert await retriever.health_check() is True

    en_hits = await retriever.retrieve("capital of Karnataka", top_k=2, language="en")
    assert len(en_hits) >= 1
    assert en_hits[0].chunk_id == "d1"
    assert en_hits[0].retrieval_method == "lexical"
    assert en_hits[0].retrieval_score is not None and en_hits[0].retrieval_score > 0

    hi_hits = await retriever.retrieve("पणजी राजधानी", top_k=2, language="hi")
    assert len(hi_hits) == 1
    assert hi_hits[0].chunk_id == "d2"


@pytest.mark.asyncio
async def test_lexical_retriever_benchmarked_via_phase1_runner(tmp_path):
    docs = [
        EvalDocument(doc_id="d1", text="Bengaluru is the capital of Karnataka.", language="en"),
        EvalDocument(doc_id="d2", text="Panaji is the capital of Goa.", language="en"),
        EvalDocument(doc_id="d3", text="पणजी गोवा की राजधानी है।", language="hi"),
    ]
    ds = EvalDataset(
        provenance=DatasetProvenance(
            dataset_id="bm25-smoke-v1",
            version="1.0",
            source_type=DatasetSourceType.SYNTHETIC,
            split="dev",
            languages=["en", "hi"],
        ),
        documents=docs,
        queries=[
            EvalQuery(query_id="q1", text="capital of Karnataka", language="en"),
            EvalQuery(query_id="q2", text="गोवा की राजधानी", language="hi"),
        ],
        judgments=[
            RelevanceJudgment(query_id="q1", doc_id="d1", relevance=1),
            RelevanceJudgment(query_id="q2", doc_id="d3", relevance=1),
        ],
    )

    chunks = [
        DocumentChunk(
            text=d.text,
            metadata=ChunkMetadata(chunk_id=d.doc_id, parent_document_id=d.doc_id, language=d.language),
        )
        for d in docs
    ]
    retriever = LexicalRetriever(chunks)
    summary, exp_dir = await run_retrieval_experiment(
        dataset=ds,
        retriever=retriever,
        config=ExperimentConfig(
            experiment_name="bm25-baseline",
            retriever_name="lexical",
            top_k=3,
            k_values=[1, 3],
        ),
        output_root=tmp_path,
    )

    assert summary.num_errors == 0
    assert summary.overall_metrics["recall@1"] == 1.0
    assert summary.overall_metrics["mrr@3"] == 1.0
    assert (exp_dir / "summary.md").exists()

