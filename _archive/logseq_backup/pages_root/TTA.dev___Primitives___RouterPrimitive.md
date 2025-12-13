type:: primitive
category:: Core
status:: documented
generated:: 2025-12-04

# RouterPrimitive

**Source:** `platform/primitives/src/tta_dev_primitives/core/routing.py`

## Overview

Route input to appropriate primitive based on routing function.

## Usage Examples

```python
# Route based on user tier
    router = RouterPrimitive(
        routes={
            "openai": openai_primitive,
            "anthropic": anthropic_primitive,
            "local": local_llm_primitive
        },
        router_fn=lambda data, ctx: ctx.metadata.get("provider", "openai"),
        default="openai"
    )

    # Route based on complexity
    router = RouterPrimitive(
        routes={
            "simple": fast_local_model,
            "complex": premium_cloud_model
        },
        router_fn=lambda data, ctx: (
            "simple" if len(data.get("prompt", "")) < 100 else "complex"
        ),
        default="simple"
    )
```

## Related

- [[TTA.dev/Primitives]] - Primitives index
- [[TTA.dev/Primitives/Core]] - Core primitives


---
**Logseq:** [[TTA.dev/_archive/Logseq_backup/Pages_root/Tta.dev___primitives___routerprimitive]]
