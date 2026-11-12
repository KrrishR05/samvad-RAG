"use client";

import React, { useCallback, useEffect, useState } from "react";
import { getAnalyticsSummary, getLatencyStats } from "@/lib/api/client";
import type {
  AnalyticsSummaryResponse,
  LatencyStatsResponse,
  PercentileStats,
} from "@/types/api";
import { AppShell } from "@/components/layout/AppShell";
import { RefreshIcon } from "@/components/ui/Icons";

function StatBox({
  label,
  value,
  sub,
}: {
  label: string;
  value: string;
  sub?: string;
}) {
  return (
    <div className="rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-panel)] p-4">
      <p className="text-[11px] font-mono-tech uppercase tracking-wider text-[var(--text-muted)]">
        {label}
      </p>
      <p className="mt-1.5 font-mono-tech text-2xl font-medium text-[var(--text-primary)]">
        {value}
      </p>
      {sub && (
        <p className="mt-1 text-xs text-[var(--text-muted)]">{sub}</p>
      )}
    </div>
  );
}

export default function AnalyticsPage() {
  const [summary, setSummary] = useState<AnalyticsSummaryResponse | null>(null);
  const [latency, setLatency] = useState<LatencyStatsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadAnalytics = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [sum, lat] = await Promise.all([
        getAnalyticsSummary(),
        getLatencyStats(),
      ]);
      setSummary(sum);
      setLatency(lat);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to fetch analytics telemetry."
      );
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    let active = true;
    Promise.all([getAnalyticsSummary(), getLatencyStats()])
      .then(([sum, lat]) => {
        if (!active) return;
        setSummary(sum);
        setLatency(lat);
      })
      .catch((err) => {
        if (!active) return;
        setError(
          err instanceof Error
            ? err.message
            : "Failed to fetch analytics telemetry."
        );
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, []);

  const stageEntries: { key: string; label: string; stats?: PercentileStats }[] =
    latency?.by_stage
      ? [
          {
            key: "query_processing",
            label: "Query Analysis",
            stats: latency.by_stage.query_processing,
          },
          {
            key: "retrieval",
            label: "Retrieval (BM25 / Dense / Hybrid)",
            stats: latency.by_stage.retrieval,
          },
          {
            key: "reranking",
            label: "Reranking",
            stats: latency.by_stage.reranking,
          },
          {
            key: "generation",
            label: "LLM Generation",
            stats: latency.by_stage.generation,
          },
          {
            key: "guardrail",
            label: "Guardrail Checks",
            stats: latency.by_stage.guardrail,
          },
          {
            key: "total",
            label: "End-to-End Total",
            stats: latency.by_stage.total,
          },
        ].filter((item) => item.stats && item.stats.count > 0)
      : [];

  return (
    <AppShell
      pageTitle="Pipeline Telemetry & Latency Analytics"
      headerActions={
        <button
          type="button"
          onClick={loadAnalytics}
          disabled={loading}
          className="inline-flex items-center gap-1.5 px-2.5 py-1.5 rounded-md text-xs font-medium bg-[var(--bg-surface)] text-[var(--text-secondary)] border border-[var(--border-subtle)] hover:text-[var(--text-primary)] transition-colors cursor-pointer"
        >
          <RefreshIcon className={loading ? "animate-spin" : ""} />
          <span>Refresh</span>
        </button>
      }
    >
      <main className="flex-1 overflow-y-auto px-4 sm:px-8 py-6">
        <div className="max-w-5xl mx-auto space-y-6">
          <div>
            <h2 className="font-display font-semibold text-xl text-[var(--text-primary)]">
              Real-Time Pipeline Analytics
            </h2>
            <p className="text-sm text-[var(--text-secondary)] mt-1">
              Exact latency percentiles recorded by the backend{" "}
              <code className="font-mono-tech text-xs px-1 py-0.5 rounded bg-[var(--bg-surface)] border border-[var(--border-subtle)]">
                MetricsStore
              </code>{" "}
              from completed and abstained query runs.
            </p>
          </div>

          {error && (
            <div className="rounded-lg border border-[var(--status-error)]/30 bg-[var(--status-error-soft)] p-3 text-xs text-[var(--status-error)]">
              {error}
            </div>
          )}

          {/* Top KPI Row */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            <StatBox
              label="Total Recorded Requests"
              value={loading ? "..." : String(summary?.total_requests ?? 0)}
              sub="Current server session"
            />
            <StatBox
              label="Overall P50"
              value={
                latency?.overall?.p50 != null
                  ? `${latency.overall.p50.toFixed(1)} ms`
                  : "—"
              }
              sub="Median end-to-end"
            />
            <StatBox
              label="Overall P70"
              value={
                latency?.overall?.p70 != null
                  ? `${latency.overall.p70.toFixed(1)} ms`
                  : "—"
              }
              sub="70th percentile"
            />
            <StatBox
              label="Overall P100"
              value={
                latency?.overall?.p100 != null
                  ? `${latency.overall.p100.toFixed(1)} ms`
                  : "—"
              }
              sub="Observed max latency"
            />
          </div>

          {/* Stage Breakdown */}
          <section className="rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-panel)] overflow-hidden">
            <div className="px-5 py-3.5 border-b border-[var(--border-subtle)] flex items-center justify-between">
              <h3 className="text-xs font-mono-tech uppercase tracking-wider text-[var(--text-muted)]">
                Per-Stage Latency Percentiles (ms)
              </h3>
              <span className="text-[11px] font-mono-tech text-[var(--text-muted)]">
                Zero synthetic data
              </span>
            </div>

            {stageEntries.length === 0 ? (
              <div className="p-10 text-center space-y-1.5">
                <p className="text-sm font-medium text-[var(--text-secondary)]">
                  No pipeline requests recorded yet
                </p>
                <p className="text-xs text-[var(--text-muted)]">
                  {summary?.message ||
                    "Submit queries from the Workspace once an LLM generator is configured to populate stage-level telemetry."}
                </p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse text-xs">
                  <thead>
                    <tr className="border-b border-[var(--border-subtle)] text-[11px] font-mono-tech text-[var(--text-muted)] bg-[var(--bg-surface)]/60">
                      <th className="py-2.5 px-4 font-medium">Stage</th>
                      <th className="py-2.5 px-4 font-medium">Count</th>
                      <th className="py-2.5 px-4 font-medium">P50</th>
                      <th className="py-2.5 px-4 font-medium">P70</th>
                      <th className="py-2.5 px-4 font-medium">P100</th>
                      <th className="py-2.5 px-4 font-medium">Mean</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[var(--border-subtle)] font-mono-tech">
                    {stageEntries.map(({ key, label, stats }) => (
                      <tr key={key} className="hover:bg-[var(--bg-surface)]/40">
                        <td className="py-3 px-4 font-sans font-medium text-[var(--text-primary)]">
                          {label}
                        </td>
                        <td className="py-3 px-4 text-[var(--text-secondary)]">
                          {stats?.count ?? 0}
                        </td>
                        <td className="py-3 px-4 text-[var(--text-primary)]">
                          {stats?.p50?.toFixed(2) ?? "—"}
                        </td>
                        <td className="py-3 px-4 text-[var(--text-primary)]">
                          {stats?.p70?.toFixed(2) ?? "—"}
                        </td>
                        <td className="py-3 px-4 text-[var(--text-primary)]">
                          {stats?.p100?.toFixed(2) ?? "—"}
                        </td>
                        <td className="py-3 px-4 text-[var(--text-secondary)]">
                          {stats?.mean?.toFixed(2) ?? "—"}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </section>
        </div>
      </main>
    </AppShell>
  );
}
