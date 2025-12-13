# RetryPrimitive

alias:: [[TTA.dev/Primitives/RetryPrimitive]]
type:: [[Primitive]]
category:: [[Recovery]]

---

> **📍 Canonical Page:** [[TTA.dev/Primitives/RetryPrimitive]]

This is an alias page for backward compatibility. All content is at the canonical location above.

---

## 🔗 Related GitHub Issues

- **#6** - [[Phase 2: Core Primitive Instrumentation|https://github.com/theinterneti/TTA.dev/issues/6]]
  - Track retry attempts and backoff delays
- **#154** - [[Performance Benchmarks|https://github.com/theinterneti/TTA.dev/issues/154]]
  - Measure retry overhead

---

## Quick Reference

```python
from tta_dev_primitives.recovery import RetryPrimitive

# Retry with exponential backoff
workflow = RetryPrimitive(
    primitive=api_call,
    max_retries=3,
    backoff_strategy="exponential"
)
```

**Source:** `platform/primitives/src/tta_dev_primitives/recovery/retry.py`


---
**Logseq:** [[TTA.dev/Logseq/Pages/Retryprimitive]]
