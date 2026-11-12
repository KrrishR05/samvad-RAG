"""
Tests — Embedding Providers & Dense Cosine Retriever
"""

from __future__ import annotations

import numpy as np
import pytest

from app.core.errors import ConfigurationError, RetrievalError
from app.embeddings.providers import LocalTfidfSVDProvider, OpenAICompatibleEmbeddingProvider
from app.ingestion.chunker import DocumentChunk
from app.retrieval.dense import DenseRetriever
from app.schemas.pipeline import ChunkMetadata


def _make_chunks() -> list[DocumentChunk]:
    return [
        DocumentChunk(
            text="Bengaluru is the capital city of Karnataka and a major technology hub.",
            metadata=ChunkMetadata(chunk_id="c1", parent_document_id="doc1", language="en"),
        ),
        DocumentChunk(
            text="नई दिल्ली भारत की राजधानी है और यहाँ संसद भवन स्थित है।",
            metadata=ChunkMetadata(chunk_id="c2", parent_document_id="doc2", language="hi"),
        ),
        DocumentChunk(
            text="Photosynthesis converts sunlight into chemical energy in green plants.",
            metadata=ChunkMetadata(chunk_id="c3", parent_document_id="doc3", language="en"),
        ),
    ]


@pytest.mark.asyncio
async def test_local_tfidf_svd_fit_and_norm():
    provider = LocalTfidfSVDProvider(target_dimension=32)
    assert await provider.health_check() is False
    with pytest.raises(RetrievalError):
        await provider.embed_query("capital")

    vecs = await provider.embed_documents([c.text for c in _make_chunks()])
    assert await provider.health_check() is True
    assert vecs.shape[0] == 3
    norms = np.linalg.norm(vecs, axis=1)
    assert np.allclose(norms, 1.0, atol=1e-4)


@pytest.mark.asyncio
async def test_dense_retriever_ranking_language_filter_and_persistence(tmp_path):
    persist_dir = tmp_path / "vec_idx"
    retriever = DenseRetriever(persist_dir=persist_dir)
    assert await retriever.health_check() is False

    chunks = _make_chunks()
    await retriever.build_index(chunks)
    assert await retriever.health_check() is True

    en_hits = await retriever.retrieve("capital of Karnataka Bengaluru", top_k=2, language="en")
    assert en_hits
    assert en_hits[0].chunk_id == "c1"
    assert en_hits[0].retrieval_method == "dense"
    assert all(hit.metadata.language == "en" for hit in en_hits)

    hi_hits = await retriever.retrieve("भारत की राजधानी", top_k=2, language="hi")
    assert hi_hits
    assert hi_hits[0].chunk_id == "c2"

    # Reload persisted index in a fresh instance
    reloaded = DenseRetriever(persist_dir=persist_dir)
    assert reloaded.load_index() is True
    reloaded_hits = await reloaded.retrieve("Bengaluru Karnataka", top_k=2)
    assert reloaded_hits and reloaded_hits[0].chunk_id == "c1"

    # Clear index removes persisted files
    await reloaded.build_index([])
    assert await reloaded.health_check() is False
    assert not (persist_dir / "vectors.npz").exists()


def test_openai_embedding_provider_requires_model():
    with pytest.raises(ConfigurationError):
        OpenAICompatibleEmbeddingProvider(model_name="")

