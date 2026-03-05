# FallbackPrimitive Specification

- **Version:** 1.3.0
- **Status:** Approved
- **Package:** tta-dev-primitives
- **Source:** `platform/primitives/src/tta_dev_primitives/recovery/fallback.py`

## 1. Purpose

`FallbackPrimitive` provides graceful degradation by attempting a primary primitive and,
on failure, executing an alternative fallback primitive. It is the primary recovery primitive
for providing alternative execution paths.

## 2. Contract

### 2.1 Type Signature

```python
class FallbackPrimitive(WorkflowPrimitive[Any, Any]):
    def __init__(
        self,
        primary: WorkflowPrimitive,
        fallback: WorkflowPrimitive,
    ): ...
```

### 2.2 Constructor Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `primary` | `WorkflowPrimitive` | *(required)* | Primary primitive to attempt first |
| `fallback` | `WorkflowPrimitive` | *(required)* | Alternative primitive if primary fails |

### 2.3 Behavior Invariants

- `execute()` MUST attempt the `primary` primitive first.
- If `primary` succeeds, `execute()` MUST return its result immediately.
- If `primary` raises any exception, `execute()` MUST attempt the `fallback` primitive.
- If `fallback` succeeds, `execute()` MUST return its result.
- If both `primary` and `fallback` fail, `execute()` MUST re-raise the original primary exception.
- The fallback primitive MUST receive the same `input_data` as the primary.

### 2.4 Error Contract

| Condition | Exception | Description |
|-----------|-----------|-------------|
| Primary succeeds | *(none)* | Returns primary result |
| Primary fails, fallback succeeds | *(none)* | Returns fallback result |
| Both fail | *(primary exception)* | The original primary exception is re-raised |

### 2.5 Observability Contract

**Spans:**

| Span Name | Attributes | Description |
|-----------|------------|-------------|
| `fallback.primary` | `fallback.execution`, `fallback.primary_type`, `fallback.status`, `fallback.error` | Span for primary attempt |
| `fallback.fallback` | `fallback.execution`, `fallback.fallback_type`, `fallback.status`, `fallback.used_fallback`, `fallback.primary_error` | Span for fallback attempt |

**Checkpoints:**

| Checkpoint | When |
|------------|------|
| `fallback.start` | Before primary attempt |
| `fallback.primary.start` | Before primary executes |
| `fallback.primary.end` | After primary completes or fails |
| `fallback.fallback.start` | Before fallback executes (only on primary failure) |
| `fallback.fallback.end` | After fallback completes or fails |
| `fallback.end` | After final result or exhaustion |

**Metrics:** Primary and fallback duration recorded via `metrics_collector.record_execution()`.

## 3. Composition Rules

- Standard `>>` and `|` operators apply.
- `FallbackPrimitive(A, B) >> C` — tries A, falls back to B, then passes result to C.
- Often combined with `RetryPrimitive`: `RetryPrimitive(A, strategy) >> FallbackPrimitive(B, C)`.

## 4. Edge Cases

| Input | Expected Behavior |
|-------|-------------------|
| Primary and fallback are the same primitive | Valid; primary is tried, then the same primitive is tried again |
| Primary raises `KeyboardInterrupt` | Exception propagates (not a standard Exception subclass) |
| Fallback modifies `context.state` | Modifications are visible to subsequent primitives |

## 5. Cross-References

- [WorkflowPrimitive Spec](workflow-primitive.spec.md) — Base class
- [RetryPrimitive Spec](retry-primitive.spec.md) — Alternative recovery strategy
- [TimeoutPrimitive Spec](timeout-primitive.spec.md) — Often combined with Fallback
- [Span Schema](../observability/span-schema.spec.md) — Span naming conventions
