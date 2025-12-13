type:: primitive
category:: Core
status:: documented
generated:: 2025-12-04

# SequentialPrimitive

**Source:** `platform/primitives/src/tta_dev_primitives/core/sequential.py`

## Overview

Execute primitives in sequence.

## Usage Examples

```python
workflow = SequentialPrimitive([
        input_processing,
        world_building,
        narrative_generation
    ])
    # Or use >> operator:
    workflow = input_processing >> world_building >> narrative_generation
```

## Related

- [[TTA.dev/Primitives]] - Primitives index
- [[TTA.dev/Primitives/Core]] - Core primitives


---
**Logseq:** [[TTA.dev/_archive/Logseq_backup/Pages_root/Tta.dev___primitives___sequentialprimitive]]
