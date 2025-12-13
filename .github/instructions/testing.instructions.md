---
applyTo: "**/tests/**/*.py,**/*_test.py,**/test_*.py"
description: "Test files - comprehensive testing with mocks and async support"
---

# Testing Guidelines

## Core Principles

- Use `MockPrimitive` instead of real implementations
- Use `@pytest.mark.asyncio` for async tests
- Follow AAA pattern: Arrange, Act, Assert
- No external dependencies (databases, APIs, filesystem)

## Basic Test Structure

```python
import pytest
from tta_dev_primitives.core.base import WorkflowContext
from tta_dev_primitives.testing import MockPrimitive

@pytest.mark.asyncio
async def test_workflow_success():
    """Test successful workflow execution."""
    # Arrange
    mock1 = MockPrimitive("step1", return_value="result1")
    mock2 = MockPrimitive("step2", return_value="result2")
    workflow = mock1 >> mock2
    context = WorkflowContext(workflow_id="test")

    # Act
    result = await workflow.execute("input", context)

    # Assert
    assert mock1.call_count == 1
    assert result == "result2"
```

## MockPrimitive Usage

```python
# Return static value
mock = MockPrimitive("name", return_value={"success": True})

# Raise exception
mock = MockPrimitive("name", side_effect=ValueError("Error"))

# Custom behavior
async def custom_logic(data, ctx):
    return {"processed": data}
mock = MockPrimitive("name", side_effect=custom_logic)

# Verify calls
assert mock.call_count == 3
assert mock.last_input == expected_input
```

## Test Markers

```python
@pytest.mark.asyncio       # Required for async tests
@pytest.mark.integration   # Heavy tests (opt-in only)
@pytest.mark.timeout(300)  # Override default 60s timeout
```

## Commands

```bash
# Fast tests (safe for local dev)
uv run pytest -m "not integration"

# All tests with coverage
uv run pytest --cov=src --cov-report=html

# Integration tests (requires resources)
RUN_INTEGRATION=true uv run pytest -m integration
```

## Coverage

- Target: 100% for new code
- Minimum: 80% overall

## Quality Checklist

- [ ] Uses `@pytest.mark.asyncio` for async tests
- [ ] Uses `MockPrimitive` for mocking
- [ ] Tests success, failure, and edge cases
- [ ] No external dependencies
- [ ] Fast execution (< 1s per test)


---
**Logseq:** [[TTA.dev/.github/Instructions/Testing.instructions]]
