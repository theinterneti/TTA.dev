---
name: core-conventions
description: Use this skill when writing or reviewing Python code in TTA.dev. Covers package manager, type hints, primitives usage, and anti-patterns.
---

### Core Conventions (TTA.dev)

Non-negotiable standards for all code in the TTA.dev repository.

#### Package Manager

**Always use `uv`, never `pip` or `poetry`.**

```bash
uv add package-name        # Add dependency
uv sync --all-extras       # Sync all dependencies
uv run pytest -v           # Run via uv
```

#### Python Version & Types

- Python 3.11+ required
- `str | None` not `Optional[str]`
- `dict[str, Any]` not `Dict[str, Any]`
- Google-style docstrings on all public functions

#### Primitives — Always Use Them

```python
# ✅ Use primitives
workflow = RetryPrimitive(primitive=api_call, max_retries=3)

# ❌ Never write manual retry/timeout loops
for attempt in range(3):  # WRONG
    try: ...
```

#### Anti-Patterns

| ❌ Don't | ✅ Do |
|---------|------|
| `try/except` retry loops | `RetryPrimitive` |
| `asyncio.wait_for()` | `TimeoutPrimitive` |
| Manual caching dicts | `CachePrimitive` |
| Global variables for state | `WorkflowContext` |
| `pip install` | `uv add` |
| `Optional[str]` | `str \| None` |

#### State Management

Pass state via `WorkflowContext`, never global variables:

```python
context = WorkflowContext(workflow_id="demo")
result = await workflow.execute(input_data, context)
```

#### Deep Reference

- Primitives API & patterns: [`docs/agent-guides/primitives-patterns.md`](../../docs/agent-guides/primitives-patterns.md)
- Python standards: [`docs/agent-guides/python-standards.md`](../../docs/agent-guides/python-standards.md)
- TODO management: [`docs/agent-guides/todo-management.md`](../../docs/agent-guides/todo-management.md)
