type:: primitive
category:: Recovery
status:: documented
generated:: 2025-12-04

# RetryPrimitive

**Source:** `platform/primitives/src/tta_dev_primitives/recovery/retry.py`

## Overview

Retry a primitive with exponential backoff.

## Usage Example

```python
workflow = RetryPrimitive(
        risky_primitive,
        strategy=RetryStrategy(max_retries=3, backoff_base=2.0)
    )
```

## Related

- [[TTA.dev/Primitives]] - Primitives index
- [[TTA.dev/Primitives/Recovery]] - Recovery primitives
