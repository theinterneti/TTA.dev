# Testing Architecture

Deep reference for TTA.dev testing standards, patterns, and infrastructure.

## Framework

- **Test runner:** pytest with pytest-asyncio
- **Parallel execution:** pytest-xdist (`-n auto --dist=loadfile`)
- **Horizontal scaling:** pytest-split (`--splits/--group`) across CI matrix runners
- **Coverage:** Codecov enforces project 80% (±2%), patch 75% (±5%); new code requires 100%

## Test Structure (AAA Pattern)

All tests follow Arrange-Act-Assert:

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

## MockPrimitive API

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
@pytest.mark.quarantine    # Auto-skipped unless explicitly selected
@pytest.mark.flaky         # Known flaky (registered but not auto-skipped)
```

## Test Commands

```bash
# Fast tests (safe for local dev)
uv run pytest -m "not integration and not slow and not external"

# All tests with coverage
uv run pytest --cov=src --cov-report=html

# Integration tests (requires resources)
RUN_INTEGRATION=true uv run pytest -m integration

# Quarantined tests only
uv run pytest -m quarantine
```

## Configuration

- `pytest.ini` at repo root sets `testpaths=tests` (overrides pyproject.toml)
- `conftest.py` auto-skips `@pytest.mark.quarantine` tests unless explicitly selected
- `TTA_LIFECYCLE_SKIP_TEST_SUBPROCESS=1` prevents spawning pytest within pytest during lifecycle checks

## CI Pipeline

- CI uses pytest-xdist for vertical scaling and pytest-split for horizontal scaling
- GitHub Actions use `.github/actions/setup-tta-env` composite action for environment setup
- Matrix runners split tests via `strategy.job-total`

## Quality Checklist

- [ ] Uses `@pytest.mark.asyncio` for async tests
- [ ] Uses `MockPrimitive` for mocking (never real implementations)
- [ ] Tests success, failure, and edge cases
- [ ] No external dependencies (databases, APIs, filesystem)
- [ ] Fast execution (< 1s per test)
- [ ] 100% coverage for new code
