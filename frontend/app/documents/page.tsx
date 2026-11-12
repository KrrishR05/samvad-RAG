"use client";

import React, { useCallback, useEffect, useRef, useState } from "react";
import {
  deleteDocument,
  listDocuments,
  uploadDocument,
} from "@/lib/api/client";
import type {
  ChunkStrategy,
  DocumentRecord,
  DocumentStatus,
} from "@/types/api";
import { AppShell } from "@/components/layout/AppShell";
import {
  AlertIcon,
  CheckIcon,
  RefreshIcon,
  TrashIcon,
  UploadIcon,
} from "@/components/ui/Icons";

function docStatusBadge(status: DocumentStatus) {
  switch (status) {
    case "indexed":
      return "bg-[var(--status-success-soft)] text-[var(--status-success)] border-[var(--status-success)]/30";
    case "processed":
      return "bg-[var(--accent-soft)] text-[var(--accent)] border-[var(--accent-border)]";
    case "failed":
      return "bg-[var(--status-error-soft)] text-[var(--status-error)] border-[var(--status-error)]/30";
    default:
      return "bg-[var(--bg-surface)] text-[var(--text-secondary)] border-[var(--border-subtle)]";
  }
}

export default function DocumentsPage() {
  const [documents, setDocuments] = useState<DocumentRecord[]>([]);
  const [totalChunks, setTotalChunks] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Upload state
  const [dragging, setDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadNotice, setUploadNotice] = useState<{
    type: "success" | "info" | "error";
    text: string;
  } | null>(null);

  // Upload options
  const [language, setLanguage] = useState("");
  const [chunkStrategy, setChunkStrategy] =
    useState<ChunkStrategy>("sliding_window");
  const [chunkSize, setChunkSize] = useState(800);
  const [chunkOverlap, setChunkOverlap] = useState(120);

  // Delete confirmation state
  const [confirmDeleteId, setConfirmDeleteId] = useState<string | null>(null);
  const [deletingId, setDeletingId] = useState<string | null>(null);

  const fileInputRef = useRef<HTMLInputElement>(null);

  const fetchDocs = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await listDocuments();
      setDocuments(res.documents);
      setTotalChunks(res.total_chunks);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to load documents."
      );
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    let active = true;
    listDocuments()
      .then((res) => {
        if (!active) return;
        setDocuments(res.documents);
        setTotalChunks(res.total_chunks);
      })
      .catch((err) => {
        if (!active) return;
        setError(
          err instanceof Error ? err.message : "Failed to load documents."
        );
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, []);

  const handleFiles = async (files: FileList | null) => {
    if (!files || files.length === 0) return;
    setUploading(true);
    setUploadNotice(null);

    let indexedCount = 0;
    let dupCount = 0;

    try {
      for (const file of Array.from(files)) {
        const res = await uploadDocument(file, {
          language: language || undefined,
          chunkStrategy,
          chunkSize,
          chunkOverlap,
        });
        if (res.duplicate) {
          dupCount += 1;
        } else {
          indexedCount += 1;
        }
      }

      if (indexedCount > 0 && dupCount === 0) {
        setUploadNotice({
          type: "success",
          text: `Successfully parsed, chunked, and indexed ${indexedCount} document${
            indexedCount === 1 ? "" : "s"
          }.`,
        });
      } else if (dupCount > 0 && indexedCount === 0) {
        setUploadNotice({
          type: "info",
          text: `Skipped ${dupCount} duplicate document${
            dupCount === 1 ? "" : "s"
          } (matching SHA-256 content already indexed).`,
        });
      } else {
        setUploadNotice({
          type: "success",
          text: `Indexed ${indexedCount} new document(s); ${dupCount} duplicate(s) skipped.`,
        });
      }
      await fetchDocs();
    } catch (err) {
      setUploadNotice({
        type: "error",
        text: err instanceof Error ? err.message : "Document upload failed.",
      });
    } finally {
      setUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  };

  const handleDelete = async (docId: string) => {
    setDeletingId(docId);
    try {
      await deleteDocument(docId);
      setConfirmDeleteId(null);
      await fetchDocs();
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to delete document."
      );
    } finally {
      setDeletingId(null);
    }
  };

  return (
    <AppShell
      pageTitle="Knowledge Base Management"
      headerActions={
        <button
          type="button"
          onClick={fetchDocs}
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
          {/* Header & Live Counts */}
          <div className="flex flex-wrap items-end justify-between gap-4">
            <div>
              <h2 className="font-display font-semibold text-xl text-[var(--text-primary)]">
                Indexed Knowledge Base
              </h2>
              <p className="text-sm text-[var(--text-secondary)] mt-1">
                Upload documents to parse, normalize (NFC Unicode), chunk, and index into both BM25 lexical and dense vector search.
              </p>
            </div>
            <div className="flex items-center gap-3 font-mono-tech text-xs">
              <div className="px-3 py-1.5 rounded-lg bg-[var(--bg-panel)] border border-[var(--border-subtle)]">
                <span className="text-[var(--text-muted)] mr-2">Documents:</span>
                <span className="text-[var(--text-primary)] font-medium">
                  {documents.length}
                </span>
              </div>
              <div className="px-3 py-1.5 rounded-lg bg-[var(--bg-panel)] border border-[var(--border-subtle)]">
                <span className="text-[var(--text-muted)] mr-2">Indexed Chunks:</span>
                <span className="text-[var(--text-primary)] font-medium">
                  {totalChunks}
                </span>
              </div>
            </div>
          </div>

          {/* Ingestion Configuration + Dropzone */}
          <section className="rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-panel)] p-5 space-y-4">
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              <div>
                <label className="block text-[11px] font-mono-tech text-[var(--text-muted)] mb-1">
                  Language Hint
                </label>
                <select
                  value={language}
                  onChange={(e) => setLanguage(e.target.value)}
                  className="w-full px-2.5 py-1.5 rounded-md text-xs bg-[var(--bg-surface)] text-[var(--text-primary)] border border-[var(--border-subtle)] focus:outline-none focus:border-[var(--accent-border)]"
                >
                  <option value="">Auto / Unspecified</option>
                  <option value="en">English (en)</option>
                  <option value="hi">Hindi (hi)</option>
                  <option value="bn">Bengali (bn)</option>
                  <option value="ta">Tamil (ta)</option>
                  <option value="te">Telugu (te)</option>
                  <option value="mr">Marathi (mr)</option>
                </select>
              </div>

              <div>
                <label className="block text-[11px] font-mono-tech text-[var(--text-muted)] mb-1">
                  Chunk Strategy
                </label>
                <select
                  value={chunkStrategy}
                  onChange={(e) =>
                    setChunkStrategy(e.target.value as ChunkStrategy)
                  }
                  className="w-full px-2.5 py-1.5 rounded-md text-xs bg-[var(--bg-surface)] text-[var(--text-primary)] border border-[var(--border-subtle)] focus:outline-none focus:border-[var(--accent-border)]"
                >
                  <option value="sliding_window">Sliding Window</option>
                  <option value="fixed_size">Fixed Size</option>
                  <option value="semantic">Semantic / Paragraph</option>
                  <option value="whole_passage">Whole Passage</option>
                </select>
              </div>

              <div>
                <label className="block text-[11px] font-mono-tech text-[var(--text-muted)] mb-1">
                  Chunk Size (chars)
                </label>
                <input
                  type="number"
                  min={100}
                  max={4000}
                  step={50}
                  value={chunkSize}
                  onChange={(e) => setChunkSize(Number(e.target.value) || 800)}
                  className="w-full px-2.5 py-1.5 rounded-md text-xs font-mono-tech bg-[var(--bg-surface)] text-[var(--text-primary)] border border-[var(--border-subtle)] focus:outline-none focus:border-[var(--accent-border)]"
                />
              </div>

              <div>
                <label className="block text-[11px] font-mono-tech text-[var(--text-muted)] mb-1">
                  Overlap (chars)
                </label>
                <input
                  type="number"
                  min={0}
                  max={1000}
                  step={20}
                  value={chunkOverlap}
                  onChange={(e) => setChunkOverlap(Number(e.target.value) || 0)}
                  className="w-full px-2.5 py-1.5 rounded-md text-xs font-mono-tech bg-[var(--bg-surface)] text-[var(--text-primary)] border border-[var(--border-subtle)] focus:outline-none focus:border-[var(--accent-border)]"
                />
              </div>
            </div>

            <div
              onDragOver={(e) => {
                e.preventDefault();
                setDragging(true);
              }}
              onDragLeave={() => setDragging(false)}
              onDrop={(e) => {
                e.preventDefault();
                setDragging(false);
                handleFiles(e.dataTransfer.files);
              }}
              onClick={() => !uploading && fileInputRef.current?.click()}
              className={`rounded-xl border-2 border-dashed px-6 py-8 text-center transition-colors cursor-pointer ${
                dragging
                  ? "border-[var(--accent)] bg-[var(--accent-soft)]"
                  : "border-[var(--border-default)] hover:border-[var(--border-strong)] bg-[var(--bg-surface)]/40"
              }`}
            >
              <input
                ref={fileInputRef}
                type="file"
                multiple
                accept=".txt,.md,.markdown,.pdf,.docx,.html,.htm,.json"
                onChange={(e) => handleFiles(e.target.files)}
                className="hidden"
              />
              <UploadIcon className="w-6 h-6 mx-auto text-[var(--accent)] mb-2" />
              <p className="text-sm font-medium text-[var(--text-primary)]">
                {uploading
                  ? "Uploading, chunking, and rebuilding retrieval indexes..."
                  : "Drop documents here or click to browse"}
              </p>
              <p className="text-xs text-[var(--text-muted)] mt-1 font-mono-tech">
                Supported: .txt, .md, .pdf, .docx, .html, .json (SHA-256 deduplicated)
              </p>
            </div>

            {uploadNotice && (
              <div
                className={`rounded-lg border px-4 py-2.5 text-xs flex items-center gap-2 ${
                  uploadNotice.type === "success"
                    ? "bg-[var(--status-success-soft)] border-[var(--status-success)]/30 text-[var(--status-success)]"
                    : uploadNotice.type === "error"
                    ? "bg-[var(--status-error-soft)] border-[var(--status-error)]/30 text-[var(--status-error)]"
                    : "bg-[var(--accent-soft)] border-[var(--accent-border)] text-[var(--accent)]"
                }`}
              >
                {uploadNotice.type === "success" ? <CheckIcon /> : <AlertIcon className="w-3.5 h-3.5" />}
                <span>{uploadNotice.text}</span>
              </div>
            )}
          </section>

          {error && (
            <div className="rounded-lg border border-[var(--status-error)]/30 bg-[var(--status-error-soft)] p-3 text-xs text-[var(--status-error)]">
              {error}
            </div>
          )}

          {/* Document Inventory Table */}
          <section className="rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-panel)] overflow-hidden">
            <div className="px-5 py-3.5 border-b border-[var(--border-subtle)] flex items-center justify-between">
              <h3 className="text-xs font-mono-tech uppercase tracking-wider text-[var(--text-muted)]">
                Document Registry
              </h3>
              <span className="text-[11px] font-mono-tech text-[var(--text-muted)]">
                SQLite + Dense Vector Index
              </span>
            </div>

            {loading ? (
              <div className="p-8 text-center text-xs text-[var(--text-muted)]">
                Loading knowledge base registry...
              </div>
            ) : documents.length === 0 ? (
              <div className="p-10 text-center space-y-1.5">
                <p className="text-sm font-medium text-[var(--text-secondary)]">
                  No documents indexed yet
                </p>
                <p className="text-xs text-[var(--text-muted)]">
                  Upload text, Markdown, PDF, or DOCX files above to start querying with evidence.
                </p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse text-xs">
                  <thead>
                    <tr className="border-b border-[var(--border-subtle)] text-[11px] font-mono-tech text-[var(--text-muted)] bg-[var(--bg-surface)]/60">
                      <th className="py-2.5 px-4 font-medium">Filename</th>
                      <th className="py-2.5 px-4 font-medium">Status</th>
                      <th className="py-2.5 px-4 font-medium">Language</th>
                      <th className="py-2.5 px-4 font-medium">Chunks</th>
                      <th className="py-2.5 px-4 font-medium">Content Hash</th>
                      <th className="py-2.5 px-4 font-medium text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[var(--border-subtle)]">
                    {documents.map((doc) => (
                      <tr
                        key={doc.doc_id}
                        className="hover:bg-[var(--bg-surface)]/40 transition-colors"
                      >
                        <td className="py-3 px-4">
                          <div className="font-medium text-[var(--text-primary)]">
                            {doc.filename}
                          </div>
                          <div className="text-[11px] font-mono-tech text-[var(--text-muted)]">
                            {doc.doc_id} &middot; {doc.media_type}
                          </div>
                          {doc.error_message && (
                            <p className="text-[11px] text-[var(--status-error)] mt-0.5">
                              {doc.error_message}
                            </p>
                          )}
                        </td>
                        <td className="py-3 px-4">
                          <span
                            className={`inline-block px-2 py-0.5 rounded font-mono-tech text-[11px] border ${docStatusBadge(
                              doc.status
                            )}`}
                          >
                            {doc.status}
                          </span>
                        </td>
                        <td className="py-3 px-4 font-mono-tech text-[var(--text-secondary)]">
                          {doc.language || "auto"}
                        </td>
                        <td className="py-3 px-4 font-mono-tech text-[var(--text-primary)]">
                          {doc.chunk_count}
                        </td>
                        <td className="py-3 px-4 font-mono-tech text-[var(--text-muted)]">
                          {doc.content_hash.slice(0, 12)}...
                        </td>
                        <td className="py-3 px-4 text-right">
                          {confirmDeleteId === doc.doc_id ? (
                            <div className="inline-flex items-center gap-1.5">
                              <button
                                type="button"
                                disabled={deletingId === doc.doc_id}
                                onClick={() => handleDelete(doc.doc_id)}
                                className="px-2 py-1 rounded bg-[var(--status-error)] text-white text-[11px] font-medium cursor-pointer"
                              >
                                {deletingId === doc.doc_id
                                  ? "Deleting..."
                                  : "Confirm"}
                              </button>
                              <button
                                type="button"
                                onClick={() => setConfirmDeleteId(null)}
                                className="px-2 py-1 rounded bg-[var(--bg-surface)] text-[var(--text-secondary)] border border-[var(--border-subtle)] text-[11px] cursor-pointer"
                              >
                                Cancel
                              </button>
                            </div>
                          ) : (
                            <button
                              type="button"
                              onClick={() => setConfirmDeleteId(doc.doc_id)}
                              title="Delete document"
                              className="inline-flex items-center gap-1 px-2 py-1 rounded text-[var(--text-muted)] hover:text-[var(--status-error)] hover:bg-[var(--status-error-soft)] transition-colors cursor-pointer"
                            >
                              <TrashIcon />
                              <span>Delete</span>
                            </button>
                          )}
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
