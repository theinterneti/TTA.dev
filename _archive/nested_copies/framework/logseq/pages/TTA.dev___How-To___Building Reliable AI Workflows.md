# How-To: Building Reliable AI Workflows

type:: [[How-To]]
category:: [[Reliability]]
difficulty:: [[Intermediate]]
estimated-time:: 45 minutes
target-audience:: [[Backend Developers]], [[AI Engineers]], [[DevOps]]
primitives-used:: [[RetryPrimitive]], [[FallbackPrimitive]], [[TimeoutPrimitive]], [[CachePrimitive]], [[CircuitBreaker]]

---

## Overview

- id:: building-reliable-workflows-overview
  **Building reliable AI workflows** requires layering multiple resilience patterns to handle failures gracefully. This guide shows you how to combine retry, fallback, timeout, cache, and circuit breaker patterns to build production-grade AI systems that maintain >99.9% availability.

---

## Prerequisites

{{embed ((prerequisites-full))}}

**Should have read:**
- [[TTA.dev/Guides/Error Handling Patterns]] - Recovery strategies
- [[TTA.dev/Guides/Agentic Primitives]] - Core concepts
- [[TTA.dev/Primitives/RetryPrimitive]] - Retry patterns
- [[TTA.dev/Primitives/FallbackPrimitive]] - Fallback strategies

---

## The Reliability Stack

### Core Layers

```
┌─────────────────────────────────────┐
│      User Request                   │
└──────────────┬──────────────────────┘
               ↓
┌─────────────────────────────────────┐
│  Layer 1: Cache (Fastest path)      │  ← 70% requests (cache hits)
└──────────────┬──────────────────────┘
               ↓ Cache miss
┌─────────────────────────────────────┐
│  Layer 2: Timeout (Prevent hang)    │  ← Max 30s wait
└──────────────┬──────────────────────┘
               ↓
┌─────────────────────────────────────┐
│  Layer 3: Circuit Breaker (Fail     │  ← Prevent cascading failures
│             fast if service down)    │
└──────────────┬──────────────────────┘
               ↓
┌─────────────────────────────────────┐
│  Layer 4: Retry (Handle transient)  │  ← 3 attempts with backoff
└──────────────┬──────────────────────┘
               ↓
┌─────────────────────────────────────┐
│  Layer 5: Primary Service           │  ← Best quality
└──────────────┬──────────────────────┘
               ↓ Failure
┌─────────────────────────────────────┐
│  Layer 6: Fallback (Degraded)       │  ← Good quality
└──────────────┬──────────────────────┘
               ↓ Failure
┌─────────────────────────────────────┐
│  Layer 7: Final Fallback (Basic)    │  ← Always succeeds
└──────────────┬──────────────────────┘
               ↓
┌─────────────────────────────────────┐
│      Response to User               │
└─────────────────────────────────────┘
```

---

## Step 1: Start Simple

**Goal:** Get basic functionality working first.

### Simple Workflow (No Reliability)

```python
from tta_dev_primitives import WorkflowPrimitive, WorkflowContext

class GPT4Primitive(WorkflowPrimitive[dict, dict]):
    """Call GPT-4 API."""
    async def execute(self, input_data: dict, context: WorkflowContext) -> dict:
        # This will fail if API is down, rate limited, or times out!
        response = await openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": input_data["query"]}]
        )
        return {"response": response.choices[0].message.content}

# Usage
workflow = GPT4Primitive()

# Problem: What if API is down? Rate limited? Times out?
# Result: Hard failure, user sees error 😞
```

**Reliability: 90%** (API uptime)

---

## Step 2: Add Retry

**Goal:** Handle transient failures (network blips, rate limits).

### With Retry

```python
from tta_dev_primitives.recovery import RetryPrimitive

# Wrap with retry
workflow = RetryPrimitive(
    primitive=GPT4Primitive(),
    max_retries=3,
    backoff_strategy="exponential",
    initial_delay=1.0,
    max_delay=10.0
)

# Execution flow:
# 1. Try GPT-4 → Fails (network blip)
# 2. Wait 1s, retry → Fails (still down)
# 3. Wait 2s, retry → Fails (still down)
# 4. Wait 4s, retry → Success! ✅

# Reliability: 90% + (10% * 50% recovery) = 95%
```

**When Retry Helps:**
- Transient network failures
- Temporary rate limiting
- Brief service outages (<10s)

**When Retry Doesn't Help:**
- Service completely down
- Invalid API key
- Malformed request
- Service degradation (500 errors)

---

## Step 3: Add Timeout

**Goal:** Prevent indefinite hangs.

### With Retry + Timeout

```python
from tta_dev_primitives.recovery import RetryPrimitive, TimeoutPrimitive

# Add timeout to each retry attempt
with_timeout = TimeoutPrimitive(
    primitive=GPT4Primitive(),
    timeout_seconds=30.0  # Max 30s per attempt
)

# Wrap with retry
workflow = RetryPrimitive(
    primitive=with_timeout,
    max_retries=3,
    backoff_strategy="exponential"
)

# Execution flow:
# 1. Try GPT-4 (timeout 30s) → Hangs, timeout after 30s ⏱️
# 2. Wait 1s, retry → Hangs, timeout after 30s ⏱️
# 3. Wait 2s, retry → Success in 2s! ✅

# Total max time: (30s * 3 attempts) + (1s + 2s + 4s backoff) = ~97s
```

**Timeout Guidelines:**

| Operation Type | Timeout |
|----------------|---------|
| GPT-3.5 | 10s |
| GPT-4 | 30s |
| Claude | 45s |
| Custom ML | 60s |
| Database | 5s |
| External API | 15s |

---

## Step 4: Add Fallback

**Goal:** Graceful degradation if primary fails.

### With Retry + Timeout + Fallback

```python
from tta_dev_primitives.recovery import FallbackPrimitive

class GPT35Primitive(WorkflowPrimitive[dict, dict]):
    """Faster, cheaper fallback."""
    async def execute(self, input_data: dict, context: WorkflowContext) -> dict:
        response = await openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": input_data["query"]}]
        )
        return {
            "response": response.choices[0].message.content,
            "model": "gpt-3.5-turbo",
            "fallback": True
        }

class CachedResponsesPrimitive(WorkflowPrimitive[dict, dict]):
    """Pre-computed responses for common queries."""
    async def execute(self, input_data: dict, context: WorkflowContext) -> dict:
        # Check if query matches common patterns
        query = input_data["query"].lower()

        if "help" in query:
            return {
                "response": "I'm here to help! Please describe your issue.",
                "model": "cached",
                "fallback": True
            }
        elif "hours" in query or "open" in query:
            return {
                "response": "We're open Monday-Friday 9am-5pm EST.",
                "model": "cached",
                "fallback": True
            }
        else:
            return {
                "response": "I apologize, but I'm temporarily unavailable. Please try again in a few minutes.",
                "model": "cached",
                "fallback": True
            }

# Build reliability stack
primary_with_timeout = TimeoutPrimitive(GPT4Primitive(), timeout_seconds=30.0)
primary_with_retry = RetryPrimitive(primary_with_timeout, max_retries=3)

fallback_with_timeout = TimeoutPrimitive(GPT35Primitive(), timeout_seconds=10.0)
fallback_with_retry = RetryPrimitive(fallback_with_timeout, max_retries=2)

workflow = FallbackPrimitive(
    primary=primary_with_retry,
    fallbacks=[
        fallback_with_retry,  # Try GPT-3.5 if GPT-4 fails
        CachedResponsesPrimitive()  # Always succeeds
    ]
)

# Execution flow:
# 1. Try GPT-4 (with timeout + retry) → Fails after 3 attempts
# 2. Try GPT-3.5 (with timeout + retry) → Fails after 2 attempts
# 3. Use cached response → Always succeeds! ✅

# Reliability: ~99.9% (only fails if all layers fail)
```

**Fallback Strategy:**

```
Best Quality (Slow, Expensive) → Good Quality (Fast, Cheap) → Cached (Instant, Free)
    GPT-4 ($10/1M)          →      GPT-3.5 ($0.50/1M)      →  Templates ($0)
```

---

## Step 5: Add Cache

**Goal:** Reduce cost and latency for repeated queries.

### Full Reliability Stack

```python
from tta_dev_primitives.performance import CachePrimitive

# Build complete stack
primary_with_timeout = TimeoutPrimitive(GPT4Primitive(), timeout_seconds=30.0)
primary_with_retry = RetryPrimitive(primary_with_timeout, max_retries=3)

fallback_with_timeout = TimeoutPrimitive(GPT35Primitive(), timeout_seconds=10.0)
fallback_with_retry = RetryPrimitive(fallback_with_timeout, max_retries=2)

with_fallback = FallbackPrimitive(
    primary=primary_with_retry,
    fallbacks=[fallback_with_retry, CachedResponsesPrimitive()]
)

# Add cache on top of everything
workflow = CachePrimitive(
    primitive=with_fallback,
    ttl_seconds=3600,  # 1 hour
    max_size=10000,
    key_fn=lambda data, ctx: data["query"]
)

# Execution flow for repeated query:
# First request:
#   Cache miss → Execute full stack → Return + Cache result
#   Time: ~2s, Cost: $0.01
#
# Second request (within 1 hour):
#   Cache hit → Return cached result immediately
#   Time: ~1ms, Cost: $0.00 ✅
#
# Result:
#   - 70% cache hit rate → 70% cost savings
#   - 70% requests < 10ms latency
#   - 99.9%+ reliability
```

**Cache Configuration:**

| Scenario | TTL | Max Size | Hit Rate |
|----------|-----|----------|----------|
| FAQs | 24h | 1,000 | 80% |
| Product info | 4h | 5,000 | 60% |
| User queries | 1h | 10,000 | 40% |
| Real-time data | 5min | 20,000 | 20% |

---

## Step 6: Add Circuit Breaker

**Goal:** Fail fast when service is down, prevent resource exhaustion.

### Production-Ready Stack

```python
class CircuitBreakerPrimitive(WorkflowPrimitive[dict, dict]):
    """Circuit breaker implementation."""

    def __init__(
        self,
        primitive: WorkflowPrimitive,
        failure_threshold: int = 5,
        success_threshold: int = 2,
        timeout_seconds: float = 60.0
    ):
        self.primitive = primitive
        self.failure_threshold = failure_threshold
        self.success_threshold = success_threshold
        self.timeout_seconds = timeout_seconds

        # State tracking
        self.state = "closed"  # closed, open, half_open
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None

    async def execute(self, input_data: dict, context: WorkflowContext) -> dict:
        import time

        # Check if circuit should transition from open to half-open
        if self.state == "open":
            if time.time() - self.last_failure_time > self.timeout_seconds:
                self.state = "half_open"
                self.success_count = 0
            else:
                # Circuit is open, fail fast
                raise Exception(f"Circuit breaker is OPEN - service unavailable (retrying in {self.timeout_seconds}s)")

        try:
            # Attempt execution
            result = await self.primitive.execute(input_data, context)

            # Success!
            if self.state == "half_open":
                self.success_count += 1
                if self.success_count >= self.success_threshold:
                    # Recovered! Close circuit
                    self.state = "closed"
                    self.failure_count = 0

            return result

        except Exception as e:
            # Failure!
            self.failure_count += 1
            self.last_failure_time = time.time()

            if self.state == "half_open":
                # Failed during recovery, go back to open
                self.state = "open"
            elif self.failure_count >= self.failure_threshold:
                # Too many failures, open circuit
                self.state = "open"

            raise e

# Add circuit breaker before retry
primary_with_timeout = TimeoutPrimitive(GPT4Primitive(), timeout_seconds=30.0)
primary_with_circuit_breaker = CircuitBreakerPrimitive(
    primitive=primary_with_timeout,
    failure_threshold=5,  # Open after 5 failures
    success_threshold=2,  # Close after 2 successes
    timeout_seconds=60.0  # Wait 60s before retry
)
primary_with_retry = RetryPrimitive(primary_with_circuit_breaker, max_retries=3)

# ... rest of stack same as above ...

# Benefits:
# - If GPT-4 is down, circuit opens after 5 failures
# - Subsequent requests fail fast (no wasted API calls)
# - After 60s, circuit tries again (half-open)
# - If successful 2x, circuit closes (back to normal)
```

**Circuit Breaker States:**

```
┌──────────┐
│  Closed  │ Normal operation
│ (Normal) │
└────┬─────┘
     │
     │ 5 failures
     ↓
┌──────────┐
│   Open   │ Failing fast, no service calls
│ (Failing)│
└────┬─────┘
     │
     │ 60s timeout
     ↓
┌──────────┐
│Half-Open │ Testing if service recovered
│(Testing) │
└────┬─────┘
     │
     ├─→ 2 successes → Back to Closed ✅
     └─→ 1 failure → Back to Open ❌
```

---

## Complete Production Stack

### Final Implementation

```python
from tta_dev_primitives import WorkflowPrimitive, WorkflowContext
from tta_dev_primitives.recovery import RetryPrimitive, FallbackPrimitive, TimeoutPrimitive
from tta_dev_primitives.performance import CachePrimitive

class ProductionAIWorkflow:
    """Production-ready AI workflow with all reliability layers."""

    def __init__(self):
        # Layer 7: Primary service (GPT-4)
        primary = GPT4Primitive()

        # Layer 6: Circuit breaker
        with_circuit_breaker = CircuitBreakerPrimitive(
            primitive=primary,
            failure_threshold=5,
            success_threshold=2,
            timeout_seconds=60.0
        )

        # Layer 5: Timeout
        with_timeout = TimeoutPrimitive(
            primitive=with_circuit_breaker,
            timeout_seconds=30.0
        )

        # Layer 4: Retry
        with_retry = RetryPrimitive(
            primitive=with_timeout,
            max_retries=3,
            backoff_strategy="exponential",
            initial_delay=1.0,
            max_delay=10.0
        )

        # Fallback chain: GPT-3.5 → Cached responses
        fallback_gpt35 = RetryPrimitive(
            TimeoutPrimitive(GPT35Primitive(), timeout_seconds=10.0),
            max_retries=2
        )

        # Layer 3: Fallback
        with_fallback = FallbackPrimitive(
            primary=with_retry,
            fallbacks=[fallback_gpt35, CachedResponsesPrimitive()]
        )

        # Layer 2: Timeout (overall workflow timeout)
        with_overall_timeout = TimeoutPrimitive(
            primitive=with_fallback,
            timeout_seconds=120.0  # 2 minutes max total
        )

        # Layer 1: Cache
        self.workflow = CachePrimitive(
            primitive=with_overall_timeout,
            ttl_seconds=3600,
            max_size=10000,
            key_fn=lambda data, ctx: data["query"]
        )

    async def execute(self, query: str) -> dict:
        """Execute workflow with full reliability stack."""
        context = WorkflowContext(
            correlation_id=f"query-{hash(query)}",
            data={"timestamp": time.time()}
        )

        return await self.workflow.execute({"query": query}, context)

# Usage
workflow = ProductionAIWorkflow()

# This workflow has:
# ✅ 70% cache hit rate (1ms latency, $0 cost)
# ✅ 99.9%+ reliability (multiple fallbacks)
# ✅ < 2min max latency (overall timeout)
# ✅ Graceful degradation (always returns response)
# ✅ Cost optimization (cache + cheaper fallbacks)
# ✅ Fast failure (circuit breaker)
```

---

## Monitoring & Metrics

### Key Metrics to Track

```python
from tta_dev_primitives import WorkflowContext

# Track metrics in context
context = WorkflowContext(
    correlation_id="req-123",
    data={
        "start_time": time.time(),
        "cache_hit": False,
        "fallback_used": False,
        "circuit_breaker_state": "closed",
        "retry_count": 0
    }
)

# After execution, log metrics
metrics = {
    "latency_ms": (time.time() - context.data["start_time"]) * 1000,
    "cache_hit": context.data["cache_hit"],
    "fallback_used": context.data["fallback_used"],
    "circuit_breaker_state": context.data["circuit_breaker_state"],
    "retry_count": context.data["retry_count"]
}

# Send to monitoring system (Prometheus, Datadog, etc.)
```

**Critical Metrics:**

| Metric | Alert Threshold | Action |
|--------|----------------|--------|
| Cache hit rate | < 50% | Increase TTL or cache size |
| Fallback rate | > 10% | Investigate primary service |
| Circuit breaker open | > 5min | Page on-call engineer |
| P95 latency | > 5s | Optimize or scale |
| Error rate | > 1% | Check logs, alert team |

---

## Testing Reliability

### Unit Tests

```python
import pytest
from tta_dev_primitives.testing import MockPrimitive

@pytest.mark.asyncio
async def test_fallback_on_primary_failure():
    """Test fallback when primary fails."""

    # Mock primary to always fail
    primary = MockPrimitive(side_effect=Exception("Service down"))

    # Mock fallback to succeed
    fallback = MockPrimitive(return_value={"response": "Fallback response"})

    # Build workflow
    workflow = FallbackPrimitive(primary=primary, fallbacks=[fallback])

    # Execute
    context = WorkflowContext()
    result = await workflow.execute({"query": "test"}, context)

    # Verify fallback was used
    assert result["response"] == "Fallback response"
    assert primary.call_count == 1
    assert fallback.call_count == 1

@pytest.mark.asyncio
async def test_cache_hit():
    """Test cache hit avoids execution."""

    # Mock expensive primitive
    expensive = MockPrimitive(return_value={"response": "Expensive result"})

    # Wrap with cache
    workflow = CachePrimitive(expensive, ttl_seconds=60)

    context = WorkflowContext()

    # First call - cache miss
    result1 = await workflow.execute({"query": "test"}, context)
    assert expensive.call_count == 1

    # Second call - cache hit
    result2 = await workflow.execute({"query": "test"}, context)
    assert expensive.call_count == 1  # Not called again!

    # Results should be identical
    assert result1 == result2

@pytest.mark.asyncio
async def test_circuit_breaker_opens():
    """Test circuit breaker opens after threshold failures."""

    # Mock failing primitive
    failing = MockPrimitive(side_effect=Exception("Always fails"))

    # Circuit breaker with low threshold for testing
    circuit_breaker = CircuitBreakerPrimitive(
        primitive=failing,
        failure_threshold=3,
        timeout_seconds=1.0
    )

    context = WorkflowContext()

    # Fail 3 times to open circuit
    for i in range(3):
        with pytest.raises(Exception):
            await circuit_breaker.execute({"query": "test"}, context)

    # Circuit should be open now
    assert circuit_breaker.state == "open"

    # Next call should fail fast (without calling primitive)
    with pytest.raises(Exception, match="Circuit breaker is OPEN"):
        await circuit_breaker.execute({"query": "test"}, context)

    # Primitive should only be called 3 times (not 4)
    assert failing.call_count == 3
```

### Integration Tests

```python
@pytest.mark.asyncio
async def test_full_reliability_stack():
    """Test complete reliability stack end-to-end."""

    # Build production stack
    workflow = ProductionAIWorkflow()

    # Test scenarios

    # 1. Normal operation
    result = await workflow.execute("What is Python?")
    assert "Python" in result["response"]

    # 2. Cache hit (second query)
    result = await workflow.execute("What is Python?")
    assert result.get("cached") is True

    # 3. Simulate primary failure (use fallback)
    # ... (inject failure) ...
    result = await workflow.execute("Complex query")
    assert result.get("fallback") is True

    # 4. Verify metrics
    metrics = workflow.get_metrics()
    assert metrics["total_requests"] > 0
    assert metrics["cache_hit_rate"] >= 0.3
    assert metrics["fallback_rate"] < 0.2
```

---

## Troubleshooting

### High Fallback Rate (>10%)

**Symptoms:**
- Primary service failing frequently
- Degraded response quality
- Increased latency

**Solutions:**

1. **Check primary service health:**
   ```bash
   curl https://api.openai.com/v1/models
   ```

2. **Review circuit breaker state:**
   ```python
   print(f"Circuit breaker: {circuit_breaker.state}")
   print(f"Failures: {circuit_breaker.failure_count}")
   ```

3. **Check rate limits:**
   ```python
   # Monitor API rate limit headers
   if response.headers.get("x-ratelimit-remaining") < 10:
       # Approaching rate limit
       pass
   ```

4. **Adjust retry strategy:**
   ```python
   # Increase backoff delays
   RetryPrimitive(
       primitive=primary,
       max_retries=3,
       backoff_strategy="exponential",
       initial_delay=2.0,  # Increased from 1.0
       max_delay=30.0      # Increased from 10.0
   )
   ```

### Low Cache Hit Rate (<50%)

**Symptoms:**
- High costs
- Slow response times
- Cache not effective

**Solutions:**

1. **Increase TTL:**
   ```python
   CachePrimitive(
       primitive=workflow,
       ttl_seconds=7200,  # Increased from 3600 (1h → 2h)
       max_size=10000
   )
   ```

2. **Normalize cache keys:**
   ```python
   def normalize_key(data: dict, context: WorkflowContext) -> str:
       query = data["query"].lower().strip()
       # Remove punctuation, extra spaces
       query = re.sub(r'[^\w\s]', '', query)
       query = re.sub(r'\s+', ' ', query)
       return query

   CachePrimitive(
       primitive=workflow,
       key_fn=normalize_key  # Better cache hits
   )
   ```

3. **Increase cache size:**
   ```python
   CachePrimitive(
       primitive=workflow,
       ttl_seconds=3600,
       max_size=50000  # Increased from 10000
   )
   ```

### Circuit Breaker Stuck Open

**Symptoms:**
- All requests failing fast
- No recovery after service comes back
- Circuit remains open

**Solutions:**

1. **Check timeout settings:**
   ```python
   CircuitBreakerPrimitive(
       primitive=primary,
       timeout_seconds=30.0  # Reduce from 60s for faster recovery
   )
   ```

2. **Manually reset circuit:**
   ```python
   circuit_breaker.state = "half_open"
   circuit_breaker.failure_count = 0
   ```

3. **Adjust thresholds:**
   ```python
   CircuitBreakerPrimitive(
       primitive=primary,
       failure_threshold=10,  # More tolerant (was 5)
       success_threshold=1    # Faster recovery (was 2)
   )
   ```

---

## Best Practices

### DO ✅

1. **Start simple, add layers incrementally**
   - Begin with basic workflow
   - Add retry for transient failures
   - Add fallback for reliability
   - Add cache for cost/latency
   - Add circuit breaker for protection

2. **Monitor everything**
   - Cache hit rate
   - Fallback usage rate
   - Circuit breaker state
   - Latency percentiles (P50, P95, P99)
   - Error rates per layer

3. **Test failure scenarios**
   - Primary service down
   - Rate limiting
   - Timeouts
   - Circuit breaker triggers
   - Cache eviction

4. **Use appropriate timeouts**
   - Set per-operation timeouts
   - Set overall workflow timeout
   - Account for retries in total time

5. **Log everything**
   ```python
   context.checkpoint("cache.miss")
   context.checkpoint("primary.start")
   context.checkpoint("primary.failed")
   context.checkpoint("fallback.start")
   context.checkpoint("fallback.success")
   ```

### DON'T ❌

1. **Don't over-retry**
   - 3-5 retries max
   - Use exponential backoff
   - Don't retry non-transient errors

2. **Don't ignore metrics**
   - Always monitor cache hit rate
   - Track fallback usage
   - Alert on anomalies

3. **Don't skip timeouts**
   - Always set timeouts
   - Account for worst-case latency
   - Test timeout behavior

4. **Don't cache everything**
   - Cache read-heavy operations
   - Skip caching for real-time data
   - Consider cache invalidation

5. **Don't trust single fallback**
   - Always have multiple fallbacks
   - Final fallback should never fail
   - Test all fallback paths

---

## Next Steps

- **Add observability:** [[TTA.dev/Guides/Observability]]
- **Optimize costs:** [[TTA.dev/Guides/Cost Optimization]]
- **Deploy to production:** [[TTA.dev/Guides/Production Deployment]]
- **Learn patterns:** [[TTA.dev/Guides/Architecture Patterns]]

---

## Key Takeaways

1. **Layer reliability patterns** - Each layer handles different failure modes
2. **Cache first** - 70%+ cache hit rate = 70% cost savings
3. **Always have fallbacks** - Graceful degradation is better than hard failure
4. **Monitor everything** - You can't improve what you don't measure
5. **Test failures** - Failure scenarios are more important than happy path

**Remember:** Start simple, measure, add reliability layers based on actual needs.

---

**Created:** [[2025-10-30]]
**Last Updated:** [[2025-10-30]]
**Estimated Time:** 45 minutes
**Difficulty:** [[Intermediate]]

- [[Project Hub]]

---
**Logseq:** [[TTA.dev/_archive/Nested_copies/Framework/Logseq/Pages/Tta.dev___how-to___building reliable ai workflows]]
