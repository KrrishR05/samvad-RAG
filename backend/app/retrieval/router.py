"""
SAMVAD Retrieval — Adaptive Query Router (Phase 6 — M6.1)

Dynamically routes incoming analyzed queries to the optimal retrieval strategy
('lexical', 'dense', or 'hybrid') based on linguistic features, token count,
named entity/identifier patterns, and query intent.
"""

from __future__ import annotations

import re
from typing import Optional, Set

from app.pipeline.interfaces import AnalyzedQuery


_EXACT_IDENTIFIER_PATTERN = re.compile(
    r"\b([A-Z]{2,}\b|\d+[-_]\w+|\b\d{4}\b|[a-zA-Z0-9_\.\-]+@[a-zA-Z0-9_\.\-]+)",
    re.UNICODE,
)
_QUESTION_PARTICLES: Set[str] = {
    # English
    "what", "why", "how", "when", "where", "who", "which", "explain", "describe",
    # Hindi (Devanagari & Latin)
    "क्या", "क्यों", "कैसे", "कब", "कहाँ", "कौन", "किसे", "kya", "kyun", "kaise", "kab", "kahan", "kaun",
    # Bengali
    "কী", "কেন", "কীভাবে", "কখন", "কোথায়", "কে", "কোনটি",
}


class AdaptiveRouter:
    """
    Selects the optimal retrieval strategy for an analyzed query.

    Strategies:
      - 'lexical': Optimal for keyword searches, exact codes, acronyms, and identifier lookups.
      - 'dense': Optimal for short conceptual or semantic questions without rare exact tokens.
      - 'hybrid': Optimal for complex, multi-faceted, deep, or cross-lingual queries.
    """

    def __init__(
        self,
        *,
        default_strategy: str = "hybrid",
        enable_exact_code_routing: bool = True,
    ) -> None:
        self.default_strategy = default_strategy
        self.enable_exact_code_routing = enable_exact_code_routing

    async def route(self, query: AnalyzedQuery) -> str:
        """Determine retrieval strategy based on linguistic and structural query traits."""
        text = (query.processed_text or query.original_text or "").strip()
        if not text:
            return self.default_strategy

        tokens = text.split()
        num_tokens = len(tokens)
        metadata = query.metadata or {}

        # 1. Deep research or System queries -> Hybrid (maximum recall)
        if metadata.get("intensity") == "deep" or metadata.get("about_samvad"):
            return "hybrid"

        # 2. Exact identifiers, codes, or isolated acronyms -> Lexical (BM25 exact match)
        if self.enable_exact_code_routing:
            has_identifier = bool(_EXACT_IDENTIFIER_PATTERN.search(text))
            # Quoted string lookups like "Chandra-3"
            has_quotes = ('"' in text) or ("'" in text)
            if (has_identifier or has_quotes) and num_tokens <= 6:
                return "lexical"

        # 3. Very short keyword lookups (1-2 words without question particles) -> Lexical
        lower_tokens = [t.lower().strip("?,.!") for t in tokens]
        has_question_word = any(t in _QUESTION_PARTICLES for t in lower_tokens)

        if num_tokens <= 2 and not has_question_word:
            return "lexical"

        # 4. Short conceptual / semantic questions (3-6 tokens with question particles) -> Dense
        if 2 <= num_tokens <= 6 and has_question_word and not bool(_EXACT_IDENTIFIER_PATTERN.search(text)):
            return "dense"

        # 5. Long, multi-clause, or complex queries -> Hybrid
        return "hybrid"

