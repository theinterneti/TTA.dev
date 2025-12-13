type:: primitive
category:: Observability
status:: documented
generated:: 2025-12-04

# InstrumentedPrimitive

**Source:** `platform/primitives/src/tta_dev_primitives/observability/instrumented_primitive.py`

## Overview

Base class for workflow primitives with automatic OpenTelemetry instrumentation.

## Usage Examples

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


---
**Logseq:** [[TTA.dev/_archive/Logseq_backup/Pages_root/Tta.dev___primitives___instrumentedprimitive]]
