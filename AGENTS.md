# TTA.dev Agent Instructions

**Composable workflow primitives for building reliable AI applications.**

## Quick Start

```bash
# Install
uv sync --all-extras

# Test
uv run pytest -v

# Quality checks
uv run ruff format . && uv run ruff check . --fix
```

## Core Concept: Primitives

TTA.dev provides composable primitives. Always use them instead of manual async orchestration.

```python
from tta_dev_primitives import WorkflowContext
from tta_dev_primitives.recovery import RetryPrimitive, FallbackPrimitive
from tta_dev_primitives.performance import CachePrimitive

# Compose with operators
workflow = (
    CachePrimitive(ttl=3600) >>    # Sequential: >>
    RetryPrimitive(max_retries=3) >>
    process_data
)

# Execute
context = WorkflowContext(workflow_id="demo")
result = await workflow.execute(input_data, context)
```

## Repository Structure

```
platform/
├── primitives/      # Core workflow primitives ✅
├── observability/   # OpenTelemetry integration ✅
└── agent-context/   # Agent context management ✅
```

## Key Rules

- **Package manager:** Use `uv`, never `pip`
- **Type hints:** Use `str | None`, not `Optional[str]`
- **Testing:** Use `MockPrimitive` from `tta_dev_primitives.testing`
- **Workflows:** Always compose primitives, never manual try/except loops

## Available Primitives

| Category | Primitives |
|----------|-----------|
| **Core** | `SequentialPrimitive`, `ParallelPrimitive`, `RouterPrimitive` |
| **Recovery** | `RetryPrimitive`, `FallbackPrimitive`, `TimeoutPrimitive` |
| **Performance** | `CachePrimitive`, `MemoryPrimitive` |
| **Testing** | `MockPrimitive` |

## Documentation

- [Getting Started](GETTING_STARTED.md) - Setup and first workflow
- [Primitives Catalog](PRIMITIVES_CATALOG.md) - Complete API reference
- [Package README](platform/primitives/README.md) - Detailed docs

## Anti-Patterns

| ❌ Don't | ✅ Do |
|---------|------|
| `try/except` with retry logic | `RetryPrimitive` |
| `asyncio.wait_for()` | `TimeoutPrimitive` |
| Manual caching dicts | `CachePrimitive` |
| `pip install` | `uv add` |
