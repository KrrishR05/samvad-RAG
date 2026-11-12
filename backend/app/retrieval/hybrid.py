"""
SAMVAD Retrieval — Hybrid (Reciprocal Rank Fusion)

Combines dense vector search and sparse BM25 lexical search using weighted
Reciprocal Rank Fusion (RRF), degrading gracefully if one leg fails while
failing honestly if no configured retriever succeeds.
"""

from __future__ import annotations

import asyncio
from typing import Optional, Sequence

from app.core.errors import RetrievalError
from app.core.logging import get_logger
from app.pipeline.interfaces import Retriever, ScoredChunk

logger = get_logger("retrieval.hybrid")


class HybridRetriever:
    """Hybrid retrieval combining dense and lexical strategies via RRF."""

    strategy_name = "hybrid"

    def __init__(
        self,
        dense_retriever: Optional[Retriever] = None,
        lexical_retriever: Optional[Retriever] = None,
        dense_weight: float = 0.7,
        lexical_weight: float = 0.3,
        rrf_k: int = 60,
    ) -> None:
        if rrf_k <= 0:
            raise ValueError("rrf_k must be positive.")
        if dense_weight < 0 or lexical_weight < 0:
            raise ValueError("Retriever weights must be non-negative.")
        self.dense_retriever = dense_retriever
        self.lexical_retriever = lexical_retriever
        self.dense_weight = dense_weight
        self.lexical_weight = lexical_weight
        self.rrf_k = rrf_k

    async def retrieve(
        self,
        query: str,
        top_k: int = 10,
        language: Optional[str] = None,
    ) -> Sequence[ScoredChunk]:
        """Run dense and lexical retrieval concurrently and fuse via weighted RRF."""
        if top_k <= 0:
            raise ValueError("top_k must be positive.")
        if self.dense_retriever is None and self.lexical_retriever is None:
            raise RetrievalError("HybridRetriever requires at least one sub-retriever.")

        candidate_k = max(top_k * 2, top_k)
        legs: list[tuple[str, float, Retriever]] = []
        if self.dense_retriever is not None and self.dense_weight > 0:
            legs.append(("dense", self.dense_weight, self.dense_retriever))
        if self.lexical_retriever is not None and self.lexical_weight > 0:
            legs.append(("lexical", self.lexical_weight, self.lexical_retriever))

        if not legs:
            return []

        raw_results = await asyncio.gather(
            *(leg.retrieve(query, top_k=candidate_k, language=language) for _, _, leg in legs),
            return_exceptions=True,
        )

        fused_scores: dict[str, float] = {}
        chunks_by_id: dict[str, ScoredChunk] = {}
        best_contrib: dict[str, float] = {}
        errors: list[Exception] = []

        for (leg_name, weight, _), result in zip(legs, raw_results):
            if isinstance(result, Exception):
                logger.warning("Hybrid leg '%s' failed: %s", leg_name, result)
                errors.append(result)
                continue

            for rank, chunk in enumerate(result, start=1):
                contrib = weight / (self.rrf_k + rank)
                cid = chunk.chunk_id
                fused_scores[cid] = fused_scores.get(cid, 0.0) + contrib
                if cid not in chunks_by_id or contrib > best_contrib.get(cid, -1.0):
                    chunks_by_id[cid] = chunk
                    best_contrib[cid] = contrib

        if len(errors) == len(legs):
            raise RetrievalError(
                f"All hybrid retrieval legs failed: {'; '.join(str(e) for e in errors)}"
            )

        ranked_ids = sorted(
            fused_scores.keys(),
            key=lambda cid: fused_scores[cid],
            reverse=True,
        )[:top_k]

        return [
            ScoredChunk(
                chunk_id=cid,
                text=chunks_by_id[cid].text,
                retrieval_score=round(fused_scores[cid], 6),
                reranker_score=chunks_by_id[cid].reranker_score,
                retrieval_method=self.strategy_name,
                metadata=chunks_by_id[cid].metadata,
            )
            for cid in ranked_ids
        ]

    async def health_check(self) -> bool:
        checks = []
        if self.dense_retriever is not None:
            checks.append(self.dense_retriever.health_check())
        if self.lexical_retriever is not None:
            checks.append(self.lexical_retriever.health_check())
        if not checks:
            return False
        results = await asyncio.gather(*checks, return_exceptions=True)
        return any(res is True for res in results)
