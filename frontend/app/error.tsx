"use client";

import React, { useEffect } from "react";
import Link from "next/link";

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    // Log the error for developer inspection
    console.error("SAMVAD Client Error Boundary caught error:", error);
  }, [error]);

  return (
    <div className="min-h-screen w-full flex items-center justify-center p-6 bg-[var(--bg-canvas)] text-[var(--text-primary)]">
      <div className="max-w-md w-full p-8 rounded-2xl bg-[var(--bg-panel)] border border-[var(--border-subtle)] shadow-xl text-center space-y-4">
        <div className="w-12 h-12 rounded-2xl bg-[var(--status-error-soft)] border border-[var(--status-error)]/30 text-[var(--status-error)] flex items-center justify-center mx-auto text-xl font-bold">
          !
        </div>
        <h2 className="font-display font-bold text-lg text-[var(--text-primary)]">
          Application Interface Notice
        </h2>
        <p className="text-xs text-[var(--text-secondary)] leading-relaxed font-mono-tech break-words">
          {error?.message || "An unexpected rendering event occurred."}
        </p>
        <div className="flex items-center justify-center gap-3 pt-2">
          <button
            type="button"
            onClick={() => reset()}
            className="px-4 py-2 rounded-xl text-xs font-semibold bg-[var(--accent)] text-white hover:opacity-90 transition-opacity cursor-pointer shadow-xs"
          >
            Retry View
          </button>
          <Link
            href="/"
            className="px-4 py-2 rounded-xl text-xs font-medium bg-[var(--bg-surface)] text-[var(--text-secondary)] hover:text-[var(--text-primary)] border border-[var(--border-subtle)] transition-colors"
          >
            Go to Workspace
          </Link>
        </div>
      </div>
    </div>
  );
}

