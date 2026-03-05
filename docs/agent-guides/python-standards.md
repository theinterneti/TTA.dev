# Python Standards

Deep reference for Python development standards in TTA.dev.

## Language Requirements

- **Python:** 3.11+ required
- **Type hints:** `str | None` not `Optional[str]`
- **Dicts:** `dict[str, Any]` not `Dict[str, Any]`
- **Docstrings:** Google-style
- **Line length:** 100 characters max

## Naming Conventions

| Kind | Style | Example |
|------|-------|---------|
| Classes | `PascalCase` | `WorkflowPrimitive` |
| Functions/methods | `snake_case` | `execute_workflow` |
| Constants | `UPPER_SNAKE_CASE` | `MAX_RETRIES` |
| Private members | `_prefix` | `_internal_method` |

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
    return result
```

## Docstring Template

Every public function requires a docstring:

```python
async def execute(
    self,
    input_data: TInput,
    context: WorkflowContext,
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

## Package Manager

**Always use `uv`, never `pip` or `poetry`.**

```bash
uv add package-name          # Install dependency
uv sync --all-extras         # Sync all dependencies
uv run python script.py      # Run Python
```

## Formatter & Linter

- **Formatter:** Ruff at 100-char line length
- **Linter:** Ruff with auto-fix

```bash
uv run ruff format .
uv run ruff check . --fix
```

## Type Checking

Pyright in basic mode:

```bash
uvx pyright platform/
```
