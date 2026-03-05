# RetryPrimitive Specification

- **Version:** 1.3.0
- **Status:** Approved
- **Package:** tta-dev-primitives
- **Source:** `platform/primitives/src/tta_dev_primitives/recovery/retry.py`

## 1. Purpose

`RetryPrimitive` wraps another primitive and automatically retries it on failure using
configurable exponential backoff with jitter. It is the primary recovery primitive for
handling transient failures.

## 2. Contract

### 2.1 Type Signature

```python
@dataclass
class RetryStrategy:
    max_retries: int = 3
    backoff_base: float = 2.0
    max_backoff: float = 60.0
    jitter: bool = True

    def calculate_delay(self, attempt: int) -> float: ...


class RetryPrimitive(WorkflowPrimitive[Any, Any]):
    def __init__(
        self,
        primitive: WorkflowPrimitive,
        strategy: RetryStrategy | None = None,
    ): ...
```

### 2.2 Constructor Parameters

**RetryStrategy:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `max_retries` | `int` | `3` | Maximum number of retry attempts (total attempts = max_retries + 1) |
| `backoff_base` | `float` | `2.0` | Base for exponential backoff calculation |
| `max_backoff` | `float` | `60.0` | Maximum delay in seconds between retries |
| `jitter` | `bool` | `True` | Whether to add random jitter to delay |

**RetryPrimitive:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `primitive` | `WorkflowPrimitive` | *(required)* | The primitive to execute with retries |
| `strategy` | `RetryStrategy \| None` | `None` | Retry configuration; defaults to `RetryStrategy()` if None |

### 2.3 Behavior Invariants

- `execute()` MUST attempt the wrapped primitive up to `strategy.max_retries + 1` total times.
- On each failure, `execute()` MUST sleep for `strategy.calculate_delay(attempt)` seconds.
- `calculate_delay()` MUST compute `min(backoff_base ** attempt, max_backoff)`.
- If `jitter` is `True`, `calculate_delay()` MUST multiply the delay by `random.uniform(0, 1)`.
- If all attempts fail, `execute()` MUST re-raise the last exception.
- On success, `execute()` MUST return the result immediately without further retries.

### 2.4 Error Contract

| Condition | Exception | Description |
|-----------|-----------|-------------|
| All retries exhausted | *(last exception)* | The exception from the final attempt is re-raised |
| Wrapped primitive raises | *(caught per attempt)* | Each exception triggers a retry until exhausted |

### 2.5 Observability Contract

**Spans:**

| Span Name | Attributes | Description |
|-----------|------------|-------------|
| `retry.attempt_{i}` | `retry.attempt`, `retry.max_attempts`, `retry.primitive_type`, `retry.status`, `retry.succeeded_on_attempt`, `retry.error` | One span per attempt |

**Checkpoints:**

| Checkpoint | When |
|------------|------|
| `retry.start` | Before first attempt |
| `retry.attempt_{i}.start` | Before each attempt |
| `retry.attempt_{i}.end` | After each attempt |
| `retry.backoff_{i}.start` | Before each backoff sleep |
| `retry.backoff_{i}.end` | After each backoff sleep |
| `retry.end` | After final result or exhaustion |

**Metrics:** Per-attempt and per-backoff duration recorded via `metrics_collector.record_execution()`.

## 3. Composition Rules

- Standard `>>` and `|` operators apply.
- `RetryPrimitive(A) >> B` retries A, then passes result to B.
- `RetryPrimitive(A >> B)` retries the entire sequence A→B on any failure.

## 4. Edge Cases

| Input | Expected Behavior |
|-------|-------------------|
| `max_retries = 0` | Single attempt, no retries |
| `max_retries = -1` | Zero total attempts (effectively never executes) |
| Primitive succeeds on first try | Returns immediately, no backoff |
| `backoff_base = 0` | All delays are 0 seconds |
| `max_backoff = 0` | All delays capped at 0 seconds |

## 5. Cross-References

- [WorkflowPrimitive Spec](workflow-primitive.spec.md) — Base class
- [FallbackPrimitive Spec](fallback-primitive.spec.md) — Alternative recovery strategy
- [TimeoutPrimitive Spec](timeout-primitive.spec.md) — Often combined with Retry
- [Span Schema](../observability/span-schema.spec.md) — Span naming conventions
