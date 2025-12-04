# SequentialPrimitive
alias:: [[TTA.dev/Primitives/SequentialPrimitive]]
type:: [[Primitive]]
category:: [[Core Workflow]]

---

> **📍 Canonical Page:** [[TTA.dev/Primitives/SequentialPrimitive]]

This is an alias page for backward compatibility. All content is at the canonical location above.

---

## Quick Reference

```python
from tta_dev_primitives import SequentialPrimitive

# Using >> operator (preferred)
workflow = step1 >> step2 >> step3
result = await workflow.execute(input_data, context)
```

**Import:** `from tta_dev_primitives import SequentialPrimitive`
**Source:** `platform/primitives/src/tta_dev_primitives/core/sequential.py`
