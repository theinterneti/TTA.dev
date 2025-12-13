# TTA.dev/Patterns/Error Handling

**Robust error management strategies for production workflows**

---

## Overview

Error handling is critical for production AI workflows. TTA.dev provides composable primitives for implementing sophisticated error handling strategies without manual try/catch blocks.

**Core Principle:** Declarative error handling through primitives
**Key Primitives:** [[RetryPrimitive]], [[FallbackPrimitive]], [[TimeoutPrimitive]], [[CompensationPrimitive]]

---

## Error Handling Strategies

### 1. Retry Pattern

**Use When:**
- Transient failures (network glitches, rate limits)
- Temporary service unavailability
- Random errors that might succeed on retry

```python
from tta_dev_primitives.recovery import RetryPrimitive
from tta_dev_primitives import WorkflowContext # Keep import for now, will address later if needed

async def unstable_api(data: dict, context: WorkflowContext) -> dict: # This is a code example, will address later if needed
    """API that sometimes fails transiently."""
    response = await external_api.call(data)
    return response

# Wrap with retry
reliable_api = RetryPrimitive(
    primitive=unstable_api,
    max_retries=3,
    backoff_strategy="exponential",  # 1s, 2s, 4s
    initial_delay=1.0,
    jitter=True  # Add randomness to prevent thundering herd
)

# Use in workflow
result = await reliable_api.execute({"query": "test"}, context)
```

**Backoff Strategies:**

```python
# Constant backoff (same delay each time)
RetryPrimitive(backoff_strategy="constant", initial_delay=2.0)
# Delays: 2s, 2s, 2s

# Linear backoff (increasing linearly)
RetryPrimitive(backoff_strategy="linear", initial_delay=1.0)
# Delays: 1s, 2s, 3s

# Exponential backoff (doubling each time)
RetryPrimitive(backoff_strategy="exponential", initial_delay=1.0)
# Delays: 1s, 2s, 4s, 8s

# With jitter (add randomness)
RetryPrimitive(backoff_strategy="exponential", initial_delay=1.0, jitter=True)
# Delays: ~1s, ~2s, ~4s (±30% random)
```

---

### 2. Fallback Pattern

**Use When:**
- Multiple service providers available
- Graceful degradation acceptable
- Need high availability

```python
from tta_dev_primitives.recovery import FallbackPrimitive

# Define primary and fallback operations
async def primary_llm(data: dict, context: WorkflowContext) -> dict: # This is a code example, will address later if needed
    """Primary LLM (OpenAI GPT-4)."""
    return await openai.generate(data["prompt"], model="gpt-4")

async def fallback_llm_1(data: dict, context: WorkflowContext) -> dict: # This is a code example, will address later if needed
    """First fallback (Anthropic Claude)."""
    return await anthropic.generate(data["prompt"], model="claude-3")

async def fallback_llm_2(data: dict, context: WorkflowContext) -> dict: # This is a code example, will address later if needed
    """Second fallback (Google Gemini)."""
    return await google.generate(data["prompt"], model="gemini-pro")

async def cached_response(data: dict, context: WorkflowContext) -> dict: # This is a code example, will address later if needed
    """Final fallback (cached responses)."""
    return {"response": "Service temporarily unavailable. Using cached response."}

# Create fallback chain
resilient_llm = FallbackPrimitive(
    primary=primary_llm,
    fallbacks=[
        fallback_llm_1,
        fallback_llm_2,
        cached_response  # Always succeeds
    ]
)

# Execute with automatic fallback
result = await resilient_llm.execute({"prompt": "Hello"}, context)
```

**Execution Flow:**
1. Try primary_llm
2. If fails → try fallback_llm_1
3. If fails → try fallback_llm_2
4. If fails → try cached_response
5. Return first successful result

---

### 3. Timeout Pattern

**Use When:**
- Operations might hang indefinitely
- Need to enforce SLA/deadlines
- Circuit breaker behavior desired

```python
from tta_dev_primitives.recovery import TimeoutPrimitive

async def slow_operation(data: dict, context: WorkflowContext) -> dict: # This is a code example, will address later if needed
    """Operation that might take too long."""
    result = await potentially_slow_api(data)
    return result

# Wrap with timeout
fast_operation = TimeoutPrimitive(
    primitive=slow_operation,
    timeout_seconds=5.0,  # Max 5 seconds
    raise_on_timeout=True  # Raise TimeoutError if exceeded
)

# Use in workflow
try:
    result = await fast_operation.execute({"query": "test"}, context)
except TimeoutError:
    # Handle timeout
    result = {"error": "Operation timed out"}
```

---

### 4. Compensation Pattern (Saga)

**Use When:**
- Distributed transactions needed
- Need to rollback partial changes
- Multi-step operations with side effects

```python
from tta_dev_primitives.recovery import CompensationPrimitive

# Define operations and compensations
async def create_user(data: dict, context: WorkflowContext) -> dict: # This is a code example, will address later if needed
    user = await db.create_user(data["user_info"])
    return {"user_id": user.id}

async def rollback_user(data: dict, context: WorkflowContext) -> dict: # This is a code example, will address later if needed
    await db.delete_user(data["user_id"])
    return {"rolled_back": "user"}

async def send_welcome_email(data: dict, context: WorkflowContext) -> dict: # This is a code example, will address later if needed
    await email.send(data["user_id"], "Welcome!")
    return {"email_sent": True}

async def rollback_email(data: dict, context: WorkflowContext) -> dict: # This is a code example, will address later if needed
    # Can't unsend email, but log it
    await log.info(f"Email was sent to {data['user_id']}")
    return {"noted": "email_sent"}

async def activate_account(data: dict, context: WorkflowContext) -> dict: # This is a code example, will address later if needed
    await db.activate_user(data["user_id"])
    return {"activated": True}

# No compensation for final step (permanent)

# Create saga with compensations
user_registration = CompensationPrimitive(
    primitives=[
        (create_user, rollback_user),
        (send_welcome_email, rollback_email),
        (activate_account, None)  # No compensation
    ]
)

# Execute - automatic rollback on failure
try:
    result = await user_registration.execute({"user_info": {...}}, context)
except Exception as e:
    # All successful steps were automatically rolled back
    logger.error(f"Registration failed: {e}")
```

---

## Combined Error Handling

### Retry + Fallback + Timeout

```python
from tta_dev_primitives.recovery import (
    RetryPrimitive,
    FallbackPrimitive,
    TimeoutPrimitive
)

# Layer 1: Timeout (prevent hanging)
timed_api = TimeoutPrimitive(
    primitive=external_api_call,
    timeout_seconds=10.0
)

# Layer 2: Retry (handle transient failures)
retry_api = RetryPrimitive(
    primitive=timed_api,
    max_retries=3,
    backoff_strategy="exponential"
)

# Layer 3: Fallback (provide alternatives)
resilient_api = FallbackPrimitive(
    primary=retry_api,
    fallbacks=[backup_api, cached_response]
)

# Use in workflow - comprehensive error handling
workflow = (
    prepare_request >>
    resilient_api >>
    process_response
)
```

**Error Handling Flow:**
```
Request → Timeout(10s) → Retry(3x) → Fallback(2 options) → Response
          ↓              ↓              ↓
          Hangs?     Transient fail?   All failed?
          Cancel     Retry              Use backup
```

---

## Error Context Propagation

### Tracking Errors Through Workflow

```python
from tta_dev_primitives import WorkflowContext # Keep import for now, will address later if needed
import structlog

logger = structlog.get_logger(__name__)

async def error_aware_operation(data: dict, context: WorkflowContext) -> dict: # This is a code example, will will address later if needed
    """Operation that tracks errors in context."""

    try:
        result = await risky_operation(data)
        return result
    except Exception as e:
        # Log with correlation ID
        logger.error(
            "operation_failed",
            correlation_id=context.correlation_id,
            error=str(e),
            exc_info=True
        )

        # Store error in context for downstream handling
        context.set("last_error", {
            "type": type(e).__name__,
            "message": str(e),
            "operation": "risky_operation"
        })

        raise  # Re-raise for primitive error handling
```

---

## Error Metrics

### Monitoring Error Rates

```python
from prometheus_client import Counter, Histogram

# Define metrics
operation_errors = Counter(
    'operation_errors_total',
    'Total operation errors',
    ['operation', 'error_type']
)

operation_duration = Histogram(
    'operation_duration_seconds',
    'Operation duration',
    ['operation', 'status']
)

async def monitored_operation(data: dict, context: WorkflowContext) -> dict: # This is a code example, will address later if needed
    """Operation with error metrics."""

    start_time = time.time()

    try:
        result = await risky_operation(data)

        # Record success
        operation_duration.labels(
            operation="risky_operation",
            status="success"
        ).observe(time.time() - start_time)

        return result

    except Exception as e:
        # Record failure
        operation_errors.labels(
            operation="risky_operation",
            error_type=type(e).__name__
        ).inc()

        operation_duration.labels(
            operation="risky_operation",
            status="error"
        ).observe(time.time() - start_time)

        raise
```

---

## Best Practices

### 1. Choose Right Strategy

```python
# ✅ Transient failures → Retry
retry_api = RetryPrimitive(unreliable_network_call, max_retries=3)

# ✅ Multiple providers → Fallback
fallback_llm = FallbackPrimitive(openai_llm, fallbacks=[anthropic_llm])

# ✅ Might hang → Timeout
timeout_op = TimeoutPrimitive(slow_operation, timeout_seconds=30)

# ✅ Distributed transaction → Compensation
saga = CompensationPrimitive([(step1, rollback1), (step2, rollback2)])
```

### 2. Layer Error Handling

```python
# ✅ Good: Multiple layers of protection
workflow = (
    TimeoutPrimitive(           # Outer: Prevent hanging
        RetryPrimitive(          # Middle: Handle transient failures
            FallbackPrimitive(   # Inner: Provide alternatives
                primary=main_operation,
                fallbacks=[backup_operation]
            ),
            max_retries=3
        ),
        timeout_seconds=30
    )
)
```

### 3. Log Errors with Context

```python
# ✅ Good: Rich error context
logger.error(
    "operation_failed",
    correlation_id=context.correlation_id,
    workflow_id=context.workflow_id,
    operation="llm_call",
    error_type=type(e).__name__,
    retry_count=retry_count,
    exc_info=True
)

# ❌ Bad: Minimal context
print(f"Error: {e}")
```

### 4. Test Error Paths

```python
import pytest

@pytest.mark.asyncio
async def test_retry_on_transient_failure():
    """Test retry behavior."""

    call_count = 0

    async def flaky_operation(data, context):
        nonlocal call_count
        call_count += 1

        if call_count < 3:
            raise ValueError("Transient failure")

        return {"success": True}

    retry_op = RetryPrimitive(flaky_operation, max_retries=5)

    result = await retry_op.execute({}, WorkflowContext()) # This is a code example, will address later if needed

    assert result["success"]
    assert call_count == 3  # Failed twice, succeeded third time
```

---

## Anti-Patterns

### ❌ Don't Catch and Ignore

```python
# Bad: Swallows errors
async def bad_operation(data: dict, context: WorkflowContext) -> dict: # This is a code example, will address later if needed
    try:
        return await risky_operation(data)
    except Exception:
        return {}  # Silent failure - bad!

# Good: Let primitives handle errors
retry_op = RetryPrimitive(risky_operation, max_retries=3)
```

### ❌ Don't Retry Forever

```python
# Bad: Infinite retries
bad_retry = RetryPrimitive(operation, max_retries=999999)

# Good: Reasonable retry limit
good_retry = RetryPrimitive(operation, max_retries=3)
```

### ❌ Don't Mix Manual and Primitive Error Handling

```python
# Bad: Mixing patterns
async def mixed_handling(data, context):
    try:
        retry_op = RetryPrimitive(operation, max_retries=3)
        return await retry_op.execute(data, context)
    except Exception:
        # Manual handling defeats the purpose
        return await fallback()

# Good: Compose primitives
workflow = FallbackPrimitive(
    primary=RetryPrimitive(operation, max_retries=3),
    fallbacks=[fallback]
)
```

---

## Related Patterns

- [[TTA.dev/Patterns/Resilience]] - Building resilient systems
- [[TTA.dev/Patterns/Observability]] - Monitoring errors
- [[TTA.dev/Patterns/Testing]] - Testing error scenarios

---

## Related Primitives

- [[RetryPrimitive]] - Retry with backoff
- [[FallbackPrimitive]] - Graceful degradation
- [[TimeoutPrimitive]] - Timeout protection
- [[CompensationPrimitive]] - Saga pattern
- [[CircuitBreakerPrimitive]] - Circuit breaker

---

## Related Examples

- [[TTA.dev/Examples/Error Handling]] - Comprehensive examples
- [[TTA.dev/Examples/RAG Workflow]] - Error handling in RAG
- [[Production]] - Production error handling

---

**Category:** Error Handling Pattern
**Complexity:** Medium to High
**Status:** Production-ready

- [[Project Hub]]


---
**Logseq:** [[TTA.dev/_archive/Nested_copies/Framework/Logseq/Pages/Tta.dev___patterns___error handling]]
