type:: primitive
category:: Core
status:: documented
generated:: 2025-12-04

# WorkflowPrimitive

**Source:** `platform/primitives/src/tta_dev_primitives/core/base.py`

## Overview

Base class for composable workflow primitives.

## Usage Examples

```python
workflow = primitive1 >> primitive2 >> primitive3
    result = await workflow.execute(input_data, context)
```

## Related

- [[TTA.dev/Primitives]] - Primitives index
- [[TTA.dev/Primitives/Core]] - Core primitives


---
**Logseq:** [[TTA.dev/Logseq/Pages/Tta.dev___primitives___workflowprimitive]]
