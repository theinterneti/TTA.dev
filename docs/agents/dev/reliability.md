# Reliability Patterns Reference

## The rules

1. **Never write manual retry/timeout loops.** Use the primitives below.
2. **Build the workflow graph first, execute second.**
3. **Compose narrow — wrap one primitive with one concern.**

## Primitive quick reference

| Problem | Primitive | Import |
|---|---|---|
| Transient failure | `RetryPrimitive` | `ttadev.primitives.recovery.retry` |
| Hung call | `TimeoutPrimitive` | `ttadev.primitives.recovery.timeout` |
| Dead service | `CircuitBreakerPrimitive` | `ttadev.primitives.recovery.circuit_breaker_primitive` |
| Fallback chain | `FallbackPrimitive` | `ttadev.primitives.recovery.fallback` |
| Cache results | `CachePrimitive` | `ttadev.primitives.performance.cache` |

## RetryPrimitive

```python
from ttadev.primitives.recovery.retry import RetryPrimitive, RetryStrategy

workflow = RetryPrimitive(
    LambdaPrimitive(call_api),
    strategy=RetryStrategy(
        max_retries=3,
        backoff_base=2.0,        # 1s, 2s, 4s
        jitter=True,             # Prevents thundering herd
        retryable_exceptions=(httpx.HTTPError, TimeoutError),
    ),
)
```

Default strategy: 3 retries, exponential backoff from 1 s, jitter enabled.

## TimeoutPrimitive

```python
from ttadev.primitives.recovery.timeout import TimeoutPrimitive

workflow = TimeoutPrimitive(
    LambdaPrimitive(slow_operation),
    timeout_seconds=30.0,       # asyncio.wait_for under the hood
)
```

`TimeoutPrimitive` raises `asyncio.TimeoutError` on expiry. Compose with `RetryPrimitive`
to retry after timeout — **put Timeout inside Retry**:

```python
# ✅ Correct order: Retry wraps Timeout
workflow = RetryPrimitive(TimeoutPrimitive(op, seconds=10), max_retries=3)

# ❌ Wrong: Timeout wraps Retry — timeout fires on total time including retries
workflow = TimeoutPrimitive(RetryPrimitive(op, max_retries=3), seconds=10)
```

## CircuitBreakerPrimitive

```python
from ttadev.primitives.recovery.circuit_breaker_primitive import CircuitBreakerPrimitive

workflow = CircuitBreakerPrimitive(
    LambdaPrimitive(external_service),
    failure_threshold=5,         # Open after 5 consecutive failures
    recovery_timeout_seconds=60, # Try again after 60 s
    success_threshold=2,         # Close after 2 consecutive successes from HALF_OPEN
)
```

**State machine:** CLOSED → OPEN (on threshold) → HALF_OPEN (after timeout) → CLOSED (on success_threshold).
Note: `success_threshold` requires consecutive successes, not a single probe.

## FallbackPrimitive

```python
from ttadev.primitives.recovery.fallback import FallbackPrimitive

workflow = FallbackPrimitive(
    primary=GroqPrimitive(...),
    fallbacks=[OpenAIPrimitive(...), OllamaPrimitive(...)],
)
```

When both primary AND all fallbacks fail, `FallbackPrimitive` re-raises the **original
primary exception** — not the last fallback exception.

## CachePrimitive

```python
from ttadev.primitives.performance.cache import CachePrimitive

def cache_key(data: dict, ctx: WorkflowContext) -> str:
    return f"{data['prompt']}:{data['model']}"

workflow = CachePrimitive(
    LambdaPrimitive(call_llm),
    cache_key_fn=cache_key,
    ttl_seconds=3600.0,
    max_size=1000,
)
```

## Standard composition pattern

```python
from ttadev.primitives.core.base import WorkflowContext, LambdaPrimitive
from ttadev.primitives.recovery.retry import RetryPrimitive, RetryStrategy
from ttadev.primitives.recovery.timeout import TimeoutPrimitive
from ttadev.primitives.performance.cache import CachePrimitive

def build_workflow():
    return CachePrimitive(
        RetryPrimitive(
            TimeoutPrimitive(LambdaPrimitive(call_api), timeout_seconds=10.0),
            strategy=RetryStrategy(max_retries=3, backoff_base=2.0),
        ),
        cache_key_fn=lambda data, ctx: str(data),
        ttl_seconds=3600.0,
    )

async def main():
    workflow = build_workflow()
    ctx = WorkflowContext(workflow_id="my-task")
    result = await workflow.execute({"prompt": "hello"}, ctx)
```

## Anti-patterns

```python
# ❌ Manual retry loop
for attempt in range(3):
    try: result = await call()
    except: await asyncio.sleep(2 ** attempt)

# ❌ Bare except that swallows errors silently
try: result = await call()
except: pass

# ❌ No timeout on external I/O
result = await httpx.get(url)  # Hangs indefinitely

# ❌ Timeout wrapping Retry (see ordering note above)
TimeoutPrimitive(RetryPrimitive(op, max_retries=3), seconds=5)
```

## Testing reliability primitives

Use `MockPrimitive` with `side_effect` to simulate failures:

```python
from ttadev.primitives.testing.mocks import MockPrimitive

fail_twice_then_succeed = MockPrimitive(
    "flaky",
    side_effect=[ValueError("fail"), ValueError("fail"), {"ok": True}],
)
workflow = RetryPrimitive(fail_twice_then_succeed, max_retries=3)
result = await workflow.execute({}, ctx)
assert result == {"ok": True}
assert fail_twice_then_succeed.call_count == 3
```
