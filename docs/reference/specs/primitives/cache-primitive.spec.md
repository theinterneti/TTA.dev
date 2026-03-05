# CachePrimitive Specification

- **Version:** 1.3.0
- **Status:** Approved
- **Package:** tta-dev-primitives
- **Source:** `platform/primitives/src/tta_dev_primitives/performance/cache.py`

## 1. Purpose

`CachePrimitive` wraps another primitive and caches its results using a user-supplied key
function. Subsequent calls with the same cache key return the cached result without
re-executing the wrapped primitive, reducing latency and cost.

## 2. Contract

### 2.1 Type Signature

```python
class CachePrimitive(WorkflowPrimitive[Any, Any]):
    def __init__(
        self,
        primitive: WorkflowPrimitive,
        cache_key_fn: Callable[[Any, WorkflowContext], str],
        ttl_seconds: float = 3600.0,
    ): ...
```

### 2.2 Constructor Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `primitive` | `WorkflowPrimitive` | *(required)* | Primitive whose results are cached |
| `cache_key_fn` | `Callable[[Any, WorkflowContext], str]` | *(required)* | Function generating cache keys from input and context |
| `ttl_seconds` | `float` | `3600.0` | Time-to-live for cached entries in seconds |

### 2.3 Behavior Invariants

- `execute()` MUST call `cache_key_fn(input_data, context)` to generate the cache key.
- If a cached entry exists AND has not expired (age < `ttl_seconds`), `execute()` MUST return the cached value without executing the wrapped primitive.
- If no cached entry exists OR the entry has expired, `execute()` MUST:
  1. Evict the expired entry (if applicable).
  2. Execute the wrapped primitive.
  3. Store the result with the current timestamp.
  4. Return the result.
- `execute()` MUST track hit/miss counts in `context.state["cache_hits"]` and `context.state["cache_misses"]`.
- `clear_cache()` MUST remove all cached entries and reset statistics.
- `get_stats()` MUST return a dict with keys: `size`, `hits`, `misses`, `expirations`, `hit_rate`.
- `get_hit_rate()` MUST return hits / (hits + misses) * 100, or 0.0 if no operations.
- `evict_expired()` MUST remove all expired entries and return the count removed.

### 2.4 Error Contract

| Condition | Exception | Description |
|-----------|-----------|-------------|
| `cache_key_fn` raises | *(propagated)* | Exception from the key function propagates |
| Wrapped primitive raises (cache miss) | *(propagated)* | Exception propagates; result is NOT cached |
| Cached value is stale | *(none)* | Expired entries are evicted, fresh execution occurs |

### 2.5 Observability Contract

**Logging:**

| Event | Level | Fields |
|-------|-------|--------|
| `cache_hit` | DEBUG | `key`, `age_seconds` |
| `cache_miss` | DEBUG | `key` |
| `cache_expired` | DEBUG | `key`, `age_seconds` |
| `cache_store` | DEBUG | `key` |
| `cache_cleared` | INFO | *(none)* |
| `cache_eviction` | DEBUG | `evicted_count` |

**State tracking:** `context.state["cache_hits"]` and `context.state["cache_misses"]` counters.

## 3. Composition Rules

- Standard `>>` and `|` operators apply.
- `CachePrimitive(A, key_fn) >> B` — A's result is cached, then passed to B.
- Common pattern: `CachePrimitive(RetryPrimitive(A), key_fn)` — retry on miss, cache on success.

## 4. Edge Cases

| Input | Expected Behavior |
|-------|-------------------|
| `ttl_seconds = 0` | Every call is a miss (entries expire immediately) |
| `ttl_seconds` is very large | Entries effectively never expire |
| `cache_key_fn` returns same key for different inputs | All inputs share one cached result |
| Wrapped primitive returns `None` | `None` is cached and returned on hits |
| Concurrent calls with same key | Race condition; both may execute, last write wins |

## 5. Cross-References

- [WorkflowPrimitive Spec](workflow-primitive.spec.md) — Base class
- [MemoryPrimitive Spec](memory-primitive.spec.md) — Long-term memory storage
- [Metrics Catalog](../observability/metrics-catalog.spec.md) — Cache hit/miss metrics
