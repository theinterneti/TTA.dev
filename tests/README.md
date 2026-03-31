# TTA.dev Test Suite

## Quick Reference

```bash
make test          # Full suite (fast, no coverage)
make watch         # Continuous testing on file change (fastest feedback)
make watch-cov     # Continuous testing with coverage report
uv run pytest -m unit             # Unit tests only (~10s)
uv run pytest -m integration      # Integration tests only
uv run pytest tests/unit/         # By directory
uv run pytest -k "circuit_breaker" # By name pattern
```

## Directory Structure

```
tests/
├── unit/          # Fast, isolated — no external services required
│   ├── test_cli_*.py          — CLI command behaviour
│   ├── test_control_plane_*.py — L0 task/run/lease state machine
│   ├── test_mcp_*.py          — MCP tool definitions
│   └── test_*.py              — Other isolated units
├── agents/        # Agent role & routing logic
├── integration/   # Tests requiring real files or subprocess
├── workflows/     # Workflow composition & orchestration
├── primitives/    # Per-primitive test suites
│   ├── recovery/     (circuit_breaker, fallback, retry, timeout)
│   ├── performance/  (cache)
│   ├── safety/       (safety_gate)
│   ├── streaming/    (streaming)
│   ├── llm/          (universal_llm)
│   ├── memory/       (agent_memory)
│   ├── coordination/ (redis_coordinator)
│   ├── code_graph/   (FalkorDB — skipped if not installed)
│   └── integrations/ (langgraph)
├── scripts/       # Tests for automation scripts in scripts/
├── observability/ # Observability pipeline tests
├── e2e/           # Playwright end-to-end (requires `playwright install`)
├── benchmarks/    # Performance benchmarks (requires pytest-benchmark)
├── fakes.py       # Shared test doubles (FakeRepository, FakeUnitOfWork)
└── conftest.py    # Pytest configuration, optional-dep excludes
```

## Markers

| Marker | Use | How to run |
|--------|-----|-----------|
| `unit` | Fast isolated tests | `-m unit` |
| `integration` | Needs real files/subprocess | `-m integration` |
| `slow` | Takes > 5 seconds | `-m slow` |
| `external` | Calls real external APIs | `-m external` |
| `workflow_proof` | L0 end-to-end proof tests | `-m workflow_proof` |

Apply markers with `@pytest.mark.<marker>` on the test function or class.

## Writing Tests

### AAA Pattern (Required)
```python
async def test_retry_succeeds_on_third_attempt():
    """Verify RetryPrimitive retries up to max_retries and returns on success."""
    # Arrange
    call_count = 0
    async def flaky(data, ctx):
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise ValueError("transient")
        return "ok"

    workflow = RetryPrimitive(LambdaPrimitive(flaky), strategy=RetryStrategy(max_retries=3))
    ctx = WorkflowContext(workflow_id="test")

    # Act
    result = await workflow.execute({}, ctx)

    # Assert
    assert result == "ok"
    assert call_count == 3
```

### Mocking (use MockPrimitive, not unittest.mock)
```python
from ttadev.primitives.testing.mocks import MockPrimitive

mock = MockPrimitive("step", return_value={"processed": True})
result = await mock.execute(data, ctx)
assert mock.call_count == 1
```

### Async tests
All async tests work without `@pytest.mark.asyncio` (asyncio_mode = auto).

### Skipping optional deps
```python
falkordb = pytest.importorskip("falkordb")  # Skip whole module if missing
```

## Adding New Tests

1. **Where?** Put in the directory matching what you're testing:
   - `ttadev/primitives/foo.py` → `tests/primitives/test_foo.py`
   - `ttadev/cli/bar.py` → `tests/unit/test_cli_bar.py`
   - `ttadev/agents/baz.py` → `tests/agents/test_baz.py`

2. **What markers?** Add `@pytest.mark.unit` for fast isolated tests; `@pytest.mark.integration` if it touches filesystem or subprocess.

3. **Coverage?** Every new module must hit 100% line coverage.

## Excluded from Default Run

| File(s) | Reason | How to run |
|---------|--------|-----------|
| `e2e/test_*.py` | Requires Playwright + live server | `playwright install && uv run pytest tests/e2e/` |
| `test_observability_ui.py` | Requires live server | (same as above) |
| `benchmarks/test_primitive_performance.py` | Requires pytest-benchmark | `uv add --dev pytest-benchmark && uv run pytest tests/benchmarks/` |

## Exemplary Test Files

Study these for patterns to follow:

- `tests/primitives/recovery/test_circuit_breaker_primitive.py` — 41 tests, thorough edge cases, good class organization
- `tests/workflows/test_quality_gate.py` — class-per-concern, high assertion density
- `tests/unit/test_mcp_control_plane_tools.py` — comprehensive tool coverage, good async patterns
