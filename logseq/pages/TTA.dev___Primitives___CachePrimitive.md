type:: primitive
category:: Performance
status:: documented
generated:: 2025-12-04

# CachePrimitive

**Source:** `platform/primitives/src/tta_dev_primitives/performance/cache.py`

## Overview

Cache primitive execution results.

## Usage Examples

```python
# Cache expensive LLM calls
    cached_llm = CachePrimitive(
        primitive=expensive_llm_call,
        cache_key_fn=lambda data, ctx: f"{data['prompt']}:{ctx.player_id}",
        ttl_seconds=3600.0  # 1 hour TTL
    )

    # Cache with custom key generation
    cached = CachePrimitive(
        primitive=world_builder,
        cache_key_fn=lambda data, ctx: (
            f"{data['theme']}:{data['setting']}:{ctx.session_id}"
        ),
        ttl_seconds=1800.0  # 30 minutes
    )

    # Short-lived cache for rapid iterations
    cached = CachePrimitive(
        primitive=validation_check,
        cache_key_fn=lambda data, ctx: str(hash(str(data))),
        ttl_seconds=60.0  # 1 minute
    )
```

## Tips & Gotchas

- ⚠️ Cache invalidation is hard - set appropriate TTL
- 💡 Use with MemoryPrimitive for bounded caching
- 📝 Consider cache key uniqueness carefully

## Related

- [[TTA.dev/Primitives]] - Primitives index
- [[TTA.dev/Primitives/Performance]] - Performance primitives


---
**Logseq:** [[TTA.dev/Logseq/Pages/Tta.dev___primitives___cacheprimitive]]
