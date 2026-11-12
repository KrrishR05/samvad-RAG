"use client";

import React, { useEffect, useState } from "react";
import { getPipelineStatus, healthCheck } from "@/lib/api/client";
import type {
  HealthResponse,
  PipelineStatusResponse,
  RetrieverStrategy,
} from "@/types/api";
import { AppShell } from "@/components/layout/AppShell";
import { useTheme } from "@/components/layout/ThemeProvider";

const PREFS_KEY = "samvad_workbench_prefs_v1";

export default function SettingsPage() {
  const { theme, setTheme } = useTheme();
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [status, setStatus] = useState<PipelineStatusResponse | null>(null);
  const [defaultStrategy, setDefaultStrategy] =
    useState<RetrieverStrategy>("hybrid");
  const [autoOpenInspector, setAutoOpenInspector] = useState(true);
  const [savedNotice, setSavedNotice] = useState(false);

  useEffect(() => {
    Promise.allSettled([healthCheck(), getPipelineStatus()]).then(
      ([h, p]) => {
        if (h.status === "fulfilled") setHealth(h.value);
        if (p.status === "fulfilled") setStatus(p.value);
      }
    );

    const id = window.setTimeout(() => {
      try {
        const raw = window.localStorage.getItem(PREFS_KEY);
        if (raw) {
          const parsed = JSON.parse(raw);
          if (
            parsed?.defaultStrategy === "hybrid" ||
            parsed?.defaultStrategy === "dense" ||
            parsed?.defaultStrategy === "lexical"
          ) {
            setDefaultStrategy(parsed.defaultStrategy);
          }
          if (typeof parsed?.autoOpenInspector === "boolean") {
            setAutoOpenInspector(parsed.autoOpenInspector);
          }
        }
      } catch {
        // Ignore storage errors
      }
    }, 0);
    return () => window.clearTimeout(id);
  }, []);

  const savePrefs = (
    nextStrategy: RetrieverStrategy,
    nextAutoOpen: boolean
  ) => {
    setDefaultStrategy(nextStrategy);
    setAutoOpenInspector(nextAutoOpen);
    try {
      window.localStorage.setItem(
        PREFS_KEY,
        JSON.stringify({
          defaultStrategy: nextStrategy,
          autoOpenInspector: nextAutoOpen,
        })
      );
      setSavedNotice(true);
      setTimeout(() => setSavedNotice(false), 1500);
    } catch {
      // Ignore
    }
  };

  return (
    <AppShell pageTitle="Settings & Environment" pipelineStatus={status}>
      <main className="flex-1 overflow-y-auto px-4 sm:px-8 py-6">
        <div className="max-w-3xl mx-auto space-y-6">
          <div>
            <h2 className="font-display font-semibold text-xl text-[var(--text-primary)]">
              Workbench Preferences & Backend Diagnostics
            </h2>
            <p className="text-sm text-[var(--text-secondary)] mt-1">
              Configure local interface defaults and inspect live backend environment capabilities.
            </p>
          </div>

          {/* Local UI Preferences */}
          <section className="rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-panel)] p-5 space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-xs font-mono-tech uppercase tracking-wider text-[var(--text-muted)]">
                Interface Preferences (Browser Local)
              </h3>
              {savedNotice && (
                <span className="text-[11px] font-mono-tech text-[var(--status-success)]">
                  Saved
                </span>
              )}
            </div>

            <div className="flex items-center justify-between gap-4 py-2 border-b border-[var(--border-subtle)]">
              <div>
                <p className="text-sm font-medium text-[var(--text-primary)]">
                  Color Theme
                </p>
                <p className="text-xs text-[var(--text-muted)]">
                  Switch between dark research terminal and warm stone light mode.
                </p>
              </div>
              <div className="inline-flex rounded-md bg-[var(--bg-surface)] border border-[var(--border-subtle)] p-0.5">
                {(["dark", "light"] as const).map((mode) => (
                  <button
                    key={mode}
                    type="button"
                    onClick={() => setTheme(mode)}
                    className={`px-3 py-1 rounded text-xs font-medium capitalize transition-colors cursor-pointer ${
                      theme === mode
                        ? "bg-[var(--accent)] text-white"
                        : "text-[var(--text-secondary)] hover:text-[var(--text-primary)]"
                    }`}
                  >
                    {mode}
                  </button>
                ))}
              </div>
            </div>

            <div className="flex items-center justify-between gap-4 py-2 border-b border-[var(--border-subtle)]">
              <div>
                <p className="text-sm font-medium text-[var(--text-primary)]">
                  Default Retrieval Strategy
                </p>
                <p className="text-xs text-[var(--text-muted)]">
                  Initial retrieval mode selected in the Research Workspace composer.
                </p>
              </div>
              <select
                value={defaultStrategy}
                onChange={(e) =>
                  savePrefs(
                    e.target.value as RetrieverStrategy,
                    autoOpenInspector
                  )
                }
                className="px-3 py-1.5 rounded-md text-xs font-mono-tech bg-[var(--bg-surface)] text-[var(--text-primary)] border border-[var(--border-subtle)]"
              >
                <option value="hybrid">hybrid (RRF)</option>
                <option value="dense">dense</option>
                <option value="lexical">lexical (BM25)</option>
              </select>
            </div>

            <div className="flex items-center justify-between gap-4 pt-1">
              <div>
                <p className="text-sm font-medium text-[var(--text-primary)]">
                  Auto-Open Evidence Inspector
                </p>
                <p className="text-xs text-[var(--text-muted)]">
                  Open the right Evidence drawer automatically when passages are retrieved.
                </p>
              </div>
              <button
                type="button"
                onClick={() =>
                  savePrefs(defaultStrategy, !autoOpenInspector)
                }
                className={`px-3 py-1.5 rounded-md text-xs font-mono-tech border transition-colors cursor-pointer ${
                  autoOpenInspector
                    ? "bg-[var(--accent-soft)] border-[var(--accent-border)] text-[var(--accent)]"
                    : "bg-[var(--bg-surface)] border-[var(--border-subtle)] text-[var(--text-muted)]"
                }`}
              >
                {autoOpenInspector ? "enabled" : "disabled"}
              </button>
            </div>
          </section>

          {/* Live Backend Configuration Readout */}
          <section className="rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-panel)] p-5 space-y-3">
            <h3 className="text-xs font-mono-tech uppercase tracking-wider text-[var(--text-muted)]">
              Live Backend Runtime Diagnostics
            </h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs font-mono-tech">
              <div className="rounded-lg bg-[var(--bg-surface)] border border-[var(--border-subtle)] p-3 flex justify-between">
                <span className="text-[var(--text-muted)]">Service</span>
                <span className="text-[var(--text-primary)]">
                  {health ? `${health.service} v${health.version}` : "Unavailable"}
                </span>
              </div>
              <div className="rounded-lg bg-[var(--bg-surface)] border border-[var(--border-subtle)] p-3 flex justify-between">
                <span className="text-[var(--text-muted)]">Environment</span>
                <span className="text-[var(--text-primary)]">
                  {health?.environment ?? "—"}
                </span>
              </div>
              <div className="rounded-lg bg-[var(--bg-surface)] border border-[var(--border-subtle)] p-3 flex justify-between">
                <span className="text-[var(--text-muted)]">Embeddings</span>
                <span className="text-[var(--text-primary)]">
                  {status
                    ? `${status.embedding_provider} (${status.embedding_dimension}d)`
                    : "—"}
                </span>
              </div>
              <div className="rounded-lg bg-[var(--bg-surface)] border border-[var(--border-subtle)] p-3 flex justify-between">
                <span className="text-[var(--text-muted)]">LLM Generator</span>
                <span
                  className={
                    status?.llm_configured
                      ? "text-[var(--status-success)]"
                      : "text-[var(--status-warning)]"
                  }
                >
                  {status
                    ? status.llm_configured
                      ? `${status.llm_provider}:${status.llm_model}`
                      : "unconfigured"
                    : "—"}
                </span>
              </div>
            </div>
          </section>

          {/* Honest .env Configuration Instructions */}
          <section className="rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-panel)] p-5 space-y-3">
            <h3 className="text-xs font-mono-tech uppercase tracking-wider text-[var(--text-muted)]">
              Configuring an LLM Provider in backend/.env
            </h3>
            <p className="text-xs text-[var(--text-secondary)] leading-relaxed">
              SAMVAD never simulates or fabricates LLM completions. To enable full end-to-end grounded answer generation, create{" "}
              <code className="font-mono-tech px-1 py-0.5 rounded bg-[var(--bg-surface)] border border-[var(--border-subtle)]">
                backend/.env
              </code>{" "}
              with one of the provider blocks below and restart the backend server:
            </p>
            <pre className="rounded-lg bg-[var(--bg-surface)] border border-[var(--border-subtle)] p-3.5 text-[11px] font-mono-tech text-[var(--text-primary)] overflow-x-auto">
{`# Option A: Local Ollama (free, offline)
LLM_PROVIDER=ollama
LLM_BASE_URL=http://localhost:11434/v1
LLM_MODEL=llama3.2

# Option B: Google Gemini API
LLM_PROVIDER=gemini
LLM_MODEL=gemini-2.5-flash
LLM_API_KEY=your-gemini-api-key

# Option C: OpenAI / OpenAI-compatible API
LLM_PROVIDER=openai
LLM_MODEL=gpt-4o-mini
LLM_API_KEY=your-openai-api-key`}
            </pre>
          </section>
        </div>
      </main>
    </AppShell>
  );
}
