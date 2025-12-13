# Whiteboard - Recovery Patterns Flow

**Visual guide to error handling and resilience patterns in TTA.dev**

---

## Purpose

Interactive whiteboard showing recovery patterns:
- Retry with exponential backoff
- Fallback cascades
- Circuit breaker (timeout)
- Saga pattern (compensation)
- Combined recovery stacks

---

## Pattern 1: Retry with Exponential Backoff

### Visual Flow

```text
Request → [Attempt 1] → Success? ──Yes──> Return
              ↓
             Fail
              ↓
          Wait 1s
              ↓
         [Attempt 2] → Success? ──Yes──> Return
              ↓
             Fail
              ↓
          Wait 2s
              ↓
         [Attempt 3] → Success? ──Yes──> Return
              ↓
             Fail
              ↓
         Max Retries → Raise Error
```

### Code

```python
from tta_dev_primitives.recovery import RetryPrimitive

retry = RetryPrimitive(
    primitive=api_call,
    max_retries=3,
    backoff_strategy="exponential",
    initial_delay=1.0,
    jitter=True
)
```

### Related: [[TTA Primitives/RetryPrimitive]]

---

## Pattern 2: Fallback Cascade

### Visual Flow

```text
Request → [Primary Service] → Success? ──Yes──> Return
               ↓
              Fail
               ↓
          [Fallback 1] → Success? ──Yes──> Return
               ↓
              Fail
               ↓
          [Fallback 2] → Success? ──Yes──> Return
               ↓
              Fail
               ↓
         [Last Resort] → Success? ──Yes──> Return
               ↓
              Fail
               ↓
          Raise Error
```

### Code

```python
from tta_dev_primitives.recovery import FallbackPrimitive

fallback = FallbackPrimitive(
    primary=gpt4,
    fallbacks=[claude_sonnet, gemini_pro, llama_local]
)
```

### Related: [[TTA Primitives/FallbackPrimitive]]

---

## Pattern 3: Circuit Breaker (Timeout)

### Visual Flow

```text
Request → [Start Timer] → [Execute Operation]
              ↓                    ↓
         Timeout? <────────────────┘
              ↓
         Yes  │  No
              ↓  └──> Return Result
         [Cancel]
              ↓
       Raise Timeout
```

### Code

```python
from tta_dev_primitives.recovery import TimeoutPrimitive

timeout = TimeoutPrimitive(
    primitive=slow_operation,
    timeout_seconds=30.0,
    raise_on_timeout=True
)
```

### Related: [[TTA Primitives/TimeoutPrimitive]]

---

## Pattern 4: Saga Pattern (Compensation)

### Visual Flow

```text
Request
    ↓
[Step 1] → Success? ──No──> Raise Error
    ↓
   Yes
    ↓
[Step 2] → Success? ──No──> [Compensate Step 1] → Raise Error
    ↓
   Yes
    ↓
[Step 3] → Success? ──No──> [Compensate Step 2] → [Compensate Step 1] → Raise Error
    ↓
   Yes
    ↓
 Complete
```

### Code

```python
from tta_dev_primitives.recovery import CompensationPrimitive

saga = CompensationPrimitive(
    primitives=[
        (create_user, delete_user),
        (send_email, cancel_email),
        (activate_account, deactivate_account),
    ]
)
```

### Related: [[TTA Primitives/CompensationPrimitive]]

---

## Pattern 5: Combined Recovery Stack

### Visual Flow

```text
Request
    ↓
[Timeout Layer]
    ↓
[Retry Layer]
    ↓
[Fallback Layer]
    ↓
[Cache Layer]
    ↓
Success → Return
    ↓
  Fail → Propagate Error
```

### Code

```python
from tta_dev_primitives.recovery import (
    TimeoutPrimitive,
    RetryPrimitive,
    FallbackPrimitive
)
from tta_dev_primitives.performance import CachePrimitive

# Layer 1: Timeout
timed = TimeoutPrimitive(api_call, timeout=30)

# Layer 2: Retry
retried = RetryPrimitive(timed, max_retries=3)

# Layer 3: Fallback
fallback = FallbackPrimitive(
    primary=retried,
    fallbacks=[backup_api, cached_response]
)

# Layer 4: Cache
cached = CachePrimitive(fallback, ttl=3600)

# Full stack
production_ready = cached
```

---

## Real-World Example: Resilient LLM Service

### Visual Architecture

```text
User Request
      ↓
[Input Validation]
      ↓
[Rate Limiter] ─── Exceeded? ──> 429 Error
      ↓
  Allowed
      ↓
[Cache Check] ─── Hit? ──> Return Cached
      ↓
    Miss
      ↓
[Timeout: 30s]
      ↓
[Retry: 3 attempts]
      ↓
[Router: GPT-4/Claude/Gemini]
      ↓
[Fallback: Local LLM]
      ↓
[Validation]
      ↓
[Cache Result]
      ↓
Response
```

### Implementation

```python
from tta_dev_primitives import WorkflowContext
from tta_dev_primitives.recovery import (
    TimeoutPrimitive,
    RetryPrimitive,
    FallbackPrimitive
)
from tta_dev_primitives.performance import CachePrimitive
from tta_dev_primitives.core import RouterPrimitive

# Build recovery stack
llm_service = (
    input_validator >>
    rate_limiter >>
    CachePrimitive(ttl=3600) >>
    TimeoutPrimitive(timeout=30) >>
    RetryPrimitive(max_retries=3, backoff="exponential") >>
    RouterPrimitive(routes={"fast": gpt4_mini, "quality": gpt4}) >>
    FallbackPrimitive(
        primary=cloud_llm,
        fallbacks=[local_llm, cached_fallback]
    ) >>
    validator
)
```

---

## Error Handling Strategies

### Strategy Matrix

| Pattern | Use When | Latency Impact | Reliability Gain |
|---------|----------|----------------|------------------|
| **Retry** | Transient failures | Medium (backoff delays) | High |
| **Fallback** | Service unavailability | Low (immediate switch) | Very High |
| **Timeout** | Hanging operations | None (caps max time) | Medium |
| **Compensation** | Distributed transactions | Medium (rollback time) | High |

### Decision Tree

```text
What kind of failure?

Transient (network blip)
    ↓
Use Retry

Service unavailable
    ↓
Use Fallback

Operation too slow
    ↓
Use Timeout

Multi-step transaction
    ↓
Use Compensation (Saga)

Multiple issues
    ↓
Combine patterns
```

---

## Whiteboard Design Elements

### Shapes

- **Rectangles:** Operations/Steps
- **Diamonds:** Decision points
- **Circles:** Start/End points
- **Hexagons:** Error handlers

### Colors

- **Green:** Success paths
- **Red:** Error paths
- **Yellow:** Decision points
- **Blue:** Recovery actions
- **Purple:** Compensation

### Annotations

- Timing information (delays, timeouts)
- Retry counts
- Fallback order
- Code snippets as sticky notes

---

## Metrics to Track

### Per Pattern

**Retry:**
- Attempt count distribution
- Success rate by attempt
- Total retry overhead

**Fallback:**
- Fallback usage rate
- Primary vs fallback latency
- Cascade depth

**Timeout:**
- Timeout frequency
- Operation duration distribution
- Circuit breaker state

**Compensation:**
- Rollback frequency
- Compensation success rate
- Partial completion rate

---

## Testing Scenarios

### Test Each Pattern

```python
# Test retry
async def test_retry_recovers_from_transient_failure():
    # Simulate transient failure
    ...

# Test fallback
async def test_fallback_uses_backup_service():
    # Primary fails, fallback succeeds
    ...

# Test timeout
async def test_timeout_cancels_slow_operation():
    # Operation exceeds timeout
    ...

# Test compensation
async def test_compensation_rolls_back_on_failure():
    # Step 2 fails, step 1 compensated
    ...
```

---

## Related Pages

- [[TTA Primitives]]
- [[TTA.dev/Architecture]]
- [[PRIMITIVES CATALOG]]
- [[Whiteboard - TTA.dev Architecture Overview]]
- [[How to Add Observability to Workflows]]

---

## Instructions for Whiteboard

1. Create whiteboard in Logseq
2. Add each pattern as a section
3. Use flow diagram style
4. Color code success/error paths
5. Link to primitive documentation
6. Export diagrams for docs

---

**Created:** [[2025-10-31]]
**Status:** Template for interactive whiteboard
**Related:** platform/primitives/src/tta_dev_primitives/recovery/


---
**Logseq:** [[TTA.dev/Logseq/Pages/Whiteboard - recovery patterns flow]]
