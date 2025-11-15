# Performance

**Tag page for performance optimization, caching, and efficiency**

---

## Overview

**Performance** in TTA.dev focuses on building efficient workflows through:
- **Caching** - Reduce redundant computations and API calls
- **Parallel execution** - Process independent operations concurrently
- **Memory management** - Conversational memory with LRU eviction
- **Cost optimization** - Smart routing to appropriate models

**Key benefits:**
- 30-60% cost reduction through caching
- 100x latency reduction on cache hits
- Efficient resource utilization
- Automatic performance metrics

**See:** [[TTA.dev/Patterns/Caching]], [[TTA Primitives/CachePrimitive]]

---

## Performance Primitives

### CachePrimitive

**LRU cache with TTL for expensive operations**

```python
from tta_dev_primitives.performance import CachePrimitive

# Cache expensive LLM calls
cached_llm = CachePrimitive(
    primitive=expensive_llm_call,
    ttl_seconds=3600,     # 1 hour TTL
    max_size=1000,        # Max 1000 entries
    key_fn=lambda data, ctx: data["prompt"]  # Custom cache key
)

# 40-60% cost reduction typical
workflow = input_validator >> cached_llm >> output_formatter
```

**Features:**
- LRU eviction policy
- TTL-based expiration
- Custom key functions
- Thread-safe with asyncio.Lock
- Automatic metrics (hit rate, size)

**Benefits:**
- **Cost reduction**: 40-60% typical savings
- **Latency reduction**: 100x faster on cache hits
- **Resource efficiency**: Reduce API calls
- **Improved UX**: Faster responses

**See:** [[TTA Primitives/CachePrimitive]], [[TTA.dev/Patterns/Caching]]

---

### MemoryPrimitive

**Conversational memory with search**

```python
from tta_dev_primitives.performance import MemoryPrimitive

# Hybrid architecture: works without Redis, upgrades automatically
memory = MemoryPrimitive(
    max_size=100,                        # In-memory LRU size
    redis_url="redis://localhost:6379",  # Optional Redis
    enable_redis=True                    # Auto-fallback if unavailable
)

# Store conversation turns
await memory.add("user_query_1", {"role": "user", "content": "What is a primitive?"})
await memory.add("assistant_1", {"role": "assistant", "content": "A primitive is..."})

# Search conversation history
history = await memory.search(keywords=["primitive", "composition"])

# Retrieve by key
turn = await memory.get("user_query_1")
```

**Features:**
- Zero-setup mode (no Docker/Redis required)
- Automatic Redis upgrade if available
- Graceful fallback to in-memory
- LRU eviction for memory management
- Keyword search across history
- Task-specific namespaces

**Use Cases:**
- Multi-turn conversations
- Task context spanning operations
- Agent memory and recall
- Personalization based on history

**See:** [[TTA Primitives/MemoryPrimitive]]

---

## Pages Tagged with #Performance

{{query (page-tags [[Performance]])}}

---

## Performance Patterns

### Multi-Level Caching

**Cache at multiple stages with different TTLs:**

```python
from tta_dev_primitives.performance import CachePrimitive

workflow = (
    # Cache parsed input (short TTL - data changes frequently)
    CachePrimitive(parse_input, ttl_seconds=300) >>

    # Cache embeddings (medium TTL - expensive to compute)
    CachePrimitive(generate_embeddings, ttl_seconds=3600) >>

    # Cache search results (long TTL - stable database)
    CachePrimitive(search_vectors, ttl_seconds=86400) >>

    # No cache on final generation (always fresh)
    generate_response
)
```

**Benefits:**
- Different caching strategies per stage
- Optimize TTL based on data volatility
- Maximum cost reduction
- Balanced freshness vs performance

---

### Parallel Processing

**Process independent operations concurrently:**

```python
from tta_dev_primitives import ParallelPrimitive

# Process multiple data sources in parallel
workflow = (
    fetch_data >>
    ParallelPrimitive([
        process_text,
        process_images,
        process_metadata
    ]) >>
    merge_results
)
```

**Benefits:**
- Reduce total latency (wall-clock time)
- Efficient resource utilization
- Natural for independent operations
- Automatic concurrency management

**See:** [[TTA Primitives/ParallelPrimitive]], [[TTA.dev/Patterns/Parallel Execution]]

---

### Smart Routing for Cost Optimization

**Route to appropriate model based on complexity:**

```python
from tta_dev_primitives.core import RouterPrimitive

# Tiered routing: fast/balanced/quality
router = RouterPrimitive(
    routes={
        "fast": gpt4_mini,        # Cheap, fast
        "balanced": claude_sonnet, # Balanced
        "quality": gpt4           # Expensive, best
    },
    router_fn=select_by_complexity,
    default="balanced"
)

# 30-40% additional cost reduction through smart routing
workflow = CachePrimitive(router, ttl_seconds=3600)
```

**Combined savings:**
- Cache: 40-60% reduction
- Smart routing: 30-40% additional reduction
- **Total: 60-80% cost reduction** possible

**See:** [[TTA Primitives/RouterPrimitive]]

---

## Performance Optimization Strategies

### 1. Cache Everything Expensive

**Identify expensive operations and cache them:**

**LLM Calls:**
```python
cached_llm = CachePrimitive(
    llm_call,
    ttl_seconds=3600,
    key_fn=lambda data, ctx: data["prompt"]
)
```

**Database Queries:**
```python
cached_query = CachePrimitive(
    database_query,
    ttl_seconds=300,
    key_fn=lambda data, ctx: data["query_hash"]
)
```

**External API Calls:**
```python
cached_api = CachePrimitive(
    api_call,
    ttl_seconds=600,
    key_fn=lambda data, ctx: data["endpoint"] + data["params"]
)
```

---

### 2. Parallelize Independent Operations

**Identify operations that don't depend on each other:**

**Sequential (Slow):**
```python
# Takes 3 seconds total (1s + 1s + 1s)
result1 = await fetch_user()      # 1s
result2 = await fetch_orders()    # 1s
result3 = await fetch_analytics() # 1s
```

**Parallel (Fast):**
```python
# Takes 1 second total (all concurrent)
workflow = (
    fetch_user |
    fetch_orders |
    fetch_analytics
)
results = await workflow.execute({}, context)  # 1s total
```

---

### 3. Use Memory for Stateful Workflows

**Preserve context across operations:**

```python
from tta_dev_primitives.performance import MemoryPrimitive

memory = MemoryPrimitive(max_size=100)

async def stateful_workflow(user_input):
    # Retrieve conversation history
    history = await memory.search(keywords=user_input.split()[:3])

    # Generate response with context
    response = await llm_with_context(user_input, history)

    # Store in memory
    await memory.add(f"turn_{timestamp}", {
        "user": user_input,
        "assistant": response
    })

    return response
```

---

### 4. Monitor Performance Metrics

**Track cache hit rates and latencies:**

```promql
# Cache hit rate
cache_hit_rate = cache_hits / (cache_hits + cache_misses)

# Cache effectiveness
cache_savings_seconds = cache_hits * avg_computation_time

# Cost savings
cost_savings_usd = cache_hits * avg_api_cost
```

**See:** [[TTA.dev/Observability]]

---

## Performance Best Practices

### ✅ DO

**Cache Idempotent Operations:**
```python
# Good: Same input always produces same output
cached_computation = CachePrimitive(
    expensive_computation,
    ttl_seconds=3600
)
```

**Use Appropriate TTLs:**
```python
# Short TTL for volatile data
user_data = CachePrimitive(fetch_user, ttl_seconds=60)

# Long TTL for stable data
static_content = CachePrimitive(fetch_docs, ttl_seconds=86400)
```

**Parallelize Independent Work:**
```python
# Good: Independent operations run concurrently
workflow = fetch_user | fetch_settings | fetch_preferences
```

**Monitor Cache Performance:**
```python
# Track metrics
cache_hit_rate = cache.cache_hits / (cache.cache_hits + cache.cache_misses)
if cache_hit_rate < 0.5:
    logger.warning("Cache hit rate low", hit_rate=cache_hit_rate)
```

---

### ❌ DON'T

**Don't Cache Non-Idempotent Operations:**
```python
# Bad: Side effects should not be cached
cached_increment = CachePrimitive(increment_counter)  # ❌
cached_send_email = CachePrimitive(send_email)        # ❌
```

**Don't Use Infinite TTL:**
```python
# Bad: Data can become stale
cache = CachePrimitive(fetch_data, ttl_seconds=None)  # ❌

# Good: Reasonable TTL
cache = CachePrimitive(fetch_data, ttl_seconds=3600)
```

**Don't Parallelize Dependent Operations:**
```python
# Bad: step2 depends on step1's output
workflow = step1 | step2  # ❌ Won't work correctly

# Good: Use sequential for dependencies
workflow = step1 >> step2
```

**Don't Over-Cache:**
```python
# Bad: Caching everything adds overhead
workflow = (
    CachePrimitive(cheap_operation1) >>  # ❌ Overhead > benefit
    CachePrimitive(cheap_operation2) >>  # ❌ Overhead > benefit
    CachePrimitive(expensive_operation)  # ✅ Worth caching
)
```

---

## Performance Metrics

**All performance primitives export metrics:**

### Cache Metrics

```promql
# Cache hits vs misses
cache_hits_total{primitive="llm_call"}
cache_misses_total{primitive="llm_call"}

# Cache size and evictions
cache_size{primitive="llm_call"}
cache_evictions_total{primitive="llm_call", reason="lru|ttl"}

# Cache hit rate
cache_hit_rate{primitive="llm_call"}

# Time saved by caching
cache_time_saved_seconds{primitive="llm_call"}
```

### Memory Metrics

```promql
# Memory operations
memory_add_total{namespace="conversation"}
memory_get_total{namespace="conversation"}
memory_search_total{namespace="conversation"}

# Memory size
memory_size{namespace="conversation"}

# Search performance
memory_search_duration_seconds{namespace="conversation"}
```

### Parallel Execution Metrics

```promql
# Parallel workflow duration
parallel_total_duration_seconds{workflow="data_processing"}

# Individual branch durations
parallel_branch_duration_seconds{branch="branch1"}

# Speedup vs sequential
parallel_speedup_ratio{workflow="data_processing"}
```

**See:** [[TTA.dev/Observability]], [[Prometheus]]

---

## Real-World Performance Examples

### Example 1: High-Performance RAG

```python
from tta_dev_primitives.performance import CachePrimitive, MemoryPrimitive

# Multi-level caching + memory
rag_workflow = (
    # Cache embeddings (expensive)
    CachePrimitive(embed_query, ttl_seconds=3600) >>

    # Cache search results
    CachePrimitive(search_vectors, ttl_seconds=1800) >>

    # Rerank (fast, no cache)
    rerank_results >>

    # Generate with conversation history
    generate_with_memory
)

async def generate_with_memory(data, context):
    memory = MemoryPrimitive(max_size=10)
    history = await memory.search(data["query"])
    return await llm_generate(data, history)
```

**Performance:**
- 60% cost reduction (caching)
- 100x faster on cache hits
- Context-aware responses (memory)

---

### Example 2: Parallel Multi-Provider LLM

```python
from tta_dev_primitives import ParallelPrimitive
from tta_dev_primitives.performance import CachePrimitive

# Query 3 LLMs in parallel, cache results
multi_llm = ParallelPrimitive([
    CachePrimitive(openai_gpt4, ttl_seconds=3600),
    CachePrimitive(anthropic_claude, ttl_seconds=3600),
    CachePrimitive(google_gemini, ttl_seconds=3600),
])

# Aggregate results
workflow = multi_llm >> aggregate_responses

# Benefits:
# - 3x faster than sequential (parallel)
# - 40-60% cost reduction (caching)
# - Higher quality (ensemble)
```

---

### Example 3: Cost-Optimized Pipeline

```python
from tta_dev_primitives.core import RouterPrimitive
from tta_dev_primitives.performance import CachePrimitive

# Smart routing + caching
optimized_pipeline = (
    # Fast path for simple queries
    RouterPrimitive(
        routes={
            "simple": gpt4_mini,      # $0.15/1M tokens
            "complex": gpt4,          # $30/1M tokens
        },
        router_fn=classify_complexity
    ) >>

    # Cache everything
    CachePrimitive(ttl_seconds=3600)
)

# Combined savings:
# - Smart routing: 70% of queries use cheap model (40% cost reduction)
# - Caching: 50% cache hit rate (50% additional reduction)
# - Total: ~70% cost reduction
```

---

## Performance Testing

### Load Testing

```python
import asyncio
import time

async def load_test_workflow():
    """Test workflow under load."""
    workflow = CachePrimitive(expensive_operation, ttl_seconds=60)

    # Simulate 100 concurrent requests
    start = time.time()
    tasks = [
        workflow.execute({"id": i}, context)
        for i in range(100)
    ]
    results = await asyncio.gather(*tasks)
    duration = time.time() - start

    print(f"Completed 100 requests in {duration:.2f}s")
    print(f"Cache hit rate: {workflow.cache_hit_rate:.2%}")
```

### Performance Benchmarking

```python
@pytest.mark.benchmark
async def test_cache_performance(benchmark):
    """Benchmark cache performance."""
    cache = CachePrimitive(expensive_op, ttl_seconds=60)

    # Warm up cache
    await cache.execute({"key": "test"}, context)

    # Benchmark cache hit
    result = await benchmark(
        cache.execute,
        {"key": "test"},
        context
    )

    # Verify performance
    assert benchmark.stats["mean"] < 0.001  # < 1ms
```

**See:** [[Testing]]

---

## Related Concepts

- [[Primitive]] - Performance primitives
- [[Workflow]] - Workflow optimization
- [[Recovery]] - Resilience vs performance
- [[Testing]] - Performance testing
- [[Production]] - Production performance

---

## Documentation

- [[TTA.dev/Patterns/Caching]] - Caching patterns
- [[TTA.dev/Patterns/Parallel Execution]] - Parallel processing
- [[PRIMITIVES_CATALOG]] - Primitive reference
- [[TTA.dev/Observability]] - Performance monitoring
- [[README]] - Project overview

---

**Tags:** #performance #optimization #caching #memory #efficiency #cost-optimization #index-page

**Last Updated:** 2025-11-05
**Maintained by:** TTA.dev Team

- [[Project Hub]]