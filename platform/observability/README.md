# TTA Observability Integration

Comprehensive observability and monitoring integration for the TTA (Therapeutic Text Adventure) platform.

## Features

- **OpenTelemetry APM Integration**: Distributed tracing and metrics collection
- **RouterPrimitive**: Route to optimal LLM provider (30% cost savings)
- **CachePrimitive**: Cache LLM responses (40% cost savings)
- **TimeoutPrimitive**: Enforce timeouts (prevent hanging workflows)

## Installation

```bash
uv add tta-observability-integration
```

## Quick Start

```python
from observability_integration import initialize_observability
from observability_integration.primitives import (
    RouterPrimitive,
    CachePrimitive,
    TimeoutPrimitive,
)

# Initialize APM (call this early in main.py)
initialize_observability(
    service_name="tta",
    enable_prometheus=True,
    prometheus_port=9464
)

# Use primitives with observability
workflow = (
    RouterPrimitive(routes={"fast": llama, "premium": gpt4})
    >> CachePrimitive(narrative_gen, ttl_seconds=3600)
    >> TimeoutPrimitive(timeout_seconds=30)
)
```

## Working Examples

The `tta-dev-primitives` package includes **5 production-ready examples** showcasing observability integration:

### Recommended Examples

| Example | Features | Benefits |
|---------|----------|----------|
| [**agentic_rag_workflow.py**](../tta-dev-primitives/examples/agentic_rag_workflow.py) | Router, Cache, Validation | Production RAG pattern with automatic tracing |
| [**cost_tracking_workflow.py**](../tta-dev-primitives/examples/cost_tracking_workflow.py) | Budget enforcement, per-model metrics | Cost management with Prometheus integration |
| [**streaming_workflow.py**](../tta-dev-primitives/examples/streaming_workflow.py) | AsyncIterator, throughput metrics | Real-time monitoring of streaming responses |

### Key Features in Examples

- ✅ **Automatic Tracing**: Every primitive creates OpenTelemetry spans
- ✅ **Prometheus Metrics**: Hit rates, latencies, costs tracked automatically
- ✅ **Correlation IDs**: Full request tracing across distributed workflows
- ✅ **Graceful Degradation**: Works even if OpenTelemetry unavailable

**Implementation Guide:** See [PHASE3_EXAMPLES_COMPLETE.md](../../PHASE3_EXAMPLES_COMPLETE.md) for detailed patterns and InstrumentedPrimitive architecture.

## Documentation

This package ships with its own **specs** and **docs** directories:

- `specs/observability-integration.md` – Component specification for the observability integration
- `docs/OBSERVABILITY_INTEGRATION_PROGRESS.md` – Historical implementation progress log
- `docs/OBSERVABILITY_PACKAGE_EXPORT_PLAN.md` – Original export plan into TTA.dev

For the **current, repo-level integration guide**, also see:

- `docs/integration/observability-integration.md` – End-to-end observability integration documentation for TTA.dev

## Testing

```bash
# Run tests
uv run pytest tests/

# Run with coverage
uv run pytest tests/ --cov=src --cov-report=html
```

## License

MIT (or as per TTA.dev repository)


---
**Logseq:** [[TTA.dev/Platform/Observability/Readme]]
