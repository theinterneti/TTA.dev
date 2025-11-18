# TTA.dev/Patterns/Error Handling

## Overview

Error handling is the foundation of reliable TTA.dev applications. Rather than scattering try/catch blocks throughout your code, TTA.dev provides specialized primitives for systematic error management: `RetryPrimitive`, `FallbackPrimitive`, `TimeoutPrimitive`, and `CompensationPrimitive`. These primitives implement industry best practices like circuit breaker patterns, exponential backoff, and saga orchestration while maintaining full observability.

Tags: #reliability #resilience #patterns #recovery
Type: Pattern Guide
Audience: Intermediate to Advanced Developers
Status: Stable

## Core Concepts

### Error Handling Primitive Types

#### Recovery Primitives (Automatic Retry & Fallback)

```python
from tta_dev_primitives.recovery import (
    RetryPrimitive,
    FallbackPrimitive,
    TimeoutPrimitive,
    CompensationPrimitive
)

# Exponential backoff retry
retry_api = RetryPrimitive(
    primitive=unreliable_api_call,
    max_retries=3,
    backoff_strategy="exponential",
    initial_delay=1.0,
    max_delay=60.0
)

# Graceful degradation fallback
resilient_api = FallbackPrimitive(
    primary=preferred_api,
    fallbacks=[backup_api, cached_response, error_message]
)

# Circuit breaker timeout
timeout_protected = TimeoutPrimitive(
    primitive=slow_operation,
    timeout_seconds=30.0,
    fallback=timeout_fallback
)

# Saga orchestration rollback
compensating_workflow = CompensationPrimitive(
    forward_operations=[step1, step2, step3],
    compensation_operations=[undo_step3, undo_step2, undo_step1]
)
```

#### Integration with WorkflowContext

All primitives propagate error context through the workflow:

```python
context = WorkflowContext(
    correlation_id="api-request-123",
    metadata={
        "user_id": "user-456",
        "priority": "high",
        "environment": "production"
    }
)

try:
    result = await resilient_workflow.execute(input_data, context)
except Exception as e:
    # Error details available in context for observability
    logger.error("Operation failed", extra={
        "correlation_id": context.correlation_id,
        "error_count": context.metadata.get("retry_count", 0),
        "last_error": str(e)
    })
```

## Recovery Patterns

### Pattern 1: API Call Resilience

```python
# External API calls with comprehensive protection
api_resilience = (
    RetryPrimitive(              # Retry transient failures
        primitive=http_api_call,
        max_retries=3,
        backoff_strategy="exponential"
    ) |
    FallbackPrimitive(           # Fallback to cache/last known good
        primary=lambda: None,    # Will use previous retry result
        fallbacks=[cache_lookup, last_known_good]
    )
).execute(input_data, context)

# Usage
result = await api_resilience
if result.get("from_cache"):
    logger.info("Used cached fallback for API call")
```

### Pattern 2: Database Transaction Saga

```python
# Complex multi-step operations with rollback
payment_processing = CompensationPrimitive(
    forward_operations=[
        validate_payment,
        charge_credit_card,      # If this fails, rollback needed
        update_inventory,
        send_confirmation_email
    ],
    compensation_operations=[
        lambda: None,           # Validation doesn't need rollback
        refund_charge,          # Credit card refund
        restore_inventory,      # Put items back
        send_failure_email      # Different email for failure
    ]
)

result = await payment_processing.execute(payment_data, context)
```

### Pattern 3: LLM Call with Multiple Models

```python
# LLM cascade with different models as fallbacks
llm_cascade = FallbackPrimitive(
    primary=RetryPrimitive(
        primitive=gpt4_call,
        max_retries=2,
        backoff_strategy="fixed",
        initial_delay=2.0
    ),
    fallbacks=[
        gpt3_5_call,           # Faster, cheaper fallback
        claude_call,           # Different provider
        cached_response        # Last resort
    ]
)

response = await llm_cascade.execute(prompt, context)
model_used = response.get("model", "unknown")
logger.info(f"LLM response from: {model_used}")
```

### Pattern 4: Circuit Breaker for Unreliable Services

```python
# Circuit breaker pattern implementation
circuit_breaker = TimeoutPrimitive(
    primitive=RetryPrimitive(
        primitive=unreliable_service,
        max_retries=2
    ),
    timeout_seconds=10.0,
    fallback=cached_result_or_error
)

# Automatically tracks failure rates and temporarily disables
result = await circuit_breaker.execute(request, context)
```

## Advanced Error Handling Patterns

### Conditional Recovery

```python
# Different strategies based on error type
def error_specific_retry(attempt: int, exception: Exception) -> float:
    """Custom backoff based on error type"""
    if isinstance(exception, ConnectionError):
        return min(2 ** attempt, 30.0)  # Network errors: faster retry
    elif isinstance(exception, RateLimitError):
        return min(attempt * 60.0, 300.0)  # Rate limits: much slower
    else:
        return min(2 ** attempt, 60.0)  # Default

smart_retry = RetryPrimitive(
    primitive=error_prone_operation,
    max_retries=5,
    backoff_fn=error_specific_retry
)
```

### Hierarchical Error Handling

```python
# Multiple layers of protection
resilient_operation = (
    TimeoutPrimitive(           # Outer: Global timeout
        primitive=RetryPrimitive(
            primitive=FallbackPrimitive(  # Inner: Specific strategies
                primary=primary_operation,
                fallbacks=[
                    backup_operation,
                    emergency_fallback
                ]
            ),
            max_retries=3
        ),
        timeout_seconds=120.0,
        fallback=ultimate_fallback
    )
)
```

### Context-Aware Error Handling

```python
# Different behaviors based on context metadata
class ContextAwareRetryPrimitive(RetryPrimitive):
    def _should_retry(self, attempt: int, exception: Exception) -> bool:
        context = self._current_context

        # Skip retry for certain users or in production
        if context.metadata.get("skip_retry", False):
            return False

        # Different limits for different priorities
        max_attempts = 5 if context.metadata.get("priority") == "high" else 2

        return attempt < max_attempts and self._is_retryable_error(exception)
```

## Best Practices

### ✅ Do This

1. **Use Primitives, Not Manual Error Handling**: Never write manual retry loops
2. **Include Fallbacks**: Always have a degradation path, never just fail
3. **Set Appropriate Timeouts**: Protect against hanging operations
4. **Monitor Error Rates**: Use observability to track error patterns
5. **Test Error Scenarios**: Include failure cases in your test suites
6. **Use Compensation for Multi-Step Operations**: Implement proper rollback
7. **Log Error Context**: Include correlation IDs and retry counts in logs

### ❌ Avoid This

1. **Don't Use Try/Except for Control Flow**: Use primitives instead
2. **Don't Set Infinite Timeouts**: Always bound operation time
3. **Don't Retry Indefinitely**: Set reasonable retry limits
4. **Don't Ignore Circuit Breaker State**: Respect failure thresholds
5. **Don't Make Fallbacks Too Expensive**: Keep degradation path fast
6. **Don't Hide Errors**: Ensure errors are logged and monitored

## Production Deployment Considerations

### Error Rate Monitoring

```python
# Monitor error rates per operation
error_metrics = {
    "retry_rate": context.metadata.get("retry_count", 0) / total_requests,
    "fallback_rate": len(fallback_invocations) / total_requests,
    "timeout_rate": len(timeout_exceptions) / total_requests,
    "compensation_rate": len(rollback_operations) / total_operations
}

# Alert thresholds
if error_metrics["retry_rate"] > 0.5:  # >50% retries
    alert("High retry rate detected")
if error_metrics["timeout_rate"] > 0.1:  # >10% timeouts
    alert("Performance degradation - high timeouts")
```

### Configuration Management

```python
# Environment-specific configurations
configs = {
    "development": {
        "retry_attempts": 1,
        "timeout_seconds": 60.0,
        "circuit_breaker_threshold": 0.8
    },
    "staging": {
        "retry_attempts": 2,
        "timeout_seconds": 30.0,
        "circuit_breaker_threshold": 0.7
    },
    "production": {
        "retry_attempts": 3,
        "timeout_seconds": 15.0,
        "circuit_breaker_threshold": 0.6
    }
}

environment_config = configs[os.getenv("ENVIRONMENT", "development")]
```

### Graceful Degradation

```python
# Multi-tier service degradation
service_levels = [
    ("full_featured", lambda: full_operation()),
    ("basic_featured", lambda: basic_operation()),
    ("minimal_featured", lambda: minimal_operation()),
    ("error_message", lambda: error_response())
]

for level_name, operation in service_levels:
    try:
        result = await operation()
        logger.info(f"Service operated at {level_name} level")
        break
    except Exception as e:
        logger.warning(f"{level_name} level failed: {e}")
        continue
```

## Troubleshooting Guide

### Symptom: High Retry Rates

**Possible Causes:**
- Network instability or intermittent failures
- Overloaded downstream services
- Inappropriate backoff configurations
- Missing circuit breaker activation

**Debugging Steps:**
1. Check error types in retry logic
2. Monitor downstream service health
3. Review backoff timing configurations
4. Verify circuit breaker thresholds

**Solutions:**
```python
# Adjust backoff for high retry rates
optimized_retry = RetryPrimitive(
    primitive=unreliable_operation,
    max_retries=5,
    backoff_strategy="exponential",
    initial_delay=5.0,  # Longer initial delay
    max_delay=300.0     # Much longer max delay
)
```

### Symptom: Frequent Fallback Usage

**Possible Causes:**
- Primary service consistently failing
- Overly restrictive timeout settings
- Issues with fallback implementation
- Improper fallback prioritization

**Debugging Steps:**
1. Monitor primary vs fallback success rates
2. Check timeout configurations
3. Validate fallback data quality
4. Review fallback selection logic

### Symptom: Compensation Failures

**Possible Causes:**
- Incomplete compensation logic
- Order-dependent compensation operations
- Resource conflicts during rollback
- Missing error handling in compensation

**Debugging Steps:**
1. Verify compensation operation order
2. Test compensation logic independently
3. Ensure compensation operations are idempotent
4. Monitor compensation success rates

### Symptom: Circuit Breaker Oscillations

**Possible Causes:**
- Incorrect threshold settings
- Too short recovery periods
- Probe requests causing additional load
- Thresholds too close to normal operation variance

**Debugging Steps:**
1. Monitor error rates around thresholds
2. Review circuit breaker recovery logic
3. Analyze traffic patterns during open/closed states
4. Adjust thresholds based on historical data

## Common Pitfalls

### Pitfall 1: Retry Storm Protection

**Problem**: All instances of a failing service trigger retries simultaneously
**Solution**: Use jittered backoff and request coalescing

```python
# Add jitter to prevent thundering herd
jittered_retry = RetryPrimitive(
    primitive=shared_service,
    max_retries=3,
    backoff_strategy="exponential",
    jitter=True  # Adds random variation to delays
)
```

### Pitfall 2: Fallback Data Consistency

**Problem**: Fallback returns stale or incorrect data
**Solution**: Validate fallback data quality and freshness

```python
async def validated_fallback(context):
    """Fallback with data validation"""
    data = await get_cached_response(context)

    # Validate data freshness and relevance
    if is_data_fresh_enough(data, context.metadata.get("max_age")):
        return data
    else:
        raise Exception("Fallback data too stale")
```

### Pitfall 3: Compensation Order Dependency

**Problem**: Compensation operations fail due to order dependencies
**Solution**: Design compensations to be order-independent where possible

```python
# Order-independent compensation
async def robust_compensation(context):
    """Compensation that handles dependencies internally"""
    results = await asyncio.gather(
        cancel_payment(context),
        restore_inventory(context),
        notify_user(context),
        return_exceptions=True  # Don't fail if one compensation fails
    )

    for result in results:
        if isinstance(result, Exception):
            logger.error(f"Compensation component failed: {result}")
        else:
            logger.info("Compensation component succeeded")
```

## Integration Examples

### With CachePrimitive

```python
# Cached operation with error recovery
cached_with_fallback = CachePrimitive(
    primitive=FallbackPrimitive(
        primary=expensive_api_call,
        fallbacks=[cache_lookup, error_stub]
    ),
    ttl_seconds=300,
    max_size=1000
)
```

### With RouterPrimitive

```python
# Route to reliable alternatives on failure
error_aware_router = RetryPrimitive(
    primitive=RouterPrimitive(
        routes={
            "primary": primary_service,
            "backup": backup_service,
            "emergency": emergency_service
        },
        routing_function=lambda x, ctx: select_best_route(ctx)
    ),
    max_retries=2
)
```

### With ParallelPrimitive

```python
# Parallel operations with individual error handling
parallel_resilient = ParallelPrimitive([
    FallbackPrimitive(primary_svc_a, [backup_svc_a]),
    RetryPrimitive(error_prone_svc_b, max_retries=2),
    TimeoutPrimitive(slow_svc_c, timeout_seconds=30.0)
])
```

## Error Handling Metrics

Monitor these key metrics in production:

- **Recovery Rate**: Percentage of failed operations recovered by error handling
- **Fallback Usage**: How often fallback paths are used
- **Retry Success Rate**: Percentage of retried operations that eventually succeed
- **Compensation Success Rate**: How often compensation operations complete successfully
- **Circuit Breaker State Changes**: Frequency of circuit breaker open/closed transitions
- **Error Propagation Time**: Time from error occurrence to final resolution

## Next Steps

### Explore Related Patterns
- [[TTA.dev/Patterns/Caching]]
- [[TTA.dev/Patterns/Performance]]
- [[TTA.dev/Primitives/RetryPrimitive]]
- [[TTA.dev/Primitives/FallbackPrimitive]]

### Related How-To Guides
- [[TTA.dev/How-To/Building Reliable AI Workflows]]
- [[TTA.dev/How-To/Adding Tracing]]
- [[TTA.dev/How-To/Debugging Workflows]]

### Implementation Examples
- [[TTA.dev/Examples/Error Recovery Patterns]]
- [[TTA.dev/Examples/API Resilience]]
- [[TTA.dev/Examples/LLM Fallback Cascade]]

### Best Practices Documentation
- [[TTA.dev/Best Practices/Error Handling]]
- [[TTA.dev/Best Practices/Circuit Breaker Usage]]
- [[TTA.dev/Best Practices/Compensation Patterns]]

---

**Last Updated:** 2025-11-18
**Author:** TTA.dev Adaptive Cline Agent
**Related Files:** `packages/tta-dev-primitives/src/tta_dev_primitives/recovery/`
