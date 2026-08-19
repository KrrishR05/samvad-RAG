"use client";

import type { QueryResponse } from "@/types/api";

interface AnswerPanelProps {
  response: QueryResponse | null;
  isLoading: boolean;
  isDemoData?: boolean;
}

export default function AnswerPanel({
  response,
  isLoading,
  isDemoData = false,
}: AnswerPanelProps) {
  // Loading state
  if (isLoading) {
    return (
      <div className="rounded-xl border border-border-subtle bg-bg-surface/50 p-6 animate-fade-in">
        <div className="flex items-center gap-3">
          <div className="w-4 h-4 rounded-full border-2 border-accent border-t-transparent animate-spin" />
          <span className="text-sm text-text-secondary">Processing query...</span>
        </div>
      </div>
    );
  }

  if (!response) return null;

  // Not implemented
  if (response.status === "not_implemented") {
    return (
      <div className="rounded-xl border border-border-subtle bg-bg-surface/50 p-6 animate-slide-up">
        <div className="flex items-start gap-3">
          <div className="w-8 h-8 rounded-lg bg-warning/10 border border-warning/20 flex items-center justify-center flex-shrink-0 mt-0.5">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-warning">
              <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
              <line x1="12" y1="9" x2="12" y2="13" />
              <line x1="12" y1="17" x2="12.01" y2="17" />
            </svg>
          </div>
          <div>
            <p className="text-sm font-medium text-text-primary mb-1">
              Pipeline Not Connected
            </p>
            <p className="text-xs text-text-secondary leading-relaxed">
              {response.message}
            </p>
            <p className="text-[10px] font-mono text-text-muted mt-2">
              ID: {response.request_id}
            </p>
          </div>
        </div>
      </div>
    );
  }

  // Abstained
  if (response.status === "abstained") {
    return (
      <div className="rounded-xl border border-abstained/20 bg-bg-surface/50 p-6 animate-slide-up">
        {isDemoData && <DemoBadge />}
        {response.transcript && (
          <p className="text-xs text-text-muted mb-3 font-mono">
            &ldquo;{response.transcript}&rdquo;
          </p>
        )}
        <div className="flex items-start gap-3">
          <div className="w-8 h-8 rounded-lg bg-abstained/10 border border-abstained/20 flex items-center justify-center flex-shrink-0">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-abstained">
              <circle cx="12" cy="12" r="10" />
              <line x1="12" y1="8" x2="12" y2="12" />
              <line x1="12" y1="16" x2="12.01" y2="16" />
            </svg>
          </div>
          <p className="text-sm text-text-secondary leading-relaxed">
            {response.message ||
              "I couldn't find enough reliable information in the available knowledge base to answer that confidently."}
          </p>
        </div>
      </div>
    );
  }

  // Error
  if (response.status === "error") {
    return (
      <div className="rounded-xl border border-error/20 bg-bg-surface/50 p-6 animate-slide-up">
        <div className="flex items-start gap-3">
          <div className="w-8 h-8 rounded-lg bg-error/10 border border-error/20 flex items-center justify-center flex-shrink-0">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-error">
              <circle cx="12" cy="12" r="10" />
              <line x1="15" y1="9" x2="9" y2="15" />
              <line x1="9" y1="9" x2="15" y2="15" />
            </svg>
          </div>
          <div>
            <p className="text-sm font-medium text-error mb-1">
              An error occurred
            </p>
            <p className="text-xs text-text-secondary">
              {response.message || "Please try again."}
            </p>
          </div>
        </div>
      </div>
    );
  }

  // Completed — full answer
  return (
    <div className="rounded-xl border border-border-subtle bg-bg-surface/50 p-6 animate-slide-up space-y-5">
      {isDemoData && <DemoBadge />}

      {/* Transcript */}
      {response.transcript && (
        <p className="text-xs text-text-muted font-mono">
          &ldquo;{response.transcript}&rdquo;
        </p>
      )}

      {/* Answer */}
      {response.answer && (
        <div className="text-sm text-text-primary leading-relaxed">
          {response.answer}
        </div>
      )}

      {/* Meta row */}
      <div className="flex flex-wrap items-center gap-3 pt-2 border-t border-border-subtle">
        {/* Grounded badge */}
        {response.grounded != null && (
          <span
            className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[10px] font-mono font-medium ${
              response.grounded
                ? "bg-success/10 text-success border border-success/20"
                : "bg-warning/10 text-warning border border-warning/20"
            }`}
          >
            <span
              className={`w-1.5 h-1.5 rounded-full ${
                response.grounded ? "bg-success" : "bg-warning"
              }`}
            />
            {response.grounded ? "Grounded" : "Ungrounded"}
          </span>
        )}

        {/* Confidence */}
        {response.confidence?.level && (
          <span className="text-[10px] font-mono text-text-muted">
            Confidence:{" "}
            <span className="text-text-secondary">
              {response.confidence.level}
              {response.confidence.score != null &&
                ` (${(response.confidence.score * 100).toFixed(0)}%)`}
            </span>
          </span>
        )}

        {/* Total latency */}
        {response.latency?.total_ms != null && (
          <span className="text-[10px] font-mono text-text-muted">
            {response.latency.total_ms.toFixed(0)}ms total
          </span>
        )}
      </div>

      {/* Sources */}
      {response.sources.length > 0 && (
        <div className="pt-2">
          <h4 className="text-[10px] font-mono font-semibold text-text-muted uppercase tracking-[0.2em] mb-2">
            Sources
          </h4>
          <div className="space-y-2">
            {response.sources.map((src, i) => (
              <div
                key={src.source_id}
                className="rounded-lg border border-border-subtle bg-bg-elevated/50 p-3"
              >
                <div className="flex items-start justify-between gap-2 mb-1">
                  <span className="text-[10px] font-mono text-text-muted">
                    [{i + 1}] {src.passage_id || src.source_id}
                  </span>
                  <div className="flex gap-2 text-[10px] font-mono text-text-muted">
                    {src.retrieval_score != null && (
                      <span>ret: {src.retrieval_score.toFixed(2)}</span>
                    )}
                    {src.reranker_score != null && (
                      <span>rrk: {src.reranker_score.toFixed(2)}</span>
                    )}
                  </div>
                </div>
                <p className="text-xs text-text-secondary leading-relaxed">
                  {src.text}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function DemoBadge() {
  return (
    <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-warning/5 border border-warning/10 w-fit">
      <div className="w-1.5 h-1.5 rounded-full bg-warning" />
      <span className="text-[9px] font-mono text-warning/80 uppercase tracking-widest">
        Demo Data — Not Real AI Output
      </span>
    </div>
  );
}
