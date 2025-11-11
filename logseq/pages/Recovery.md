# Recovery

**Tag page for error handling, resilience, and recovery patterns**

---

## Overview

**Recovery** in TTA.dev refers to strategies for handling errors and building resilient workflows. Recovery primitives provide:
- Automatic retry with backoff strategies
- Graceful degradation through fallback chains
- Circuit breaker patterns to prevent cascade failures
- Compensation patterns (Saga) for distributed transactions

All recovery primitives are **declarative** - you compose them into workflows rather than writing manual try/catch blocks.

**See:** [[TTA.dev/Patterns/Error Handling]]

---

## Recovery Primitives

### Retry Pattern

**[[TTA Primitives/RetryPrimitive]]** - Retry failed operations with backoff

**Backoff Strategies:**
- **Constant**: Fixed delay between retries
- **Linear**: Increasing delay (1s, 2s, 3s)
- **Exponential**: Exponentially increasing (1s, 2s, 4s, 8s)
- **Jitter**: Random variation to prevent thundering herd

**Example:**
```python
from tta_dev_primitives.recovery import RetryPrimitive

workflow = RetryPrimitive(
    primitive=api_call,
    max_retries=3,
    backoff_strategy="exponential",
    initial_delay=1.0,
    jitter=True
)
```

**Use Cases:**
- Transient network failures
- Rate-limited API calls
- Database connection timeouts
- Temporary service unavailability

---

### Fallback Pattern

**[[TTA Primitives/FallbackPrimitive]]** - Graceful degradation cascade

**Pattern:**
```python
from tta_dev_primitives.recovery import FallbackPrimitive

workflow = FallbackPrimitive(
    primary=expensive_api,
    fallbacks=[
        cheaper_api,
        cached_response,
        default_value
    ]
)
```

**Use Cases:**
- Multi-provider LLM services
- Primary/secondary data sources
- High availability systems
- Cost optimization (expensive → cheap → cached)

---

### Timeout Pattern

**[[TTA Primitives/TimeoutPrimitive]]** - Circuit breaker to prevent hanging

**Pattern:**
```python
from tta_dev_primitives.recovery import TimeoutPrimitive

workflow = TimeoutPrimitive(
    primitive=slow_operation,
    timeout_seconds=30.0,
    raise_on_timeout=True
)
```

**Use Cases:**
- Enforce SLA requirements
- Prevent resource exhaustion
- Circuit breaker implementation
- Long-running operation safeguards

---

### Compensation Pattern

**[[TTA Primitives/CompensationPrimitive]]** - Saga pattern for distributed transactions

**Pattern:**
```python
from tta_dev_primitives.recovery import CompensationPrimitive

workflow = CompensationPrimitive(
    primitives=[
        (create_user, rollback_user),
        (send_email, rollback_email),
        (activate_account, None),  # No rollback needed
    ]
)
```

**Use Cases:**
- Multi-step transactions
- Distributed workflows
- Database + external service coordination
- Rollback on partial failure

---

### Circuit Breaker Pattern

**[[TTA Primitives/CircuitBreakerPrimitive]]** - Prevent cascade failures

**States:**
- **Closed**: Normal operation, requests pass through
- **Open**: Too many failures, reject requests immediately
- **Half-Open**: Testing if service recovered

**Use Cases:**
- Protect dependent services
- Prevent cascade failures
- Fast failure in degraded state
- Automatic recovery detection

---

## Combined Recovery Patterns

### Layered Recovery

**Pattern:** Stack multiple recovery primitives for robust workflows

```python
from tta_dev_primitives.recovery import (
    TimeoutPrimitive,
    RetryPrimitive,
    FallbackPrimitive
)

workflow = (
    TimeoutPrimitive(timeout_seconds=10) >>
    RetryPrimitive(max_retries=3, backoff_strategy="exponential") >>
    FallbackPrimitive(
        primary=expensive_api,
        fallbacks=[cheap_api, cached_response]
    )
)
```

**Benefits:**
- Timeout prevents hanging (circuit breaker)
- Retry handles transient failures
- Fallback provides degraded service
- Combined: Maximum reliability

---

### Recovery with Composition

**Sequential with Recovery:**
```python
workflow = (
    input_validator >>
    RetryPrimitive(data_processor) >>
    FallbackPrimitive(
        primary=primary_storage,
        fallbacks=[backup_storage]
    )
)
```

**Parallel with Recovery:**
```python
workflow = (
    FallbackPrimitive(
        primary=expensive_llm,
        fallbacks=[fast_llm, cached_response]
    ) |
    RetryPrimitive(database_query) |
    TimeoutPrimitive(external_api)
)
```

**See:** [[TTA.dev/Concepts/Composition]]

---

## Pages Tagged with #Recovery

{{query (page-tags [[Recovery]])}}

---

## Error Handling Best Practices

### ✅ DO

**Choose the Right Strategy:**
- **Transient failures** → Use `RetryPrimitive`
- **Provider failures** → Use `FallbackPrimitive`
- **Slow operations** → Use `TimeoutPrimitive`
- **Distributed transactions** → Use `CompensationPrimitive`

**Layer Error Handling:**
```python
# Good: Multiple layers of protection
workflow = (
    TimeoutPrimitive(timeout_seconds=30) >>
    RetryPrimitive(max_retries=3) >>
    FallbackPrimitive(primary=api1, fallbacks=[api2, cached])
)
```

**Log Errors with Context:**
```python
logger.error(
    "Operation failed",
    extra={
        "correlation_id": context.correlation_id,
        "attempt": attempt_number,
        "error": str(error)
    }
)
```

**Test Error Paths:**
- Test each recovery primitive in isolation
- Test combined recovery strategies
- Test with real error conditions
- Verify observability (traces, metrics)

---

### ❌ DON'T

**Don't Catch and Ignore:**
```python
# Bad: Silent failure
try:
    result = await operation()
except Exception:
    pass  # ❌ Error is lost
```

**Don't Retry Forever:**
```python
# Bad: Infinite retries
RetryPrimitive(
    primitive=api_call,
    max_retries=None  # ❌ Will retry forever
)
```

**Don't Mix Manual and Primitive Handling:**
```python
# Bad: Mixing patterns
try:
    result = await RetryPrimitive(api_call).execute(data, context)
except Exception:
    # ❌ RetryPrimitive already handles retries
    result = await fallback_call()
```

---

## Error Context Propagation

**Recovery primitives automatically propagate error context:**

```python
context = WorkflowContext(
    correlation_id="req-123",
    data={"request_id": "abc"}
)

# All recovery primitives preserve context
workflow = RetryPrimitive(
    FallbackPrimitive(
        TimeoutPrimitive(operation)
    )
)

# Context flows through all layers
result = await workflow.execute(input_data, context)
```

**Context includes:**
- `correlation_id` - Request tracking
- `workflow_id` - Workflow identification
- `metadata` - Custom data
- `parent_span` - OpenTelemetry trace context

**See:** [[WorkflowContext]], [[TTA.dev/Concepts/Context Propagation]]

---

## Recovery Metrics

**All recovery primitives export Prometheus metrics:**

### Retry Metrics
```promql
# Total retry attempts
retry_attempts_total{primitive="api_call", status="success|failure"}

# Retry duration
retry_duration_seconds{primitive="api_call"}

# Backoff time
retry_backoff_seconds{strategy="exponential"}
```

### Fallback Metrics
```promql
# Fallback activations
fallback_activations_total{primary="api1", fallback="api2"}

# Fallback success rate
fallback_success_rate{primitive="llm_call"}
```

### Timeout Metrics
```promql
# Timeout events
timeout_events_total{primitive="slow_op"}

# Operation duration vs timeout
operation_duration_seconds{primitive="slow_op"}
timeout_threshold_seconds{primitive="slow_op"}
```

**See:** [[TTA.dev/Observability]], [[Prometheus]]

---

## Real-World Examples

### Example 1: Resilient LLM Pipeline

```python
from tta_dev_primitives.recovery import (
    TimeoutPrimitive,
    RetryPrimitive,
    FallbackPrimitive
)

# Multi-layer resilience
llm_workflow = (
    TimeoutPrimitive(
        timeout_seconds=30,
        primitive=RetryPrimitive(
            max_retries=3,
            backoff_strategy="exponential",
            primitive=FallbackPrimitive(
                primary=openai_gpt4,
                fallbacks=[
                    anthropic_claude,
                    google_gemini,
                    cached_response
                ]
            )
        )
    )
)
```

**Benefits:**
- 30s timeout (prevent hanging)
- 3 retries with exponential backoff
- 4-tier fallback (3 providers + cache)
- ~99.9% availability

---

### Example 2: Distributed Transaction

```python
from tta_dev_primitives.recovery import CompensationPrimitive

# Saga pattern for user registration
registration = CompensationPrimitive(
    primitives=[
        (create_user_record, delete_user_record),
        (send_welcome_email, send_cancellation_email),
        (activate_subscription, cancel_subscription),
        (notify_admin, None),  # No rollback
    ]
)

# If any step fails, previous steps are rolled back
try:
    result = await registration.execute(user_data, context)
except Exception:
    # All completed steps already rolled back
    logger.error("Registration failed and rolled back")
```

---

### Example 3: Rate-Limited API

```python
from tta_dev_primitives.recovery import RetryPrimitive

# Retry with jitter for rate limits
rate_limited_api = RetryPrimitive(
    primitive=external_api_call,
    max_retries=5,
    backoff_strategy="exponential",
    initial_delay=2.0,
    backoff_factor=2.0,
    jitter=True,  # Prevent thundering herd
    retry_on_exceptions=[RateLimitError, TimeoutError]
)
```

**Delays with jitter:**
- Attempt 1: Immediate
- Attempt 2: ~2s ± jitter
- Attempt 3: ~4s ± jitter
- Attempt 4: ~8s ± jitter
- Attempt 5: ~16s ± jitter

---

## Recovery Testing

### Unit Testing

```python
import pytest
from tta_dev_primitives.testing import MockPrimitive
from tta_dev_primitives.recovery import RetryPrimitive

@pytest.mark.asyncio
async def test_retry_success_after_failures():
    # Mock primitive that fails twice, then succeeds
    mock = MockPrimitive(
        side_effects=[
            Exception("Fail 1"),
            Exception("Fail 2"),
            {"result": "success"}
        ]
    )

    workflow = RetryPrimitive(mock, max_retries=3)
    result = await workflow.execute({}, context)

    assert result["result"] == "success"
    assert mock.call_count == 3
```

### Integration Testing

```python
@pytest.mark.asyncio
async def test_fallback_cascade():
    # Test real fallback behavior
    workflow = FallbackPrimitive(
        primary=failing_api,
        fallbacks=[backup_api, cached_response]
    )

    result = await workflow.execute(input_data, context)

    # Verify fallback was used
    assert result["source"] == "backup_api"
```

**See:** [[Testing]], [[TTA.dev/Testing Strategy]]

---

## Related Patterns

- [[TTA.dev/Patterns/Error Handling]] - Comprehensive error handling guide
- [[TTA.dev/Patterns/Caching]] - Caching for fallback responses
- [[TTA.dev/Patterns/Sequential Workflow]] - Sequential execution with recovery
- [[TTA.dev/Multi-Agent Patterns]] - Multi-agent error handling

---

## Related Concepts

- [[Primitive]] - All primitive types
- [[Workflow]] - Workflow composition
- [[Performance]] - Performance optimization
- [[Testing]] - Testing strategies
- [[Production]] - Production best practices

---

## Documentation

- [[TTA.dev/Patterns/Error Handling]] - Main error handling guide
- [[PRIMITIVES_CATALOG]] - Complete primitive reference
- [[AGENTS]] - Agent instructions
- [[README]] - Project overview

---

**Tags:** #recovery #error-handling #resilience #retry #fallback #timeout #circuit-breaker #index-page

**Last Updated:** 2025-11-05
**Maintained by:** TTA.dev Team

- [[Project Hub]]