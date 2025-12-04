# LambdaPrimitive

type:: [[Primitive]]
category:: [[Core]]
package:: [[TTA.dev/Packages/tta-dev-primitives]]
status:: [[Stable]]
version:: 1.0.0
test-coverage:: 100
complexity:: [[Low]]
python-class:: `LambdaPrimitive`
import-path:: `from tta_dev_primitives.core.base import LambdaPrimitive`
related-primitives:: [[TTA.dev/Primitives/WorkflowPrimitive]], [[TTA.dev/Primitives/SequentialPrimitive]]

---

## Overview

- id:: lambda-primitive-overview
  A lightweight primitive that wraps a simple function or lambda expression. Useful for inline transformations, adapters, and quick data manipulations within workflows.

  **Think of it as:** A bridge between simple Python functions and the TTA.dev primitive composition system.

---

## Use Cases

- id:: lambda-primitive-use-cases
  - **Data transformation:** Quick inline data manipulation
  - **Adapters:** Convert between data formats
  - **Filters:** Simple data filtering logic
  - **Quick prototyping:** Rapidly test workflow ideas
  - **Composition glue:** Connect primitives that have different signatures

---

## Key Benefits

- id:: lambda-primitive-benefits
  - ✅ **Minimal boilerplate** - No need to create a full class for simple operations
  - ✅ **Supports sync/async** - Automatically detects and handles both
  - ✅ **Full composition** - Works with `>>` and `|` operators
  - ✅ **Type-safe** - Maintains generic type parameters
  - ✅ **Lightweight** - No overhead for simple transformations

---

## API Reference

- id:: lambda-primitive-api

### Constructor

```python
LambdaPrimitive(func: Callable[[T, WorkflowContext], U])
```

**Parameters:**
- `func`: A function that takes `(input_data, context)` and returns output. Can be sync or async.

---

## Examples

### Basic Transformation

- id:: lambda-basic-example

```python
from tta_dev_primitives.core.base import LambdaPrimitive, WorkflowContext

# Create a simple transformation
uppercase = LambdaPrimitive(lambda x, ctx: x.upper())

# Use in workflow
context = WorkflowContext(correlation_id="test-001")
result = await uppercase.execute("hello", context)
# result: "HELLO"
```

### In Workflow Composition

- id:: lambda-composition-example

```python
from tta_dev_primitives.core.base import LambdaPrimitive

# Chain with other primitives using >>
workflow = (
    input_validator >>
    LambdaPrimitive(lambda data, ctx: {"processed": data["input"].strip()}) >>
    output_formatter
)
```

### Async Lambda

- id:: lambda-async-example

```python
async def async_fetch(data, context):
    async with aiohttp.ClientSession() as session:
        async with session.get(data["url"]) as response:
            return await response.json()

fetch_primitive = LambdaPrimitive(async_fetch)
result = await fetch_primitive.execute({"url": "https://api.example.com"}, context)
```

### Data Adapter

- id:: lambda-adapter-example

```python
# Adapt output format from one primitive to input format of another
adapter = LambdaPrimitive(lambda data, ctx: {
    "query": data["user_input"],
    "context": ctx.metadata.get("session_data", {})
})

workflow = user_input_primitive >> adapter >> llm_primitive
```

---

## Best Practices

- id:: lambda-best-practices

✅ **Use for simple transformations** - One-liners and quick mappings
✅ **Name complex lambdas** - Use named functions for clarity
✅ **Keep it stateless** - Avoid side effects in lambdas
✅ **Use context when needed** - Access metadata, correlation_id, etc.

❌ **Don't use for complex logic** - Create a full WorkflowPrimitive instead
❌ **Don't mutate input data** - Return new data structures
❌ **Don't ignore context** - It's there for observability

---

## Related Content

### Works Well With

- [[TTA.dev/Primitives/SequentialPrimitive]] - Chain lambdas in sequence
- [[TTA.dev/Primitives/ParallelPrimitive]] - Run lambdas in parallel
- [[TTA.dev/Primitives/ConditionalPrimitive]] - Use lambdas as conditions

---

## Metadata

**Source Code:** [base.py](https://github.com/theinterneti/TTA.dev/blob/main/platform/primitives/src/tta_dev_primitives/core/base.py)
**Tests:** [test_base.py](https://github.com/theinterneti/TTA.dev/blob/main/platform/primitives/tests/core/test_base.py)

**Created:** [[2025-12-04]]
**Last Updated:** [[2025-12-04]]
**Status:** [[Stable]] - Production Ready
