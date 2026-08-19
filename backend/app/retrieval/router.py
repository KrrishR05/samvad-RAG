"""
SAMVAD Retrieval — Adaptive Query Router

Placeholder for adaptive routing logic that selects
the best retrieval strategy per query.

TODO: Implement routing heuristics or a trained classifier.
"""

from __future__ import annotations

from app.pipeline.interfaces import AnalyzedQuery


class AdaptiveRouter:
    """
    Selects the retrieval strategy for a given query.

    Possible strategies: "dense", "lexical", "hybrid".

    TODO: Implement adaptive routing.
      - Short factual queries → dense
      - Keyword-heavy queries → lexical
      - Ambiguous / complex queries → hybrid
    """

    async def route(self, query: AnalyzedQuery) -> str:
        """
        Determine retrieval strategy.

        TODO: Replace with actual routing logic.
        Default: hybrid (safest general-purpose strategy).
        """
        # TODO: Implement adaptive routing logic.
        return "hybrid"
