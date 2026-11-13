"""
Tests — Indic Query Analyzer & Language Identification (Phase 3 — M3.2)
"""

import asyncio
import pytest

from app.retrieval.query_analyzer import (
    IndicQueryAnalyzer,
    detect_language,
    extract_intent,
    extract_keywords_for_retrieval,
    normalize_query_text,
)


def test_detect_language_indic_scripts():
    # Hindi (Devanagari)
    lang, conf = detect_language("भारत की राजधानी नई दिल्ली है।")
    assert lang == "hi"
    assert conf > 0.7

    # Marathi (Devanagari with Marathi markers)
    lang, conf = detect_language("महाराष्ट्र राज्याची राजधानी मुंबई आहे आणि ते मोठे शहर आहे.")
    assert lang == "mr"
    assert conf > 0.7

    # Bengali
    lang, conf = detect_language("পশ্চিমবঙ্গের রাজধানী কলকাতা।")
    assert lang == "bn"
    assert conf > 0.7

    # Tamil
    lang, conf = detect_language("தமிழ்நாட்டின் தலைநகரம் சென்னை.")
    assert lang == "ta"
    assert conf > 0.7

    # Telugu
    lang, conf = detect_language("ఆంధ్రప్రదేశ్ రాజధాని అమరావతి.")
    assert lang == "te"
    assert conf > 0.7

    # English
    lang, conf = detect_language("What is the capital of India?")
    assert lang == "en"
    assert conf > 0.7


def test_detect_language_empty_and_whitespace():
    lang, conf = detect_language("")
    assert lang == "en"
    assert conf == 0.0


def test_normalize_query_text():
    raw = "  What   is  \t  Bengaluru? \n "
    normalized = normalize_query_text(raw)
    assert normalized == "What is Bengaluru?"


def test_extract_intent():
    assert extract_intent("What is the population of Mumbai?") == "factoid"
    assert extract_intent("How to optimize vector search latency?") == "method_or_quantity"
    assert extract_intent("Why does BM25 fail on semantic queries?") == "explanatory"
    assert extract_intent("Compare dense retrieval vs sparse BM25") == "comparative"
    assert extract_intent("Summarize the key findings from the document") == "summary"
    assert extract_intent("भारत की राजधानी क्या है?") == "factoid"


def test_extract_keywords_for_retrieval():
    query = "Please tell me what is the climate of Bengaluru"
    keywords = extract_keywords_for_retrieval(query, language="en")
    assert "please" not in keywords.lower()
    assert "tell" not in keywords.lower()
    assert "climate" in keywords.lower()
    assert "bengaluru" in keywords.lower()


def test_indic_query_analyzer_integration():
    import asyncio
    analyzer = IndicQueryAnalyzer()
    res = asyncio.run(analyzer.analyze("भारत का राष्ट्रीय पशु क्या है?"))
    assert res.language == "hi"
    assert res.intent == "factoid"
    assert "राष्ट्रीय" in res.processed_text
    assert "detected_language" in res.metadata
    assert res.metadata["detected_language"] == "hi"


def test_detect_intensity_and_samvad_query():
    analyzer = IndicQueryAnalyzer()
    
    # Deep intensity checks
    res_deep_en = asyncio.run(analyzer.analyze("Explain in detail all security policies in the architecture"))
    assert res_deep_en.metadata["intensity"] == "deep"

    res_deep_hi = asyncio.run(analyzer.analyze("इस दस्तावेज़ के बारे में विस्तार से पूरी जानकारी दें"))
    assert res_deep_hi.metadata["intensity"] == "deep"

    # Standard intensity
    res_std = asyncio.run(analyzer.analyze("Who is the CEO?"))
    assert res_std.metadata["intensity"] == "standard"

    # Samvad self-identity checks
    res_samvad_en = asyncio.run(analyzer.analyze("What is SAMVAD and what can you do?"))
    assert res_samvad_en.metadata["about_samvad"] is True

    res_samvad_hi = asyncio.run(analyzer.analyze("संवाद क्या है?"))
    assert res_samvad_hi.metadata["about_samvad"] is True

    res_other = asyncio.run(analyzer.analyze("What is the capital of India?"))
    assert res_other.metadata["about_samvad"] is False
