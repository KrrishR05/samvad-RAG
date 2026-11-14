"use client";

import React, { useCallback, useEffect, useMemo, useRef, useState } from "react";
import Link from "next/link";
import {
  getPipelineStatus,
  submitTextQuery,
  submitVoiceQuery,
} from "@/lib/api/client";
import type { PipelineStatusResponse, RetrieverStrategy } from "@/types/api";
import { AppShell, type SidebarSessionItem } from "@/components/layout/AppShell";
import { QueryComposer } from "@/components/workspace/QueryComposer";
import {
  ResearchMessage,
  type ResearchTurn,
} from "@/components/workspace/ResearchMessage";
import { InspectorDrawer } from "@/components/workspace/InspectorDrawer";
import {
  DocumentsIcon,
  InspectorToggleIcon,
  SamvadLogo,
  SettingsIcon,
} from "@/components/ui/Icons";

interface ResearchSession {
  id: string;
  title: string;
  createdAt: string;
  updatedAt: string;
  turns: ResearchTurn[];
}

const SESSIONS_KEY = "samvad_sessions_v1";
const PREFS_KEY = "samvad_workbench_prefs_v1";

const STARTER_PROMPTS = [
  "Summarize the key claims across my indexed documents with citations.",
  "Compare multilingual passages mentioning technology and public infrastructure.",
  "What gaps or limitations exist in the currently indexed corpus?",
];

function createEmptySession(): ResearchSession {
  const now = new Date().toISOString();
  return {
    id: `sess-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`,
    title: "New Research Session",
    createdAt: now,
    updatedAt: now,
    turns: [],
  };
}

export default function ResearchWorkspacePage() {
  const [sessions, setSessions] = useState<ResearchSession[]>([]);
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
  const [sessionsHydrated, setSessionsHydrated] = useState(false);

  const [pipelineStatus, setPipelineStatus] =
    useState<PipelineStatusResponse | null>(null);
  const [inspectorOpen, setInspectorOpen] = useState(false);
  const [inspectedTurnId, setInspectedTurnId] = useState<string | null>(null);
  const [inspectorTab, setInspectorTab] = useState<"evidence" | "pipeline">(
    "evidence"
  );
  const [selectedSourceIdx, setSelectedSourceIdx] = useState<number | null>(
    null
  );
  const [composerQuery, setComposerQuery] = useState("");
  const [defaultStrategy, setDefaultStrategy] =
    useState<RetrieverStrategy>("hybrid");
  const [autoOpenInspector, setAutoOpenInspector] = useState(true);

  const threadEndRef = useRef<HTMLDivElement>(null);

  // Load saved local sessions + preferences asynchronously after hydration
  useEffect(() => {
    const id = window.setTimeout(() => {
      try {
        const rawPrefs = window.localStorage.getItem(PREFS_KEY);
        if (rawPrefs) {
          const parsed = JSON.parse(rawPrefs);
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
        // Ignore malformed local prefs
      }

      try {
        const raw = window.localStorage.getItem(SESSIONS_KEY);
        if (raw) {
          const parsed = JSON.parse(raw) as ResearchSession[];
          if (Array.isArray(parsed) && parsed.length > 0) {
            setSessions(parsed);
            setActiveSessionId(parsed[0].id);
            setSessionsHydrated(true);
            return;
          }
        }
      } catch {
        // Fall back to fresh session
      }
      const fresh = createEmptySession();
      setSessions([fresh]);
      setActiveSessionId(fresh.id);
      setSessionsHydrated(true);
    }, 0);
    return () => window.clearTimeout(id);
  }, []);

  // Persist local sessions
  useEffect(() => {
    if (!sessionsHydrated) return;
    try {
      const cleanSessions = sessions.map((s) => ({
        ...s,
        turns: s.turns.map((t) => ({ ...t, isLoading: false })),
      }));
      window.localStorage.setItem(SESSIONS_KEY, JSON.stringify(cleanSessions));
    } catch {
      // Ignore storage quota issues
    }
  }, [sessions, sessionsHydrated]);

  // Fetch live backend capabilities
  useEffect(() => {
    getPipelineStatus()
      .then(setPipelineStatus)
      .catch(() => setPipelineStatus(null));
  }, []);

  const activeSession = useMemo(
    () => sessions.find((s) => s.id === activeSessionId) ?? sessions[0] ?? null,
    [sessions, activeSessionId]
  );

  const inspectedTurn = useMemo(() => {
    if (!activeSession) return null;
    if (inspectedTurnId) {
      const found = activeSession.turns.find((t) => t.id === inspectedTurnId);
      if (found) return found;
    }
    return activeSession.turns[activeSession.turns.length - 1] ?? null;
  }, [activeSession, inspectedTurnId]);

  const isAnyLoading = Boolean(
    activeSession?.turns.some((t) => t.isLoading)
  );

  const handleNewSession = useCallback(() => {
    const fresh = createEmptySession();
    setSessions((prev) => [fresh, ...prev]);
    setActiveSessionId(fresh.id);
    setInspectedTurnId(null);
    setSelectedSourceIdx(null);
  }, []);

  const handleSelectSession = useCallback((id: string) => {
    setActiveSessionId(id);
    setInspectedTurnId(null);
    setSelectedSourceIdx(null);
  }, []);

  const handleDeleteSession = useCallback(
    (id: string) => {
      setSessions((prev) => {
        const remaining = prev.filter((s) => s.id !== id);
        if (remaining.length === 0) {
          const fresh = createEmptySession();
          setActiveSessionId(fresh.id);
          return [fresh];
        }
        if (activeSessionId === id) {
          setActiveSessionId(remaining[0].id);
        }
        return remaining;
      });
    },
    [activeSessionId]
  );

  const handleInspectTurn = useCallback(
    (turnId: string, tab: "evidence" | "pipeline" = "evidence", sourceIdx?: number) => {
      setInspectedTurnId(turnId);
      setInspectorTab(tab);
      setSelectedSourceIdx(sourceIdx ?? null);
      setInspectorOpen(true);
    },
    []
  );

  const updateTurnInSession = useCallback(
    (sessionId: string, turnId: string, patch: Partial<ResearchTurn>) => {
      setSessions((prev) =>
        prev.map((sess) =>
          sess.id !== sessionId
            ? sess
            : {
              ...sess,
              updatedAt: new Date().toISOString(),
              turns: sess.turns.map((t) =>
                t.id === turnId ? { ...t, ...patch } : t
              ),
            }
        )
      );
    },
    []
  );

  const handleSubmitText = useCallback(
    async ({
      query,
      language,
      strategy,
      topK,
    }: {
      query: string;
      language?: string;
      strategy: RetrieverStrategy;
      topK: number;
    }) => {
      if (!activeSession) return;
      const sessionId = activeSession.id;
      const turnId = `turn-${Date.now()}-${Math.random().toString(36).slice(2, 6)}`;
      const now = new Date().toISOString();

      const pendingTurn: ResearchTurn = {
        id: turnId,
        query,
        kind: "text",
        language,
        strategy,
        createdAt: now,
        isLoading: true,
      };

      setSessions((prev) =>
        prev.map((sess) =>
          sess.id !== sessionId
            ? sess
            : {
              ...sess,
              title:
                sess.turns.length === 0
                  ? query.slice(0, 48) + (query.length > 48 ? "..." : "")
                  : sess.title,
              updatedAt: now,
              turns: [...sess.turns, pendingTurn],
            }
        )
      );
      setInspectedTurnId(turnId);
      setSelectedSourceIdx(null);

      setTimeout(() => {
        threadEndRef.current?.scrollIntoView({ behavior: "smooth" });
      }, 60);

      try {
        const res = await submitTextQuery({
          query,
          language,
          retriever_strategy: strategy,
          top_k: topK,
        });
        updateTurnInSession(sessionId, turnId, {
          response: res,
          isLoading: false,
        });
        if (autoOpenInspector && res.sources.length > 0) {
          setInspectorTab("evidence");
          setInspectorOpen(true);
        }
      } catch (err) {
        updateTurnInSession(sessionId, turnId, {
          error:
            err instanceof Error
              ? err.message
              : "Failed to reach SAMVAD backend API.",
          isLoading: false,
        });
      }
    },
    [activeSession, autoOpenInspector, updateTurnInSession]
  );

  const handleSubmitVoice = useCallback(
    async (
      blob: Blob,
      language?: string,
      strategy?: RetrieverStrategy,
      topK?: number
    ) => {
      if (!activeSession) return;
      const sessionId = activeSession.id;
      const turnId = `turn-${Date.now()}-${Math.random().toString(36).slice(2, 6)}`;
      const now = new Date().toISOString();
      const effectiveStrategy = strategy ?? defaultStrategy;

      const pendingTurn: ResearchTurn = {
        id: turnId,
        query: "Voice audio recording submitted",
        kind: "voice",
        language,
        strategy: effectiveStrategy,
        createdAt: now,
        isLoading: true,
      };

      setSessions((prev) =>
        prev.map((sess) =>
          sess.id !== sessionId
            ? sess
            : {
              ...sess,
              title:
                sess.turns.length === 0 ? "Voice Research Query" : sess.title,
              updatedAt: now,
              turns: [...sess.turns, pendingTurn],
            }
        )
      );
      setInspectedTurnId(turnId);

      try {
        const res = await submitVoiceQuery(
          blob,
          undefined,
          language,
          effectiveStrategy,
          topK
        );
        updateTurnInSession(sessionId, turnId, {
          query: res.transcript || "Voice audio query",
          response: res,
          isLoading: false,
        });
        if (autoOpenInspector && res.sources.length > 0) {
          setInspectorTab("evidence");
          setInspectorOpen(true);
        }
      } catch (err) {
        updateTurnInSession(sessionId, turnId, {
          error:
            err instanceof Error
              ? err.message
              : "Failed to submit voice query.",
          isLoading: false,
        });
      }
    },
    [activeSession, autoOpenInspector, defaultStrategy, updateTurnInSession]
  );

  const sidebarSessions: SidebarSessionItem[] = useMemo(
    () =>
      sessions
        .filter((s) => s.turns.length > 0 || s.id === activeSession?.id)
        .map((s) => ({
          id: s.id,
          title: s.title,
          updatedAt: s.updatedAt,
          messageCount: s.turns.length,
        })),
    [sessions, activeSession?.id]
  );

  return (
    <AppShell
      pageTitle={activeSession?.title || "Research Workspace"}
      sessions={sidebarSessions}
      activeSessionId={activeSession?.id ?? null}
      onNewSession={handleNewSession}
      onSelectSession={handleSelectSession}
      onDeleteSession={handleDeleteSession}
      pipelineStatus={pipelineStatus}
      headerActions={
        <div className="flex items-center gap-2">
          {pipelineStatus && (
            <Link
              href="/documents"
              className="hidden sm:inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-mono-tech bg-[var(--bg-surface)] text-[var(--text-secondary)] border border-[var(--border-subtle)] hover:border-[var(--border-default)] transition-colors"
            >
              <span>{pipelineStatus.indexed_documents} docs</span>
              <span className="text-[var(--text-muted)]">/</span>
              <span>{pipelineStatus.indexed_chunks} chunks</span>
            </Link>
          )}
          <button
            type="button"
            onClick={() => setInspectorOpen((prev) => !prev)}
            className={`inline-flex items-center gap-1.5 px-2.5 py-1.5 rounded-md text-xs font-medium border transition-colors cursor-pointer ${inspectorOpen
                ? "bg-[var(--accent-soft)] border-[var(--accent-border)] text-[var(--text-primary)]"
                : "bg-[var(--bg-surface)] border-[var(--border-subtle)] text-[var(--text-secondary)] hover:text-[var(--text-primary)]"
              }`}
          >
            <InspectorToggleIcon className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">Inspector</span>
          </button>
        </div>
      }
    >
      {/* Center Research Column */}
      <div className="flex-1 min-w-0 flex flex-col h-full">
        <div className="flex-1 overflow-y-auto px-4 py-6">
          <div className="max-w-3xl mx-auto">
            {!activeSession || activeSession.turns.length === 0 ? (
              <div className="py-10 sm:py-16 space-y-8 samvad-welcome-bg rounded-2xl">
                {/* Editorial Welcome Header */}
                <div className="space-y-4">
                  <div className="inline-flex items-center gap-2.5 px-3 py-1.5 rounded-full bg-[var(--bg-panel)] border border-[var(--accent-border)]/40 text-[11px] font-mono-tech text-[var(--text-secondary)] shadow-xs" style={{boxShadow: '0 0 20px rgba(167,139,250,0.08)'}}>
                    <SamvadLogo className="w-4 h-4 shrink-0" />
                    <span>SAMVAD <span className="text-[var(--accent)] font-semibold">| संवाद</span> &mdash; Intelligence Through Evidence</span>
                  </div>
                  <h2 className="font-display font-semibold text-2xl sm:text-3xl tracking-tight text-[var(--text-primary)] leading-tight">
                    Evidence-grounded answers across <span className="text-[var(--accent)]">multilingual documents</span>.
                  </h2>
                  <p className="text-sm sm:text-[15px] text-[var(--text-secondary)] leading-relaxed max-w-2xl">
                    Query your knowledge base using hybrid Reciprocal Rank Fusion (BM25 + dense vector search), inspect retrieved source passages with clickable citations, and audit every pipeline stage in real time.
                  </p>
                </div>

                {/* Live Setup Check Banner (shown honestly only if needed) */}
                {pipelineStatus &&
                  (!pipelineStatus.retrieval_ready ||
                    !pipelineStatus.llm_configured) && (
                    <div className="rounded-xl border border-[var(--border-default)] bg-[var(--bg-panel)]/80 backdrop-blur-sm p-4 space-y-3">
                      <p className="text-xs font-mono-tech uppercase tracking-wider text-[var(--text-muted)]">
                        Workspace Readiness
                      </p>
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
                        <Link
                          href="/documents"
                          className="rounded-lg border border-[var(--border-subtle)] bg-[var(--bg-surface)] p-3 hover:border-[var(--accent-border)] transition-colors flex items-start gap-2.5"
                        >
                          <DocumentsIcon className="w-4 h-4 text-[var(--accent)] shrink-0 mt-0.5" />
                          <div>
                            <p className="font-medium text-[var(--text-primary)]">
                              {pipelineStatus.retrieval_ready
                                ? `${pipelineStatus.indexed_documents} Documents Indexed`
                                : "Upload Documents to Index"}
                            </p>
                            <p className="text-[var(--text-muted)] mt-0.5">
                              {pipelineStatus.retrieval_ready
                                ? `${pipelineStatus.indexed_chunks} searchable chunks ready.`
                                : "PDF, DOCX, Markdown, TXT, HTML, and JSON supported."}
                            </p>
                          </div>
                        </Link>

                        <Link
                          href="/settings"
                          className="rounded-lg border border-[var(--border-subtle)] bg-[var(--bg-surface)] p-3 hover:border-[var(--accent-border)] transition-colors flex items-start gap-2.5"
                        >
                          <SettingsIcon className="w-4 h-4 text-[var(--accent)] shrink-0 mt-0.5" />
                          <div>
                            <p className="font-medium text-[var(--text-primary)]">
                              {pipelineStatus.llm_configured
                                ? `LLM Connected (${pipelineStatus.llm_model})`
                                : "Configure LLM Generator"}
                            </p>
                            <p className="text-[var(--text-muted)] mt-0.5">
                              {pipelineStatus.llm_configured
                                ? `Provider: ${pipelineStatus.llm_provider}`
                                : "Add OpenAI, Ollama, or Gemini credentials in backend/.env."}
                            </p>
                          </div>
                        </Link>
                      </div>
                    </div>
                  )}

                {/* Starter Prompts */}
                <div className="space-y-2.5">
                  <p className="text-[11px] font-mono-tech uppercase tracking-wider text-[var(--text-muted)]">
                    Starter Queries
                  </p>
                  <div className="grid grid-cols-1 gap-2">
                    {STARTER_PROMPTS.map((prompt) => (
                      <button
                        key={prompt}
                        type="button"
                        onClick={() => setComposerQuery(prompt)}
                        className="samvad-prompt-card text-left px-4 py-3 rounded-lg text-[13px] text-[var(--text-secondary)] hover:text-[var(--text-primary)] cursor-pointer"
                      >
                        {prompt}
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            ) : (
              <div className="space-y-5">
                {activeSession.turns.map((turn) => (
                  <ResearchMessage
                    key={turn.id}
                    turn={turn}
                    isInspected={inspectedTurn?.id === turn.id}
                    onInspectTurn={handleInspectTurn}
                  />
                ))}
                <div ref={threadEndRef} />
              </div>
            )}
          </div>
        </div>

        {/* Query Composer */}
        <QueryComposer
          query={composerQuery}
          onQueryChange={setComposerQuery}
          onSubmitText={handleSubmitText}
          onSubmitVoice={handleSubmitVoice}
          disabled={isAnyLoading}
          defaultStrategy={defaultStrategy}
        />
      </div>

      {/* Right Evidence & Pipeline Inspector */}
      <InspectorDrawer
        open={inspectorOpen}
        onClose={() => setInspectorOpen(false)}
        turn={inspectedTurn}
        activeTab={inspectorTab}
        onTabChange={setInspectorTab}
        selectedSourceIndex={selectedSourceIdx}
        onSelectSourceIndex={setSelectedSourceIdx}
      />
    </AppShell>
  );
}
