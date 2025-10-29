# TTA Dev Observability

Observability and tracing extensions for TTA development primitives.

## Features

- **W3C Trace Context Propagation**: Seamless distributed tracing across workflow primitives
- **Instrumented Primitives**: Auto-instrumented base classes with built-in observability
- **Context Extraction**: Extract and inject trace context from WorkflowContext
- **Graceful Degradation**: Works with or without OpenTelemetry installed

## Installation

```bash
# Basic installation
uv pip install -e packages/tta-dev-observability

# With OpenTelemetry tracing support
uv pip install -e "packages/tta-dev-observability[tracing]"
```

## Quick Start

### Inject Trace Context

```python
from tta_dev_primitives.core.base import WorkflowContext
from tta_dev_observability.context.propagation import inject_trace_context

# At workflow entry point (e.g., HTTP handler)
context = WorkflowContext(workflow_id="process-123")
context = inject_trace_context(context)  # Injects current span info

# Now context.trace_id and context.span_id are populated
```

### Create Instrumented Primitives

```python
from tta_dev_observability.instrumentation.base import InstrumentedPrimitive
from tta_dev_primitives.core.base import WorkflowContext

class MyPrimitive(InstrumentedPrimitive[dict, dict]):
    async def _execute_impl(self, input_data: dict, context: WorkflowContext) -> dict:
        # Your logic here - tracing is automatic
        return {"result": "success"}

# Use like any other primitive
primitive = MyPrimitive(name="my-operation")
result = await primitive.execute({"query": "test"}, context)
```

## Features

### Trace Context Propagation

The package provides functions to inject and extract W3C Trace Context:

- `inject_trace_context(context)` - Inject current OpenTelemetry span into WorkflowContext
- `extract_trace_context(context)` - Extract SpanContext from WorkflowContext
- `create_linked_span(tracer, name, context)` - Create span linked to context

### InstrumentedPrimitive

Base class that automatically adds:

- Distributed tracing with parent-child relationships
- Structured logging with correlation IDs
- Exception tracking in spans
- Execution metrics (duration, success/failure)

## Development

```bash
# Install dependencies
cd packages/tta-dev-observability
uv sync --all-extras

# Run tests
uv run pytest -v

# Format code
uv run ruff format .
```

## License

MIT License
