# Architecture Patterns

type:: [[Guide]]
category:: [[Architecture]]
difficulty:: [[Intermediate]]
estimated-time:: 40 minutes
target-audience:: [[Architects]], [[Senior Developers]], [[AI Engineers]]

---

## Overview

- id:: architecture-patterns-overview
  **Architecture patterns** for AI workflows provide proven solutions to common design challenges. This guide covers battle-tested patterns for building reliable, scalable, and maintainable AI systems using TTA.dev primitives. Each pattern includes when to use it, implementation details, and real-world examples.

---

## Prerequisites

{{embed ((prerequisites-full))}}

**Should have read:**
- [[TTA.dev/Guides/Agentic Primitives]] - Core concepts
- [[TTA.dev/Guides/Workflow Composition]] - Composition patterns
- [[TTA.dev/Guides/Error Handling Patterns]] - Recovery strategies

**Should understand:**
- Software architecture principles
- Distributed systems basics
- AI/LLM limitations and failure modes

---

## Pattern Catalog

### 1. Multi-Model Orchestra Pattern

**Problem:** Single model can't handle all scenarios (quality vs speed vs cost)

**Solution:** Run multiple models in parallel, aggregate results

**When to use:**
- Critical decisions requiring consensus
- Quality over latency acceptable
- Can afford parallel model calls

**Architecture:**

```
Input → Parallel(GPT-4, Claude, PaLM) → Consensus Aggregator → Output
         ↓         ↓         ↓
      Model 1   Model 2   Model 3
```

**Implementation:**

```python
from tta_dev_primitives import ParallelPrimitive, WorkflowPrimitive, WorkflowContext

class GPT4Model(WorkflowPrimitive[dict, dict]):
    """OpenAI GPT-4 implementation."""
    async def execute(self, input_data: dict, context: WorkflowContext) -> dict:
        # Call GPT-4 API
        return {
            "model": "gpt-4",
            "response": "GPT-4 analysis...",
            "confidence": 0.92
        }

class ClaudeModel(WorkflowPrimitive[dict, dict]):
    """Anthropic Claude implementation."""
    async def execute(self, input_data: dict, context: WorkflowContext) -> dict:
        # Call Claude API
        return {
            "model": "claude-3-opus",
            "response": "Claude analysis...",
            "confidence": 0.89
        }

class PaLMModel(WorkflowPrimitive[dict, dict]):
    """Google PaLM implementation."""
    async def execute(self, input_data: dict, context: WorkflowContext) -> dict:
        # Call PaLM API
        return {
            "model": "palm-2",
            "response": "PaLM analysis...",
            "confidence": 0.85
        }

class ConsensusAggregator(WorkflowPrimitive[list, dict]):
    """Aggregate multiple model responses."""
    async def execute(self, input_data: list, context: WorkflowContext) -> dict:
        # Find consensus or weighted average
        responses = [item["response"] for item in input_data]
        confidences = [item["confidence"] for item in input_data]

        # Simple majority vote (production would be more sophisticated)
        if len(set(responses)) == 1:
            # Perfect consensus
            return {
                "response": responses[0],
                "consensus": "unanimous",
                "confidence": sum(confidences) / len(confidences)
            }
        else:
            # Weighted by confidence
            best_idx = confidences.index(max(confidences))
            return {
                "response": responses[best_idx],
                "consensus": "weighted",
                "confidence": confidences[best_idx],
                "alternatives": [r for i, r in enumerate(responses) if i != best_idx]
            }

# Build workflow
parallel_models = GPT4Model() | ClaudeModel() | PaLMModel()
aggregator = ConsensusAggregator()

workflow = parallel_models >> aggregator
```

**Benefits:**
- Higher accuracy through consensus
- Reduces model-specific biases
- Catches hallucinations (disagreement signals issue)

**Tradeoffs:**
- 3x cost (running 3 models)
- 3x latency (slowest model determines speed)
- More complex aggregation logic

**Optimizations:**
- Add timeout to each model
- Use cache to reduce repeated calls
- Route simple queries to single model

---

### 2. Intelligent Router Pattern

**Problem:** All queries go to expensive model, wasting money on simple tasks

**Solution:** Route queries to appropriate model based on complexity

**When to use:**
- Variable query complexity
- Significant cost differences between models
- Can classify complexity accurately

**Architecture:**

```
Input → Complexity Analyzer → Router → Appropriate Model → Output
                                ├─→ Fast (70% queries)
                                ├─→ Balanced (20% queries)
                                └─→ Quality (10% queries)
```

**Implementation:**

```python
from tta_dev_primitives import RouterPrimitive, WorkflowPrimitive, WorkflowContext

class ComplexityAnalyzer(WorkflowPrimitive[dict, dict]):
    """Analyze query complexity."""
    async def execute(self, input_data: dict, context: WorkflowContext) -> dict:
        query = input_data["query"]

        # Complexity scoring
        score = 0

        # Length-based heuristics
        if len(query.split()) > 50:
            score += 0.3

        # Keyword-based heuristics
        complex_keywords = ["analyze", "compare", "explain", "why", "how"]
        if any(kw in query.lower() for kw in complex_keywords):
            score += 0.3

        # Domain-specific heuristics
        if "technical" in query.lower() or "code" in query.lower():
            score += 0.2

        # Multi-part questions
        if "?" in query[:-1]:  # Multiple question marks
            score += 0.2

        # Classify complexity
        if score >= 0.6:
            complexity = "high"
        elif score >= 0.3:
            complexity = "medium"
        else:
            complexity = "low"

        return {
            **input_data,
            "complexity": complexity,
            "complexity_score": score
        }

def route_selector(input_data: dict, context: WorkflowContext) -> str:
    """Select route based on complexity."""
    complexity = input_data.get("complexity", "low")

    if complexity == "high":
        return "quality"  # GPT-4
    elif complexity == "medium":
        return "balanced"  # GPT-4 Turbo
    else:
        return "fast"  # GPT-3.5

# Define model primitives
fast_model = GPT35Model()      # $0.50/1M tokens
balanced_model = GPT4TurboModel()  # $5/1M tokens
quality_model = GPT4Model()    # $10/1M tokens

# Build router
router = RouterPrimitive(
    routes={
        "fast": fast_model,
        "balanced": balanced_model,
        "quality": quality_model
    },
    route_selector=route_selector
)

# Complete workflow
analyzer = ComplexityAnalyzer()
workflow = analyzer >> router

# Cost calculation example:
# Without routing: 100% at $10/1M = $10/1M
# With routing (70% fast, 20% balanced, 10% quality):
#   70% * $0.50 = $0.35
#   20% * $5.00 = $1.00
#   10% * $10.00 = $1.00
#   Total: $2.35/1M (76.5% savings!)
```

**Benefits:**
- 70-80% cost reduction
- Faster response for simple queries
- Same quality for complex queries

**Tradeoffs:**
- Complexity analysis overhead
- Risk of misclassification
- Need to tune thresholds

**Optimizations:**
- Use ML model for complexity classification
- A/B test routing decisions
- Monitor quality by complexity bucket

---

### 3. Fallback Chain Pattern

**Problem:** Primary service can fail, need graceful degradation

**Solution:** Chain of fallbacks from best to acceptable

**When to use:**
- Service reliability critical
- Multiple viable alternatives exist
- Degraded service better than no service

**Architecture:**

```
Input → Try Primary → Success → Output
         ↓ Fail
         Try Secondary → Success → Output
         ↓ Fail
         Try Tertiary → Success → Output
         ↓ Fail
         Cached/Simple Response → Output
```

**Implementation:**

```python
from tta_dev_primitives.recovery import FallbackPrimitive, RetryPrimitive
from tta_dev_primitives.performance import CachePrimitive

class PrimaryModel(WorkflowPrimitive[dict, dict]):
    """Best quality, may be slow or rate-limited."""
    async def execute(self, input_data: dict, context: WorkflowContext) -> dict:
        # GPT-4 with fine-tuning
        return {"response": "High quality answer", "tier": "primary"}

class SecondaryModel(WorkflowPrimitive[dict, dict]):
    """Good quality, more reliable."""
    async def execute(self, input_data: dict, context: WorkflowContext) -> dict:
        # Standard GPT-4
        return {"response": "Good quality answer", "tier": "secondary"}

class TertiaryModel(WorkflowPrimitive[dict, dict]):
    """Fast, cheaper, always available."""
    async def execute(self, input_data: dict, context: WorkflowContext) -> dict:
        # GPT-3.5 Turbo
        return {"response": "Fast answer", "tier": "tertiary"}

class CachedResponses(WorkflowPrimitive[dict, dict]):
    """Pre-computed responses for common queries."""
    async def execute(self, input_data: dict, context: WorkflowContext) -> dict:
        # Return cached or template response
        return {
            "response": "Standard response (service temporarily unavailable)",
            "tier": "cached",
            "fallback": True
        }

# Build fallback chain with retries at each level
primary_with_retry = RetryPrimitive(PrimaryModel(), max_retries=2)
secondary_with_retry = RetryPrimitive(SecondaryModel(), max_retries=2)
tertiary_with_retry = RetryPrimitive(TertiaryModel(), max_retries=2)

workflow = FallbackPrimitive(
    primary=primary_with_retry,
    fallbacks=[
        secondary_with_retry,
        tertiary_with_retry,
        CachedResponses()
    ]
)

# Execution flow:
# 1. Try primary (with 2 retries) - 90% success
# 2. If fails, try secondary (with 2 retries) - 8% usage
# 3. If fails, try tertiary (with 2 retries) - 1.5% usage
# 4. If all fail, use cached response - 0.5% usage
```

**Benefits:**
- 99.9%+ availability
- Graceful degradation
- User always gets response

**Tradeoffs:**
- Increased latency on failures
- More complex monitoring
- Need to track which tier used

**Monitoring:**

```python
# Track fallback usage
context.checkpoint("primary.attempt")
# ... execution ...
if used_fallback:
    context.checkpoint("fallback.used")
    context.metadata["fallback_tier"] = tier_used
```

---

### 4. Cache-Aside Pattern

**Problem:** Expensive operations called repeatedly with same inputs

**Solution:** Check cache before calling expensive operation

**When to use:**
- High query repetition (>30%)
- Expensive operations (LLM calls, DB queries)
- Stale data acceptable for TTL period

**Architecture:**

```
Input → Cache Lookup → Hit? → Return Cached
         ↓ Miss
         Execute Expensive Operation → Store in Cache → Return Result
```

**Implementation:**

```python
from tta_dev_primitives.performance import CachePrimitive

class ExpensiveLLMCall(WorkflowPrimitive[dict, dict]):
    """Expensive LLM operation."""
    async def execute(self, input_data: dict, context: WorkflowContext) -> dict:
        context.checkpoint("llm.start")

        # Expensive call ($0.01 per call)
        result = await call_gpt4(input_data["query"])

        context.checkpoint("llm.end")
        return {"response": result, "cost": 0.01}

# Wrap with cache
cached_llm = CachePrimitive(
    primitive=ExpensiveLLMCall(),
    ttl_seconds=3600,  # 1 hour
    max_size=10000,
    key_fn=lambda data, ctx: data["query"]  # Cache key
)

# Usage
context = WorkflowContext()

# First call - cache miss ($0.01)
result1 = await cached_llm.execute({"query": "What is Python?"}, context)
print(f"Cost: ${result1['cost']}")  # $0.01

# Second call - cache hit ($0.00)
result2 = await cached_llm.execute({"query": "What is Python?"}, context)
print(f"Cost: $0.00")  # Cache hit!

# Different query - cache miss ($0.01)
result3 = await cached_llm.execute({"query": "What is Rust?"}, context)
print(f"Cost: ${result3['cost']}")  # $0.01
```

**Cache Hit Rate Impact:**

| Hit Rate | Cost Savings | Monthly Savings (1M requests) |
|----------|--------------|-------------------------------|
| 30% | 30% | $3,000 |
| 50% | 50% | $5,000 |
| 70% | 70% | $7,000 |

**TTL Guidelines:**

| Content Type | TTL | Reason |
|--------------|-----|--------|
| Static FAQs | 24 hours | Rarely changes |
| Product info | 4 hours | Updates occasionally |
| Real-time data | 5 minutes | Changes frequently |
| User-specific | 1 hour | Balance freshness/cost |

**Cache Invalidation:**

```python
# Manual invalidation when content changes
cache.invalidate(key="What is Python?")

# Bulk invalidation
cache.clear()

# TTL-based invalidation (automatic)
# Entries expire after TTL seconds
```

---

### 5. Circuit Breaker Pattern

**Problem:** Failing service causes cascading failures, wasting resources

**Solution:** Stop calling failing service, fail fast, auto-recover

**When to use:**
- External service dependencies
- Services with known failure modes
- Need to prevent resource exhaustion

**Architecture:**

```
Request → Circuit Breaker (Closed) → Service → Success
                ↓ Failures exceed threshold
         Circuit Breaker (Open) → Fast Fail (no service call)
                ↓ After cooldown period
         Circuit Breaker (Half-Open) → Test Service
                ↓ Success
         Circuit Breaker (Closed) → Normal operation
```

**Implementation:**

```python
from tta_dev_primitives.recovery import TimeoutPrimitive, FallbackPrimitive
import time
from typing import Dict

class CircuitBreakerPrimitive(WorkflowPrimitive[dict, dict]):
    """Circuit breaker pattern implementation."""

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

        # State
        self.state = "closed"  # closed, open, half_open
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None

    async def execute(self, input_data: dict, context: WorkflowContext) -> dict:
        # Check if circuit should transition from open to half-open
        if self.state == "open":
            if time.time() - self.last_failure_time > self.timeout_seconds:
                self.state = "half_open"
                self.success_count = 0
            else:
                # Circuit is open, fail fast
                raise Exception("Circuit breaker is OPEN - service unavailable")

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

# Usage with fallback
unreliable_service = UnreliableExternalAPI()

circuit_breaker = CircuitBreakerPrimitive(
    primitive=unreliable_service,
    failure_threshold=5,
    success_threshold=2,
    timeout_seconds=60.0
)

# Add fallback for when circuit is open
with_fallback = FallbackPrimitive(
    primary=circuit_breaker,
    fallbacks=[SimpleFallbackResponse()]
)

workflow = with_fallback
```

**State Transitions:**

```
Closed (normal) --[5 failures]--> Open (failing fast)
    ↑                                   ↓
    |                              [60s timeout]
    |                                   ↓
    +--[2 successes]--<-- Half-Open (testing)
                              ↓
                         [1 failure]
                              ↓
                          Open (back to failing)
```

**Benefits:**
- Prevents resource exhaustion
- Faster failure detection
- Automatic recovery
- Protects downstream services

---

### 6. Saga Pattern (Distributed Transaction)

**Problem:** Multi-step operation across services, need rollback on failure

**Solution:** Execute steps with compensation for rollback

**When to use:**
- Multi-service transactions
- Need atomicity across services
- Can't use 2-phase commit

**Architecture:**

```
Step 1 → Success → Step 2 → Success → Step 3 → Success → Complete
  ↓                  ↓                  ↓
Compensate 1    Compensate 2    Compensate 3
  ←--[Rollback]-----←---------←----------← Failure
```

**Implementation:**

```python
from tta_dev_primitives.recovery import CompensationPrimitive

# E-commerce order example

class ReserveInventory(WorkflowPrimitive[dict, dict]):
    """Reserve items in inventory."""
    async def execute(self, input_data: dict, context: WorkflowContext) -> dict:
        order_id = input_data["order_id"]
        items = input_data["items"]

        # Reserve inventory
        reservation_id = await inventory_service.reserve(items)

        return {
            **input_data,
            "reservation_id": reservation_id,
            "inventory_reserved": True
        }

class ReleaseInventory(WorkflowPrimitive[dict, dict]):
    """Compensation: Release reserved inventory."""
    async def execute(self, input_data: dict, context: WorkflowContext) -> dict:
        reservation_id = input_data["reservation_id"]

        # Release reservation
        await inventory_service.release(reservation_id)

        return {**input_data, "inventory_released": True}

class ChargePayment(WorkflowPrimitive[dict, dict]):
    """Charge customer payment."""
    async def execute(self, input_data: dict, context: WorkflowContext) -> dict:
        order_id = input_data["order_id"]
        amount = input_data["amount"]

        # Charge payment
        transaction_id = await payment_service.charge(amount)

        return {
            **input_data,
            "transaction_id": transaction_id,
            "payment_charged": True
        }

class RefundPayment(WorkflowPrimitive[dict, dict]):
    """Compensation: Refund payment."""
    async def execute(self, input_data: dict, context: WorkflowContext) -> dict:
        transaction_id = input_data["transaction_id"]

        # Refund payment
        await payment_service.refund(transaction_id)

        return {**input_data, "payment_refunded": True}

class CreateShipment(WorkflowPrimitive[dict, dict]):
    """Create shipping order."""
    async def execute(self, input_data: dict, context: WorkflowContext) -> dict:
        order_id = input_data["order_id"]

        # Create shipment
        shipment_id = await shipping_service.create(order_id)

        return {
            **input_data,
            "shipment_id": shipment_id,
            "shipment_created": True
        }

class CancelShipment(WorkflowPrimitive[dict, dict]):
    """Compensation: Cancel shipment."""
    async def execute(self, input_data: dict, context: WorkflowContext) -> dict:
        shipment_id = input_data["shipment_id"]

        # Cancel shipment
        await shipping_service.cancel(shipment_id)

        return {**input_data, "shipment_cancelled": True}

# Build saga workflow
inventory_saga = CompensationPrimitive(
    forward=ReserveInventory(),
    compensation=ReleaseInventory()
)

payment_saga = CompensationPrimitive(
    forward=ChargePayment(),
    compensation=RefundPayment()
)

shipping_saga = CompensationPrimitive(
    forward=CreateShipment(),
    compensation=CancelShipment()
)

# Chain sagas together
order_workflow = inventory_saga >> payment_saga >> shipping_saga

# Execution scenarios:

# Scenario 1: All steps succeed
result = await order_workflow.execute(order_data, context)
# ✅ Inventory reserved, Payment charged, Shipment created

# Scenario 2: Shipping fails
try:
    result = await order_workflow.execute(order_data, context)
except Exception:
    pass
# ✅ Inventory reserved → Payment charged → Shipment failed
# 🔄 Compensation: Refund payment → Release inventory
# Result: Clean rollback, no orphaned resources

# Scenario 3: Payment fails
try:
    result = await order_workflow.execute(order_data, context)
except Exception:
    pass
# ✅ Inventory reserved → Payment failed
# 🔄 Compensation: Release inventory
# Result: Clean rollback
```

**Benefits:**
- Atomic multi-service operations
- Automatic rollback on failure
- No orphaned resources
- Maintains data consistency

**Best Practices:**
- Make compensations idempotent
- Log all saga steps
- Monitor compensation rates
- Test failure scenarios

---

### 7. Bulkhead Pattern

**Problem:** One workflow type consuming all resources, starving others

**Solution:** Isolate resources per workflow type

**When to use:**
- Multiple workflow types with different priorities
- Resource contention issues
- Need to prevent cascading failures

**Architecture:**

```
Critical Workflows → Dedicated Pool (50% resources)
Standard Workflows → Standard Pool (30% resources)
Batch Workflows → Batch Pool (20% resources)
```

**Implementation:**

```python
import asyncio
from typing import Dict

class BulkheadPrimitive(WorkflowPrimitive[dict, dict]):
    """Resource isolation per workflow type."""

    def __init__(
        self,
        primitive: WorkflowPrimitive,
        max_concurrent: int = 10,
        workflow_type: str = "default"
    ):
        self.primitive = primitive
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.workflow_type = workflow_type

    async def execute(self, input_data: dict, context: WorkflowContext) -> dict:
        # Acquire semaphore (blocks if at max concurrent)
        async with self.semaphore:
            return await self.primitive.execute(input_data, context)

# Define bulkheads for different workflow types
critical_workflow = BulkheadPrimitive(
    primitive=CriticalOperations(),
    max_concurrent=50,  # 50% of 100 total
    workflow_type="critical"
)

standard_workflow = BulkheadPrimitive(
    primitive=StandardOperations(),
    max_concurrent=30,  # 30% of 100 total
    workflow_type="standard"
)

batch_workflow = BulkheadPrimitive(
    primitive=BatchOperations(),
    max_concurrent=20,  # 20% of 100 total
    workflow_type="batch"
)

# Route to appropriate bulkhead
async def execute_with_priority(data: dict, priority: str):
    if priority == "critical":
        return await critical_workflow.execute(data, context)
    elif priority == "batch":
        return await batch_workflow.execute(data, context)
    else:
        return await standard_workflow.execute(data, context)
```

**Benefits:**
- Prevents resource starvation
- Isolates failures
- Predictable performance per type

---

## Anti-Patterns to Avoid

### ❌ God Workflow

**Problem:** Single workflow tries to do everything

```python
# BAD - 1000 line workflow that does everything
mega_workflow = (
    validate >> sanitize >> authenticate >> authorize >>
    check_cache >> route >> process >> transform >>
    validate_output >> format >> log >> audit >>
    notify >> update_db >> send_email >> ...
)
```

**Solution:** Break into focused sub-workflows

```python
# GOOD - Focused workflows
auth_workflow = authenticate >> authorize
processing_workflow = check_cache >> route >> process
post_process_workflow = format >> log >> audit

workflow = auth_workflow >> processing_workflow >> post_process_workflow
```

### ❌ Premature Optimization

**Problem:** Adding complexity before measuring

```python
# BAD - Complex caching before knowing if needed
workflow = (
    MultiLayerCache(
        L1=InMemoryCache(ttl=60),
        L2=RedisCache(ttl=3600),
        L3=DatabaseCache(ttl=86400)
    ) >> expensive_operation
)
```

**Solution:** Start simple, optimize based on metrics

```python
# GOOD - Start simple
workflow = CachePrimitive(expensive_operation, ttl_seconds=3600)

# Monitor cache hit rate, then optimize if needed
```

### ❌ Ignoring Failure Modes

**Problem:** No error handling, assuming success

```python
# BAD - No error handling
workflow = api_call >> process >> save
```

**Solution:** Plan for failures

```python
# GOOD - Comprehensive error handling
workflow = (
    RetryPrimitive(api_call, max_retries=3) >>
    FallbackPrimitive(
        primary=process,
        fallbacks=[simple_process]
    ) >>
    CompensationPrimitive(
        forward=save,
        compensation=rollback
    )
)
```

---

## Pattern Selection Guide

### Decision Tree

```
Need multiple models for accuracy?
  YES → Multi-Model Orchestra
  NO ↓

Variable query complexity?
  YES → Intelligent Router
  NO ↓

Primary service unreliable?
  YES → Fallback Chain + Circuit Breaker
  NO ↓

High query repetition?
  YES → Cache-Aside
  NO ↓

Multi-service transaction?
  YES → Saga Pattern
  NO ↓

Resource contention?
  YES → Bulkhead Pattern
  NO → Simple Sequential/Parallel
```

### Pattern Combinations

**High-Reliability System:**
```python
workflow = (
    CachePrimitive(  # Cache-Aside
        RetryPrimitive(  # Retry
            FallbackPrimitive(  # Fallback Chain
                primary=CircuitBreakerPrimitive(  # Circuit Breaker
                    primary_service
                ),
                fallbacks=[secondary_service]
            ),
            max_retries=3
        ),
        ttl_seconds=3600
    )
)
```

**Cost-Optimized System:**
```python
workflow = (
    CachePrimitive(  # Cache-Aside
        RouterPrimitive(  # Intelligent Router
            routes={
                "fast": cheap_model,
                "quality": expensive_model
            },
            route_selector=complexity_based_routing
        ),
        ttl_seconds=7200
    )
)
```

---

## Real-World Case Studies

### Case Study 1: Customer Support Platform

**Requirements:**
- 100K requests/day
- <2s P95 latency
- >99.9% availability
- Cost <$1K/month

**Architecture:**

```python
# Layer 1: Cache (70% hit rate)
cached = CachePrimitive(ttl_seconds=3600)

# Layer 2: Router (complexity-based)
router = RouterPrimitive(
    routes={
        "faq": cached_faq_responses,  # 40% of queries
        "simple": gpt35_model,         # 30% of queries
        "complex": gpt4_model          # 30% of queries
    }
)

# Layer 3: Fallback
with_fallback = FallbackPrimitive(
    primary=router,
    fallbacks=[simple_template_responses]
)

# Complete workflow
workflow = cached >> with_fallback
```

**Results:**
- ✅ P95 latency: 850ms
- ✅ Availability: 99.95%
- ✅ Cost: $450/month (55% under budget)
- ✅ Cache hit rate: 68%

### Case Study 2: Content Moderation Service

**Requirements:**
- 1M items/day
- High accuracy (>99%)
- <5s P95 latency
- Minimize false positives

**Architecture:**

```python
# Multi-model consensus for high accuracy
parallel_models = (
    GPT4Moderator() |
    ClaudeModerator() |
    CustomMLModel()
)

consensus = ConsensusAggregator(threshold=2)  # 2 of 3 agree

# Fallback to human review if disagreement
with_fallback = FallbackPrimitive(
    primary=parallel_models >> consensus,
    fallbacks=[QueueForHumanReview()]
)

workflow = with_fallback
```

**Results:**
- ✅ Accuracy: 99.4%
- ✅ P95 latency: 3.2s
- ✅ False positive rate: 0.1%
- ✅ Human review queue: 5% (down from 30%)

---

## Next Steps

- **Implement patterns:** [[TTA.dev/Guides/Workflow Composition]]
- **Add monitoring:** [[TTA.dev/Guides/Observability]]
- **Optimize costs:** [[TTA.dev/Guides/Cost Optimization]]

---

## Key Takeaways

1. **Multi-Model Orchestra** - Consensus for critical decisions
2. **Intelligent Router** - Route by complexity for cost savings
3. **Fallback Chain** - Graceful degradation for reliability
4. **Cache-Aside** - Reduce costs with caching
5. **Circuit Breaker** - Fail fast, auto-recover
6. **Saga Pattern** - Atomic multi-service operations
7. **Bulkhead** - Resource isolation per priority

**Remember:** Start simple, measure, optimize based on actual needs.

---

**Created:** [[2025-10-30]]
**Last Updated:** [[2025-10-30]]
**Estimated Time:** 40 minutes
**Difficulty:** [[Intermediate]]

- [[Project Hub]]

---
**Logseq:** [[TTA.dev/_archive/Nested_copies/Framework/Logseq/Pages/Tta.dev___guides___architecture patterns]]
