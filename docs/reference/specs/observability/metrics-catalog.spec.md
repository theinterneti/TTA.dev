# Metrics Catalog Specification

- **Version:** 1.0.0
- **Status:** Approved
- **Package:** tta-dev-primitives (observability module)
- **Source:** `platform/primitives/src/tta_dev_primitives/observability/`

## 1. Purpose

This specification catalogs all metrics emitted by TTA.dev primitives, covering both
OpenTelemetry (OTel) metrics and Prometheus metrics. It defines metric names, types,
labels, and descriptions as the contract for dashboards and alerting.

## 2. OpenTelemetry Metrics

Source: `observability/metrics_v2.py`

| Metric Name | Type | Labels | Description |
|-------------|------|--------|-------------|
| `primitive.execution.count` | Counter | `primitive.name`, `primitive.type`, `execution.status`, `agent.type`, `error.type` | Total primitive executions |
| `primitive.execution.duration` | Histogram | `primitive.name`, `primitive.type`, `execution.status`, `agent.type`, `error.type` | Execution latency in milliseconds |
| `primitive.connection.count` | Counter | `source.primitive`, `target.primitive`, `connection.type` | Service map connections between primitives |
| `llm.tokens.total` | Counter | `llm.provider`, `llm.model_name`, `llm.token_type` | Total LLM tokens consumed |
| `cache.hits` | Counter | `primitive.name`, `cache.type` | Cache hit count |
| `cache.total` | Counter | `primitive.name`, `cache.type` | Total cache operations |
| `agent.workflows.active` | UpDownCounter | `agent.type` | Currently active workflows (gauge-like) |

**Histogram Buckets for `primitive.execution.duration`:**
`[10, 50, 100, 250, 500, 1000, 2500, 5000, 10000]` (milliseconds)

## 3. Prometheus Metrics

Source: `observability/prometheus_metrics.py`

| Metric Name | Type | Labels | Unit | Description |
|-------------|------|--------|------|-------------|
| `tta_workflow_executions_total` | Counter | `workflow_name`, `status`, `job` | 1 | Total workflow executions |
| `tta_primitive_executions_total` | Counter | `primitive_type`, `primitive_name`, `status`, `job` | 1 | Total primitive executions |
| `tta_llm_cost_total` | Counter | `model`, `provider`, `job` | USD | Cumulative LLM API costs |
| `tta_execution_duration_seconds` | Histogram | `primitive_type`, `job` | seconds | Primitive execution duration |
| `tta_cache_hits_total` | Counter | `primitive_name`, `cache_type`, `job` | 1 | Cache hits |
| `tta_cache_misses_total` | Counter | `primitive_name`, `cache_type`, `job` | 1 | Cache misses |

**Histogram Buckets for `tta_execution_duration_seconds`:**
`[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0]` (seconds)

## 4. Basic Metrics (In-Memory)

Source: `observability/metrics.py`

These metrics are always available, even without OpenTelemetry or Prometheus.

| Property | Type | Description |
|----------|------|-------------|
| `total_executions` | Counter | Total executions across all primitives |
| `successful_executions` | Counter | Successful executions |
| `failed_executions` | Counter | Failed executions |
| `total_duration_ms` | Accumulator | Sum of all execution durations |
| `min_duration_ms` | Gauge | Minimum observed execution duration |
| `max_duration_ms` | Gauge | Maximum observed execution duration |
| `error_counts` | Counter dict | Error counts keyed by exception type |
| `success_rate` | Derived | `successful / total * 100` (0.0 if no executions) |
| `average_duration_ms` | Derived | `total_duration / total` (0.0 if no executions) |

## 5. Label Value Conventions

| Label | Valid Values | Description |
|-------|-------------|-------------|
| `execution.status` | `"success"`, `"error"` | Execution outcome |
| `primitive.type` | Class name (e.g., `"RetryPrimitive"`) | Python class name |
| `connection.type` | `"sequential"`, `"parallel"` | Composition type |
| `llm.token_type` | `"input"`, `"output"`, `"total"` | Token category |
| `cache.type` | `"memory"`, `"redis"`, `"lru"` | Cache backend type |
| `status` | `"success"`, `"error"`, `"timeout"` | General status |

## 6. Behavior Invariants

- All metric recording MUST be conditional on the metrics library being available.
- If `prometheus_client` is not installed, Prometheus metrics MUST degrade silently.
- If `opentelemetry` is not installed, OTel metrics MUST degrade silently.
- Basic in-memory metrics MUST always be available with zero external dependencies.
- Metric recording MUST NOT raise exceptions that affect primitive execution.
- Counter metrics MUST only increase (never decrease or reset during runtime).
- Histogram metrics MUST use the defined bucket boundaries.

## 7. Cross-References

- [Span Schema](span-schema.spec.md) — Companion span specification
- [Context Propagation](context-propagation.spec.md) — Trace context propagation
- [CachePrimitive Spec](../primitives/cache-primitive.spec.md) — Cache hit/miss source
- [RetryPrimitive Spec](../primitives/retry-primitive.spec.md) — Per-attempt metrics
