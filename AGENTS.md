# TTA.dev - Universal Agent Instructions

**Workspace-wide instructions for all AI coding agents (GitHub Copilot, Cline, Cursor, Augment, Roo, Claude)**

This file defines universal behavior and project context for AI assistants working in this repository. Tool-specific configurations are in their respective directories.

---

## 🎯 Project Overview

**TTA.dev** is an AI Development Toolkit providing:
- **tta-dev-primitives**: Production-ready workflow primitives (Router, Cache, Timeout, Retry)
- **tta-observability-integration**: OpenTelemetry APM with metrics, tracing, and Prometheus export
- **universal-agent-context**: Portable agent configuration system for AI assistants

### Repository Structure

```
TTA.dev/
├── packages/
│   ├── tta-dev-primitives/       # Core workflow primitives
│   ├── tta-observability-integration/  # Observability layer
│   └── universal-agent-context/  # Agent configuration templates
├── scripts/                      # Automation scripts
├── tests/                        # Integration tests
├── docs/                         # Documentation
└── .github/instructions/         # Path-specific instructions
```

### Key Principle

**Use primitives for everything** - Any workflow, orchestration, or automation task should compose primitives rather than manual implementation.

---

## 🔧 Tool-Specific Configuration Files

| Tool | Instructions | Rules |
|------|-------------|-------|
| **GitHub Copilot** | `.github/copilot-instructions.md` | `.github/instructions/*.instructions.md` |
| **Cline** | `.cline/instructions.md` | `.cline/rules/*.instructions.md` |
| **Cursor** | `.cursor/instructions.md` | `.cursor/rules/*.instructions.md` |
| **Augment** | `.augment/instructions.md` | `.augment/rules/*.instructions.md` |
| **Claude** | `CLAUDE.md` | (uses AGENTS.md + CLAUDE.md) |

---

## 📋 Universal Behaviors

### Code Quality Standards

1. **Type Safety**: Full type annotations using Python 3.11+ style (`T | None`, not `Optional[T]`)
2. **Testing**: Use `MockPrimitive` for isolated tests, `@pytest.mark.asyncio` for async
3. **Documentation**: Docstrings with examples for all public APIs
4. **Imports**: Use `uv` package manager, never `pip` directly

### Workflow Primitive Pattern

All workflows implement:
```python
from tta_dev_primitives.core.base import WorkflowPrimitive, WorkflowContext

class MyPrimitive(WorkflowPrimitive[InputType, OutputType]):
    async def execute(self, input_data: InputType, context: WorkflowContext) -> OutputType:
        # Implementation
        pass
```

Composition operators:
- `>>` - Sequential execution (output flows to next)
- `|` - Parallel execution (all receive same input)

### Anti-Patterns to Avoid

| ❌ Don't | ✅ Do |
|---------|-------|
| Manual async orchestration | Use `SequentialPrimitive` / `ParallelPrimitive` |
| Try/except with retry logic | Use `RetryPrimitive` |
| `asyncio.wait_for()` for timeouts | Use `TimeoutPrimitive` |
| Manual caching dictionaries | Use `CachePrimitive` |
| Global variables for state | Use `WorkflowContext` |
| `pip install` | `uv pip install` or `uv sync` |

### Context Management

**Never use global state.** Pass data through `WorkflowContext`:

```python
context = WorkflowContext(
    workflow_id="unique-id",
    session_id="session-123",
    metadata={"tier": "premium", "user_id": "alice"},
    state={}  # Mutable state for workflow
)
```

---

## 🧪 Testing Guidelines

### Test Structure (AAA Pattern)

```python
@pytest.mark.asyncio
async def test_workflow_behavior():
    # Arrange
    mock = MockPrimitive("step", return_value={"result": "success"})
    context = WorkflowContext(workflow_id="test")

    # Act
    result = await mock.execute({"input": "data"}, context)

    # Assert
    assert result == {"result": "success"}
    assert mock.call_count == 1
```

### Running Tests

```bash
# Run all tests
uv run pytest -v

# Run with coverage
uv run pytest --cov=packages --cov-report=html

# Run specific package tests
cd packages/tta-dev-primitives && uv run pytest -v
```

---

## 📊 Observability Integration

All primitives support observability through OpenTelemetry:

```python
from tta_dev_primitives.apm import setup_apm
from tta_dev_primitives.apm.instrumented import APMWorkflowPrimitive

# Initialize APM
setup_apm(
    service_name="my-service",
    enable_prometheus=True,
    prometheus_port=9464
)

# Use instrumented primitives
class MyPrimitive(APMWorkflowPrimitive):
    async def _execute_impl(self, data, context):
        # Automatically traced and metriced
        return result
```

---

## 🔗 Integration with External Repos

TTA.dev primitives can be integrated into other repositories:

### Option 1: Git Submodule
```bash
git submodule add https://github.com/theinterneti/TTA.dev packages/tta-dev
```

### Option 2: Direct Install
```bash
uv pip install git+https://github.com/theinterneti/TTA.dev#subdirectory=packages/tta-dev-primitives
```

### Option 3: Copy Agent Context
```bash
# Copy agent configuration templates
cp -r TTA.dev/packages/universal-agent-context/.github/ .
cp TTA.dev/packages/universal-agent-context/AGENTS.md .
```

### Safe Integration Pattern

When integrating with repositories like `theinterneti/TTA`:

1. **Keep packages loosely coupled** - No hard dependencies between repos
2. **Use primitives interface** - Wrap external code in primitives
3. **Test at boundaries** - Integration tests for cross-repo interfaces
4. **Observe everything** - Use observability integration to track cross-repo calls

---

## 🚀 Quick Commands

```bash
# Sync dependencies
uv sync --all-extras

# Quality checks
uv run ruff format .
uv run ruff check . --fix
uvx pyright packages/

# Run demos
cd packages/tta-dev-primitives && uv run python examples/quick_wins_demo.py
cd packages/tta-dev-primitives && uv run python examples/apm_example.py
```

---

## 📚 Documentation Links

- [Package README](packages/tta-dev-primitives/README.md)
- [Architecture Overview](docs/architecture/Overview.md)
- [Coding Standards](docs/development/CodingStandards.md)
- [Testing Guide](docs/development/Testing_Guide.md)

---

## Agent-Specific Notes

### For Claude (Cline, Augment with Claude, GitHub Copilot with Claude)
See [CLAUDE.md](CLAUDE.md) for Claude-specific capabilities like extended context, artifacts, and structured output.

### For Copilot
Path-specific instructions in `.github/instructions/` are automatically loaded based on file patterns.

### For Cursor
Global instructions in `.cursor/instructions.md`, rules in `.cursor/rules/`.

### For Augment
Identity system and workflows in `.augment/`, with modular instructions and memory system.
