"""
Tests — Context Optimizer & Deduplication (Phase 3 — M3.3)
"""

from app.pipeline.interfaces import ScoredChunk
from app.retrieval.context_builder import ContextOptimizer, compute_token_jaccard


def test_compute_token_jaccard():
    sim_identical = compute_token_jaccard("apple banana orange", "orange banana apple")
    assert sim_identical == 1.0

    sim_disjoint = compute_token_jaccard("apple banana", "car airplane train")
    assert sim_disjoint == 0.0

    sim_partial = compute_token_jaccard("machine learning algorithms", "deep learning algorithms")
    assert 0.4 < sim_partial < 0.8


def test_context_optimizer_deduplication():
    optimizer = ContextOptimizer(dedup_similarity_threshold=0.75)

    chunk_1 = ScoredChunk(
        chunk_id="c1",
        text="The quick brown fox jumps over the lazy dog in the meadow.",
        retrieval_score=0.9,
    )
    # Near identical chunk (duplicate)
    chunk_2 = ScoredChunk(
        chunk_id="c2",
        text="The quick brown fox jumps over the lazy dog in the sunny meadow.",
        retrieval_score=0.85,
    )
    # Different chunk
    chunk_3 = ScoredChunk(
        chunk_id="c3",
        text="Quantum computing harnesses superposition and entanglement for rapid simulation.",
        retrieval_score=0.7,
    )

    optimized = optimizer.optimize([chunk_1, chunk_2, chunk_3], max_chunks=3)
    # chunk_2 should be dropped due to similarity with chunk_1
    assert len(optimized) == 2
    assert optimized[0].chunk_id == "c1"
    assert optimized[1].chunk_id == "c3"


def test_context_optimizer_token_budget():
    # Set a tiny token limit (~10 tokens = ~40 chars)
    optimizer = ContextOptimizer(max_context_tokens=15)

    c1 = ScoredChunk(chunk_id="c1", text="First short sentence.", retrieval_score=0.9)
    c2 = ScoredChunk(chunk_id="c2", text="Second relatively long sentence that will exceed budget.", retrieval_score=0.8)

    optimized = optimizer.optimize([c1, c2], max_chunks=5)
    # Only c1 should fit within budget
    assert len(optimized) == 1
    assert optimized[0].chunk_id == "c1"

