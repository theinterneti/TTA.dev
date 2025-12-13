type:: primitive
category:: Recovery
status:: documented
generated:: 2025-12-04

# FallbackPrimitive

**Source:** `platform/primitives/src/tta_dev_primitives/recovery/fallback.py`

## Overview

Try a primitive with fallback to alternative.

## Usage Examples

```python
workflow = FallbackPrimitive(
        primary=openai_narrative,
        fallback=local_narrative
    )
```

## Related

- [[TTA.dev/Primitives]] - Primitives index
- [[TTA.dev/Primitives/Recovery]] - Recovery primitives


---
**Logseq:** [[TTA.dev/_archive/Logseq_backup/Pages_root/Tta.dev___primitives___fallbackprimitive]]
