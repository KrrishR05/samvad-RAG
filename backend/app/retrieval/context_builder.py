"""
SAMVAD Retrieval — Context Builder & Optimization (Phase 3 — M3.3)

Optimizes retrieved passages before injection into LLM generation context:
  - Deduplication: Drops near-identical passages based on character/token Jaccard similarity.
  - Token-Budget Packing: Bounds total context length within a configurable token budget.
  - Context Structure: Formats chunks with explicit provenance headers (doc ID, chunk index).
"""

from __future__ import annotations

import re
from typing import Sequence

from app.pipeline.interfaces import ScoredChunk


def compute_token_jaccard(text_a: str, text_b: str) -> float:
    """Compute token Jaccard similarity between two texts."""
    tokens_a = set(re.findall(r"\w+", text_a.lower()))
    tokens_b = set(re.findall(r"\w+", text_b.lower()))
    if not tokens_a or not tokens_b:
        return 0.0
    intersection = len(tokens_a & tokens_b)
    union = len(tokens_a | tokens_b)
    return intersection / union if union > 0 else 0.0


class ContextOptimizer:
    """
    Deduplicates and packs ScoredChunks into a structured, bounded context window.
    """

    def __init__(
        self,
        max_context_tokens: int = 3000,
        dedup_similarity_threshold: float = 0.80,
    ) -> None:
        self.max_context_tokens = max_context_tokens
        self.dedup_similarity_threshold = dedup_similarity_threshold

    def optimize(
        self,
        candidates: Sequence[ScoredChunk],
        max_chunks: int = 5,
    ) -> list[ScoredChunk]:
        """
        Deduplicate candidates, filter redundant spans, and pack within token budget.
        """
        if not candidates:
            return []

        selected: list[ScoredChunk] = []
        estimated_total_tokens = 0

        for cand in candidates:
            if len(selected) >= max_chunks:
                break

            # 1. Deduplication check against already selected chunks
            is_duplicate = False
            for prev in selected:
                sim = compute_token_jaccard(cand.text, prev.text)
                if sim >= self.dedup_similarity_threshold:
                    is_duplicate = True
                    break

            if is_duplicate:
                continue

            # 2. Approximate token count (roughly 4 characters per token for English/Indic)
            cand_tokens = max(1, len(cand.text) // 4)
            if estimated_total_tokens + cand_tokens > self.max_context_tokens and selected:
                # Stop if adding this chunk exceeds token budget, but always keep at least 1 chunk
                break

            selected.append(cand)
            estimated_total_tokens += cand_tokens

        return selected

