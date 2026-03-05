# TimeoutPrimitive Specification

- **Version:** 1.3.0
- **Status:** Approved
- **Package:** tta-dev-primitives
- **Source:** `platform/primitives/src/tta_dev_primitives/recovery/timeout.py`

## 1. Purpose

`TimeoutPrimitive` enforces a maximum execution time on a wrapped primitive. If the
primitive does not complete within the specified duration, it is cancelled and either
a fallback is executed or a `TimeoutError` is raised.

## 2. Contract

### 2.1 Type Signature

```python
class TimeoutError(Exception):
    """Raised when a primitive exceeds its timeout and no fallback is configured."""
    pass


class TimeoutPrimitive(WorkflowPrimitive[Any, Any]):
    def __init__(
        self,
        primitive: WorkflowPrimitive,
        timeout_seconds: float,
        fallback: WorkflowPrimitive | None = None,
        track_timeouts: bool = True,
    ): ...
```

### 2.2 Constructor Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `primitive` | `WorkflowPrimitive` | *(required)* | Primitive to execute with timeout |
| `timeout_seconds` | `float` | *(required)* | Maximum execution time in seconds |
| `fallback` | `WorkflowPrimitive \| None` | `None` | Optional primitive to execute on timeout |
| `track_timeouts` | `bool` | `True` | Whether to track timeout events in `context.state` |

### 2.3 Behavior Invariants

- `execute()` MUST use `asyncio.wait_for()` to enforce the timeout.
- If the primitive completes within `timeout_seconds`, `execute()` MUST return its result.
- If the primitive exceeds `timeout_seconds` and `fallback` is set, `execute()` MUST execute the fallback.
- If the primitive exceeds `timeout_seconds` and `fallback` is `None`, `execute()` MUST raise `TimeoutError`.
- If `track_timeouts` is `True`, on timeout `execute()` MUST:
  - Increment `context.state["timeout_count"]` (initializing to 0 if absent).
  - Append a record to `context.state["timeout_history"]` containing `primitive_type`, `timeout_seconds`, and `timestamp`.

### 2.4 Error Contract

| Condition | Exception | Description |
|-----------|-----------|-------------|
| Timeout exceeded, no fallback | `TimeoutError` | Custom exception from `timeout.py` |
| Timeout exceeded, fallback fails | *(fallback exception)* | Exception from the fallback propagates |
| Wrapped primitive raises before timeout | *(propagated)* | Non-timeout exceptions propagate immediately |

### 2.5 Observability Contract

**Logging:**

| Event | Level | Fields |
|-------|-------|--------|
| `timeout_success` | INFO | Primitive completed within timeout |
| `timeout_exceeded` | WARNING | Primitive exceeded timeout |
| `executing_fallback` | INFO | Fallback is being executed |

**State tracking:** `context.state["timeout_count"]` and `context.state["timeout_history"]`.

## 3. Composition Rules

- Standard `>>` and `|` operators apply.
- `TimeoutPrimitive(A, 30) >> B` — A must complete in 30s, then result passes to B.
- Common pattern: `TimeoutPrimitive(RetryPrimitive(A), 60)` — retry with overall timeout.

## 4. Edge Cases

| Input | Expected Behavior |
|-------|-------------------|
| `timeout_seconds = 0` | Immediate timeout; fallback or `TimeoutError` |
| `timeout_seconds` is negative | Behavior undefined (depends on `asyncio.wait_for`) |
| Primitive completes exactly at timeout | Race condition; may succeed or timeout |
| `track_timeouts = False` | No state modifications on timeout |

## 5. Cross-References

- [WorkflowPrimitive Spec](workflow-primitive.spec.md) — Base class
- [RetryPrimitive Spec](retry-primitive.spec.md) — Often combined with Timeout
- [FallbackPrimitive Spec](fallback-primitive.spec.md) — Alternative to timeout fallback
- [Span Schema](../observability/span-schema.spec.md) — Span naming conventions
