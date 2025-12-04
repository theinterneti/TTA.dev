type:: primitive
category:: Core
status:: documented
generated:: 2025-12-04

# LambdaPrimitive

**Source:** `platform/primitives/src/tta_dev_primitives/core/base.py`

## Overview

Primitive that wraps a simple function or lambda.

Useful for simple transformations or adapters.

## Usage Example

```python
transform = LambdaPrimitive(lambda x, ctx: x.upper())
    workflow = input_primitive >> transform >> output_primitive
```

## Related

- [[TTA.dev/Primitives]] - Primitives index
- [[TTA.dev/Primitives/Core]] - Core primitives
