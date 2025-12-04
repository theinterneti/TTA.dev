# ConditionalPrimitive
alias:: [[TTA.dev/Primitives/ConditionalPrimitive]]
type:: [[Primitive]]
category:: [[Core Workflow]]

---

> **📍 Canonical Page:** [[TTA.dev/Primitives/ConditionalPrimitive]]

This is an alias page for backward compatibility. All content is at the canonical location above.

---

## Quick Reference

```python
from tta_dev_primitives import ConditionalPrimitive

workflow = ConditionalPrimitive(
    condition=lambda data, ctx: len(data.get("text", "")) < 1000,
    then_primitive=fast_processor,
    else_primitive=slow_processor
)
```

**Import:** `from tta_dev_primitives import ConditionalPrimitive`
**Source:** `platform/primitives/src/tta_dev_primitives/core/conditional.py`
