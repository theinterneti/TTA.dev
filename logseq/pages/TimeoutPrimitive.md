# TimeoutPrimitive

alias:: [[TTA.dev/Primitives/TimeoutPrimitive]]
type:: [[Primitive]]
category:: [[Recovery]]

---

> **📍 Canonical Page:** [[TTA.dev/Primitives/TimeoutPrimitive]]

This is an alias page for backward compatibility. All content is at the canonical location above.

---

## 🔗 Related GitHub Issues

- **#6** - [[Phase 2: Core Primitive Instrumentation|https://github.com/theinterneti/TTA.dev/issues/6]]
  - Track timeout events and durations
- **#154** - [[Performance Benchmarks|https://github.com/theinterneti/TTA.dev/issues/154]]
  - Measure timeout overhead

---

## Quick Reference

```python
from tta_dev_primitives.recovery import TimeoutPrimitive

# Circuit breaker with timeout
workflow = TimeoutPrimitive(
    primitive=slow_operation,
    timeout_seconds=30.0
)
```

**Source:** `platform/primitives/src/tta_dev_primitives/recovery/timeout.py`
