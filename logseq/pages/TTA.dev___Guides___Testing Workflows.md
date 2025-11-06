# Testing Workflows

type:: [[Guide]]
category:: [[Development]]
difficulty:: [[Intermediate]]
estimated-time:: 30 minutes
target-audience:: [[Developers]], [[QA Engineers]], [[AI Engineers]]

---

## Overview

- id:: testing-workflows-overview
  **Testing workflows** ensures AI systems behave reliably. TTA.dev provides `MockPrimitive` for unit testing, plus patterns for integration testing, error scenario testing, and performance testing. Test workflows the same way you test regular code - with clear expectations and comprehensive coverage.

---

## Prerequisites

{{embed ((prerequisites-full))}}

**Should have read:**
- [[TTA.dev/Guides/Agentic Primitives]] - Core concepts
- [[TTA.dev/Guides/Workflow Composition]] - Building workflows

**Should understand:**
- pytest basics
- async/await in Python
- WorkflowContext usage

---

## Why Test Workflows?

### What Can Go Wrong

**Without testing:**
- ❌ LLM calls fail silently
- ❌ Retry logic doesn't activate
- ❌ Fallbacks never triggered
- ❌ Cache returns stale data
- ❌ Context not propagated correctly
- ❌ Performance regressions unnoticed

**With testing:**
- ✅ Verify primitives compose correctly
- ✅ Validate error handling works
- ✅ Ensure context flows through workflow
- ✅ Confirm expected behavior
- ✅ Catch regressions early
- ✅ Document intended behavior

---

## Testing Philosophy

### Test Pyramid for Workflows

```
         /\
        /  \  Integration Tests (10%)
       /    \  - Full workflow end-to-end
      /------\  - Real context propagation
     /        \ - Error scenarios
    /----------\
   /            \ Unit Tests (90%)
  /              \ - Individual primitives
 /                \ - Mock dependencies
/__________________\ - Fast execution
```

**Focus on:**
- **Unit tests** - 90% of tests, fast, isolated
- **Integration tests** - 10% of tests, slower, realistic
- **Property tests** - Verify invariants (context preserved, etc.)

---

## MockPrimitive: Your Testing Tool

### Basic Usage

```python
from tta_dev_primitives.testing import MockPrimitive
from tta_dev_primitives import WorkflowContext
import pytest

@pytest.mark.asyncio
async def test_simple_mock():
    """Test using a mock primitive."""

    # Create mock that returns fixed value
    mock = MockPrimitive(return_value={"result": "mocked"})

    # Execute
    context = WorkflowContext()
    result = await mock.execute({"input": "test"}, context)

    # Verify
    assert result == {"result": "mocked"}
    assert mock.call_count == 1
    assert mock.calls[0]["input_data"] == {"input": "test"}
```

### MockPrimitive API

**Constructor:**
- `return_value` - Fixed value to return
- `side_effect` - Function or exception to raise
- `execution_time` - Simulated delay

**Properties:**
- `call_count` - Number of times executed
- `calls` - List of all calls (input_data, context)
- `last_call` - Most recent call

**Methods:**
- `reset()` - Clear call history

---

## Testing Sequential Workflows

### Simple Sequential Test

```python
from tta_dev_primitives import SequentialPrimitive
from tta_dev_primitives.testing import MockPrimitive
import pytest

@pytest.mark.asyncio
async def test_sequential_workflow():
    """Test A >> B >> C workflow."""

    # Create mocks
    step_a = MockPrimitive(return_value={"stage": "a", "value": 1})
    step_b = MockPrimitive(return_value={"stage": "b", "value": 2})
    step_c = MockPrimitive(return_value={"stage": "c", "value": 3})

    # Build workflow
    workflow = step_a >> step_b >> step_c

    # Execute
    context = WorkflowContext()
    result = await workflow.execute({"input": "test"}, context)

    # Verify final result
    assert result == {"stage": "c", "value": 3}

    # Verify all steps called
    assert step_a.call_count == 1
    assert step_b.call_count == 1
    assert step_c.call_count == 1

    # Verify data flow
    assert step_b.calls[0]["input_data"] == {"stage": "a", "value": 1}
    assert step_c.calls[0]["input_data"] == {"stage": "b", "value": 2}
```

### Testing with Real Implementation

```python
from tta_dev_primitives import WorkflowPrimitive

class InputProcessor(WorkflowPrimitive[dict, dict]):
    """Real primitive that processes input."""
    async def execute(self, input_data: dict, context: WorkflowContext) -> dict:
        return {"processed": input_data["raw"].upper()}

@pytest.mark.asyncio
async def test_mixed_real_and_mock():
    """Test real primitive with mocked LLM."""

    # Real processor
    processor = InputProcessor()

    # Mock LLM (expensive to call in tests)
    mock_llm = MockPrimitive(return_value={"response": "AI output"})

    # Mock formatter
    mock_formatter = MockPrimitive(return_value={"final": "formatted"})

    # Build workflow
    workflow = processor >> mock_llm >> mock_formatter

    # Execute
    context = WorkflowContext()
    result = await workflow.execute({"raw": "hello"}, context)

    # Verify
    assert result == {"final": "formatted"}
    assert mock_llm.calls[0]["input_data"] == {"processed": "HELLO"}
```

---

## Testing Parallel Workflows

### Basic Parallel Test

```python
from tta_dev_primitives import ParallelPrimitive
from tta_dev_primitives.testing import MockPrimitive
import pytest

@pytest.mark.asyncio
async def test_parallel_workflow():
    """Test A | B | C workflow."""

    # Create mocks with different execution times
    branch_a = MockPrimitive(return_value={"branch": "a"}, execution_time=0.1)
    branch_b = MockPrimitive(return_value={"branch": "b"}, execution_time=0.2)
    branch_c = MockPrimitive(return_value={"branch": "c"}, execution_time=0.15)

    # Build parallel workflow
    workflow = branch_a | branch_b | branch_c

    # Execute
    context = WorkflowContext()
    results = await workflow.execute({"input": "test"}, context)

    # Verify all branches executed
    assert branch_a.call_count == 1
    assert branch_b.call_count == 1
    assert branch_c.call_count == 1

    # Verify all branches got same input
    assert branch_a.calls[0]["input_data"] == {"input": "test"}
    assert branch_b.calls[0]["input_data"] == {"input": "test"}
    assert branch_c.calls[0]["input_data"] == {"input": "test"}

    # Verify results
    assert len(results) == 3
    assert {"branch": "a"} in results
    assert {"branch": "b"} in results
    assert {"branch": "c"} in results
```

### Testing Parallel Aggregation

```python
from tta_dev_primitives import ParallelPrimitive, SequentialPrimitive

class AggregatorPrimitive(WorkflowPrimitive[list, dict]):
    """Aggregate parallel results."""
    async def execute(self, input_data: list, context: WorkflowContext) -> dict:
        return {
            "count": len(input_data),
            "results": input_data
        }

@pytest.mark.asyncio
async def test_parallel_aggregation():
    """Test (A | B | C) >> Aggregator."""

    # Parallel branches
    branch_a = MockPrimitive(return_value={"value": 1})
    branch_b = MockPrimitive(return_value={"value": 2})
    branch_c = MockPrimitive(return_value={"value": 3})

    parallel = branch_a | branch_b | branch_c

    # Aggregator
    aggregator = AggregatorPrimitive()

    # Complete workflow
    workflow = parallel >> aggregator

    # Execute
    context = WorkflowContext()
    result = await workflow.execute({"input": "test"}, context)

    # Verify aggregation
    assert result["count"] == 3
    assert {"value": 1} in result["results"]
    assert {"value": 2} in result["results"]
    assert {"value": 3} in result["results"]
```

---

## Testing Error Scenarios

### Testing Exceptions

```python
from tta_dev_primitives.testing import MockPrimitive
import pytest

@pytest.mark.asyncio
async def test_exception_handling():
    """Test that exceptions are raised correctly."""

    # Mock that raises exception
    failing_primitive = MockPrimitive(
        side_effect=ValueError("Something went wrong")
    )

    # Verify exception raised
    context = WorkflowContext()
    with pytest.raises(ValueError, match="Something went wrong"):
        await failing_primitive.execute({"input": "test"}, context)

    # Verify still tracked
    assert failing_primitive.call_count == 1
```

### Testing Retry Behavior

```python
from tta_dev_primitives.recovery import RetryPrimitive
from tta_dev_primitives.testing import MockPrimitive
import pytest

@pytest.mark.asyncio
async def test_retry_success_on_second_attempt():
    """Test RetryPrimitive succeeds after first failure."""

    # Mock that fails first time, succeeds second time
    call_count = 0

    def side_effect(input_data, context):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise ValueError("First attempt failed")
        return {"success": True, "attempt": call_count}

    failing_primitive = MockPrimitive(side_effect=side_effect)

    # Wrap with retry
    retry_workflow = RetryPrimitive(
        primitive=failing_primitive,
        max_retries=3,
        backoff_strategy="exponential"
    )

    # Execute
    context = WorkflowContext()
    result = await retry_workflow.execute({"input": "test"}, context)

    # Verify succeeded on second attempt
    assert result == {"success": True, "attempt": 2}
    assert failing_primitive.call_count == 2

@pytest.mark.asyncio
async def test_retry_exhausted():
    """Test RetryPrimitive raises after max retries."""

    # Mock that always fails
    failing_primitive = MockPrimitive(
        side_effect=ValueError("Always fails")
    )

    # Wrap with retry
    retry_workflow = RetryPrimitive(
        primitive=failing_primitive,
        max_retries=3
    )

    # Verify raises after 3 attempts
    context = WorkflowContext()
    with pytest.raises(ValueError, match="Always fails"):
        await retry_workflow.execute({"input": "test"}, context)

    # Verify attempted 3 times
    assert failing_primitive.call_count == 3
```

### Testing Fallback Behavior

```python
from tta_dev_primitives.recovery import FallbackPrimitive
from tta_dev_primitives.testing import MockPrimitive
import pytest

@pytest.mark.asyncio
async def test_fallback_on_primary_failure():
    """Test FallbackPrimitive uses fallback on primary failure."""

    # Primary fails
    primary = MockPrimitive(side_effect=ValueError("Primary failed"))

    # Fallback succeeds
    fallback = MockPrimitive(return_value={"fallback": True})

    # Build workflow
    workflow = FallbackPrimitive(primary=primary, fallbacks=[fallback])

    # Execute
    context = WorkflowContext()
    result = await workflow.execute({"input": "test"}, context)

    # Verify fallback used
    assert result == {"fallback": True}
    assert primary.call_count == 1
    assert fallback.call_count == 1

@pytest.mark.asyncio
async def test_fallback_primary_success():
    """Test FallbackPrimitive doesn't use fallback on primary success."""

    # Primary succeeds
    primary = MockPrimitive(return_value={"primary": True})

    # Fallback (should not be called)
    fallback = MockPrimitive(return_value={"fallback": True})

    # Build workflow
    workflow = FallbackPrimitive(primary=primary, fallbacks=[fallback])

    # Execute
    context = WorkflowContext()
    result = await workflow.execute({"input": "test"}, context)

    # Verify primary used
    assert result == {"primary": True}
    assert primary.call_count == 1
    assert fallback.call_count == 0  # Never called
```

### Testing Timeout Behavior

```python
from tta_dev_primitives.recovery import TimeoutPrimitive
from tta_dev_primitives.testing import MockPrimitive
import pytest
import asyncio

@pytest.mark.asyncio
async def test_timeout_exceeded():
    """Test TimeoutPrimitive raises on timeout."""

    # Mock that takes too long
    slow_primitive = MockPrimitive(
        return_value={"result": "done"},
        execution_time=2.0  # 2 seconds
    )

    # Wrap with 0.5 second timeout
    timeout_workflow = TimeoutPrimitive(
        primitive=slow_primitive,
        timeout_seconds=0.5
    )

    # Verify raises TimeoutError
    context = WorkflowContext()
    with pytest.raises(asyncio.TimeoutError):
        await timeout_workflow.execute({"input": "test"}, context)

    # Note: slow_primitive still counts as called (started execution)
    assert slow_primitive.call_count == 1

@pytest.mark.asyncio
async def test_timeout_with_fallback():
    """Test TimeoutPrimitive uses fallback on timeout."""

    # Slow primary
    slow_primitive = MockPrimitive(
        return_value={"result": "slow"},
        execution_time=2.0
    )

    # Fast fallback
    fallback = MockPrimitive(return_value={"result": "fallback"})

    # Wrap with timeout + fallback
    timeout_workflow = TimeoutPrimitive(
        primitive=slow_primitive,
        timeout_seconds=0.5,
        fallback=fallback
    )

    # Execute
    context = WorkflowContext()
    result = await timeout_workflow.execute({"input": "test"}, context)

    # Verify fallback used
    assert result == {"result": "fallback"}
    assert fallback.call_count == 1
```

---

## Testing Context Propagation

### Verify Context Flow

```python
from tta_dev_primitives import WorkflowPrimitive, WorkflowContext
import pytest

class ContextInspector(WorkflowPrimitive[dict, dict]):
    """Primitive that inspects context."""
    async def execute(self, input_data: dict, context: WorkflowContext) -> dict:
        return {
            "workflow_id": context.workflow_id,
            "correlation_id": context.correlation_id,
            "metadata": context.metadata
        }

@pytest.mark.asyncio
async def test_context_propagation():
    """Test context flows through workflow."""

    # Create context with metadata
    context = WorkflowContext(
        workflow_id="test-workflow",
        correlation_id="test-123",
        metadata={"user_id": "user-789"}
    )

    # Build workflow
    inspector = ContextInspector()
    workflow = inspector

    # Execute
    result = await workflow.execute({"input": "test"}, context)

    # Verify context preserved
    assert result["workflow_id"] == "test-workflow"
    assert result["correlation_id"] == "test-123"
    assert result["metadata"]["user_id"] == "user-789"

@pytest.mark.asyncio
async def test_child_context():
    """Test child context inherits from parent."""

    # Parent context
    parent_context = WorkflowContext(
        workflow_id="parent",
        correlation_id="parent-123"
    )

    # Create child context
    child_context = parent_context.create_child_context()

    # Verify inheritance
    assert child_context.correlation_id == parent_context.correlation_id
    assert child_context.parent_span_id == parent_context.span_id
    assert child_context.trace_id == parent_context.trace_id
```

---

## Testing Cache Behavior

### Cache Hit/Miss Tests

```python
from tta_dev_primitives.performance import CachePrimitive
from tta_dev_primitives.testing import MockPrimitive
import pytest

@pytest.mark.asyncio
async def test_cache_hit():
    """Test cache returns cached value on second call."""

    # Mock primitive
    expensive_op = MockPrimitive(return_value={"computed": True})

    # Wrap with cache
    cached_op = CachePrimitive(primitive=expensive_op, ttl_seconds=60)

    # First call - cache miss
    context = WorkflowContext()
    result1 = await cached_op.execute({"input": "test"}, context)
    assert result1 == {"computed": True}
    assert expensive_op.call_count == 1

    # Second call - cache hit
    result2 = await cached_op.execute({"input": "test"}, context)
    assert result2 == {"computed": True}
    assert expensive_op.call_count == 1  # Still 1, not called again

@pytest.mark.asyncio
async def test_cache_miss_different_input():
    """Test cache miss on different input."""

    # Mock primitive
    expensive_op = MockPrimitive(return_value={"computed": True})

    # Wrap with cache
    cached_op = CachePrimitive(primitive=expensive_op, ttl_seconds=60)

    # First call
    context = WorkflowContext()
    result1 = await cached_op.execute({"input": "test1"}, context)
    assert expensive_op.call_count == 1

    # Second call with different input - cache miss
    result2 = await cached_op.execute({"input": "test2"}, context)
    assert expensive_op.call_count == 2  # Called again

@pytest.mark.asyncio
async def test_cache_ttl_expiration():
    """Test cache expires after TTL."""

    # Mock primitive
    expensive_op = MockPrimitive(return_value={"computed": True})

    # Wrap with short TTL
    cached_op = CachePrimitive(primitive=expensive_op, ttl_seconds=0.1)

    # First call
    context = WorkflowContext()
    result1 = await cached_op.execute({"input": "test"}, context)
    assert expensive_op.call_count == 1

    # Wait for TTL to expire
    await asyncio.sleep(0.2)

    # Second call - cache expired
    result2 = await cached_op.execute({"input": "test"}, context)
    assert expensive_op.call_count == 2  # Called again after expiration
```

---

## Integration Testing

### Full Workflow Test

```python
from tta_dev_primitives import SequentialPrimitive
from tta_dev_primitives.recovery import RetryPrimitive, FallbackPrimitive
from tta_dev_primitives.performance import CachePrimitive
import pytest

@pytest.mark.asyncio
async def test_complete_workflow_integration():
    """Integration test for complete workflow."""

    # Real primitives (not mocked)
    input_processor = InputProcessor()
    validator = DataValidator()
    formatter = OutputFormatter()

    # Mock expensive LLM call
    llm = MockPrimitive(return_value={"llm_output": "AI response"})

    # Build production-like workflow
    cached_llm = CachePrimitive(llm, ttl_seconds=3600)
    retry_llm = RetryPrimitive(cached_llm, max_retries=3)

    simple_fallback = MockPrimitive(return_value={"llm_output": "fallback"})
    resilient_llm = FallbackPrimitive(
        primary=retry_llm,
        fallbacks=[simple_fallback]
    )

    workflow = (
        input_processor >>
        validator >>
        resilient_llm >>
        formatter
    )

    # Execute with production-like context
    context = WorkflowContext(
        workflow_id="integration-test",
        correlation_id="test-456",
        metadata={"test": True}
    )

    result = await workflow.execute({"raw": "user input"}, context)

    # Verify complete flow
    assert "formatted_output" in result
    assert llm.call_count == 1
    assert simple_fallback.call_count == 0  # Not needed
```

---

## Performance Testing

### Measure Execution Time

```python
import time
import pytest

@pytest.mark.asyncio
async def test_workflow_performance():
    """Test workflow completes within time budget."""

    # Build workflow
    fast_op = MockPrimitive(return_value={"fast": True}, execution_time=0.1)
    workflow = fast_op

    # Measure execution time
    context = WorkflowContext()
    start = time.time()
    result = await workflow.execute({"input": "test"}, context)
    duration = time.time() - start

    # Verify within budget
    assert duration < 0.5  # Should complete in < 500ms

    # Check context elapsed time
    assert context.elapsed_ms() < 500

@pytest.mark.asyncio
async def test_parallel_performance_gain():
    """Test parallel execution is faster than sequential."""

    # Slow operations
    slow_op_a = MockPrimitive(return_value={"a": True}, execution_time=0.5)
    slow_op_b = MockPrimitive(return_value={"b": True}, execution_time=0.5)
    slow_op_c = MockPrimitive(return_value={"c": True}, execution_time=0.5)

    # Sequential: A >> B >> C
    sequential = slow_op_a >> slow_op_b >> slow_op_c

    # Parallel: A | B | C
    parallel = slow_op_a | slow_op_b | slow_op_c

    context = WorkflowContext()

    # Measure sequential
    start = time.time()
    await sequential.execute({"input": "test"}, context)
    sequential_time = time.time() - start

    # Reset mocks
    slow_op_a.reset()
    slow_op_b.reset()
    slow_op_c.reset()

    # Measure parallel
    start = time.time()
    await parallel.execute({"input": "test"}, context)
    parallel_time = time.time() - start

    # Verify parallel is faster
    assert parallel_time < sequential_time
    assert sequential_time >= 1.5  # ~1.5 seconds (0.5 * 3)
    assert parallel_time < 1.0  # ~0.5 seconds (max of 3)
```

---

## Best Practices

### Test Organization

✅ **One test per behavior** (not per primitive)
✅ **Clear test names** (describe what is being tested)
✅ **Arrange-Act-Assert** (setup, execute, verify)
✅ **Independent tests** (no shared state)
✅ **Fast tests** (mock expensive operations)

### What to Test

✅ **Happy path** (workflow succeeds)
✅ **Error paths** (workflow handles failures)
✅ **Edge cases** (empty input, null, etc.)
✅ **Context propagation** (data flows correctly)
✅ **Performance** (within time budgets)

### What to Mock

✅ **External services** (APIs, databases)
✅ **LLM calls** (expensive and variable)
✅ **Slow operations** (keep tests fast)
✅ **Non-deterministic operations** (randomness)

❌ **Don't mock everything** (test real logic)
❌ **Don't mock primitives under test** (defeats purpose)

---

## Common Testing Mistakes

### Mistake 1: Not Using Context

```python
# ❌ BAD - No context
@pytest.mark.asyncio
async def test_without_context():
    workflow = step1 >> step2
    result = await workflow.execute({"input": "test"}, None)  # ❌ None context
```

```python
# ✅ GOOD - Always use context
@pytest.mark.asyncio
async def test_with_context():
    context = WorkflowContext()
    workflow = step1 >> step2
    result = await workflow.execute({"input": "test"}, context)
```

### Mistake 2: Testing Implementation Instead of Behavior

```python
# ❌ BAD - Testing internal details
@pytest.mark.asyncio
async def test_internal_state():
    primitive = MyPrimitive()
    assert primitive._internal_counter == 0  # Don't test internals
```

```python
# ✅ GOOD - Testing behavior
@pytest.mark.asyncio
async def test_behavior():
    primitive = MyPrimitive()
    result = await primitive.execute({"input": "test"}, context)
    assert result["output"] == "expected"  # Test behavior
```

### Mistake 3: Not Resetting Mocks

```python
# ❌ BAD - Mocks not reset between tests
mock = MockPrimitive(return_value={"result": "test"})

@pytest.mark.asyncio
async def test_first():
    await mock.execute({"input": "test"}, context)
    assert mock.call_count == 1

@pytest.mark.asyncio
async def test_second():
    await mock.execute({"input": "test"}, context)
    assert mock.call_count == 1  # ❌ Fails! call_count is 2
```

```python
# ✅ GOOD - Reset between tests
@pytest.fixture
def mock():
    m = MockPrimitive(return_value={"result": "test"})
    yield m
    m.reset()

@pytest.mark.asyncio
async def test_first(mock):
    await mock.execute({"input": "test"}, context)
    assert mock.call_count == 1

@pytest.mark.asyncio
async def test_second(mock):
    await mock.execute({"input": "test"}, context)
    assert mock.call_count == 1  # ✅ Works!
```

---

## Testing Checklist

- [ ] Unit tests for each primitive (90% coverage)
- [ ] Integration tests for complete workflows
- [ ] Test happy path (workflow succeeds)
- [ ] Test error paths (failures handled)
- [ ] Test context propagation (data flows)
- [ ] Test retry behavior (retries work)
- [ ] Test fallback behavior (fallbacks activate)
- [ ] Test timeout behavior (timeouts fire)
- [ ] Test cache behavior (hit/miss logic)
- [ ] Test parallel execution (concurrency works)
- [ ] Performance tests (within budgets)
- [ ] Use MockPrimitive for expensive ops
- [ ] Reset mocks between tests
- [ ] Use fixtures for common setup

---

## Next Steps

- **Monitor in production:** [[TTA.dev/Guides/Observability]]
- **Optimize costs:** [[TTA.dev/Guides/Cost Optimization]]
- **Handle errors:** [[TTA.dev/Guides/Error Handling Patterns]]

---

## Related Content

### Testing Primitives

{{query (page-property type [[MockPrimitive]])}}

### Essential Guides

- [[TTA.dev/Guides/Agentic Primitives]] - Core concepts
- [[TTA.dev/Guides/Workflow Composition]] - Building workflows
- [[TTA.dev/Guides/Error Handling Patterns]] - Recovery strategies

---

## Key Takeaways

1. **MockPrimitive** - Your primary testing tool for workflows
2. **Test behaviors** - Not internal implementation details
3. **Context required** - Always use WorkflowContext in tests
4. **90% unit tests** - Fast, isolated tests for individual primitives
5. **10% integration** - Slower tests for complete workflows
6. **Reset mocks** - Clean state between tests for reliability

---

**Created:** [[2025-10-30]]
**Last Updated:** [[2025-10-30]]
**Estimated Time:** 30 minutes
**Difficulty:** [[Intermediate]]
