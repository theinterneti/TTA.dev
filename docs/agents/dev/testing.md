# Testing Reference

## Framework and infrastructure

| Tool | Purpose |
|---|---|
| `pytest` | Test runner |
| `pytest-asyncio` | Async test support |
| `pytest-xdist` | Parallel execution (`-n auto`) |
| `pytest-cov` | Coverage reporting |
| `MockPrimitive` | Primitive mocking |

Config lives in `pyproject.toml` under `[tool.pytest.ini_options]` — no `pytest.ini`.

## Test structure (mandatory AAA pattern)

```python
import pytest
from ttadev.primitives.core.base import WorkflowContext
from ttadev.primitives.testing.mocks import MockPrimitive

@pytest.mark.asyncio
async def test_workflow_success():
    """Test successful workflow execution."""
    # Arrange
    mock = MockPrimitive("step", return_value={"status": "ok"})
    ctx = WorkflowContext(workflow_id="test-123")

    # Act
    result = await mock.execute({"input": "data"}, ctx)

    # Assert
    assert result == {"status": "ok"}
    assert mock.call_count == 1
```

## MockPrimitive API

```python
# Static return value
mock = MockPrimitive("name", return_value={"ok": True})

# Raise exception
mock = MockPrimitive("name", side_effect=ValueError("boom"))

# Custom async behaviour
async def logic(data, ctx):
    return {"processed": data}
mock = MockPrimitive("name", side_effect=logic)

# Assertions
assert mock.call_count == 3
assert mock.last_input == expected_input
assert mock.last_context.workflow_id == "test-123"
```

## Test markers

```python
@pytest.mark.asyncio        # Required for every async test
@pytest.mark.integration    # Heavy tests requiring real services (opt-in)
@pytest.mark.timeout(300)   # Override default 60 s timeout
```

**Never use `@pytest.mark.integration` for unit tests.** Integration tests are excluded
from the standard CI run and require `RUN_INTEGRATION=true`.

## Coverage requirements

| Scope | Threshold |
|---|---|
| Overall project | 80% (`fail_under = 80` in pyproject.toml) |
| New code (new files / new functions) | 100% |

Coverage is enforced in CI via `--cov-fail-under=80`. PRs that drop coverage below 80% will fail.

## Commands

```bash
make watch          # Continuous TDD loop — fast, fail-fast (use during development)
make watch-cov      # Continuous TDD loop with live coverage (use before committing)
make test           # Full one-shot run with coverage (CI equivalent)

# Integration tests (requires running services)
RUN_INTEGRATION=true uv run pytest -m integration
```

## CI matrix

4 jobs: `ubuntu-latest` + `macos-latest` × `python 3.12` + `python 3.13`.
Windows is excluded (server-side library).
Python 3.11 is excluded (`requires-python = ">=3.12"`).

## Async patterns

- Always use `@pytest.mark.asyncio` — never `asyncio.run()` inside tests.
- Use `pytest-asyncio` in `auto` mode (configured in `pyproject.toml`).
- For primitives with background tasks, ensure cleanup in test teardown.

## What NOT to do

```python
# ❌ External API calls in unit tests
result = await real_api.call(...)

# ❌ Direct instantiation of heavy primitives instead of mocks
router = ModelRouterPrimitive(providers=[...])

# ❌ asyncio.run() in test body
result = asyncio.run(some_coroutine())

# ❌ Manual retry loops — they belong in primitives, not tests
```

## Test file location

| Type | Location |
|---|---|
| Unit tests | `tests/test_<module_name>.py` |
| Integration tests | `tests/integration/test_<name>.py` |
| Test fixtures | `tests/conftest.py` |

See [testing-architecture](../../agent-guides/testing-architecture.md) for the full deep reference.
