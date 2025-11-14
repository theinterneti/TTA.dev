---
applyTo: "**/tests/**/*.py,**/*_test.py,**/test_*.py"
description: "Testing standards and best practices"
---

# Testing Instructions

## Testing Philosophy

1. **Test-Driven Development (TDD)** - Write tests first when possible
2. **Comprehensive Coverage** - Aim for >90% code coverage
3. **Fast Feedback** - Tests should run quickly
4. **Isolation** - Tests should be independent
5. **Descriptive Names** - Test names should explain what they test

## Test Structure

### Standard Test Pattern

```python
import pytest
from unittest.mock import AsyncMock, Mock, patch

# Arrange - Set up test data and mocks
# Act - Execute the code under test
# Assert - Verify the results

@pytest.mark.asyncio
async def test_feature_success_case():
    """Test feature works correctly with valid input."""
    # Arrange
    input_data = {"key": "value"}
    expected_output = {"result": "success"}

    # Act
    result = await feature_function(input_data)

    # Assert
    assert result == expected_output
```

## Required Test Categories

### 1. Unit Tests

Test individual functions and classes in isolation:

```python
async def test_primitive_execute():
    """Test primitive executes successfully."""
    primitive = MyPrimitive()
    context = WorkflowContext(workflow_id="test")

    result = await primitive.execute({"input": "data"}, context)

    assert result["status"] == "success"
    assert "output" in result
```

### 2. Integration Tests

Test components working together:

```python
async def test_workflow_integration():
    """Test complete workflow execution."""
    workflow = step1 >> step2 >> step3
    context = WorkflowContext(workflow_id="integration-test")

    result = await workflow.execute({"data": "test"}, context)

    assert result["step1_complete"]
    assert result["step2_complete"]
    assert result["step3_complete"]
```

### 3. Async Tests

All async code must use `@pytest.mark.asyncio`:

```python
@pytest.mark.asyncio
async def test_async_operation():
    """Test asynchronous operation."""
    result = await async_function()
    assert result is not None
```

## Fixtures and Mocks

### Common Fixtures

```python
@pytest.fixture
def workflow_context():
    """Create test workflow context."""
    return WorkflowContext(
        workflow_id="test-workflow",
        session_id="test-session",
        correlation_id="test-correlation"
    )

@pytest.fixture
async def mock_database():
    """Provide mock database for testing."""
    db = AsyncMock()
    db.query.return_value = [{"id": 1, "name": "test"}]
    yield db
    # Cleanup if needed
```

### Mocking External Services

```python
@patch("module.external_api_call")
async def test_with_mocked_api(mock_api):
    """Test with mocked external API."""
    mock_api.return_value = {"status": "ok"}

    result = await function_that_calls_api()

    assert result["api_response"]["status"] == "ok"
    mock_api.assert_called_once()
```

## Test Naming Conventions

Use descriptive names that explain:
- **What** is being tested
- **Under what conditions**
- **What the expected outcome is**

```python
# Good test names
async def test_retry_primitive_succeeds_after_transient_failure()
async def test_cache_primitive_returns_cached_value_on_second_call()
async def test_validation_raises_error_for_invalid_input()

# Bad test names
async def test_retry()  # Too vague
async def test_1()  # Not descriptive
async def test_it_works()  # Unclear
```

## Coverage Requirements

```bash
# Run tests with coverage
uv run pytest --cov=packages --cov-report=html --cov-report=term-missing

# Coverage targets:
# - Overall: >90%
# - Critical paths (auth, security): >95%
# - Utility functions: >85%
```

## Parameterized Tests

Use `@pytest.mark.parametrize` for testing multiple scenarios:

```python
@pytest.mark.parametrize("input_value,expected", [
    ("valid", "success"),
    ("", "error"),
    (None, "error"),
    ("special_case", "special_result"),
])
async def test_multiple_inputs(input_value, expected):
    """Test function with various inputs."""
    result = await process(input_value)
    assert result["status"] == expected
```

## Error Testing

Always test error conditions:

```python
async def test_raises_on_invalid_input():
    """Test proper error handling."""
    with pytest.raises(ValueError, match="Invalid input"):
        await function_with_validation(invalid_input)
```

## Test Organization

```
tests/
├── unit/                    # Fast, isolated tests
│   ├── test_primitives.py
│   └── test_utils.py
├── integration/             # Tests with real dependencies
│   ├── test_workflows.py
│   └── test_database.py
└── e2e/                     # Full system tests
    └── test_complete_flow.py
```

## Continuous Testing

```python
# Run on file changes
uv run pytest-watch

# Run specific test file
uv run pytest tests/unit/test_retry.py -v

# Run specific test
uv run pytest tests/unit/test_retry.py::test_retry_succeeds -v

# Run with markers
uv run pytest -m "not slow"  # Skip slow tests
```

## Test Markers

```python
import pytest

@pytest.mark.slow
async def test_performance_heavy_operation():
    """Mark slow tests for optional exclusion."""
    pass

@pytest.mark.integration
async def test_database_integration():
    """Mark integration tests."""
    pass

@pytest.mark.requires_api
async def test_external_api():
    """Mark tests requiring external services."""
    pass
```

## Quality Checklist

- [ ] All new code has tests
- [ ] Tests follow AAA pattern (Arrange, Act, Assert)
- [ ] Async code uses `@pytest.mark.asyncio`
- [ ] Mocks used for external dependencies
- [ ] Edge cases tested
- [ ] Error conditions tested
- [ ] Test names are descriptive
- [ ] Coverage >90% for new code
- [ ] Tests run quickly (<5 seconds for unit tests)
- [ ] No flaky tests (random failures)

## Anti-Patterns

❌ **Avoid:**
```python
# Testing implementation details
assert primitive._internal_state == "value"

# Tests that depend on execution order
def test_part_1(): global_state.value = 1
def test_part_2(): assert global_state.value == 1  # Fragile!

# Overly complex tests
def test_everything():  # Tests 10 different things
```

✅ **Prefer:**
```python
# Test public interface
assert primitive.get_state() == "value"

# Independent tests
@pytest.fixture
def clean_state():
    return State()

# Focused tests
def test_one_specific_behavior():  # Tests one thing well
```

## References

- [pytest Documentation](https://docs.pytest.org/)
- [Testing Best Practices](https://docs.python-guide.org/writing/tests/)
- [Effective Testing](https://testdriven.io/blog/testing-best-practices/)
