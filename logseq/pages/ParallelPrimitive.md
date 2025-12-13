# ParallelPrimitive
alias:: [[TTA.dev/Primitives/ParallelPrimitive]]
type:: [[Primitive]]
category:: [[Core Workflow]]

---

> **📍 Canonical Page:** [[TTA.dev/Primitives/ParallelPrimitive]]

This is an alias page for backward compatibility. All content is at the canonical location above.

---

## Quick Reference

```python
from tta_dev_primitives import ParallelPrimitive

# Using | operator (preferred)
workflow = branch1 | branch2 | branch3
results = await workflow.execute(input_data, context)
# Returns: [result1, result2, result3]
```

**Import:** `from tta_dev_primitives import ParallelPrimitive`
**Source:** `platform/primitives/src/tta_dev_primitives/core/parallel.py`


---
**Logseq:** [[TTA.dev/Logseq/Pages/Parallelprimitive]]
