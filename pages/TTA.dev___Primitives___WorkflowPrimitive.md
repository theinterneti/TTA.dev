type:: primitive
category:: Core
status:: documented
generated:: 2025-12-04

# WorkflowPrimitive

**Source:** `platform/primitives/src/tta_dev_primitives/core/base.py`

## Overview

Base class for composable workflow primitives.

Primitives are the building blocks of workflows. They can be composed
using operators:
- `>>` for sequential execution (self then other)
- `|` for parallel execution (self and other concurrently)

## Usage Example

```python
workflow = primitive1 >> primitive2 >> primitive3
    result = await workflow.execute(input_data, context)
```

## Related

- [[TTA.dev/Primitives]] - Primitives index
- [[TTA.dev/Primitives/Core]] - Core primitives
