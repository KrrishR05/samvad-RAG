/**
 * SAMVAD Demo Data
 *
 * ⚠️ DEVELOPMENT / DEMO ONLY
 * This data is used exclusively for visual development and UI testing.
 * It must NOT be presented as real AI-generated results.
 *
 * When the RAG pipeline is connected, all demo data should be removed
 * from production views.
 */

import type { QueryResponse } from "@/types/api";

export const DEMO_ANSWERED_RESPONSE: QueryResponse = {
  request_id: "demo-001",
  status: "completed",
  transcript: "What is the capital of Karnataka?",
  answer:
    "Based on the available knowledge base, Bengaluru (formerly Bangalore) is the capital city of Karnataka, India. It serves as the administrative and legislative capital of the state.",
  grounded: true,
  confidence: { score: 0.92, level: "high" },
  sources: [
    {
      source_id: "demo-src-1",
      passage_id: "doc-4521",
      text: "Bengaluru is the capital and largest city of the Indian state of Karnataka.",
      metadata: { language: "en", chunk_strategy: "whole_passage" },
      retrieval_score: 0.96,
      reranker_score: 0.94,
    },
    {
      source_id: "demo-src-2",
      passage_id: "doc-4522",
      text: "Karnataka is a state in the south-western region of India with its capital Bengaluru.",
      metadata: { language: "en", chunk_strategy: "semantic" },
      retrieval_score: 0.89,
      reranker_score: 0.87,
    },
  ],
  latency: {
    stt_ms: 120,
    query_processing_ms: 8,
    embedding_ms: 15,
    retrieval_ms: 22,
    reranking_ms: 18,
    generation_ms: 45,
    guardrail_ms: 5,
    total_ms: 148,
  },
};

export const DEMO_ABSTAINED_RESPONSE: QueryResponse = {
  request_id: "demo-002",
  status: "abstained",
  transcript: "What will the weather be like tomorrow?",
  answer: null,
  grounded: null,
  confidence: { score: 0.12, level: "insufficient" },
  sources: [],
  message:
    "I couldn't find enough reliable information in the available knowledge base to answer that confidently.",
};

/**
 * Flag to distinguish demo data from real responses.
 * Components should check this before rendering.
 */
export const IS_DEMO_DATA = true;
