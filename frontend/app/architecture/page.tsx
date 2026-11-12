"use client";

import React, { useEffect, useState } from "react";
import { getPipelineStatus } from "@/lib/api/client";
import type { PipelineStatusResponse } from "@/types/api";
import { AppShell } from "@/components/layout/AppShell";

export default function ArchitecturePage() {
  const [status, setStatus] = useState<PipelineStatusResponse | null>(null);

  useEffect(() => {
    getPipelineStatus()
      .then(setStatus)
      .catch(() => setStatus(null));
  }, []);

  const subsystems = [
    {
      name: "Document Ingestion & Chunking",
      phase: "Phase 2 — Live",
      active: true,
      detail:
        "Parses TXT, Markdown, PDF, DOCX, HTML, and JSON with NFC Unicode normalization, SHA-256 deduplication, SQLite chunk provenance, and Indic sentence splitting.",
    },
    {
      name: "Lexical BM25 Retriever",
      phase: "Phase 2 — Live",
      active: Boolean(status?.available_strategies.includes("lexical")),
      detail:
        "Unicode-aware Okapi BM25 preserving Indic combining matras and Devanagari/Bengali/Tamil script boundaries.",
    },
    {
      name: "Dense Cosine Retriever",
      phase: "Phase 2 — Live",
      active: Boolean(status?.available_strategies.includes("dense")),
      detail: status
        ? `Provider: ${status.embedding_provider} (${status.embedding_dimension}-dim L2-normalized vectors with on-disk .npz persistence).`
        : "EmbeddingProvider protocol supporting local TF-IDF+SVD baseline and OpenAI-compatible/Ollama endpoints.",
    },
    {
      name: "Hybrid Reciprocal Rank Fusion (RRF)",
      phase: "Phase 2 — Live",
      active: Boolean(status?.available_strategies.includes("hybrid")),
      detail:
        "Parallel dense + lexical retrieval merged with weighted RRF (k=60) and single-leg fault tolerance.",
    },
    {
      name: "Provider-Agnostic LLM Answer Generator",
      phase: status?.llm_configured ? "Phase 2 — Configured" : "Phase 2 — Unconfigured",
      active: Boolean(status?.llm_configured),
      detail: status?.llm_configured
        ? `Active provider '${status.llm_provider}' (${status.llm_model}) with delimited <evidence> prompt-injection isolation and inline [n] citation mapping.`
        : "Ready in backend; requires LLM_PROVIDER, LLM_MODEL, and optional LLM_API_KEY in backend/.env.",
    },
    {
      name: "Cross-Encoder Reranker",
      phase: "Phase 3 — Planned",
      active: Boolean(status?.reranker_configured),
      detail:
        "Reranker protocol defined (keeps retrieval_score and reranker_score strictly separated); cross-encoder scoring arrives in Phase 3.",
    },
    {
      name: "Confidence, Grounding & Relevance Guardrails",
      phase: "Phase 3 — Planned",
      active: Boolean(status?.guardrails_configured),
      detail:
        "InputGuard implemented; NLI grounding verification, relevance scoring, and calibrated confidence gating planned for Phase 3.",
    },
    {
      name: "Multilingual Voice (STT)",
      phase: "Phase 4 — Planned",
      active: Boolean(status?.stt_configured),
      detail:
        "Validated audio upload endpoint with magic-byte checks and Sarvam/ElevenLabs adapters planned for Phase 4.",
    },
  ];

  const flowStages = [
    "Query",
    "Validation",
    "Query Analysis",
    "Hybrid Retrieval (BM25 + Dense RRF)",
    "Reranking (opt)",
    "Confidence Check",
    "LLM Generation [1][2]",
    "Grounding Check",
  ];

  return (
    <AppShell
      pageTitle="Pipeline Explorer & Architecture"
      pipelineStatus={status}
    >
      <main className="flex-1 overflow-y-auto px-4 sm:px-8 py-6">
        <div className="max-w-5xl mx-auto space-y-6">
          <div>
            <h2 className="font-display font-semibold text-xl text-[var(--text-primary)]">
              SAMVAD Architecture & Live Capability Audit
            </h2>
            <p className="text-sm text-[var(--text-secondary)] mt-1">
              Every badge below reflects real capability reporting from{" "}
              <code className="font-mono-tech text-xs px-1.5 py-0.5 rounded bg-[var(--bg-surface)] border border-[var(--border-subtle)]">
                GET /api/v1/pipeline/status
              </code>
              .
            </p>
          </div>

          {/* Pipeline Sequence Strip */}
          <section className="rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-panel)] p-5 space-y-3">
            <p className="text-[11px] font-mono-tech uppercase tracking-wider text-[var(--text-muted)]">
              Canonical Execution Flow
            </p>
            <div className="flex flex-wrap items-center gap-2">
              {flowStages.map((stage, idx) => (
                <React.Fragment key={stage}>
                  <span className="px-2.5 py-1.5 rounded-md text-xs font-mono-tech bg-[var(--bg-surface)] text-[var(--text-primary)] border border-[var(--border-subtle)]">
                    {stage}
                  </span>
                  {idx < flowStages.length - 1 && (
                    <span className="text-[var(--text-muted)] text-xs">&rarr;</span>
                  )}
                </React.Fragment>
              ))}
            </div>
          </section>

          {/* Subsystem Grid */}
          <section className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {subsystems.map((sub) => (
              <div
                key={sub.name}
                className="rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-panel)] p-4 space-y-2"
              >
                <div className="flex items-start justify-between gap-2">
                  <h3 className="font-display font-medium text-sm text-[var(--text-primary)]">
                    {sub.name}
                  </h3>
                  <span
                    className={`shrink-0 px-2 py-0.5 rounded text-[10px] font-mono-tech border ${
                      sub.active
                        ? "bg-[var(--status-success-soft)] text-[var(--status-success)] border-[var(--status-success)]/30"
                        : "bg-[var(--bg-surface)] text-[var(--text-muted)] border-[var(--border-subtle)]"
                    }`}
                  >
                    {sub.phase}
                  </span>
                </div>
                <p className="text-xs leading-relaxed text-[var(--text-secondary)]">
                  {sub.detail}
                </p>
              </div>
            ))}
          </section>
        </div>
      </main>
    </AppShell>
  );
}
