# CachePrimitive
alias:: [[TTA.dev/Primitives/CachePrimitive]]
type:: [[Primitive]]
category:: [[Performance]]

---

> **📍 Canonical Page:** [[TTA.dev/Primitives/CachePrimitive]]

This is an alias page for backward compatibility. All content is at the canonical location above.

---

## 🔗 Related GitHub Issues

- **#6** - [[Phase 2: Core Primitive Instrumentation|https://github.com/theinterneti/TTA.dev/issues/6]]
  - Add OpenTelemetry spans and metrics to CachePrimitive
  - Track cache hit/miss rates
- **#154** - [[Performance Benchmarks|https://github.com/theinterneti/TTA.dev/issues/154]]
  - Benchmark cache operations/sec
  - Measure memory overhead
- **#141** - [[MCP Tool Schemas|https://github.com/theinterneti/TTA.dev/issues/141]]
  - Define JSON schema for cache configuration

---

## Quick Reference

```python
from tta_dev_primitives.performance import CachePrimitive

# Wrap expensive operation with caching
cached_op = CachePrimitive(
    primitive=expensive_llm_call,
    ttl_seconds=3600,
    max_size=1000
)
```

**Source:** `platform/primitives/src/tta_dev_primitives/performance/cache.py`


---
**Logseq:** [[TTA.dev/Logseq/Pages/Cacheprimitive]]
