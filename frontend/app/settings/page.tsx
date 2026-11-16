"use client";

import React, { startTransition, Suspense, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { getPipelineStatus, healthCheck } from "@/lib/api/client";
import type {
  HealthResponse,
  PipelineStatusResponse,
  RetrieverStrategy,
} from "@/types/api";
import { AppShell } from "@/components/layout/AppShell";
import { useTheme } from "@/components/layout/ThemeProvider";
import { useAuth } from "@/context/AuthContext";

const PREFS_KEY = "samvad_workbench_prefs_v1";

type SettingsTab = "general" | "account" | "plan" | "diagnostics";

export default function SettingsPage() {
  return (
    <Suspense fallback={<div className="p-8 text-center text-xs">Loading settings...</div>}>
      <SettingsContent />
    </Suspense>
  );
}

function SettingsContent() {
  const { theme, setTheme } = useTheme();
  const { user, isAuthenticated, openAuthModal, logout, updateProfile } = useAuth();
  const searchParams = useSearchParams();

  const [activeTab, setActiveTab] = useState<SettingsTab>("general");
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [status, setStatus] = useState<PipelineStatusResponse | null>(null);
  const [defaultStrategy, setDefaultStrategy] = useState<RetrieverStrategy>("hybrid");
  const [autoOpenInspector, setAutoOpenInspector] = useState(true);
  const [savedNotice, setSavedNotice] = useState(false);

  // Edit profile state
  const [editName, setEditName] = useState(user?.name || "");
  const [nameSaved, setNameSaved] = useState(false);
  const [planSaved, setPlanSaved] = useState(false);

  useEffect(() => {
    const tabParam = searchParams.get("tab") as SettingsTab;
    if (tabParam && ["general", "account", "plan", "diagnostics"].includes(tabParam)) {
      startTransition(() => setActiveTab(tabParam));
    }
  }, [searchParams]);

  useEffect(() => {
    if (user?.name) {
      startTransition(() => setEditName(user.name));
    }
  }, [user]);

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

  const handleSaveName = async () => {
    if (!editName.trim() || !user) return;
    await updateProfile({ name: editName.trim() });
    setNameSaved(true);
    setTimeout(() => setNameSaved(false), 2000);
  };

  const handleTogglePlan = async (targetPlan: "free" | "pro") => {
    if (!user) {
      openAuthModal("signup");
      return;
    }
    await updateProfile({ plan: targetPlan });
    setPlanSaved(true);
    setTimeout(() => setPlanSaved(false), 2000);
  };

  const getInitials = (name: string) => {
    const parts = name.trim().split(" ");
    if (parts.length >= 2) return (parts[0][0] + parts[1][0]).toUpperCase();
    return name.slice(0, 2).toUpperCase();
  };

  return (
    <AppShell pageTitle="Settings & Preferences" pipelineStatus={status}>
      <main className="flex-1 overflow-y-auto px-4 sm:px-8 py-6">
        <div className="max-w-3xl mx-auto space-y-6">
          {/* Header Title */}
          <div>
            <h2 className="font-display font-semibold text-xl text-[var(--text-primary)]">
              SAMVAD Settings
            </h2>
            <p className="text-sm text-[var(--text-secondary)] mt-1">
              Manage your personal account, research preferences, subscription tier, and system diagnostics.
            </p>
          </div>

          {/* Settings Tabs (ChatGPT & Gemini style) */}
          <div className="flex items-center gap-1.5 border-b border-[var(--border-subtle)] pb-2 overflow-x-auto">
            <button
              type="button"
              onClick={() => setActiveTab("general")}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors cursor-pointer shrink-0 ${
                activeTab === "general"
                  ? "bg-[var(--accent-soft)] text-[var(--accent)] border border-[var(--accent-border)] font-semibold"
                  : "text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-hover)]"
              }`}
            >
              General & UI
            </button>
            <button
              type="button"
              onClick={() => setActiveTab("account")}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors cursor-pointer shrink-0 ${
                activeTab === "account"
                  ? "bg-[var(--accent-soft)] text-[var(--accent)] border border-[var(--accent-border)] font-semibold"
                  : "text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-hover)]"
              }`}
            >
              Account & Profile
            </button>
            <button
              type="button"
              onClick={() => setActiveTab("plan")}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors cursor-pointer shrink-0 ${
                activeTab === "plan"
                  ? "bg-[var(--accent-soft)] text-[var(--accent)] border border-[var(--accent-border)] font-semibold"
                  : "text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-hover)]"
              }`}
            >
              Subscription & Plan
            </button>
            <button
              type="button"
              onClick={() => setActiveTab("diagnostics")}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors cursor-pointer shrink-0 ${
                activeTab === "diagnostics"
                  ? "bg-[var(--accent-soft)] text-[var(--accent)] border border-[var(--accent-border)] font-semibold"
                  : "text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-hover)]"
              }`}
            >
              Backend & Models
            </button>
          </div>

          {/* TAB 1: GENERAL & UI */}
          {activeTab === "general" && (
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
                          ? "bg-[var(--accent)] text-white font-semibold shadow-xs"
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
                  className="px-3 py-1.5 rounded-md text-xs font-mono-tech bg-[var(--bg-surface)] text-[var(--text-primary)] border border-[var(--border-subtle)] focus:outline-none"
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
          )}

          {/* TAB 2: ACCOUNT & PROFILE */}
          {activeTab === "account" && (
            <div className="space-y-5">
              {/* Profile Card */}
              <section className="rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-panel)] p-5 space-y-4">
                <div className="flex items-center justify-between">
                  <h3 className="text-xs font-mono-tech uppercase tracking-wider text-[var(--text-muted)]">
                    Personal Account
                  </h3>
                  {nameSaved && (
                    <span className="text-[11px] font-mono-tech text-[var(--status-success)]">
                      Name updated!
                    </span>
                  )}
                </div>

                {user ? (
                  <div className="space-y-4">
                    {/* Avatar & Identifiers */}
                    <div className="flex items-center gap-4 pb-4 border-b border-[var(--border-subtle)]">
                      <div className="w-14 h-14 rounded-full bg-gradient-to-tr from-[#EA4335] via-[#FBBC05] to-[#8b5cf6] flex items-center justify-center text-white font-bold text-lg shadow-md shrink-0">
                        {getInitials(user.name)}
                      </div>
                      <div className="min-w-0 flex-1">
                        <div className="flex items-center gap-2">
                          <span className="font-semibold text-base text-[var(--text-primary)]">
                            {user.name}
                          </span>
                          <span className="px-2 py-0.5 rounded-full text-[10px] font-mono-tech uppercase tracking-wider bg-[var(--accent-soft)] text-[var(--accent)] border border-[var(--accent-border)]">
                            {user.plan === "pro" ? "Pro" : "Free"}
                          </span>
                        </div>
                        <div className="text-xs text-[var(--text-muted)] mt-0.5 truncate">
                          {user.email}
                        </div>
                        <div className="text-[10.5px] font-mono-tech text-[var(--text-secondary)] mt-1">
                          Auth: {user.provider === "google" ? "Google OAuth" : "Email / Password"} · ID: {user.id}
                        </div>
                      </div>
                    </div>

                    {/* Edit Name Form */}
                    <div className="space-y-2">
                      <label className="block text-xs font-medium text-[var(--text-secondary)]">
                        Display Name
                      </label>
                      <div className="flex items-center gap-3">
                        <input
                          type="text"
                          value={editName}
                          onChange={(e) => setEditName(e.target.value)}
                          className="max-w-md flex-1 text-xs px-3 py-2 rounded-xl bg-[var(--bg-surface)] border border-[var(--border-subtle)] text-[var(--text-primary)] focus:border-[var(--accent)] focus:outline-none"
                          placeholder="Your Name"
                        />
                        <button
                          type="button"
                          onClick={handleSaveName}
                          disabled={!editName.trim() || editName === user.name}
                          className="px-4 py-2 rounded-xl text-xs font-semibold bg-[var(--accent)] hover:opacity-95 text-white transition-opacity disabled:opacity-40 cursor-pointer shadow-sm"
                        >
                          Save Changes
                        </button>
                      </div>
                    </div>

                    {/* Connected Accounts */}
                    <div className="pt-2 border-t border-[var(--border-subtle)]">
                      <p className="text-xs font-medium text-[var(--text-secondary)] mb-2">
                        Connected Authentication Providers
                      </p>
                      <div className="p-3 rounded-xl bg-[var(--bg-surface)] border border-[var(--border-subtle)] flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <div className="w-7 h-7 rounded-lg bg-[var(--bg-panel)] flex items-center justify-center border border-[var(--border-subtle)]">
                            <GoogleMiniIcon className="w-4 h-4" />
                          </div>
                          <div>
                            <span className="text-xs font-medium text-[var(--text-primary)] block">
                              Google Account
                            </span>
                            <span className="text-[11px] text-[var(--text-muted)]">
                              {user.provider === "google" ? user.email : "Not linked as primary Google account"}
                            </span>
                          </div>
                        </div>
                        <span className={`text-[10.5px] font-mono-tech px-2 py-0.5 rounded ${
                          user.provider === "google"
                            ? "bg-[var(--status-success)]/10 text-[var(--status-success)] border border-[var(--status-success)]/30"
                            : "bg-[var(--bg-panel)] text-[var(--text-muted)] border border-[var(--border-subtle)]"
                        }`}>
                          {user.provider === "google" ? "Connected" : "Optional"}
                        </span>
                      </div>
                    </div>

                    {/* Sign Out & Switch */}
                    <div className="pt-2 flex items-center justify-between">
                      <button
                        type="button"
                        onClick={() => openAuthModal("login")}
                        className="text-xs text-[var(--accent)] hover:underline font-medium cursor-pointer"
                      >
                        Switch Account / Sign In with Another Email &rarr;
                      </button>

                      <button
                        type="button"
                        onClick={logout}
                        className="px-3 py-1.5 rounded-lg text-xs font-medium text-[var(--status-error)] hover:bg-[var(--status-error)]/10 border border-[var(--status-error)]/30 transition-colors cursor-pointer"
                      >
                        Sign Out
                      </button>
                    </div>
                  </div>
                ) : (
                  <div className="text-center py-6 space-y-3">
                    <p className="text-xs text-[var(--text-secondary)]">
                      You are currently browsing in guest mode. Sign in to save research history across devices.
                    </p>
                    <button
                      type="button"
                      onClick={() => openAuthModal("login")}
                      className="px-4 py-2 rounded-xl text-xs font-semibold bg-[var(--accent)] text-white hover:opacity-95 shadow-sm cursor-pointer"
                    >
                      Sign In or Create Account
                    </button>
                  </div>
                )}
              </section>
            </div>
          )}

          {/* TAB 3: SUBSCRIPTION & PLAN */}
          {activeTab === "plan" && (
            <div className="space-y-5">
              <section className="rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-panel)] p-5 space-y-4">
                <div className="flex items-center justify-between">
                  <h3 className="text-xs font-mono-tech uppercase tracking-wider text-[var(--text-muted)]">
                    Available Research Plans
                  </h3>
                  {planSaved && (
                    <span className="text-[11px] font-mono-tech text-[var(--status-success)]">
                      Plan updated!
                    </span>
                  )}
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {/* Free Plan */}
                  <div className={`p-5 rounded-2xl border transition-all flex flex-col justify-between ${
                    user?.plan !== "pro"
                      ? "border-[var(--accent)] bg-[var(--accent-soft)]/20 shadow-md"
                      : "border-[var(--border-subtle)] bg-[var(--bg-surface)] opacity-80"
                  }`}>
                    <div>
                      <div className="flex items-center justify-between mb-2">
                        <span className="font-display font-bold text-base text-[var(--text-primary)]">
                          SAMVAD Free
                        </span>
                        {user?.plan !== "pro" && (
                          <span className="text-[10px] font-mono-tech px-2 py-0.5 rounded-full bg-[var(--accent)] text-white font-semibold">
                            CURRENT
                          </span>
                        )}
                      </div>
                      <div className="text-2xl font-bold font-display text-[var(--text-primary)] mb-3">
                        $0 <span className="text-xs font-normal text-[var(--text-muted)]">/ forever</span>
                      </div>
                      <ul className="text-xs text-[var(--text-secondary)] space-y-2 mb-4">
                        <li className="flex items-center gap-2">✓ 1,500 daily requests (Gemini 3.5 Flash Lite)</li>
                        <li className="flex items-center gap-2">✓ Native Indic Voice STT/TTS (Sarvam AI)</li>
                        <li className="flex items-center gap-2">✓ Hybrid RRF (BM25 + Dense vector search)</li>
                        <li className="flex items-center gap-2">✓ Transparent clickable evidence citations</li>
                        <li className="flex items-center gap-2">✓ Standard document ingestion</li>
                      </ul>
                    </div>

                    <button
                      type="button"
                      disabled={user?.plan !== "pro"}
                      onClick={() => handleTogglePlan("free")}
                      className="w-full py-2 rounded-xl text-xs font-semibold border border-[var(--border-subtle)] bg-[var(--bg-panel)] text-[var(--text-primary)] hover:bg-[var(--bg-hover)] transition-colors disabled:opacity-40 cursor-pointer"
                    >
                      {user?.plan !== "pro" ? "Active Plan" : "Switch to Free"}
                    </button>
                  </div>

                  {/* Pro Plan */}
                  <div className={`p-5 rounded-2xl border transition-all flex flex-col justify-between ${
                    user?.plan === "pro"
                      ? "border-[var(--accent)] bg-[var(--accent-soft)]/20 shadow-md ring-1 ring-[var(--accent)]"
                      : "border-[var(--border-default)] bg-[var(--bg-surface)] hover:border-[var(--accent)]"
                  }`}>
                    <div>
                      <div className="flex items-center justify-between mb-2">
                        <span className="font-display font-bold text-base text-[var(--accent)] flex items-center gap-1.5">
                          <span>SAMVAD Pro</span>
                          <span className="text-xs">✦</span>
                        </span>
                        {user?.plan === "pro" && (
                          <span className="text-[10px] font-mono-tech px-2 py-0.5 rounded-full bg-[var(--status-success)] text-white font-semibold">
                            ACTIVE PRO
                          </span>
                        )}
                      </div>
                      <div className="text-2xl font-bold font-display text-[var(--text-primary)] mb-3">
                        $20 <span className="text-xs font-normal text-[var(--text-muted)]">/ month</span>
                      </div>
                      <ul className="text-xs text-[var(--text-secondary)] space-y-2 mb-4">
                        <li className="flex items-center gap-2 text-[var(--text-primary)] font-medium">✦ Everything in Free, plus:</li>
                        <li className="flex items-center gap-2">✓ Unlimited knowledge base documents</li>
                        <li className="flex items-center gap-2">✓ Deep multi-pass intensity reranking</li>
                        <li className="flex items-center gap-2">✓ Priority Sarvam Bulbul voice synthesis</li>
                        <li className="flex items-center gap-2">✓ Custom domain embeddings & SVD models</li>
                        <li className="flex items-center gap-2">✓ Workspace collaboration & multi-turn traces</li>
                      </ul>
                    </div>

                    <button
                      type="button"
                      onClick={() => handleTogglePlan("pro")}
                      className="w-full py-2 rounded-xl text-xs font-semibold bg-[var(--accent)] hover:opacity-95 text-white transition-opacity shadow-sm cursor-pointer"
                    >
                      {user?.plan === "pro" ? "Manage Pro Subscription" : "Upgrade to SAMVAD Pro"}
                    </button>
                  </div>
                </div>
              </section>
            </div>
          )}

          {/* TAB 4: BACKEND & MODELS */}
          {activeTab === "diagnostics" && (
            <div className="space-y-5">
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

# Option B: Google Gemini API (Currently Active: gemini-3.5-flash-lite)
LLM_PROVIDER=gemini
LLM_MODEL=gemini-3.5-flash-lite
LLM_API_KEY=your-gemini-api-key

# Option C: OpenAI / OpenAI-compatible API
LLM_PROVIDER=openai
LLM_MODEL=gpt-4o-mini
LLM_API_KEY=your-openai-api-key`}
                </pre>
              </section>
            </div>
          )}
        </div>
      </main>
    </AppShell>
  );
}

function GoogleMiniIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24">
      <path
        fill="#4285F4"
        d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
      />
      <path
        fill="#34A853"
        d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
      />
      <path
        fill="#FBBC05"
        d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z"
      />
      <path
        fill="#EA4335"
        d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z"
      />
    </svg>
  );
}
