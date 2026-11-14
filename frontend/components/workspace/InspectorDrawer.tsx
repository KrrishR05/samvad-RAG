"use client";

import React, { useEffect, useRef, useState } from "react";
import type { QueryResponse, StageResult } from "@/types/api";
import type { ResearchTurn } from "@/components/workspace/ResearchMessage";

interface InspectorDrawerProps {
  open: boolean;
  onClose: () => void;
  turn: ResearchTurn | null;
  activeTab: "evidence" | "pipeline";
  onTabChange: (tab: "evidence" | "pipeline") => void;
  selectedSourceIndex: number | null;
  onSelectSourceIndex: (index: number | null) => void;
}

function stageBadgeClass(status: StageResult["status"]) {
  switch (status) {
    case "completed":
      return "bg-[var(--status-success-soft)] text-[var(--status-success)] border-[var(--status-success)]/30";
    case "error":
      return "bg-[var(--status-error-soft)] text-[var(--status-error)] border-[var(--status-error)]/30";
    case "abstained":
      return "bg-[var(--status-abstained-soft)] text-[var(--status-abstained)] border-[var(--status-abstained)]/30";
    case "skipped":
      return "bg-[var(--status-warning-soft)] text-[var(--status-warning)] border-[var(--status-warning)]/30";
    default:
      return "bg-[var(--bg-surface)] text-[var(--text-muted)] border-[var(--border-subtle)]";
  }
}

export function InspectorDrawer({
  open,
  onClose,
  turn,
  activeTab,
  onTabChange,
  selectedSourceIndex,
  onSelectSourceIndex,
}: InspectorDrawerProps) {
  const [expandedSources, setExpandedSources] = useState<Record<string, boolean>>({});
  const sourceRefs = useRef<Record<number, HTMLDivElement | null>>({});

  useEffect(() => {
    if (selectedSourceIndex !== null && activeTab === "evidence") {
      const el = sourceRefs.current[selectedSourceIndex];
      el?.scrollIntoView({ behavior: "smooth", block: "nearest" });
    }
  }, [selectedSourceIndex, activeTab]);

  if (!open) return null;

  const resp: QueryResponse | null | undefined = turn?.response;
  const sources = resp?.sources ?? [];
  const stages = resp?.stages ?? [];
  const maxDuration = stages.reduce(
    (max, st) => Math.max(max, st.duration_ms ?? 0),
    1
  );

  return (
    <aside
      aria-label="Evidence and Pipeline Inspector"
      className="w-full sm:w-[390px] shrink-0 h-full border-l border-[var(--brand-forest-border)] flex flex-col"
      style={{
        background: 'linear-gradient(180deg, rgba(14,22,20,0.97) 0%, rgba(12,20,18,0.99) 100%)',
        backdropFilter: 'blur(8px)',
      }}
    >
      {/* Header + Tabs */}
      <div className="h-14 shrink-0 px-4 border-b border-[var(--brand-forest-border)] flex items-center justify-between gap-2">
        <div className="inline-flex rounded-md bg-[var(--bg-surface)] border border-[var(--border-subtle)] p-0.5">
          <button
            type="button"
            onClick={() => onTabChange("evidence")}
            className={`px-2.5 py-1 rounded text-xs font-medium transition-colors cursor-pointer ${
              activeTab === "evidence"
                ? "bg-[var(--accent-soft)] text-[var(--accent)] border border-[var(--accent-border)]/50 shadow-sm"
                : "text-[var(--text-muted)] hover:text-[var(--text-primary)]"
            }`}
          >
            Evidence ({sources.length})
          </button>
          <button
            type="button"
            onClick={() => onTabChange("pipeline")}
            className={`px-2.5 py-1 rounded text-xs font-medium transition-colors cursor-pointer ${
              activeTab === "pipeline"
                ? "bg-[var(--accent-soft)] text-[var(--accent)] border border-[var(--accent-border)]/50 shadow-sm"
                : "text-[var(--text-muted)] hover:text-[var(--text-primary)]"
            }`}
          >
            Pipeline ({stages.length})
          </button>
        </div>

        <button
          type="button"
          onClick={onClose}
          className="px-2 py-1 rounded text-xs text-[var(--text-muted)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-hover)] cursor-pointer"
        >
          Close
        </button>
      </div>

      {/* Body */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {!turn && (
          <div className="rounded-lg border border-dashed border-[var(--border-default)] p-6 text-center text-xs text-[var(--text-muted)]">
            Run a query or click &ldquo;Inspect Trace&rdquo; on any response to examine retrieved passages, real retrieval scores, and stage timings.
          </div>
        )}

        {turn && turn.isLoading && (
          <div className="rounded-lg border border-[var(--border-subtle)] bg-[var(--bg-surface)] p-4 text-xs text-[var(--text-secondary)]">
            Executing query pipeline stages...
          </div>
        )}

        {turn && !turn.isLoading && activeTab === "evidence" && (
          <>
            {sources.length === 0 ? (
              <div className="rounded-lg border border-dashed border-[var(--border-default)] p-5 text-xs text-[var(--text-muted)] space-y-1.5">
                <p className="font-medium text-[var(--text-secondary)]">
                  No passages retrieved
                </p>
                <p>
                  No chunks matched this query in the indexed corpus. Try indexing documents in Knowledge Base or relaxing the language filter.
                </p>
              </div>
            ) : (
              sources.map((src, idx) => {
                const isSelected = selectedSourceIndex === idx;
                const isCited = Boolean(src.metadata?.is_cited);
                const docId =
                  typeof src.metadata?.parent_document_id === "string"
                    ? src.metadata.parent_document_id
                    : src.passage_id || src.source_id;
                const lang =
                  typeof src.metadata?.language === "string"
                    ? src.metadata.language
                    : null;
                const method =
                  typeof src.metadata?.retrieval_method === "string"
                    ? src.metadata.retrieval_method
                    : resp?.retrieval_method || "retrieval";
                const chunkStrategy =
                  typeof src.metadata?.chunk_strategy === "string"
                    ? src.metadata.chunk_strategy
                    : null;
                const chunkIndex =
                  typeof src.metadata?.chunk_index === "number"
                    ? src.metadata.chunk_index
                    : null;

                const isExpanded =
                  expandedSources[src.source_id] || src.text.length <= 280;

                return (
                  <div
                    key={src.source_id}
                    ref={(el) => {
                      sourceRefs.current[idx] = el;
                    }}
                    onClick={() => onSelectSourceIndex(idx)}
                    className={`rounded-lg border p-3.5 space-y-2.5 transition-colors ${
                      isSelected
                        ? "border-[var(--accent)] bg-[var(--accent-soft)]/50"
                        : "border-[var(--border-subtle)] bg-[var(--bg-surface)]/70 hover:border-[var(--border-default)]"
                    }`}
                  >
                    <div className="flex items-start justify-between gap-2">
                      <div className="flex items-center gap-2 min-w-0">
                        <span className="font-mono-tech text-xs font-semibold px-1.5 py-0.5 rounded bg-[var(--accent-soft)] text-[var(--accent)] border border-[var(--accent-border)]">
                          [{idx + 1}]
                        </span>
                        <span className="font-mono-tech text-xs text-[var(--text-primary)] truncate">
                          {docId}
                        </span>
                      </div>
                      {isCited && (
                        <span className="text-[10px] font-mono-tech px-1.5 py-0.5 rounded bg-[var(--status-success-soft)] text-[var(--status-success)] border border-[var(--status-success)]/30 shrink-0">
                          Cited
                        </span>
                      )}
                    </div>

                    {/* Real numeric scores only */}
                    <div className="flex flex-wrap items-center gap-1.5 text-[10px] font-mono-tech">
                      <span className="px-1.5 py-0.5 rounded bg-[var(--bg-panel)] border border-[var(--border-subtle)] text-[var(--text-secondary)]">
                        {method}
                      </span>
                      {src.retrieval_score !== undefined &&
                        src.retrieval_score !== null && (
                          <span className="px-1.5 py-0.5 rounded bg-[var(--bg-panel)] border border-[var(--border-subtle)] text-[var(--text-primary)]">
                            score: {src.retrieval_score.toFixed(4)}
                          </span>
                        )}
                      {src.reranker_score !== undefined &&
                        src.reranker_score !== null && (
                          <span className="px-1.5 py-0.5 rounded bg-[var(--bg-panel)] border border-[var(--border-subtle)] text-[var(--text-primary)]">
                            rerank: {src.reranker_score.toFixed(4)}
                          </span>
                        )}
                      {lang && (
                        <span className="px-1.5 py-0.5 rounded bg-[var(--bg-panel)] border border-[var(--border-subtle)] text-[var(--text-muted)]">
                          {lang}
                        </span>
                      )}
                      {chunkIndex !== null && (
                        <span className="px-1.5 py-0.5 rounded bg-[var(--bg-panel)] border border-[var(--border-subtle)] text-[var(--text-muted)]">
                          chunk #{chunkIndex}
                        </span>
                      )}
                      {chunkStrategy && (
                        <span className="px-1.5 py-0.5 rounded bg-[var(--bg-panel)] border border-[var(--border-subtle)] text-[var(--text-muted)]">
                          {chunkStrategy}
                        </span>
                      )}
                    </div>

                    <p className="text-xs leading-relaxed text-[var(--text-secondary)] whitespace-pre-wrap">
                      {isExpanded ? src.text : `${src.text.slice(0, 280)}...`}
                    </p>

                    {src.text.length > 280 && (
                      <button
                        type="button"
                        onClick={(e) => {
                          e.stopPropagation();
                          setExpandedSources((prev) => ({
                            ...prev,
                            [src.source_id]: !prev[src.source_id],
                          }));
                        }}
                        className="text-[11px] font-mono-tech text-[var(--accent)] hover:underline cursor-pointer"
                      >
                        {isExpanded ? "Show less" : "Read full chunk"}
                      </button>
                    )}
                  </div>
                );
              })
            )}
          </>
        )}

        {turn && !turn.isLoading && activeTab === "pipeline" && (
          <div className="space-y-4">
            {/* Request Metadata */}
            {resp && (
              <div className="rounded-lg border border-[var(--border-subtle)] bg-[var(--bg-surface)] p-3 space-y-1.5 text-[11px] font-mono-tech">
                <div className="flex justify-between gap-2">
                  <span className="text-[var(--text-muted)]">request_id</span>
                  <span className="text-[var(--text-primary)] truncate">
                    {resp.request_id}
                  </span>
                </div>
                <div className="flex justify-between gap-2">
                  <span className="text-[var(--text-muted)]">status</span>
                  <span className="text-[var(--text-primary)]">{resp.status}</span>
                </div>
                {resp.retrieval_method && (
                  <div className="flex justify-between gap-2">
                    <span className="text-[var(--text-muted)]">retriever</span>
                    <span className="text-[var(--text-primary)]">
                      {resp.retrieval_method}
                    </span>
                  </div>
                )}
              </div>
            )}

            {/* Stage Execution Trace */}
            <div className="space-y-2">
              <p className="text-[10px] font-mono-tech uppercase tracking-wider text-[var(--text-muted)]">
                Executed Pipeline Stages
              </p>
              {stages.length === 0 ? (
                <p className="text-xs text-[var(--text-muted)]">
                  No stage telemetry returned for this response.
                </p>
              ) : (
                stages.map((st, idx) => {
                  const pct =
                    st.duration_ms != null
                      ? Math.max(4, Math.round((st.duration_ms / maxDuration) * 100))
                      : 0;
                  return (
                    <div
                      key={`${st.stage}-${idx}`}
                      className="rounded-lg border border-[var(--border-subtle)] bg-[var(--bg-surface)] p-3 space-y-2"
                    >
                      <div className="flex items-center justify-between gap-2">
                        <span className="font-mono-tech text-xs font-medium text-[var(--text-primary)]">
                          {idx + 1}. {st.stage}
                        </span>
                        <div className="flex items-center gap-2">
                          {st.duration_ms != null && (
                            <span className="font-mono-tech text-[11px] text-[var(--text-secondary)]">
                              {st.duration_ms.toFixed(2)} ms
                            </span>
                          )}
                          <span
                            className={`px-1.5 py-0.5 rounded text-[10px] font-mono-tech border ${stageBadgeClass(
                              st.status
                            )}`}
                          >
                            {st.status}
                          </span>
                        </div>
                      </div>

                      {st.duration_ms != null && (
                        <div className="w-full h-1 rounded-full bg-[var(--bg-panel)] overflow-hidden">
                          <div
                            className="h-full bg-[var(--accent)] rounded-full"
                            style={{ width: `${pct}%` }}
                          />
                        </div>
                      )}

                      {st.output != null && (
                        <pre className="text-[10px] font-mono-tech text-[var(--text-muted)] overflow-x-auto whitespace-pre-wrap">
                          {JSON.stringify(st.output)}
                        </pre>
                      )}

                      {st.error && (
                        <p className="text-[11px] text-[var(--status-error)]">
                          {st.error}
                        </p>
                      )}
                    </div>
                  );
                })
              )}
            </div>

            {/* Latency Breakdown Table */}
            {resp?.latency && (
              <div className="rounded-lg border border-[var(--border-subtle)] bg-[var(--bg-surface)] p-3 space-y-2">
                <p className="text-[10px] font-mono-tech uppercase tracking-wider text-[var(--text-muted)]">
                  Latency Breakdown
                </p>
                <div className="space-y-1 text-xs font-mono-tech">
                  {(
                    [
                      ["Query analysis", resp.latency.query_processing_ms],
                      ["Retrieval", resp.latency.retrieval_ms],
                      ["Reranking", resp.latency.reranking_ms],
                      ["Generation", resp.latency.generation_ms],
                      ["Guardrails", resp.latency.guardrail_ms],
                      ["End-to-end Total", resp.latency.total_ms],
                    ] as const
                  )
                    .filter(([, val]) => val !== undefined && val !== null)
                    .map(([label, val]) => (
                      <div key={label} className="flex justify-between">
                        <span className="text-[var(--text-secondary)]">{label}</span>
                        <span className="text-[var(--text-primary)]">
                          {(val as number).toFixed(2)} ms
                        </span>
                      </div>
                    ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </aside>
  );
}

