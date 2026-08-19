/**
 * SAMVAD API Types
 *
 * These types mirror the backend Pydantic schemas.
 * Keep in sync with backend/app/schemas/*.py
 */

// ─── Enums ───

export type QueryStatus =
  | "processing"
  | "completed"
  | "abstained"
  | "error"
  | "not_implemented";

export type ConfidenceLevel = "high" | "medium" | "low" | "insufficient";

export type PipelineStage =
  | "idle"
  | "listening"
  | "transcribing"
  | "validating"
  | "query_analysis"
  | "retrieving"
  | "reranking"
  | "confidence_check"
  | "generating"
  | "grounding_check"
  | "complete"
  | "error"
  | "retrying"
  | "fallback"
  | "abstained";

export type StageStatus =
  | "pending"
  | "active"
  | "completed"
  | "error"
  | "skipped"
  | "abstained";

// ─── Request Models ───

export interface QueryRequest {
  query: string;
  request_id?: string;
  language?: string;
}

export interface VoiceQueryRequest {
  audio: Blob;
  request_id?: string;
  language?: string;
}

// ─── Response Models ───

export interface Source {
  source_id: string;
  passage_id?: string | null;
  text: string;
  metadata: Record<string, unknown>;
  retrieval_score?: number | null;
  reranker_score?: number | null;
}

export interface Confidence {
  score?: number | null;
  level?: ConfidenceLevel | null;
}

export interface LatencyBreakdown {
  stt_ms?: number | null;
  query_processing_ms?: number | null;
  embedding_ms?: number | null;
  retrieval_ms?: number | null;
  reranking_ms?: number | null;
  generation_ms?: number | null;
  guardrail_ms?: number | null;
  total_ms?: number | null;
}

export interface QueryResponse {
  request_id: string;
  status: QueryStatus;
  transcript?: string | null;
  answer?: string | null;
  grounded?: boolean | null;
  confidence?: Confidence | null;
  sources: Source[];
  latency?: LatencyBreakdown | null;
  message?: string | null;
}

export interface HealthResponse {
  status: string;
  service: string;
  version: string;
  environment: string;
}

// ─── Analytics Models ───

export interface PercentileStats {
  p50?: number;
  p70?: number;
  p100?: number;
  mean?: number;
  min?: number;
  max?: number;
  count: number;
}

export interface StageLatencyStats {
  stt?: PercentileStats;
  query_processing?: PercentileStats;
  embedding?: PercentileStats;
  retrieval?: PercentileStats;
  reranking?: PercentileStats;
  generation?: PercentileStats;
  guardrail?: PercentileStats;
  total?: PercentileStats;
}

export interface AnalyticsSummaryResponse {
  total_requests: number;
  stage_latency?: StageLatencyStats;
  message?: string;
}

export interface LatencyStatsResponse {
  total_records: number;
  overall?: PercentileStats;
  by_stage?: StageLatencyStats;
  message?: string;
}

// ─── Error Response ───

export interface ApiError {
  status: "error";
  error: {
    code: string;
    message: string;
  };
  request_id?: string;
}
