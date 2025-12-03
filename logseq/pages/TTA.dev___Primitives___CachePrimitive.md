# CachePrimitive

type:: [[Primitive]]
category:: [[Performance]]
package:: [[TTA.dev/Packages/tta-dev-primitives]]
status:: [[Stable]]
version:: 1.0.0
test-coverage:: 100
complexity:: [[Medium]]
python-class:: `CachePrimitive`
import-path:: `from tta_dev_primitives.performance import CachePrimitive`
related-primitives:: [[TTA.dev/Primitives/RouterPrimitive]], [[TTA.dev/Primitives/ParallelPrimitive]]

---

## Overview

- id:: cache-primitive-overview
  Cache expensive operation results with LRU eviction and TTL expiration. Essential for cost optimization and performance improvement.

  **Think of it as:** A smart memoization layer that remembers expensive results and serves them instantly on repeated requests.

---

## Use Cases

- id:: cache-primitive-use-cases
  - **LLM responses:** Cache identical prompts (save $$$ on API calls)
  - **API calls:** Cache external API responses
  - **Database queries:** Cache expensive query results
  - **Computation:** Cache heavy computation results
  - **Cost optimization:** Reduce redundant expensive operations by 30-80%

---

## Key Benefits

- id:: cache-primitive-benefits
  - ✅ **30-80% cost reduction** - Eliminate redundant expensive calls
  - ✅ **Faster responses** - Cached results return instantly
  - ✅ **LRU eviction** - Automatically remove least recently used items
  - ✅ **TTL expiration** - Cache entries expire after time limit
  - ✅ **Hit/miss tracking** - Monitor cache effectiveness
  - ✅ **Thread-safe** - Works with async and parallel execution

---

## API Reference

- id:: cache-primitive-api

### Constructor

```python
CachePrimitive(
    primitive: WorkflowPrimitive[T, U],
    max_size: int = 1000,
    ttl_seconds: float | None = None,
    cache_key_fn: Callable[[T], str] | None = None
)
```

**Parameters:**

- `primitive`: The primitive to wrap with caching
- `max_size`: Maximum cache entries (LRU eviction when exceeded)
- `ttl_seconds`: Time-to-live in seconds (None = no expiration)
- `cache_key_fn`: Custom function to generate cache keys from input

**Returns:** A new `CachePrimitive` instance

---

## Examples

### Cache LLM Responses

- id:: cache-llm-example

```python
{{embed ((standard-imports))}}
from tta_dev_primitives.performance import CachePrimitive

# Expensive LLM call
llm_call = LambdaPrimitive(lambda data, ctx: call_gpt4(data))

# Cache for 1 hour, max 1000 entries
cached_llm = CachePrimitive(
    primitive=llm_call,
    ttl_seconds=3600,  # 1 hour
    max_size=1000
)

context = WorkflowContext(correlation_id="cache-001")

# First call: Expensive API call
result1 = await cached_llm.execute(
    input_data={"prompt": "Explain caching"},
    context=context
)

# Second call with SAME prompt: Instant from cache! 🚀
result2 = await cached_llm.execute(
    input_data={"prompt": "Explain caching"},
    context=context
)

# Cost savings: 50% (1 API call instead of 2)
# Speed improvement: 100x faster (instant vs. API latency)
```

### Custom Cache Key

- id:: cache-custom-key

```python
# Custom cache key that ignores certain fields
def custom_key(data):
    # Only cache by 'query', ignore 'user_id' and 'session_id'
    return data.get("query", "")

cached_search = CachePrimitive(
    primitive=search_api,
    cache_key_fn=custom_key,
    ttl_seconds=300  # 5 minutes
)

# These will use the same cache entry (same query)
result1 = await cached_search.execute({"query": "python", "user_id": "user1"}, ctx)
result2 = await cached_search.execute({"query": "python", "user_id": "user2"}, ctx)
```

---

## Composition Patterns

- id:: cache-composition-patterns

### Cache + Retry

```python
from tta_dev_primitives.recovery import RetryPrimitive

# Retry on failure, cache successes
reliable_call = RetryPrimitive(api_call, max_retries=3)
cached_call = CachePrimitive(reliable_call, ttl_seconds=3600)

workflow = input_processor >> cached_call >> output_formatter
```

### Cache Multiple Branches

```python
# Cache each parallel branch independently
cached_gpt4 = CachePrimitive(gpt4_call, ttl_seconds=7200)
cached_claude = CachePrimitive(claude_call, ttl_seconds=7200)

workflow = cached_gpt4 | cached_claude | cached_llama
```

---

## Performance Impact

- id:: cache-performance-impact

### Cost Reduction

**Example: LLM API calls at $0.01 per request**

- Without cache: 1000 requests = $10.00
- With 70% hit rate: 300 requests = $3.00
- **Savings: $7.00 (70%)**

### Speed Improvement

- **Cache hit:** ~1ms (memory lookup)
- **Cache miss:** Original operation time
- **Typical improvement:** 100-1000x faster for hits

### Memory Usage

- **Per entry:** ~100-500 bytes (depends on result size)
- **1000 entries:** ~100-500 KB
- **Max size limit:** Prevents unbounded growth via LRU

---

## Best Practices

- id:: cache-best-practices

✅ **Cache expensive operations** - LLM calls, API calls, heavy computation
✅ **Set appropriate TTL** - Balance freshness vs. cost savings
✅ **Monitor hit rate** - Target 50-80% for good caching
✅ **Limit cache size** - Use max_size to prevent memory issues
✅ **Custom keys for flexibility** - Cache by meaningful fields only
✅ **Combine with retry** - Cache successful retried operations

❌ **Don't cache non-deterministic** - Random operations, timestamps
❌ **Don't cache too long** - Data may become stale
❌ **Don't cache security-sensitive** - Credentials, tokens, PII
❌ **Don't use tiny TTL** - Overhead not worth it (<10 seconds)

---

## Cache Effectiveness Monitoring

- id:: cache-monitoring

### Key Metrics

```python
# Access cache statistics
stats = cached_primitive.get_stats()

print(f"Hit rate: {stats['hit_rate']:.1%}")
print(f"Total requests: {stats['total_requests']}")
print(f"Cache hits: {stats['cache_hits']}")
print(f"Cache misses: {stats['cache_misses']}")
print(f"Cache size: {stats['cache_size']}")
```

### Ideal Hit Rates

- **50-70%**: Good - cache is effective
- **70-90%**: Excellent - high repetition
- **<30%**: Poor - consider longer TTL or larger cache
- **>95%**: Over-caching - may be stale data

---

## Related Content

### Works Well With

- [[TTA.dev/Primitives/RouterPrimitive]] - Cache expensive routes
- [[TTA.dev/Primitives/ParallelPrimitive]] - Cache parallel branches
- [[TTA.dev/Primitives/RetryPrimitive]] - Cache after successful retry
- [[TTA.dev/Primitives/FallbackPrimitive]] - Cache as fallback option

### Used In Examples

{{query (and [[Example]] [[CachePrimitive]])}}

---

## Observability

### Tracing

```
workflow_execution
└── cache_execution
    ├── cache_lookup (hit/miss)
    └── [if miss] wrapped_primitive_execution
```

### Metrics

- `cache.hit_rate` - Percentage of cache hits
- `cache.size` - Current number of cached entries
- `cache.evictions` - LRU evictions count
- `cache.expirations` - TTL expirations count

---

## Metadata

**Source Code:** [cache.py](https://github.com/theinterneti/TTA.dev/blob/main/platform/primitives/src/tta_dev_primitives/performance/cache.py)
**Tests:** [test_cache.py](https://github.com/theinterneti/TTA.dev/blob/main/platform/primitives/tests/test_cache.py)

**Created:** [[2025-10-30]]
**Last Updated:** [[2025-10-30]]
**Test Coverage:** 100%
**Status:** [[Stable]] - Production Ready

**Real-world impact:** 30-80% cost reduction for LLM workflows
