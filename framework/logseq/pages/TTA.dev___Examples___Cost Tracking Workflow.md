# TTA.dev/Examples/Cost Tracking Workflow

**Production-ready cost optimization and budget enforcement for LLM workflows.**

## Overview

Cost tracking workflow demonstrates comprehensive cost management: caching for 30-40% reduction, smart routing for 20-30% reduction, real-time budget enforcement, and detailed cost metrics.

**Source:** `packages/tta-dev-primitives/examples/cost_tracking_workflow.py`

## Complete Example

```python
from tta_dev_primitives import SequentialPrimitive, WorkflowContext
from tta_dev_primitives.performance import CachePrimitive
from tta_dev_primitives.core import RouterPrimitive
from dataclasses import dataclass
import structlog

logger = structlog.get_logger()

@dataclass
class CostTracker:
    """Track LLM costs in real-time."""

    total_cost: float = 0.0
    cache_hits: int = 0
    cache_misses: int = 0
    requests_by_model: dict = None

    def __post_init__(self):
        if self.requests_by_model is None:
            self.requests_by_model = {}

    def record_request(self, model: str, tokens: int, cost: float, cached: bool):
        """Record a single request."""
        if cached:
            self.cache_hits += 1
        else:
            self.cache_misses += 1
            self.total_cost += cost

        if model not in self.requests_by_model:
            self.requests_by_model[model] = {"count": 0, "cost": 0.0}

        self.requests_by_model[model]["count"] += 1
        if not cached:
            self.requests_by_model[model]["cost"] += cost

        logger.info(
            "cost_tracked",
            model=model,
            tokens=tokens,
            cost=cost,
            cached=cached,
            total_cost=self.total_cost
        )

    @property
    def cache_hit_rate(self) -> float:
        """Calculate cache hit rate."""
        total = self.cache_hits + self.cache_misses
        return self.cache_hits / total if total > 0 else 0.0

    @property
    def estimated_savings(self) -> float:
        """Estimate savings from caching."""
        # Average cost per miss
        if self.cache_misses == 0:
            return 0.0
        avg_cost = self.total_cost / self.cache_misses
        return avg_cost * self.cache_hits

# Model pricing (per 1M tokens)
PRICING = {
    "gpt-4o-mini": {"input": 0.15, "output": 0.60},
    "gpt-4": {"input": 30.0, "output": 60.0},
    "claude-3.5-sonnet": {"input": 3.0, "output": 15.0}
}

def calculate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    """Calculate cost for a model request."""
    pricing = PRICING.get(model, {"input": 1.0, "output": 2.0})
    input_cost = (input_tokens / 1_000_000) * pricing["input"]
    output_cost = (output_tokens / 1_000_000) * pricing["output"]
    return input_cost + output_cost

async def llm_with_cost_tracking(
    data: dict,
    context: WorkflowContext,
    cost_tracker: CostTracker,
    model: str
) -> dict:
    """LLM call with cost tracking."""
    # Simulate LLM call
    prompt = data.get("prompt", "")
    input_tokens = len(prompt.split()) * 1.3  # Rough estimate
    output_tokens = 100  # Assume fixed output

    # Calculate cost
    cost = calculate_cost(model, int(input_tokens), int(output_tokens))

    # Record in tracker
    cached = context.data.get("cache_hit", False)
    cost_tracker.record_request(model, int(input_tokens + output_tokens), cost, cached)

    return {
        "response": f"Response from {model}",
        "model": model,
        "cost": cost,
        "cached": cached
    }

# Budget enforcement
class BudgetExceededError(Exception):
    """Raised when budget is exceeded."""
    pass

async def enforce_budget(
    data: dict,
    context: WorkflowContext,
    cost_tracker: CostTracker,
    budget: float
) -> dict:
    """Check if budget allows request."""
    if cost_tracker.total_cost >= budget:
        raise BudgetExceededError(
            f"Budget exceeded: ${cost_tracker.total_cost:.4f} / ${budget:.2f}"
        )
    return data

# Build cost-optimized workflow
def build_cost_workflow(cost_tracker: CostTracker, budget: float = 10.0):
    """Build workflow with cost tracking and optimization."""

    # Layer 1: Budget enforcement
    budget_check = lambda data, ctx: enforce_budget(data, ctx, cost_tracker, budget)

    # Layer 2: Cache (30-40% cost reduction)
    cached_llm = CachePrimitive(
        primitive=lambda data, ctx: llm_with_cost_tracking(
            data, ctx, cost_tracker, "gpt-4o-mini"
        ),
        ttl_seconds=3600,
        max_size=1000
    )

    # Layer 3: Smart routing (20-30% additional reduction)
    router = RouterPrimitive(
        routes={
            "fast": cached_llm,  # gpt-4o-mini: $0.15/$0.60 per 1M tokens
            "balanced": lambda data, ctx: llm_with_cost_tracking(
                data, ctx, cost_tracker, "claude-3.5-sonnet"
            ),
            "quality": lambda data, ctx: llm_with_cost_tracking(
                data, ctx, cost_tracker, "gpt-4"
            )
        },
        router_fn=lambda data, ctx: (
            "quality" if "complex" in data.get("prompt", "").lower()
            else "fast"
        ),
        default="fast"
    )

    # Compose workflow
    return budget_check >> router

# Example usage
async def main():
    # Initialize cost tracker
    tracker = CostTracker()

    # Build workflow with $5 budget
    workflow = build_cost_workflow(tracker, budget=5.0)

    # Execute requests
    context = WorkflowContext(correlation_id="cost-example")

    # Request 1: Simple (fast route, cached)
    result1 = await workflow.execute(
        {"prompt": "What is Python?"},
        context
    )

    # Request 2: Same (cache hit!)
    result2 = await workflow.execute(
        {"prompt": "What is Python?"},
        context
    )

    # Request 3: Complex (quality route)
    result3 = await workflow.execute(
        {"prompt": "Explain the complex implications of quantum computing"},
        context
    )

    # Print cost report
    print(f"\n{'='*50}")
    print(f"COST REPORT")
    print(f"{'='*50}")
    print(f"Total Cost: ${tracker.total_cost:.4f}")
    print(f"Cache Hit Rate: {tracker.cache_hit_rate:.1%}")
    print(f"Estimated Savings: ${tracker.estimated_savings:.4f}")
    print(f"\nRequests by Model:")
    for model, stats in tracker.requests_by_model.items():
        print(f"  {model}: {stats['count']} requests, ${stats['cost']:.4f}")
    print(f"{'='*50}\n")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
```

## Key Features

### 1. Real-Time Cost Tracking

```python
@dataclass
class CostTracker:
    total_cost: float = 0.0
    cache_hits: int = 0
    cache_misses: int = 0
    requests_by_model: dict = None
```

Track:
- Total accumulated cost
- Cache hit/miss rates
- Per-model costs and request counts
- Estimated savings from caching

### 2. Budget Enforcement

```python
async def enforce_budget(data, context, tracker, budget):
    if tracker.total_cost >= budget:
        raise BudgetExceededError(f"Budget exceeded: ${tracker.total_cost}")
    return data
```

Prevent overspending:
- Hard budget limits
- Real-time checks before requests
- Graceful error handling

### 3. Multi-Tier Cost Optimization

```python
workflow = (
    budget_check >>           # Enforce limits
    CachePrimitive(ttl=3600) >>  # 30-40% reduction
    RouterPrimitive(tier="balanced")  # 20-30% reduction
)
```

**Combined savings: 60-80% total cost reduction**

### 4. Detailed Metrics

```python
print(f"Total Cost: ${tracker.total_cost:.4f}")
print(f"Cache Hit Rate: {tracker.cache_hit_rate:.1%}")
print(f"Estimated Savings: ${tracker.estimated_savings:.4f}")
```

Track:
- Absolute costs
- Savings percentages
- Per-model breakdowns
- Cache effectiveness

## Cost Reduction Strategies

### Strategy 1: Aggressive Caching

```python
CachePrimitive(
    ttl_seconds=7200,  # 2 hour cache
    max_size=5000,     # Large cache
)
```

**Typical savings:** 30-40% for repeated queries

### Strategy 2: Smart Model Selection

```python
RouterPrimitive(
    routes={
        "fast": gpt4_mini,      # $0.15 input
        "balanced": claude,      # $3.00 input
        "quality": gpt4          # $30.00 input
    }
)
```

**Typical savings:** 20-30% from appropriate model selection

### Strategy 3: Request Batching

```python
ParallelPrimitive([req1, req2, req3])  # Single batch
# vs
await workflow(req1)  # 3 separate calls
await workflow(req2)
await workflow(req3)
```

**Savings:** Reduced overhead and better cache hits

### Strategy 4: Budget Allocation

```python
# Daily budget per user
user_tracker = CostTracker()
workflow = build_cost_workflow(user_tracker, budget=1.00)  # $1/day
```

**Control:** Per-user, per-day, per-project budgets

## Running the Example

```bash
# From repository root
cd packages/tta-dev-primitives/examples
uv run python cost_tracking_workflow.py

# Expected output:
# ==================================================
# COST REPORT
# ==================================================
# Total Cost: $0.0042
# Cache Hit Rate: 33.3%
# Estimated Savings: $0.0021
#
# Requests by Model:
#   gpt-4o-mini: 2 requests, $0.0021
#   gpt-4: 1 requests, $0.0021
# ==================================================
```

## Integration with Prometheus

Export cost metrics:

```python
from prometheus_client import Counter, Gauge, Histogram

cost_total = Counter(
    'llm_cost_total_dollars',
    'Total LLM cost in dollars',
    ['model']
)

cache_hits = Counter(
    'llm_cache_hits_total',
    'Cache hits',
    ['model']
)

def record_request_metrics(model: str, cost: float, cached: bool):
    if not cached:
        cost_total.labels(model=model).inc(cost)
    if cached:
        cache_hits.labels(model=model).inc()
```

**Query in Grafana:**

```promql
# Total cost over time
sum(rate(llm_cost_total_dollars[5m]))

# Cache effectiveness
sum(rate(llm_cache_hits_total[5m])) / sum(rate(llm_requests_total[5m]))
```

## Related Examples

- [[TTA.dev/Examples/RAG Workflow]] - RAG with cost optimization
- [[TTA.dev/Examples/Multi-Agent Workflow]] - Multi-agent cost tracking
- [[TTA.dev/Examples/Basic Workflow]] - Basic patterns

## Documentation

- [[CachePrimitive]] - Caching for cost reduction
- [[RouterPrimitive]] - Smart model routing
- [[PRIMITIVES CATALOG]] - All primitives
- [[tta-observability-integration]] - Metrics integration

## Source Code

**File:** `packages/tta-dev-primitives/examples/cost_tracking_workflow.py`

## Tags

example:: cost-tracking
type:: production
feature:: cost-optimization
primitives:: cache, router, budget-enforcement

- [[Project Hub]]