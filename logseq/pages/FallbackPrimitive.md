# FallbackPrimitive

alias:: [[TTA.dev/Primitives/FallbackPrimitive]]
type:: [[Primitive]]
category:: [[Recovery]]

---

> **📍 Canonical Page:** [[TTA.dev/Primitives/FallbackPrimitive]]

This is an alias page for backward compatibility. All content is at the canonical location above.

---

## 🔗 Related GitHub Issues

- **#6** - [[Phase 2: Core Primitive Instrumentation|https://github.com/theinterneti/TTA.dev/issues/6]]
  - Add OpenTelemetry spans and metrics
- **#154** - [[Performance Benchmarks|https://github.com/theinterneti/TTA.dev/issues/154]]
  - Benchmark fallback trigger latency

---

## Quick Reference

```python
from tta_dev_primitives.recovery import FallbackPrimitive

# Graceful degradation with fallbacks
workflow = FallbackPrimitive(
    primary=main_llm,
    fallbacks=[backup_llm, cached_response]
)
```

**Source:** `platform/primitives/src/tta_dev_primitives/recovery/fallback.py`
