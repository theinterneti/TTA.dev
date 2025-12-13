---
description: 'Create a new workflow primitive following TTA.dev patterns'
agent: 'agent'
---

# Create Primitive

Create a new workflow primitive following TTA.dev conventions.

## Requirements

1. Inherit from `WorkflowPrimitive[TInput, TOutput]`
2. Implement `async def execute(self, input_data: TInput, context: WorkflowContext) -> TOutput`
3. Use type hints throughout
4. Include comprehensive docstring
5. Add to `__init__.py` exports

## Template

```python
"""${input:PrimitiveName} primitive implementation."""

from tta_dev_primitives.core.base import WorkflowPrimitive, WorkflowContext

class ${input:PrimitiveName}Primitive(WorkflowPrimitive[${input:InputType}, ${input:OutputType}]):
    """${input:Description}.

    Args:
        ${input:ConstructorArgs}

    Example:
        ```python
        primitive = ${input:PrimitiveName}Primitive(...)
        result = await primitive.execute(input_data, context)
        ```
    """

    def __init__(self, ${input:ConstructorParams}) -> None:
        """Initialize the primitive."""
        super().__init__()
        # Store configuration

    async def execute(
        self,
        input_data: ${input:InputType},
        context: WorkflowContext
    ) -> ${input:OutputType}:
        """Execute the primitive.

        Args:
            input_data: Input to process.
            context: Workflow execution context.

        Returns:
            Processed output.

        Raises:
            WorkflowExecutionError: If execution fails.
        """
        # Implementation here
        pass
```

## After Creating

1. Add tests in `tests/test_${input:module}.py`
2. Export from `__init__.py`
3. Add to `PRIMITIVES_CATALOG.md`
4. Run quality checks: `uv run ruff format . && uv run pytest -v`


---
**Logseq:** [[TTA.dev/.github/Prompts/Create-primitive.prompt]]
