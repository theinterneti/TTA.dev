---
title: "Python Testing Guide"
applyTo: "**/*.py"
tags: ["python", "testing", "pytest"]
version: "1.0.0"
---

# Python Testing (pytest)

This document contains Python-specific testing guidance for projects in this repository. Place language-agnostic testing philosophy in `packages/universal-agent-context`.

## Toolchain

- Test runner: `pytest`
- Async support: `pytest-asyncio`
- Coverage: `pytest-cov`

## Patterns

- AAA: Arrange / Act / Assert
- Use `pytest` fixtures for reusable test setup
- Prefer mocking external systems with `unittest.mock` or pytest fixtures
- Keep unit tests fast and focused; integration tests in `tests/integration/`

## Markers

Use markers for optional external services and long-running tests:

```python
@pytest.mark.redis
@pytest.mark.neo4j
@pytest.mark.integration
@pytest.mark.slow
```

## Common commands (using `uv`/`uvx` from the Python pathway)

Run tests for the package or a given target:

```bash
# Run tests (verbose)
uvx pytest tests/ -v

# Run a single file
uvx pytest tests/test_orchestrator.py -q

# Coverage
uvx pytest --cov=src --cov-report=term-missing
```

## Async tests

Use `pytest-asyncio` and `@pytest.mark.asyncio` for coroutine-based tests.

```python
@pytest.mark.asyncio
async def test_async_behavior():
    result = await my_async_func()
    assert result is True
```

## Fixtures

See `packages/python-pathway/fixtures/pytest-fixtures.py` for recommended uv-aware fixtures and examples.

## Notes

Keep language-agnostic testing philosophy in `packages/universal-agent-context/` and link to this file for implementation details.
