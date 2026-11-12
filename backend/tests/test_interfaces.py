"""
Tests — Canonical Interfaces & Orchestrator Registry
"""

from app.generation.generator import LLMGenerator
from app.guardrails.interfaces import InputGuard
from app.pipeline.interfaces import (
    AnswerGenerator,
    GuardrailService,
    QueryRouter,
    Reranker,
    Retriever,
    ScoredChunk,
    SpeechService,
)
from app.pipeline.orchestrator import PipelineOrchestrator
from app.retrieval.dense import DenseRetriever
from app.retrieval.hybrid import HybridRetriever
from app.retrieval.lexical import LexicalRetriever
from app.retrieval.reranker import CrossEncoderReranker
from app.retrieval.router import AdaptiveRouter
from app.speech.provider import ElevenLabsSpeechProvider, SarvamSpeechProvider


def test_protocol_conformance():
    assert isinstance(DenseRetriever(), Retriever)
    assert isinstance(LexicalRetriever(), Retriever)
    assert isinstance(HybridRetriever(), Retriever)
    assert isinstance(CrossEncoderReranker(), Reranker)
    assert isinstance(AdaptiveRouter(), QueryRouter)
    assert isinstance(LLMGenerator(), AnswerGenerator)
    assert isinstance(InputGuard(), GuardrailService)
    assert isinstance(SarvamSpeechProvider(api_key="test"), SpeechService)
    assert isinstance(ElevenLabsSpeechProvider(api_key="test"), SpeechService)


def test_scored_chunk_keeps_scores_separate():
    chunk = ScoredChunk(
        chunk_id="c1",
        text="Bengaluru is the capital of Karnataka.",
        retrieval_score=0.82,
        reranker_score=0.95,
        retrieval_method="hybrid",
    )
    assert chunk.retrieval_score == 0.82
    assert chunk.reranker_score == 0.95
    assert chunk.retrieval_method == "hybrid"


def test_orchestrator_retriever_registry():
    dense = DenseRetriever()
    lexical = LexicalRetriever()
    orch = PipelineOrchestrator(retrievers={"dense": dense, "lexical": lexical})
    assert set(orch.retrievers.keys()) == {"dense", "lexical"}

    single = PipelineOrchestrator(retriever=dense)
    assert single.retrievers == {"dense": dense}

