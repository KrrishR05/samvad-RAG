"use client";

import React, { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { createPortal } from "react-dom";
import Link from "next/link";
import {
  deleteDocument,
  getDocumentChunks,
  listDocuments,
  uploadDocument,
} from "@/lib/api/client";
import type {
  ChunkItem,
  ChunkStrategy,
  DocumentRecord,
  DocumentStatus,
} from "@/types/api";
import { AppShell } from "@/components/layout/AppShell";
import {
  AlertIcon,
  CheckIcon,
  DocumentsIcon,
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

function formatDate(iso: string) {
  try {
    const d = new Date(iso);
    return d.toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return iso;
  }
}

export default function DocumentsPage() {
  const [documents, setDocuments] = useState<DocumentRecord[]>([]);
  const [totalChunks, setTotalChunks] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Search & Filter
  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [langFilter, setLangFilter] = useState<string>("all");

  // Upload state
  const [dragging, setDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadNotice, setUploadNotice] = useState<{
    type: "success" | "info" | "error";
    text: string;
  } | null>(null);

  // Ingestion settings toggle
  const [showSettings, setShowSettings] = useState(false);
  const [language, setLanguage] = useState("");
  const [chunkStrategy, setChunkStrategy] =
    useState<ChunkStrategy>("sliding_window");
  const [chunkSize, setChunkSize] = useState(800);
  const [chunkOverlap, setChunkOverlap] = useState(120);

  // Delete state
  const [confirmDeleteId, setConfirmDeleteId] = useState<string | null>(null);
  const [deletingId, setDeletingId] = useState<string | null>(null);

  // Document Chunk Inspection Drawer
  const [mounted, setMounted] = useState(false);
  const [selectedDoc, setSelectedDoc] = useState<DocumentRecord | null>(null);
  const [inspectChunks, setInspectChunks] = useState<ChunkItem[]>([]);
  const [inspectLoading, setInspectLoading] = useState(false);
  const [copiedChunkId, setCopiedChunkId] = useState<string | null>(null);
  const [inspectFilter, setInspectFilter] = useState("");

  useEffect(() => {
    setMounted(true);
  }, []);

  // Close inspector on Escape key
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape" && selectedDoc) {
        setSelectedDoc(null);
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [selectedDoc]);

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
    const id = window.setTimeout(() => {
      void fetchDocs();
    }, 0);
    return () => window.clearTimeout(id);
  }, [fetchDocs]);

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
          text: `Successfully parsed, normalized, chunked, and indexed ${indexedCount} document${
            indexedCount === 1 ? "" : "s"
          }.`,
        });
      } else if (dupCount > 0 && indexedCount === 0) {
        setUploadNotice({
          type: "info",
          text: `Skipped ${dupCount} duplicate document${
            dupCount === 1 ? "" : "s"
          } (matching SHA-256 content hash already registered).`,
        });
      } else {
        setUploadNotice({
          type: "success",
          text: `Indexed ${indexedCount} new document(s); ${dupCount} duplicate(s) preserved.`,
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
      if (selectedDoc?.doc_id === docId) {
        setSelectedDoc(null);
      }
      await fetchDocs();
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to delete document."
      );
    } finally {
      setDeletingId(null);
    }
  };

  const handleInspectDoc = async (doc: DocumentRecord) => {
    setSelectedDoc(doc);
    setInspectLoading(true);
    setInspectFilter("");
    try {
      const res = await getDocumentChunks(doc.doc_id);
      setInspectChunks(res.chunks || []);
    } catch {
      setInspectChunks([]);
    } finally {
      setInspectLoading(false);
    }
  };

  const copyChunk = (id: string, text: string) => {
    navigator.clipboard.writeText(text);
    setCopiedChunkId(id);
    setTimeout(() => setCopiedChunkId(null), 1500);
  };

  const loadSampleDossier = async () => {
    setUploading(true);
    setUploadNotice(null);
    try {
      const sampleText = `ISRO Chandrayaan-3 Mission & Lunar South Pole Exploration Dossier

Chandrayaan-3 is the third lunar exploration mission developed by the Indian Space Research Organisation (ISRO).
Launched on 14 July 2023 from Satish Dhawan Space Centre in Sriharikota, the spacecraft successfully completed a soft landing on the lunar south pole region on 23 August 2023 at 18:04 IST.
This historic achievement made India the first nation to successfully land a craft near the lunar south pole and the fourth country to soft-land on the Moon, following the United States, the Soviet Union, and China.

The mission consists of the Vikram lander, named after Dr. Vikram Sarabhai (father of India's space programme), and the Pragyan rover (Sanskrit for wisdom).
The scientific payloads onboard included:
1. ChaSTE (Chandra's Surface Thermophysical Experiment) measuring thermal conductivity and temperature gradients up to a depth of 10 cm.
2. ILSA (Instrument for Lunar Seismic Activity) recording lunar seismicity to investigate sub-surface crustal characteristics.
3. LP (Langmuir Probe) estimating lunar plasma density and variation over lunar daytime.
4. APXS (Alpha Particle X-Ray Spectrometer) analyzing lunar soil elemental composition, confirming presence of sulfur, aluminum, calcium, iron, titanium, and oxygen.
5. LIBS (Laser-Induced Breakdown Spectroscopy) confirming elemental sulfur (S) through direct in-situ spectral signatures.

The propulsion module continues to operate in lunar orbit carrying the SHAPE (Spectro-polarimetry of Habitable Planet Earth) payload to study Earth's habitable signatures from lunar distance.`;

      const blob = new Blob([sampleText], { type: "text/plain" });
      const file = new File([blob], "chandrayaan3_mission_dossier.txt", {
        type: "text/plain",
      });

      const res = await uploadDocument(file, {
        language: "en",
        chunkStrategy: "sliding_window",
        chunkSize: 600,
        chunkOverlap: 100,
      });

      setUploadNotice({
        type: res.duplicate ? "info" : "success",
        text: res.duplicate
          ? "Sample dossier is already indexed in your knowledge base."
          : `Sample ISRO Chandrayaan-3 Dossier successfully indexed (${res.total_chunks_indexed} chunks).`,
      });
      await fetchDocs();
    } catch (err) {
      setUploadNotice({
        type: "error",
        text: err instanceof Error ? err.message : "Failed to load sample dossier.",
      });
    } finally {
      setUploading(false);
    }
  };

  // Filtered documents
  const filteredDocs = useMemo(() => {
    return documents.filter((doc) => {
      const matchesSearch =
        doc.filename.toLowerCase().includes(searchQuery.toLowerCase()) ||
        doc.doc_id.toLowerCase().includes(searchQuery.toLowerCase());
      const matchesStatus =
        statusFilter === "all" || doc.status === statusFilter;
      const matchesLang =
        langFilter === "all" || (doc.language || "auto") === langFilter;
      return matchesSearch && matchesStatus && matchesLang;
    });
  }, [documents, searchQuery, statusFilter, langFilter]);

  return (
    <AppShell
      pageTitle="Knowledge Base & Document Index"
      headerActions={
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={loadSampleDossier}
            disabled={uploading}
            className="hidden sm:inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium bg-[var(--accent-soft)] text-[var(--accent)] border border-[var(--accent-border)] hover:bg-[var(--accent)] hover:text-white transition-all cursor-pointer shadow-xs disabled:opacity-50"
            title="Index a sample scientific dossier to test retrieval immediately"
          >
            <span>✦ Load Sample Dossier</span>
          </button>
          <button
            type="button"
            onClick={fetchDocs}
            disabled={loading}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium bg-[var(--bg-surface)] text-[var(--text-secondary)] border border-[var(--border-subtle)] hover:text-[var(--text-primary)] transition-colors cursor-pointer"
          >
            <RefreshIcon className={loading ? "animate-spin" : ""} />
            <span>Refresh</span>
          </button>
        </div>
      }
    >
      <main className="flex-1 overflow-y-auto px-4 sm:px-8 py-6">
        <div className="max-w-5xl mx-auto space-y-6">
          {/* Header & KPI Metrics */}
          <div className="flex flex-wrap items-end justify-between gap-4">
            <div>
              <h2 className="font-display font-semibold text-xl text-[var(--text-primary)]">
                Knowledge Base Registry
              </h2>
              <p className="text-sm text-[var(--text-secondary)] mt-1 max-w-2xl leading-relaxed">
                Ingest, normalize (NFC Unicode), and chunk scientific research documents. All indexed chunks are simultaneously available in Okapi BM25 and dense SVD cosine retrieval.
              </p>
            </div>
            <div className="flex items-center gap-3 font-mono-tech text-xs">
              <div className="px-3.5 py-2 rounded-xl bg-[var(--bg-panel)] border border-[var(--border-subtle)] shadow-xs">
                <span className="text-[var(--text-muted)] mr-2">Documents:</span>
                <span className="text-[var(--text-primary)] font-bold text-sm">
                  {documents.length}
                </span>
              </div>
              <div className="px-3.5 py-2 rounded-xl bg-[var(--bg-panel)] border border-[var(--border-subtle)] shadow-xs">
                <span className="text-[var(--text-muted)] mr-2">Indexed Chunks:</span>
                <span className="text-[var(--accent)] font-bold text-sm">
                  {totalChunks}
                </span>
              </div>
            </div>
          </div>

          {/* Upload Dropzone & Ingestion Parameters */}
          <section className="rounded-2xl border border-[var(--border-subtle)] bg-[var(--bg-panel)] p-5 space-y-4 shadow-sm">
            {/* Dropzone */}
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
              className={`rounded-xl border-2 border-dashed p-8 text-center transition-all cursor-pointer group ${
                dragging
                  ? "border-[var(--accent)] bg-[var(--accent-soft)] scale-[1.005]"
                  : "border-[var(--border-strong)] hover:border-[var(--accent-border)] bg-[var(--bg-surface)]/30 hover:bg-[var(--bg-surface)]/60"
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
              <div className="w-12 h-12 rounded-2xl bg-[var(--accent-soft)] border border-[var(--accent-border)] flex items-center justify-center mx-auto mb-3 group-hover:scale-105 transition-transform">
                <UploadIcon className="w-6 h-6 text-[var(--accent)]" />
              </div>
              <p className="text-sm font-semibold text-[var(--text-primary)]">
                {uploading
                  ? "Parsing, chunking, and indexing into vector database..."
                  : "Drop scientific documents here or click to browse"}
              </p>
              <p className="text-xs text-[var(--text-muted)] mt-1.5 font-mono-tech">
                Supports PDF, DOCX, TXT, Markdown, HTML, JSON &middot; SHA-256 deduplicated &middot; Auto Indic Tokenization
              </p>
            </div>

            {/* Ingestion Parameters Toggle */}
            <div className="flex items-center justify-between pt-1">
              <button
                type="button"
                onClick={() => setShowSettings(!showSettings)}
                className="text-xs font-mono-tech text-[var(--text-secondary)] hover:text-[var(--accent)] flex items-center gap-1.5 transition-colors cursor-pointer"
              >
                <span>{showSettings ? "▼ Hide" : "▶ Advanced"} Ingestion Parameters</span>
                <span className="text-[10px] text-[var(--text-muted)]">
                  ({chunkStrategy}, {chunkSize} chars, {chunkOverlap} overlap)
                </span>
              </button>
            </div>

            {/* Expandable Chunking Configuration */}
            {showSettings && (
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-3 border-t border-[var(--border-subtle)] animate-in fade-in duration-150">
                <div>
                  <label className="block text-[11px] font-mono-tech text-[var(--text-muted)] mb-1">
                    Language Hint
                  </label>
                  <select
                    value={language}
                    onChange={(e) => setLanguage(e.target.value)}
                    className="w-full px-2.5 py-1.5 rounded-lg text-xs bg-[var(--bg-surface)] text-[var(--text-primary)] border border-[var(--border-subtle)] focus:outline-none focus:border-[var(--accent-border)]"
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
                    className="w-full px-2.5 py-1.5 rounded-lg text-xs bg-[var(--bg-surface)] text-[var(--text-primary)] border border-[var(--border-subtle)] focus:outline-none focus:border-[var(--accent-border)]"
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
                    className="w-full px-2.5 py-1.5 rounded-lg text-xs font-mono-tech bg-[var(--bg-surface)] text-[var(--text-primary)] border border-[var(--border-subtle)] focus:outline-none focus:border-[var(--accent-border)]"
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
                    className="w-full px-2.5 py-1.5 rounded-lg text-xs font-mono-tech bg-[var(--bg-surface)] text-[var(--text-primary)] border border-[var(--border-subtle)] focus:outline-none focus:border-[var(--accent-border)]"
                  />
                </div>
              </div>
            )}

            {/* Notification Banner */}
            {uploadNotice && (
              <div
                className={`rounded-xl border px-4 py-3 text-xs flex items-center gap-2.5 animate-in fade-in duration-200 ${
                  uploadNotice.type === "success"
                    ? "bg-[var(--status-success-soft)] border-[var(--status-success)]/30 text-[var(--status-success)]"
                    : uploadNotice.type === "error"
                    ? "bg-[var(--status-error-soft)] border-[var(--status-error)]/30 text-[var(--status-error)]"
                    : "bg-[var(--accent-soft)] border-[var(--accent-border)] text-[var(--accent)]"
                }`}
              >
                {uploadNotice.type === "success" ? (
                  <CheckIcon className="w-4 h-4 shrink-0" />
                ) : (
                  <AlertIcon className="w-4 h-4 shrink-0" />
                )}
                <span className="font-medium">{uploadNotice.text}</span>
              </div>
            )}
          </section>

          {error && (
            <div className="rounded-xl border border-[var(--status-error)]/30 bg-[var(--status-error-soft)] p-3.5 text-xs text-[var(--status-error)] flex items-center gap-2">
              <AlertIcon className="w-4 h-4 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {/* Search, Filter & Document Inventory Table */}
          <section className="rounded-2xl border border-[var(--border-subtle)] bg-[var(--bg-panel)] overflow-hidden shadow-sm">
            {/* Search and Filters Bar */}
            <div className="p-4 border-b border-[var(--border-subtle)] flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3 bg-[var(--bg-surface)]/20">
              {/* Search input */}
              <div className="relative flex-1 max-w-md">
                <input
                  type="text"
                  placeholder="Search documents by filename or ID..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full pl-9 pr-3 py-2 text-xs rounded-xl bg-[var(--bg-surface)] border border-[var(--border-subtle)] focus:border-[var(--accent-border)] focus:outline-none text-[var(--text-primary)] placeholder-[var(--text-muted)]"
                />
                <svg
                  className="w-4 h-4 text-[var(--text-muted)] absolute left-3 top-1/2 -translate-y-1/2"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                >
                  <circle cx="11" cy="11" r="8" />
                  <line x1="21" y1="21" x2="16.65" y2="16.65" />
                </svg>
              </div>

              {/* Status & Language Filter Pills */}
              <div className="flex items-center gap-2 flex-wrap text-xs">
                <div className="flex items-center gap-1 bg-[var(--bg-surface)] p-1 rounded-xl border border-[var(--border-subtle)]">
                  {["all", "indexed", "failed"].map((st) => (
                    <button
                      key={st}
                      type="button"
                      onClick={() => setStatusFilter(st)}
                      className={`px-2.5 py-1 rounded-lg capitalize font-mono-tech text-[11px] transition-colors cursor-pointer ${
                        statusFilter === st
                          ? "bg-[var(--accent)] text-white font-semibold shadow-xs"
                          : "text-[var(--text-muted)] hover:text-[var(--text-primary)]"
                      }`}
                    >
                      {st}
                    </button>
                  ))}
                </div>

                <select
                  value={langFilter}
                  onChange={(e) => setLangFilter(e.target.value)}
                  className="px-2.5 py-1.5 rounded-xl text-xs bg-[var(--bg-surface)] border border-[var(--border-subtle)] text-[var(--text-secondary)] focus:outline-none"
                >
                  <option value="all">All Languages</option>
                  <option value="en">English (en)</option>
                  <option value="hi">Hindi (hi)</option>
                  <option value="auto">Auto / Unspecified</option>
                </select>
              </div>
            </div>

            {/* Document Inventory Table */}
            {loading ? (
              <div className="p-12 text-center text-xs text-[var(--text-muted)] flex items-center justify-center gap-2">
                <div className="w-4 h-4 border-2 border-[var(--accent)] border-t-transparent rounded-full animate-spin" />
                <span>Loading knowledge base registry...</span>
              </div>
            ) : filteredDocs.length === 0 ? (
              <div className="p-12 text-center space-y-3">
                <div className="w-12 h-12 rounded-2xl bg-[var(--bg-surface)] border border-[var(--border-subtle)] flex items-center justify-center mx-auto text-[var(--text-muted)]">
                  <DocumentsIcon className="w-6 h-6" />
                </div>
                <div>
                  <p className="text-sm font-semibold text-[var(--text-secondary)]">
                    {searchQuery ? "No matching documents found" : "Knowledge Base is Empty"}
                  </p>
                  <p className="text-xs text-[var(--text-muted)] mt-1 max-w-sm mx-auto">
                    {searchQuery
                      ? `No documents matched '${searchQuery}'. Try clearing your filter.`
                      : "Upload PDF, DOCX, or text files above to begin grounding queries with citations."}
                  </p>
                </div>
                {!searchQuery && (
                  <button
                    type="button"
                    onClick={loadSampleDossier}
                    className="px-4 py-2 rounded-xl text-xs font-semibold bg-[var(--accent)] text-white hover:opacity-95 shadow-sm cursor-pointer"
                  >
                    Load Sample ISRO Dossier
                  </button>
                )}
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse text-xs">
                  <thead>
                    <tr className="border-b border-[var(--border-subtle)] text-[11px] font-mono-tech text-[var(--text-muted)] bg-[var(--bg-surface)]/50">
                      <th className="py-3 px-4 font-medium">Filename & Provenance</th>
                      <th className="py-3 px-4 font-medium">Status</th>
                      <th className="py-3 px-4 font-medium">Lang</th>
                      <th className="py-3 px-4 font-medium">Chunks</th>
                      <th className="py-3 px-4 font-medium">Indexed Date</th>
                      <th className="py-3 px-4 font-medium text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[var(--border-subtle)]">
                    {filteredDocs.map((doc) => (
                      <tr
                        key={doc.doc_id}
                        onClick={() => handleInspectDoc(doc)}
                        className={`hover:bg-[var(--bg-surface)]/40 transition-colors cursor-pointer group ${
                          selectedDoc?.doc_id === doc.doc_id
                            ? "bg-[var(--accent-soft)]/20"
                            : ""
                        }`}
                      >
                        <td className="py-3.5 px-4">
                          <div className="font-semibold text-[var(--text-primary)] group-hover:text-[var(--accent)] transition-colors flex items-center gap-2">
                            <span>{doc.filename}</span>
                          </div>
                          <div className="text-[11px] font-mono-tech text-[var(--text-muted)] mt-0.5">
                            {doc.doc_id} &middot; {doc.media_type} &middot;{" "}
                            <span title={doc.content_hash}>
                              sha256:{doc.content_hash.slice(0, 8)}...
                            </span>
                          </div>
                          {doc.error_message && (
                            <p className="text-[11px] text-[var(--status-error)] mt-1">
                              {doc.error_message}
                            </p>
                          )}
                        </td>

                        <td className="py-3.5 px-4">
                          <span
                            className={`inline-block px-2.5 py-0.5 rounded-full font-mono-tech text-[10.5px] font-semibold border ${docStatusBadge(
                              doc.status
                            )}`}
                          >
                            {doc.status}
                          </span>
                        </td>

                        <td className="py-3.5 px-4 font-mono-tech text-[var(--text-secondary)] uppercase">
                          {doc.language || "auto"}
                        </td>

                        <td className="py-3.5 px-4">
                          <span className="font-mono-tech font-bold text-[var(--text-primary)] px-2 py-1 rounded-md bg-[var(--bg-surface)] border border-[var(--border-subtle)]">
                            {doc.chunk_count}
                          </span>
                        </td>

                        <td className="py-3.5 px-4 text-[var(--text-muted)] text-[11px]">
                          {formatDate(doc.created_at)}
                        </td>

                        <td
                          className="py-3.5 px-4 text-right"
                          onClick={(e) => e.stopPropagation()}
                        >
                          <div className="inline-flex items-center gap-1.5">
                            <button
                              type="button"
                              onClick={(e) => {
                                e.stopPropagation();
                                handleInspectDoc(doc);
                              }}
                              className="px-2.5 py-1 rounded-lg text-[11px] font-medium bg-[var(--bg-surface)] text-[var(--text-secondary)] hover:text-[var(--text-primary)] border border-[var(--border-subtle)] hover:border-[var(--accent-border)] transition-colors cursor-pointer"
                              title="Inspect document chunks and provenance"
                            >
                              Inspect
                            </button>

                            <Link
                              href={`/?q=${encodeURIComponent(
                                `Summarize key claims in ${doc.filename}`
                              )}`}
                              className="px-2.5 py-1 rounded-lg text-[11px] font-medium bg-[var(--accent-soft)] text-[var(--accent)] hover:bg-[var(--accent)] hover:text-white transition-all cursor-pointer"
                              title="Ask a query about this document"
                            >
                              Query
                            </Link>

                            {confirmDeleteId === doc.doc_id ? (
                              <div className="inline-flex items-center gap-1">
                                <button
                                  type="button"
                                  disabled={deletingId === doc.doc_id}
                                  onClick={() => handleDelete(doc.doc_id)}
                                  className="px-2 py-1 rounded-lg bg-[var(--status-error)] text-white text-[11px] font-semibold cursor-pointer shadow-xs"
                                >
                                  {deletingId === doc.doc_id ? "..." : "Confirm"}
                                </button>
                                <button
                                  type="button"
                                  onClick={() => setConfirmDeleteId(null)}
                                  className="px-2 py-1 rounded-lg bg-[var(--bg-surface)] text-[var(--text-muted)] border border-[var(--border-subtle)] text-[11px] cursor-pointer"
                                >
                                  ✕
                                </button>
                              </div>
                            ) : (
                              <button
                                type="button"
                                onClick={() => setConfirmDeleteId(doc.doc_id)}
                                title="Delete document"
                                className="p-1.5 rounded-lg text-[var(--text-muted)] hover:text-[var(--status-error)] hover:bg-[var(--status-error-soft)] transition-colors cursor-pointer"
                              >
                                <TrashIcon className="w-3.5 h-3.5" />
                              </button>
                            )}
                          </div>
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

      {/* SLIDE-OVER DOCUMENT CHUNK INSPECTION DRAWER (Rendered via Portal to document.body) */}
      {mounted &&
        selectedDoc &&
        createPortal(
          <div className="fixed inset-0 z-[100] overflow-hidden flex justify-end">
            {/* Dark Blur Backdrop */}
            <div
              className="fixed inset-0 bg-black/60 backdrop-blur-sm transition-opacity"
              onClick={() => setSelectedDoc(null)}
              aria-hidden="true"
            />

            {/* Drawer Container */}
            <div
              className="relative w-full max-w-2xl bg-[var(--bg-panel)] border-l border-[var(--border-subtle)] shadow-2xl flex flex-col h-full z-10 transition-transform duration-300 ease-out"
              role="dialog"
              aria-modal="true"
            >
              {/* Drawer Top Header */}
              <div className="p-5 border-b border-[var(--border-subtle)] bg-[var(--bg-surface)]/40 flex items-start justify-between gap-4">
                <div className="space-y-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="text-[10px] font-mono-tech px-2 py-0.5 rounded-full bg-[var(--accent-soft)] text-[var(--accent)] font-bold uppercase tracking-wider">
                      CHUNK INSPECTOR
                    </span>
                    <span
                      className={`inline-block px-2 py-0.5 rounded-full font-mono-tech text-[10px] font-semibold border ${docStatusBadge(
                        selectedDoc.status
                      )}`}
                    >
                      {selectedDoc.status}
                    </span>
                  </div>
                  <h3
                    className="font-display font-bold text-lg text-[var(--text-primary)] truncate"
                    title={selectedDoc.filename}
                  >
                    {selectedDoc.filename}
                  </h3>
                  <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-xs font-mono-tech text-[var(--text-muted)]">
                    <span>
                      ID:{" "}
                      <code className="text-[var(--text-secondary)]">
                        {selectedDoc.doc_id.slice(0, 16)}...
                      </code>
                    </span>
                    <span>&bull;</span>
                    <span className="font-semibold text-[var(--text-primary)]">
                      {selectedDoc.chunk_count} Chunks
                    </span>
                    <span>&bull;</span>
                    <span>Lang: {selectedDoc.language || "AUTO"}</span>
                  </div>
                </div>

                <div className="flex items-center gap-2 shrink-0">
                  <Link
                    href={`/?q=${encodeURIComponent(
                      `Summarize ${selectedDoc.filename}`
                    )}`}
                    className="px-3 py-1.5 rounded-xl text-xs font-semibold bg-[var(--accent)] text-white hover:opacity-95 transition-opacity shadow-sm"
                  >
                    Query in Workspace ↗
                  </Link>
                  <button
                    type="button"
                    onClick={() => setSelectedDoc(null)}
                    className="p-1.5 rounded-lg text-[var(--text-muted)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-surface)] transition-colors cursor-pointer text-lg leading-none"
                    title="Close drawer (Esc)"
                  >
                    ✕
                  </button>
                </div>
              </div>

              {/* Sub-bar: Search chunks & token info */}
              <div className="p-3.5 border-b border-[var(--border-subtle)] bg-[var(--bg-surface)]/20 flex items-center justify-between gap-3">
                <div className="relative flex-1">
                  <input
                    type="text"
                    placeholder="Filter chunks in this document..."
                    value={inspectFilter}
                    onChange={(e) => setInspectFilter(e.target.value)}
                    className="w-full pl-8 pr-3 py-1.5 text-xs rounded-lg bg-[var(--bg-surface)] border border-[var(--border-subtle)] focus:border-[var(--accent-border)] focus:outline-none text-[var(--text-primary)] placeholder-[var(--text-muted)]"
                  />
                  <svg
                    className="w-3.5 h-3.5 text-[var(--text-muted)] absolute left-2.5 top-1/2 -translate-y-1/2"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                  >
                    <circle cx="11" cy="11" r="8" />
                    <line x1="21" y1="21" x2="16.65" y2="16.65" />
                  </svg>
                </div>
                <span className="text-[11px] font-mono-tech text-[var(--text-muted)] shrink-0">
                  {
                    inspectChunks.filter((c) =>
                      inspectFilter
                        ? c.text
                            .toLowerCase()
                            .includes(inspectFilter.toLowerCase())
                        : true
                    ).length
                  }{" "}
                  of {inspectChunks.length} chunks
                </span>
              </div>

              {/* Chunks List Body */}
              <div className="flex-1 overflow-y-auto p-5 space-y-3.5">
                {inspectLoading ? (
                  <div className="py-20 text-center text-xs text-[var(--text-muted)] flex flex-col items-center justify-center gap-3">
                    <div className="w-6 h-6 border-2 border-[var(--accent)] border-t-transparent rounded-full animate-spin" />
                    <span className="font-mono-tech">
                      Loading parsed document chunks from database store...
                    </span>
                  </div>
                ) : inspectChunks.length === 0 ? (
                  <div className="py-16 text-center text-xs text-[var(--text-muted)] space-y-2">
                    <p className="font-semibold text-sm text-[var(--text-secondary)]">
                      No chunks found
                    </p>
                    <p>
                      No chunks currently indexed for this document in the database.
                    </p>
                  </div>
                ) : (
                  inspectChunks
                    .filter((c) =>
                      inspectFilter
                        ? c.text
                            .toLowerCase()
                            .includes(inspectFilter.toLowerCase())
                        : true
                    )
                    .map((chunk) => (
                      <div
                        key={chunk.chunk_id}
                        className="p-4 rounded-xl bg-[var(--bg-surface)] border border-[var(--border-subtle)] space-y-2.5 text-xs shadow-xs hover:border-[var(--accent-border)]/50 transition-colors"
                      >
                        <div className="flex items-center justify-between text-[11px] font-mono-tech text-[var(--text-muted)] pb-2 border-b border-[var(--border-subtle)]/50">
                          <span className="font-semibold text-[var(--accent)] flex items-center gap-1.5">
                            <span className="px-1.5 py-0.5 rounded bg-[var(--accent-soft)] text-[var(--accent)]">
                              #{chunk.chunk_index + 1}
                            </span>
                            <span className="text-[var(--text-muted)] text-[10px]">
                              ({chunk.chunk_id.slice(0, 12)}...)
                            </span>
                          </span>
                          <div className="flex items-center gap-3">
                            <span>{chunk.char_count} chars</span>
                            <span>~{chunk.token_count} tokens</span>
                            <button
                              type="button"
                              onClick={() =>
                                copyChunk(chunk.chunk_id, chunk.text)
                              }
                              className="px-2 py-0.5 rounded text-[10.5px] font-medium bg-[var(--bg-panel)] text-[var(--text-secondary)] hover:text-[var(--text-primary)] border border-[var(--border-subtle)] transition-colors cursor-pointer"
                            >
                              {copiedChunkId === chunk.chunk_id
                                ? "✓ Copied"
                                : "Copy"}
                            </button>
                          </div>
                        </div>
                        <p className="text-[var(--text-primary)] leading-relaxed whitespace-pre-wrap font-sans text-xs select-text">
                          {chunk.text}
                        </p>
                      </div>
                    ))
                )}
              </div>

              {/* Drawer Footer */}
              <div className="p-4 border-t border-[var(--border-subtle)] bg-[var(--bg-surface)]/30 flex items-center justify-between text-xs font-mono-tech text-[var(--text-muted)]">
                <span
                  className="truncate max-w-xs"
                  title={selectedDoc.content_hash}
                >
                  SHA-256: {selectedDoc.content_hash.slice(0, 16)}...
                </span>
                <button
                  type="button"
                  onClick={() => setSelectedDoc(null)}
                  className="px-3 py-1.5 rounded-lg bg-[var(--bg-surface)] text-[var(--text-primary)] border border-[var(--border-subtle)] hover:border-[var(--accent-border)] transition-colors cursor-pointer text-xs font-sans font-medium"
                >
                  Close
                </button>
              </div>
            </div>
          </div>,
          document.body
        )}
    </AppShell>
  );
}
