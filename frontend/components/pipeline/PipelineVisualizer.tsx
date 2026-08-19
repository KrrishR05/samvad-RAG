"use client";

import type { PipelineStageInfo } from "@/types/pipeline";
import type { StageStatus } from "@/types/api";

interface PipelineVisualizerProps {
  stages: PipelineStageInfo[];
}

function StageIcon({ status }: { status: StageStatus }) {
  switch (status) {
    case "completed":
      return (
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" className="text-success">
          <polyline points="20 6 9 17 4 12" />
        </svg>
      );
    case "active":
      return (
        <div className="w-3 h-3 rounded-full bg-accent animate-pulse" />
      );
    case "error":
      return (
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" className="text-error">
          <line x1="18" y1="6" x2="6" y2="18" />
          <line x1="6" y1="6" x2="18" y2="18" />
        </svg>
      );
    case "abstained":
      return (
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" className="text-abstained">
          <line x1="5" y1="12" x2="19" y2="12" />
        </svg>
      );
    case "skipped":
      return (
        <div className="w-3 h-3 rounded-full border border-text-muted/40" />
      );
    default: // pending
      return (
        <div className="w-3 h-3 rounded-full border border-border-default" />
      );
  }
}

export default function PipelineVisualizer({
  stages,
}: PipelineVisualizerProps) {
  return (
    <div className="rounded-xl border border-border-subtle bg-bg-surface/50 p-5">
      <h3 className="text-[10px] font-mono font-semibold text-text-muted uppercase tracking-[0.2em] mb-4">
        Pipeline
      </h3>
      <div className="space-y-1">
        {stages.map((stage, i) => (
          <div key={stage.id} className="flex items-center gap-3 group">
            {/* Connector line */}
            <div className="flex flex-col items-center w-5">
              <div className="flex items-center justify-center w-5 h-5">
                <StageIcon status={stage.status} />
              </div>
              {i < stages.length - 1 && (
                <div
                  className={`w-px h-4 ${
                    stage.status === "completed"
                      ? "bg-success/30"
                      : "bg-border-subtle"
                  }`}
                />
              )}
            </div>
            {/* Label */}
            <div className="flex-1 flex items-center justify-between py-1">
              <span
                className={`text-xs transition-colors ${
                  stage.status === "active"
                    ? "text-accent font-medium"
                    : stage.status === "completed"
                    ? "text-text-primary"
                    : stage.status === "error"
                    ? "text-error"
                    : "text-text-muted"
                }`}
              >
                {stage.label}
              </span>
              {stage.durationMs != null && (
                <span className="text-[10px] font-mono text-text-muted">
                  {stage.durationMs.toFixed(0)}ms
                </span>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
