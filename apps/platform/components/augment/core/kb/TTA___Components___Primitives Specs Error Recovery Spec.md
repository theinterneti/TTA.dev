---
title: Primitive Specification: Error Recovery
tags: #TTA
status: Active
repo: theinterneti/TTA
path: scripts/primitives/specs/error_recovery_spec.md
created: 2025-11-01
updated: 2025-11-01
---
# [[TTA/Components/Primitive Specification: Error Recovery]]

**Version:** 1.0
**Status:** Stable
**Location:** `scripts/primitives/error_recovery.py`

---

## Purpose

Automatic retry with exponential backoff and circuit breaker for transient failures in development operations.

---

## Contract

### Inputs

#### `with_retry` Decorator

**Parameters:**
- `config: RetryConfig | None` - Retry configuration
  - `max_retries: int = 3` - Maximum number of retry attempts
  - `base_delay: float = 1.0` - Base delay in seconds
  - `max_delay: float = 60.0` - Maximum delay in seconds
  - `exponential_base: float = 2.0` - Exponential backoff base
  - `jitter: bool = True` - Add random jitter to delays
- `fallback: Callable | None` - Optional fallback function to call if all retries fail

**Decorated Function:**
- Can be any callable with any signature
- Should raise exceptions on failure

#### `with_retry_async` Decorator

Same as `with_retry` but for async functions.

#### `CircuitBreaker` Class

**Constructor:**
- `failure_threshold: int = 5` - Number of failures before opening circuit
- `recovery_timeout: float = 60.0` - Seconds before attempting recovery
- `expected_exception: type = Exception` - Exception type to track

**Methods:**
- `call(func, *args, **kwargs)` - Call function through circuit breaker

### Outputs

#### `with_retry` / `with_retry_async`

**Returns:**
- Original function result if successful
- Fallback function result if all retries exhausted and fallback provided

**Raises:**
- Last exception if all retries exhausted and no fallback

**Side Effects:**
- Logs retry attempts with warnings
- Logs permanent failures with errors
- Logs fallback usage with info
- Sleeps between retry attempts

#### `CircuitBreaker`

**Returns:**
- Function result if circuit is CLOSED or HALF_OPEN and call succeeds

**Raises:**
- `CircuitBreakerOpenError` if circuit is OPEN
- Original exception if call fails

**State Transitions:**
- CLOSED → OPEN: After `failure_threshold` consecutive failures
- OPEN → HALF_OPEN: After `recovery_timeout` seconds
- HALF_OPEN → CLOSED: After successful call
- HALF_OPEN → OPEN: After failed call

### Guarantees

1. **Retry Only Transient Errors**
   - Network errors (connection, timeout)
   - Rate limit errors (429, "too many requests")
   - Transient errors (503, "unavailable")
   - Does NOT retry permanent errors

2. **Exponential Backoff with Jitter**
   - Delay = `min(base_delay * (exponential_base ^ attempt), max_delay)`
   - Jitter multiplies delay by random value in [0.5, 1.5]
   - Prevents thundering herd problem

3. **Comprehensive Logging**
   - All retry attempts logged with attempt number and delay
   - Permanent failures logged with error level
   - Fallback usage logged with info level

4. **Async Support**
   - `with_retry_async` provides same guarantees for async functions
   - Uses `asyncio.sleep` instead of `time.sleep`

5. **Circuit Breaker Protection**
   - Prevents cascading failures
   - Automatic recovery after timeout
   - Half-open state for testing recovery

### Error Classification

**Network Errors:**
- Keywords: "connection", "timeout", "network"
- Retry: YES

**Rate Limit Errors:**
- Keywords: "rate limit", "too many requests", "429"
- Retry: YES

**Resource Errors:**
- Keywords: "memory", "disk", "resource"
- Retry: NO (permanent)

**Transient Errors:**
- Keywords: "temporary", "unavailable", "503"
- Retry: YES

**Permanent Errors:**
- All other errors
- Retry: NO

---

## Usage Patterns

### Pattern 1: Simple Retry with Defaults

```python
from primitives.error_recovery import with_retry

@with_retry()
def flaky_api_call():
    # May fail transiently
    response = requests.get("https://api.example.com/data")
    response.raise_for_status()
    return response.json()
```

**Behavior:**
- Max 3 retries
- Exponential backoff: 1s, 2s, 4s
- Jitter applied
- Retries network/rate-limit/transient errors only

### Pattern 2: Custom Retry Configuration

```python
from primitives.error_recovery import with_retry, RetryConfig

@with_retry(RetryConfig(
    max_retries=5,
    base_delay=2.0,
    max_delay=30.0,
    exponential_base=2.0,
    jitter=True
))
def important_operation():
    # Critical operation with more retries
    pass
```

**Behavior:**
- Max 5 retries
- Exponential backoff: 2s, 4s, 8s, 16s, 30s (capped)
- Jitter applied

### Pattern 3: Retry with Fallback

```python
from primitives.error_recovery import with_retry

def use_cached_data():
    return {"data": "cached"}

@with_retry(fallback=use_cached_data)
def fetch_fresh_data():
    # Try to fetch fresh data
    response = requests.get("https://api.example.com/data")
    response.raise_for_status()
    return response.json()
```

**Behavior:**
- Retries up to 3 times
- If all retries fail, calls `use_cached_data()` instead
- Returns cached data instead of raising exception

### Pattern 4: Async Retry

```python
from primitives.error_recovery import with_retry_async
import aiohttp

@with_retry_async()
async def async_api_call():
    async with aiohttp.ClientSession() as session:
        async with session.get("https://api.example.com/data") as response:
            response.raise_for_status()
            return await response.json()
```

**Behavior:**
- Same as sync version but uses `asyncio.sleep`
- Works with async/await syntax

### Pattern 5: Circuit Breaker

```python
from primitives.error_recovery import CircuitBreaker

circuit_breaker = CircuitBreaker(
    failure_threshold=5,
    recovery_timeout=60.0
)

def call_external_service():
    return circuit_breaker.call(make_api_call)
```

**Behavior:**
- Opens circuit after 5 consecutive failures
- Rejects calls for 60 seconds
- Attempts recovery after timeout
- Closes circuit on successful recovery

---

## Integration Points

### With Development Scripts

```python
# scripts/dev_with_recovery.py
from primitives.error_recovery import with_retry, RetryConfig

@with_retry(RetryConfig(max_retries=3))
def run_quality_checks():
    # Linting, type checking, tests
    pass
```

### With CI/CD Workflows

```yaml
# .github/workflows/dev-with-error-recovery.yml
- name: Run tests with retry
  uses: nick-fields/retry@v2
  with:
    timeout_minutes: 10
    max_attempts: 3
    command: python scripts/dev_with_recovery.py test
```

### With Observability

```python
from primitives.error_recovery import with_retry
from observability.dev_metrics import track_execution

@track_execution("api_call_with_retry")
@with_retry()
def monitored_api_call():
    # Metrics track total time including retries
    pass
```

### With Context Management

```python
from primitives.error_recovery import with_retry
from .augment.context.conversation_manager import AIConversationContextManager

@with_retry()
def save_conversation_context(session_id):
    # Retry if file write fails transiently
    context_mgr.save_session(session_id)
```

---

## Performance Characteristics

### Time Complexity

- **Best Case:** O(1) - Single successful execution
- **Worst Case:** O(n) where n = max_retries
- **Average Case:** Depends on failure rate

### Space Complexity

- O(1) - No significant memory overhead
- Stores only current execution state

### Latency Impact

**Without Retries:**
- Single execution time

**With Retries (3 attempts, default config):**
- Best case: Same as without retries
- Worst case: Original time + (1s + 2s + 4s) = Original + 7s
- With jitter: Original + ~3.5s to ~10.5s

**Recommendation:** Use retries for operations where:
- Transient failures are common (>5%)
- Operation is idempotent
- Additional latency is acceptable

---

## Testing Considerations

### Unit Tests

```python
def test_retry_success_on_second_attempt():
    call_count = 0

    @with_retry()
    def flaky_function():
        nonlocal call_count
        call_count += 1
        if call_count < 2:
            raise ConnectionError("Transient failure")
        return "success"

    result = flaky_function()
    assert result == "success"
    assert call_count == 2
```

### Integration Tests

```python
def test_retry_with_real_api():
    @with_retry(RetryConfig(max_retries=3))
    def call_api():
        response = requests.get("https://httpbin.org/status/503")
        response.raise_for_status()

    with pytest.raises(requests.HTTPError):
        call_api()  # Should retry 3 times then fail
```

---

## Phase 2 Considerations

When integrating into TTA application:

### LLM API Calls

```python
@with_retry_async(RetryConfig(
    max_retries=5,
    base_delay=1.0,
    max_delay=60.0
))
async def call_llm_api(prompt: str):
    # Retry on rate limits, network errors
    response = await openai.ChatCompletion.create(...)
    return response
```

### Database Operations

```python
@with_retry(RetryConfig(max_retries=3))
def save_to_redis(key: str, value: str):
    # Retry on connection errors
    redis_client.set(key, value)
```

### Agent Orchestration

```python
@with_retry_async(fallback=use_cached_response)
async def agent_workflow_step(context):
    # Retry with fallback to cached/default response
    result = await execute_agent_step(context)
    return result
```

### Distributed Tracing

```python
# Add OpenTelemetry spans for retry attempts
@with_retry()
@trace_span("api_call")
def traced_api_call():
    # Each retry attempt creates a span
    pass
```

### Retry Budgets

```python
# Implement retry budget to prevent excessive retries
class RetryBudget:
    def __init__(self, max_retries_per_minute: int):
        self.budget = max_retries_per_minute

    def can_retry(self) -> bool:
        return self.budget > 0

    def consume(self):
        self.budget -= 1
```

---

## Limitations

1. **Not Suitable for Non-Idempotent Operations**
   - Don't retry operations with side effects (e.g., payments, emails)
   - Ensure operations are idempotent before adding retry

2. **Error Classification is Heuristic**
   - Based on string matching in error messages
   - May misclassify some errors
   - Consider custom classification for critical operations

3. **No Distributed Coordination**
   - Circuit breaker is per-process
   - For distributed systems, use external circuit breaker (e.g., Hystrix, Resilience4j)

4. **No Retry Budget**
   - No global limit on retries across operations
   - Could lead to excessive retries under load
   - Consider implementing retry budget for production

---

**Status:** Stable - Ready for production use
**Last Updated:** 2025-10-20
**Next Review:** Before Phase 2 integration


---
**Logseq:** [[TTA.dev/Platform_tta_dev/Components/Augment/Core/Kb/Tta___components___primitives specs error recovery spec]]
