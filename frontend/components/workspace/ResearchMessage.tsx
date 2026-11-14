"use client";

import React, { useRef, useState } from "react";
import Link from "next/link";
import type { QueryResponse, RetrieverStrategy } from "@/types/api";
import { AlertIcon, CheckIcon, CopyIcon, SpeakerIcon } from "@/components/ui/Icons";
import { synthesizeSpeech } from "@/lib/api/client";
import { MarkdownAnswer } from "@/components/workspace/MarkdownAnswer";

export interface ResearchTurn {
  id: string;
  query: string;
  kind: "text" | "voice";
  language?: string;
  strategy: RetrieverStrategy;
  createdAt: string;
  response?: QueryResponse | null;
  error?: string | null;
  isLoading?: boolean;
}

interface ResearchMessageProps {
  turn: ResearchTurn;
  isInspected: boolean;
  onInspectTurn: (turnId: string, tab?: "evidence" | "pipeline", sourceIdx?: number) => void;
}


export function ResearchMessage({
  turn,
  isInspected,
  onInspectTurn,
}: ResearchMessageProps) {
  const [copied, setCopied] = useState(false);
  const [isPlayingAudio, setIsPlayingAudio] = useState(false);
  const [isAudioLoading, setIsAudioLoading] = useState(false);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const resp = turn.response;

  const handleSpeak = async () => {
    if (isPlayingAudio && audioRef.current) {
      audioRef.current.pause();
      setIsPlayingAudio(false);
      return;
    }
    if (!resp?.answer) return;
    try {
      setIsAudioLoading(true);
      const blob = await synthesizeSpeech(resp.answer, turn.language);
      const url = URL.createObjectURL(blob);
      const audio = new Audio(url);
      audioRef.current = audio;
      audio.onended = () => setIsPlayingAudio(false);
      audio.onerror = () => {
        setIsPlayingAudio(false);
        setIsAudioLoading(false);
      };
      setIsAudioLoading(false);
      setIsPlayingAudio(true);
      await audio.play();
    } catch (err) {
      console.error("TTS playback failed:", err);
      setIsAudioLoading(false);
      setIsPlayingAudio(false);
    }
  };

  const handleCopy = async () => {
    if (!resp?.answer) return;
    try {
      await navigator.clipboard.writeText(resp.answer);
      setCopied(true);
      setTimeout(() => setCopied(false), 1800);
    } catch {
      // Ignore clipboard denials
    }
  };

  return (
    <article
      className={`rounded-xl border transition-all duration-200 ${
        isInspected
          ? "samvad-message-card-active border-[var(--accent-border)] shadow-[0_0_28px_rgba(167,139,250,0.12)]"
          : "samvad-message-card border-[var(--brand-forest-border)] hover:border-[var(--border-default)] hover:shadow-[0_4px_24px_rgba(0,0,0,0.25)]"
      }`}
    >
      {/* Query Strip */}
      <div className="px-5 py-3.5 border-b border-[var(--brand-forest-border)] flex items-start justify-between gap-4 samvad-query-accent">
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2 mb-1">
            <span className="text-[10px] font-mono-tech uppercase tracking-wider text-[var(--text-muted)]">
              {turn.kind === "voice" ? "Voice Query" : "Query"}
            </span>
            <span className="text-[10px] font-mono-tech px-1.5 py-0.5 rounded bg-[var(--accent-soft)] text-[var(--accent)] border border-[var(--accent-border)]/50">
              {turn.strategy}
            </span>
            {turn.language && (
              <span className="text-[10px] font-mono-tech px-1.5 py-0.5 rounded bg-[var(--bg-surface)] text-[var(--text-muted)] border border-[var(--border-subtle)]">
                lang:{turn.language}
              </span>
            )}
          </div>
          <p className="font-display font-medium text-[15px] text-[var(--text-primary)] leading-snug">
            {turn.query}
          </p>
        </div>

        <span className="text-[11px] font-mono-tech text-[var(--text-muted)] shrink-0 mt-0.5">
          {new Date(turn.createdAt).toLocaleTimeString([], {
            hour: "2-digit",
            minute: "2-digit",
          })}
        </span>
      </div>

      {/* Answer / Loading / Error Body */}
      <div className="px-5 py-4 space-y-4">
        {turn.isLoading && (
          <div className="flex items-center gap-3 py-2 text-sm text-[var(--text-secondary)]">
            <span className="w-2 h-2 rounded-full bg-[var(--accent)] animate-pulse" />
            <span>Running retrieval and evidence grounding pipeline...</span>
          </div>
        )}

        {turn.error && !turn.isLoading && (
          <div className="rounded-lg border border-[var(--status-error)]/30 bg-[var(--status-error-soft)] px-4 py-3 flex items-start gap-2.5 text-sm text-[var(--text-primary)]">
            <AlertIcon className="w-4 h-4 text-[var(--status-error)] shrink-0 mt-0.5" />
            <div>
              <p className="font-medium text-xs uppercase tracking-wider font-mono-tech text-[var(--status-error)]">
                Request Failed
              </p>
              <p className="mt-1 text-[13px] text-[var(--text-secondary)]">{turn.error}</p>
            </div>
          </div>
        )}

        {resp && !turn.isLoading && (
          <>
            {/* Metadata & Status Header */}
            <div className="flex flex-wrap items-center justify-between gap-2">
              <div className="flex flex-wrap items-center gap-2">
                {resp.status === "completed" && (
                  <span
                    className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-[11px] font-mono-tech border ${
                      resp.grounded
                        ? "bg-[var(--status-success-soft)] text-[var(--status-success)] border-[var(--status-success)]/30"
                        : "bg-[var(--status-warning-soft)] text-[var(--status-warning)] border-[var(--status-warning)]/30"
                    }`}
                  >
                    <span className="w-1.5 h-1.5 rounded-full bg-current" />
                    {resp.grounded ? "Citation-Linked" : "Uncited Output"}
                  </span>
                )}

                {resp.status === "abstained" && (
                  <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-[11px] font-mono-tech bg-[var(--status-abstained-soft)] text-[var(--status-abstained)] border border-[var(--status-abstained)]/30">
                    Abstained — Insufficient Evidence
                  </span>
                )}

                {resp.status === "not_implemented" && (
                  <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-[11px] font-mono-tech bg-[var(--status-warning-soft)] text-[var(--status-warning)] border border-[var(--status-warning)]/30">
                    Generation Unconfigured
                  </span>
                )}

                {resp.retrieval_method && (
                  <span className="text-[11px] font-mono-tech text-[var(--text-muted)]">
                    via {resp.retrieval_method}
                  </span>
                )}

                {resp.sources.length > 0 && (
                  <button
                    type="button"
                    onClick={() => onInspectTurn(turn.id, "evidence")}
                    className="text-[11px] font-mono-tech text-[var(--accent)] hover:underline cursor-pointer"
                  >
                    {resp.sources.length} passage{resp.sources.length === 1 ? "" : "s"} retrieved
                  </button>
                )}
              </div>

              <div className="flex items-center gap-2">
                {resp.latency?.total_ms !== undefined && resp.latency?.total_ms !== null && (
                  <span className="text-[11px] font-mono-tech text-[var(--text-muted)]">
                    {resp.latency.total_ms.toFixed(1)} ms
                  </span>
                )}
                {resp.answer && (
                  <>
                    <button
                      type="button"
                      onClick={handleSpeak}
                      disabled={isAudioLoading}
                      className={`inline-flex items-center gap-1.5 px-2 py-1 rounded text-[11px] font-mono-tech border transition-colors cursor-pointer ${
                        isPlayingAudio
                          ? "bg-[var(--accent-soft)] text-[var(--accent)] border-[var(--accent-border)] animate-pulse"
                          : "text-[var(--text-muted)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-hover)] border-transparent"
                      }`}
                      title={isPlayingAudio ? "Pause speech audio" : "Listen to answer via Sarvam Bulbul"}
                    >
                      <SpeakerIcon className="w-3.5 h-3.5" />
                      <span>
                        {isAudioLoading ? "Loading..." : isPlayingAudio ? "Playing..." : "Listen"}
                      </span>
                    </button>

                    <button
                      type="button"
                      onClick={handleCopy}
                      className="inline-flex items-center gap-1 px-2 py-1 rounded text-[11px] text-[var(--text-muted)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-hover)] transition-colors cursor-pointer"
                      title="Copy answer"
                    >
                      {copied ? <CheckIcon /> : <CopyIcon />}
                      <span>{copied ? "Copied" : "Copy"}</span>
                    </button>
                  </>
                )}
                <button
                  type="button"
                  onClick={() => onInspectTurn(turn.id, "pipeline")}
                  className="px-2 py-1 rounded text-[11px] font-mono-tech text-[var(--text-secondary)] hover:text-[var(--text-primary)] bg-[var(--bg-surface)] border border-[var(--border-subtle)] hover:border-[var(--border-default)] transition-colors cursor-pointer"
                >
                  Inspect Trace
                </button>
              </div>
            </div>

            {/* Voice transcript notice if present */}
            {resp.transcript && (
              <div className="rounded-lg bg-[var(--bg-surface)] border border-[var(--border-subtle)] px-3.5 py-2 text-xs text-[var(--text-secondary)]">
                <span className="font-mono-tech uppercase text-[10px] text-[var(--text-muted)] mr-2">
                  Transcript:
                </span>
                &ldquo;{resp.transcript}&rdquo;
              </div>
            )}

            {/* Answer Prose with Markdown Formatting & Interactive Citations */}
            {resp.answer && resp.answer !== resp.message && (
              <div className="text-[15px] leading-[1.7] text-[var(--text-primary)]">
                <MarkdownAnswer
                  content={resp.answer}
                  totalSources={resp.sources.length}
                  onSelectCitation={(citNum) =>
                    onInspectTurn(turn.id, "evidence", citNum - 1)
                  }
                />
              </div>
            )}

            {/* Diagnostic / Unconfigured / Abstained Message */}
            {resp.message && resp.status !== "completed" && (
              <div className="rounded-lg border border-[var(--border-subtle)] bg-[var(--bg-surface)] px-4 py-3 text-[13px] text-[var(--text-secondary)] space-y-2">
                <p>{resp.message}</p>
                {resp.status === "not_implemented" && (
                  <div className="flex flex-wrap gap-3 pt-1 text-xs">
                    <Link
                      href="/settings"
                      className="text-[var(--accent)] hover:underline font-medium"
                    >
                      View .env Provider Setup &rarr;
                    </Link>
                    <Link
                      href="/documents"
                      className="text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:underline"
                    >
                      Manage Knowledge Base &rarr;
                    </Link>
                  </div>
                )}
              </div>
            )}

            {/* Compact Source Chips Strip */}
            {resp.sources.length > 0 && (
              <div className="pt-2 border-t border-[var(--border-subtle)] flex flex-wrap items-center gap-1.5">
                <span className="text-[11px] font-mono-tech text-[var(--text-muted)] mr-1">
                  Sources:
                </span>
                {resp.sources.map((src, i) => {
                  const isCited = Boolean(src.metadata?.is_cited);
                  const docId =
                    typeof src.metadata?.parent_document_id === "string"
                      ? src.metadata.parent_document_id
                      : src.passage_id || src.source_id;
                  return (
                    <button
                      key={src.source_id}
                      type="button"
                      onClick={() => onInspectTurn(turn.id, "evidence", i)}
                      className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-md text-[11px] font-mono-tech border transition-colors cursor-pointer ${
                        isCited
                          ? "bg-[var(--accent-soft)] border-[var(--accent-border)] text-[var(--text-primary)]"
                          : "bg-[var(--bg-surface)] border-[var(--border-subtle)] text-[var(--text-secondary)] hover:border-[var(--border-default)]"
                      }`}
                    >
                      <span className="text-[var(--accent)] font-semibold">[{i + 1}]</span>
                      <span className="truncate max-w-[140px]">{docId}</span>
                      {src.retrieval_score !== undefined && src.retrieval_score !== null && (
                        <span className="text-[var(--text-muted)]">
                          {src.retrieval_score.toFixed(3)}
                        </span>
                      )}
                    </button>
                  );
                })}
              </div>
            )}
          </>
        )}
      </div>
    </article>
  );
}

