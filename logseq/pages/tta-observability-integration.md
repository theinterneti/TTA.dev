type:: [[Package]]
path:: platform/observability
pypi:: tta-observability-integration
status:: production

# tta-observability-integration

OpenTelemetry integration for distributed tracing and metrics.

## Installation

```bash
uv add tta-observability-integration
```

## Features

- **Tracing** - Automatic span creation for primitives
- **Metrics** - Prometheus-compatible metrics export
- **Logging** - Structured JSON logging
- **Context Propagation** - Trace context across services

## Quick Example

```python
from tta_observability_integration import setup_tracing
from opentelemetry import trace

# Setup
setup_tracing(service_name="my-service")

# Traces are automatic with primitives
tracer = trace.get_tracer(__name__)
with tracer.start_as_current_span("operation") as span:
    result = await workflow.execute(data, context)
```

## Configuration

Environment variables:
- `OTEL_SERVICE_NAME` - Service name for traces
- `OTEL_EXPORTER_OTLP_ENDPOINT` - OTLP endpoint URL
- `OTEL_TRACES_SAMPLER` - Sampling strategy

## Metrics

Common metrics exposed:
- `primitive_execution_duration_seconds`
- `primitive_execution_total`
- `cache_hit_total`
- `cache_miss_total`
- `retry_attempt_total`

## Related
- [[tta-dev-primitives]] - Core primitives
- [[TTA.dev/Architecture]] - System design
