# How to Create a New Primitive

**Step-by-step guide for implementing custom workflow primitives in TTA.dev**

---

## Overview

This guide walks you through creating a new primitive from scratch, including:
- Class structure and inheritance
- Type annotations
- Implementation details
- Testing
- Documentation
- Integration

**Estimated Time:** 2-4 hours for a complete primitive

---

## Prerequisites

- Python 3.11+ installed
- TTA.dev repository cloned
- Development environment set up (see [[GETTING_STARTED]])
- Understanding of async/await
- Familiarity with type hints

---

## Step 1: Choose Primitive Type

### Questions to Ask

1. **What does this primitive do?**
   - Single responsibility
   - Clear input/output contract

2. **Which category?**
   - Core workflow (sequential, parallel, conditional)
   - Recovery (retry, fallback, timeout)
   - Performance (cache, rate limit)
   - Orchestration (delegation, routing)

3. **Is composition better?**
   - Can you achieve this by combining existing primitives?
   - Create new primitive only if truly reusable

---

## Step 2: Set Up File Structure

### Create Primitive File

```bash
# Choose appropriate directory
cd packages/tta-dev-primitives/src/tta_dev_primitives/

# Examples:
# - core/ for workflow primitives
# - recovery/ for error handling
# - performance/ for optimization
# - orchestration/ for multi-agent

# Create your file
touch category/my_primitive.py
```

### Create Test File

```bash
cd packages/tta-dev-primitives/tests/

# Create corresponding test file
touch test_my_primitive.py
```

---

## Step 3: Implement the Primitive

### Basic Template

```python
"""MyPrimitive - Brief description of what it does."""

from typing import Any
from tta_dev_primitives.observability import InstrumentedPrimitive
from tta_dev_primitives import WorkflowContext


class MyPrimitive(InstrumentedPrimitive[dict, dict]):
    """
    Detailed description of the primitive.

    This primitive [what it does] by [how it works].

    Attributes:
        param1: Description of first parameter
        param2: Description of second parameter

    Example:
        ```python
        from tta_dev_primitives.category import MyPrimitive

        primitive = MyPrimitive(param1="value")
        result = await primitive.execute(input_data, context)
        ```

    Note:
        - Important usage notes
        - Limitations
        - Best practices
    """

    def __init__(
        self,
        param1: str,
        param2: int = 10,
        name: str = "my_primitive"
    ):
        """
        Initialize the primitive.

        Args:
            param1: Description
            param2: Description with default value
            name: Name for observability (default: "my_primitive")
        """
        super().__init__(name=name)
        self.param1 = param1
        self.param2 = param2

    async def _execute_impl(
        self,
        input_data: dict,
        context: WorkflowContext
    ) -> dict:
        """
        Execute the primitive logic.

        Args:
            input_data: Input data dictionary
            context: Workflow context for tracing

        Returns:
            Processed output dictionary

        Raises:
            ValueError: If input is invalid
            RuntimeError: If processing fails
        """
        # Validate input
        if not input_data:
            raise ValueError("Input data cannot be empty")

        # Log execution
        self.logger.info(
            "Executing primitive",
            extra={
                "param1": self.param1,
                "input_size": len(input_data)
            }
        )

        # Your implementation here
        result = self._process(input_data)

        # Add observability attributes
        context.add_attribute("result_size", len(result))

        return result

    def _process(self, data: dict) -> dict:
        """Helper method for processing logic."""
        # Implementation details
        return {
            "processed": True,
            "data": data,
            "param1": self.param1
        }
```

---

## Step 4: Add Type Safety

### Type Annotations

```python
from typing import TypeVar, Generic

# Define generic types
TInput = TypeVar('TInput')
TOutput = TypeVar('TOutput')


class MyGenericPrimitive(InstrumentedPrimitive[TInput, TOutput]):
    """Generic primitive with type safety."""

    async def _execute_impl(
        self,
        input_data: TInput,
        context: WorkflowContext
    ) -> TOutput:
        # Implementation with strong types
        ...
```

### Example: Specific Types

```python
from pydantic import BaseModel


class InputModel(BaseModel):
    query: str
    max_results: int = 10


class OutputModel(BaseModel):
    results: list[str]
    count: int


class SearchPrimitive(InstrumentedPrimitive[InputModel, OutputModel]):
    """Type-safe search primitive."""

    async def _execute_impl(
        self,
        input_data: InputModel,
        context: WorkflowContext
    ) -> OutputModel:
        # Type-safe implementation
        results = await self._search(input_data.query)
        return OutputModel(
            results=results[:input_data.max_results],
            count=len(results)
        )
```

---

## Step 5: Add Observability

### Tracing

```python
async def _execute_impl(
    self,
    input_data: dict,
    context: WorkflowContext
) -> dict:
    # Span is automatically created by InstrumentedPrimitive

    # Add custom attributes
    context.add_attribute("custom_metric", value)

    # Add events
    context.add_event("processing_started")

    # Your logic
    result = await self._process(input_data)

    # Add result attributes
    context.add_attribute("result_size", len(result))

    return result
```

### Metrics

```python
from tta_dev_primitives.observability import PrimitiveMetrics

class MyPrimitive(InstrumentedPrimitive[dict, dict]):
    def __init__(self, name: str = "my_primitive"):
        super().__init__(name=name)
        self.metrics = PrimitiveMetrics(primitive_name=name)

    async def _execute_impl(self, input_data, context):
        # Metrics are automatically collected by InstrumentedPrimitive

        # Add custom metrics if needed
        self.metrics.record_custom_metric("items_processed", count)

        return result
```

---

## Step 6: Write Tests

### Test Template

```python
"""Tests for MyPrimitive."""

import pytest
from tta_dev_primitives.category import MyPrimitive
from tta_dev_primitives import WorkflowContext


@pytest.mark.asyncio
async def test_my_primitive_basic():
    """Test basic functionality."""
    # Arrange
    primitive = MyPrimitive(param1="test")
    context = WorkflowContext(workflow_id="test")
    input_data = {"key": "value"}

    # Act
    result = await primitive.execute(input_data, context)

    # Assert
    assert result["processed"] is True
    assert result["data"] == input_data


@pytest.mark.asyncio
async def test_my_primitive_invalid_input():
    """Test error handling."""
    primitive = MyPrimitive(param1="test")
    context = WorkflowContext(workflow_id="test")

    with pytest.raises(ValueError, match="cannot be empty"):
        await primitive.execute({}, context)


@pytest.mark.asyncio
async def test_my_primitive_composition():
    """Test primitive composition."""
    primitive1 = MyPrimitive(param1="first")
    primitive2 = MyPrimitive(param1="second")

    # Sequential composition
    workflow = primitive1 >> primitive2

    context = WorkflowContext(workflow_id="test")
    result = await workflow.execute({"key": "value"}, context)

    assert result is not None


@pytest.mark.asyncio
async def test_my_primitive_observability():
    """Test observability features."""
    primitive = MyPrimitive(param1="test")
    context = WorkflowContext(
        workflow_id="test",
        correlation_id="corr-123"
    )

    result = await primitive.execute({"key": "value"}, context)

    # Check context was updated
    assert context.attributes.get("result_size") is not None
```

---

## Step 7: Add Documentation

### Docstring Standards

```python
class MyPrimitive(InstrumentedPrimitive[dict, dict]):
    """
    One-line summary.

    Detailed description of what the primitive does,
    how it works, and when to use it.

    Attributes:
        param1: Description
        param2: Description

    Example:
        Basic usage:
        ```python
        primitive = MyPrimitive(param1="value")
        result = await primitive.execute(data, context)
        ```

        With composition:
        ```python
        workflow = step1 >> MyPrimitive(param1="value") >> step2
        ```

    Note:
        - Performance considerations
        - Thread safety notes
        - Best practices

    See Also:
        - RelatedPrimitive: Description
        - AnotherPrimitive: Description
    """
```

### Create Example File

```python
# packages/tta-dev-primitives/examples/my_primitive_example.py

"""Example usage of MyPrimitive."""

import asyncio
from tta_dev_primitives.category import MyPrimitive
from tta_dev_primitives import WorkflowContext


async def main():
    """Demonstrate MyPrimitive usage."""
    # Create primitive
    primitive = MyPrimitive(param1="example")

    # Create context
    context = WorkflowContext(workflow_id="example")

    # Execute
    result = await primitive.execute(
        {"input": "data"},
        context
    )

    print(f"Result: {result}")


if __name__ == "__main__":
    asyncio.run(main())
```

---

## Step 8: Update Package Exports

### Add to __init__.py

```python
# packages/tta-dev-primitives/src/tta_dev_primitives/category/__init__.py

from .my_primitive import MyPrimitive

__all__ = ["MyPrimitive"]
```

### Update Main Package

```python
# packages/tta-dev-primitives/src/tta_dev_primitives/__init__.py

from .category import MyPrimitive

__all__ = [
    # ... existing exports
    "MyPrimitive",
]
```

---

## Step 9: Run Quality Checks

```bash
# Format code
uv run ruff format .

# Lint
uv run ruff check . --fix

# Type check
uvx pyright packages/tta-dev-primitives/

# Run tests
uv run pytest packages/tta-dev-primitives/tests/test_my_primitive.py -v

# Coverage
uv run pytest --cov=packages/tta-dev-primitives --cov-report=html
```

---

## Step 10: Update Catalogs

### Add to PRIMITIVES_CATALOG.md

```markdown
### MyPrimitive

**Brief description.**

**Import:**
\`\`\`python
from tta_dev_primitives.category import MyPrimitive
\`\`\`

**Source:** [my_primitive.py](packages/tta-dev-primitives/src/tta_dev_primitives/category/my_primitive.py)

**Usage:**
\`\`\`python
primitive = MyPrimitive(param1="value")
result = await primitive.execute(input_data, context)
\`\`\`

**Properties:**
- ✅ Feature 1
- ✅ Feature 2
- ✅ Automatic observability
```

---

## Checklist

Before submitting your primitive:

- [ ] Primitive class implemented with InstrumentedPrimitive
- [ ] Type annotations complete (TInput, TOutput)
- [ ] Docstrings following standards
- [ ] Unit tests with 100% coverage
- [ ] Integration test with composition
- [ ] Example file created
- [ ] Added to package __init__.py exports
- [ ] PRIMITIVES_CATALOG.md updated
- [ ] Code formatted with ruff
- [ ] Type checked with pyright
- [ ] All tests passing

---

## Common Patterns

### Pattern: Configurable Behavior

```python
class ConfigurablePrimitive(InstrumentedPrimitive[dict, dict]):
    def __init__(
        self,
        mode: Literal["fast", "quality"] = "fast",
        **kwargs
    ):
        super().__init__(name=f"configurable_{mode}")
        self.mode = mode
```

### Pattern: State Management

```python
class StatefulPrimitive(InstrumentedPrimitive[dict, dict]):
    def __init__(self):
        super().__init__(name="stateful")
        self._cache: dict = {}
        self._lock = asyncio.Lock()

    async def _execute_impl(self, input_data, context):
        async with self._lock:
            # Thread-safe state access
            ...
```

### Pattern: External Service Integration

```python
class APIClientPrimitive(InstrumentedPrimitive[dict, dict]):
    def __init__(self, api_key: str):
        super().__init__(name="api_client")
        self.client = httpx.AsyncClient()
        self.api_key = api_key

    async def _execute_impl(self, input_data, context):
        response = await self.client.post(
            url,
            headers={"Authorization": f"Bearer {self.api_key}"}
        )
        return response.json()
```

---

## Troubleshooting

### Issue: "Cannot instantiate abstract class"

**Solution:** Extend `InstrumentedPrimitive` and implement `_execute_impl`:

```python
class MyPrimitive(InstrumentedPrimitive[dict, dict]):
    async def _execute_impl(self, input_data, context):
        # Implementation required
        ...
```

### Issue: Type errors

**Solution:** Ensure generic types match:

```python
# Input and output types must match type parameters
class MyPrimitive(InstrumentedPrimitive[InputType, OutputType]):
    async def _execute_impl(
        self,
        input_data: InputType,  # Must match TInput
        context: WorkflowContext
    ) -> OutputType:  # Must match TOutput
        ...
```

---

## Next Steps

- Create primitive following this guide
- Add tests with 100% coverage
- Document in PRIMITIVES_CATALOG.md
- Share example usage
- Submit pull request

---

## Related Pages

- [[TTA Primitives]]
- [[PRIMITIVES_CATALOG]]
- [[packages/tta-dev-primitives/AGENTS.md]]
- [[How to Add Observability to Workflows]]

---

**Last Updated:** [[2025-10-31]]
**Difficulty:** Intermediate
**Time:** 2-4 hours
