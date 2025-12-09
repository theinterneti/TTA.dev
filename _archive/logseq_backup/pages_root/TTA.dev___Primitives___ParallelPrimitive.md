type:: primitive
category:: Core
status:: documented
generated:: 2025-12-04

# ParallelPrimitive

**Source:** `platform/primitives/src/tta_dev_primitives/core/parallel.py`

## Overview

Execute primitives in parallel.

## Usage Examples

```python
workflow = ParallelPrimitive([
        world_building,
        character_analysis,
        theme_analysis
    ])
    # Or use | operator:
    workflow = world_building | character_analysis | theme_analysis
```

## Tips & Gotchas

- ⚠️ Errors in one branch don't cancel others by default
- 💡 Set `max_concurrency` to limit resource usage
- 📝 Results maintain order of input primitives

## Related

- [[TTA.dev/Primitives]] - Primitives index
- [[TTA.dev/Primitives/Core]] - Core primitives
