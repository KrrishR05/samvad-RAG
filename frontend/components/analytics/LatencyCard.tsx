"use client";

import type { PercentileStats } from "@/types/api";

interface LatencyCardProps {
  label: string;
  stats: PercentileStats | null | undefined;
}

export default function LatencyCard({ label, stats }: LatencyCardProps) {
  const hasData = stats && stats.count > 0;

  return (
    <div className="rounded-xl border border-border-subtle bg-bg-surface/50 p-5 animate-fade-in">
      <h3 className="text-[10px] font-mono font-semibold text-text-muted uppercase tracking-[0.2em] mb-4">
        {label}
      </h3>

      {!hasData ? (
        <p className="text-xs text-text-muted">No data available</p>
      ) : (
        <div className="space-y-3">
          {/* Main percentiles */}
          <div className="grid grid-cols-3 gap-3">
            <MetricBox label="P50" value={stats.p50} unit="ms" />
            <MetricBox label="P70" value={stats.p70} unit="ms" />
            <MetricBox label="P100" value={stats.p100} unit="ms" />
          </div>

          {/* Secondary stats */}
          <div className="flex items-center gap-4 pt-2 border-t border-border-subtle">
            <span className="text-[10px] font-mono text-text-muted">
              mean:{" "}
              <span className="text-text-secondary">
                {stats.mean?.toFixed(1)}ms
              </span>
            </span>
            <span className="text-[10px] font-mono text-text-muted">
              min:{" "}
              <span className="text-text-secondary">
                {stats.min?.toFixed(1)}ms
              </span>
            </span>
            <span className="text-[10px] font-mono text-text-muted">
              max:{" "}
              <span className="text-text-secondary">
                {stats.max?.toFixed(1)}ms
              </span>
            </span>
            <span className="text-[10px] font-mono text-text-muted">
              n={stats.count}
            </span>
          </div>
        </div>
      )}
    </div>
  );
}

function MetricBox({
  label,
  value,
  unit,
}: {
  label: string;
  value: number | null | undefined;
  unit: string;
}) {
  return (
    <div className="rounded-lg bg-bg-elevated/70 border border-border-subtle p-3 text-center">
      <div className="text-[10px] font-mono text-text-muted mb-1">{label}</div>
      <div className="text-lg font-semibold text-text-primary font-mono">
        {value != null ? value.toFixed(1) : "—"}
      </div>
      <div className="text-[10px] text-text-muted">{unit}</div>
    </div>
  );
}
