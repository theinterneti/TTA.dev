# RetryPrimitive

type:: [[Primitive]]
category:: [[Recovery]]
package:: [[TTA.dev/Packages/tta-dev-primitives]]
status:: [[Stable]]
version:: 1.0.0
test-coverage:: 100
complexity:: [[Low]]
python-class:: `RetryPrimitive`
import-path:: `from tta_dev_primitives.recovery import RetryPrimitive`
related-primitives:: [[TTA.dev/Primitives/FallbackPrimitive]], [[TTA.dev/Primitives/TimeoutPrimitive]]

---

## Overview

- id:: retry-primitive-overview
  Automatically retry failed operations with configurable backoff strategies. Essential for handling transient failures in distributed systems.

  **Think of it as:** A smart wrapper that says "if at first you don't succeed, try, try again" - but with exponential backoff and jitter.

---

## Use Cases

- id:: retry-primitive-use-cases
  - **API calls:** Retry failed HTTP requests (network glitches, rate limits)
  - **Database operations:** Retry failed queries (connection timeouts, deadlocks)
  - **LLM calls:** Retry on rate limits or temporary service issues
  - **File I/O:** Retry on temporary file system errors
  - **Message queues:** Retry failed message processing
  - **External services:** Handle any transient failures gracefully

---

## Key Benefits

- id:: retry-primitive-benefits
  - ✅ **Automatic retries** - No manual retry logic needed
  - ✅ **Configurable strategies** - Constant, linear, exponential backoff
  - ✅ **Jitter support** - Avoid thundering herd problem
  - ✅ **Max retry limit** - Prevent infinite loops
  - ✅ **Exception filtering** - Only retry specific exceptions
  - ✅ **Built-in observability** - Track retry attempts and success rate
  - ✅ **Composable** - Wrap any primitive with retry logic

---

## API Reference

- id:: retry-primitive-api

### Constructor

```python
RetryPrimitive(
    primitive: WorkflowPrimitive[T, U],
    max_retries: int = 3,
    backoff_strategy: str = "exponential",
    initial_delay: float = 1.0,
    max_delay: float = 60.0,
    jitter: bool = True,
    retryable_exceptions: tuple[type[Exception], ...] | None = None
)
```

**Parameters:**

- `primitive`: The primitive to wrap with retry logic
- `max_retries`: Maximum number of retry attempts (default: 3)
- `backoff_strategy`: "constant", "linear", or "exponential" (default: "exponential")
- `initial_delay`: Initial delay in seconds (default: 1.0)
- `max_delay`: Maximum delay between retries (default: 60.0)
- `jitter`: Add random jitter to backoff (default: True)
- `retryable_exceptions`: Tuple of exception types to retry (None = retry all)

**Returns:** A new `RetryPrimitive` instance

---

## Backoff Strategies

- id:: retry-backoff-strategies

### Constant Backoff

```python
# Always wait the same amount
RetryPrimitive(
    primitive=api_call,
    backoff_strategy="constant",
    initial_delay=2.0
)
# Delays: 2s, 2s, 2s, ...
```

### Linear Backoff

```python
# Delay increases linearly
RetryPrimitive(
    primitive=api_call,
    backoff_strategy="linear",
    initial_delay=1.0
)
# Delays: 1s, 2s, 3s, 4s, ...
```

### Exponential Backoff (Recommended)

```python
# Delay doubles each time
RetryPrimitive(
    primitive=api_call,
    backoff_strategy="exponential",
    initial_delay=1.0
)
# Delays: 1s, 2s, 4s, 8s, 16s, ...
```

### Exponential with Jitter (Best Practice)

```python
# Exponential + random jitter (prevents thundering herd)
RetryPrimitive(
    primitive=api_call,
    backoff_strategy="exponential",
    initial_delay=1.0,
    jitter=True
)
# Delays: ~1s, ~2s (±random), ~4s (±random), ...
```

---

## Examples

### Basic API Retry

- id:: retry-basic-example

```python
{{embed ((standard-imports))}}
from tta_dev_primitives.recovery import RetryPrimitive

# Unreliable API call
async def unreliable_api(data, context):
    response = await call_external_api(data["endpoint"])
    return response

api_primitive = LambdaPrimitive(unreliable_api)

# Wrap with retry logic
reliable_api = RetryPrimitive(
    primitive=api_primitive,
    max_retries=3,
    backoff_strategy="exponential",
    initial_delay=1.0,
    jitter=True
)

context = WorkflowContext(correlation_id="api-call-001")
result = await reliable_api.execute(
    input_data={"endpoint": "/users/123"},
    context=context
)

# Automatically retries up to 3 times with exponential backoff
```

### LLM with Rate Limit Handling

- id:: retry-llm-rate-limits

```python
from openai import RateLimitError

# Only retry on rate limits
llm_call = LambdaPrimitive(lambda data, ctx: call_gpt4(data))

resilient_llm = RetryPrimitive(
    primitive=llm_call,
    max_retries=5,  # More retries for rate limits
    backoff_strategy="exponential",
    initial_delay=2.0,
    max_delay=120.0,
    retryable_exceptions=(RateLimitError,)  # Only retry rate limits
)

# Will retry on RateLimitError, but not on other errors
result = await resilient_llm.execute(input_data=prompt, context=context)
```

### Database Operation Retry

- id:: retry-database-operations

```python
from sqlalchemy.exc import OperationalError

# Retry database operations
db_query = LambdaPrimitive(lambda data, ctx: execute_query(data["sql"]))

resilient_query = RetryPrimitive(
    primitive=db_query,
    max_retries=3,
    backoff_strategy="exponential",
    initial_delay=0.5,
    retryable_exceptions=(OperationalError, TimeoutError)
)

result = await resilient_query.execute(
    input_data={"sql": "SELECT * FROM users WHERE id = ?"},
    context=context
)
```

---

## Composition Patterns

- id:: retry-composition-patterns

### Retry + Timeout

```python
from tta_dev_primitives.recovery import TimeoutPrimitive

# Timeout each attempt, retry on timeout
timeout_call = TimeoutPrimitive(slow_api, timeout_seconds=5.0)

retry_workflow = RetryPrimitive(
    primitive=timeout_call,
    max_retries=3,
    backoff_strategy="exponential"
)

# Each retry has 5-second timeout
```

### Retry + Fallback

```python
from tta_dev_primitives.recovery import FallbackPrimitive

# Try with retry, fallback if all retries fail
primary = RetryPrimitive(expensive_api, max_retries=3)

workflow = FallbackPrimitive(
    primary=primary,
    fallbacks=[cheap_api, cached_response]
)

# Retries expensive_api 3 times, then tries fallbacks
```

### Sequential with Retry

```python
# Add retry to specific steps
workflow = (
    input_validator >>
    RetryPrimitive(api_fetcher, max_retries=3) >>  # Retry this step
    data_processor >>
    RetryPrimitive(db_writer, max_retries=2) >>    # Retry this step
    output_formatter
)
```

---

## Exception Filtering

- id:: retry-exception-filtering

### Retry All Exceptions (Default)

```python
# Retries on any exception
RetryPrimitive(
    primitive=api_call,
    max_retries=3
)
```

### Retry Specific Exceptions Only

```python
# Only retry network and timeout errors
RetryPrimitive(
    primitive=api_call,
    max_retries=3,
    retryable_exceptions=(
        ConnectionError,
        TimeoutError,
        HTTPError
    )
)

# Other exceptions (ValueError, etc.) will raise immediately
```

### Don't Retry Certain Errors

```python
# Retry everything except client errors
from requests.exceptions import HTTPError

def is_retryable(exc):
    if isinstance(exc, HTTPError):
        # Don't retry 4xx errors (client errors)
        return exc.response.status_code >= 500
    return True

# Custom retry logic via exception filtering
```

---

## Best Practices

- id:: retry-best-practices

✅ **Use exponential backoff** - Prevents overwhelming failing service
✅ **Enable jitter** - Avoids thundering herd problem
✅ **Set max_delay** - Prevent extremely long waits
✅ **Filter exceptions** - Only retry transient errors
✅ **Limit max_retries** - Avoid infinite loops (3-5 is typical)
✅ **Monitor retry rates** - High retry rate indicates problems
✅ **Combine with timeout** - Prevent hanging on slow operations

❌ **Don't retry indefinitely** - Always set max_retries
❌ **Don't retry client errors** - 4xx errors won't succeed on retry
❌ **Don't use constant backoff** - Can overload failing service
❌ **Don't retry without jitter** - Can cause thundering herd
❌ **Don't retry non-idempotent operations** - Unless you handle duplicates

---

## Related Content

### Works Well With

- [[TTA.dev/Primitives/TimeoutPrimitive]] - Timeout each retry attempt
- [[TTA.dev/Primitives/FallbackPrimitive]] - Fallback after retries exhausted
- [[TTA.dev/Primitives/CircuitBreakerPrimitive]] - Stop retrying if service is down
- [[TTA.dev/Primitives/SequentialPrimitive]] - Retry specific steps

### Used In Examples

{{query (and [[Example]] [[RetryPrimitive]])}}

### Referenced By

{{query (and (mentions [[TTA.dev/Primitives/RetryPrimitive]]))}}

---

## Performance Impact

- id:: retry-performance-impact

### Success Case

- **No retries:** Same performance as wrapped primitive
- **Overhead:** ~1-2ms for retry logic

### Failure Case

- **With retries:** Total time = sum of all retry delays + execution times
- **Example:** 3 retries with exponential backoff (1s, 2s, 4s) = ~7s + execution time

### Best Case vs. Worst Case

```python
# Best case: Success on first try
# Time: ~100ms (API call)

# Worst case: 3 retries, all fail
# Time: 100ms + 1s + 100ms + 2s + 100ms + 4s = ~7.3s
```

---

## Testing

### Example Test

```python
import pytest
from tta_dev_primitives.recovery import RetryPrimitive
from tta_dev_primitives import WorkflowContext
from tta_dev_primitives.testing import MockPrimitive

@pytest.mark.asyncio
async def test_retry_success_after_failures():
    # Mock that fails twice, then succeeds
    call_count = 0

    async def flaky_operation(data, context):
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise ConnectionError("Temporary failure")
        return "success"

    primitive = LambdaPrimitive(flaky_operation)

    # Wrap with retry
    retry_workflow = RetryPrimitive(
        primitive=primitive,
        max_retries=5,
        backoff_strategy="constant",
        initial_delay=0.01  # Fast for testing
    )

    # Execute
    context = WorkflowContext(correlation_id="test-001")
    result = await retry_workflow.execute(input_data="test", context=context)

    # Verify: Failed twice, succeeded on third attempt
    assert result == "success"
    assert call_count == 3
```

---

## Observability

### Tracing

Retry attempts create spans:

```
workflow_execution (parent span)
└── retry_execution (span)
    ├── attempt: 1 (failed)
    ├── attempt: 2 (failed)
    └── attempt: 3 (success)
```

### Metrics

- `retry.attempts_total` - Total retry attempts
- `retry.success_rate` - Success rate after retries
- `retry.exhausted_count` - Times all retries exhausted
- `retry.backoff_duration` - Time spent waiting

### Logging

```python
# Structured logs for each retry
logger.warning(
    "retry_attempt",
    attempt=2,
    max_retries=3,
    exception="ConnectionError",
    next_delay_seconds=2.0
)
```

---

## Metadata

**Source Code:** [retry.py](https://github.com/theinterneti/TTA.dev/blob/main/packages/tta-dev-primitives/src/tta_dev_primitives/recovery/retry.py)
**Tests:** [test_retry.py](https://github.com/theinterneti/TTA.dev/blob/main/packages/tta-dev-primitives/tests/test_retry.py)
**Examples:** [error_handling_patterns.py](https://github.com/theinterneti/TTA.dev/blob/main/packages/tta-dev-primitives/examples/error_handling_patterns.py)

**Created:** [[2025-10-30]]
**Last Updated:** [[2025-10-30]]
**Test Coverage:** 100%
**Status:** [[Stable]] - Production Ready


---
**Logseq:** [[TTA.dev/_archive/Nested_copies/Framework/Logseq/Pages/Tta.dev___primitives___retryprimitive]]
