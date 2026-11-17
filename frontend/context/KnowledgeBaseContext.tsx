"use client";

import React, {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useRef,
  useState,
} from "react";
import type {
  ChunkStrategy,
  DocumentRecord,
  DocumentUploadResponse,
  PipelineStatusResponse,
} from "@/types/api";
import {
  deleteDocument,
  getPipelineStatus,
  listDocuments,
  uploadDocument,
} from "@/lib/api/client";
import { useAuth } from "@/context/AuthContext";

const PIPELINE_STATUS_CACHE_KEY = "samvad_pipeline_status_cache_v1";

export const DEFAULT_PIPELINE_STATUS: PipelineStatusResponse = {
  retrieval_ready: false,
  indexed_documents: 0,
  indexed_chunks: 0,
  available_strategies: ["dense", "hybrid", "lexical"],
  embedding_provider: "local-tfidf-svd-128",
  embedding_dimension: 128,
  llm_configured: true,
  llm_provider: "gemini",
  llm_model: "gemini-3.5-flash-lite",
  reranker_configured: true,
  stt_configured: true,
  guardrails_configured: true,
};

interface KnowledgeBaseContextType {
  documents: DocumentRecord[];
  totalDocuments: number;
  totalChunks: number;
  pipelineStatus: PipelineStatusResponse | null;
  isLoading: boolean;
  isLoaded: boolean;
  error: string | null;
  refresh: (silent?: boolean) => Promise<void>;
  upload: (
    file: File,
    options?: {
      language?: string;
      chunkStrategy?: ChunkStrategy;
      chunkSize?: number;
      chunkOverlap?: number;
    }
  ) => Promise<DocumentUploadResponse>;
  remove: (docId: string) => Promise<boolean>;
}

const KnowledgeBaseContext = createContext<KnowledgeBaseContextType | undefined>(
  undefined
);

export function KnowledgeBaseProvider({
  children,
}: {
  children: React.ReactNode;
}) {
  const { user } = useAuth();
  const currentUserId = user?.id || "guest";

  const [documents, setDocuments] = useState<DocumentRecord[]>([]);
  const [totalChunks, setTotalChunks] = useState(0);
  const [pipelineStatus, setPipelineStatus] =
    useState<PipelineStatusResponse>(DEFAULT_PIPELINE_STATUS);
  const [isLoading, setIsLoading] = useState(true);
  const [isLoaded, setIsLoaded] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const prevUserIdRef = useRef<string>(currentUserId);

  // Restore client-cached status on mount without SSR mismatch
  useEffect(() => {
    try {
      const cached = localStorage.getItem(PIPELINE_STATUS_CACHE_KEY);
      if (cached) {
        const parsed = JSON.parse(cached);
        // The cache is client-only state restored after mount.
        // eslint-disable-next-line react-hooks/set-state-in-effect
        setPipelineStatus(parsed);
      }
    } catch {}
  }, []);

  const fetchKnowledgeBase = useCallback(
    async (silent = false) => {
      if (!silent) {
        setIsLoading(true);
      }
      setError(null);
      try {
        const [docsRes, pipeRes] = await Promise.allSettled([
          listDocuments(),
          getPipelineStatus(),
        ]);

        if (docsRes.status === "fulfilled") {
          setDocuments(docsRes.value.documents);
          setTotalChunks(docsRes.value.total_chunks);
        } else {
          setError(
            docsRes.reason instanceof Error
              ? docsRes.reason.message
              : "Failed to load documents."
          );
        }

        if (pipeRes.status === "fulfilled") {
          setPipelineStatus(pipeRes.value);
          try {
            localStorage.setItem(
              PIPELINE_STATUS_CACHE_KEY,
              JSON.stringify(pipeRes.value)
            );
          } catch {}
        }
      } catch (err) {
        setError(
          err instanceof Error ? err.message : "Failed to load knowledge base."
        );
      } finally {
        setIsLoading(false);
        setIsLoaded(true);
      }
    },
    []
  );

  // Re-fetch whenever user changes (login, logout, switch user)
  useEffect(() => {
    if (prevUserIdRef.current !== currentUserId) {
      prevUserIdRef.current = currentUserId;
      // Reset documents for new user
      setDocuments([]);
      setTotalChunks(0);
      setIsLoaded(false);
    }
    // This effect synchronizes the knowledge base with the active user.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    void fetchKnowledgeBase(false);
  }, [currentUserId, fetchKnowledgeBase]);

  const upload = useCallback(
    async (
      file: File,
      options?: {
        language?: string;
        chunkStrategy?: ChunkStrategy;
        chunkSize?: number;
        chunkOverlap?: number;
      }
    ): Promise<DocumentUploadResponse> => {
      const res = await uploadDocument(file, options);
      // Background re-fetch to keep counts and status synchronized
      void fetchKnowledgeBase(true);
      return res;
    },
    [fetchKnowledgeBase]
  );

  const remove = useCallback(
    async (docId: string): Promise<boolean> => {
      // Optimistic removal from UI list
      setDocuments((prev) => prev.filter((d) => d.doc_id !== docId));
      try {
        await deleteDocument(docId);
        void fetchKnowledgeBase(true);
        return true;
      } catch (err) {
        // Rollback on failure
        void fetchKnowledgeBase(true);
        throw err;
      }
    },
    [fetchKnowledgeBase]
  );

  const totalDocuments = documents.length;

  return (
    <KnowledgeBaseContext.Provider
      value={{
        documents,
        totalDocuments,
        totalChunks,
        pipelineStatus,
        isLoading,
        isLoaded,
        error,
        refresh: fetchKnowledgeBase,
        upload,
        remove,
      }}
    >
      {children}
    </KnowledgeBaseContext.Provider>
  );
}

export function useKnowledgeBase() {
  const ctx = useContext(KnowledgeBaseContext);
  if (!ctx) {
    throw new Error(
      "useKnowledgeBase must be used within a KnowledgeBaseProvider"
    );
  }
  return ctx;
}
