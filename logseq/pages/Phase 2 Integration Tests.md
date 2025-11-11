# Phase 2 Integration Tests

**Integration testing strategy for TTA.dev multi-component workflows**

---

## Overview

Phase 2 integration tests validate interactions between TTA.dev components in realistic scenarios. Unlike unit tests that test primitives in isolation, integration tests verify that components work together correctly.

**Phase:** Phase 2 (Component Integration)
**Category:** Testing
**Related:** [[TTA.dev/Testing Strategy]], [[MockPrimitive]]

---

## Test Scope

### What Integration Tests Cover

1. **Inter-Primitive Communication**
   - Data flow between [[WorkflowPrimitive]] instances
   - [[WorkflowContext]] propagation
   - Error handling across primitive boundaries

2. **Package Integration**
   - [[tta-dev-primitives]] + [[tta-observability-integration]]
   - [[tta-dev-primitives]] + [[universal-agent-context]]
   - Multi-package workflows

3. **External Service Integration**
   - Database connections (with test containers)
   - API calls (with mock servers)
   - Message queues (with test instances)

---

## Test Structure

### Directory Layout

```
tests/
├── unit/                          # Unit tests (fast, no I/O)
│   └── test_primitives.py
├── integration/                   # Integration tests (Phase 2)
│   ├── test_workflow_integration.py
│   ├── test_observability_integration.py
│   ├── test_cache_integration.py
│   └── test_context_propagation.py
└── e2e/                          # End-to-end tests (full stack)
    └── test_complete_workflows.py
```

### Test Markers

```python
import pytest

# Mark as integration test
@pytest.mark.integration
async def test_cache_with_retry():
    """Test CachePrimitive + RetryPrimitive integration."""
    pass

# Mark as slow (requires external services)
@pytest.mark.slow
async def test_database_workflow():
    """Test with real database."""
    pass

# Mark as safe (can run in CI without side effects)
@pytest.mark.safe
async def test_mock_external_apis():
    """Test with mocked external services."""
    pass
```

---

## Example Integration Tests

### Test 1: Cache + Retry Integration

```python
import pytest
from tta_dev_primitives import WorkflowContext
from tta_dev_primitives.performance import CachePrimitive
from tta_dev_primitives.recovery import RetryPrimitive

@pytest.mark.integration
@pytest.mark.asyncio
async def test_cache_retry_integration():
    """Test that cache works correctly with retry."""

    call_count = 0

    async def flaky_operation(data: dict, context: WorkflowContext) -> dict:
        nonlocal call_count
        call_count += 1

        # Fail first 2 times, succeed on 3rd
        if call_count < 3:
            raise ValueError("Temporary failure")

        return {"result": f"Success after {call_count} attempts"}

    # Create workflow: Cache wrapping Retry
    workflow = CachePrimitive(
        primitive=RetryPrimitive(
            primitive=flaky_operation,
            max_retries=5,
            backoff_strategy="constant"
        ),
        ttl_seconds=60
    )

    context = WorkflowContext(workflow_id="test-cache-retry")

    # First execution: retries until success
    result1 = await workflow.execute({"input": "test"}, context)
    assert result1["result"] == "Success after 3 attempts"
    assert call_count == 3

    # Second execution: cache hit (no additional calls)
    result2 = await workflow.execute({"input": "test"}, context)
    assert result2["result"] == "Success after 3 attempts"
    assert call_count == 3  # No additional calls

    # Different input: cache miss, new retry cycle
    call_count = 0
    result3 = await workflow.execute({"input": "different"}, context)
    assert call_count == 3  # Retry again for new input
```

### Test 2: Context Propagation

```python
import pytest
from tta_dev_primitives import WorkflowContext, SequentialPrimitive

@pytest.mark.integration
@pytest.mark.asyncio
async def test_context_propagation():
    """Test that context propagates through workflow."""

    captured_contexts = []

    async def capture_context_1(data: dict, context: WorkflowContext) -> dict:
        captured_contexts.append(("step1", context.correlation_id, context.workflow_id))
        return data

    async def capture_context_2(data: dict, context: WorkflowContext) -> dict:
        captured_contexts.append(("step2", context.correlation_id, context.workflow_id))
        return data

    async def capture_context_3(data: dict, context: WorkflowContext) -> dict:
        captured_contexts.append(("step3", context.correlation_id, context.workflow_id))
        return data

    # Create sequential workflow
    workflow = SequentialPrimitive([
        capture_context_1,
        capture_context_2,
        capture_context_3
    ])

    # Execute with specific context
    context = WorkflowContext(
        workflow_id="test-workflow",
        correlation_id="test-correlation-123"
    )

    await workflow.execute({"input": "test"}, context)

    # Verify context propagated to all steps
    assert len(captured_contexts) == 3

    for step_name, corr_id, workflow_id in captured_contexts:
        assert corr_id == "test-correlation-123"
        assert workflow_id == "test-workflow"
```

### Test 3: Observability Integration

```python
import pytest
from tta_dev_primitives import WorkflowContext
from tta_observability_integration import initialize_observability
from tta_observability_integration.primitives import RouterPrimitive

@pytest.mark.integration
@pytest.mark.asyncio
async def test_observability_metrics():
    """Test that observability integration records metrics."""

    # Initialize observability (test mode)
    initialize_observability(
        service_name="test-service",
        enable_prometheus=True,
        enable_tracing=False  # Disable for test speed
    )

    async def fast_operation(data: dict, context: WorkflowContext) -> dict:
        return {"result": "fast", "cost": 0.001}

    async def quality_operation(data: dict, context: WorkflowContext) -> dict:
        return {"result": "quality", "cost": 0.01}

    # Create router with observability
    router = RouterPrimitive(
        routes={
            "fast": fast_operation,
            "quality": quality_operation
        },
        router_fn=lambda d, c: d.get("tier", "fast")
    )

    context = WorkflowContext(workflow_id="test-observability")

    # Execute with different tiers
    result_fast = await router.execute({"tier": "fast"}, context)
    result_quality = await router.execute({"tier": "quality"}, context)

    # Verify results
    assert result_fast["result"] == "fast"
    assert result_quality["result"] == "quality"

    # Note: Full metric verification requires Prometheus client
    # In production, query Prometheus to verify metrics recorded
```

---

## Running Integration Tests

### Command Line

```bash
# Run all integration tests
uv run pytest tests/integration/ -v

# Run only safe integration tests (CI-friendly)
uv run pytest -m "integration and safe" -v

# Run with coverage
uv run pytest tests/integration/ --cov=packages --cov-report=html

# Run specific test file
uv run pytest tests/integration/test_workflow_integration.py -v

# Run with parallel execution (faster)
uv run pytest tests/integration/ -n auto
```

### Environment Variables

```bash
# Enable integration tests (safeguard)
export RUN_INTEGRATION=true

# Configure test database
export TEST_DATABASE_URL=postgresql://localhost/test_db

# Use test API keys (lower rate limits)
export OPENAI_API_KEY=${OPENAI_TEST_KEY}

# Run tests
uv run pytest tests/integration/ -v
```

---

## Test Fixtures

### Shared Fixtures

```python
# tests/integration/conftest.py
import pytest
from tta_dev_primitives import WorkflowContext

@pytest.fixture
def test_context():
    """Provide test context for integration tests."""
    return WorkflowContext(
        workflow_id="test-integration",
        correlation_id="test-correlation"
    )

@pytest.fixture
async def test_cache():
    """Provide test cache instance."""
    from tta_dev_primitives.performance import CachePrimitive

    cache = CachePrimitive(
        primitive=lambda d, c: d,  # Pass-through
        ttl_seconds=60,
        max_size=100
    )

    yield cache

    # Cleanup
    cache.clear()

@pytest.fixture
async def mock_llm():
    """Provide mock LLM for testing."""
    from tta_dev_primitives.testing import MockPrimitive

    return MockPrimitive(
        return_value={"response": "Test LLM response"}
    )
```

---

## CI/CD Integration

### GitHub Actions Workflow

```yaml
# .github/workflows/integration-tests.yml
name: Integration Tests

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  integration-tests:
    runs-on: ubuntu-latest

    services:
      redis:
        image: redis:7-alpine
        ports:
          - 6379:6379

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install uv
        run: pip install uv

      - name: Install dependencies
        run: uv sync --all-extras

      - name: Run safe integration tests
        env:
          RUN_INTEGRATION: true
        run: uv run pytest tests/integration/ -m "integration and safe" -v

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          files: ./coverage.xml
```

---

## Best Practices

### 1. Isolation

- Each test should be independent
- Use fixtures for setup/teardown
- Don't rely on test execution order

### 2. Realistic Scenarios

- Test real workflow patterns
- Use realistic data sizes
- Include error scenarios

### 3. External Services

- Use test containers when possible (Docker)
- Mock external APIs with [[MockPrimitive]]
- Have fallback mocks for CI environments

### 4. Performance

- Integration tests are slower than unit tests
- Use markers to separate fast/slow tests
- Run slow tests less frequently (nightly)

### 5. Cleanup

- Always clean up resources (connections, caches)
- Use fixtures with `yield` for automatic cleanup
- Handle cleanup even when tests fail

---

## Related Documentation

- [[TTA.dev/Testing Strategy]] - Overall testing approach
- [[MockPrimitive]] - Mocking framework
- [[WorkflowContext]] - Context propagation
- [[GitHub Actions]] - CI/CD setup

---

## Related Primitives

- [[SequentialPrimitive]] - Workflow composition
- [[ParallelPrimitive]] - Concurrent execution
- [[CachePrimitive]] - Caching (common in integration tests)
- [[RetryPrimitive]] - Retry logic (common in integration tests)

---

**Phase:** Phase 2 (Component Integration)
**Status:** Active
**Category:** Testing

- [[Project Hub]]