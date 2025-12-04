---
description: 'Python code standards for TTA.dev packages'
applyTo: 'platform/**/src/**/*.py'
---

# Python Development

## General Instructions

- Use Python 3.11+ features
- Type hints: `str | None` not `Optional[str]`
- Dicts: `dict[str, Any]` not `Dict[str, Any]`
- Follow Google-style docstrings
- Maximum line length: 100 characters

## Naming Conventions

- Classes: `PascalCase` (e.g., `WorkflowPrimitive`)
- Functions/methods: `snake_case` (e.g., `execute_workflow`)
- Constants: `UPPER_SNAKE_CASE` (e.g., `MAX_RETRIES`)
- Private: prefix with `_` (e.g., `_internal_method`)

## Import Order

```python
# 1. Standard library
import asyncio
from typing import Any

# 2. Third-party
import pytest
from opentelemetry import trace

# 3. Local
from tta_dev_primitives import WorkflowPrimitive
```

## Primitives Pattern

All workflow logic must use primitives:

```python
# ✅ Correct: Use primitives
from tta_dev_primitives.recovery import RetryPrimitive

workflow = RetryPrimitive(
    primitive=api_call,
    max_retries=3,
    backoff_strategy="exponential"
)

# ❌ Wrong: Manual retry loop
for attempt in range(3):
    try:
        result = await api_call()
        break
    except Exception:
        await asyncio.sleep(2 ** attempt)
```

## Error Handling

- Define custom exceptions in `exceptions.py`
- Inherit from `TTA*Error` base classes
- Include context in error messages

```python
class WorkflowExecutionError(TTAError):
    """Raised when workflow execution fails."""
    def __init__(self, workflow_id: str, cause: Exception):
        super().__init__(f"Workflow {workflow_id} failed: {cause}")
        self.workflow_id = workflow_id
        self.cause = cause
```

## Async Patterns

- Use `async def` for I/O operations
- Avoid blocking calls in async code
- Use `asyncio.gather()` for parallel operations

```python
async def execute(self, data: dict, context: WorkflowContext) -> dict:
    """Execute the primitive."""
    # Implementation here
    return result
```

## Documentation

Every public function needs:

```python
async def execute(
    self,
    input_data: TInput,
    context: WorkflowContext
) -> TOutput:
    """Execute the primitive with the given input.

    Args:
        input_data: The input data to process.
        context: Workflow context with tracing and metadata.

    Returns:
        The processed output data.

    Raises:
        WorkflowExecutionError: If execution fails.
    """
```

## Validation

Before committing:

```bash
uv run ruff format .
uv run ruff check . --fix
uvx pyright platform/
uv run pytest -v
```
