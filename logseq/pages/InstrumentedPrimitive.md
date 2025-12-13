# InstrumentedPrimitive
alias:: [[TTA.dev/Primitives/InstrumentedPrimitive]]
type:: [[Primitive]]
category:: [[Observability]]

---

> **📍 Canonical Page:** [[TTA.dev/Primitives/InstrumentedPrimitive]]

This is an alias page for backward compatibility. All content is at the canonical location above.

---

## Quick Reference

```python
from tta_dev_primitives.observability import InstrumentedPrimitive

class MyPrimitive(InstrumentedPrimitive[dict, dict]):
    async def _execute_internal(self, input_data: dict, context: WorkflowContext) -> dict:
        # Your logic here - automatically traced!
        return {"result": "processed"}
```

**Import:** `from tta_dev_primitives.observability import InstrumentedPrimitive`
**Source:** `platform/primitives/src/tta_dev_primitives/observability/instrumented_primitive.py`


---
**Logseq:** [[TTA.dev/Logseq/Pages/Instrumentedprimitive]]
