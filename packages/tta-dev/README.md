# tta-dev

**TTA.dev Platform - Unified API for composable AI workflow primitives.**

This package provides a single, coherent entry point for TTA.dev's production-ready
workflow primitives. It re-exports the most commonly used primitives from the
underlying packages, with optional extras for observability and multi-agent context.

## Installation

```bash
# Core primitives only (minimal dependencies)
pip install tta-dev
# or: uv add tta-dev

# With observability (OpenTelemetry, Prometheus, Redis)
pip install tta-dev[observability]

# With agent context (multi-agent workflows)
pip install tta-dev[context]

# Full platform (all packages)
pip install tta-dev[all]
```

## Quick Start

```python
from tta_dev import (
    WorkflowContext,
    SequentialPrimitive,
    ParallelPrimitive,
    RetryPrimitive,
    CachePrimitive,
)

# Build composable workflows using operators
workflow = step1 >> step2 >> step3  # Sequential (>>)
parallel = branch1 | branch2        # Parallel (|)

# Execute with context
context = WorkflowContext(workflow_id="my-workflow")
result = await workflow.execute(input_data, context)
```

## Layered Architecture

`tta-dev` is a façade over three focused packages:

| Package | Purpose | Installed By |
|---------|---------|--------------|
| `tta-dev-primitives` | Core workflow primitives | Always (base dependency) |
| `tta-observability-integration` | OpenTelemetry, metrics | `tta-dev[observability]` |
| `universal-agent-context` | Multi-agent coordination | `tta-dev[context]` |

### Core Primitives (always available)

- `WorkflowContext` - Correlation IDs, tracing, shared state
- `WorkflowPrimitive` - Base class for all primitives
- `SequentialPrimitive` - Chain steps with `>>`
- `ParallelPrimitive` - Run in parallel with `|`
- `ConditionalPrimitive` - Branching logic
- `RetryPrimitive` / `RetryStrategy` - Retry with backoff
- `TimeoutPrimitive` - Enforce timeouts
- `CachePrimitive` - TTL caching
- `CompensationPrimitive` - Saga/rollback patterns
- `MockPrimitive` - Testing utilities

### Observability (optional)

```python
from tta_dev import (
    initialize_observability,
    ObservableRouterPrimitive,
    ObservableCachePrimitive,
    ObservableTimeoutPrimitive,
)

# Initialize OpenTelemetry
initialize_observability(service_name="my-app", enable_prometheus=True)

# Use observability-enhanced primitives
router = ObservableRouterPrimitive(routes={"fast": llm1, "quality": llm2})
```

### Agent Context (optional)

```python
from tta_dev import (
    AgentHandoffPrimitive,
    AgentMemoryPrimitive,
    AgentCoordinationPrimitive,
)

# Coordinate multiple agents
coordination = AgentCoordinationPrimitive(agents=[agent1, agent2])
```

## Checking Availability

```python
from tta_dev import observability_available, context_available

if observability_available():
    from tta_dev import initialize_observability
    initialize_observability(service_name="my-app")

if context_available():
    from tta_dev import AgentHandoffPrimitive
    # Use agent coordination
```

## Documentation

- [Getting Started](../../GETTING_STARTED.md)
- [Primitives Catalog](../../PRIMITIVES_CATALOG.md)
- [Architecture Overview](../../docs/architecture/Overview.md)

## License

MIT

