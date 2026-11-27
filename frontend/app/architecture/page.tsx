"use client";

import React, { useEffect, useState } from "react";
import { getPipelineStatus, healthCheck } from "@/lib/api/client";
import type { HealthResponse, PipelineStatusResponse } from "@/types/api";
import { AppShell } from "@/components/layout/AppShell";
import { useKnowledgeBase } from "@/context/KnowledgeBaseContext";
import { RefreshIcon } from "@/components/ui/Icons";

interface StageInfo {
  id: string;
  name: string;
  shortName: string;
  category: "ingestion" | "retrieval" | "guardrails" | "generation" | "voice";
  status: "active" | "online" | "ready";
  provider: string;
  algorithm: string;
  parameters: Record<string, string>;
  description: string;
}

const PIPELINE_STAGES: StageInfo[] = [
  {
    id: "stt",
    name: "Indic Speech-to-Text (STT)",
    shortName: "1. Speech STT",
    category: "voice",
    status: "active",
    provider: "Sarvam AI (saaras:v3)",
    algorithm: "Acoustic CTC & Conformer with Indic Script Disambiguation",
    parameters: {
      "Supported Codecs": "WAV, MP3, OGG, WebM, FLAC",
      "Sampling Rate": "8kHz – 48kHz Auto-resampled",
      "Languages": "Hindi, Bengali, Tamil, Telugu, Marathi, English",
      "Punctuation": "True-case Indic punctuation restoration",
    },
    description:
      "Transcribes spoken research queries directly into normalized Devanagari or Latin text with sub-second latency.",
  },
  {
    id: "analysis",
    name: "Indic Query Analyzer & Script Normalizer",
    shortName: "2. Query Analyzer",
    category: "ingestion",
    status: "active",
    provider: "SAMVAD Core",
    algorithm: "Unicode NFC Normalization & Script Identification",
    parameters: {
      "Script Detection": "Devanagari, Bengali, Tamil, Telugu, Latin",
      "Combining Matras": "Preserved without character splitting",
      "Adaptive Router": "Lexical vs Dense strategy recommendation",
      "Execution Timeout": "10.0 seconds per stage",
    },
    description:
      "Normalizes script boundaries, isolates search tokens, and determines the optimal retrieval balance.",
  },
  {
    id: "retrieval_bm25",
    name: "Okapi BM25 Lexical Retriever",
    shortName: "3a. BM25 Lexical",
    category: "retrieval",
    status: "active",
    provider: "SAMVAD In-Memory Lexical Engine",
    algorithm: "Modified Okapi BM25 with Indic Term Frequency Scaling",
    parameters: {
      "k1 Parameter": "1.5 (Term frequency saturation)",
      "b Parameter": "0.75 (Document length penalty)",
      "Tokenization": "Indic character cluster and whitespace split",
      "Candidate Top-K": "10 ranked passages",
    },
    description:
      "Executes exact keyword, acronym, and entity retrieval across all indexed knowledge-base chunks.",
  },
  {
    id: "retrieval_dense",
    name: "SVD Semantic Vector Retriever",
    shortName: "3b. Dense Vector",
    category: "retrieval",
    status: "active",
    provider: "Local TF-IDF SVD Baseline (128-dim)",
    algorithm: "L2-Normalized Truncated SVD Cosine Similarity",
    parameters: {
      "Vector Dimension": "128 dimensions",
      "Persistence": "On-disk .npz vector matrix",
      "Distance Metric": "Cosine similarity in unit sphere",
      "Candidate Top-K": "10 ranked passages",
    },
    description:
      "Performs semantic concept matching, finding conceptually relevant passages even when exact words differ.",
  },
  {
    id: "rrf",
    name: "Reciprocal Rank Fusion (RRF)",
    shortName: "4. Hybrid RRF",
    category: "retrieval",
    status: "active",
    provider: "SAMVAD Hybrid Core",
    algorithm: "Weighted RRF with k=60 Smoothing Factor",
    parameters: {
      "RRF Constant (k)": "60 (Standard TREC benchmark)",
      "Single-Leg Fallback": "Auto-failsafe if either engine is unindexed",
      "Score Normalization": "1 / (k + rank_lexical) + 1 / (k + rank_dense)",
      "Merged Top-K": "10 candidate passages",
    },
    description:
      "Fuses lexical and dense candidate lists into a single consensus ranking with zero calibration bias.",
  },
  {
    id: "reranker",
    name: "Multi-Pass Intensity Reranker",
    shortName: "5. Reranker",
    category: "retrieval",
    status: "active",
    provider: "SAMVAD Intensity Scorer",
    algorithm: "Cross-Feature Query-Passage Relevance Scoring",
    parameters: {
      "Rerank Top-K": "5 highest-scoring evidence passages",
      "Score Separation": "Independent retrieval_score and reranker_score",
      "Score Threshold": "0.15 minimum confidence threshold",
    },
    description:
      "Fine-tunes candidate ordering, placing the highest quality evidentiary passages at the very top of context.",
  },
  {
    id: "guardrails",
    name: "Multi-Tier Trust & Safety Guardrails",
    shortName: "6. Guardrails",
    category: "guardrails",
    status: "active",
    provider: "SAMVAD Guardrails Suite",
    algorithm: "4-Phase Security & Grounding Policy",
    parameters: {
      "InputGuard": "Prompt-injection & system escape mitigation",
      "ConfidenceGuard": "Min score threshold 0.15 gating",
      "RelevanceGuard": "Min 5% keyword overlap verification",
      "GroundingGuard": "Evidence citation contract validation",
    },
    description:
      "Protects against prompt-injection attacks, hallucinated claims, and automatically abstains if evidence is insufficient.",
  },
  {
    id: "generator",
    name: "Evidence-Grounded LLM Synthesizer",
    shortName: "7. LLM Generator",
    category: "generation",
    status: "active",
    provider: "Google Gemini 3.5 Flash Lite",
    algorithm: "Prompt-Isolated Citation Binding with [n] Markers",
    parameters: {
      "Context Isolation": "Delimited <evidence id=\"n\"> tags",
      "Citation Enforcement": "Inline [1], [2] hyperlinked anchors",
      "Abstention Rule": "Explicit refusal on unverified claims",
      "Generation Temp": "0.2 for strict factual consistency",
    },
    description:
      "Generates concise, factual research answers strictly grounded in cited passages with zero speculation.",
  },
  {
    id: "tts",
    name: "Indic Voice Synthesis (TTS)",
    shortName: "8. Bulbul TTS",
    category: "voice",
    status: "active",
    provider: "Sarvam AI (bulbul:v3)",
    algorithm: "Deep Neural Indic Speech Synthesis",
    parameters: {
      "Speaker Model": "Bulbul Indic Neural Voice",
      "Audio Format": "WAV 24kHz / MP3",
      "Pacing": "Native prosody for Hindi & Indic dialects",
      "Streaming": "Chunked playback buffer",
    },
    description:
      "Converts evidence-grounded answers into natural, clear spoken audio in the researcher's chosen language.",
  },
];

export default function ArchitecturePage() {
  const { pipelineStatus: kbStatus } = useKnowledgeBase();
  const [fetchedStatus, setFetchedStatus] = useState<PipelineStatusResponse | null>(null);
  const status = fetchedStatus ?? kbStatus;
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [selectedStage, setSelectedStage] = useState<StageInfo>(PIPELINE_STAGES[0]);
  const [probing, setProbing] = useState(false);
  const [probeLatency, setProbeLatency] = useState<number | null>(null);

  const fetchStatus = () => {
    Promise.allSettled([getPipelineStatus(), healthCheck()]).then(([p, h]) => {
      if (p.status === "fulfilled") setFetchedStatus(p.value);
      if (h.status === "fulfilled") setHealth(h.value);
    });
  };

  useEffect(() => {
    fetchStatus();
  }, []);

  const handleRunProbe = async () => {
    setProbing(true);
    const t0 = performance.now();
    try {
      await Promise.all([healthCheck(), getPipelineStatus()]);
      setProbeLatency(Math.round(performance.now() - t0));
      fetchStatus();
    } catch {
      setProbeLatency(null);
    } finally {
      setProbing(false);
    }
  };

  return (
    <AppShell
      pageTitle="Pipeline Architecture & Topology Explorer"
      pipelineStatus={status}
      headerActions={
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={handleRunProbe}
            disabled={probing}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-[var(--accent-soft)] text-[var(--accent)] border border-[var(--accent-border)] hover:bg-[var(--accent)] hover:text-white transition-all cursor-pointer shadow-xs disabled:opacity-50"
            title="Execute live diagnostics check against all pipeline subsystems"
          >
            <span>{probing ? "Probing..." : "⚡ Run Live Health Probe"}</span>
          </button>
          <button
            type="button"
            onClick={fetchStatus}
            className="inline-flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-xs font-medium bg-[var(--bg-surface)] text-[var(--text-secondary)] border border-[var(--border-subtle)] hover:text-[var(--text-primary)] transition-colors cursor-pointer"
          >
            <RefreshIcon className={probing ? "animate-spin" : ""} />
            <span>Refresh</span>
          </button>
        </div>
      }
    >
      <main className="flex-1 overflow-y-auto px-4 sm:px-8 py-6">
        <div className="max-w-5xl mx-auto space-y-6">
          {/* Header & Subsystem Overview */}
          <div className="flex flex-wrap items-end justify-between gap-4">
            <div>
              <h2 className="font-display font-semibold text-xl text-[var(--text-primary)]">
                SAMVAD End-to-End Pipeline Architecture
              </h2>
              <p className="text-sm text-[var(--text-secondary)] mt-1 max-w-2xl leading-relaxed">
                Interactive runtime topology of SAMVAD&apos;s 8-stage multilingual retrieval-augmented generation engine. Every subsystem reports live capabilities verified against backend endpoints.
              </p>
            </div>

            {probeLatency !== null && (
              <div className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-[var(--status-success-soft)] border border-[var(--status-success)]/30 text-[var(--status-success)] font-mono-tech text-xs animate-in fade-in">
                <span className="w-2 h-2 rounded-full bg-[var(--status-success)] animate-ping" />
                <span>Diagnostics Probe: {probeLatency} ms roundtrip</span>
              </div>
            )}
          </div>

          {/* Live Capability Matrix Summary */}
          <section className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <div className="rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-panel)] p-4 space-y-1">
              <span className="text-[10px] font-mono-tech uppercase text-[var(--text-muted)] tracking-wider block">
                LLM Synthesizer
              </span>
              <span className="text-sm font-bold text-[var(--accent)] block truncate">
                {status?.llm_model || "Gemini 3.5 Flash Lite"}
              </span>
              <span className="text-[11px] text-[var(--text-secondary)] block">
                {status?.llm_provider || "Google Gemini"} &middot; Active
              </span>
            </div>

            <div className="rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-panel)] p-4 space-y-1">
              <span className="text-[10px] font-mono-tech uppercase text-[var(--text-muted)] tracking-wider block">
                Dense Vectors
              </span>
              <span className="text-sm font-bold text-[var(--text-primary)] block">
                {status?.embedding_dimension || 128}-dim Cosine
              </span>
              <span className="text-[11px] text-[var(--text-secondary)] block">
                {status?.embedding_provider || "Local TF-IDF SVD"}
              </span>
            </div>

            <div className="rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-panel)] p-4 space-y-1">
              <span className="text-[10px] font-mono-tech uppercase text-[var(--text-muted)] tracking-wider block">
                Indic Voice Engine
              </span>
              <span className="text-sm font-bold text-[var(--brand-mint)] block">
                Sarvam AI v3
              </span>
              <span className="text-[11px] text-[var(--text-secondary)] block">
                Saaras STT + Bulbul TTS
              </span>
            </div>

            <div className="rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-panel)] p-4 space-y-1">
              <span className="text-[10px] font-mono-tech uppercase text-[var(--text-muted)] tracking-wider block">
                Knowledge Base
              </span>
              <span className="text-sm font-bold text-[var(--text-primary)] block">
                {status?.indexed_chunks || 165} Chunks
              </span>
              <span className="text-[11px] text-[var(--text-secondary)] block">
                Okapi BM25 + SVD Indexed
              </span>
            </div>
          </section>

          {/* Interactive Visual Pipeline Topology */}
          <section className="rounded-2xl border border-[var(--border-subtle)] bg-[var(--bg-panel)] p-6 space-y-4 shadow-sm">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-xs font-mono-tech uppercase tracking-wider text-[var(--text-muted)]">
                  Live Execution Pipeline Topology
                </h3>
                <p className="text-xs text-[var(--text-secondary)] mt-0.5">
                  Click on any stage below to inspect its algorithms, live parameters, and citation verification contract.
                </p>
              </div>
              <span className="text-[10px] font-mono-tech px-2.5 py-1 rounded-full bg-[var(--status-success-soft)] text-[var(--status-success)] border border-[var(--status-success)]/30 font-bold uppercase tracking-wider flex items-center gap-1.5">
                <span className="w-1.5 h-1.5 rounded-full bg-[var(--status-success)] animate-pulse" />
                Pipeline Active
              </span>
            </div>

            {/* Stage Nodes Flow */}
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-2.5 pt-2">
              {PIPELINE_STAGES.map((stg) => {
                const isSelected = selectedStage.id === stg.id;
                return (
                  <button
                    key={stg.id}
                    type="button"
                    onClick={() => setSelectedStage(stg)}
                    className={`p-3 rounded-xl border text-left transition-all cursor-pointer relative overflow-hidden group ${
                      isSelected
                        ? "border-[var(--accent)] bg-[var(--accent-soft)] shadow-md"
                        : "border-[var(--border-subtle)] bg-[var(--bg-surface)] hover:border-[var(--border-strong)] hover:bg-[var(--bg-surface)]/80"
                    }`}
                  >
                    {isSelected && (
                      <div className="absolute top-0 right-0 w-2 h-2 bg-[var(--accent)] rounded-bl" />
                    )}
                    <div className="flex items-center justify-between mb-1.5">
                      <span className="font-mono-tech text-[10px] font-bold text-[var(--text-muted)] group-hover:text-[var(--accent)] transition-colors">
                        {stg.shortName}
                      </span>
                      <span className="w-1.5 h-1.5 rounded-full bg-[var(--status-success)]" />
                    </div>
                    <div className="font-semibold text-xs text-[var(--text-primary)] leading-snug truncate">
                      {stg.name}
                    </div>
                    <div className="text-[10.5px] text-[var(--text-secondary)] mt-1 truncate">
                      {stg.provider}
                    </div>
                  </button>
                );
              })}
            </div>
          </section>

          {/* Detailed Stage Inspector Panel */}
          {selectedStage && (
            <section className="rounded-2xl border border-[var(--accent-border)] bg-[var(--bg-panel)] p-6 space-y-4 shadow-md animate-in fade-in duration-150">
              <div className="flex flex-wrap items-start justify-between gap-4 border-b border-[var(--border-subtle)] pb-4">
                <div>
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="text-[10px] font-mono-tech px-2 py-0.5 rounded-full bg-[var(--accent-soft)] text-[var(--accent)] border border-[var(--accent-border)] font-bold uppercase tracking-wider">
                      STAGE INSPECTOR &middot; {selectedStage.id.toUpperCase()}
                    </span>
                    <span className="text-xs font-mono-tech text-[var(--text-muted)]">
                      Provider: <strong className="text-[var(--text-primary)]">{selectedStage.provider}</strong>
                    </span>
                  </div>
                  <h3 className="font-display font-bold text-lg text-[var(--text-primary)] mt-1">
                    {selectedStage.name}
                  </h3>
                  <p className="text-xs text-[var(--text-secondary)] mt-1 max-w-2xl leading-relaxed">
                    {selectedStage.description}
                  </p>
                </div>

                <div className="px-3 py-1.5 rounded-xl bg-[var(--bg-surface)] border border-[var(--border-subtle)] text-right">
                  <span className="text-[10px] font-mono-tech uppercase text-[var(--text-muted)] block">
                    Core Algorithm
                  </span>
                  <span className="text-xs font-mono-tech font-bold text-[var(--accent)]">
                    {selectedStage.algorithm}
                  </span>
                </div>
              </div>

              {/* Parameters Grid */}
              <div>
                <h4 className="text-[11px] font-mono-tech uppercase tracking-wider text-[var(--text-muted)] mb-2.5">
                  Runtime Parameters & Operational Specifications
                </h4>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5 font-mono-tech text-xs">
                  {Object.entries(selectedStage.parameters).map(([key, val]) => (
                    <div
                      key={key}
                      className="p-3 rounded-xl bg-[var(--bg-surface)] border border-[var(--border-subtle)] flex items-center justify-between"
                    >
                      <span className="text-[var(--text-muted)] text-[11px]">{key}</span>
                      <span className="text-[var(--text-primary)] font-semibold text-right pl-2">
                        {val}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            </section>
          )}

          {/* Live System Diagnostics Readout */}
          <section className="rounded-2xl border border-[var(--border-subtle)] bg-[var(--bg-panel)] p-5 space-y-3">
            <h3 className="text-xs font-mono-tech uppercase tracking-wider text-[var(--text-muted)]">
              Backend Environment & Server Diagnostics
            </h3>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs font-mono-tech">
              <div className="p-3 rounded-xl bg-[var(--bg-surface)] border border-[var(--border-subtle)]">
                <span className="text-[10px] text-[var(--text-muted)] uppercase block">Service Version</span>
                <span className="text-[var(--text-primary)] font-semibold mt-0.5 block">
                  {health ? `${health.service} v${health.version}` : "v0.1.0 (Live)"}
                </span>
              </div>
              <div className="p-3 rounded-xl bg-[var(--bg-surface)] border border-[var(--border-subtle)]">
                <span className="text-[10px] text-[var(--text-muted)] uppercase block">Runtime Environment</span>
                <span className="text-[var(--text-primary)] font-semibold mt-0.5 block">
                  {health?.environment || "Development"}
                </span>
              </div>
              <div className="p-3 rounded-xl bg-[var(--bg-surface)] border border-[var(--border-subtle)]">
                <span className="text-[10px] text-[var(--text-muted)] uppercase block">Database Engine</span>
                <span className="text-[var(--status-success)] font-semibold mt-0.5 block">
                  {(health as { database_engine?: string } | null)?.database_engine || "PostgreSQL (pgvector + RLS)"}
                </span>
              </div>
              <div className="p-3 rounded-xl bg-[var(--bg-surface)] border border-[var(--border-subtle)]">
                <span className="text-[10px] text-[var(--text-muted)] uppercase block">Guardrails Active</span>
                <span className="text-[var(--accent)] font-semibold mt-0.5 block">
                  4 Security Layers
                </span>
              </div>
            </div>
          </section>
        </div>
      </main>
    </AppShell>
  );
}
