# Observability Guide

Deep reference for OpenTelemetry integration patterns in TTA.dev.

## Packages

| Package | Purpose |
|---------|---------|
| `tta-observability-integration` | Core OpenTelemetry integration |
| `tta-dev-primitives` (instrumented) | `InstrumentedPrimitive` base class |

## Tracing

All primitives that extend `InstrumentedPrimitive` automatically emit OpenTelemetry spans.

```python
from opentelemetry import trace

tracer = trace.get_tracer(__name__)

with tracer.start_as_current_span("my-operation") as span:
    span.set_attribute("workflow.id", context.workflow_id)
    result = await primitive.execute(data, context)
```

## Metrics

Key metrics tracked:

| Metric | Type | Description |
|--------|------|-------------|
| `workflow.duration` | Histogram | End-to-end workflow execution time |
| `workflow.success_count` | Counter | Successful workflow completions |
| `workflow.failure_count` | Counter | Failed workflow executions |
| `primitive.retry_count` | Counter | Number of retries per primitive |
| `cache.hit_rate` | Gauge | Cache hit/miss ratio |

## Context Propagation

`WorkflowContext` carries tracing context through primitive chains:

```python
context = WorkflowContext(
    workflow_id="demo",
    correlation_id="req-123",
)
# Context propagates through >> and | operators
result = await (step1 >> step2 >> step3).execute(data, context)
```

## Configuration

Environment variables for observability:

```bash
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317
OTEL_SERVICE_NAME=tta-dev
OTEL_TRACES_SAMPLER=parentbased_traceidratio
OTEL_TRACES_SAMPLER_ARG=1.0
```

## Key Files

- **Observability package:** `platform/observability/src/observability_integration/`
- **Instrumented base:** `platform/primitives/src/tta_dev_primitives/core/instrumented.py`
- **Spec references:** `docs/reference/specs/observability/`
