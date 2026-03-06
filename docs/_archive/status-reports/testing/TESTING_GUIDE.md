# TTA.dev Testing Guide

**Safe, efficient testing methodology for local development and CI**

## Overview

This guide explains TTA.dev's testing approach after refactoring to avoid resource exhaustion and WSL crashes.

## Testing Philosophy

1. **Unit tests are fast and safe** - Run locally by default
2. **Integration tests are heavy** - Run in CI or explicitly with safety checks
3. **Documentation is validated** - Lightweight static checks
4. **Clear separation** - Markers distinguish test types

## Test Categories

### Unit Tests
- **Marker**: `@pytest.mark.unit`
- **Scope**: Single function/class behavior
- **Speed**: < 1 second each
- **Resources**: Minimal (no network, no servers)
- **Run**: Locally by default

### Integration Tests
- **Marker**: `@pytest.mark.integration`
- **Scope**: Cross-package interactions, MCP servers, observability
- **Speed**: Seconds to minutes
- **Resources**: May start services, open ports, spawn processes
- **Run**: CI or explicit opt-in only

### Slow Tests
- **Marker**: `@pytest.mark.slow`
- **Scope**: Performance tests, long-running operations
- **Speed**: > 30 seconds
- **Resources**: May consume significant CPU/memory
- **Run**: CI or scheduled runs

### External Tests
- **Marker**: `@pytest.mark.external`
- **Scope**: Tests requiring external services (APIs, databases)
- **Speed**: Variable
- **Resources**: Network access required
- **Run**: With credentials in CI

## Running Tests Locally

### Fast Tests (Recommended Default)

Run unit tests only - safe for WSL and resource-constrained environments:

```bash
# Using wrapper script (recommended)
./scripts/test_fast.sh

# Direct pytest
uv run pytest -q -m "not integration and not slow and not external"

# VS Code task
# Ctrl+Shift+P → Tasks: Run Task → "🧪 Run Fast Tests (Unit Only)"
```

### Integration Tests (Use with Caution)

Integration tests can crash WSL due to resource consumption. Only run when necessary:

```bash
# Requires explicit opt-in
RUN_INTEGRATION=true ./scripts/test_integration.sh

# VS Code task
# Ctrl+Shift+P → Tasks: Run Task → "🧪 Run Integration Tests (Safe)"
```

**WARNING**: Integration tests may:
- Start network servers on ports 8001, 8002
- Spawn multiple Python processes
- Consume 1GB+ memory
- Run for several minutes

### All Tests

Run complete test suite (use in CI or powerful machines):

```bash
uv run pytest -v

# VS Code task
# Ctrl+Shift+P → Tasks: Run Task → "🧪 Run All Tests"
```

### Coverage

Generate coverage report (unit tests only to avoid long runs):

```bash
uv run pytest --cov=packages --cov-report=html -m "not integration and not slow"

# VS Code task
# Ctrl+Shift+P → Tasks: Run Task → "🧪 Run Tests with Coverage"
```

## Documentation Testing

Check markdown files for correctness:

```bash
# All static checks (links, code blocks, frontmatter)
python scripts/docs/check_md.py --all

# Just check links
python scripts/docs/check_md.py --links

# VS Code task
# Ctrl+Shift+P → Tasks: Run Task → "📝 Check Markdown Docs"
```

See [scripts/docs/README.md](../scripts/docs/README.md) for details.

## Emergency: Stopping Stale Processes

If tests hang or crash, use the emergency stop script:

```bash
./scripts/emergency_stop.sh
```

This will:
1. Find pytest and server processes
2. Prompt for confirmation
3. Kill processes and free ports

## Writing New Tests

### Unit Test Template

```python
import pytest
from tta_dev_primitives import WorkflowPrimitive, WorkflowContext

@pytest.mark.unit
@pytest.mark.asyncio
async def test_my_primitive():
    """Test MyPrimitive behavior."""
    primitive = MyPrimitive()
    context = WorkflowContext()

    result = await primitive.execute(input_data, context)

    assert result["status"] == "success"
```

### Integration Test Template

```python
import pytest

@pytest.mark.integration
@pytest.mark.asyncio
async def test_mcp_server_integration():
    """Test MCP server lifecycle."""
    # This test may start services
    server = create_test_server()
    await server.start()

    try:
        # Test operations
        response = await server.call_tool("test")
        assert response is not None
    finally:
        await server.stop()
```

### Marking Tests

Always mark tests with appropriate markers:

```python
@pytest.mark.unit          # Fast, pure logic
@pytest.mark.integration   # Heavy, may start services
@pytest.mark.slow          # Takes > 30 seconds
@pytest.mark.external      # Requires network/APIs
```

## CI Configuration

GitHub Actions workflow splits tests for efficiency:

### Job 1: Quick Checks (runs always)
- Ruff format/lint
- Pyright type checking
- Unit tests
- ~5-10 minutes

### Job 2: Documentation (runs always)
- Markdown link checking
- Code block validation
- ~2-5 minutes

### Job 3: Integration (runs on main or manual)
- Integration tests
- Larger runner
- ~15-30 minutes

### Job 4: Coverage (runs on main)
- Coverage report
- Codecov upload
- ~10-15 minutes

See [.github/workflows/tests-split.yml](../../.github/workflows/tests-split.yml) for configuration.

## Configuration

### pytest Configuration

Located in `pyproject.toml`:

```toml
[tool.pytest.ini_options]
pythonpath = ["."]
testpaths = ["platform/primitives/tests"]
asyncio_mode = "auto"
addopts = "-v --strict-markers --timeout=60"
timeout = 60
timeout_method = "thread"
markers = [
    "asyncio: mark test as async",
    "integration: mark test as integration test",
    "unit: mark test as unit test",
    "slow: mark test as slow running",
    "external: mark test as requiring external services",
]
```

### Timeout Protection

All tests have 60-second default timeout via `pytest-timeout`:

```bash
# Override timeout for specific test
uv run pytest --timeout=300 tests/integration/
```

## Best Practices

### DO ✅

- Mark all tests with appropriate markers
- Run fast tests frequently during development
- Use mocks for external services in unit tests
- Add timeouts to integration tests
- Clean up resources (files, processes, ports) in test teardown
- Test one thing per test function

### DON'T ❌

- Run integration tests on WSL without explicit opt-in
- Forget to mark slow or integration tests
- Leave servers running after test completion
- Use network calls in unit tests
- Test multiple concerns in one test
- Commit without running fast tests

## Troubleshooting

### WSL Crashed During Tests

**Cause**: Integration tests consumed too many resources

**Solution**:
1. Run `./scripts/emergency_stop.sh` to kill stale processes
2. Only run `./scripts/test_fast.sh` locally
3. Use CI for integration tests

### Tests Hanging

**Cause**: Test waiting for network or subprocess that never completes

**Solution**:
1. Ctrl+C to interrupt
2. Run `./scripts/emergency_stop.sh`
3. Check test has proper timeout: `@pytest.mark.timeout(30)`

### Import Errors

**Cause**: Dependencies not synced

**Solution**:
```bash
uv sync --all-extras
```

### Ports Already in Use

**Cause**: Previous test didn't clean up server

**Solution**:
```bash
./scripts/emergency_stop.sh
```

Or manually:
```bash
lsof -ti:8001,8002 | xargs kill -9
```

## Performance Tips

### Parallel Execution (Advanced)

For powerful machines, run tests in parallel:

```bash
# Install pytest-xdist
uv add --dev pytest-xdist

# Run with 4 workers
uv run pytest -n 4 -m "unit"
```

**WARNING**: Do NOT use parallel execution on WSL or resource-constrained systems.

### Test Selection

Run specific test files or functions:

```bash
# Single file
uv run pytest platform/primitives/tests/test_sequential.py

# Single test
uv run pytest platform/primitives/tests/test_sequential.py::test_basic_sequence

# By keyword
uv run pytest -k "cache"
```

## Summary

- **Local development**: Use `./scripts/test_fast.sh` (fast, safe)
- **Integration testing**: Use CI or explicit `RUN_INTEGRATION=true`
- **Documentation**: Use `python scripts/docs/check_md.py --all`
- **Emergency**: Use `./scripts/emergency_stop.sh`
- **Always mark tests** with appropriate markers

---

**Questions?** See [AGENTS.md](../AGENTS.md) or open an issue.


---
**Logseq:** [[TTA.dev/Docs/Status-reports/Testing/Testing_guide]]
