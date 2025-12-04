# WorkflowPrimitive
alias:: [[TTA.dev/Primitives/WorkflowPrimitive]]
type:: [[Primitive]]
category:: [[Core]]

---

> **📍 Canonical Page:** [[TTA.dev/Primitives/WorkflowPrimitive]]

This is an alias page for backward compatibility. All content is at the canonical location above.

---

## Quick Reference

```python
from tta_dev_primitives import WorkflowPrimitive, WorkflowContext

class MyPrimitive(WorkflowPrimitive[str, dict]):
    async def execute(self, input_data: str, context: WorkflowContext) -> dict:
        return {"result": input_data.upper()}

# Composition operators
workflow = step1 >> step2   # Sequential
workflow = step1 | step2    # Parallel
```

**Import:** `from tta_dev_primitives import WorkflowPrimitive`
**Source:** `platform/primitives/src/tta_dev_primitives/core/base.py`
