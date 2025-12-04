type:: primitive
category:: Recovery
status:: documented
generated:: 2025-12-04

# SagaPrimitive

**Source:** `platform/primitives/src/tta_dev_primitives/recovery/compensation.py`

## Overview

Saga pattern: Execute with compensation on failure.

Useful for maintaining consistency across distributed operations.

## Usage Example

```python
workflow = SagaPrimitive(
        forward=update_world_state,
        compensation=rollback_world_state
    )
```

## Related

- [[TTA.dev/Primitives]] - Primitives index
- [[TTA.dev/Primitives/Recovery]] - Recovery primitives
