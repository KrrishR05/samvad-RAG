# SAMVAD Benchmarks

This directory stores benchmark results and benchmark runner scripts.

## Planned Structure

```
benchmarks/
├── README.md           ← This file
├── results/            ← JSON/CSV benchmark output (gitignored, populated by runner)
│   └── .gitkeep
└── runner.py           ← Future benchmark runner script
```

## Benchmark Requirements

All benchmark values must be based on **actual pipeline executions**, never hardcoded or invented.

### Metrics Collected

| Metric              | Description                                      |
|----------------------|--------------------------------------------------|
| `stt_ms`             | Speech-to-text latency                           |
| `query_processing_ms`| Query analysis and preprocessing                 |
| `embedding_ms`       | Query embedding generation                       |
| `retrieval_ms`       | Vector search / BM25 retrieval                   |
| `reranking_ms`       | Cross-encoder reranking                          |
| `generation_ms`      | LLM answer generation                            |
| `guardrail_ms`       | Guardrail check execution                        |
| `total_ms`           | End-to-end pipeline latency                      |

### Percentile Targets

- **P50** — Median latency
- **P70** — 70th percentile
- **P100** — Maximum observed latency

### Performance Target

The HHG requirement specifies a **sub-200 ms pipeline performance target** where applicable under defined benchmark conditions.

This target has NOT been achieved yet — it will be validated once the full pipeline is implemented and benchmarked.

## Integration Points

- Latency recording: `backend/app/schemas/analytics.py → LatencyRecord`
- Percentile computation: `backend/app/analytics/percentiles.py`
- Metrics store: `backend/app/analytics/metrics.py → MetricsStore`
- Analytics API: `GET /api/v1/analytics/summary`, `GET /api/v1/analytics/latency`
