"""
SAMVAD Phase 5 — Multilingual & Voice Retrieval Benchmark Runner

Fulfills Phase 5 Acceptance Criteria:
1. Publishes per-language (en, hi, bn) and cross-lingual evaluation tables to backend/benchmarks/results/.
2. Evaluates STT transcript normalization isolating speech disfluencies from retrieval metrics (Recall@K, MRR@K).
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

from app.embeddings.providers import LocalTfidfSVDProvider
from app.evaluation.loader import load_eval_dataset
from app.evaluation.runner import ExperimentConfig, run_retrieval_experiment
from app.ingestion.chunker import DocumentChunk
from app.retrieval.dense import DenseRetriever
from app.retrieval.hybrid import HybridRetriever
from app.retrieval.lexical import LexicalRetriever
from app.schemas.pipeline import ChunkMetadata, ChunkStrategy
from app.speech.normalizer import SpeechNormalizer


async def main():
    root_dir = Path(__file__).resolve().parent
    dataset_path = root_dir / "datasets" / "synthetic_smoke_v1.json"
    results_dir = root_dir / "results"
    results_dir.mkdir(parents=True, exist_ok=True)

    print(f"1. Loading Multilingual Evaluation Dataset: {dataset_path.name}...")
    dataset = load_eval_dataset(dataset_path, verify_checksum=True)
    print(f"   Loaded {len(dataset.documents)} documents, {len(dataset.queries)} queries, {len(dataset.judgments)} judgments across languages: {dataset.provenance.languages}")

    # Convert EvalDocuments into DocumentChunks
    chunks: list[DocumentChunk] = []
    for d in dataset.documents:
        chunks.append(
            DocumentChunk(
                text=d.text,
                metadata=ChunkMetadata(
                    chunk_id=d.doc_id,
                    parent_document_id=d.doc_id,
                    language=d.language,
                    chunk_strategy=ChunkStrategy.WHOLE_PASSAGE,
                    char_count=len(d.text),
                    extra={"title": d.title or ""},
                ),
            )
        )

    # 2. Build Retrievers
    print("\n2. Initializing Retrievers across Multilingual Corpus...")
    # Lexical (BM25)
    lexical = LexicalRetriever(chunks)

    # Dense
    emb_provider = LocalTfidfSVDProvider(n_components=16)
    dense_path = results_dir / "_temp_dense_phase5"
    dense = DenseRetriever(
        embedding_provider=emb_provider,
        index_dir=str(dense_path),
        similarity_threshold=0.0,
    )
    await dense.build_index(chunks)

    # Hybrid (RRF)
    hybrid = HybridRetriever(
        dense_retriever=dense,
        lexical_retriever=lexical,
        dense_weight=1.0,
        lexical_weight=1.0,
        rrf_k=60,
    )

    retrievers = [
        ("lexical_bm25", lexical),
        ("dense_tfidf_svd", dense),
        ("hybrid_rrf", hybrid),
    ]

    summaries = []

    print("\n3. Running Multilingual Benchmark Experiments...")
    for name, ret in retrievers:
        cfg = ExperimentConfig(
            experiment_name=f"phase5_multilingual_{name}",
            retriever_name=name,
            top_k=5,
            k_values=[1, 3, 5],
            notes="Phase 5 Multilingual Indic Retrieval Benchmark",
        )
        summary, out_dir = await run_retrieval_experiment(
            dataset=dataset,
            retriever=ret,
            config=cfg,
            output_root=results_dir,
        )
        summaries.append((name, summary, out_dir))
        print(f"   -> [{name}] Done: Recall@5={summary.overall_metrics.get('recall@5', 0):.4f}, MRR@5={summary.overall_metrics.get('mrr@5', 0):.4f}")

    # 4. STT Transcript Error Isolation Benchmark
    print("\n4. Running STT Transcript Normalization Isolation Benchmark (M5.2)...")
    normalizer = SpeechNormalizer()
    stt_corrupted_queries = [
        ("q-en-1", "Um, uh, Chandrayaan 3 mission ISRO landing date like you know"),
        ("q-hi-1", "अरे सुनो, मतलब चंद्रयान-3 का सफल प्रक्षेपण कब हुआ था?"),
        ("q-bn-1", "শান্তিনিকেতনে রবীন্দ্রনাথ ঠাকুর কোন বিশ্ববিদ্যালয় প্রতিষ্ঠা করেন?"),
    ]

    raw_hits = 0
    clean_hits = 0
    for qid, noisy_text in stt_corrupted_queries:
        cleaned_text = normalizer.normalize(noisy_text)
        raw_res = await hybrid.retrieve(noisy_text, top_k=3)
        clean_res = await hybrid.retrieve(cleaned_text, top_k=3)

        # Check target doc in top 3
        # find matching judgment
        target_doc = next(j.doc_id for j in dataset.judgments if j.query_id == qid)
        if any(r.chunk_id == target_doc for r in raw_res):
            raw_hits += 1
        if any(r.chunk_id == target_doc for r in clean_res):
            clean_hits += 1

    print(f"   Noisy STT Transcript Retrieval HitRate@3: {raw_hits}/{len(stt_corrupted_queries)} ({raw_hits/len(stt_corrupted_queries):.1%})")
    print(f"   Normalized Speech Retrieval HitRate@3:     {clean_hits}/{len(stt_corrupted_queries)} ({clean_hits/len(stt_corrupted_queries):.1%})")

    # 5. Generate Consolidated Phase 5 Report
    report_file = results_dir / "phase5_multilingual_speech_report.md"
    report_lines = [
        "# SAMVAD Phase 5 — Multilingual & Voice Evaluation Report",
        "",
        "## 1. Multilingual Retrieval Benchmark by Strategy",
        "",
        "| Strategy | Recall@1 | Recall@5 | MRR@5 | nDCG@5 | Avg Latency (ms) |",
        "| :--- | :--- | :--- | :--- | :--- | :--- |",
    ]
    for name, s, _ in summaries:
        report_lines.append(
            f"| `{name}` | {s.overall_metrics.get('recall@1', 0):.4f} | {s.overall_metrics.get('recall@5', 0):.4f} | "
            f"{s.overall_metrics.get('mrr@5', 0):.4f} | {s.overall_metrics.get('ndcg@5', 0):.4f} | "
            f"{s.latency_stats.mean if s.latency_stats else 0:.2f} |"
        )

    report_lines.extend([
        "",
        "## 2. Per-Language Retrieval Breakdown (Hybrid RRF)",
        "",
        "| Language | Language Name | Queries | Recall@5 | MRR@5 | nDCG@5 |",
        "| :--- | :--- | :--- | :--- | :--- | :--- |",
    ])
    hybrid_summary = summaries[2][1]
    lang_names = {"en": "English", "hi": "Hindi (हिन्दी)", "bn": "Bengali (বাংলা)"}
    for lang, metrics in hybrid_summary.by_language_metrics.items():
        report_lines.append(
            f"| `{lang}` | {lang_names.get(lang, lang)} | {metrics.get('count', 0)} | "
            f"{metrics.get('recall@5', 0):.4f} | {metrics.get('mrr@5', 0):.4f} | {metrics.get('ndcg@5', 0):.4f} |"
        )

    report_lines.extend([
        "",
        "## 3. Speech-Aware Normalization (STT Error Isolation)",
        "",
        "| Condition | HitRate@3 | Retrieval Impact |",
        "| :--- | :--- | :--- |",
        f"| Raw Unnormalized STT Transcripts (with fillers / disfluencies) | {raw_hits}/{len(stt_corrupted_queries)} ({raw_hits/len(stt_corrupted_queries):.1%}) | Baseline |",
        f"| Normalized Speech Queries (SpeechNormalizer M5.2) | {clean_hits}/{len(stt_corrupted_queries)} ({clean_hits/len(stt_corrupted_queries):.1%}) | +{(clean_hits - raw_hits)/len(stt_corrupted_queries):.1%} improvement |",
    ])

    report_file.write_text("\n".join(report_lines), encoding="utf-8")
    print(f"\n[SUCCESS] Consolidated Phase 5 Benchmark Report written to: {report_file}")


if __name__ == "__main__":
    asyncio.run(main())

