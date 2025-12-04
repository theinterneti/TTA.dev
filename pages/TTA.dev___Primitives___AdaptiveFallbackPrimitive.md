type:: primitive
category:: Adaptive
status:: documented
generated:: 2025-12-04

# AdaptiveFallbackPrimitive

**Source:** `platform/primitives/src/tta_dev_primitives/adaptive/fallback.py`

## Overview

Adaptive fallback that learns which fallback chains work best.

Learns from execution patterns:
- Which services fail most often
- Which fallbacks succeed for different failure types
- Optimal fallback order based on success rates
- Context-specific fallback strategies

## Usage Example

```python
from tta_dev_primitives.adaptive import AdaptiveFallbackPrimitive, LearningMode

    adaptive_fallback = AdaptiveFallbackPrimitive(
        primary=openai_api,
        fallbacks={
            "anthropic": anthropic_api,
            "google": google_api,
            "local": local_llm
        },
        learning_mode=LearningMode.ACTIVE
    )

    result = await adaptive_fallback.execute(data, context)

    # Check learned fallback order
    stats = adaptive_fallback.get_fallback_stats()
    print(f"Optimal fallback order: {stats['best_fallback_order']}")
```

## Related

- [[TTA.dev/Primitives]] - Primitives index
- [[TTA.dev/Primitives/Adaptive]] - Adaptive primitives
