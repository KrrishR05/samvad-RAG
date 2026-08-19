"use client";

import { useEffect, useState } from "react";
import Header from "@/components/layout/Header";
import LatencyCard from "@/components/analytics/LatencyCard";
import { getLatencyStats } from "@/lib/api/client";
import type { LatencyStatsResponse } from "@/types/api";

const STAGE_LABELS: Record<string, string> = {
  stt: "Speech-to-Text",
  query_processing: "Query Processing",
  embedding: "Embedding",
  retrieval: "Retrieval",
  reranking: "Reranking",
  generation: "Generation",
  guardrail: "Guardrails",
  total: "Total Pipeline",
};

export default function AnalyticsPage() {
  const [data, setData] = useState<LatencyStatsResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getLatencyStats()
      .then(setData)
      .catch((err) =>
        setError(err instanceof Error ? err.message : "Failed to load analytics")
      )
      .finally(() => setLoading(false));
  }, []);

  const hasData = data && data.total_records > 0;

  return (
    <div className="min-h-screen flex flex-col">
      <Header />

      <main className="flex-1 max-w-7xl w-full mx-auto px-6 py-8">
        {/* Page header */}
        <div className="mb-8 animate-fade-in">
          <h1 className="text-2xl font-bold tracking-tight text-text-primary">
            Analytics
          </h1>
          <p className="text-sm text-text-muted mt-1">
            Pipeline latency metrics and performance benchmarks
          </p>
        </div>

        {/* Loading */}
        {loading && (
          <div className="flex items-center gap-3 py-12 justify-center">
            <div className="w-4 h-4 rounded-full border-2 border-accent border-t-transparent animate-spin" />
            <span className="text-sm text-text-secondary">
              Loading analytics...
            </span>
          </div>
        )}

        {/* Error */}
        {error && (
          <div className="rounded-xl border border-error/20 bg-error/5 p-6 text-center animate-fade-in">
            <p className="text-sm text-error">{error}</p>
            <p className="text-xs text-text-muted mt-2">
              Make sure the backend is running on{" "}
              <code className="font-mono">localhost:8000</code>
            </p>
          </div>
        )}

        {/* Empty state */}
        {!loading && !error && !hasData && (
          <div className="rounded-xl border border-border-subtle bg-bg-surface/50 p-12 text-center animate-fade-in">
            <div className="w-16 h-16 rounded-2xl bg-bg-elevated border border-border-default flex items-center justify-center mx-auto mb-4">
              <svg
                width="24"
                height="24"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="1.5"
                strokeLinecap="round"
                strokeLinejoin="round"
                className="text-text-muted"
              >
                <path d="M3 3v18h18" />
                <path d="M18.7 8l-5.1 5.2-2.8-2.7L7 14.3" />
              </svg>
            </div>
            <h2 className="text-lg font-semibold text-text-primary mb-2">
              No Benchmark Data Available
            </h2>
            <p className="text-sm text-text-secondary max-w-md mx-auto mb-4">
              {data?.message ||
                "Run pipeline queries to collect latency metrics. Analytics will populate automatically once the RAG pipeline is connected and queries are processed."}
            </p>
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-bg-elevated border border-border-subtle">
              <span className="text-[10px] font-mono text-text-muted uppercase tracking-widest">
                Target: sub-200ms P70
              </span>
            </div>
          </div>
        )}

        {/* Data display */}
        {!loading && !error && hasData && (
          <div className="space-y-6 animate-slide-up">
            {/* Overall */}
            <LatencyCard label="Overall Latency" stats={data.overall} />

            {/* Per-stage */}
            <div>
              <h2 className="text-xs font-mono font-semibold text-text-muted uppercase tracking-[0.2em] mb-4">
                Stage Breakdown
              </h2>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                {data.by_stage &&
                  Object.entries(data.by_stage).map(([key, stats]) =>
                    stats ? (
                      <LatencyCard
                        key={key}
                        label={STAGE_LABELS[key] || key}
                        stats={stats}
                      />
                    ) : null
                  )}
              </div>
            </div>

            <div className="text-center pt-4">
              <span className="text-[10px] font-mono text-text-muted">
                {data.total_records} total recorded requests
              </span>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
