"""
Tests — Phase 5: Speech-Aware Normalizer (M5.2)
"""

import pytest
from app.speech.normalizer import SpeechNormalizer


def test_speech_normalizer_cleans_english_fillers():
    normalizer = SpeechNormalizer()
    raw = "Um, uh, tell me like what is Nokvirae actually?"
    cleaned = normalizer.normalize(raw, language="en")
    assert "um" not in cleaned.lower()
    assert "uh" not in cleaned.lower()
    assert "like" not in cleaned.lower()
    assert "actually" not in cleaned.lower()
    assert "Nokvirae" in cleaned


def test_speech_normalizer_cleans_indic_fillers():
    normalizer = SpeechNormalizer()
    raw = "सुनो, मतलब Nokvirae का आर्किटेक्चर क्या है?"
    cleaned = normalizer.normalize(raw, language="hi")
    assert "सुनो" not in cleaned
    assert "मतलब" not in cleaned
    assert "Nokvirae" in cleaned
    assert "आर्किटेक्चर" in cleaned


def test_speech_normalizer_deduplicates_stutters():
    normalizer = SpeechNormalizer()
    raw = "what what is the the main database?"
    cleaned = normalizer.normalize(raw, language="en")
    assert "what what" not in cleaned
    assert "the the" not in cleaned
    assert cleaned.startswith("what is the main database")


def test_speech_normalizer_hinglish_stem_expansion():
    normalizer = SpeechNormalizer()
    raw = "Nokvirae ke architecture ke baare me batao"
    cleaned = normalizer.normalize(raw, language="hi")
    # Expands Hinglish stem with Devanagari keyword to boost hybrid search
    assert "के बारे में" in cleaned

