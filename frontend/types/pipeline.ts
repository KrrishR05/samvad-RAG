/**
 * SAMVAD Pipeline Types
 *
 * Types for the pipeline visualization component.
 */

import type { PipelineStage, StageStatus } from "./api";

export interface PipelineStageInfo {
  id: PipelineStage;
  label: string;
  description: string;
  status: StageStatus;
  durationMs?: number;
  error?: string;
}

export const PIPELINE_STAGES: PipelineStageInfo[] = [
  {
    id: "listening",
    label: "Listening",
    description: "Capturing voice input",
    status: "pending",
  },
  {
    id: "transcribing",
    label: "Transcribing",
    description: "Converting speech to text",
    status: "pending",
  },
  {
    id: "validating",
    label: "Validating",
    description: "Checking input quality",
    status: "pending",
  },
  {
    id: "retrieving",
    label: "Retrieving Context",
    description: "Searching knowledge base",
    status: "pending",
  },
  {
    id: "reranking",
    label: "Reranking",
    description: "Scoring candidate relevance",
    status: "pending",
  },
  {
    id: "generating",
    label: "Generating Response",
    description: "Creating grounded answer",
    status: "pending",
  },
  {
    id: "grounding_check",
    label: "Verifying Evidence",
    description: "Checking answer grounding",
    status: "pending",
  },
];
