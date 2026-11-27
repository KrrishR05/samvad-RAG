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
    cancelRecording,
    reset: resetRecorder,
  } = useVoiceRecorder(voiceOptions);

  useEffect(() => {
    if (recState === "stopped" && audioBlob) {
      onSubmitVoice(audioBlob, language || undefined, strategy, topK);
      onQueryChange("");
      resetRecorder();
    }
  }, [recState, audioBlob, language, strategy, topK, onSubmitVoice, onQueryChange, resetRecorder]);

  // Keep textarea in compact normal position: min 38px, capped at 72px with scrollbar
  useEffect(() => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = "auto";
    const targetHeight = Math.min(Math.max(el.scrollHeight, 38), 72);
    el.style.height = `${targetHeight}px`;
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

  const handleCancelVoice = () => {
    cancelRecording();
    onQueryChange("");
  };

  const isRecording = recState === "recording";

  return (
    <div className="shrink-0 border-t border-[var(--border-subtle)] bg-[var(--bg-canvas)]/95 backdrop-blur-sm px-4 py-2.5 flex flex-col justify-center">
      <form
        onSubmit={handleSubmit}
        className="max-w-3xl mx-auto w-full rounded-xl border border-[var(--border-default)] bg-[var(--bg-panel)] focus-within:border-[var(--accent-border)] focus-within:shadow-[0_0_20px_rgba(167,139,250,0.1)] transition-all"
      >
        {isRecording && (
          <div className="px-4 py-1.5 flex items-center justify-between text-xs border-b border-[var(--border-subtle)] bg-[var(--status-error-soft)] text-[var(--status-error)] rounded-t-xl">
            <span className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-[var(--status-error)] animate-pulse" />
              <span className="font-medium font-mono-tech">Listening to microphone... speak now</span>
            </span>
            <button
              type="button"
              onClick={handleCancelVoice}
              className="text-[11px] font-mono-tech text-[var(--text-secondary)] hover:text-[var(--text-primary)] underline underline-offset-2 cursor-pointer"
            >
              Cancel
            </button>
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
          className="w-full resize-none bg-transparent px-3.5 pt-2 pb-1 text-[13.5px] leading-relaxed text-[var(--text-primary)] placeholder:text-[var(--text-muted)] focus:outline-none disabled:opacity-60 overflow-y-auto max-h-[72px]"
          style={{ minHeight: "38px" }}
        />

        {/* Bottom Utility Strip */}
        <div className="px-3 pb-1.5 pt-0.5 flex flex-wrap items-center justify-between gap-2 border-t border-[var(--border-subtle)]/60">
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
                  className={`px-2 py-0.5 rounded text-[11px] font-mono-tech transition-colors cursor-pointer ${
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
              className="px-2 py-0.5 rounded-md text-[11px] font-mono-tech bg-[var(--bg-surface)] text-[var(--text-secondary)] border border-[var(--border-subtle)] focus:outline-none focus:border-[var(--accent-border)] cursor-pointer"
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
              className="px-2 py-0.5 rounded-md text-[11px] font-mono-tech bg-[var(--bg-surface)] text-[var(--text-secondary)] border border-[var(--border-subtle)] focus:outline-none focus:border-[var(--accent-border)] cursor-pointer"
            >
              <option value={3}>top-3</option>
              <option value={5}>top-5</option>
              <option value={10}>top-10</option>
            </select>
          </div>

          <div className="flex items-center gap-2">
            {/* Cancel Voice Recording Button (shown while recording) */}
            {isRecording && (
              <button
                type="button"
                onClick={handleCancelVoice}
                aria-label="Cancel voice recording"
                title="Cancel recording without sending"
                className="w-9 h-9 rounded-full border border-[var(--border-strong)] bg-[var(--bg-surface)] text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:border-[var(--status-error)]/50 hover:bg-[var(--status-error-soft)] flex items-center justify-center transition-all cursor-pointer active:scale-95"
              >
                <svg
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2.2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  className="w-4 h-4"
                >
                  <line x1="18" y1="6" x2="6" y2="18" />
                  <line x1="6" y1="6" x2="18" y2="18" />
                </svg>
              </button>
            )}

            {/* Voice-First Mic Button */}
            <button
              type="button"
              onClick={isRecording ? stopRecording : startRecording}
              disabled={disabled || recState === "requesting"}
              aria-label={isRecording ? "Stop and submit voice query" : "Record voice query"}
              title={
                isRecording
                  ? "Stop and submit voice query"
                  : "Speak your query (Sarvam AI Indic STT)"
              }
              className={`relative w-9 h-9 rounded-full border flex items-center justify-center transition-all cursor-pointer active:scale-95 disabled:opacity-40 disabled:cursor-not-allowed ${
                isRecording
                  ? "bg-[var(--status-error)] border-[var(--status-error)] text-white shadow-[0_0_18px_rgba(239,68,68,0.45)]"
                  : "bg-[var(--accent-soft)] border-[var(--accent-border)] text-[var(--accent)] hover:bg-[var(--accent)]/20 hover:shadow-[0_0_16px_rgba(167,139,250,0.28)]"
              }`}
            >
              {isRecording && (
                <span className="absolute inset-0 rounded-full border-2 border-[var(--status-error)] animate-ping opacity-60" />
              )}
              {isRecording ? (
                <StopIcon className="w-4 h-4 relative z-10" />
              ) : (
                <MicIcon className="w-4 h-4 relative z-10" />
              )}
            </button>

            {/* Arrow-Only Submit Button (ChatGPT-style) */}
            <button
              type="submit"
              disabled={!query.trim() || disabled || isRecording}
              aria-label="Send query"
              title="Send query (Enter)"
              className={`w-9 h-9 rounded-full flex items-center justify-center transition-all cursor-pointer active:scale-95 ${
                !query.trim() || disabled || isRecording
                  ? "bg-[var(--bg-surface)] text-[var(--text-muted)] border border-[var(--border-subtle)] opacity-55 cursor-not-allowed"
                  : "bg-[var(--accent)] text-[#0C1412] hover:bg-[var(--accent-hover)] shadow-[0_0_16px_rgba(167,139,250,0.3)]"
              }`}
            >
              <SendIcon className="w-4 h-4" />
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
