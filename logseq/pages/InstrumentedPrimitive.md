# InstrumentedPrimitive

**Base class providing automatic observability for all TTA.dev primitives.**

## Overview

InstrumentedPrimitive is the foundational base class that provides automatic tracing, metrics, and logging for all workflow primitives in TTA.dev.

**Import:**
```python
from tta_dev_primitives.observability import InstrumentedPrimitive
```

## What It Provides

### 1. Automatic OpenTelemetry Tracing

Every primitive execution automatically creates spans:

```python
class MyPrimitive(InstrumentedPrimitive[Input, Output]):
    async def _execute_impl(self, input_data: Input, context: WorkflowContext) -> Output:
        # Span automatically created: "my_primitive.execute"
        return process(input_data)
```

### 2. Prometheus Metrics

Automatic metrics collection:

- `primitive_execution_duration_seconds` - Execution time
- `primitive_execution_total` - Total executions
- `primitive_execution_errors_total` - Failed executions

### 3. Structured Logging

Built-in logging with context:

```python
logger.info(
    "primitive_execution_complete",
    primitive=self.__class__.__name__,
    duration_ms=duration,
    status="success"
)
```

### 4. Context Propagation

- [[WorkflowContext]] automatically propagated
- Correlation IDs maintained
- Parent span context preserved

## Usage

### Creating Custom Primitives

```python
from tta_dev_primitives.observability import InstrumentedPrimitive
from tta_dev_primitives import WorkflowContext

class CustomPrimitive(InstrumentedPrimitive[dict, dict]):
    """My custom primitive with automatic observability."""

    async def _execute_impl(
        self,
        input_data: dict,
        context: WorkflowContext
    ) -> dict:
        # Your logic here
        # Tracing, metrics, logging all automatic
        result = await some_operation(input_data)
        return result
```

### Adding Custom Spans

```python
from opentelemetry import trace

class AdvancedPrimitive(InstrumentedPrimitive[dict, dict]):
    async def _execute_impl(self, input_data: dict, context: WorkflowContext) -> dict:
        # Automatic parent span already created

        tracer = trace.get_tracer(__name__)

        # Add child span for sub-operation
        with tracer.start_as_current_span("sub_operation") as span:
            span.set_attribute("input_size", len(input_data))
            result = await detailed_processing(input_data)
            span.add_event("processing_complete")

        return result
```

### Adding Custom Metrics

```python
from prometheus_client import Counter, Histogram

cache_hits = Counter("cache_hits_total", "Total cache hits")
query_duration = Histogram("query_duration_seconds", "Query duration")

class CachedPrimitive(InstrumentedPrimitive[dict, dict]):
    async def _execute_impl(self, input_data: dict, context: WorkflowContext) -> dict:
        if result := self.cache.get(input_data):
            cache_hits.inc()  # Custom metric
            return result

        with query_duration.time():  # Custom metric
            result = await expensive_query(input_data)

        return result
```

## Architecture

### Inheritance Hierarchy

```
InstrumentedPrimitive[TInput, TOutput]
  ↓
WorkflowPrimitive[TInput, TOutput]
  ↓
SequentialPrimitive, ParallelPrimitive, etc.
```

### Key Methods

```python
class InstrumentedPrimitive:
    async def execute(self, input_data: TInput, context: WorkflowContext) -> TOutput:
        """Public execute method with automatic instrumentation."""
        # 1. Start span
        # 2. Start metrics timer
        # 3. Log start
        # 4. Call _execute_impl()
        # 5. Log completion
        # 6. Record metrics
        # 7. End span
        # 8. Return result

    async def _execute_impl(self, input_data: TInput, context: WorkflowContext) -> TOutput:
        """Subclasses implement this - observability automatic."""
        raise NotImplementedError
```

## Observability Features

### Span Attributes

Automatically added to every span:

- `primitive.name` - Primitive class name
- `primitive.input_type` - Input data type
- `primitive.output_type` - Output data type
- `correlation_id` - From WorkflowContext
- `workflow_id` - From WorkflowContext

### Metrics Labels

Automatic labels on all metrics:

- `primitive_name` - Primitive class name
- `status` - success | error
- `error_type` - Exception class if failed

### Log Fields

Structured logging includes:

- `primitive` - Class name
- `correlation_id` - Request tracking
- `duration_ms` - Execution time
- `status` - success | error
- `input_size` - Input data size
- `output_size` - Output data size

## Benefits

### For Development

- ✅ No boilerplate observability code
- ✅ Consistent instrumentation
- ✅ Easy to add custom spans/metrics
- ✅ Type-safe context propagation

### For Production

- ✅ Distributed tracing out-of-box
- ✅ Performance metrics automatic
- ✅ Error tracking built-in
- ✅ Debug logs structured

### For Operations

- ✅ Grafana dashboards ready
- ✅ Prometheus metrics exported
- ✅ Jaeger traces viewable
- ✅ Log aggregation compatible

## Examples

### Basic Usage

See [[TTA.dev/Examples]] for working examples:

- `examples/basic_workflow.py` - Simple instrumented primitives
- `examples/observability.py` - Advanced tracing patterns

### Real-World Patterns

From [[PHASE3_EXAMPLES_COMPLETE]]:

- RAG workflow with full tracing
- Cost tracking with custom metrics
- Multi-agent coordination with spans

## Integration

### With tta-observability-integration

```python
from observability_integration import initialize_observability

# Initialize once at startup
initialize_observability(
    service_name="my-app",
    enable_prometheus=True
)

# All InstrumentedPrimitive instances automatically instrumented
```

### With Custom Exporters

```python
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

# Custom OTLP exporter
provider = TracerProvider()
provider.add_span_processor(
    BatchSpanProcessor(OTLPSpanExporter(endpoint="http://my-collector:4317"))
)
```

## Related Primitives

All TTA.dev primitives inherit from InstrumentedPrimitive:

- [[SequentialPrimitive]] - Sequential composition
- [[ParallelPrimitive]] - Parallel execution
- [[RouterPrimitive]] - Dynamic routing
- [[CachePrimitive]] - Caching
- [[RetryPrimitive]] - Retry logic

## Implementation

**Source:** `packages/tta-dev-primitives/src/tta_dev_primitives/observability/instrumented_primitive.py`

**Tests:** `packages/tta-dev-primitives/tests/test_instrumented_primitive.py`

## Related Documentation

- [[PRIMITIVES CATALOG]] - Complete primitive reference
- [[TTA.dev/Primitives]] - All primitives
- [[TTA.dev/Guides/Observability]] - Observability guide
- [[PHASE3_EXAMPLES_COMPLETE]] - Production examples

## External Resources

- OpenTelemetry Python: <https://opentelemetry.io/docs/languages/python/>
- Prometheus: <https://prometheus.io/docs/introduction/overview/>
- Grafana: <https://grafana.com/docs/>

## Tags

primitive:: base-class
type:: observability
feature:: tracing
feature:: metrics
feature:: logging
