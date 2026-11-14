"""
Tests — Context Compression & Sentence Pruning (Phase 6 — M6.3)
"""

from app.pipeline.interfaces import ScoredChunk
from app.retrieval.context_builder import ContextCompressor, ContextOptimizer
from app.schemas.pipeline import ChunkMetadata


def test_compressor_prunes_peripheral_sentences():
    compressor = ContextCompressor(min_sentences_to_compress=2, max_sentences_per_chunk=2)

    text = (
        "ISRO launched Chandrayaan-3 successfully in July 2023. "
        "The weather in Sriharikota was mostly sunny with moderate wind. "
        "The propulsion module carried the lander configuration to lunar orbit. "
        "Several dignitaries and guests watched the launch from the viewing gallery."
    )

    chunk = ScoredChunk(
        chunk_id="c_test",
        text=text,
        retrieval_score=0.9,
        metadata=ChunkMetadata(
            chunk_id="c_test",
            parent_document_id="p1",
            language="en",
            extra={},
        ),
    )

    query = "Chandrayaan-3 lunar orbit propulsion module"
    compressed = compressor.compress_chunk(chunk, query)

    # Should retain high-salience sentences matching query terms
    assert "Chandrayaan-3" in compressed.text
    assert "propulsion module" in compressed.text
    # Should have pruned peripheral sentences
    assert "viewing gallery" not in compressed.text
    assert len(compressed.text) < len(text)
    assert compressed.metadata.extra.get("compressed") is True


def test_compressor_respects_short_chunks():
    compressor = ContextCompressor(min_sentences_to_compress=3)
    text = "Short text with only one sentence."
    chunk = ScoredChunk(chunk_id="c_short", text=text, retrieval_score=0.9)

    compressed = compressor.compress_chunk(chunk, "some query")
    assert compressed.text == text


def test_context_optimizer_with_compression_enabled():
    optimizer = ContextOptimizer(enable_compression=True)
    text = (
        "First sentence defines the core algorithm. "
        "Second sentence is completely irrelevant filler content about lunch menus. "
        "Third sentence details the core algorithm performance benchmarks. "
        "Fourth sentence talks about the office coffee machine."
    )
    chunk = ScoredChunk(
        chunk_id="c1",
        text=text,
        retrieval_score=0.95,
        metadata=ChunkMetadata(chunk_id="c1", parent_document_id="p1", language="en", extra={}),
    )

    optimized = optimizer.optimize([chunk], max_chunks=1, query="core algorithm benchmarks")
    assert len(optimized) == 1
    assert "core algorithm" in optimized[0].text
    assert "coffee machine" not in optimized[0].text

