"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { getSharedSession, type SharedSessionDetail } from "@/lib/api/client";
import { ResearchMessage, type ResearchTurn } from "@/components/workspace/ResearchMessage";
import { SamvadLogo } from "@/components/ui/Icons";

export default function SharedSessionPage() {
  const params = useParams<{ id: string }>();
  const shareId = params?.id;

  const [session, setSession] = useState<SharedSessionDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!shareId) return;
    getSharedSession(shareId)
      .then((data) => {
        setSession(data);
        setLoading(false);
      })
      .catch((err) => {
        setError(err instanceof Error ? err.message : "Shared chat could not be loaded.");
        setLoading(false);
      });
  }, [shareId]);

  return (
    <div className="min-h-screen bg-[var(--bg-canvas)] text-[var(--text-primary)] flex flex-col">
      {/* Top Bar */}
      <header className="sticky top-0 z-20 border-b border-[var(--border-subtle)] bg-[var(--bg-panel)]/95 backdrop-blur-md px-4 sm:px-8 py-3 flex items-center justify-between gap-4">
        <Link href="/" className="flex items-center gap-2.5 group">
          <SamvadLogo className="w-6 h-6 shrink-0" />
          <div className="leading-tight">
            <span className="font-display font-bold text-sm tracking-tight text-[var(--text-primary)]">
              SAMVAD <span className="text-[var(--accent)]">| संवाद</span>
            </span>
            <span className="block text-[10px] font-mono-tech text-[var(--text-muted)]">
              Shared Research Session
            </span>
          </div>
        </Link>

        <Link
          href="/"
          className="px-3.5 py-1.5 rounded-full text-xs font-semibold bg-[var(--accent)] text-[#0C1412] hover:bg-[var(--accent-hover)] transition-colors shadow-xs"
        >
          Open SAMVAD &rarr;
        </Link>
      </header>

      {/* Content */}
      <main className="flex-1 max-w-3xl w-full mx-auto px-4 py-8">
        {loading ? (
          <div className="py-24 flex flex-col items-center justify-center gap-3">
            <div className="w-6 h-6 border-2 border-[var(--accent)] border-t-transparent rounded-full animate-spin" />
            <span className="text-xs font-mono-tech text-[var(--text-muted)]">
              Loading shared research session...
            </span>
          </div>
        ) : error || !session ? (
          <div className="rounded-xl border border-[var(--status-error)]/30 bg-[var(--status-error-soft)] p-6 text-center space-y-3">
            <p className="text-sm font-semibold text-[var(--status-error)]">
              Shared Session Unavailable
            </p>
            <p className="text-xs text-[var(--text-secondary)]">
              {error || "This shared chat link does not exist or has expired."}
            </p>
            <Link
              href="/"
              className="inline-block mt-2 px-4 py-2 rounded-lg text-xs font-semibold bg-[var(--bg-panel)] border border-[var(--border-default)] hover:border-[var(--accent-border)] transition-colors"
            >
              Go to Workspace
            </Link>
          </div>
        ) : (
          <div className="space-y-6">
            <div className="border-b border-[var(--border-subtle)] pb-4 space-y-1.5">
              <div className="inline-flex items-center gap-2 px-2.5 py-0.5 rounded-full bg-[var(--accent-soft)] border border-[var(--accent-border)] text-[10px] font-mono-tech text-[var(--accent)] uppercase tracking-wider">
                Shared Conversation
              </div>
              <h1 className="font-display font-bold text-xl sm:text-2xl text-[var(--text-primary)]">
                {session.title}
              </h1>
              <p className="text-[11px] font-mono-tech text-[var(--text-muted)]">
                Shared on {new Date(session.created_at).toLocaleString()}
              </p>
            </div>

            <div className="space-y-5">
              {session.turns.map((t, idx) => {
                const turn: ResearchTurn = {
                  id: t.id || `shared-turn-${idx}`,
                  query: t.query,
                  kind: t.kind === "voice" ? "voice" : "text",
                  strategy:
                    (t.response?.retrieval_method as "hybrid" | "dense" | "lexical") ||
                    "hybrid",
                  createdAt: t.createdAt || session.created_at,
                  response: t.response,
                  isLoading: false,
                };
                return (
                  <ResearchMessage
                    key={turn.id}
                    turn={turn}
                    isInspected={false}
                    onInspectTurn={() => {}}
                  />
                );
              })}
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
