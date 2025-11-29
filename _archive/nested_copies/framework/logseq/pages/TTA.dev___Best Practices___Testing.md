# Testing Best Practices

#best-practices #testing #stage-testing #tta-dev

## Overview

Best practices for testing TTA.dev primitives and workflows.

## When to Apply

- **Stage:** TESTING
- **Priority:** HIGH
- **Audience:** All developers

## Key Principles

### 1. 100% Test Coverage Required

All new code must have 100% test coverage before merging.

```python
# Run tests with coverage
uv run pytest --cov=packages --cov-report=term-missing
```

### 2. Use pytest-asyncio for Async Tests

All async primitives require async tests:

```python
import pytest
from tta_dev_primitives.core.base import WorkflowContext

@pytest.mark.asyncio
async def test_my_primitive():
    """Test my primitive execution."""
    primitive = MyPrimitive()
    context = WorkflowContext()
    result = await primitive.execute(input_data, context)
    assert result is not None
```

### 3. Test All Code Paths

- ✅ Success case
- ✅ Error cases (all exception types)
- ✅ Edge cases (empty input, None values, etc.)
- ✅ Boundary conditions

### 4. Mock External Dependencies

Use MockPrimitive for testing workflows:

```python
from tta_dev_primitives.testing import MockPrimitive

@pytest.mark.asyncio
async def test_workflow_with_mocks():
    mock_llm = MockPrimitive(return_value={"output": "test"})
    workflow = step1 >> mock_llm >> step3
    result = await workflow.execute(input_data, context)
    assert mock_llm.call_count == 1
```

### 5. Test Observability Integration

Verify WorkflowContext propagation:

```python
@pytest.mark.asyncio
async def test_context_propagation():
    context = WorkflowContext(
        correlation_id="test-123",
        metadata={"user": "test"}
    )
    result = await primitive.execute(input_data, context)
    # Verify spans created, metrics recorded
```

## Anti-Patterns to Avoid

### ❌ Don't Skip Async Marker

```python
# BAD - Missing pytest.mark.asyncio
async def test_my_primitive():
    result = await primitive.execute()
```

### ❌ Don't Use time.sleep() in Async Tests

```python
# BAD - Blocks event loop
import time
time.sleep(1)

# GOOD - Use asyncio.sleep()
import asyncio
await asyncio.sleep(1)
```

### ❌ Don't Test Implementation Details

```python
# BAD - Testing private methods
assert primitive._internal_state == "value"

# GOOD - Test public API
result = await primitive.execute(input_data, context)
assert result["output"] == "expected"
```

## Testing Checklist

Before moving to STAGING:

- [ ] All unit tests pass
- [ ] 100% test coverage achieved
- [ ] All async tests use @pytest.mark.asyncio
- [ ] External dependencies mocked
- [ ] Error cases tested
- [ ] Edge cases tested
- [ ] Observability verified
- [ ] No time.sleep() in tests
- [ ] Type hints complete

## Related Pages

- [[TTA.dev/Common Mistakes/Testing Antipatterns]]
- [[TTA.dev/Examples/Test Examples]]
- [[TTA.dev/Stage Guides/Testing Stage]]
- [[Testing TTA Primitives]]

## References

- pytest documentation: https://docs.pytest.org/
- pytest-asyncio: https://pytest-asyncio.readthedocs.io/
- TTA.dev testing guide: `docs/development/CodingStandards.md`

- [[Project Hub]]