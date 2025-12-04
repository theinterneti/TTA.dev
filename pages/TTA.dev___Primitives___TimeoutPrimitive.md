type:: primitive
category:: Recovery
status:: documented
generated:: 2025-12-04

# TimeoutPrimitive

**Source:** `platform/primitives/src/tta_dev_primitives/recovery/timeout.py`

## Overview

Enforce execution timeout with optional fallback.

Prevents workflows from hanging indefinitely by enforcing time limits.
Essential for maintaining good UX and resource efficiency.

## Usage Example

```python
# Simple timeout
    workflow = TimeoutPrimitive(
        primitive=slow_operation,
        timeout_seconds=30.0
    )

    # Timeout with fallback
    workflow = TimeoutPrimitive(
        primitive=expensive_llm_call,
        timeout_seconds=30.0,
        fallback=cached_response_primitive
    )

    # Timeout with monitoring
    workflow = TimeoutPrimitive(
        primitive=critical_operation,
        timeout_seconds=45.0,
        fallback=degraded_service,
        track_timeouts=True
    )
```

## Related

- [[TTA.dev/Primitives]] - Primitives index
- [[TTA.dev/Primitives/Recovery]] - Recovery primitives
