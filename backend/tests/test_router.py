"""
Tests — Adaptive Query Router (Phase 6 — M6.1)
"""

import pytest

from app.pipeline.interfaces import AnalyzedQuery
from app.retrieval.router import AdaptiveRouter


@pytest.mark.asyncio
async def test_router_exact_acronym_and_identifier():
    router = AdaptiveRouter()

    # Acronyms / exact codes -> lexical
    q1 = AnalyzedQuery(original_text="ISRO Chandrayaan mission", processed_text="ISRO Chandrayaan mission")
    res1 = await router.route(q1)
    assert res1 == "lexical"

    # Year / code pattern -> lexical
    q2 = AnalyzedQuery(original_text="Report 2024 summary", processed_text="Report 2024 summary")
    res2 = await router.route(q2)
    assert res2 == "lexical"


@pytest.mark.asyncio
async def test_router_short_keyword():
    router = AdaptiveRouter()

    # 1-2 words keyword lookup -> lexical
    q = AnalyzedQuery(original_text="Bengaluru weather", processed_text="Bengaluru weather")
    res = await router.route(q)
    assert res == "lexical"


@pytest.mark.asyncio
async def test_router_short_conceptual_question():
    router = AdaptiveRouter()

    # Short question with question particle -> dense
    q_en = AnalyzedQuery(original_text="What is machine learning?", processed_text="What is machine learning?")
    assert await router.route(q_en) == "dense"

    q_hi = AnalyzedQuery(original_text="चंद्रयान क्या है?", processed_text="चंद्रयान क्या है?")
    assert await router.route(q_hi) == "dense"


@pytest.mark.asyncio
async def test_router_deep_intensity_and_samvad_system():
    router = AdaptiveRouter()

    # Deep intensity -> hybrid
    q_deep = AnalyzedQuery(
        original_text="Explain system architecture",
        processed_text="Explain system architecture",
        metadata={"intensity": "deep"},
    )
    assert await router.route(q_deep) == "hybrid"

    # About samvad -> hybrid
    q_samvad = AnalyzedQuery(
        original_text="what is samvad?",
        processed_text="what is samvad?",
        metadata={"about_samvad": True},
    )
    assert await router.route(q_samvad) == "hybrid"


@pytest.mark.asyncio
async def test_router_complex_multi_clause():
    router = AdaptiveRouter()

    # Long multi-word complex query -> hybrid
    q_long = AnalyzedQuery(
        original_text="Can you describe how the transformer architecture compares to recurrent networks in processing sequential Indian language text?",
        processed_text="Can you describe how the transformer architecture compares to recurrent networks in processing sequential Indian language text?",
    )
    assert await router.route(q_long) == "hybrid"

