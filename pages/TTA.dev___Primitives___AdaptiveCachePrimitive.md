type:: primitive
category:: Adaptive
status:: documented
generated:: 2025-12-04

# AdaptiveCachePrimitive

**Source:** `platform/primitives/src/tta_dev_primitives/adaptive/cache.py`

## Overview

Cache primitive that learns optimal TTL and size parameters.

Learns from execution patterns to optimize:
- TTL (time-to-live) for different contexts
- Maximum cache size to balance memory vs hit rate
- Eviction strategies



The primitive tracks:
- Cache hit rate per context
- Average age of cache hits
- Memory usage vs performance trade-off

And learns:
- Optimal TTL values (queries that benefit from longer/shorter TTL)
- Optimal cache size limits
- Context-specific caching strategies

## Usage Example

```python
from tta_dev_primitives.adaptive import (
        AdaptiveCachePrimitive,
        LogseqStrategyIntegration,
        LearningMode
    )

    # Create adaptive cache that learns optimal TTL
    logseq = LogseqStrategyIntegration("llm_service")
    adaptive_cache = AdaptiveCachePrimitive(
        target_primitive=expensive_llm,
        cache_key_fn=lambda data, ctx: f"{data['prompt']}:{ctx.user_id}",
        logseq_integration=logseq,
        enable_auto_persistence=True,
        learning_mode=LearningMode.ACTIVE
    )

    # Use it - will learn optimal TTL per context
    result = await adaptive_cache.execute({"prompt": "..."}, context)

    # Check learned strategies
    for name, strategy in adaptive_cache.strategies.items():
        print(f"{name}: TTL={strategy.parameters['ttl_seconds']}s")
```

## Related

- [[TTA.dev/Primitives]] - Primitives index
- [[TTA.dev/Primitives/Adaptive]] - Adaptive primitives
