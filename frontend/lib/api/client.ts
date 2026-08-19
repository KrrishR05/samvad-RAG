/**
 * SAMVAD API Client
 *
 * Typed API functions for communicating with the backend.
 * All fetch calls are centralised here — components should
 * never make raw fetch requests.
 */

import type {
  AnalyticsSummaryResponse,
  HealthResponse,
  LatencyStatsResponse,
  QueryRequest,
  QueryResponse,
} from "@/types/api";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// ─── Helpers ───

async function request<T>(
  path: string,
  options?: RequestInit
): Promise<T> {
  const url = `${API_BASE}${path}`;
  const res = await fetch(url, {
    headers: { "Content-Type": "application/json", ...options?.headers },
    ...options,
  });

  if (!res.ok) {
    const body = await res.json().catch(() => null);
    throw new ApiClientError(
      body?.error?.message || `Request failed: ${res.status}`,
      res.status,
      body?.error?.code
    );
  }

  return res.json() as Promise<T>;
}

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

// ─── API Functions ───

export async function healthCheck(): Promise<HealthResponse> {
  return request<HealthResponse>("/health");
}

export async function submitTextQuery(
  body: QueryRequest
): Promise<QueryResponse> {
  return request<QueryResponse>("/api/v1/query", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export async function submitVoiceQuery(
  audio: Blob,
  requestId?: string,
  language?: string
): Promise<QueryResponse> {
  const formData = new FormData();
  formData.append("audio", audio, "recording.webm");
  if (requestId) formData.append("request_id", requestId);
  if (language) formData.append("language", language);

  const url = `${API_BASE}/api/v1/voice/query`;
  const res = await fetch(url, {
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

export async function getAnalyticsSummary(): Promise<AnalyticsSummaryResponse> {
  return request<AnalyticsSummaryResponse>("/api/v1/analytics/summary");
}

export async function getLatencyStats(): Promise<LatencyStatsResponse> {
  return request<LatencyStatsResponse>("/api/v1/analytics/latency");
}
