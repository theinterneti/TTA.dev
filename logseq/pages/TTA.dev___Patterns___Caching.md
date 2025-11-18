# TTA.dev/Patterns/Caching

## Overview

Caching is a critical performance optimization pattern in TTA.dev workflows. By intelligently caching expensive operations, you can reduce latency, lower costs, and improve user experience. TTA.dev provides the `CachePrimitive` as the primary tool for implementing caching patterns with built-in observability and automatic optimization.

Tags: #performance #optimization #patterns
Type: Pattern Guide
Audience: Intermediate Developers, Performance Engineers
Status: Stable

## Core Concepts

### CachePrimitive Architecture

The `CachePrimitive` wraps any expensive operation and provides:

```python
from tta_dev_primitives.performance import CachePrimitive
from tta_dev_primitives.core.base import WorkflowContext

# Basic usage - cache LLM calls
cached_llm = CachePrimitive(
    primitive=expensive_llm_call,
    ttl_seconds=3600,  # Cache for 1 hour
    max_size=1000      # Keep up to 1000 entries
)

# Use in workflow context
context = WorkflowContext(correlation_id="req-123")
result = await cached_llm.execute(input_data, context)
```

### Key Caching Strategies

#### 1. **Lookup Cache** (Most Common)
- Cache by input hash
- Perfect for deterministic operations
- Example: API responses, LLM completions

#### 2. **Time-based Expiration**
- TTL (Time To Live) controls cache freshness
- Balance freshness vs performance
- Example: TTL=3600 for moderately stale data

#### 3. **Size-based Eviction**
- LRU (Least Recently Used) eviction
- Prevents unbounded memory growth
- Example: max_size=1000 for high-traffic caches

#### 4. **Context-aware Caching**
- Include metadata in cache keys
- Different caching for different environments
- Example: User-specific vs global caches

## Implementation Patterns

### Pattern 1: LLM Response Caching

```python
# Cache expensive LLM calls
llm_cache = CachePrimitive(
    primitive=gpt4_call,
    ttl_seconds=1800,  # 30 minutes
    max_size=500
)

# Context-aware caching
context = WorkflowContext(
    correlation_id="llm-req-123",
    metadata={
        "model": "gpt-4",
        "temperature": 0.7,
        "user_id": "user-456"
    }
)

response = await llm_cache.execute(prompt, context)
```

### Pattern 2: API Response Caching

```python
# Cache external API calls
api_cache = CachePrimitive(
    primitive=external_api_call,
    ttl_seconds=300,  # 5 minutes for dynamic data
    max_size=200
)

# Parallel with fallback
workflow = api_cache | direct_api_call  # Try cache first, fallback to direct
```

### Pattern 3: Database Query Caching

```python
# Cache expensive database queries
query_cache = CachePrimitive(
    primitive=db_complex_query,
    ttl_seconds=600,  # 10 minutes for analytics
    max_size=100
)

# Use specific cache key function
def query_cache_key(query_params, context):
    return f"{context.metadata.get('user_id')}_{hash(query_params)}"

cached_query = CachePrimitive(
    primitive=db_complex_query,
    key_fn=query_cache_key
)
```

## Advanced Caching Patterns

### Cache Hierarchy

```python
# Multi-level caching strategy
fast_cache = CachePrimitive(expensive_op, ttl_seconds=60, max_size=100)   # L1: Fast, small, short TTL
slow_cache = CachePrimitive(fast_cache, ttl_seconds=3600, max_size=1000)  # L2: Slower, larger, longer TTL

# Try L1 first (fast), fallback to L2
workflow = fast_cache | slow_cache
```

### Conditional Caching

```python
# Only cache successful results
def should_cache_condition(input_data, context):
    return context.metadata.get("cache_enabled", True)

conditional_cache = CachePrimitive(
    primitive=my_operation,
    condition_fn=should_cache_condition
)
```

### Cache Invalidation Strategies

```python
# Time-based expiration (built-in)

# Manual invalidation
await cache.invalidate("specific_key")

# Pattern-based invalidation
await cache.invalidate_pattern("user_*")  # Clear all user-related cache

# Complete cache flush
await cache.clear()
```

## Performance Considerations

### Cache Hit Ratios

Monitor hit rates to optimize configuration:

```
Good: >70% hit rate
Okay: 40-70% hit rate
Poor: <40% hit rate (consider removing cache)
```

### Memory Usage

- Monitor cache size vs hit rate tradeoffs
- Set appropriate max_size limits
- Consider cache size in resource planning

### Latency Impact

- Cache hits: typically <1ms
- Cache misses: full operation latency
- Network costs: reduced by caching

## Best Practices

### ✅ Do This

1. **Cache Deterministic Operations**: Only cache operations that produce consistent results for identical inputs
2. **Set Appropriate TTLs**: Balance data freshness with performance gains
3. **Use LRU Eviction**: Let the cache manage size automatically
4. **Monitor Hit Rates**: Track cache effectiveness metrics
5. **Include Context in Keys**: Make cache keys specific enough to avoid conflicts

### ❌ Avoid This

1. **Don't Cache Random Operations**: Functions with random outputs defeat caching purpose
2. **Don't Set Unlimited TTL**: Stale data can cause bugs
3. **Don't Ignore Memory Limits**: Unbounded caches can cause OOM
4. **Don't Cache Secrets**: Never cache sensitive data
5. **Don't Use Caching for Debugging**: Caching masks real performance issues

## Common Pitfalls

### Pitfall 1: Cache Key Collisions

```python
# Bad: Generic key function
def bad_key_fn(input_data, context):
    return "cache_key"  # Always same key!

# Good: Specific key function
def good_key_fn(input_data, context):
    return f"{context.correlation_id}_{hash(input_data)}"
```

### Pitfall 2: Ignoring Cache Invalidation

Problem: Data updates don't clear cache
Solution: Implement proper invalidation strategies

### Pitfall 3: Cache Stampede

Problem: Multiple requests hit cache miss simultaneously
Solution: Use single-flight caching or request coalescing

## Monitoring & Observability

Cache primitives include built-in metrics:

- `cache_hits_total`: Number of cache hits
- `cache_misses_total`: Number of cache misses
- `cache_size_gauge`: Current cache size
- `cache_evictions_total`: Items evicted from cache

```python
# Monitor cache effectiveness
cache_metrics = await cache.get_metrics()
hit_rate = cache_metrics.hits / (cache_metrics.hits + cache_metrics.misses)

# Alert if hit rate drops below 50%
if hit_rate < 0.5:
    logger.warning(f"Low cache hit rate: {hit_rate:.1%}")
```

## Integration with Other Primitives

### With RetryPrimitive

```python
# Cache + Retry for resilient calls
cached_retry = CachePrimitive(
    RetryPrimitive(api_call, max_retries=3),
    ttl_seconds=300
)
```

### With ParallelPrimitive

```python
# Parallel cached operations
parallel_cached = ParallelPrimitive([
    CachePrimitive(op1, ttl_seconds=600),
    CachePrimitive(op2, ttl_seconds=600),
    CachePrimitive(op3, ttl_seconds=600)
])
```

### With RouterPrimitive

```python
# Route to fastest cached alternative
cached_router = RouterPrimitive({
    "fast": CachePrimitive(fast_model, ttl_seconds=1800),
    "quality": CachePrimitive(slow_model, ttl_seconds=3600)
})
```

## Production Deployment Considerations

### Cache Warming

Pre-populate cache with common queries:

```python
# Warm cache on startup
common_queries = ["popular_query_1", "popular_query_2"]
for query in common_queries:
    await cache.execute(query, context)
```

### Cache Clustering

For multi-instance deployments:

```python
# Use Redis or similar for shared caching
redis_cache = RedisCachePrimitive(
    primitive=my_operation,
    redis_url="redis://cache-cluster:6379"
)
```

### Cache Backup/Restore

```python
# Export cache state
cache_state = await cache.export()

# Import cache state
await cache.import(cache_state)
```

## Troubleshooting Guide

### Symptom: Poor Hit Rates

**Check:**
- Cache key granularity (too specific = low hits)
- TTL settings (too short = rapid expiration)
- Cache size (too small = frequent eviction)

**Solutions:**
- Simplify cache keys
- Increase TTL
- Increase cache size

### Symptom: Memory Issues

**Check:**
- Cache size limits
- Object sizes in cache
- Memory leak patterns

**Solutions:**
- Implement size limits
- Use cache serialization
- Periodic cache cleanup

### Symptom: Cache Miss Storms

**Check:**
- TTL expiration patterns
- Concurrent request patterns
- Cache key distribution

**Solutions:**
- Jitter TTL expiration
- Implement request coalescing
- Use longer TTLs with validation

## Next Steps

### Explore Related Patterns
- [[TTA.dev/Patterns/Performance]]
- [[TTA.dev/Patterns/Error Handling]]
- [[TTA.dev/Primitives/CachePrimitive]]
- [[TTA.dev/Examples/Cached LLM]]

### Related How-To Guides
- [[TTA.dev/How-To/Implement Caching]]
- [[TTA.dev/How-To/Performance Tuning]]
- [[TTA.dev/How-To/Monitor Cache Performance]]

### Implementation Examples
- [[TTA.dev/Examples/API Response Caching]]
- [[TTA.dev/Examples/LLM Response Caching]]
- [[TTA.dev/Examples/Database Query Caching]]

---

**Last Updated:** 2025-11-18
**Author:** TTA.dev Cline Adaptive Agent
**Related Files:** `packages/tta-dev-primitives/src/tta_dev_primitives/performance/cache.py`
