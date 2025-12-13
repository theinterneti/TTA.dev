type:: primitive
category:: Core
status:: documented
generated:: 2025-12-04

# SwitchPrimitive

**Source:** `platform/primitives/src/tta_dev_primitives/core/conditional.py`

## Overview

Multi-way conditional branching primitive.

## Usage Examples

```python
workflow = SwitchPrimitive(
        selector=lambda input, ctx: input.get("intent"),
        cases={
            "explore": explore_primitive,
            "combat": combat_primitive,
            "dialogue": dialogue_primitive,
        },
        default=generic_primitive
    )
```

## Related

- [[TTA.dev/Primitives]] - Primitives index
- [[TTA.dev/Primitives/Core]] - Core primitives


---
**Logseq:** [[TTA.dev/_archive/Logseq_backup/Pages_root/Tta.dev___primitives___switchprimitive]]
