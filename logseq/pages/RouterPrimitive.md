# RouterPrimitive

alias:: [[TTA.dev/Primitives/RouterPrimitive]]
type:: [[Primitive]]
category:: [[Core]]

---

> **📍 Canonical Page:** [[TTA.dev/Primitives/RouterPrimitive]]

This is an alias page for backward compatibility. All content is at the canonical location above.

---

## 🔗 Related GitHub Issues

- **#6** - [[Phase 2: Core Primitive Instrumentation|https://github.com/theinterneti/TTA.dev/issues/6]]
  - Log routing decisions with context
- **#141** - [[MCP Tool Schemas|https://github.com/theinterneti/TTA.dev/issues/141]]
  - Define JSON schema for routing config

---

## Quick Reference

```python
from tta_dev_primitives import RouterPrimitive

# Dynamic routing based on input
router = RouterPrimitive(
    routes={"fast": gpt4_mini, "quality": gpt4},
    default_route="fast"
)
```

**Source:** `platform/primitives/src/tta_dev_primitives/core/routing.py`


---
**Logseq:** [[TTA.dev/Logseq/Pages/Routerprimitive]]
