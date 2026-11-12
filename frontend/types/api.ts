/**
 * SAMVAD API Types
 *
 * Mirrors the backend Pydantic schemas in backend/app/schemas/*.py
 * and backend/app/api/routes_documents.py.
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

export type RetrieverStrategy = "hybrid" | "dense" | "lexical";

export type ChunkStrategy =
  | "sliding_window"
  | "fixed_size"
  | "semantic"
  | "whole_passage";

export type DocumentStatus = "uploaded" | "processed" | "indexed" | "failed";

// ─── Request Models ───

export interface QueryRequest {
  query: string;
  request_id?: string;
  language?: string;
  retriever_strategy?: RetrieverStrategy;
  top_k?: number;
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

export interface StageResult {
  stage: PipelineStage;
  status: StageStatus;
  duration_ms?: number | null;
  output?: unknown;
  error?: string | null;
  retries: number;
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
  stages?: StageResult[];
  retrieval_method?: string | null;
  message?: string | null;
}

export interface HealthResponse {
  status: string;
  service: string;
  version: string;
  environment: string;
}

// ─── Document & Pipeline Status Models ───

export interface DocumentRecord {
  doc_id: string;
  filename: string;
  content_hash: string;
  media_type: string;
  language?: string | null;
  status: DocumentStatus;
  error_message?: string | null;
  chunk_count: number;
  created_at: string;
  updated_at: string;
  metadata: Record<string, unknown>;
}

export interface DocumentUploadResponse {
  document: DocumentRecord;
  duplicate: boolean;
  total_chunks_indexed: number;
}

export interface DocumentListResponse {
  documents: DocumentRecord[];
  total_documents: number;
  total_chunks: number;
}

export interface DocumentDeleteResponse {
  doc_id: string;
  deleted: boolean;
  total_chunks_indexed: number;
}

export interface PipelineStatusResponse {
  retrieval_ready: boolean;
  indexed_documents: number;
  indexed_chunks: number;
  available_strategies: string[];
  embedding_provider: string;
  embedding_dimension: number;
  llm_configured: boolean;
  llm_provider?: string | null;
  llm_model?: string | null;
  reranker_configured: boolean;
  stt_configured: boolean;
  guardrails_configured: boolean;
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
