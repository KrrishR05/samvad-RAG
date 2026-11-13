/**
 * SAMVAD API Client
 *
 * Typed API functions for communicating with the FastAPI backend.
 * All fetch calls are centralised here.
 */

import type {
  AnalyticsSummaryResponse,
  ChunkStrategy,
  DocumentDeleteResponse,
  DocumentListResponse,
  DocumentUploadResponse,
  HealthResponse,
  LatencyStatsResponse,
  PipelineStatusResponse,
  QueryRequest,
  QueryResponse,
  RetrieverStrategy,
} from "@/types/api";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export class ApiClientError extends Error {
  constructor(
    message: string,
    public statusCode: number,
    public code?: string
  ) {
    super(message);
    this.name = "ApiClientError";
  }
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const url = `${API_BASE}${path}`;
  const res = await fetch(url, {
    headers: { "Content-Type": "application/json", ...options?.headers },
    ...options,
  });

  if (!res.ok) {
    const body = await res.json().catch(() => null);
    const detailMessage =
      body?.error?.message ||
      (typeof body?.detail === "string" ? body.detail : null) ||
      `Request failed: ${res.status}`;
    throw new ApiClientError(detailMessage, res.status, body?.error?.code);
  }

  return res.json() as Promise<T>;
}

// ─── Health & Status ───

export async function healthCheck(): Promise<HealthResponse> {
  return request<HealthResponse>("/health");
}

export async function getPipelineStatus(): Promise<PipelineStatusResponse> {
  return request<PipelineStatusResponse>("/api/v1/pipeline/status");
}

// ─── Query Endpoints ───

export async function submitTextQuery(body: QueryRequest): Promise<QueryResponse> {
  return request<QueryResponse>("/api/v1/query", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export async function submitVoiceQuery(
  audio: Blob,
  requestId?: string,
  language?: string,
  retrieverStrategy?: RetrieverStrategy,
  topK?: number
): Promise<QueryResponse> {
  const formData = new FormData();
  formData.append("audio", audio, "recording.webm");
  if (requestId) formData.append("request_id", requestId);
  if (language) formData.append("language", language);
  if (retrieverStrategy) formData.append("retriever_strategy", retrieverStrategy);
  if (topK !== undefined) formData.append("top_k", String(topK));

  const res = await fetch(`${API_BASE}/api/v1/voice/query`, {
    method: "POST",
    body: formData,
  });

  if (!res.ok) {
    const body = await res.json().catch(() => null);
    throw new ApiClientError(
      body?.error?.message || `Voice request failed: ${res.status}`,
      res.status,
      body?.error?.code
    );
  }

  return res.json() as Promise<QueryResponse>;
}

// ─── Document Management Endpoints ───

export async function listDocuments(): Promise<DocumentListResponse> {
  return request<DocumentListResponse>("/api/v1/documents");
}

export async function uploadDocument(
  file: File,
  options?: {
    language?: string;
    chunkStrategy?: ChunkStrategy;
    chunkSize?: number;
    chunkOverlap?: number;
  }
): Promise<DocumentUploadResponse> {
  const formData = new FormData();
  formData.append("file", file, file.name);
  if (options?.language) formData.append("language", options.language);
  if (options?.chunkStrategy) formData.append("chunk_strategy", options.chunkStrategy);
  if (options?.chunkSize) formData.append("chunk_size", String(options.chunkSize));
  if (options?.chunkOverlap !== undefined) {
    formData.append("chunk_overlap", String(options.chunkOverlap));
  }

  const res = await fetch(`${API_BASE}/api/v1/documents`, {
    method: "POST",
    body: formData,
  });

  if (!res.ok) {
    const body = await res.json().catch(() => null);
    throw new ApiClientError(
      body?.error?.message || `Upload failed: ${res.status}`,
      res.status,
      body?.error?.code
    );
  }

  return res.json() as Promise<DocumentUploadResponse>;
}

export async function deleteDocument(docId: string): Promise<DocumentDeleteResponse> {
  return request<DocumentDeleteResponse>(
    `/api/v1/documents/${encodeURIComponent(docId)}`,
    { method: "DELETE" }
  );
}

// ─── Analytics Endpoints ───

export async function getAnalyticsSummary(): Promise<AnalyticsSummaryResponse> {
  return request<AnalyticsSummaryResponse>("/api/v1/analytics/summary");
}

export async function getLatencyStats(): Promise<LatencyStatsResponse> {
  return request<LatencyStatsResponse>("/api/v1/analytics/latency");
}
