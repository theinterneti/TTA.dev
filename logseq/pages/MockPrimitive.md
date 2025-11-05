# MockPrimitive

**Testing primitive for mocking expensive operations in unit tests**

---

## Overview

`MockPrimitive` is a [[WorkflowPrimitive]] designed specifically for testing workflows. It allows you to mock expensive or external operations (LLM calls, API requests, database queries) with configurable return values, making tests faster, deterministic, and independent of external services.

**Package:** [[tta-dev-primitives]]
**Category:** Testing Primitives
**Use Cases:** Unit testing, integration testing, CI/CD pipelines

---

## Key Features

### 1. Configurable Return Values
- **Static return**: Always return the same value
- **Sequential returns**: Return different values on successive calls
- **Callable return**: Compute return value dynamically
- **Exception simulation**: Test error handling

### 2. Call Tracking
- **Call count**: Number of times primitive was called
- **Call arguments**: Track input data and context from each call
- **Call history**: Full history of all invocations

### 3. Type Safety
- **Generic types**: `MockPrimitive[TInput, TOutput]` with full type checking
- **Type hints**: Same type safety as production primitives
- **Editor support**: Autocomplete and type checking in IDEs

---

## Basic Usage

### Simple Mock

```python
from tta_dev_primitives.testing import MockPrimitive
from tta_dev_primitives import WorkflowContext
import pytest

@pytest.mark.asyncio
async def test_simple_workflow():
    # Create mock LLM
    mock_llm = MockPrimitive(
        return_value={"response": "Mocked LLM output"}
    )
    
    # Use in workflow
    workflow = input_processor >> mock_llm >> output_formatter
    
    # Execute
    context = WorkflowContext(correlation_id="test-1")
    result = await workflow.execute({"input": "test"}, context)
    
    # Verify
    assert result["formatted_response"] == "Mocked LLM output"
    assert mock_llm.call_count == 1
```

### Mock with Sequential Returns

```python
@pytest.mark.asyncio
async def test_retry_logic():
    # First 2 calls fail, 3rd succeeds
    mock_api = MockPrimitive(
        return_values=[
            Exception("API Error 1"),
            Exception("API Error 2"),
            {"data": "success"}
        ]
    )
    
    # Workflow with retry
    workflow = RetryPrimitive(
        primitive=mock_api,
        max_retries=3
    )
    
    # Execute
    result = await workflow.execute({"request": "data"}, context)
    
    # Verify retry worked
    assert result["data"] == "success"
    assert mock_api.call_count == 3
```

---

## Common Testing Patterns

### Pattern 1: Mocking LLM Calls

```python
from tta_dev_primitives.testing import MockPrimitive

@pytest.mark.asyncio
async def test_llm_workflow():
    # Mock expensive LLM call
    mock_llm = MockPrimitive(
        return_value={
            "choices": [{
                "message": {
                    "content": "This is a test response"
                }
            }],
            "usage": {
                "prompt_tokens": 10,
                "completion_tokens": 5
            }
        }
    )
    
    # Build workflow
    workflow = (
        prepare_prompt >>
        mock_llm >>  # No actual LLM call
        extract_response
    )
    
    # Test
    result = await workflow.execute({"input": "test"}, context)
    
    # Verify
    assert "test response" in result["output"]
    assert mock_llm.call_count == 1
    
    # Check what was passed to LLM
    call_data = mock_llm.call_history[0]
    assert "prompt" in call_data["input_data"]
```

### Pattern 2: Mocking API Requests

```python
@pytest.mark.asyncio
async def test_api_integration():
    # Mock external API
    mock_api = MockPrimitive(
        return_value={
            "status": "success",
            "data": {
                "user_id": "user-123",
                "profile": {"name": "Test User"}
            }
        }
    )
    
    # Workflow with fallback
    workflow = FallbackPrimitive(
        primary=mock_api,
        fallback=local_cache
    )
    
    # Test
    result = await workflow.execute({"user_id": "user-123"}, context)
    
    assert result["data"]["user_id"] == "user-123"
```

### Pattern 3: Mocking Database Queries

```python
@pytest.mark.asyncio
async def test_database_workflow():
    # Mock database query
    mock_db = MockPrimitive(
        return_value=[
            {"id": 1, "name": "Document 1", "content": "..."},
            {"id": 2, "name": "Document 2", "content": "..."},
        ]
    )
    
    # RAG workflow with mock retrieval
    workflow = (
        mock_db >>  # No actual DB query
        rerank_documents >>
        generate_response
    )
    
    # Test
    result = await workflow.execute({"query": "test"}, context)
    
    assert len(result["sources"]) == 2
```

### Pattern 4: Testing Error Handling

```python
@pytest.mark.asyncio
async def test_error_recovery():
    # Mock that always fails
    mock_failing = MockPrimitive(
        return_value=Exception("Simulated failure")
    )
    
    # Workflow with fallback
    workflow = FallbackPrimitive(
        primary=mock_failing,
        fallback=MockPrimitive(return_value={"status": "fallback used"})
    )
    
    # Test fallback triggered
    result = await workflow.execute({"input": "test"}, context)
    
    assert result["status"] == "fallback used"
```

---

## Advanced Usage

### Dynamic Return Values

```python
@pytest.mark.asyncio
async def test_dynamic_mock():
    # Callable return value
    def compute_response(data, context):
        # Access input to compute response
        query = data.get("query", "")
        return {
            "response": f"Processed: {query}",
            "length": len(query)
        }
    
    mock_processor = MockPrimitive(
        return_value=compute_response
    )
    
    # Test
    result = await mock_processor.execute(
        {"query": "hello world"},
        context
    )
    
    assert result["response"] == "Processed: hello world"
    assert result["length"] == 11
```

### Call History Inspection

```python
@pytest.mark.asyncio
async def test_call_tracking():
    mock_step = MockPrimitive(return_value={"status": "ok"})
    
    # Execute multiple times
    workflow = step1 >> mock_step >> step3
    
    await workflow.execute({"a": 1}, context)
    await workflow.execute({"b": 2}, context)
    await workflow.execute({"c": 3}, context)
    
    # Inspect all calls
    assert mock_step.call_count == 3
    
    # Check first call
    first_call = mock_step.call_history[0]
    assert first_call["input_data"]["a"] == 1
    
    # Check correlation IDs
    for call in mock_step.call_history:
        assert "correlation_id" in call["context"].data
```

### Conditional Mocking

```python
@pytest.mark.asyncio
async def test_conditional_behavior():
    # Different behavior based on input
    def conditional_response(data, context):
        if data.get("type") == "fast":
            return {"result": "fast response", "cost": 0.001}
        else:
            return {"result": "quality response", "cost": 0.01}
    
    mock_router = MockPrimitive(return_value=conditional_response)
    
    # Test fast path
    fast_result = await mock_router.execute(
        {"type": "fast", "query": "test"},
        context
    )
    assert fast_result["cost"] == 0.001
    
    # Test quality path
    quality_result = await mock_router.execute(
        {"type": "quality", "query": "test"},
        context
    )
    assert quality_result["cost"] == 0.01
```

---

## Integration with Testing Frameworks

### pytest Fixtures

```python
import pytest
from tta_dev_primitives.testing import MockPrimitive, create_test_context

@pytest.fixture
def mock_llm():
    """Reusable mock LLM for tests."""
    return MockPrimitive(
        return_value={
            "response": "Test response",
            "model": "gpt-4-mini"
        }
    )

@pytest.fixture
def test_context():
    """Reusable test context."""
    return create_test_context(correlation_id="test-fixture")

@pytest.mark.asyncio
async def test_with_fixtures(mock_llm, test_context):
    workflow = input_processor >> mock_llm >> output_formatter
    result = await workflow.execute({"input": "test"}, test_context)
    
    assert "Test response" in result["output"]
```

### Parametrized Tests

```python
@pytest.mark.parametrize("input_data,expected", [
    ({"query": "hello"}, "hello"),
    ({"query": "world"}, "world"),
    ({"query": ""}, ""),
])
@pytest.mark.asyncio
async def test_parametrized(input_data, expected):
    mock_processor = MockPrimitive(
        return_value=lambda d, c: {"result": d["query"]}
    )
    
    result = await mock_processor.execute(input_data, context)
    assert result["result"] == expected
```

---

## Best Practices

### 1. Mock at the Right Level

```python
# ✅ Good - Mock external dependencies
mock_llm = MockPrimitive(return_value={"response": "..."})
workflow = internal_logic >> mock_llm >> more_internal_logic

# ❌ Bad - Don't mock internal logic you should test
mock_everything = MockPrimitive(return_value=final_result)
# This tests nothing!
```

### 2. Use Realistic Mock Data

```python
# ✅ Good - Realistic structure
mock_api = MockPrimitive(return_value={
    "status": 200,
    "data": {
        "user": {"id": "123", "name": "Test"},
        "preferences": {"theme": "dark"}
    },
    "timestamp": "2025-11-01T12:00:00Z"
})

# ❌ Bad - Oversimplified
mock_api = MockPrimitive(return_value={"result": "ok"})
```

### 3. Test Both Success and Failure

```python
@pytest.mark.asyncio
async def test_success():
    mock = MockPrimitive(return_value={"status": "success"})
    # ... test success path

@pytest.mark.asyncio
async def test_failure():
    mock = MockPrimitive(return_value=Exception("Error"))
    # ... test error handling
```

### 4. Verify Mock Interactions

```python
@pytest.mark.asyncio
async def test_caching():
    mock_llm = MockPrimitive(return_value={"response": "cached"})
    
    workflow = CachePrimitive(mock_llm, ttl=60)
    
    # First call
    await workflow.execute({"input": "test"}, context)
    assert mock_llm.call_count == 1
    
    # Second call (should use cache)
    await workflow.execute({"input": "test"}, context)
    assert mock_llm.call_count == 1  # Still 1, cache hit!
```

---

## Configuration Options

### Constructor Parameters

```python
MockPrimitive(
    return_value=None,          # Single return value (any type)
    return_values=None,         # List of values for sequential calls
    side_effect=None,           # Callable for dynamic behavior
    
    # Advanced options
    record_calls=True,          # Track call history
    max_history_size=100,       # Limit history size
    validate_input=False,       # Validate input against schema
)
```

### Return Value Types

```python
# Static value
MockPrimitive(return_value={"result": "static"})

# Exception
MockPrimitive(return_value=ValueError("Test error"))

# Callable
MockPrimitive(return_value=lambda d, c: compute(d))

# Sequential
MockPrimitive(return_values=[
    {"attempt": 1},
    {"attempt": 2},
    {"attempt": 3}
])
```

---

## Testing Complex Workflows

### Multi-Agent Workflow Testing

```python
@pytest.mark.asyncio
async def test_multi_agent():
    # Mock each agent
    mock_research = MockPrimitive(return_value={"data": "research"})
    mock_analysis = MockPrimitive(return_value={"insights": "analysis"})
    mock_writing = MockPrimitive(return_value={"content": "written"})
    
    # Build multi-agent workflow
    workflow = ParallelPrimitive([
        mock_research,
        mock_analysis,
        mock_writing
    ]) >> aggregate_results
    
    # Test
    result = await workflow.execute({"task": "test"}, context)
    
    # Verify all agents called
    assert mock_research.call_count == 1
    assert mock_analysis.call_count == 1
    assert mock_writing.call_count == 1
```

### RAG Workflow Testing

```python
@pytest.mark.asyncio
async def test_rag_workflow():
    # Mock retrieval
    mock_retriever = MockPrimitive(return_value={
        "documents": [
            {"id": 1, "content": "Doc 1", "score": 0.9},
            {"id": 2, "content": "Doc 2", "score": 0.8},
        ]
    })
    
    # Mock LLM
    mock_llm = MockPrimitive(return_value={
        "response": "Answer based on docs",
        "sources": [1, 2]
    })
    
    # RAG workflow
    workflow = (
        mock_retriever >>
        rerank_documents >>
        assemble_context >>
        mock_llm >>
        format_response
    )
    
    # Test
    result = await workflow.execute({"query": "test"}, context)
    
    assert "Answer based on docs" in result["text"]
    assert len(result["sources"]) == 2
```

---

## Performance Testing

### Latency Simulation

```python
import asyncio

@pytest.mark.asyncio
async def test_timeout_handling():
    # Mock slow operation
    async def slow_response(data, context):
        await asyncio.sleep(5)  # Simulate slow API
        return {"result": "slow"}
    
    mock_slow = MockPrimitive(return_value=slow_response)
    
    # Workflow with timeout
    workflow = TimeoutPrimitive(mock_slow, timeout=1.0)
    
    # Test timeout triggered
    with pytest.raises(TimeoutError):
        await workflow.execute({"input": "test"}, context)
```

### Load Testing

```python
@pytest.mark.asyncio
async def test_parallel_load():
    mock_api = MockPrimitive(return_value={"status": "ok"})
    
    # Simulate 100 concurrent requests
    workflow = mock_api
    
    tasks = [
        workflow.execute({"request": i}, context)
        for i in range(100)
    ]
    
    results = await asyncio.gather(*tasks)
    
    assert len(results) == 100
    assert mock_api.call_count == 100
```

---

## Debugging Failed Tests

### Enable Verbose Logging

```python
import logging

logging.basicConfig(level=logging.DEBUG)

@pytest.mark.asyncio
async def test_with_logging():
    mock = MockPrimitive(return_value={"result": "test"})
    
    # Logs will show:
    # - When mock is called
    # - Input data passed
    # - Return value
    # - Call count
    
    result = await mock.execute({"input": "debug"}, context)
```

### Inspect Call History

```python
@pytest.mark.asyncio
async def test_debug_calls():
    mock = MockPrimitive(return_value={"status": "ok"})
    
    # Execute workflow
    await workflow.execute({"input": "test"}, context)
    
    # Debug: Print all calls
    for i, call in enumerate(mock.call_history):
        print(f"Call {i}:")
        print(f"  Input: {call['input_data']}")
        print(f"  Context: {call['context'].correlation_id}")
        print(f"  Timestamp: {call['timestamp']}")
```

---

## Related Primitives

- [[WorkflowPrimitive]] - Base class for all primitives
- [[InstrumentedPrimitive]] - Primitive with observability
- [[SequentialPrimitive]] - Sequential execution for testing workflows
- [[ParallelPrimitive]] - Parallel execution for testing concurrency

---

## Related Documentation

- [[TTA.dev/Testing]] - Testing strategies for TTA.dev
- [[TTA.dev/Examples]] - Example tests using MockPrimitive
- [[tta-dev-primitives]] - Package overview

---

## External Resources

- [pytest Documentation](https://docs.pytest.org/) - Testing framework
- [pytest-asyncio](https://pytest-asyncio.readthedocs.io/) - Async testing
- [unittest.mock](https://docs.python.org/3/library/unittest.mock.html) - Python mocking

---

**Package:** [[tta-dev-primitives]]
**Category:** Testing Primitives
**Source:** `src/tta_dev_primitives/testing/mock_primitive.py`
**Tests:** `tests/testing/test_mock_primitive.py`
