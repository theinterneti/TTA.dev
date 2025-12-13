# Python

**Tag page for Python development, tools, and best practices**

---

## Overview

**Python** in TTA.dev includes:
- 🐍 Python 3.9+ development
- 📦 Package management (uv)
- 🧪 Testing frameworks
- 🔧 Development tools
- 📚 Type hints and documentation

**Goal:** Modern Python development with best practices and tooling.

**See:** [[Infrastructure]], [[Testing]]

---

## Pages Tagged with #Python

{{query (page-tags [[Python]])}}

---

## Python Development

### 1. Python Versions

**Supported versions:**

```bash
# TTA.dev supports Python 3.9+
python --version

# Recommended: Python 3.11+
# Benefits: Better performance, improved type hints, cleaner syntax
```

**Version-specific features used:**

```python
# Python 3.9+: Type hints without imports
def process(data: dict[str, Any]) -> list[str]:
    return list(data.keys())

# Python 3.10+: Match statements
match status:
    case "success":
        return True
    case "error":
        return False
    case _:
        return None

# Python 3.11+: Exception groups
try:
    workflow.execute()
except* ValueError as e:
    log.error(f"Value errors: {e.exceptions}")
except* TypeError as e:
    log.error(f"Type errors: {e.exceptions}")
```

**See:** [[TTA.dev/Python Requirements]]

---

### 2. Package Management with uv

**Why uv?**

- ⚡ **10-100x faster** than pip
- 🔒 **Deterministic** dependency resolution
- 🎯 **Modern** Python tooling
- 📦 **Workspace** support for monorepos
- 🚀 **Built-in** virtual environment management

---

**Installation:**

```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Verify installation
uv --version

# Initialize project
uv init

# Add to existing project
uv add --dev pytest pytest-asyncio
```

---

**Common commands:**

```bash
# Sync dependencies
uv sync --all-extras

# Add dependency
uv add requests httpx pydantic

# Add dev dependency
uv add --dev pytest ruff pyright

# Update dependencies
uv lock --upgrade

# Run command in venv
uv run pytest

# Run Python script
uv run python script.py

# List dependencies
uv pip list

# Show dependency tree
uv pip tree
```

**See:** [[TTA.dev/uv Guide]]

---

### 3. Project Structure

**Monorepo layout:**

```
TTA.dev/
├── pyproject.toml          # Workspace root
├── packages/
│   ├── tta-dev-primitives/
│   │   ├── pyproject.toml
│   │   ├── src/
│   │   │   └── tta_dev_primitives/
│   │   │       ├── __init__.py
│   │   │       ├── core/
│   │   │       ├── recovery/
│   │   │       └── performance/
│   │   ├── tests/
│   │   └── examples/
│   │
│   ├── tta-observability-integration/
│   │   ├── pyproject.toml
│   │   └── src/
│   │       └── observability_integration/
│   │
│   └── universal-agent-context/
│       ├── pyproject.toml
│       └── src/
│           └── universal_agent_context/
│
├── scripts/
└── tests/
```

---

**Package pyproject.toml:**

```toml
# platform/primitives/pyproject.toml
[project]
name = "tta-dev-primitives"
version = "0.1.0"
description = "Composable workflow primitives for AI applications"
requires-python = ">=3.9"

dependencies = [
    "structlog>=23.0.0",
    "opentelemetry-api>=1.20.0",
    "prometheus-client>=0.18.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "pytest-asyncio>=0.21.0",
    "pytest-cov>=4.1.0",
    "ruff>=0.1.0",
    "pyright>=1.1.0",
]

[tool.ruff]
line-length = 100
target-version = "py39"

[tool.pyright]
typeCheckingMode = "strict"
pythonVersion = "3.9"
```

---

### 4. Type Hints

**Modern type hints:**

```python
from typing import Any, TypeVar
from collections.abc import Callable, Awaitable

# Generic types
T = TypeVar("T")
U = TypeVar("U")

# Modern syntax (3.9+)
def process(data: dict[str, Any]) -> list[str]:
    return list(data.keys())

# Union types (3.10+)
def handle(value: int | str | None) -> bool:
    return value is not None

# Generic classes
class WorkflowPrimitive[TInput, TOutput]:
    async def execute(
        self,
        input_data: TInput,
        context: WorkflowContext
    ) -> TOutput:
        ...

# Callable types
Transformer = Callable[[dict[str, Any]], Awaitable[dict[str, Any]]]

def apply_transform(fn: Transformer) -> Transformer:
    async def wrapper(data: dict[str, Any]) -> dict[str, Any]:
        return await fn(data)
    return wrapper
```

**See:** [[TTA.dev/Type Hints Guide]]

---

### 5. Async/Await Patterns

**Async primitives:**

```python
import asyncio
from typing import Any

# Basic async function
async def fetch_data(url: str) -> dict[str, Any]:
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        return response.json()

# Concurrent execution
async def fetch_all(urls: list[str]) -> list[dict[str, Any]]:
    tasks = [fetch_data(url) for url in urls]
    return await asyncio.gather(*tasks)

# With timeout
async def fetch_with_timeout(url: str, timeout: float = 10.0) -> dict[str, Any]:
    return await asyncio.wait_for(
        fetch_data(url),
        timeout=timeout
    )

# Error handling
async def safe_fetch(url: str) -> dict[str, Any] | None:
    try:
        return await fetch_data(url)
    except Exception as e:
        logger.error(f"Failed to fetch {url}: {e}")
        return None
```

**See:** [[TTA.dev/Async Patterns]]

---

### 6. Testing with pytest

**Test structure:**

```python
import pytest
from tta_dev_primitives import WorkflowContext

# Async test
@pytest.mark.asyncio
async def test_primitive():
    """Test primitive execution."""
    primitive = MyPrimitive()
    context = WorkflowContext()

    result = await primitive.execute({"input": "test"}, context)

    assert result["output"] == "expected"

# Fixture
@pytest.fixture
def sample_data():
    """Provide sample test data."""
    return {"key": "value"}

# Parametrized test
@pytest.mark.parametrize("input_value,expected", [
    ("hello", "HELLO"),
    ("world", "WORLD"),
])
async def test_transform(input_value: str, expected: str):
    """Test transformation with multiple inputs."""
    result = await transform(input_value)
    assert result == expected

# Exception testing
async def test_error_handling():
    """Test error handling."""
    with pytest.raises(ValueError, match="Invalid input"):
        await primitive.execute({"invalid": "data"}, context)
```

---

**Test execution:**

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=packages --cov-report=html

# Run specific test
uv run pytest tests/test_primitive.py::test_execution

# Run with markers
uv run pytest -m "not slow"

# Verbose output
uv run pytest -v

# Stop on first failure
uv run pytest -x

# Run in parallel
uv run pytest -n auto
```

**See:** [[Testing]], [[TTA.dev/Testing Guide]]

---

## Python Tools

### 1. Ruff - Linting and Formatting

**Configuration:**

```toml
# pyproject.toml
[tool.ruff]
line-length = 100
target-version = "py39"

[tool.ruff.lint]
select = [
    "E",   # pycodestyle errors
    "W",   # pycodestyle warnings
    "F",   # pyflakes
    "I",   # isort
    "B",   # flake8-bugbear
    "C4",  # flake8-comprehensions
    "UP",  # pyupgrade
]
ignore = [
    "E501",  # line too long (handled by formatter)
]

[tool.ruff.format]
quote-style = "double"
indent-style = "space"
```

---

**Usage:**

```bash
# Format code
uv run ruff format .

# Check code
uv run ruff check .

# Fix issues
uv run ruff check . --fix

# Check specific file
uv run ruff check src/module.py
```

**See:** [[TTA.dev/Code Quality]]

---

### 2. Pyright - Type Checking

**Configuration:**

```toml
# pyproject.toml
[tool.pyright]
typeCheckingMode = "strict"
pythonVersion = "3.9"
pythonPlatform = "Linux"

include = ["src"]
exclude = [
    "**/__pycache__",
    "**/node_modules",
    ".venv",
]

reportMissingImports = true
reportMissingTypeStubs = false
reportUnknownMemberType = false
reportUnknownArgumentType = false
```

---

**Usage:**

```bash
# Type check all packages
uvx pyright packages/

# Type check specific package
uvx pyright platform/primitives/

# Type check with config
uvx pyright --project pyproject.toml
```

**See:** [[TTA.dev/Type Checking]]

---

### 3. pytest - Testing Framework

**Configuration:**

```toml
# pyproject.toml
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py", "*_test.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]

asyncio_mode = "auto"

markers = [
    "slow: marks tests as slow (deselect with '-m \"not slow\"')",
    "integration: marks tests as integration tests",
]

# Coverage
[tool.coverage.run]
source = ["packages"]
omit = [
    "*/tests/*",
    "*/examples/*",
]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise AssertionError",
    "raise NotImplementedError",
    "if __name__ == .__main__.:",
]
```

**See:** [[Testing]]

---

## Python Best Practices

### ✅ DO

**Use Type Hints:**
```python
# ✅ Good: Full type hints
def process(data: dict[str, Any]) -> list[str]:
    return list(data.keys())

# ❌ Bad: No type hints
def process(data):
    return list(data.keys())
```

**Use Context Managers:**
```python
# ✅ Good: Context manager
async with httpx.AsyncClient() as client:
    response = await client.get(url)

# ❌ Bad: Manual cleanup
client = httpx.AsyncClient()
try:
    response = await client.get(url)
finally:
    await client.aclose()
```

**Use Modern Syntax:**
```python
# ✅ Good: Modern (3.9+)
def process(data: dict[str, Any]) -> list[str]:
    ...

# ❌ Bad: Old style
from typing import Dict, List, Any

def process(data: Dict[str, Any]) -> List[str]:
    ...
```

---

### ❌ DON'T

**Don't Ignore Type Errors:**
```python
# ❌ Bad: Silencing errors
result = cast(dict, data)  # type: ignore

# ✅ Good: Fix the issue
if isinstance(data, dict):
    result = data
```

**Don't Use Mutable Defaults:**
```python
# ❌ Bad: Mutable default
def process(items: list[str] = []) -> list[str]:
    items.append("new")
    return items

# ✅ Good: None default
def process(items: list[str] | None = None) -> list[str]:
    if items is None:
        items = []
    items.append("new")
    return items
```

---

## Python Patterns

### Pattern: Primitive Implementation

**Create new primitive:**

```python
from tta_dev_primitives import WorkflowPrimitive, WorkflowContext
from typing import Any

class MyPrimitive(WorkflowPrimitive[dict[str, Any], dict[str, Any]]):
    """Custom primitive implementation."""

    def __init__(self, config: dict[str, Any]):
        super().__init__()
        self.config = config

    async def _execute(
        self,
        input_data: dict[str, Any],
        context: WorkflowContext
    ) -> dict[str, Any]:
        """Execute primitive logic."""
        # Implementation
        result = self._process(input_data)

        return {
            "output": result,
            "metadata": {
                "primitive": self.__class__.__name__,
                "context_id": context.correlation_id
            }
        }

    def _process(self, data: dict[str, Any]) -> Any:
        """Internal processing logic."""
        return data.get("input", "").upper()
```

**See:** [[TTA Primitives]], [[TTA.dev/Creating Primitives]]

---

### Pattern: Async Workflow

**Composing async workflows:**

```python
async def build_workflow():
    """Build complete async workflow."""
    # Sequential steps
    workflow = (
        validate_input >>
        process_data >>
        transform_result >>
        save_output
    )

    # With error handling
    safe_workflow = RetryPrimitive(
        primitive=workflow,
        max_retries=3,
        backoff_strategy="exponential"
    )

    # Execute
    context = WorkflowContext(correlation_id="workflow-123")
    result = await safe_workflow.execute(input_data, context)

    return result
```

---

## Related Concepts

- [[Testing]] - Testing strategies
- [[Infrastructure]] - Development environment
- [[TTA Primitives]] - Python primitives
- [[Documentation]] - Python documentation
- [[Examples]] - Python examples

---

## Documentation

- [[TTA.dev/Python Requirements]] - Version requirements
- [[TTA.dev/uv Guide]] - Package manager guide
- [[TTA.dev/Type Hints Guide]] - Type hints reference
- [[TTA.dev/Async Patterns]] - Async/await patterns
- [[TTA.dev/Testing Guide]] - Testing practices

---

**Tags:** #python #development #tools #best-practices #testing #index-page

**Last Updated:** 2025-11-05
**Maintained by:** TTA.dev Team


---
**Logseq:** [[TTA.dev/Logseq/Pages/Python]]
