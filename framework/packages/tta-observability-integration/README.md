# TTA.dev Observability Integration

Comprehensive observability and monitoring integration for the TTA.dev toolkit.

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

See `docs/` directory for complete documentation:
- `specs/observability-integration.md` - Complete specification
- `docs/OBSERVABILITY_INTEGRATION_PROGRESS.md` - Implementation progress
- `docs/OBSERVABILITY_PACKAGE_EXPORT_PLAN.md` - Export plan

## Testing

```bash
# Run tests
uv run pytest tests/

# Run with coverage
uv run pytest tests/ --cov=src --cov-report=html
```

## License

MIT License - see [LICENSE](../../LICENSE) for details
