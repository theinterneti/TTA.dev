---
applyTo: "packages/**/src/**/*.py"
description: "Python package source code - production quality standards"
---

# TTA.dev - AI Development Toolkit

**Production-quality agentic primitives and workflow patterns for building reliable AI applications.**

[![CI](https://github.com/theinterneti/TTA.dev/workflows/CI/badge.svg)](https://github.com/theinterneti/TTA.dev/actions)
[![Quality](https://github.com/theinterneti/TTA.dev/workflows/Quality%20Checks/badge.svg)](https://github.com/theinterneti/TTA.dev/actions)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Code style: Ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)
[![Type checked: Pyright](https://img.shields.io/badge/type%20checked-pyright-blue.svg)](https://github.com/microsoft/pyright)

---

## 🎯 What is TTA.dev?

TTA.dev is a curated collection of **battle-tested components following production-quality standards** for building reliable AI applications. Every component here has:

- ✅ Comprehensive test coverage (52% overall, Core: 88%, Performance: 100%)
- ✅ Real-world usage validation
- ✅ Comprehensive documentation
- ✅ Zero known critical bugs

**Philosophy:** Only proven code following production-quality standards enters this repository.

---

## 📦 Packages

### tta-dev-primitives

Production-quality development primitives for building TTA agents and workflows. Provides composable workflow patterns, recovery strategies, performance utilities, and observability tools.

**Features:**
- 🔀 Router, Cache, Timeout, Retry primitives
- 🔗 Composition operators (`>>`, `|`)
- ⚡ Parallel and conditional execution
- 📊 OpenTelemetry integration
- 💪 Comprehensive error handling (Retry, Fallback, Compensation)
- 📉 30-40% cost reduction via intelligent caching
- 🧪 Testing utilities with mock primitives

**Installation:**
```bash
# Install from local package
uv pip install -e packages/tta-dev-primitives

# Install with all extras
uv pip install -e "packages/tta-dev-primitives[dev,tracing,apm]"
```

**Quick Start:**

```python
from tta_dev_primitives import RouterPrimitive, CachePrimitive

# Compose workflow with operators
workflow = (
    validate_input >>
    CachePrimitive(ttl=3600) >>
    process_data >>
    generate_response
)

# Execute
result = await workflow.execute(data, context)
```

[📚 Full Documentation](../../packages/tta-dev-primitives/README.md)

---

## 🚀 Quick Start

### Installation

```bash
# Install from local package with uv (recommended)
uv pip install -e packages/tta-dev-primitives

# Install with all extras
uv pip install -e "packages/tta-dev-primitives[dev,tracing,apm]"
```

### Basic Workflow Example

```python
from tta_workflow_primitives import WorkflowContext
from tta_workflow_primitives.core.base import LambdaPrimitive

# Define primitives
validate = LambdaPrimitive(lambda x, ctx: {"validated": True, **x})
process = LambdaPrimitive(lambda x, ctx: {"processed": True, **x})
generate = LambdaPrimitive(lambda x, ctx: {"result": "success"})

# Compose with >> operator
workflow = validate >> process >> generate

# Execute
context = WorkflowContext(workflow_id="demo", session_id="123")
result = await workflow.execute({"input": "data"}, context)

print(result)  # {"validated": True, "processed": True, "result": "success"}
```

---

## 🏗️ Architecture

TTA.dev follows a **composable, modular architecture**:

```
┌─────────────────────────────────────────────────────┐
│                  Your Application                   │
└─────────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────┐
│              tta-dev-primitives                     │
│  ┌────────────┬──────────────┬─────────────────┐   │
│  │   Router   │    Cache     │    Timeout      │   │
│  ├────────────┼──────────────┼─────────────────┤   │
│  │  Parallel  │ Conditional  │     Retry       │   │
│  ├────────────┼──────────────┼─────────────────┤   │
│  │  Fallback  │ Compensation │  Observability  │   │
│  └────────────┴──────────────┴─────────────────┘   │
└─────────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────┐
│           OpenTelemetry / Prometheus                │
│  ┌────────────┬──────────────┬─────────────────┐   │
│  │  Logging   │   Retries    │   Test Utils    │   │
│  └────────────┴──────────────┴─────────────────┘   │
└─────────────────────────────────────────────────────┘
```

---

## 📚 Documentation

- **[Getting Started Guide](../../GETTING_STARTED.md)** - 5-minute quickstart
- **[Architecture Overview](../../docs/architecture/Overview.md)** - System design and principles
- **[Coding Standards](../../docs/development/CodingStandards.md)** - Development best practices
- **[MCP Integration](../../docs/mcp/README.md)** - Model Context Protocol guides
- **[Package Documentation](../../packages/tta-dev-primitives/README.md)** - Detailed API reference

### Additional Resources

- [AI Libraries Comparison](../../docs/integration/AI_Libraries_Comparison.md)
- [Model Selection Guide](../../docs/models/Model_Selection_Strategy.md)
- [Examples](../../packages/tta-dev-primitives/examples/)

---

## 🧪 Testing

The package maintains **52% test coverage** with 35 comprehensive tests (100% passing).

```bash
# Run all tests
cd packages/tta-dev-primitives && uv run pytest -v

# Run with coverage
cd packages/tta-dev-primitives && uv run pytest --cov=src --cov-report=html

# Run specific test module
cd packages/tta-dev-primitives && uv run pytest tests/test_cache.py -v
```

---

## 🛠️ Development

### Prerequisites

- Python 3.11+
- [uv](https://github.com/astral-sh/uv) (recommended) or pip
- VS Code with Copilot (recommended)

### Setup

```bash
# Clone repository
git clone https://github.com/theinterneti/TTA.dev
cd TTA.dev

# Install dependencies
uv sync --all-extras

# Run tests
uv run pytest -v

# Run quality checks
uv run ruff format .
uv run ruff check . --fix
uvx pyright packages/
```

### VS Code Workflow

We provide VS Code tasks for common operations:

1. Press `Cmd/Ctrl+Shift+P`
2. Type "Task: Run Task"
3. Select from:
   - 🧪 Run All Tests
   - ✅ Quality Check (All)
   - 📦 Validate Package
   - 🔍 Lint Code
   - ✨ Format Code

[See full task list](../../.vscode/tasks.json)

---

## 🤝 Contributing

We welcome contributions! However, **only battle-tested, proven code is accepted**.

### Contribution Criteria

Before submitting a PR, ensure:

- ✅ All tests passing
- ✅ Test coverage >80% for new code
- ✅ Documentation complete
- ✅ Ruff + Pyright checks pass
- ✅ Real-world usage validation
- ✅ No known critical bugs

### Contribution Workflow

1. **Create feature branch**

   ```bash
git checkout -b feature/add-awesome-feature
```

2. **Make changes and validate**

   ```bash
./scripts/validation/validate-package.sh <package-name>
```

3. **Commit with semantic message**

   ```bash
git commit -m "feat(package): Add awesome feature"
```

4. **Create PR**

   ```bash
gh pr create --title "feat: Add awesome feature"
```

5. **Squash merge after approval**

[See full contribution guide](../../CONTRIBUTING.md) (Coming soon)

---

## 📋 Code Quality Standards

### Formatting

- **Ruff** with 100 character line length
- Auto-format on save in VS Code

### Linting

- **Ruff** with strict rules
- No unused imports or variables

### Type Checking

- **Pyright** in basic mode
- Type hints required for all functions

### Testing

- **pytest** with AAA pattern
- 52% coverage (Core: 88%, Performance: 100%, Recovery: 67%)
- All tests must pass

### Documentation

- Google-style docstrings
- README for each package
- Examples for all features

---

## 🚦 CI/CD

All PRs automatically run:

- ✅ Ruff format check
- ✅ Ruff lint check
- ✅ Pyright type check
- ✅ pytest (all tests)
- ✅ Coverage report
- ✅ Multi-OS testing (Ubuntu, macOS, Windows)
- ✅ Multi-Python testing (3.11, 3.12)

**Merging requires all checks to pass.**

---

## 📊 Project Status

### Current Release: v0.1.0 (Initial)

| Package | Version | Tests | Coverage | Status |
|---------|---------|-------|----------|--------|
| tta-dev-primitives | 0.1.0 | 35/35 ✅ | 52% | 🟢 Stable |

### Roadmap

- [ ] v0.2.0: Add more workflow primitives (saga, circuit breaker)
- [ ] v0.3.0: Enhanced observability features
- [ ] v1.0.0: First stable release

---

## 🔗 Related Projects

- **TTA** - Therapeutic text adventure game (private)
- **Augment Code** - AI coding assistant
- **GitHub Copilot** - AI pair programmer

---

## 📄 License

MIT License - see [LICENSE](../../LICENSE) for details

---

## 🙏 Acknowledgments

Built with:

- [Python](https://www.python.org/)
- [uv](https://github.com/astral-sh/uv) - Fast Python package installer
- [Ruff](https://github.com/astral-sh/ruff) - Fast Python linter
- [Pyright](https://github.com/microsoft/pyright) - Type checker
- [pytest](https://pytest.org/) - Testing framework
- [GitHub Copilot](https://github.com/features/copilot) - AI assistance

---

## 📧 Contact

- **Maintainer:** @theinterneti
- **Issues:** [GitHub Issues](https://github.com/theinterneti/TTA.dev/issues)
- **Discussions:** [GitHub Discussions](https://github.com/theinterneti/TTA.dev/discussions)

---

## ⭐ Star History

If you find TTA.dev useful, please consider giving it a star! ⭐

---

**Last Updated:** 2025-10-27
**Status:** 🚀 Ready for migration

## Documentation Anti-Patterns

### Missing Docstrings
❌ **BAD**:
```python
async def execute(self, input_data: dict, context: WorkflowContext) -> dict:
    return process(input_data)
```

✅ **GOOD**:
```python
async def execute(self, input_data: dict, context: WorkflowContext) -> dict:
    """
    Process input with validation.

    Args:
        input_data: Data to process
        context: Workflow context

    Returns:
        Processed result

    Example:
```python
        result = await processor.execute({"key": "value"}, context)
        ```
"""
    return process(input_data)
```

### Docstrings Without Examples
❌ **BAD**:
```python
"""Process data and return result."""
```

✅ **GOOD**:
```python
"""
Process data and return result.

Example:
```python
    processor = DataProcessor()
    context = WorkflowContext(workflow_id="demo")
    result = await processor.execute({"query": "test"}, context)
    ```
"""
```

## Testing Anti-Patterns

### Not Using MockPrimitive
❌ **BAD**:
```python
@pytest.mark.asyncio
async def test_workflow():
    # Using real implementations in tests
    workflow = RealStep1() >> RealStep2()
    result = await workflow.execute(data, context)
    assert result == expected
```

✅ **GOOD**:
```python
@pytest.mark.asyncio
async def test_workflow():
    # Using mocks for fast, isolated tests
    mock1 = MockPrimitive("step1", return_value="result1")
    mock2 = MockPrimitive("step2", return_value="result2")
    workflow = mock1 >> mock2
    result = await workflow.execute(data, context)
    assert mock1.call_count == 1
    assert result == "result2"
```

### Not Testing Failures
❌ **BAD**:
```python
@pytest.mark.asyncio
async def test_success():
    # Only testing happy path
    result = await primitive.execute(valid_data, context)
    assert result == expected
```

✅ **GOOD**:
```python
@pytest.mark.asyncio
async def test_success():
    result = await primitive.execute(valid_data, context)
    assert result == expected

@pytest.mark.asyncio
async def test_invalid_input():
    with pytest.raises(ValidationError, match="Missing required field"):
        await primitive.execute(invalid_data, context)

@pytest.mark.asyncio
async def test_timeout():
    slow_mock = MockPrimitive("slow", side_effect=asyncio.TimeoutError())
    with pytest.raises(asyncio.TimeoutError):
        await slow_mock.execute(data, context)
```

## Development Workflow Anti-Patterns

### Modifying Code Without Running Quality Checks
❌ **BAD**:
```bash
# Make changes, commit directly
git add .
git commit -m "fix stuff"
```

✅ **GOOD**:
```bash
# Make changes, run quality checks
uv run ruff format .
uv run ruff check . --fix
uvx pyright packages/
uv run pytest -v
git add .
git commit -m "fix: specific description of fix"
```

### Committing Without Tests
❌ **BAD**:
```bash
# Add new feature
git add packages/tta-dev-primitives/src/core/new_feature.py
git commit -m "feat: add new feature"
```

✅ **GOOD**:
```bash
# Add new feature with tests
git add packages/tta-dev-primitives/src/core/new_feature.py
git add packages/tta-dev-primitives/tests/test_new_feature.py
uv run pytest -v
git commit -m "feat: add new feature with tests"
```

## Remember

**This is a production library** - avoid these patterns to maintain:
- ✅ Type safety
- ✅ Test coverage
- ✅ Composability
- ✅ Reliability
- ✅ Maintainability

### Running Tests

```bash
# All tests
cd packages/tta-dev-primitives && uv run pytest -v

# With coverage
cd packages/tta-dev-primitives && uv run pytest --cov=src --cov-report=html

# Specific test module
cd packages/tta-dev-primitives && uv run pytest tests/test_cache.py -v

# Use VS Code task: "🧪 Run All Tests"
```

### Creating a PR

1. Run quality checks: `uv run pytest -v && uv run ruff format . && uvx pyright packages/`
2. Update `CHANGELOG.md` (if exists)
3. Follow PR template in `.github/PULL_REQUEST_TEMPLATE.md`
4. Ensure >80% test coverage for new code
5. Use Conventional Commits format: `feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`

## Debugging Tips

- Use `WorkflowContext.metadata` for debugging state across primitives
- Enable structured logging: `from tta_workflow_primitives.observability import setup_logging; setup_logging("DEBUG")`
- Check test output for primitive call counts: `assert mock.call_count == expected`
- For async issues, ensure `@pytest.mark.asyncio` decorator present

## Anti-Patterns to Avoid

❌ Using `pip` instead of `uv`
❌ Creating primitives without type hints
❌ Skipping tests ("will add later")
❌ Global state instead of `WorkflowContext`
❌ Modifying code without running quality checks
❌ Using `Optional[T]` instead of `T | None` (this is Python 3.11+)

## Quick Reference

**Run quality checks**: `cd packages/tta-dev-primitives && uv run pytest -v && uv run ruff check . && uvx pyright .`
**Install package locally**: `uv pip install -e packages/tta-dev-primitives`
**View tasks**: VS Code → Cmd/Ctrl+Shift+P → "Task: Run Task"

**Remember**: This is a production library - every line must be tested, typed, and documented.
1. **Create feature branch**

   ```bash
git checkout -b feature/add-awesome-feature
```

2. **Make changes and validate**

   ```bash
./scripts/validate-package.sh <package-name>
```

3. **Commit with semantic message**

   ```bash
git commit -m "feat(package): Add awesome feature"
```

4. **Create PR**

   ```bash
gh pr create --title "feat: Add awesome feature"
```

5. **Squash merge after approval**

[See full contribution guide](CONTRIBUTING.md) (Coming soon)

---

## 📋 Code Quality Standards

### Formatting

- **Ruff** with 100 character line length
- Auto-format on save in VS Code

### Linting

- **Ruff** with strict rules
- No unused imports or variables

### Type Checking

- **Pyright** in basic mode
- Type hints required for all functions

### Testing

- **pytest** with AAA pattern
- 52% coverage (Core: 88%, Performance: 100%, Recovery: 67%)
- All tests must pass

### Documentation

- Google-style docstrings
- README for each package
- Examples for all features

---

## 🚦 CI/CD

All PRs automatically run:

- ✅ Ruff format check
- ✅ Ruff lint check
- ✅ Pyright type check
- ✅ pytest (all tests)
- ✅ Coverage report
- ✅ Multi-OS testing (Ubuntu, macOS, Windows)
- ✅ Multi-Python testing (3.11, 3.12)

**Merging requires all checks to pass.**

---

## 📊 Project Status

### Current Release: v0.1.0 (Initial)

| Package | Version | Tests | Coverage | Status |
|---------|---------|-------|----------|--------|
| tta-dev-primitives | 0.1.0 | 35/35 ✅ | 52% | 🟢 Stable |

### Roadmap

- [ ] v0.2.0: Add more workflow primitives (saga, circuit breaker)
- [ ] v0.3.0: Enhanced observability features
- [ ] v1.0.0: First stable release

---

## 🔗 Related Projects

- **TTA** - Therapeutic text adventure game (private)
- **Augment Code** - AI coding assistant
- **GitHub Copilot** - AI pair programmer

---

## 📄 License

MIT License - see [LICENSE](LICENSE) for details

---

## 🙏 Acknowledgments

Built with:

- [Python](https://www.python.org/)
- [uv](https://github.com/astral-sh/uv) - Fast Python package installer
- [Ruff](https://github.com/astral-sh/ruff) - Fast Python linter
- [Pyright](https://github.com/microsoft/pyright) - Type checker
- [pytest](https://pytest.org/) - Testing framework
- [GitHub Copilot](https://github.com/features/copilot) - AI assistance

---

## 📧 Contact

- **Maintainer:** @theinterneti
- **Issues:** [GitHub Issues](https://github.com/theinterneti/TTA.dev/issues)
- **Discussions:** [GitHub Discussions](https://github.com/theinterneti/TTA.dev/discussions)

---

## ⭐ Star History

If you find TTA.dev useful, please consider giving it a star! ⭐

---

**Last Updated:** 2025-10-27
**Status:** 🚀 Ready for migration
ation
n
seful, please consider giving it a star! ⭐

---

**Last Updated:** 2025-10-27
**Status:** 🚀 Ready for migration

@pytest.mark.asyncio
async def test_workflow():
    # Using mocks for fast, isolated tests
    mock1 = MockPrimitive("step1", return_value="result1")
    mock2 = MockPrimitive("step2", return_value="result2")
    workflow = mock1 >> mock2
    result = await workflow.execute(data, context)
    assert mock1.call_count == 1
    assert result == "result2"
```

### Not Testing Failures
❌ **BAD**:
```python
@pytest.mark.asyncio
async def test_success():
    # Only testing happy path
    result = await primitive.execute(valid_data, context)
    assert result == expected
```

✅ **GOOD**:
```python
@pytest.mark.asyncio
async def test_success():
    result = await primitive.execute(valid_data, context)
    assert result == expected

@pytest.mark.asyncio
async def test_invalid_input():
    with pytest.raises(ValidationError, match="Missing required field"):
        await primitive.execute(invalid_data, context)

@pytest.mark.asyncio
async def test_timeout():
    slow_mock = MockPrimitive("slow", side_effect=asyncio.TimeoutError())
    with pytest.raises(asyncio.TimeoutError):
        await slow_mock.execute(data, context)
```

## Development Workflow Anti-Patterns

### Modifying Code Without Running Quality Checks
❌ **BAD**:
```bash
# Make changes, commit directly
git add .
git commit -m "fix stuff"
```

✅ **GOOD**:
```bash
# Make changes, run quality checks
uv run ruff format .
uv run ruff check . --fix
uvx pyright packages/
uv run pytest -v
git add .
git commit -m "fix: specific description of fix"
```

### Committing Without Tests
❌ **BAD**:
```bash
# Add new feature
git add packages/tta-dev-primitives/src/core/new_feature.py
git commit -m "feat: add new feature"
```

✅ **GOOD**:
```bash
# Add new feature with tests
git add packages/tta-dev-primitives/src/core/new_feature.py
git add packages/tta-dev-primitives/tests/test_new_feature.py
uv run pytest -v
git commit -m "feat: add new feature with tests"
```

## Remember

**This is a production library** - avoid these patterns to maintain:
- ✅ Type safety
- ✅ Test coverage
- ✅ Composability
- ✅ Reliability
- ✅ Maintainability
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
# Package Source Code Guidelines

## Core Principles

1. **Use TTA Dev Primitives**: Always compose workflows using primitives
2. **Type Safety First**: Full type annotations required
3. **Test Coverage**: Every public API must have tests
4. **Documentation**: Google-style docstrings with examples

## Type Annotations

```python
# ✅ GOOD: Python 3.11+ style
def process(data: dict[str, Any]) -> str | None:
    ...

class MyPrimitive(WorkflowPrimitive[dict, str]):
    async def execute(self, input_data: dict, context: WorkflowContext) -> str:
        ...

# ❌ BAD: Old style
from typing import Optional, Dict, Any

def process(data: Dict[str, Any]) -> Optional[str]:  # Don't use this
    ...
```

## Workflow Primitives

All workflows must extend `WorkflowPrimitive[T, U]` and implement `execute()`:

```python
from tta_dev_primitives.core.base import WorkflowPrimitive, WorkflowContext

class MyWorkflow(WorkflowPrimitive[InputType, OutputType]):
    async def execute(self, input_data: InputType, context: WorkflowContext) -> OutputType:
        """
        Brief description.

        Args:
            input_data: Description
            context: Workflow context for tracing

        Returns:
            Description

        Example:
```python
            workflow = MyWorkflow()
            context = WorkflowContext(workflow_id="demo")
            result = await workflow.execute(input_data, context)
            ```
"""
        # Implementation
        pass
```

## Composition Patterns

Use operators for composition:

```python
# Sequential
workflow = step1 >> step2 >> step3

# Parallel
workflow = branch1 | branch2 | branch3

# Mixed
workflow = input_step >> (parallel1 | parallel2) >> aggregator
```

## Context Management

**Never use global state**. Pass data through `WorkflowContext`:

```python
# ✅ GOOD: Use context
async def execute(self, input_data: dict, context: WorkflowContext) -> dict:
    user_id = context.metadata.get("user_id")
    context.state["processed_count"] = context.state.get("processed_count", 0) + 1
    return result

# ❌ BAD: Global state
GLOBAL_COUNTER = 0  # Don't do this

async def execute(self, input_data: dict, context: WorkflowContext) -> dict:
    global GLOBAL_COUNTER  # Don't do this
    GLOBAL_COUNTER += 1
    ...
```

## Error Handling

Use specific exceptions with context:

```python
# ✅ GOOD
class ValidationError(Exception):
    """Raised when input validation fails."""
    pass

async def execute(self, input_data: dict, context: WorkflowContext) -> dict:
    if not input_data.get("required_field"):
        raise ValidationError(
            f"Missing required_field in {self.__class__.__name__} "
            f"for workflow_id={context.workflow_id}"
        )

# ❌ BAD
async def execute(self, input_data: dict, context: WorkflowContext) -> dict:
    if not input_data.get("required_field"):
        raise Exception("Missing field")  # Too generic, no context
```

## Naming Conventions

- Classes: `PascalCase` ending in `Primitive` for workflow components
- Functions/variables: `snake_case`
- Constants: `UPPER_SNAKE_CASE`
- Private members: `_leading_underscore`

## Documentation Requirements

Every public class and method needs Google-style docstrings:

```python
async def execute(self, input_data: dict, context: WorkflowContext) -> dict:
    """
    Process input data with validation and transformation.

    This method validates the input structure, applies transformations,
    and returns the processed result.

    Args:
        input_data: Raw input containing 'query' and optional 'params'
        context: Workflow context with session tracking info

    Returns:
        Processed data with 'result' and 'metadata' keys

    Raises:
        ValidationError: If required fields are missing
        TimeoutError: If processing exceeds configured timeout

    Example:
```python
        processor = DataProcessor(timeout=5.0)
        context = WorkflowContext(workflow_id="process-123")
        result = await processor.execute(
            {"query": "test", "params": {}},
            context
        )
        ```
"""
    ...
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
from tta_dev_primitives.recovery.retry import RetryPrimitive
```

## Pydantic Models

Use Pydantic v2 for all data structures:

```python
from pydantic import BaseModel, Field

class InputData(BaseModel):
    """Input structure for processing."""

    query: str = Field(..., description="Search query")
    max_results: int = Field(10, ge=1, le=100, description="Maximum results")
    metadata: dict[str, Any] = Field(default_factory=dict)
```

## Quality Checklist

Before committing, ensure:
- [ ] Full type annotations
- [ ] Google-style docstrings with examples
- [ ] Tests using `MockPrimitive`
- [ ] No global state
- [ ] Specific exceptions with context
- [ ] Uses primitives for composition
- [ ] Formatted with `uv run ruff format`
- [ ] Linted with `uv run ruff check --fix`
- [ ] Type-checked with `uvx pyright`
ntext) -> dict:
    """
    Process input data with validation and transformation.

    This method validates the input structure, applies transformations,
    and returns the processed result.

    Args:
        input_data: Raw input containing 'query' and optional 'params'
        context: Workflow context with session tracking info

    Returns:
        Processed data with 'result' and 'metadata' keys

    Raises:
        ValidationError: If required fields are missing
        TimeoutError: If processing exceeds configured timeout

    Example:
        ```python
        processor = DataProcessor(timeout=5.0)
        context = WorkflowContext(workflow_id="process-123")
        result = await processor.execute(
            {"query": "test", "params": {}},
            context
        )
        ```
    """
    ...
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
from tta_dev_primitives.recovery.retry import RetryPrimitive
```

## Pydantic Models

Use Pydantic v2 for all data structures:

```python
from pydantic import BaseModel, Field

class InputData(BaseModel):
    """Input structure for processing."""

    query: str = Field(..., description="Search query")
    max_results: int = Field(10, ge=1, le=100, description="Maximum results")
    metadata: dict[str, Any] = Field(default_factory=dict)
```

## Quality Checklist

Before committing, ensure:
- [ ] Full type annotations
- [ ] Google-style docstrings with examples
- [ ] Tests using `MockPrimitive`
- [ ] No global state
- [ ] Specific exceptions with context
- [ ] Uses primitives for composition
- [ ] Formatted with `uv run ruff format`
- [ ] Linted with `uv run ruff check --fix`
- [ ] Type-checked with `uvx pyright`


---
**Logseq:** [[TTA.dev/_archive/Nested_copies/Framework/.github/Instructions/Package-source.instructions.instructions]]
