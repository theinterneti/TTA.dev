type:: primitive
category:: Core
status:: documented
generated:: 2025-12-04

# ParallelPrimitive

**Source:** `platform/primitives/src/tta_dev_primitives/core/parallel.py`

## Overview

Execute primitives in parallel.

All primitives receive the same input and execute concurrently.
Results are collected in a list.

## Usage Example

```python
workflow = ParallelPrimitive([
        world_building,
        character_analysis,
        theme_analysis
    ])
    # Or use | operator:
    workflow = world_building | character_analysis | theme_analysis
```

## Related

- [[TTA.dev/Primitives]] - Primitives index
- [[TTA.dev/Primitives/Core]] - Core primitives
