# MockPrimitive

type:: [[Primitive]]
category:: [[Testing]]
package:: [[TTA.dev/Packages/tta-dev-primitives]]
status:: [[Stable]]
version:: 1.0.0
test-coverage:: 100
complexity:: [[Low]]
python-class:: `MockPrimitive`
import-path:: `from tta_dev_primitives.testing import MockPrimitive`
related-primitives:: [[TTA.dev/Primitives/SequentialPrimitive]], [[TTA.dev/Primitives/ParallelPrimitive]]

---

## Overview

- id:: mock-primitive-overview
  A testing primitive that returns predefined values, tracks call count, and simulates delays. Essential for testing workflows without external dependencies.

  **Think of it as:** A test double that replaces real primitives in tests, making tests fast, reliable, and deterministic.

---

## Use Cases

- id:: mock-primitive-use-cases
  - **Unit testing:** Test workflows without calling real LLMs/APIs
  - **Integration testing:** Mock external services
  - **Performance testing:** Simulate different response times
  - **Error testing:** Simulate failures and exceptions
  - **Cost-free testing:** No API costs during test runs

---

## Key Benefits

- id:: mock-primitive-benefits
  - ✅ **Fast tests** - No network calls, instant responses
  - ✅ **Deterministic** - Same input always produces same output
  - ✅ **Cost-free** - No API charges during testing
  - ✅ **Call tracking** - Verify primitives were called correctly
  - ✅ **Delay simulation** - Test timeout and performance scenarios
  - ✅ **Error simulation** - Test error handling paths

---

## API Reference

- id:: mock-primitive-api

### Constructor

```python
MockPrimitive(
    return_value: Any = None,
    side_effect: Callable | Exception | list | None = None,
    delay: float = 0.0,
    name: str = "MockPrimitive"
)
```

**Parameters:**

- `return_value`: Value to return on execution
- `side_effect`: Callable, exception, or list of values for multiple calls
- `delay`: Simulated delay in seconds (for testing timeouts)
- `name`: Name for debugging

**Returns:** A new `MockPrimitive` instance

---

## Examples

### Basic Mock

- id:: mock-basic-example

```python
import pytest
from tta_dev_primitives import WorkflowContext
from tta_dev_primitives.testing import MockPrimitive

@pytest.mark.asyncio
async def test_workflow():
    # Mock an expensive LLM call
    mock_llm = MockPrimitive(
        return_value={"response": "This is a mock response"}
    )

    # Use in workflow
    workflow = step1 >> mock_llm >> step3

    context = WorkflowContext(correlation_id="test-001")
    result = await workflow.execute(input_data="test", context=context)

    # Verify
    assert result["response"] == "This is a mock response"
    assert mock_llm.call_count == 1
```

### Mock with Side Effect

- id:: mock-side-effect

```python
# Different return value each call
mock = MockPrimitive(
    side_effect=["first", "second", "third"]
)

result1 = await mock.execute("test", context)  # Returns "first"
result2 = await mock.execute("test", context)  # Returns "second"
result3 = await mock.execute("test", context)  # Returns "third"
```

### Mock Failure

- id:: mock-failure-example

```python
# Simulate an exception
mock_api = MockPrimitive(
    side_effect=ConnectionError("API unavailable")
)

# Test error handling
try:
    result = await mock_api.execute("test", context)
except ConnectionError as e:
    assert str(e) == "API unavailable"
```

### Mock with Delay

- id:: mock-delay-example

```python
from tta_dev_primitives.recovery import TimeoutPrimitive

# Simulate slow operation
slow_mock = MockPrimitive(
    return_value="slow response",
    delay=5.0  # 5 seconds
)

# Test timeout handling
timeout_workflow = TimeoutPrimitive(slow_mock, timeout_seconds=2.0)

try:
    result = await timeout_workflow.execute("test", context)
except TimeoutError:
    print("Correctly timed out!")
```

---

## Testing Patterns

- id:: mock-testing-patterns

### Test Sequential Workflow

```python
@pytest.mark.asyncio
async def test_sequential():
    mock1 = MockPrimitive(return_value={"step": 1})
    mock2 = MockPrimitive(return_value={"step": 2})
    mock3 = MockPrimitive(return_value={"step": 3})

    workflow = mock1 >> mock2 >> mock3

    result = await workflow.execute("test", context)

    assert result["step"] == 3
    assert all(m.call_count == 1 for m in [mock1, mock2, mock3])
```

### Test Parallel Workflow

```python
@pytest.mark.asyncio
async def test_parallel():
    mock1 = MockPrimitive(return_value="result1", delay=0.1)
    mock2 = MockPrimitive(return_value="result2", delay=0.1)
    mock3 = MockPrimitive(return_value="result3", delay=0.1)

    workflow = mock1 | mock2 | mock3

    start = time.time()
    results = await workflow.execute("test", context)
    duration = time.time() - start

    assert results == ["result1", "result2", "result3"]
    assert duration < 0.2  # Parallel, not sequential (0.3s)
```

### Test Error Recovery

```python
@pytest.mark.asyncio
async def test_retry_on_failure():
    # Fails twice, succeeds third time
    mock = MockPrimitive(
        side_effect=[
            ConnectionError("fail 1"),
            ConnectionError("fail 2"),
            "success"
        ]
    )

    retry_workflow = RetryPrimitive(mock, max_retries=3)

    result = await retry_workflow.execute("test", context)

    assert result == "success"
    assert mock.call_count == 3
```

---

## Verification Methods

- id:: mock-verification

### Call Count

```python
mock = MockPrimitive(return_value="test")
await mock.execute("input", context)
await mock.execute("input", context)

assert mock.call_count == 2
```

### Call Arguments

```python
mock = MockPrimitive(return_value="test")
await mock.execute("input1", context)
await mock.execute("input2", context)

# Verify all calls
assert len(mock.calls) == 2
assert mock.calls[0]["input_data"] == "input1"
assert mock.calls[1]["input_data"] == "input2"
```

### Reset Mock

```python
mock = MockPrimitive(return_value="test")
await mock.execute("test", context)

assert mock.call_count == 1

mock.reset()

assert mock.call_count == 0
assert len(mock.calls) == 0
```

---

## Best Practices

- id:: mock-best-practices

✅ **Mock external services** - APIs, databases, LLMs
✅ **Verify call count** - Ensure primitives called correct number of times
✅ **Use side_effect for sequences** - Different return values per call
✅ **Simulate delays** - Test timeout scenarios
✅ **Test error paths** - Use side_effect with exceptions
✅ **Reset between tests** - Use mock.reset() or create new mocks

❌ **Don't over-mock** - Test real code when possible
❌ **Don't mock internals** - Mock at boundaries (external services)
❌ **Don't skip integration tests** - Mocks don't replace real testing
❌ **Don't forget assertions** - Always verify mock was called

---

## Related Content

### Works Well With

- [[TTA.dev/Primitives/RetryPrimitive]] - Test retry logic
- [[TTA.dev/Primitives/FallbackPrimitive]] - Test fallback scenarios
- [[TTA.dev/Primitives/TimeoutPrimitive]] - Test timeout handling
- All primitives - Mock any primitive in tests

### Used In Examples

{{query (and [[Example]] [[Testing]])}}

---

## Observability

### Tracing

Mock primitives create spans like real primitives:

```
workflow_execution
└── mock_primitive_execution
    ├── return_value: "mocked"
    └── call_count: 1
```

---

## Metadata

**Source Code:** [mock_primitive.py](https://github.com/theinterneti/TTA.dev/blob/main/platform/primitives/src/tta_dev_primitives/testing/mock_primitive.py)
**Tests:** [test_mock_primitive.py](https://github.com/theinterneti/TTA.dev/blob/main/platform/primitives/tests/test_mock_primitive.py)

**Created:** [[2025-10-30]]
**Last Updated:** [[2025-10-30]]
**Test Coverage:** 100%
**Status:** [[Stable]] - Production Ready
