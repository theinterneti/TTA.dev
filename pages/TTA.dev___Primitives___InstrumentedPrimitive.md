type:: primitive
category:: Observability
status:: documented
generated:: 2025-12-04

# InstrumentedPrimitive

**Source:** `platform/primitives/src/tta_dev_primitives/observability/instrumented_primitive.py`

## Overview

Base class for workflow primitives with automatic OpenTelemetry instrumentation.

Automatically creates spans, injects trace context, and adds observability
metadata for all primitive executions. Subclasses implement `_execute_impl()`
instead of `execute()`.

Features:
- Automatic span creation with proper parent-child relationships
- Trace context injection from active OpenTelemetry spans
- Span attributes from WorkflowContext metadata
- Graceful degradation when OpenTelemetry unavailable
- Timing and checkpoint tracking

## Usage Example

```python
class MyPrimitive(InstrumentedPrimitive[dict, str]):
        async def _execute_impl(self, input_data: dict, context: WorkflowContext) -> str:
            # Your implementation here
            return f"Processed: {input_data}"

    # Usage
    primitive = MyPrimitive(name="my_processor")
    context = WorkflowContext(workflow_id="demo")
    result = await primitive.execute({"key": "value"}, context)
    # Automatically creates span "primitive.my_processor" with trace context
```

## Related

- [[TTA.dev/Primitives]] - Primitives index
- [[TTA.dev/Primitives/Observability]] - Observability primitives
