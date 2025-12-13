# Project Overview

# Project Overview

TTA.dev is an **AI development toolkit following production-quality standards** providing battle-tested workflow primitives for building reliable AI applications.

## Core Package

**tta-dev-primitives**: Production-quality development primitives providing:
- Composable workflow patterns (Router, Cache, Timeout, Retry, Sequential, Parallel)
- Recovery strategies (Fallback, Compensation)
- Performance utilities (LRU Cache, optimization)
- Observability tools (Logging, metrics, tracing)

## Philosophy

**Only proven code enters this repository:**
- Comprehensive testing required
- Real production usage validated
- Complete documentation included
- Type-safe implementation

## Repository Structure

This is a **monorepo** with:
- `platform/primitives/` - Core primitives package
- `platform/observability/` - Observability integration
- `platform/agent-context/` - Agent context management
- `scripts/` - Automation scripts (should use primitives)
- `tests/` - Integration tests
- `docs/` - Architecture and development guides
- `archive/` - Legacy code (ignore this)

## Key Principle

**Use primitives for everything** - Any workflow, orchestration, or automation task should compose primitives rather than manual implementation.


# Architecture

# Architecture

## Workflow Primitive Composition

The foundation is `WorkflowPrimitive[T, U]` - all workflows implement:

```python
async execute(input_data: T, context: WorkflowContext) -> U
```

### Composition Operators

**Sequential (>>)**: Output of each becomes input to next
```python
workflow = step1 >> step2 >> step3
```

**Parallel (|)**: All receive same input, returns list of outputs
```python
workflow = branch1 | branch2 | branch3
```

**Mixed**: Combine patterns
```python
workflow = input_processor >> (fast_path | slow_path) >> aggregator
```

## Context Management

**Key insight**: Every primitive receives `WorkflowContext` containing:
- `workflow_id` - Unique workflow identifier
- `session_id` - Session tracking
- `player_id` - User/player identifier
- `metadata` - Additional context data
- `state` - Stateful data passing

**Never use global state** - Pass data through `WorkflowContext`.

## Package Structure

```
platform/<package-name>/
├── src/<package_name>/
│   ├── core/          # Base abstractions
│   ├── recovery/      # Retry, fallback, timeout, compensation
│   ├── performance/   # Cache, optimization
│   ├── observability/ # Logging, metrics, tracing
│   ├── apm/          # Agent Package Manager integration
│   └── testing/       # Test utilities (MockPrimitive)
├── tests/             # Mirror src/ structure
├── pyproject.toml     # Uses hatchling, pytest, ruff, mypy
└── README.md
```

## Available Primitives

### Core Workflows
- `SequentialPrimitive` - Execute in order
- `ParallelPrimitive` - Execute concurrently
- `ConditionalPrimitive` - Branch based on conditions
- `RouterPrimitive` - Dynamic routing with cost optimization

### Recovery
- `RetryPrimitive` - Exponential backoff with jitter
- `FallbackPrimitive` - Graceful degradation
- `TimeoutPrimitive` - Circuit breaker pattern
- `CompensationPrimitive` - Saga pattern for rollback

### Performance
- `CachePrimitive` - LRU cache with TTL

### Utilities
- `LambdaPrimitive` - Wrap any function as primitive
- `MockPrimitive` - Testing utilities


# Development Workflow

# Development Workflow

## Package Management

**ALWAYS use `uv`, never `pip` directly:**

```bash
# Install dependencies
uv sync --all-extras

# Run tests
uv run pytest -v

# Format code
uv run ruff format .

# Lint code
uv run ruff check . --fix

# Type check
uvx pyright platform/ apps/
```

## Testing Requirements

**Comprehensive test coverage is required**:
- Use `pytest-asyncio` with `@pytest.mark.asyncio` for async tests
- Use `MockPrimitive` from `testing/` for workflow testing
- Test files mirror source structure: `src/core/cache.py` → `tests/test_cache.py`
- Coverage command: `uv run pytest --cov=platform --cov-report=html`

Example test pattern:
```python
from tta_dev_primitives.testing import MockPrimitive

@pytest.mark.asyncio
async def test_sequential_workflow():
    mock1 = MockPrimitive("step1", return_value="result1")
    mock2 = MockPrimitive("step2", return_value="result2")
    workflow = mock1 >> mock2

    context = WorkflowContext()
    result = await workflow.execute("input", context)

    assert mock1.call_count == 1
    assert result == "result2"
```

## Quality Gates

Before any commit/PR, run:
```bash
uv run ruff format .
uv run ruff check . --fix
uvx pyright packages/
uv run pytest -v
```

Or use VS Code task: "✅ Quality Check (All)"

## Package Validation

```bash
./scripts/validate-package.sh tta-dev-primitives
```

## Common Tasks

### Adding a New Primitive

1. Create in appropriate subpackage: `src/<package>/core/my_primitive.py`
2. Extend `WorkflowPrimitive[T, U]` with typed generics
3. Implement `async execute(input_data: T, context: WorkflowContext) -> U`
4. Add comprehensive docstring with example
5. Export in `__init__.py`
6. Create `tests/test_my_primitive.py` with 100% coverage
7. Update package README with usage example

### Creating a PR

1. Run quality checks
2. Update `CHANGELOG.md` (if exists)
3. Follow PR template
4. Ensure 100% test coverage for new code
5. Use Conventional Commits: `feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`


# Quality Standards

# Quality Standards

## Type Hints (Strictly Enforced)

- Use Pydantic v2 models for all data structures
- Full type annotations required
- Generic types for primitives: `class MyPrimitive(WorkflowPrimitive[InputType, OutputType])`
- **Python 3.11+ style**: Use `str | None`, NOT `Optional[str]`

## Docstrings (Google Style)

```python
async def execute(self, input_data: dict, context: WorkflowContext) -> dict:
    """
    Process input with intelligent caching.

    Args:
        input_data: Request data with 'query' key
        context: Workflow context with session info

    Returns:
        Processed result with 'response' key

    Raises:
        ValueError: If input_data missing required keys

    Example:
        ```python
        cache = CachePrimitive(ttl=3600)
        result = await cache.execute({"query": "..."}, context)
        ```
    """
```

## Naming Conventions

- **Classes**: `PascalCase` (e.g., `SequentialPrimitive`, `WorkflowContext`)
- **Functions/Variables**: `snake_case`
- **Constants**: `UPPER_SNAKE_CASE`
- **Private members**: `_leading_underscore`
- **Primitives**: Always suffix with `Primitive`

## Error Handling

- Use specific exceptions, not generic `Exception`
- Always include context in error messages
- Use structured logging with correlation IDs from `WorkflowContext`

Example:
```python
if not input_data.get("required_field"):
    raise ValidationError(
        f"Missing required_field in {self.__class__.__name__} "
        f"for workflow_id={context.workflow_id}"
    )
```

## Import Organization

```python
# Standard library
import asyncio
from typing import Any

# Third-party
from pydantic import BaseModel, Field

# Local package - absolute imports
from tta_dev_primitives.core.base import WorkflowContext, WorkflowPrimitive
```

## Anti-Patterns to Avoid

❌ Using `pip` instead of `uv`
❌ Creating primitives without type hints
❌ Skipping tests ("will add later")
❌ Global state instead of `WorkflowContext`
❌ Modifying code without running quality checks
❌ Using `Optional[T]` instead of `T | None`


---
**Logseq:** [[TTA.dev/.augment/Instructions]]
