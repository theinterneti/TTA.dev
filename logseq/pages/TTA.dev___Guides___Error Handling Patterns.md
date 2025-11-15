# Error Handling Patterns

type:: [[Guide]]
category:: [[Advanced Topics]]
difficulty:: [[Intermediate]]
estimated-time:: 20 minutes
target-audience:: [[Developers]], [[AI Engineers]]

---

## Overview

- id:: error-handling-overview
  Learn how to build resilient AI workflows using TTA.dev's recovery primitives. Handle failures gracefully with retry, fallback, timeout, and compensation patterns.

---

## Prerequisites

{{embed ((prerequisites-full))}}

**Should know:**
- Basic workflow composition ([[TTA.dev/Guides/Getting Started]])
- Sequential and parallel primitives
- [[WorkflowContext]] usage

---

## Recovery Primitives

### Available Patterns

- [[TTA.dev/Primitives/RetryPrimitive]] - Automatic retry with backoff
- [[TTA.dev/Primitives/FallbackPrimitive]] - Graceful degradation
- [[TTA.dev/Primitives/TimeoutPrimitive]] - Circuit breaker
- [[TTA.dev/Primitives/CompensationPrimitive]] - Saga pattern

---

## Pattern 1: Retry on Transient Failures

### When to Use

- API rate limits
- Network glitches
- Temporary service outages
- Database connection timeouts

### Example

```python
from tta_dev_primitives.recovery import RetryPrimitive

# Wrap unreliable operation with retry
unreliable_api = LambdaPrimitive(lambda data, ctx: call_external_api(data))

reliable_api = RetryPrimitive(
    primitive=unreliable_api,
    max_retries=3,
    backoff_strategy="exponential",
    initial_delay=1.0,
    jitter=True
)

# Automatically retries with exponential backoff: 1s, 2s, 4s
result = await reliable_api.execute(input_data, context)
```

### Best Practices

✅ Use exponential backoff for rate limits
✅ Enable jitter to avoid thundering herd
✅ Limit max_retries (3-5 is typical)
✅ Only retry transient errors, not client errors

---

## Pattern 2: Fallback for Graceful Degradation

### When to Use

- Primary service unavailable
- Cost optimization (try expensive, fallback to cheap)
- Multiple data sources
- Feature degradation

### Example

```python
from tta_dev_primitives.recovery import FallbackPrimitive

# Try expensive service, fall back to alternatives
expensive_llm = LambdaPrimitive(lambda data, ctx: call_gpt4(data))
cheap_llm = LambdaPrimitive(lambda data, ctx: call_gpt4_mini(data))
cached_response = LambdaPrimitive(lambda data, ctx: get_cache(data))

resilient_workflow = FallbackPrimitive(
    primary=expensive_llm,
    fallbacks=[cheap_llm, cached_response]
)

# Always returns something, even if GPT-4 is down
result = await resilient_workflow.execute(input_data, context)
```

### Best Practices

✅ Order fallbacks by preference (best to worst)
✅ Monitor fallback usage rate
✅ Ensure all fallbacks return same type
✅ Use cache as final fallback

---

## Pattern 3: Combining Retry + Fallback

### The Power Combo

Retry the primary a few times, then fallback if still failing.

### Example

```python
# Retry expensive service 3 times
primary_with_retry = RetryPrimitive(
    primitive=expensive_service,
    max_retries=3,
    backoff_strategy="exponential"
)

# If all retries fail, use fallback
ultra_reliable = FallbackPrimitive(
    primary=primary_with_retry,
    fallbacks=[cheap_service, cached_data]
)

result = await ultra_reliable.execute(input_data, context)
```

### Flow

```
1. Try expensive_service
2. Fail → Retry (1s delay)
3. Fail → Retry (2s delay)
4. Fail → Retry (4s delay)
5. Fail → Try cheap_service
6. Fail → Return cached_data
```

---

## Pattern 4: Timeout to Prevent Hanging

### When to Use

- Slow external APIs
- Database queries that might hang
- Operations with unpredictable latency
- Need guaranteed response time

### Example

```python
from tta_dev_primitives.recovery import TimeoutPrimitive

# Set maximum wait time
timeout_api = TimeoutPrimitive(
    primitive=slow_api_call,
    timeout_seconds=5.0
)

try:
    result = await timeout_api.execute(input_data, context)
except TimeoutError:
    logger.error("API call exceeded 5 second timeout")
    # Use fallback or return error
```

### Combining Timeout + Retry

```python
# Timeout each retry attempt
timeout_call = TimeoutPrimitive(api_call, timeout_seconds=5.0)

retry_workflow = RetryPrimitive(
    primitive=timeout_call,
    max_retries=3
)

# Each of 3 retries has 5-second timeout
```

---

## Pattern 5: Parallel with Individual Error Handling

### Multiple Services with Fallbacks

```python
# Each branch has its own error handling
branch1 = RetryPrimitive(service1, max_retries=3)
branch2 = FallbackPrimitive(service2, fallbacks=[backup2])
branch3 = TimeoutPrimitive(service3, timeout_seconds=5.0)

# Execute in parallel
workflow = branch1 | branch2 | branch3

# Collect results (some may be errors if fail_fast=False)
results = await workflow.execute(input_data, context)
```

---

## Pattern 6: Circuit Breaker (Advanced)

### When to Use

- Prevent cascading failures
- Protect failing service from overload
- Fast-fail when service is known to be down

### Conceptual Example

```python
# Circuit breaker logic
if circuit_breaker.is_open():
    # Service is down, fail immediately
    raise ServiceUnavailable("Circuit breaker open")

try:
    result = await service_call(data)
    circuit_breaker.record_success()
    return result
except Exception as e:
    circuit_breaker.record_failure()
    if circuit_breaker.should_open():
        circuit_breaker.open()
    raise
```

---

## Real-World Example: Resilient LLM Pipeline

### Complete Production Pattern

```python
from tta_dev_primitives import SequentialPrimitive, ParallelPrimitive
from tta_dev_primitives.recovery import RetryPrimitive, FallbackPrimitive, TimeoutPrimitive
from tta_dev_primitives.performance import CachePrimitive

# 1. Input validation (fast-fail on invalid input)
validator = LambdaPrimitive(validate_input)

# 2. Check cache first (avoid expensive calls)
cached_llm = CachePrimitive(
    primitive=expensive_llm,
    ttl_seconds=3600,
    max_size=1000
)

# 3. Add timeout to prevent hanging
timeout_llm = TimeoutPrimitive(
    primitive=cached_llm,
    timeout_seconds=30.0
)

# 4. Add retry for transient failures
retry_llm = RetryPrimitive(
    primitive=timeout_llm,
    max_retries=3,
    backoff_strategy="exponential"
)

# 5. Add fallback to cheaper service
resilient_llm = FallbackPrimitive(
    primary=retry_llm,
    fallbacks=[cheap_llm, rule_based_response]
)

# 6. Complete workflow
workflow = (
    validator >>
    resilient_llm >>
    output_formatter
)

# This workflow:
# ✅ Validates input (fast-fail)
# ✅ Checks cache (cost savings)
# ✅ Times out slow calls (30s max)
# ✅ Retries transient failures (3 attempts)
# ✅ Falls back to alternatives (always responds)
# ✅ Formats output consistently
```

---

## Monitoring Error Patterns

### Key Metrics to Track

```python
# Retry metrics
retry_rate = retries_attempted / total_requests
avg_retries_per_success = retries / successful_requests

# Fallback metrics
fallback_rate = fallback_used / total_requests
primary_success_rate = primary_succeeded / total_requests

# Timeout metrics
timeout_rate = timeouts / total_requests
p95_latency = percentile(latencies, 95)
```

### Alert Thresholds

⚠️ **High retry rate (>20%)** - Primary service having issues
⚠️ **High fallback rate (>30%)** - Primary unreliable, investigate
⚠️ **High timeout rate (>10%)** - Service too slow, optimize or increase timeout
⚠️ **Low cache hit rate (<30%)** - Cache not effective, adjust TTL

---

## Best Practices Summary

### Do's ✅

- **Use retry for transient failures** - Network issues, rate limits
- **Use fallback for service outages** - Multiple alternatives
- **Combine patterns** - Retry + Fallback + Timeout
- **Monitor recovery metrics** - Track when recovery patterns activate
- **Set appropriate timeouts** - Prevent hanging indefinitely
- **Test error paths** - Use [[TTA.dev/Primitives/MockPrimitive]]

### Don'ts ❌

- **Don't retry indefinitely** - Always set max_retries
- **Don't retry 4xx errors** - Client errors won't succeed on retry
- **Don't hide all errors** - Some errors should propagate
- **Don't use tiny timeouts** - Allow reasonable time for operations
- **Don't forget to log** - Track failures for debugging

---

## Testing Error Scenarios

### Using MockPrimitive

```python
from tta_dev_primitives.testing import MockPrimitive

@pytest.mark.asyncio
async def test_retry_on_failure():
    # Simulate 2 failures then success
    mock = MockPrimitive(
        side_effect=[
            ConnectionError("fail 1"),
            ConnectionError("fail 2"),
            {"result": "success"}
        ]
    )

    retry_workflow = RetryPrimitive(mock, max_retries=3)

    result = await retry_workflow.execute("test", context)

    assert result["result"] == "success"
    assert mock.call_count == 3
```

---

## Next Steps

- **Practice:** Implement error handling in your workflows
- **Monitor:** Track retry/fallback rates in production
- **Optimize:** Adjust timeouts and retry strategies
- **Learn more:** [[TTA.dev/Guides/Observability]] for monitoring

---

## Related Content

- [[TTA.dev/Primitives/RetryPrimitive]] - Full retry documentation
- [[TTA.dev/Primitives/FallbackPrimitive]] - Full fallback documentation
- [[TTA.dev/Guides/Cost Optimization]] - Reduce costs with caching + fallback

---

**Created:** [[2025-10-30]]
**Last Updated:** [[2025-10-30]]
**Estimated Time:** 20 minutes
**Difficulty:** [[Intermediate]]
