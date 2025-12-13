type:: primitive
category:: Recovery
status:: documented
generated:: 2025-12-04

# SagaPrimitive

**Source:** `platform/primitives/src/tta_dev_primitives/recovery/compensation.py`

## Overview

Saga pattern: Execute with compensation on failure.

## Usage Examples

```python
workflow = SagaPrimitive(
        forward=update_world_state,
        compensation=rollback_world_state
    )
```

## Related

- [[TTA.dev/Primitives]] - Primitives index
- [[TTA.dev/Primitives/Recovery]] - Recovery primitives


---
**Logseq:** [[TTA.dev/_archive/Logseq_backup/Pages_root/Tta.dev___primitives___sagaprimitive]]
