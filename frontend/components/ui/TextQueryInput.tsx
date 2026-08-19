"use client";

import { useState, type FormEvent } from "react";

interface TextQueryInputProps {
  onSubmit: (query: string) => void;
  isLoading: boolean;
}

export default function TextQueryInput({
  onSubmit,
  isLoading,
}: TextQueryInputProps) {
  const [query, setQuery] = useState("");

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    const trimmed = query.trim();
    if (trimmed && !isLoading) {
      onSubmit(trimmed);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="w-full">
      <div className="flex items-center gap-2 rounded-xl border border-border-subtle bg-bg-surface/50 px-4 py-2 focus-within:border-accent/40 transition-colors">
        <input
          id="text-query-input"
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Or type your question here..."
          disabled={isLoading}
          className="flex-1 bg-transparent text-sm text-text-primary placeholder:text-text-muted outline-none disabled:opacity-50"
        />
        <button
          id="text-query-submit"
          type="submit"
          disabled={!query.trim() || isLoading}
          className="px-4 py-1.5 rounded-lg text-xs font-medium bg-accent/10 text-accent border border-accent/20 hover:bg-accent/20 disabled:opacity-30 disabled:cursor-not-allowed transition-colors cursor-pointer"
        >
          {isLoading ? (
            <div className="w-3 h-3 rounded-full border-2 border-accent border-t-transparent animate-spin" />
          ) : (
            "Send"
          )}
        </button>
      </div>
    </form>
  );
}
