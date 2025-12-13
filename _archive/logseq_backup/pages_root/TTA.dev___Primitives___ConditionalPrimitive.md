type:: primitive
category:: Core
status:: documented
generated:: 2025-12-04

# ConditionalPrimitive

**Source:** `platform/primitives/src/tta_dev_primitives/core/conditional.py`

## Overview

Conditional branching primitive.

## Usage Examples

```python
workflow = ConditionalPrimitive(
        condition=lambda result, ctx: result.safety_level != "blocked",
        then_primitive=standard_narrative,
        else_primitive=safe_narrative
    )
```

## Related

- [[TTA.dev/Primitives]] - Primitives index
- [[TTA.dev/Primitives/Core]] - Core primitives


---
**Logseq:** [[TTA.dev/_archive/Logseq_backup/Pages_root/Tta.dev___primitives___conditionalprimitive]]
