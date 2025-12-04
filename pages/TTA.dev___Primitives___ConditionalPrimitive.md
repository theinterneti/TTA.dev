type:: primitive
category:: Core
status:: documented
generated:: 2025-12-04

# ConditionalPrimitive

**Source:** `platform/primitives/src/tta_dev_primitives/core/conditional.py`

## Overview

Conditional branching primitive.

Executes different primitives based on a condition function.

## Usage Example

```python
workflow = ConditionalPrimitive(
        condition=lambda result, ctx: result.safety_level != "blocked",
        then_primitive=standard_narrative,
        else_primitive=safe_narrative
    )
```

## Related

- [[TTA.dev/Primitives]] - Primitives index
- [[TTA.dev/Primitives/Core]] - Core primitives
