"""
SAMVAD NLP — Corpus-Aware Spell Correction & Contraction Expansion

Handles real-world user typos, missing/swapped/extra characters, and informal
contractions (e.g., "whats chandryaan 3" -> "what is chandrayaan 3") in <2ms
using Damerau-Levenshtein distance against the indexed corpus vocabulary.
"""

from __future__ import annotations

import re
import unicodedata
from typing import Iterable, Optional


# Informal / missing-apostrophe English contractions
CONTRACTIONS: dict[str, str] = {
    "whats": "what is",
    "what's": "what is",
    "whos": "who is",
    "who's": "who is",
    "hows": "how is",
    "how's": "how is",
    "wheres": "where is",
    "where's": "where is",
    "whys": "why is",
    "why's": "why is",
    "whens": "when is",
    "when's": "when is",
    "dont": "do not",
    "don't": "do not",
    "doesnt": "does not",
    "doesn't": "does not",
    "didnt": "did not",
    "didn't": "did not",
    "cant": "cannot",
    "can't": "cannot",
    "wont": "will not",
    "won't": "will not",
    "isnt": "is not",
    "isn't": "is not",
    "arent": "are not",
    "aren't": "are not",
    "wasnt": "was not",
    "wasn't": "was not",
    "werent": "were not",
    "weren't": "were not",
    "im": "i am",
    "i'm": "i am",
    "ive": "i have",
    "i've": "i have",
    "youre": "you are",
    "you're": "you are",
    "theyre": "they are",
    "they're": "they are",
    "theres": "there is",
    "there's": "there is",
    "heres": "here is",
    "here's": "here is",
    "thats": "that is",
    "that's": "that is",
    "its": "it is",
}

# Common conversational / platform terms that should never be miscorrected
COMMON_DOMAIN_TERMS: set[str] = {
    "samvad", "samvaad", "hello", "namaste", "namaskar", "greetings",
    "what", "where", "when", "which", "explain", "describe", "summarize",
    "summary", "overview", "compare", "difference", "details", "detail",
    "about", "capabilities", "architecture", "retrieve", "retrieval",
    "citation", "citations", "ground", "grounded", "grounding", "answer",
    "answers", "document", "documents", "knowledge", "evidence", "research",
    "analysis", "question", "questions", "exactly", "strict", "enforce",
    "enforces", "context", "history", "earlier", "previous", "session",
}


def damerau_levenshtein(a: str, b: str) -> int:
    """
    Compute optimal string alignment (restricted Damerau-Levenshtein) distance.
    Counts insertions, deletions, substitutions, and adjacent transpositions as 1 edit.
    """
    la, lb = len(a), len(b)
    if a == b:
        return 0
    if la == 0:
        return lb
    if lb == 0:
        return la

    # Quick lower bound on edit distance
    if abs(la - lb) > 3:
        return abs(la - lb)

    d = [[0] * (lb + 1) for _ in range(la + 1)]
    for i in range(la + 1):
        d[i][0] = i
    for j in range(lb + 1):
        d[0][j] = j

    for i in range(1, la + 1):
        ai = a[i - 1]
        for j in range(1, lb + 1):
            bj = b[j - 1]
            cost = 0 if ai == bj else 1
            best = min(
                d[i - 1][j] + 1,       # deletion
                d[i][j - 1] + 1,       # insertion
                d[i - 1][j - 1] + cost # substitution
            )
            if i > 1 and j > 1 and ai == b[j - 2] and a[i - 2] == bj:
                transposition = d[i - 2][j - 2] + 1
                if transposition < best:
                    best = transposition
            d[i][j] = best
    return d[la][lb]


def expand_contractions(text: str) -> str:
    """Expand informal or apostrophe-less contractions while preserving punctuation."""
    if not text:
        return text

    def _replace(match: re.Match[str]) -> str:
        word = match.group(0)
        expanded = CONTRACTIONS.get(word.lower())
        return expanded if expanded is not None else word

    return re.sub(r"\b[A-Za-z']+\b", _replace, text)


def find_best_vocab_match(
    token: str,
    vocab: Iterable[str],
    *,
    min_similarity: float = 0.80,
    idf_weights: Optional[dict[str, float]] = None,
) -> tuple[str, float]:
    """
    Find the closest vocabulary term for a possibly misspelled token.
    Returns (best_term, similarity_score). Returns (token, 1.0) if exact match or too short.
    """
    norm_tok = unicodedata.normalize("NFC", token).lower()
    if len(norm_tok) < 4 or norm_tok.isdigit():
        return token, 1.0

    vocab_set = vocab if isinstance(vocab, (set, dict)) else set(vocab)
    if norm_tok in vocab_set or norm_tok in COMMON_DOMAIN_TERMS:
        return token, 1.0

    max_dist = 1 if len(norm_tok) <= 6 else 2
    best_candidate: Optional[str] = None
    best_key: tuple[int, int, float, float] = (999, 1, 0.0, 999.0)

    all_candidates = set(vocab_set) | COMMON_DOMAIN_TERMS
    t_len = len(norm_tok)
    first_char = norm_tok[0]

    for cand in all_candidates:
        if len(cand) < 4 or abs(len(cand) - t_len) > max_dist:
            continue
        dist = damerau_levenshtein(norm_tok, cand)
        if dist == 0 or dist > max_dist:
            continue
        sim = 1.0 - (dist / max(t_len, len(cand)))
        if sim < min_similarity:
            continue

        # Ranking key: lowest edit distance, same first letter (0 vs 1), highest similarity
        same_first = 0 if cand[0] == first_char else 1
        idf_val = idf_weights.get(cand, 5.0) if idf_weights else 5.0
        key = (dist, same_first, -sim, idf_val)
        if key < best_key:
            best_key = key
            best_candidate = cand

    if best_candidate is not None:
        return best_candidate, round(-best_key[2], 3)
    return token, 1.0


def correct_query_against_vocab(
    text: str,
    vocab: Iterable[str],
    *,
    idf_weights: Optional[dict[str, float]] = None,
) -> tuple[str, dict[str, str]]:
    """
    Correct misspelled tokens in *text* against *vocab* + common domain terms.
    Returns (corrected_text, corrections_applied).
    """
    expanded = expand_contractions(text)
    vocab_set = vocab if isinstance(vocab, (set, dict)) else set(vocab)

    corrections: dict[str, str] = {}
    out_tokens: list[str] = []

    for tok in expanded.split():
        # Strip surrounding punctuation while preserving it
        m = re.match(r"^([^\w]*)([\w-]+)([^\w]*)$", tok, re.UNICODE)
        if not m:
            out_tokens.append(tok)
            continue
        prefix, core, suffix = m.groups()
        if "-" in core:
            # Handle hyphenated tokens like "chandryaan-3"
            parts = core.split("-")
            fixed_parts: list[str] = []
            for part in parts:
                fixed, _ = find_best_vocab_match(part, vocab_set, idf_weights=idf_weights)
                if fixed.lower() != part.lower():
                    corrections[part] = fixed
                fixed_parts.append(fixed)
            out_tokens.append(f"{prefix}{'-'.join(fixed_parts)}{suffix}")
        else:
            fixed, _ = find_best_vocab_match(core, vocab_set, idf_weights=idf_weights)
            if fixed.lower() != core.lower():
                corrections[core] = fixed
            out_tokens.append(f"{prefix}{fixed}{suffix}")

    return " ".join(out_tokens), corrections

