"""
SAMVAD Query Analyzer & Language Identification (Phase 3 — M3.2)

Provides deterministic multilingual script detection, Indic language identification,
Unicode normalization, and retrieval-optimized query transformation.
"""

from __future__ import annotations

import re
import unicodedata
from typing import Any, Optional

from app.pipeline.interfaces import AnalyzedQuery


# Unicode script ranges for Indic and major scripts
SCRIPT_RANGES = [
    ("hi", (0x0900, 0x097F)),  # Devanagari (Hindi / Marathi / Sanskrit)
    ("bn", (0x0980, 0x09FF)),  # Bengali / Assamese
    ("ta", (0x0B80, 0x0BFF)),  # Tamil
    ("te", (0x0C00, 0x0C7F)),  # Telugu
    ("kn", (0x0C80, 0x0CFF)),  # Kannada
    ("ml", (0x0D00, 0x0D7F)),  # Malayalam
    ("gu", (0x0A80, 0x0AFF)),  # Gujarati
    ("pa", (0x0A00, 0x0A7F)),  # Gurmukhi (Punjabi)
    ("or", (0x0B00, 0x0B7F)),  # Odia
    ("en", (0x0041, 0x007A)),  # Latin (English / transliterated)
]

# Characteristic Marathi tokens in Devanagari script to disambiguate from Hindi
MARATHI_MARKERS = {
    "आहे", "नाही", "आहेत", "नाहीत", "होते", "होती", "झाला", "झाली", "झाले",
    "कसा", "कशी", "काय", "कुठे", "केव्हा", "म्हणून", "आणि", "पण", "किंवा",
    "त्यांचे", "त्यांना", "याच्या", "त्याच्या"
}

# Question intent markers across languages
INTENT_PATTERNS = [
    (r"\b(what|which|who|whom|whose)\b", "factoid"),
    (r"\b(how|how much|how many)\b", "method_or_quantity"),
    (r"\b(why|explain|reason)\b", "explanatory"),
    (r"\b(compare|difference|versus|vs)\b", "comparative"),
    (r"\b(summarize|summary|overview|brief)\b", "summary"),
    # Hindi / Indic intent markers (safe against virama / conjunct word boundaries)
    (r"(?:^|[\s\W])(क्या|कौन|किस|किसे)(?:$|[\s\W])", "factoid"),
    (r"(?:^|[\s\W])(कैसे|कितना|कितने)(?:$|[\s\W])", "method_or_quantity"),
    (r"(?:^|[\s\W])(क्यों|कारण|स्पष्ट)(?:$|[\s\W])", "explanatory"),
    (r"(?:^|[\s\W])(अंतर|तुलना)(?:$|[\s\W])", "comparative"),
    (r"(?:^|[\s\W])(सारांश|संक्षेप)(?:$|[\s\W])", "summary"),
]

INTENSITY_PATTERNS = [
    r"\b(in detail|detailed|comprehensive|all details|all the details|elaborate|deep dive|thoroughly|explain everything|break down|step by step|full list|everything about|complete analysis)\b",
    r"(?:^|[\s\W])(विस्तार से|विस्तृत|पूरी जानकारी|सभी विवरण|व्याख्या|गहराई से|सब कुछ|समझाएं|विस्तारपूर्वक|पूरा)(?:$|[\s\W])",
]

SAMVAD_PATTERNS = [
    r"\b(samvad|samvaad)\b",
    r"(?:^|[\s\W])(संवाद)(?:$|[\s\W])",
    r"\b(who are you|what are you|what is this platform|about yourself|what can you do)\b",
    r"(?:^|[\s\W])(तुम कौन हो|आप कौन हैं|यह क्या है|अपने बारे में)(?:$|[\s\W])",
]


def detect_intensity(text: str) -> str:
    """Detect whether user query asks for deep, comprehensive coverage or concise answer."""
    lowered = text.lower()
    for pattern in INTENSITY_PATTERNS:
        if re.search(pattern, lowered):
            return "deep"
    return "standard"


def is_samvad_query(text: str) -> bool:
    """Detect if the query asks about the SAMVAD platform itself or its capabilities."""
    lowered = text.lower()
    for pattern in SAMVAD_PATTERNS:
        if re.search(pattern, lowered):
            return True
    return False


def detect_language(text: str) -> tuple[str, float]:
    """
    Detect the primary language of the text using Unicode script distributions
    and Indic vocabulary heuristics.

    Returns:
        tuple[language_code, confidence_ratio]
    """
    if not text.strip():
        return "en", 0.0

    script_counts: dict[str, int] = {lang: 0 for lang, _ in SCRIPT_RANGES}
    total_letters = 0

    for char in text:
        cp = ord(char)
        for lang, (start, end) in SCRIPT_RANGES:
            if start <= cp <= end:
                script_counts[lang] += 1
                total_letters += 1
                break

    if total_letters == 0:
        return "en", 0.0

    # Find dominant script
    dominant_lang, dominant_count = max(script_counts.items(), key=lambda item: item[1])
    confidence = round(dominant_count / total_letters, 3)

    # Disambiguate Devanagari between Hindi and Marathi
    if dominant_lang == "hi":
        words = set(re.findall(r"[\u0900-\u097F]+", text))
        if words & MARATHI_MARKERS:
            return "mr", confidence

    return dominant_lang, confidence


def extract_intent(text: str) -> str:
    """Classify the user's research query intent."""
    normalized = text.lower()
    for pattern, intent in INTENT_PATTERNS:
        if re.search(pattern, normalized):
            return intent
    return "general_search"


def normalize_query_text(text: str) -> str:
    """
    NFC Unicode normalization, whitespace collapsing, and punctuation hygiene.
    Preserves Indic diacritics and matras.
    """
    # Canonical Unicode NFC normalization
    normalized = unicodedata.normalize("NFC", text)
    # Collapse irregular whitespace and tabs
    normalized = re.sub(r"[\s\t\r\n]+", " ", normalized).strip()
    return normalized


def extract_keywords_for_retrieval(text: str, language: str = "en") -> str:
    """
    Produce an expanded/cleaned representation of the query for lexical search.
    Removes conversational filler phrases while retaining content-bearing keywords.
    """
    fillers_en = {
        "please", "tell", "me", "about", "can", "you", "give", "provide",
        "i", "want", "to", "know", "what", "is", "are", "the", "a", "an",
        "in", "on", "at", "for", "with", "of", "and"
    }
    fillers_hi = {
        "कृपया", "मुझे", "बताएं", "बताओ", "क्या", "है", "हैं", "का", "के", "की",
        "में", "पर", "के", "लिए", "और", "से"
    }

    fillers = fillers_hi if language == "hi" else fillers_en
    tokens = text.split()
    retained = [t for t in tokens if t.lower() not in fillers]

    if not retained:
        return text

    return " ".join(retained)


class IndicQueryAnalyzer:
    """
    Deterministic Indic & English Query Analyzer.

    Conforms to the QueryAnalyzer protocol in app.pipeline.interfaces.
    """

    async def analyze(self, query: str) -> AnalyzedQuery:
        """
        Analyze, detect language, classify intent, and produce a normalized
        representation for retrieval.
        """
        cleaned = normalize_query_text(query)
        lang, confidence = detect_language(cleaned)
        intent = extract_intent(cleaned)
        intensity = detect_intensity(cleaned)
        about_samvad = is_samvad_query(cleaned)
        retrieval_text = extract_keywords_for_retrieval(cleaned, language=lang)

        metadata: dict[str, Any] = {
            "detected_language": lang,
            "language_confidence": confidence,
            "intent": intent,
            "intensity": intensity,
            "about_samvad": about_samvad,
            "normalized_length": len(cleaned),
        }

        return AnalyzedQuery(
            original_text=query,
            processed_text=retrieval_text,
            language=lang,
            intent=intent,
            metadata=metadata,
        )
