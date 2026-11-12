# SAMVAD Ingestion Module

This directory will contain the MSMARCO-XI dataset ingestion pipeline.

## Planned Responsibilities

1. **Dataset Download** — Fetch MSMARCO-XI from AI4Bharat via HuggingFace `datasets`.
2. **Schema Inspection** — Inspect actual dataset columns before making assumptions.
3. **Preprocessing** — Clean and normalise text across languages.
4. **Chunking** — Apply configurable chunking strategies:
   - Whole-passage / fixed-size
   - Semantic chunking
   - Sliding window with overlap
   - Metadata-aware chunking
5. **Embedding** — Generate embeddings using the configured model.
6. **Indexing** — Build FAISS / Qdrant vector indexes.
7. **Persistence** — Store processed chunks and indexes to disk.

## Integration Points

- Chunk metadata schema: `backend/app/schemas/pipeline.py → ChunkMetadata`
- Retrieval interface: `backend/app/pipeline/interfaces.py → Retriever`
- Config: `backend/app/core/config.py → dataset_cache_dir, vector_db_path, embedding_model`

## Notes

- Do NOT hardcode MSMARCO-XI column names before inspecting the actual dataset.
- Support multilingual content and metadata.
- All offline processing (chunking, embedding, indexing) should be runnable
  independently of the API server.
