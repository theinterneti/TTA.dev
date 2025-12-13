# TimeoutPrimitive

type:: [[Primitive]]
category:: [[Recovery]]
status:: [[Stable]]
version:: 0.1.0
package:: [[tta-dev-primitives]]
test-coverage:: 100%
complexity:: [[Medium]]
import-path:: from tta_dev_primitives.recovery import TimeoutPrimitive

---

## Overview

- id:: timeout-primitive-overview
  **TimeoutPrimitive** enforces execution time limits on workflows to prevent operations from hanging indefinitely. Acts as a circuit breaker pattern, essential for maintaining good UX and resource efficiency. Optionally executes a fallback primitive when timeout is exceeded.

---

## Use Cases

- **API Call Protection** - Prevent slow external APIs from blocking workflows
- **Database Query Timeouts** - Kill queries that take too long
- **LLM Response Limits** - Ensure AI responses within acceptable time
- **User Experience** - Guarantee maximum response time for requests
- **Resource Management** - Free up resources from stuck operations
- **Cascading Failure Prevention** - Stop slow operations before they cause system-wide issues

---

## Key Benefits

- **Prevents Hanging** - No more indefinitely waiting operations
- **Predictable Latency** - Guarantee maximum response time
- **Resource Efficiency** - Free resources from stuck operations
- **Optional Fallback** - Graceful degradation when timeout occurs
- **Timeout Tracking** - Monitor timeout rates in context metadata
- **Composability** - Combine with retry, fallback, cache primitives

---

## API Reference

### Constructor

```python
def __init__(
    self,
    primitive: WorkflowPrimitive,
    timeout_seconds: float,
    fallback: WorkflowPrimitive | None = None,
    track_timeouts: bool = True
)
```

**Parameters:**
- `primitive` (WorkflowPrimitive) - Primitive to execute with timeout
- `timeout_seconds` (float) - Maximum execution time in seconds
- `fallback` (WorkflowPrimitive | None) - Optional fallback on timeout
- `track_timeouts` (bool) - Track timeout occurrences in context (default: True)

**Returns:** TimeoutPrimitive instance

### Execute Method

```python
async def execute(self, input_data: Any, context: WorkflowContext) -> Any
```

**Parameters:**
- `input_data` (Any) - Input data for the primitive
- `context` (WorkflowContext) - Workflow context

**Returns:** Output from primitive, or fallback if timeout exceeded

**Raises:** `TimeoutError` if timeout exceeded and no fallback provided

---

## Examples

### Example 1: Simple API Timeout

- id:: timeout-api-example

```python
from tta_dev_primitives.recovery import TimeoutPrimitive
from tta_dev_primitives import LambdaPrimitive, WorkflowContext

# Slow API call (might take 20-60 seconds)
slow_api = LambdaPrimitive(lambda data, ctx: call_external_api(data))

# Enforce 5-second timeout
fast_api = TimeoutPrimitive(
    primitive=slow_api,
    timeout_seconds=5.0
)

context = WorkflowContext()

try:
    result = await fast_api.execute({"query": "search"}, context)
    # Success: API responded within 5 seconds
except TimeoutError:
    # API took longer than 5 seconds
    print("API call timed out after 5 seconds")
```

### Example 2: Timeout with Fallback

- id:: timeout-fallback-example

```python
# Primary: Expensive LLM (might be slow)
expensive_llm = LambdaPrimitive(lambda data, ctx: call_gpt4(data))

# Fallback: Cached response (always fast)
cached_response = LambdaPrimitive(lambda data, ctx: get_cached_response(data))

# Try expensive LLM for 30 seconds, fallback to cache
reliable_llm = TimeoutPrimitive(
    primitive=expensive_llm,
    timeout_seconds=30.0,
    fallback=cached_response
)

# Always returns something (never hangs, never errors)
result = await reliable_llm.execute("What is quantum computing?", context)
# Returns GPT-4 response if <30s, cached response if timeout
```

### Example 3: Database Query Timeout

- id:: timeout-database-example

```python
# Database query that might hang
complex_query = LambdaPrimitive(lambda params, ctx: run_complex_sql_query(params))

# Kill query after 10 seconds
safe_query = TimeoutPrimitive(
    primitive=complex_query,
    timeout_seconds=10.0
)

try:
    results = await safe_query.execute({"table": "users", "filters": {...}}, context)
except TimeoutError:
    logger.error("Query exceeded 10 second limit - needs optimization")
    # Return empty results or cached data
    results = []
```

### Example 4: Combining with Retry

- id:: timeout-retry-combination

```python
from tta_dev_primitives.recovery import RetryPrimitive, TimeoutPrimitive

# Individual request timeout: 5 seconds
timeout_api = TimeoutPrimitive(
    primitive=api_call,
    timeout_seconds=5.0
)

# Retry up to 3 times if timeout occurs
reliable_api = RetryPrimitive(
    primitive=timeout_api,
    max_retries=3,
    backoff_strategy="constant",
    initial_delay=1.0
)

# Pattern: Try for 5s, if timeout retry after 1s, try for 5s again, etc.
# Maximum total time: 5s + 1s + 5s + 1s + 5s = 17 seconds (3 attempts)
```

### Example 5: Monitoring Timeout Rates

- id:: timeout-monitoring-example

```python
# Enable timeout tracking
monitored_operation = TimeoutPrimitive(
    primitive=slow_operation,
    timeout_seconds=10.0,
    track_timeouts=True  # Adds metadata to context
)

context = WorkflowContext()

try:
    result = await monitored_operation.execute(data, context)
except TimeoutError:
    # Check timeout metadata
    timeout_count = context.metadata.get("timeout_count", 0)
    logger.warning(f"Operation timed out (total timeouts: {timeout_count})")

    # Alert if timeout rate is high
    if timeout_count > 10:
        alert_ops_team("High timeout rate detected")
```

---

## Composition Patterns

### Timeout → Fallback → Cache

- id:: timeout-pattern-fallback-cache

```python
from tta_dev_primitives.performance import CachePrimitive

# Layer 1: Cache results (fast)
cached_op = CachePrimitive(expensive_operation, ttl_seconds=3600)

# Layer 2: Timeout cached operation
timeout_op = TimeoutPrimitive(cached_op, timeout_seconds=30.0)

# Layer 3: Fallback to degraded service
workflow = FallbackPrimitive(
    primary=timeout_op,
    fallbacks=[degraded_service]
)

# Execution flow:
# 1. Check cache (instant)
# 2. If cache miss, execute expensive_operation (max 30s)
# 3. If timeout, use degraded_service
```

### Timeout on Each Parallel Branch

- id:: timeout-pattern-parallel

```python
from tta_dev_primitives import ParallelPrimitive

# Timeout each branch independently
branch1_timeout = TimeoutPrimitive(llm1, timeout_seconds=10.0)
branch2_timeout = TimeoutPrimitive(llm2, timeout_seconds=15.0)
branch3_timeout = TimeoutPrimitive(llm3, timeout_seconds=20.0)

# Execute all in parallel with individual timeouts
workflow = branch1_timeout | branch2_timeout | branch3_timeout

# Each branch has its own timeout, doesn't affect others
```

### Sequential with Timeout at Each Stage

- id:: timeout-pattern-sequential

```python
# Each stage has timeout
stage1 = TimeoutPrimitive(fetch_data, timeout_seconds=5.0)
stage2 = TimeoutPrimitive(process_data, timeout_seconds=10.0)
stage3 = TimeoutPrimitive(save_data, timeout_seconds=3.0)

# Total maximum time: 5 + 10 + 3 = 18 seconds
workflow = stage1 >> stage2 >> stage3
```

---

## Best Practices

### Choosing Timeout Values

✅ **Measure first** - Profile operations to understand typical duration
✅ **Add buffer** - Set timeout at P95 or P99 latency (95th/99th percentile)
✅ **Consider user experience** - UI operations should timeout <30s
✅ **Background jobs** - Can have longer timeouts (minutes)
✅ **External APIs** - Check their documented SLA/timeout

### Example Timeout Guidelines

- **UI-blocking operations:** 1-5 seconds
- **API calls:** 5-30 seconds
- **Database queries:** 3-10 seconds
- **LLM inference:** 10-60 seconds
- **Batch processing:** 5-30 minutes
- **File uploads:** Based on size + network speed

### Using Fallbacks

✅ **Always have fallback** for critical paths
✅ **Fallback should be fast** (<1s typical)
✅ **Degrade gracefully** - Partial results better than total failure
✅ **Log timeout events** - Monitor and alert on high rates
✅ **Cache as fallback** - Stale data better than no data

### Don'ts

❌ Don't set timeout too low (causes false positives)
❌ Don't set timeout too high (defeats purpose)
❌ Don't ignore TimeoutError (handle or propagate)
❌ Don't retry forever on timeout (use max_retries)
❌ Don't forget to clean up resources after timeout

---

## Real-World Example: Resilient Search Service

```python
from tta_dev_primitives import SequentialPrimitive
from tta_dev_primitives.recovery import TimeoutPrimitive, FallbackPrimitive, RetryPrimitive
from tta_dev_primitives.performance import CachePrimitive

# Stage 1: Query parsing (fast, should never timeout)
parse_query = LambdaPrimitive(lambda q, ctx: {"parsed": parse_search_query(q)})

# Stage 2: Primary search (Elasticsearch, can be slow)
primary_search = LambdaPrimitive(lambda data, ctx: elasticsearch_search(data))

# Cache search results (1 hour TTL)
cached_search = CachePrimitive(primary_search, ttl_seconds=3600)

# Timeout search at 10 seconds
timeout_search = TimeoutPrimitive(cached_search, timeout_seconds=10.0)

# Retry once if timeout (maybe cache was building)
retry_search = RetryPrimitive(timeout_search, max_retries=1)

# Fallback to simpler search
simple_search = LambdaPrimitive(lambda data, ctx: simple_keyword_search(data))
timeout_simple = TimeoutPrimitive(simple_search, timeout_seconds=3.0)

# Fallback chain
resilient_search = FallbackPrimitive(
    primary=retry_search,
    fallbacks=[timeout_simple]
)

# Stage 3: Format results
format_results = LambdaPrimitive(lambda data, ctx: {"results": format_for_ui(data)})

# Complete search pipeline
search_service = parse_query >> resilient_search >> format_results

# Guarantees:
# ✅ Never hangs (10s + 1s + 3s max = 14s worst case)
# ✅ Cache hit: <100ms (instant)
# ✅ Primary search success: <10s
# ✅ Primary timeout: Falls back to simple search (<3s)
# ✅ Always returns results (or throws meaningful error)
```

---

## Monitoring & Alerting

### Key Metrics

Track these metrics for timeout operations:

```python
# Timeout rate
timeout_rate = timeouts / total_requests

# P95/P99 latency
latency_p95 = percentile(latencies, 95)
latency_p99 = percentile(latencies, 99)

# Fallback usage rate
fallback_rate = fallback_used / total_requests
```

### Alert Thresholds

⚠️ **High timeout rate (>10%)** - Operation is too slow, increase timeout or optimize
⚠️ **Rising P95 latency** - Performance degrading, investigate
⚠️ **High fallback rate (>30%)** - Primary is unreliable
⚠️ **Consistent timeouts** - Service might be down, page ops team

### Logging

```python
# Automatic logs from TimeoutPrimitive
logger.info("timeout_success")  # Completed within timeout
logger.warning("timeout_exceeded", fallback_available=True)
logger.error("timeout_exceeded", fallback_available=False)
```

---

## Testing

### Testing Timeout Behavior

```python
import pytest
import asyncio
from tta_dev_primitives.recovery import TimeoutPrimitive
from tta_dev_primitives import LambdaPrimitive, WorkflowContext

@pytest.mark.asyncio
async def test_timeout_enforced():
    # Create slow operation (5 second delay)
    slow_op = LambdaPrimitive(lambda data, ctx: asyncio.sleep(5))

    # Set 1 second timeout (should trigger)
    timeout_op = TimeoutPrimitive(slow_op, timeout_seconds=1.0)

    context = WorkflowContext()

    with pytest.raises(TimeoutError):
        await timeout_op.execute("test", context)

@pytest.mark.asyncio
async def test_timeout_with_fallback():
    # Slow operation
    slow_op = LambdaPrimitive(lambda data, ctx: asyncio.sleep(5))

    # Fast fallback
    fallback = LambdaPrimitive(lambda data, ctx: "fallback result")

    # Timeout with fallback
    timeout_op = TimeoutPrimitive(
        slow_op,
        timeout_seconds=1.0,
        fallback=fallback
    )

    result = await timeout_op.execute("test", WorkflowContext())

    assert result == "fallback result"
```

---

## Related Content

### Recovery Primitives

{{query (and (page-property type [[Primitive]]) (page-property category [[Recovery]]))}}

### Complementary Patterns

- [[TTA.dev/Primitives/RetryPrimitive]] - Retry after timeout
- [[TTA.dev/Primitives/FallbackPrimitive]] - Graceful degradation on timeout
- [[TTA.dev/Primitives/CachePrimitive]] - Reduce likelihood of timeout
- [[TTA.dev/Guides/Error Handling Patterns]] - Comprehensive error handling guide

---

## References

- **GitHub Source:** [`packages/tta-dev-primitives/src/tta_dev_primitives/recovery/timeout.py`](https://github.com/theinterneti/TTA.dev/blob/main/packages/tta-dev-primitives/src/tta_dev_primitives/recovery/timeout.py)
- **Tests:** [`packages/tta-dev-primitives/tests/recovery/test_timeout.py`](https://github.com/theinterneti/TTA.dev/blob/main/packages/tta-dev-primitives/tests/recovery/test_timeout.py)

---

**Created:** [[2025-10-30]]
**Last Updated:** [[2025-10-30]]
**Category:** [[Recovery]]
**Complexity:** [[Medium]]


---
**Logseq:** [[TTA.dev/_archive/Nested_copies/Framework/Logseq/Pages/Tta.dev___primitives___timeoutprimitive]]
