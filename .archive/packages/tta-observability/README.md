# TTA Observability Integration

Comprehensive observability and monitoring integration for the TTA (Therapeutic Text Adventure) platform.

> **⚠️ IMPORTANT - LangFuse Integration Consolidation**
> The LangFuse integration previously in this package (`observability_integration.langfuse_integration`) has been **deprecated**.
> Use `tta_apm_langfuse` instead. See [LANGFUSE_CONSOLIDATION.md](../../docs/observability/LANGFUSE_CONSOLIDATION.md) for migration guide.

## Features

- **OpenTelemetry APM Integration**: Distributed tracing and metrics collection
- **Sampling Strategies**: Reduce overhead while maintaining visibility at scale
  - **ProbabilisticSampler**: Fixed-rate sampling with consistent hashing
  - **TailBasedSampler**: Always sample errors and slow requests
  - **AdaptiveSampler**: Dynamically adjust sampling based on system load
  - **CompositeSampler**: Combine multiple strategies with OR logic
- **RouterPrimitive**: Route to optimal LLM provider (30% cost savings)
- **CachePrimitive**: Cache LLM responses (40% cost savings)
- **TimeoutPrimitive**: Enforce timeouts (prevent hanging workflows)
- **LangFuse Integration**: Unified LLM observability (via `tta_apm_langfuse` package)

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

### Sampling for Production Scale

When running at scale (>100K req/day), use sampling to reduce overhead:

```python
from observability_integration import (
    ProbabilisticSampler,
    TailBasedSampler,
    AdaptiveSampler,
    CompositeSampler,
)

# Sample 10% of requests
basic_sampler = ProbabilisticSampler(sample_rate=0.1)

# Always sample errors and slow requests
tail_sampler = TailBasedSampler(
    always_sample_errors=True,
    always_sample_slow=True,
    slow_threshold_ms=1000.0,
)

# Dynamically adjust sampling based on load
adaptive_sampler = AdaptiveSampler(
    min_rate=0.01,  # Sample at least 1%
    max_rate=1.0,   # Sample up to 100%
    target_overhead=0.02,  # Target 2% overhead
    adjustment_interval=60.0,  # Adjust every 60 seconds
)

# Combine strategies: sample 10% baseline + all errors/slow requests
composite_sampler = CompositeSampler(
    strategies=[ProbabilisticSampler(0.1), tail_sampler]
)

# Use in your observability setup
decision = composite_sampler.should_sample(trace_id, {"has_error": False, "duration_ms": 250})
```
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

- `docs/guides/integration/observability-integration.md` – End-to-end observability integration documentation for TTA.dev

## Testing

```bash
# Run tests
uv run pytest tests/

# Run with coverage
uv run pytest tests/ --cov=src --cov-report=html
```

## License

MIT (or as per TTA.dev repository)
