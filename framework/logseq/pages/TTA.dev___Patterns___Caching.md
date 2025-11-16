# TTA.dev/Patterns/Caching

**Performance optimization through intelligent caching strategies**

---

## Overview

Caching is a critical pattern for reducing costs and improving performance in TTA.dev workflows. By storing and reusing results of expensive operations, caching can reduce API calls, lower costs, and improve response times.

**Impact:** 40-60% cost reduction typical, up to 100x latency reduction on cache hits
**Primitive:** [[CachePrimitive]]
**Category:** Performance Pattern

---

## When to Use Caching

### ✅ Good Candidates for Caching

1. **LLM API Calls**
   - Same prompts repeated frequently
   - Deterministic results expected
   - Cost is significant factor

2. **External API Requests**
   - Slow response times (>100ms)
   - Rate-limited services
   - Expensive per-request cost

3. **Database Queries**
   - Complex aggregations
   - Frequently accessed data
   - Relatively static content

4. **Computation-Heavy Operations**
   - ML model inference
   - Complex data transformations
   - Expensive parsing/processing

### ❌ Poor Candidates for Caching

1. **User-Specific Data**
   - Personalized content
   - Session-dependent results
   - Real-time user state

2. **Rapidly Changing Data**
   - Live feeds
   - Stock prices
   - Real-time metrics

3. **Non-Deterministic Operations**
   - Random number generation
   - Time-sensitive calculations
   - Creative generation (when variety needed)

---

## Basic Caching Pattern

### Simple LRU Cache

```python
from tta_dev_primitives.performance import CachePrimitive
from tta_dev_primitives import WorkflowContext # Keep import for now, will address later if needed

async def expensive_llm_call(data: dict, context: WorkflowContext) -> dict: # This is a code example, will address later if needed
    """Expensive operation that benefits from caching."""
    # Simulate expensive LLM call
    response = await openai.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": data["prompt"]}]
    )

    return {
        "response": response.choices[0].message.content,
        "tokens": response.usage.total_tokens,
        "cost": calculate_cost(response.usage)
    }

# Wrap with cache
cached_llm = CachePrimitive(
    primitive=expensive_llm_call,
    ttl_seconds=3600,      # 1 hour TTL
    max_size=1000,         # Max 1000 cached items
    key_fn=lambda d, c: d["prompt"]  # Cache key function
)

# Use in workflow
context = WorkflowContext(workflow_id="cached-workflow") # This is a code example, will address later if needed

# First call: cache miss (executes LLM call)
result1 = await cached_llm.execute(
    {"prompt": "What is TTA.dev?"},
    context
)

# Second call with same prompt: cache hit (instant)
result2 = await cached_llm.execute(
    {"prompt": "What is TTA.dev?"},
    context
)

# Different prompt: cache miss (new LLM call)
result3 = await cached_llm.execute(
    {"prompt": "What is a primitive?"},
    context
)
```

---

## Multi-Level Caching

### Pattern: L1 + L2 Cache

```python
from tta_dev_primitives.performance import CachePrimitive

async def data_retrieval(data: dict, context: WorkflowContext) -> dict: # This is a code example, will address later if needed
    """Expensive data retrieval operation."""
    # Simulate expensive database or API call
    return await fetch_from_database(data["query"])

# L1: Fast in-memory cache (small, short TTL)
l1_cache = CachePrimitive(
    primitive=data_retrieval,
    ttl_seconds=300,       # 5 minutes
    max_size=100,          # Small cache
    key_fn=lambda d, c: d["query"]
)

# L2: Larger distributed cache (Redis-backed, longer TTL)
l2_cache = CachePrimitive(
    primitive=l1_cache,    # Wrap L1 cache
    ttl_seconds=3600,      # 1 hour
    max_size=10000,        # Larger cache
    backend="redis",       # Distributed cache
    redis_url="redis://localhost:6379"
)

# Use multi-level cache
result = await l2_cache.execute({"query": "user-123"}, context)

# Cache hit path: L1 → instant
# L1 miss, L2 hit: Redis lookup → fast
# L1 miss, L2 miss: Database query → slow
```

---

## Context-Aware Caching

### Pattern: Include Context in Cache Key

```python
from tta_dev_primitives.performance import CachePrimitive

def context_aware_key(data: dict, context: WorkflowContext) -> str: # This is a code example, will address later if needed
    """Generate cache key including context."""
    return f"{data['prompt']}:{context.user_id}:{context.get('tier', 'default')}"

cached_personalized_llm = CachePrimitive(
    primitive=personalized_llm_call,
    ttl_seconds=1800,      # 30 minutes
    max_size=1000,
    key_fn=context_aware_key  # Include user_id in cache key
)

# Different users get different cached results
context_user1 = WorkflowContext(user_id="user-1") # This is a code example, will address later if needed
context_user2 = WorkflowContext(user_id="user-2") # This is a code example, will address later if needed

# These create separate cache entries
result1 = await cached_personalized_llm.execute(
    {"prompt": "My settings"},
    context_user1
)

result2 = await cached_personalized_llm.execute(
    {"prompt": "My settings"},  # Same prompt
    context_user2                # Different user
)
```

---

## Cache Warming

### Pattern: Pre-populate Cache

```python
async def warm_cache(common_queries: list[str], cache: CachePrimitive):
    """Pre-populate cache with common queries."""
    context = WorkflowContext(workflow_id="cache-warming") # This is a code example, will address later if needed

    for query in common_queries:
        await cache.execute({"prompt": query}, context)

    print(f"Cache warmed with {len(common_queries)} queries")

# Common queries
common_queries = [
    "What is TTA.dev?",
    "How do I use primitives?",
    "What is a workflow?",
    "How do I cache results?",
]

# Warm cache on startup
await warm_cache(common_queries, cached_llm)

# Now users get instant responses for common questions
```

---

## Cache Invalidation Strategies

### Strategy 1: TTL-Based Invalidation

```python
# Automatic expiration after TTL
cache = CachePrimitive(
    primitive=operation,
    ttl_seconds=3600  # Expires after 1 hour
)
```

### Strategy 2: Manual Invalidation

```python
# Clear entire cache
cache.clear()

# Invalidate specific key
cache.invalidate(key="specific-prompt")

# Selective invalidation
async def invalidate_user_cache(user_id: str):
    """Invalidate all cache entries for a user."""
    for key in cache.keys():
        if user_id in key:
            cache.invalidate(key=key)
```

### Strategy 3: Conditional Invalidation

```python
async def cached_with_validation(data: dict, context: WorkflowContext) -> dict: # This is a code example, will address later if needed
    """Cache with validation on retrieval."""

    # Check if cached result is still valid
    cached_result = cache.get(data)

    if cached_result and is_still_valid(cached_result):
        return cached_result

    # Re-fetch if invalid
    fresh_result = await expensive_operation(data, context)
    cache.set(data, fresh_result)

    return fresh_result
```

---

## Monitoring Cache Performance

### Metrics to Track

```python
from tta_dev_primitives.performance import CachePrimitive
from prometheus_client import Counter, Histogram

# Prometheus metrics
cache_hits = Counter('cache_hits_total', 'Total cache hits')
cache_misses = Counter('cache_misses_total', 'Total cache misses')
cache_latency = Histogram('cache_latency_seconds', 'Cache operation latency')

# Enhanced cache with metrics
class MetricsCachePrimitive(CachePrimitive):
    async def execute(self, data: dict, context: WorkflowContext) -> dict: # This is a code example, will address later if needed
        start_time = time.time()

        # Check cache
        cached = self.get(data, context)

        if cached:
            cache_hits.inc()
            cache_latency.observe(time.time() - start_time)
            return cached

        # Cache miss
        cache_misses.inc()
        result = await super().execute(data, context)
        cache_latency.observe(time.time() - start_time)

        return result

# Query metrics in Prometheus
# cache_hit_rate = cache_hits_total / (cache_hits_total + cache_misses_total)
```

---

## Best Practices

### 1. Choose Appropriate TTL

```python
# Short TTL for frequently changing data
cache_short = CachePrimitive(ttl_seconds=300)   # 5 minutes

# Medium TTL for semi-static data
cache_medium = CachePrimitive(ttl_seconds=3600)  # 1 hour

# Long TTL for static data
cache_long = CachePrimitive(ttl_seconds=86400)   # 24 hours
```

### 2. Size Cache Appropriately

```python
# Small cache for high-cardinality keys
cache_small = CachePrimitive(max_size=100)

# Medium cache for moderate cardinality
cache_medium = CachePrimitive(max_size=1000)

# Large cache for low cardinality
cache_large = CachePrimitive(max_size=10000)
```

### 3. Use Semantic Cache Keys

```python
# ✅ Good: Semantic content-based key
def semantic_key(data: dict, context: WorkflowContext) -> str: # This is a code example, will address later if needed
    prompt = data["prompt"]
    # Hash or embed prompt for similarity matching
    return f"semantic:{hash_prompt(prompt)}"

# ❌ Bad: Random or opaque keys
def bad_key(data: dict, context: WorkflowContext) -> str: # This is a code example, will address later if needed
    return str(uuid.uuid4())  # Every call generates new key
```

### 4. Handle Cache Failures Gracefully

```python
async def fault_tolerant_cache(data: dict, context: WorkflowContext) -> dict: # This is a code example, will address later if needed
    """Cache that falls back on failure."""
    try:
        return await cached_operation.execute(data, context)
    except CacheError as e:
        logger.warning(f"Cache failure: {e}, falling back to direct execution")
        return await direct_operation.execute(data, context)
```

---

## Related Patterns

- [[TTA.dev/Patterns/Cost Optimization]] - Caching reduces costs
- [[TTA.dev/Patterns/Performance]] - Caching improves performance
- [[TTA.dev/Patterns/Resilience]] - Caching provides fallback data

---

## Related Primitives

- [[CachePrimitive]] - Main caching implementation
- [[RouterPrimitive]] - Route to cached vs fresh data
- [[FallbackPrimitive]] - Fallback to cache on failure

---

## Related Examples

- [[TTA.dev/Examples/Cached LLM]] - LLM caching example
- [[TTA.dev/Examples/RAG Workflow]] - RAG with caching
- [[TTA.dev/Examples/Cost Tracking]] - Cost reduction via caching

---

**Category:** Performance Pattern
**Impact:** High (40-60% cost reduction)
**Complexity:** Low to Medium
**Status:** Production-ready

- [[Project Hub]]
