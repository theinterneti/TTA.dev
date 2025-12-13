---
type: "agent_requested"
description: "Example description"
---

# Test File Guidelines

## Testing Philosophy

Every test should be:
1. **Fast**: Use `MockPrimitive` instead of real implementations
2. **Isolated**: No external dependencies (databases, APIs, etc.)
3. **Async-ready**: Use `@pytest.mark.asyncio` for async tests
4. **Comprehensive**: Test success, failure, and edge cases

## Test Structure

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
    assert mock2.call_count == 1
    assert mock1.last_input == "input"
    assert result == "result2"

@pytest.mark.asyncio
async def test_workflow_failure():
    """Test workflow handles failures correctly."""
    # Arrange
    error = ValueError("Test error")
    mock_fail = MockPrimitive("fail", side_effect=error)
    context = WorkflowContext()

    # Act & Assert
    with pytest.raises(ValueError, match="Test error"):
        await mock_fail.execute("input", context)
```

## Testing Primitives with MockPrimitive

```python
from tta_dev_primitives.testing import MockPrimitive

# Return static value
mock = MockPrimitive("name", return_value={"result": "success"})

# Raise exception
mock = MockPrimitive("name", side_effect=ValueError("Error"))

# Custom behavior
async def custom_logic(data, ctx):
    return {"processed": data}

mock = MockPrimitive("name", side_effect=custom_logic)

# Verify calls
assert mock.call_count == 3
assert mock.last_input == expected_input
assert mock.last_context.workflow_id == "test-123"
```

## Testing Sequential Workflows

```python
@pytest.mark.asyncio
async def test_sequential_pipeline():
    """Test sequential execution with data passing."""
    mock1 = MockPrimitive("validate", return_value={"valid": True})
    mock2 = MockPrimitive("process", return_value={"processed": True})
    mock3 = MockPrimitive("save", return_value={"saved": True})

    workflow = mock1 >> mock2 >> mock3
    context = WorkflowContext()

    result = await workflow.execute({"input": "data"}, context)

    # Verify execution order
    assert mock1.call_count == 1
    assert mock2.call_count == 1
    assert mock3.call_count == 1

    # Verify data flow
    assert mock1.last_input == {"input": "data"}
    assert mock2.last_input == {"valid": True}
    assert mock3.last_input == {"processed": True}
    assert result == {"saved": True}
```

## Testing Parallel Workflows

```python
@pytest.mark.asyncio
async def test_parallel_execution():
    """Test parallel workflow executes all branches."""
    mock1 = MockPrimitive("branch1", return_value="result1")
    mock2 = MockPrimitive("branch2", return_value="result2")
    mock3 = MockPrimitive("branch3", return_value="result3")

    workflow = mock1 | mock2 | mock3
    context = WorkflowContext()

    results = await workflow.execute("input", context)

    # All branches executed
    assert mock1.call_count == 1
    assert mock2.call_count == 1
    assert mock3.call_count == 1

    # All receive same input
    assert mock1.last_input == "input"
    assert mock2.last_input == "input"
    assert mock3.last_input == "input"

    # Results collected
    assert results == ["result1", "result2", "result3"]
```

## Testing Error Handling

```python
@pytest.mark.asyncio
async def test_retry_on_failure():
    """Test retry primitive retries on failure."""
    from tta_dev_primitives.recovery.retry import RetryPrimitive

    call_count = 0
    async def flaky_operation(data, ctx):
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise ValueError("Temporary error")
        return "success"

    retry_workflow = RetryPrimitive(
        MockPrimitive("flaky", side_effect=flaky_operation),
        max_attempts=3,
        backoff_factor=1.0
    )

    context = WorkflowContext()
    result = await retry_workflow.execute("input", context)

    assert call_count == 3
    assert result == "success"

@pytest.mark.asyncio
async def test_timeout_enforced():
    """Test timeout primitive enforces time limits."""
    from tta_dev_primitives.recovery.timeout import TimeoutPrimitive, TimeoutError

    async def slow_operation(data, ctx):
        await asyncio.sleep(10.0)  # Too slow
        return "done"

    timeout_workflow = TimeoutPrimitive(
        MockPrimitive("slow", side_effect=slow_operation),
        timeout_seconds=0.1
    )

    context = WorkflowContext()

    with pytest.raises(TimeoutError):
        await timeout_workflow.execute("input", context)
```

## Testing Cache Behavior

```python
@pytest.mark.asyncio
async def test_cache_hits_and_misses():
    """Test cache primitive caches results correctly."""
    from tta_dev_primitives.performance.cache import CachePrimitive

    call_count = 0
    async def expensive_op(data, ctx):
        nonlocal call_count
        call_count += 1
        return f"result-{call_count}"

    cached = CachePrimitive(
        MockPrimitive("expensive", side_effect=expensive_op),
        cache_key_fn=lambda d, c: str(d),
        ttl_seconds=60.0
    )

    context = WorkflowContext()

    # First call - cache miss
    result1 = await cached.execute("input", context)
    assert result1 == "result-1"
    assert call_count == 1

    # Second call - cache hit
    result2 = await cached.execute("input", context)
    assert result2 == "result-1"  # Same result
    assert call_count == 1  # Not called again

    # Different input - cache miss
    result3 = await cached.execute("different", context)
    assert result3 == "result-2"
    assert call_count == 2
```

## Fixtures and Setup

```python
@pytest.fixture
def sample_context():
    """Provide a standard test context."""
    return WorkflowContext(
        workflow_id="test-workflow",
        session_id="test-session",
        metadata={"env": "test"}
    )

@pytest.fixture
async def mock_workflow():
    """Provide a mock workflow for testing."""
    return MockPrimitive("test", return_value={"success": True})

@pytest.mark.asyncio
async def test_with_fixtures(sample_context, mock_workflow):
    """Test using fixtures."""
    result = await mock_workflow.execute("input", sample_context)
    assert result == {"success": True}
```

## Parameterized Tests

```python
@pytest.mark.asyncio
@pytest.mark.parametrize("input_data,expected", [
    ({"value": 1}, {"result": 2}),
    ({"value": 5}, {"result": 10}),
    ({"value": 0}, {"result": 0}),
])
async def test_multiple_inputs(input_data, expected):
    """Test with multiple input scenarios."""
    async def double_value(data, ctx):
        return {"result": data["value"] * 2}

    workflow = MockPrimitive("double", side_effect=double_value)
    context = WorkflowContext()

    result = await workflow.execute(input_data, context)
    assert result == expected
```

## Testing Context Propagation

```python
@pytest.mark.asyncio
async def test_context_propagation():
    """Test that context is passed through workflow."""
    contexts_seen = []

    async def capture_context(data, ctx):
        contexts_seen.append(ctx)
        return data

    mock1 = MockPrimitive("step1", side_effect=capture_context)
    mock2 = MockPrimitive("step2", side_effect=capture_context)

    workflow = mock1 >> mock2
    context = WorkflowContext(workflow_id="test-propagation")

    await workflow.execute("input", context)

    # Same context instance passed to both
    assert len(contexts_seen) == 2
    assert contexts_seen[0] is contexts_seen[1]
    assert contexts_seen[0].workflow_id == "test-propagation"
```

## Test Organization

```
tests/
├── test_core.py          # Core primitive tests
├── test_recovery.py      # Recovery pattern tests
├── test_performance.py   # Performance utility tests
├── test_routing.py       # Router tests
└── integration/          # Integration tests
    └── test_workflows.py
```

## Coverage Requirements

- **Target**: 100% coverage for new code
- **Minimum**: 80% overall coverage
- **Command**: `uv run pytest --cov=src --cov-report=html`

## Quality Checklist

- [ ] Uses `@pytest.mark.asyncio` for async tests
- [ ] Uses `MockPrimitive` instead of real implementations
- [ ] Tests success, failure, and edge cases
- [ ] Verifies call counts and data flow
- [ ] Uses descriptive test names and docstrings
- [ ] No external dependencies (no network, DB, filesystem)
- [ ] Fast execution (< 1s per test)


---
**Logseq:** [[TTA.dev/.augment/Rules/Tests.instructions]]
