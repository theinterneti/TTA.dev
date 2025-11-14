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

MIT (or as per TTA.dev repository)
