type:: primitive
category:: Recovery
status:: documented
generated:: 2025-12-04

# RetryPrimitive

**Source:** `platform/primitives/src/tta_dev_primitives/recovery/retry.py`

## Overview

Retry a primitive with exponential backoff.

## Usage Examples

```python
workflow = RetryPrimitive(
        risky_primitive,
        strategy=RetryStrategy(max_retries=3, backoff_base=2.0)
    )
```

## Tips & Gotchas

- ⚠️ Set appropriate `max_retries` to avoid infinite loops
- 💡 Use `jitter=True` to prevent thundering herd
- 📝 Only retries on transient errors by default

## Related

- [[TTA.dev/Primitives]] - Primitives index
- [[TTA.dev/Primitives/Recovery]] - Recovery primitives
