# Cost Optimization

type:: [[Guide]]
category:: [[Production]]
difficulty:: [[Intermediate]]
estimated-time:: 30 minutes
target-audience:: [[Developers]], [[Product Managers]], [[AI Engineers]]

---

## Overview

- id:: cost-optimization-overview
  **Cost optimization** in AI workflows can reduce expenses by **30-80%** without sacrificing quality. By combining smart caching, model routing, and fallback strategies, you pay only for the compute you actually need - using expensive models sparingly and cheap models liberally.

---

## Prerequisites

{{embed ((prerequisites-full))}}

**Should have read:**

- [[TTA.dev/Guides/Agentic Primitives]] - Core concepts
- [[TTA.dev/Guides/Workflow Composition]] - Composition patterns

**Should understand:**

- CachePrimitive basics
- RouterPrimitive basics
- LLM pricing models

---

## The Cost Problem

### Typical LLM Costs

| Model | Input (per 1M tokens) | Output (per 1M tokens) | Use Case |
|-------|----------------------|------------------------|----------|
| GPT-4 | $10.00 | $30.00 | Complex reasoning |
| GPT-4 Turbo | $5.00 | $15.00 | Balanced quality/cost |
| GPT-3.5 Turbo | $0.50 | $1.50 | Simple tasks |
| Claude 3 Opus | $15.00 | $75.00 | Highest quality |
| Claude 3 Sonnet | $3.00 | $15.00 | Balanced |
| Claude 3 Haiku | $0.25 | $1.25 | Fast/cheap |

**Reality check:**

- Processing 1M requests with GPT-4 = **$10,000-30,000**
- Processing 1M requests with GPT-3.5 = **$500-1,500**
- **20-60x price difference** for same volume!

---

## Three Cost Optimization Strategies

### 1. Caching (30-70% Savings)

- id:: cost-optimization-caching

**Cache identical requests** to avoid redundant LLM calls:

```python
from tta_dev_primitives.performance import CachePrimitive

# Without cache: Every call costs money
expensive_llm = GPT4Primitive()
result1 = await expensive_llm.execute("What is Python?", context)  # $0.001
result2 = await expensive_llm.execute("What is Python?", context)  # $0.001
# Total: $0.002

# With cache: Second call is free
cached_llm = CachePrimitive(
    primitive=expensive_llm,
    ttl_seconds=3600,  # 1 hour
    max_size=10000
)
result1 = await cached_llm.execute("What is Python?", context)  # $0.001
result2 = await cached_llm.execute("What is Python?", context)  # $0 (cache hit!)
# Total: $0.001 (50% savings)
```

**Cache hit rate impact:**

- 30% hit rate = 30% cost reduction
- 50% hit rate = 50% cost reduction
- 70% hit rate = 70% cost reduction

### 2. Smart Routing (40-80% Savings)

- id:: cost-optimization-routing

**Route to cheap models when possible**, expensive models when necessary:

```python
from tta_dev_primitives import RouterPrimitive

def select_model(input_data: dict, context: WorkflowContext) -> str:
    """Route based on complexity."""
    complexity = estimate_complexity(input_data["prompt"])

    if complexity == "simple":
        return "fast"  # GPT-3.5 ($0.50/1M)
    elif complexity == "medium":
        return "balanced"  # GPT-4 Turbo ($5/1M)
    else:
        return "complex"  # GPT-4 ($10/1M)

router = RouterPrimitive(
    routes={
        "fast": gpt35_model,      # 70% of requests
        "balanced": gpt4_turbo,   # 20% of requests
        "complex": gpt4_model     # 10% of requests
    },
    route_selector=select_model
)

# Cost calculation:
# - 70% at $0.50 = $0.35
# - 20% at $5.00 = $1.00
# - 10% at $10.00 = $1.00
# Average: $2.35/1M tokens
# vs all GPT-4: $10/1M tokens
# Savings: 76.5%!
```

### 3. Fallback Chains (20-50% Savings)

- id:: cost-optimization-fallback

**Try cheap first, fallback to expensive** only if needed:

```python
from tta_dev_primitives.recovery import FallbackPrimitive

# Strategy: Fast → Medium → Expensive → Cache
workflow = FallbackPrimitive(
    primary=gpt35_model,           # Try cheap first (90% success)
    fallbacks=[
        gpt4_turbo_model,          # Fallback to medium (9% usage)
        gpt4_model,                # Last resort expensive (1% usage)
        cached_response_primitive  # Ultimate fallback (free)
    ]
)

# Cost calculation:
# - 90% at $0.50 = $0.45
# - 9% at $5.00 = $0.45
# - 1% at $10.00 = $0.10
# Average: $1.00/1M tokens
# vs all GPT-4: $10/1M tokens
# Savings: 90%!
```

---

## Strategy Comparison

| Strategy | Savings | Complexity | Best For |
|----------|---------|------------|----------|
| **Cache only** | 30-70% | Low | Repeated queries |
| **Router only** | 40-80% | Medium | Variable complexity |
| **Fallback only** | 20-50% | Low | Quality degradation OK |
| **Cache + Router** | 60-90% | Medium | Most workflows |
| **All three** | 70-95% | High | Cost-critical production |

---

## Real-World Example 1: Content Moderation

```python
from tta_dev_primitives import SequentialPrimitive
from tta_dev_primitives.performance import CachePrimitive
from tta_dev_primitives.recovery import FallbackPrimitive

# Step 1: Cache safety checks (high repetition)
safety_check = CachePrimitive(
    primitive=SafetyClassifierPrimitive(),
    ttl_seconds=7200,  # 2 hours
    max_size=50000
)

# Step 2: Cheap content filter first
cheap_filter = GPT35ContentFilter()
expensive_filter = GPT4ContentFilter()

content_filter = FallbackPrimitive(
    primary=cheap_filter,
    fallbacks=[expensive_filter]
)

# Complete workflow
workflow = safety_check >> content_filter

# Cost analysis:
# - Safety checks: 70% cache hit rate = 70% savings
# - Content filter: 85% handled by GPT-3.5 = 85% savings
# Overall: ~78% cost reduction
# Before: $10,000/month
# After: $2,200/month
# Savings: $7,800/month
```

---

## Real-World Example 2: Customer Support

```python
from tta_dev_primitives import RouterPrimitive
from tta_dev_primitives.performance import CachePrimitive

# FAQ cache (common questions)
faq_cache = CachePrimitive(
    primitive=FAQPrimitive(),
    ttl_seconds=86400,  # 24 hours
    max_size=100000
)

# Complexity-based routing
def select_support_model(input_data: dict, context: WorkflowContext) -> str:
    """Route based on query complexity."""
    query = input_data["query"]

    # Check if FAQ
    if is_faq(query):
        return "faq"

    # Analyze complexity
    if has_keywords(query, ["billing", "refund", "payment"]):
        return "complex"  # Need GPT-4 for accuracy
    elif word_count(query) < 20:
        return "simple"
    else:
        return "medium"

router = RouterPrimitive(
    routes={
        "faq": faq_cache,             # 40% of queries (free after cache)
        "simple": gpt35_model,        # 30% of queries ($0.50/1M)
        "medium": gpt4_turbo_model,   # 20% of queries ($5/1M)
        "complex": gpt4_model         # 10% of queries ($10/1M)
    },
    route_selector=select_support_model
)

# Cost calculation:
# - 40% cached FAQ = $0 (after first hit)
# - 30% GPT-3.5 = $0.15
# - 20% GPT-4 Turbo = $1.00
# - 10% GPT-4 = $1.00
# Average: $2.15/1M tokens (with cache hits)
# vs all GPT-4: $10/1M tokens
# Savings: 78.5%
```

---

## Real-World Example 3: Multi-LLM Orchestra

```python
from tta_dev_primitives import ParallelPrimitive, SequentialPrimitive
from tta_dev_primitives.performance import CachePrimitive
from tta_dev_primitives.recovery import TimeoutPrimitive

# Cache all LLMs (20% cache hit rate across all)
cached_gpt4 = CachePrimitive(gpt4_model, ttl_seconds=3600)
cached_claude = CachePrimitive(claude_opus_model, ttl_seconds=3600)
cached_palm = CachePrimitive(palm_model, ttl_seconds=3600)

# Add timeouts (cost control if LLM hangs)
timeout_gpt4 = TimeoutPrimitive(cached_gpt4, timeout_seconds=30.0)
timeout_claude = TimeoutPrimitive(cached_claude, timeout_seconds=30.0)
timeout_palm = TimeoutPrimitive(cached_palm, timeout_seconds=30.0)

# Run 3 LLMs in parallel
parallel_llms = timeout_gpt4 | timeout_claude | timeout_palm

# Aggregate results
aggregator = ConsensusAggregator()

workflow = parallel_llms >> aggregator

# Cost calculation:
# Before optimization:
# - GPT-4: $10/1M
# - Claude Opus: $15/1M
# - PaLM: $8/1M
# Total: $33/1M per request
#
# After optimization (20% cache hit):
# - 20% cache hit = free
# - 80% actual calls = $33 * 0.8 = $26.40/1M
# Savings: 20% ($6.60/1M)
#
# Additional savings from timeouts preventing runaway costs
```

---

## Measuring Cost Impact

### Key Metrics

**Cost Metrics:**

- **Cost per request** - Total LLM cost / request count
- **Cost per user** - Total LLM cost / active users
- **Cost per success** - Total LLM cost / successful outcomes

**Efficiency Metrics:**

- **Cache hit rate** - (Cache hits / total requests) * 100
- **Model distribution** - % of requests to each model
- **Token usage** - Average tokens per request

**Quality Metrics:**

- **Success rate** - % of requests that succeed
- **User satisfaction** - User ratings/feedback
- **Response quality** - Manual evaluation scores

### Prometheus Queries

```promql
# Average cost per request (estimate)
sum(rate(llm_tokens_total[5m])) * avg(llm_cost_per_token)

# Cache hit rate
sum(rate(cache_hits_total[5m])) /
(sum(rate(cache_hits_total[5m])) + sum(rate(cache_misses_total[5m]))) * 100

# Model distribution
sum(rate(router_executions_total[5m])) by (route)

# Token usage by model
sum(rate(llm_tokens_total[5m])) by (model)
```

### Cost Tracking Example

```python
from observability_integration import initialize_observability
import structlog

logger = structlog.get_logger(__name__)

class CostTrackingPrimitive(WorkflowPrimitive[dict, dict]):
    """Track LLM costs in metrics."""

    def __init__(self, llm_primitive, cost_per_1k_tokens: float):
        self.llm = llm_primitive
        self.cost_per_1k = cost_per_1k_tokens

    async def execute(self, input_data: dict, context: WorkflowContext) -> dict:
        # Execute LLM
        result = await self.llm.execute(input_data, context)

        # Calculate cost
        tokens_used = result.get("tokens", 0)
        cost = (tokens_used / 1000) * self.cost_per_1k

        # Log cost
        logger.info(
            "llm_cost",
            model=self.llm.model_name,
            tokens=tokens_used,
            cost_usd=cost,
            workflow_id=context.workflow_id
        )

        # Could also update Prometheus metric here
        # llm_cost_total.labels(model=model_name).inc(cost)

        return result

# Usage
gpt4_tracked = CostTrackingPrimitive(gpt4_model, cost_per_1k_tokens=0.03)
gpt35_tracked = CostTrackingPrimitive(gpt35_model, cost_per_1k_tokens=0.0015)

router = RouterPrimitive(
    routes={
        "fast": gpt35_tracked,
        "quality": gpt4_tracked
    },
    route_selector=select_model
)
```

---

## Optimization Decision Tree

```
Start: Need to reduce LLM costs?
│
├─ High repetition (same queries)?
│  └─ YES → Use CachePrimitive
│     ├─ Cache hit rate > 30%? → Keep caching ✅
│     └─ Cache hit rate < 30%? → Try different TTL or cache key
│
├─ Variable query complexity?
│  └─ YES → Use RouterPrimitive
│     ├─ Can classify complexity? → Route by complexity ✅
│     ├─ Can't classify? → Use heuristics (length, keywords)
│     └─ All queries complex? → Routing won't help ❌
│
├─ Quality degradation acceptable?
│  └─ YES → Use FallbackPrimitive
│     ├─ Cheap model success rate > 80%? → Use fallback chain ✅
│     └─ Cheap model success rate < 80%? → Skip cheap model ❌
│
└─ Need maximum savings?
   └─ Combine all three:
      Cache → Router → Fallback ✅
```

---

## Best Practices

### Caching

✅ **Cache common queries** (FAQs, standard responses)
✅ **Use appropriate TTL** (longer for stable content)
✅ **Monitor cache hit rate** (target > 30%)
✅ **Invalidate when content changes** (manual invalidation if needed)
✅ **Consider cache size** (memory usage vs hit rate)

❌ **Don't cache personalized content** (low hit rate)
❌ **Don't cache time-sensitive data** (stale responses)
❌ **Don't cache everything** (memory waste)

### Routing

✅ **Route by complexity** (cheap for simple, expensive for complex)
✅ **Route by domain** (specialized models for specialized tasks)
✅ **Route by priority** (fast for real-time, slow for batch)
✅ **Monitor route distribution** (ensure balanced usage)
✅ **Validate route selection** (ensure quality maintained)

❌ **Don't always route to cheapest** (quality matters)
❌ **Don't over-complicate routing logic** (diminishing returns)
❌ **Don't route without validation** (quality regressions)

### Fallbacks

✅ **Order by cost** (cheap → expensive)
✅ **Order by speed** (fast → slow)
✅ **Include cached fallback** (ultimate free option)
✅ **Monitor fallback usage** (should be < 20%)
✅ **Test degraded quality** (ensure acceptable)

❌ **Don't add too many fallbacks** (complexity)
❌ **Don't fallback without monitoring** (quality blind spot)
❌ **Don't use fallbacks as primary** (defeats purpose)

---

## Common Mistakes

### Mistake 1: Caching Everything

**Problem:** Caching personalized content with low hit rate

```python
# ❌ BAD - Low cache hit rate
cached_personalized = CachePrimitive(
    primitive=PersonalizedResponseGenerator(),
    ttl_seconds=3600
)
# Every user gets different response = 0% hit rate
```

**Solution:** Only cache shareable content

```python
# ✅ GOOD - Cache base content, personalize after
base_content = CachePrimitive(
    primitive=BaseContentGenerator(),
    ttl_seconds=3600
)

workflow = base_content >> PersonalizeContent()
# Cache hits on base content, personalization is cheap
```

### Mistake 2: Always Routing to Cheapest

**Problem:** Sacrificing quality for cost savings

```python
# ❌ BAD - Always use cheap model
router = RouterPrimitive(
    routes={"cheap": gpt35_model},
    route_selector=lambda d, c: "cheap"
)
# Poor quality for complex tasks
```

**Solution:** Route based on actual complexity

```python
# ✅ GOOD - Route by complexity
def intelligent_routing(input_data: dict, context: WorkflowContext) -> str:
    complexity = analyze_complexity(input_data)
    return "cheap" if complexity < 0.3 else "expensive"

router = RouterPrimitive(
    routes={
        "cheap": gpt35_model,
        "expensive": gpt4_model
    },
    route_selector=intelligent_routing
)
```

### Mistake 3: No Cost Monitoring

**Problem:** Can't measure optimization impact

```python
# ❌ BAD - No visibility into costs
workflow = cache >> router >> fallback
result = await workflow.execute(input_data, context)
# No idea if optimization is working
```

**Solution:** Track costs and metrics

```python
# ✅ GOOD - Monitor everything
workflow = (
    CachePrimitive(expensive_op, ttl_seconds=3600) >>
    RouterPrimitive(routes, selector) >>
    FallbackPrimitive(primary, fallbacks)
)

result = await workflow.execute(input_data, context)

# Log metrics
logger.info(
    "workflow_complete",
    cache_hit_rate=calculate_cache_hit_rate(),
    route_distribution=get_route_distribution(),
    fallback_usage=get_fallback_usage_rate(),
    estimated_cost=calculate_cost(context)
)
```

---

## Cost Optimization Checklist

**Before optimization:**

- [ ] Measure baseline costs ($/request, $/user, $/month)
- [ ] Identify most expensive operations (usually LLM calls)
- [ ] Analyze query patterns (repetition, complexity distribution)
- [ ] Define quality requirements (acceptable degradation?)

**During optimization:**

- [ ] Implement caching for repeated queries
- [ ] Add routing for variable complexity
- [ ] Set up fallback chains if quality degradation OK
- [ ] Monitor cache hit rates (target > 30%)
- [ ] Track route distribution (ensure balance)
- [ ] Measure quality metrics (satisfaction, success rate)

**After optimization:**

- [ ] Compare costs (before vs after)
- [ ] Validate quality maintained (user feedback, metrics)
- [ ] Document cost savings (report to stakeholders)
- [ ] Set up alerts (cost spikes, quality drops)
- [ ] Plan ongoing optimization (continuous improvement)

---

## Next Steps

- **Monitor workflows:** [[TTA.dev/Guides/Observability]]
- **Test optimizations:** [[TTA.dev/Guides/Testing Workflows]]
- **Handle failures:** [[TTA.dev/Guides/Error Handling Patterns]]

---

## Related Content

### Cost-Related Primitives

{{query (and (page-property type [[Primitive]]) (or [[CachePrimitive]] [[RouterPrimitive]] [[FallbackPrimitive]]))}}

### Essential Guides

- [[TTA.dev/Guides/Agentic Primitives]] - Core concepts
- [[TTA.dev/Guides/Workflow Composition]] - Building workflows
- [[TTA.dev/Guides/Observability]] - Monitoring costs

---

## Key Takeaways

1. **Caching alone:** 30-70% savings (high repetition required)
2. **Routing alone:** 40-80% savings (variable complexity required)
3. **Fallbacks alone:** 20-50% savings (quality degradation OK)
4. **Combined strategies:** 70-95% savings (best results)
5. **Always monitor:** Track costs, quality, and optimization impact
6. **Quality first:** Never sacrifice quality for cost alone

---

**Created:** [[2025-10-30]]
**Last Updated:** [[2025-10-30]]
**Estimated Time:** 30 minutes
**Difficulty:** [[Intermediate]]
