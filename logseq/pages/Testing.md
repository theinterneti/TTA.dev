# Testing

**Tag page for testing strategies, tools, and best practices**

---

## Overview

**Testing** in TTA.dev ensures workflows are reliable, correct, and production-ready. The testing approach includes:
- **Unit testing** - Test primitives in isolation
- **Integration testing** - Test workflows end-to-end
- **Mocking** - Use `MockPrimitive` for dependencies
- **100% coverage requirement** - All new code must be tested

**See:** [[TTA.dev/Testing Strategy]], [[TESTING_GUIDE]]

---

## Testing Tools

### MockPrimitive

**Mock primitives for testing workflows**

```python
from tta_dev_primitives.testing import MockPrimitive
import pytest

@pytest.mark.asyncio
async def test_workflow():
    # Mock LLM response
    mock_llm = MockPrimitive(
        return_value={"output": "mocked response"}
    )

    workflow = input_processor >> mock_llm >> output_formatter
    result = await workflow.execute(input_data, context)

    assert mock_llm.call_count == 1
    assert result["formatted_output"] == "mocked response"
```

**Features:**
- Return static values
- Return sequences (side effects)
- Track call count
- Inspect call arguments

**See:** [[TTA Primitives/MockPrimitive]]

---

### Test Fixtures

**Common test setup:**

```python
import pytest
from tta_dev_primitives import WorkflowContext

@pytest.fixture
def test_context():
    """Standard test context."""
    return WorkflowContext(
        correlation_id="test-123",
        workflow_id="test-workflow",
        data={"test": True}
    )

@pytest.fixture
def sample_input():
    """Sample input data."""
    return {"text": "test input", "metadata": {}}
```

---

### Pytest Configuration

**TTA.dev uses pytest with asyncio:**

```python
# pyproject.toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
markers = [
    "unit: Unit tests",
    "integration: Integration tests",
    "slow: Slow tests",
]
```

**Run tests:**
```bash
# All tests
uv run pytest -v

# Unit tests only
uv run pytest -m "unit" -v

# Integration tests
uv run pytest -m "integration" -v

# With coverage
uv run pytest --cov=packages --cov-report=html
```

**See:** [[TESTING_GUIDE]]

---

## Pages Tagged with #Testing

{{query (page-tags [[Testing]])}}

---

## Testing Patterns

### Unit Testing Primitives

**Test primitives in isolation:**

```python
@pytest.mark.asyncio
async def test_cache_primitive_hit():
    """Test cache hit scenario."""
    cache = CachePrimitive(
        primitive=MockPrimitive(return_value={"result": "computed"}),
        ttl_seconds=60
    )

    # First call - cache miss
    result1 = await cache.execute({"key": "test"}, context)

    # Second call - cache hit (mock not called again)
    result2 = await cache.execute({"key": "test"}, context)

    assert result1 == result2
    assert cache.cache_hits == 1
```

---

### Testing Sequential Workflows

**Test step-by-step execution:**

```python
@pytest.mark.asyncio
async def test_sequential_workflow():
    mock_step1 = MockPrimitive(return_value={"step1": "done"})
    mock_step2 = MockPrimitive(return_value={"step2": "done"})
    mock_step3 = MockPrimitive(return_value={"step3": "done"})

    workflow = mock_step1 >> mock_step2 >> mock_step3
    result = await workflow.execute({}, context)

    # Verify all steps called in order
    assert mock_step1.call_count == 1
    assert mock_step2.call_count == 1
    assert mock_step3.call_count == 1
    assert result["step3"] == "done"
```

---

### Testing Parallel Workflows

**Test concurrent execution:**

```python
@pytest.mark.asyncio
async def test_parallel_workflow():
    mock_branch1 = MockPrimitive(return_value={"branch1": "result"})
    mock_branch2 = MockPrimitive(return_value={"branch2": "result"})
    mock_branch3 = MockPrimitive(return_value={"branch3": "result"})

    workflow = mock_branch1 | mock_branch2 | mock_branch3
    results = await workflow.execute({}, context)

    # Verify all branches called
    assert len(results) == 3
    assert mock_branch1.call_count == 1
    assert mock_branch2.call_count == 1
    assert mock_branch3.call_count == 1
```

---

### Testing Error Handling

**Test recovery primitives:**

```python
@pytest.mark.asyncio
async def test_retry_primitive_success_after_failures():
    """Test retry succeeds after transient failures."""
    mock = MockPrimitive(
        side_effects=[
            Exception("Transient error 1"),
            Exception("Transient error 2"),
            {"result": "success"}  # Third attempt succeeds
        ]
    )

    workflow = RetryPrimitive(mock, max_retries=3)
    result = await workflow.execute({}, context)

    assert result["result"] == "success"
    assert mock.call_count == 3  # Failed twice, succeeded on third
```

```python
@pytest.mark.asyncio
async def test_fallback_cascade():
    """Test fallback activates when primary fails."""
    primary = MockPrimitive(side_effects=[Exception("Primary failed")])
    fallback = MockPrimitive(return_value={"source": "fallback"})

    workflow = FallbackPrimitive(primary=primary, fallbacks=[fallback])
    result = await workflow.execute({}, context)

    assert result["source"] == "fallback"
    assert primary.call_count == 1
    assert fallback.call_count == 1
```

---

### Testing with Side Effects

**Mock multiple return values:**

```python
@pytest.mark.asyncio
async def test_side_effects():
    mock = MockPrimitive(
        side_effects=[
            {"status": "pending"},
            {"status": "processing"},
            {"status": "complete"}
        ]
    )

    # Each call returns next value in sequence
    result1 = await mock.execute({}, context)
    result2 = await mock.execute({}, context)
    result3 = await mock.execute({}, context)

    assert result1["status"] == "pending"
    assert result2["status"] == "processing"
    assert result3["status"] == "complete"
```

---

## Integration Testing

### End-to-End Workflow Testing

**Test complete workflows:**

```python
@pytest.mark.integration
@pytest.mark.asyncio
async def test_rag_workflow_integration():
    """Test RAG workflow end-to-end."""
    rag_workflow = (
        embed_query >>
        search_vectors >>
        rerank_results >>
        generate_response
    )

    result = await rag_workflow.execute(
        {"query": "What are primitives?"},
        context
    )

    assert "response" in result
    assert result["response_length"] > 0
    assert result["sources_count"] > 0
```

---

### Testing with Real Services

**Use test databases/APIs:**

```python
@pytest.mark.integration
@pytest.mark.asyncio
async def test_with_test_database():
    """Test with actual database (isolated test instance)."""
    # Use test database connection
    db_primitive = DatabasePrimitive(
        connection_string="postgresql://test_db"
    )

    workflow = validate_data >> db_primitive >> verify_storage
    result = await workflow.execute(test_data, context)

    assert result["stored"] is True

    # Cleanup
    await db_primitive.cleanup()
```

---

### Testing Observability

**Verify tracing and metrics:**

```python
@pytest.mark.asyncio
async def test_workflow_creates_spans(caplog):
    """Test workflow creates OpenTelemetry spans."""
    from opentelemetry import trace
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import SimpleSpanProcessor
    from opentelemetry.sdk.trace.export.in_memory_span_exporter import (
        InMemorySpanExporter
    )

    # Setup in-memory span exporter
    exporter = InMemorySpanExporter()
    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    trace.set_tracer_provider(provider)

    # Execute workflow
    workflow = step1 >> step2 >> step3
    await workflow.execute({}, context)

    # Verify spans created
    spans = exporter.get_finished_spans()
    assert len(spans) >= 3  # At least one per step
```

---

## Testing Best Practices

### ✅ DO

**Test Success and Failure:**
```python
# Test happy path
@pytest.mark.asyncio
async def test_success_case():
    result = await workflow.execute(valid_input, context)
    assert result["status"] == "success"

# Test error cases
@pytest.mark.asyncio
async def test_error_case():
    with pytest.raises(ValidationError):
        await workflow.execute(invalid_input, context)
```

**Use Descriptive Names:**
```python
# Good: Clear what is being tested
async def test_cache_primitive_returns_cached_value_on_second_call()

# Bad: Unclear purpose
async def test_cache()
```

**Arrange-Act-Assert:**
```python
@pytest.mark.asyncio
async def test_workflow():
    # Arrange - Setup test data
    mock = MockPrimitive(return_value={"result": "test"})
    workflow = step1 >> mock >> step3

    # Act - Execute operation
    result = await workflow.execute(input_data, context)

    # Assert - Verify outcome
    assert result["result"] == "test"
    assert mock.call_count == 1
```

**Test Edge Cases:**
```python
# Test empty input
async def test_empty_input()

# Test maximum values
async def test_maximum_size_input()

# Test special characters
async def test_special_characters_in_input()

# Test concurrent access
async def test_concurrent_execution()
```

---

### ❌ DON'T

**Don't Test Implementation Details:**
```python
# Bad: Testing internal state
assert workflow._internal_cache == expected_cache

# Good: Testing behavior
assert workflow.cache_hit_rate > 0.8
```

**Don't Share State Between Tests:**
```python
# Bad: Tests share state
cache = CachePrimitive(...)

def test_1():
    cache.add("key", "value")  # ❌ Affects test_2

def test_2():
    assert cache.get("key") is None  # ❌ Fails due to test_1

# Good: Fresh state per test
def test_1():
    cache = CachePrimitive(...)
    cache.add("key", "value")

def test_2():
    cache = CachePrimitive(...)
    assert cache.get("key") is None
```

**Don't Skip Async:**
```python
# Bad: Synchronous test for async code
def test_workflow():
    result = workflow.execute(data, context)  # ❌ Missing await

# Good: Proper async test
@pytest.mark.asyncio
async def test_workflow():
    result = await workflow.execute(data, context)
```

---

## Coverage Requirements

**TTA.dev requires 100% test coverage for all new code:**

### Check Coverage

```bash
# Generate coverage report
uv run pytest --cov=packages --cov-report=html --cov-report=term-missing

# View HTML report
open htmlcov/index.html
```

### Coverage Configuration

```python
# pyproject.toml
[tool.coverage.run]
source = ["packages"]
omit = ["*/tests/*", "*/test_*.py"]

[tool.coverage.report]
precision = 2
fail_under = 95.0
show_missing = true
```

**See:** [[TESTING_GUIDE]]

---

## Testing Tools & Frameworks

### Core Testing Stack

- **pytest** - Test framework
- **pytest-asyncio** - Async test support
- **pytest-cov** - Coverage reporting
- **pytest-mock** - Mocking utilities

### TTA.dev Testing Tools

- **MockPrimitive** - Mock workflow primitives
- **TestContext** - Standard test context
- **Integration test utilities** - Safe integration testing

**See:** [[TTA.dev/Testing Strategy]]

---

## Example Test Suites

### Example 1: Primitive Test Suite

```python
# tests/test_cache_primitive.py

import pytest
from tta_dev_primitives.performance import CachePrimitive
from tta_dev_primitives.testing import MockPrimitive, create_test_context

class TestCachePrimitive:
    """Test suite for CachePrimitive."""

    @pytest.fixture
    def context(self):
        return create_test_context()

    @pytest.fixture
    def mock_primitive(self):
        return MockPrimitive(return_value={"computed": True})

    @pytest.mark.asyncio
    async def test_cache_miss(self, mock_primitive, context):
        """Test cache miss calls underlying primitive."""
        cache = CachePrimitive(mock_primitive, ttl_seconds=60)
        result = await cache.execute({"key": "test"}, context)

        assert result["computed"] is True
        assert mock_primitive.call_count == 1

    @pytest.mark.asyncio
    async def test_cache_hit(self, mock_primitive, context):
        """Test cache hit doesn't call underlying primitive."""
        cache = CachePrimitive(mock_primitive, ttl_seconds=60)

        # First call - miss
        await cache.execute({"key": "test"}, context)

        # Second call - hit
        result = await cache.execute({"key": "test"}, context)

        assert result["computed"] is True
        assert mock_primitive.call_count == 1  # Only called once
        assert cache.cache_hits == 1

    @pytest.mark.asyncio
    async def test_cache_ttl_expiration(self, mock_primitive, context):
        """Test cache expiration after TTL."""
        import asyncio

        cache = CachePrimitive(mock_primitive, ttl_seconds=0.1)

        # First call
        await cache.execute({"key": "test"}, context)

        # Wait for expiration
        await asyncio.sleep(0.2)

        # Should be expired
        await cache.execute({"key": "test"}, context)

        assert mock_primitive.call_count == 2  # Called twice
```

---

### Example 2: Workflow Integration Test

```python
# tests/integration/test_rag_workflow.py

import pytest
from workflows.rag import create_rag_workflow

@pytest.mark.integration
class TestRAGWorkflowIntegration:
    """Integration tests for RAG workflow."""

    @pytest.fixture
    def rag_workflow(self):
        return create_rag_workflow()

    @pytest.mark.asyncio
    async def test_simple_query(self, rag_workflow, context):
        """Test RAG workflow with simple query."""
        result = await rag_workflow.execute(
            {"query": "What is a primitive?"},
            context
        )

        assert "response" in result
        assert len(result["response"]) > 0
        assert result["sources_count"] > 0

    @pytest.mark.asyncio
    async def test_complex_query(self, rag_workflow, context):
        """Test RAG workflow with complex query."""
        result = await rag_workflow.execute(
            {"query": "How do I compose primitives in parallel?"},
            context
        )

        assert "response" in result
        assert "parallel" in result["response"].lower()
        assert result["confidence"] > 0.7
```

---

## Related Concepts

- [[Primitive]] - Testing primitives
- [[Workflow]] - Testing workflows
- [[Recovery]] - Testing error handling
- [[Performance]] - Performance testing
- [[Production]] - Production testing strategies

---

## Documentation

- [[TESTING_GUIDE]] - Comprehensive testing guide
- [[TTA.dev/Testing Strategy]] - Testing strategy
- [[TESTING_METHODOLOGY_SUMMARY]] - Testing methodology
- [[TESTING_VERIFICATION_COMPLETE]] - Testing verification
- [[PRIMITIVES_CATALOG]] - Primitive reference
- [[AGENTS]] - Agent instructions

---

**Tags:** #testing #pytest #mocking #coverage #quality #index-page

**Last Updated:** 2025-11-05
**Maintained by:** TTA.dev Team
