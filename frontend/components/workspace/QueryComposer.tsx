"use client";

import React, { useEffect, useMemo, useRef, useState } from "react";
import type { RetrieverStrategy } from "@/types/api";
import { useVoiceRecorder } from "@/hooks/use-voice-recorder";
import { MicIcon, SendIcon, StopIcon } from "@/components/ui/Icons";

interface QueryComposerProps {
  query: string;
  onQueryChange: (value: string) => void;
  onSubmitText: (params: {
    query: string;
    language?: string;
    strategy: RetrieverStrategy;
    topK: number;
  }) => void;
  onSubmitVoice: (
    blob: Blob,
    language?: string,
    strategy?: RetrieverStrategy,
    topK?: number
  ) => void;
  disabled?: boolean;
  defaultStrategy?: RetrieverStrategy;
}

const LANGUAGES = [
  { code: "", label: "Auto Lang" },
  { code: "en", label: "English (en)" },
  { code: "hi", label: "Hindi (hi)" },
  { code: "bn", label: "Bengali (bn)" },
  { code: "ta", label: "Tamil (ta)" },
  { code: "te", label: "Telugu (te)" },
  { code: "mr", label: "Marathi (mr)" },
];

const STRATEGIES: { value: RetrieverStrategy; label: string }[] = [
  { value: "hybrid", label: "Hybrid RRF" },
  { value: "dense", label: "Dense" },
  { value: "lexical", label: "BM25" },
];

export function QueryComposer({
  query,
  onQueryChange,
  onSubmitText,
  onSubmitVoice,
  disabled = false,
  defaultStrategy = "hybrid",
}: QueryComposerProps) {
  const [language, setLanguage] = useState("");
  const [strategyOverride, setStrategyOverride] =
    useState<RetrieverStrategy | null>(null);
  const strategy = strategyOverride ?? defaultStrategy;
  const [topK, setTopK] = useState<number>(5);

  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const voiceOptions = useMemo(
    () => ({
      language: language || undefined,
      onLiveTranscript: (text: string) => {
        onQueryChange(text);
      },
    }),
    [language, onQueryChange]
  );

  const {
    state: recState,
    audioBlob,
    error: recError,
    startRecording,
    stopRecording,
    reset: resetRecorder,
  } = useVoiceRecorder(voiceOptions);

  useEffect(() => {
    if (recState === "stopped" && audioBlob) {
      onSubmitVoice(audioBlob, language || undefined, strategy, topK);
      resetRecorder();
    }
  }, [recState, audioBlob, language, strategy, topK, onSubmitVoice, resetRecorder]);

  // Auto-resize textarea cleanly up to ~180px
  useEffect(() => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = `${Math.min(el.scrollHeight, 180)}px`;
  }, [query]);

  const handleSubmit = (e?: React.FormEvent) => {
    e?.preventDefault();
    const trimmed = query.trim();
    if (!trimmed || disabled) return;
    onSubmitText({
      query: trimmed,
      language: language || undefined,
      strategy,
      topK,
    });
    onQueryChange("");
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const isRecording = recState === "recording";

  return (
    <div className="shrink-0 border-t border-[var(--border-subtle)] bg-[var(--bg-canvas)]/95 backdrop-blur-sm px-4 py-3.5">
      <form
        onSubmit={handleSubmit}
        className="max-w-3xl mx-auto rounded-xl border border-[var(--border-default)] bg-[var(--bg-panel)] focus-within:border-[var(--accent-border)] focus-within:shadow-[0_0_25px_rgba(167,139,250,0.12)] transition-all"
      >
        {isRecording && (
          <div className="px-4 py-2 flex items-center justify-between text-xs border-b border-[var(--border-subtle)] bg-[var(--status-error-soft)] text-[var(--status-error)] rounded-t-xl">
            <span className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-[var(--status-error)] animate-pulse" />
              <span className="font-medium font-mono-tech">Listening to microphone... speak now</span>
            </span>
            <span className="text-[11px] font-mono-tech text-[var(--text-secondary)]">
              Click red stop button when finished
            </span>
          </div>
        )}

        <textarea
          ref={textareaRef}
          rows={1}
          value={query}
          onChange={(e) => onQueryChange(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={disabled}
          placeholder={
            isRecording
              ? "Listening... spoken words will appear here live as you talk."
              : "Ask a research question across your indexed documents..."
          }
          className="w-full resize-none bg-transparent px-4 pt-3.5 pb-2 text-[14.5px] leading-relaxed text-[var(--text-primary)] placeholder:text-[var(--text-muted)] focus:outline-none disabled:opacity-60"
        />

        {/* Bottom Utility Strip */}
        <div className="px-3 pb-2.5 pt-1 flex flex-wrap items-center justify-between gap-2 border-t border-[var(--border-subtle)]/60">
          <div className="flex flex-wrap items-center gap-1.5">
            {/* Retrieval Strategy Selector */}
            <div
              className="inline-flex rounded-md bg-[var(--bg-surface)] border border-[var(--border-subtle)] p-0.5"
              role="group"
              aria-label="Retrieval strategy"
            >
              {STRATEGIES.map((s) => (
                <button
                  key={s.value}
                  type="button"
                  onClick={() => setStrategyOverride(s.value)}
                  className={`px-2 py-1 rounded text-[11px] font-mono-tech transition-colors cursor-pointer ${
                    strategy === s.value
                      ? "bg-[var(--accent)] text-[#0C1412] font-semibold shadow-xs"
                      : "text-[var(--text-secondary)] hover:text-[var(--text-primary)]"
                  }`}
                >
                  {s.label}
                </button>
              ))}
            </div>

            {/* Language Filter */}
            <select
              value={language}
              onChange={(e) => setLanguage(e.target.value)}
              aria-label="Query language"
              className="px-2 py-1 rounded-md text-[11px] font-mono-tech bg-[var(--bg-surface)] text-[var(--text-secondary)] border border-[var(--border-subtle)] focus:outline-none focus:border-[var(--accent-border)] cursor-pointer"
            >
              {LANGUAGES.map((l) => (
                <option key={l.code} value={l.code}>
                  {l.label}
                </option>
              ))}
            </select>

            {/* Top-K */}
            <select
              value={topK}
              onChange={(e) => setTopK(Number(e.target.value))}
              aria-label="Passages count"
              className="px-2 py-1 rounded-md text-[11px] font-mono-tech bg-[var(--bg-surface)] text-[var(--text-secondary)] border border-[var(--border-subtle)] focus:outline-none focus:border-[var(--accent-border)] cursor-pointer"
            >
              <option value={3}>top-3</option>
              <option value={5}>top-5</option>
              <option value={10}>top-10</option>
            </select>
          </div>

          <div className="flex items-center gap-2">
            {/* Voice Toggle */}
            <button
              type="button"
              onClick={isRecording ? stopRecording : startRecording}
              disabled={disabled || recState === "requesting"}
              title={
                isRecording
                  ? "Stop and submit voice query"
                  : "Record voice query (Phase 4 STT backend)"
              }
              className={`relative p-2 rounded-lg border transition-colors cursor-pointer ${
                isRecording
                  ? "bg-[var(--status-error-soft)] border-[var(--status-error)]/40 text-[var(--status-error)]"
                  : "bg-[var(--bg-surface)] border-[var(--border-subtle)] text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:border-[var(--border-default)]"
              }`}
            >
              {isRecording && (
                <span className="absolute inset-0 rounded-lg border border-[var(--status-error)] animate-pulse-ring" />
              )}
              {isRecording ? <StopIcon className="w-3.5 h-3.5" /> : <MicIcon className="w-3.5 h-3.5" />}
            </button>

            {/* Submit Button */}
            <button
              type="submit"
              disabled={!query.trim() || disabled || isRecording}
              className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg text-xs font-semibold bg-[var(--accent)] text-[#0C1412] hover:bg-[var(--accent-hover)] shadow-[0_0_15px_rgba(167,139,250,0.2)] disabled:opacity-35 disabled:cursor-not-allowed transition-all cursor-pointer active:scale-95"
            >
              <span>Run</span>
              <SendIcon className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      </form>

      {recError && (
        <p className="max-w-3xl mx-auto mt-1.5 text-[11px] text-[var(--status-error)]">
          Microphone error: {recError}
        </p>
      )}
    </div>
  );
}
