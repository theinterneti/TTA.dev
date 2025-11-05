# WorkflowPrimitive

**Base class for all TTA.dev workflow primitives providing type-safe composition and automatic observability.**

## Overview

`WorkflowPrimitive[TInput, TOutput]` is the foundation of TTA.dev's composable workflow system. All primitives inherit from this base class to gain type safety, operator overloading, and built-in observability.

**Source:** `packages/tta-dev-primitives/src/tta_dev_primitives/core/base.py`

## Basic Usage

```python
from tta_dev_primitives import WorkflowPrimitive, WorkflowContext
from typing import TypeVar

TInput = TypeVar('TInput')
TOutput = TypeVar('TOutput')

class MyPrimitive(WorkflowPrimitive[dict, dict]):
    """Custom primitive implementation."""

    async def _execute_impl(
        self,
        input_data: dict,
        context: WorkflowContext
    ) -> dict:
        """Implement your primitive logic here."""
        # Your processing logic
        result = process(input_data)
        return result

# Use it
primitive = MyPrimitive()
context = WorkflowContext(correlation_id="example-1")
result = await primitive.execute({"input": "data"}, context)
```

## Type Parameters

### TInput

**Input data type for the primitive.**

```python
class StringProcessor(WorkflowPrimitive[str, dict]):
    """Accepts string, returns dict."""
    pass

class DictTransformer(WorkflowPrimitive[dict, dict]):
    """Accepts dict, returns dict."""
    pass
```

**Benefits:**
- Type checking with pyright/mypy
- IDE autocomplete support
- Early error detection

### TOutput

**Output data type from the primitive.**

```python
class DataFetcher(WorkflowPrimitive[dict, list]):
    """Accepts dict, returns list."""
    pass

class Aggregator(WorkflowPrimitive[list, dict]):
    """Accepts list, returns dict."""
    pass
```

**Type safety:** Output of one primitive must match input of next in composition.

## Core Methods

### execute()

**Primary method to run the primitive.**

```python
async def execute(
    self,
    input_data: TInput,
    context: WorkflowContext
) -> TOutput:
    """Execute primitive with automatic observability."""
    pass
```

**What it does:**
1. Creates OpenTelemetry span
2. Records start time
3. Calls `_execute_impl()` (your implementation)
4. Records metrics
5. Handles errors
6. Returns result

**Usage:**
```python
result = await primitive.execute(data, context)
```

### _execute_impl()

**Abstract method you implement.**

```python
async def _execute_impl(
    self,
    input_data: TInput,
    context: WorkflowContext
) -> TOutput:
    """Your primitive implementation."""
    raise NotImplementedError("Subclasses must implement _execute_impl")
```

**Guidelines:**
- Don't call `execute()` directly in implementation
- Use `context` for correlation IDs and metadata
- Return type must match `TOutput`
- Raise exceptions for errors (handled by base class)

## Composition Operators

### Sequential: `>>`

**Chain primitives in sequence.**

```python
workflow = step1 >> step2 >> step3
```

**Equivalent to:**
```python
workflow = SequentialPrimitive([step1, step2, step3])
```

**Type constraint:** `step1.TOutput` must match `step2.TInput`

### Parallel: `|`

**Execute primitives concurrently.**

```python
workflow = branch1 | branch2 | branch3
```

**Equivalent to:**
```python
workflow = ParallelPrimitive([branch1, branch2, branch3])
```

**Type constraint:** All primitives must have same `TInput`

## WorkflowContext

**Carries metadata and state through workflow.**

```python
from tta_dev_primitives import WorkflowContext

context = WorkflowContext(
    correlation_id="req-12345",        # For tracing
    workflow_id="my-workflow",         # Workflow identifier
    data={                             # Custom metadata
        "user_id": "user-789",
        "request_type": "analysis"
    }
)
```

**Automatic propagation:**
- Correlation IDs for distributed tracing
- Span context for OpenTelemetry
- Custom metadata accessible in all primitives

**Access in primitive:**
```python
async def _execute_impl(self, input_data, context):
    user_id = context.data.get("user_id")
    logger.info("processing", user_id=user_id, correlation_id=context.correlation_id)
    return result
```

## Built-in Observability

### Automatic Tracing

Every `execute()` call creates an OpenTelemetry span:

```python
# Span name: primitive_name.execute
# Span attributes:
#   - primitive.name
#   - correlation_id
#   - workflow_id
#   - input_type
#   - output_type
```

**View in Jaeger:** <http://localhost:16686>

### Automatic Metrics

Prometheus metrics exported on `:9464/metrics`:

```promql
# Execution duration
primitive_execution_duration_seconds{primitive="MyPrimitive"}

# Total executions
primitive_execution_total{primitive="MyPrimitive"}

# Error count
primitive_execution_errors_total{primitive="MyPrimitive"}
```

### Structured Logging

Automatic logs for execution lifecycle:

```json
{
  "event": "primitive_execution_started",
  "primitive": "MyPrimitive",
  "correlation_id": "req-12345"
}
{
  "event": "primitive_execution_completed",
  "primitive": "MyPrimitive",
  "duration_ms": 45.2,
  "status": "success"
}
```

## Advanced Patterns

### Pattern 1: Custom Primitive with Validation

```python
class ValidatedPrimitive(WorkflowPrimitive[dict, dict]):
    """Primitive with input validation."""

    def __init__(self, required_fields: list[str]):
        super().__init__()
        self.required_fields = required_fields

    async def _execute_impl(self, input_data: dict, context: WorkflowContext) -> dict:
        # Validate input
        for field in self.required_fields:
            if field not in input_data:
                raise ValueError(f"Missing required field: {field}")

        # Process
        result = await self._process(input_data, context)
        return result

    async def _process(self, data: dict, context: WorkflowContext) -> dict:
        """Override this method in subclasses."""
        raise NotImplementedError
```

### Pattern 2: Primitive with Configuration

```python
from dataclasses import dataclass

@dataclass
class ProcessorConfig:
    """Configuration for processor primitive."""
    max_retries: int = 3
    timeout_seconds: float = 30.0
    cache_enabled: bool = True

class ConfigurablePrimitive(WorkflowPrimitive[dict, dict]):
    """Primitive with configuration."""

    def __init__(self, config: ProcessorConfig):
        super().__init__()
        self.config = config

    async def _execute_impl(self, input_data: dict, context: WorkflowContext) -> dict:
        # Use configuration
        if self.config.cache_enabled:
            cached = await check_cache(input_data)
            if cached:
                return cached

        result = await process_with_config(input_data, self.config)
        return result
```

### Pattern 3: Primitive with State

```python
class StatefulPrimitive(WorkflowPrimitive[dict, dict]):
    """Primitive maintaining internal state."""

    def __init__(self):
        super().__init__()
        self.execution_count = 0
        self.total_processing_time = 0.0

    async def _execute_impl(self, input_data: dict, context: WorkflowContext) -> dict:
        start = time.time()

        # Process
        result = await process(input_data)

        # Update state
        self.execution_count += 1
        self.total_processing_time += time.time() - start

        return result

    @property
    def average_time(self) -> float:
        """Calculate average execution time."""
        return self.total_processing_time / self.execution_count if self.execution_count > 0 else 0.0
```

### Pattern 4: Generic Primitive

```python
from typing import Generic, TypeVar, Callable

TIn = TypeVar('TIn')
TOut = TypeVar('TOut')

class FunctionPrimitive(WorkflowPrimitive[TIn, TOut], Generic[TIn, TOut]):
    """Wrap a function as a primitive."""

    def __init__(self, func: Callable[[TIn, WorkflowContext], TOut]):
        super().__init__()
        self.func = func

    async def _execute_impl(self, input_data: TIn, context: WorkflowContext) -> TOut:
        if asyncio.iscoroutinefunction(self.func):
            return await self.func(input_data, context)
        else:
            return self.func(input_data, context)

# Usage
def my_processor(data: dict, context: WorkflowContext) -> dict:
    return {"processed": data}

primitive = FunctionPrimitive(my_processor)
```

## Testing Primitives

### Unit Testing

```python
import pytest
from tta_dev_primitives import WorkflowContext

@pytest.mark.asyncio
async def test_my_primitive():
    # Arrange
    primitive = MyPrimitive()
    context = WorkflowContext(correlation_id="test-1")
    input_data = {"value": 42}

    # Act
    result = await primitive.execute(input_data, context)

    # Assert
    assert result["value"] == 42
    assert "processed" in result
```

### Testing with Mocks

```python
from tta_dev_primitives.testing import MockPrimitive

@pytest.mark.asyncio
async def test_workflow_with_mock():
    # Mock expensive operation
    mock_llm = MockPrimitive(return_value={"response": "mocked"})

    # Compose workflow
    workflow = step1 >> mock_llm >> step3

    # Execute
    result = await workflow.execute(input_data, context)

    # Verify
    assert mock_llm.call_count == 1
    assert result["response"] == "mocked"
```

## Integration with Enhanced Primitives

### Using tta-observability-integration

```python
from observability_integration import initialize_observability
from observability_integration.primitives import CachePrimitive

# Initialize observability
initialize_observability(service_name="my-app")

# Use enhanced primitives
workflow = (
    CachePrimitive(expensive_op, ttl=3600) >>
    my_primitive >>
    format_output
)
```

**Benefits:**
- Enhanced metrics with cache hit rate
- Automatic Prometheus export on :9464
- Grafana dashboard integration

## Best Practices

### 1. Always Use Type Hints

```python
# ✅ Good
class MyPrimitive(WorkflowPrimitive[dict, dict]):
    async def _execute_impl(
        self,
        input_data: dict,
        context: WorkflowContext
    ) -> dict:
        return {"result": input_data}

# ❌ Bad
class MyPrimitive(WorkflowPrimitive):
    async def _execute_impl(self, input_data, context):
        return {"result": input_data}
```

### 2. Use Context for Metadata

```python
# ✅ Good
async def _execute_impl(self, input_data, context):
    user_id = context.data.get("user_id")
    logger.info("processing", user_id=user_id)
    return process(input_data, user_id)

# ❌ Bad - global variable
USER_ID = "user-123"
async def _execute_impl(self, input_data, context):
    return process(input_data, USER_ID)
```

### 3. Handle Errors Properly

```python
# ✅ Good - let base class handle errors
async def _execute_impl(self, input_data, context):
    if not input_data.get("required_field"):
        raise ValueError("Missing required field")
    return process(input_data)

# ❌ Bad - swallow errors
async def _execute_impl(self, input_data, context):
    try:
        return process(input_data)
    except Exception:
        return {"error": "Something went wrong"}
```

### 4. Keep Primitives Focused

```python
# ✅ Good - single responsibility
class FetchDataPrimitive(WorkflowPrimitive[dict, dict]):
    async def _execute_impl(self, input_data, context):
        return await fetch_from_api(input_data)

class ProcessDataPrimitive(WorkflowPrimitive[dict, dict]):
    async def _execute_impl(self, input_data, context):
        return process(input_data)

workflow = FetchDataPrimitive() >> ProcessDataPrimitive()

# ❌ Bad - doing too much
class FetchAndProcessPrimitive(WorkflowPrimitive[dict, dict]):
    async def _execute_impl(self, input_data, context):
        data = await fetch_from_api(input_data)
        return process(data)
```

## Related Documentation

- [[InstrumentedPrimitive]] - Base class with observability
- [[SequentialPrimitive]] - Sequential composition
- [[ParallelPrimitive]] - Parallel execution
- [[PRIMITIVES CATALOG]] - All primitives
- [[tta-dev-primitives]] - Core primitives package

## Source Code

**File:** `packages/tta-dev-primitives/src/tta_dev_primitives/core/base.py`

## Tags

primitive:: base-class
type:: foundation
feature:: composition
feature:: type-safety
feature:: observability
