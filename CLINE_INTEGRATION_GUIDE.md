 # TTA.dev Cline Integration Guide

**Comprehensive guide for using Cline with TTA.dev**

---

## Overview

TTA.dev is optimized for AI coding agent integration, including Cline. This guide covers:

1. **Cline Rules** (`.clinerules`) - Project-specific instructions
2. **VS Code Integration** - Settings and tasks
3. **TTA.dev Primitives as Tools** - Composable workflow patterns
4. **Development Workflow** - Best practices with Cline

---

## 🔧 Cline Rules Configuration

TTA.dev includes a comprehensive `.clinerules` file that provides Cline with project-specific instructions.

### Key Rules

**Package Manager:**
```bash
# ✅ ALWAYS use uv
uv add package-name
uv run pytest -v
uv sync --all-extras

# ❌ NEVER use pip or poetry
pip install package-name  # WRONG
```

**Python Type Hints (3.11+):**
```python
# ✅ CORRECT - Modern syntax
def process(data: str | None) -> dict[str, Any]:
    ...

# ❌ WRONG - Legacy syntax
from typing import Optional, Dict
def process(data: Optional[str]) -> Dict[str, Any]:
    ...
```

**Primitive Usage:**
```python
# ✅ CORRECT - Use primitives for workflows
from tta_dev_primitives import SequentialPrimitive, RetryPrimitive

workflow = step1 >> step2 >> step3
retry_workflow = RetryPrimitive(workflow, max_retries=3)

# ❌ WRONG - Manual orchestration
async def workflow():
    for i in range(3):
        try:
            result = await step1()
            result = await step2(result)
            return await step3(result)
        except Exception:
            pass
```

---

## 📁 Repository Structure

```text
TTA.dev/
├── platform/                 # Production packages
│   ├── primitives/          # ✅ Core workflow primitives
│   ├── observability/       # ✅ OpenTelemetry integration
│   ├── agent-context/       # ✅ Agent context management
│   ├── agent-coordination/  # Multi-agent orchestration
│   ├── integrations/        # Pre-built integrations
│   ├── documentation/       # Docs automation
│   └── kb-automation/       # Knowledge base tools
│
├── apps/                    # Applications
│   └── observability-ui/    # VS Code observability dashboard
│
├── .clinerules              # Cline project rules
├── .augment/                # Augment Code rules
├── .github/
│   ├── copilot-instructions.md    # GitHub Copilot rules
│   └── instructions/              # Path-based instructions
│
├── docs/                    # Documentation
├── logseq/                  # Knowledge base & TODOs
└── scripts/                 # Automation scripts
```

---

## 🔀 TTA.dev Primitives

### Core Primitives

**Composition Operators:**
```python
# Sequential (>>): Output becomes input to next
workflow = step1 >> step2 >> step3

# Parallel (|): Same input to all, returns list
workflow = branch1 | branch2 | branch3

# Mixed patterns
workflow = (
    input_processor >>
    (fast_path | slow_path | cached_path) >>
    aggregator
)
```

### Recovery Primitives

| Primitive | Purpose | Example |
|-----------|---------|---------|
| `RetryPrimitive` | Automatic retry with backoff | `RetryPrimitive(api_call, max_retries=3)` |
| `FallbackPrimitive` | Graceful degradation | `FallbackPrimitive(primary, [backup1, backup2])` |
| `TimeoutPrimitive` | Circuit breaker | `TimeoutPrimitive(slow_call, timeout=30.0)` |
| `CompensationPrimitive` | Saga/rollback pattern | `CompensationPrimitive(forward, compensation)` |

### Performance Primitives

```python
from tta_dev_primitives.performance import CachePrimitive

# Cache expensive operations
cached_llm = CachePrimitive(
    primitive=expensive_llm_call,
    ttl_seconds=3600,  # 1 hour
    max_size=1000      # LRU eviction
)
```

### Observability

All primitives include built-in observability:
- Structured logging with correlation IDs
- OpenTelemetry tracing
- Prometheus metrics
- Context propagation

```python
from tta_dev_primitives import WorkflowContext

context = WorkflowContext(
    workflow_id="my-workflow",
    correlation_id="req-12345",
    data={"user_id": "user-789"}
)

result = await workflow.execute(input_data, context)
```

---

## 🧪 Testing with Cline

### MockPrimitive for Testing

```python
from tta_dev_primitives.testing import MockPrimitive
import pytest

@pytest.mark.asyncio
async def test_workflow():
    # Arrange
    mock_llm = MockPrimitive(return_value={"output": "test"})
    workflow = step1 >> mock_llm >> step3
    context = WorkflowContext(workflow_id="test")

    # Act
    result = await workflow.execute(input_data, context)

    # Assert
    assert mock_llm.call_count == 1
```

### Running Tests

```bash
# All tests
uv run pytest -v

# Specific package
uv run pytest platform/primitives/tests/ -v

# With coverage
uv run pytest --cov=platform --cov-report=html
```

---

## 📊 Quality Checks

Before committing, run quality checks:

```bash
# Format code
uv run ruff format .

# Lint code
uv run ruff check . --fix

# Type check
uvx pyright platform/ apps/

# Run tests
uv run pytest -v

# All at once
uv run ruff format . && uv run ruff check . --fix && uvx pyright platform/ apps/ && uv run pytest -v
```

---

## 📋 TODO Management

TTA.dev uses Logseq for TODO management. Add TODOs to daily journals:

**Location:** `logseq/journals/YYYY_MM_DD.md`

**Format:**
```markdown
- TODO Implement CachePrimitive metrics #dev-todo
  type:: implementation
  priority:: high
  package:: tta-dev-primitives
  related:: [[TTA Primitives/CachePrimitive]]
```

**Tags:**
- `#dev-todo` - Development work
- `#learning-todo` - User education
- `#ops-todo` - Infrastructure

---

## 🔗 Related Documentation

- **Agent Instructions:** [`AGENTS.md`](AGENTS.md) - Main agent hub
- **Getting Started:** [`GETTING_STARTED.md`](GETTING_STARTED.md) - Quick start
- **Primitives Catalog:** [`PRIMITIVES_CATALOG.md`](PRIMITIVES_CATALOG.md) - Full reference
- **Copilot Instructions:** [`.github/copilot-instructions.md`](.github/copilot-instructions.md)
- **Cline Rules:** [`.clinerules`](.clinerules)

---

## 🚀 Quick Commands for Cline

```bash
# Install dependencies
uv sync --all-extras

# Run observability demo
uv run python platform/primitives/examples/observability_demo.py

# Run specific test
uv run pytest platform/primitives/tests/test_cache.py -v

# Format and lint
uv run ruff format . && uv run ruff check . --fix
```

---

**Last Updated:** December 2025
**Maintained by:** TTA.dev Team
