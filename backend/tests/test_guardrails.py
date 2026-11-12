"""
Tests — Guardrails
"""

import pytest

from app.guardrails.interfaces import (
    ConfidenceGuard,
    GroundingGuard,
    InputGuard,
    RelevanceGuard,
)


@pytest.mark.asyncio
async def test_input_guard_allows_valid_query():
    guard = InputGuard()
    res = await guard.check(query="What is SAMVAD?")
    assert res.passed is True


@pytest.mark.asyncio
@pytest.mark.parametrize("bad_query", [None, "", "   \t\n ", "hello\x00world"])
async def test_input_guard_rejects_invalid_queries(bad_query):
    guard = InputGuard()
    res = await guard.check(query=bad_query)
    assert res.passed is False
    assert res.action == "abstain"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "guard_cls",
    [RelevanceGuard, ConfidenceGuard, GroundingGuard],
)
async def test_unimplemented_guardrails_fail_explicitly(guard_cls):
    guard = guard_cls()
    with pytest.raises(NotImplementedError):
        await guard.check(query="test", answer="test", confidence=0.9)

