# Primitive1

**Generic primitive reference page**

---

## Overview

This page serves as a disambiguation and reference for generic primitive placeholders referenced throughout the TTA.dev knowledge base.

**Note:** "Primitive1" typically refers to a placeholder for any TTA.dev workflow primitive in documentation examples.

---

## What is a Primitive?

In TTA.dev, a **primitive** is a composable building block for AI workflows. Each primitive:

- Implements `WorkflowPrimitive[TInput, TOutput]`
- Has a clear, single responsibility
- Supports composition via `>>` and `|` operators
- Includes automatic observability
- Is fully testable in isolation

See [[WorkflowPrimitive]] for the base class documentation.

---

## Common Primitive Categories

### Core Workflow Primitives

**Sequential and parallel execution:**

- [[SequentialPrimitive]] - Execute steps in order
- [[ParallelPrimitive]] - Execute steps concurrently
- [[ConditionalPrimitive]] - Branch based on conditions
- [[RouterPrimitive]] - Dynamic routing to handlers

**Documentation:** [[TTA.dev/Concepts/Composition]]

### Recovery Primitives

**Error handling and resilience:**

- [[RetryPrimitive]] - Retry with backoff strategies
- [[FallbackPrimitive]] - Graceful degradation
- [[TimeoutPrimitive]] - Timeout protection
- [[CompensationPrimitive]] - Saga pattern for rollback
- [[CircuitBreakerPrimitive]] - Circuit breaker pattern

**Documentation:** [[TTA.dev/Patterns/Error Handling]]

### Performance Primitives

**Optimization and caching:**

- [[CachePrimitive]] - LRU cache with TTL
- [[MemoryPrimitive]] - Conversational memory

**Documentation:** [[TTA.dev/Patterns/Caching]], [[TTA.dev/Patterns/Performance]]

### Orchestration Primitives

**Multi-agent coordination:**

- [[DelegationPrimitive]] - Orchestrator → Executor pattern
- [[MultiModelWorkflow]] - Multi-model coordination
- [[TaskClassifierPrimitive]] - Task classification and routing

**Documentation:** [[Multi-Agent Orchestration]]

### Testing Primitives

**Test utilities:**

- [[MockPrimitive]] - Mock primitive for testing

**Documentation:** [[TTA.dev/Testing Strategy]]

---

## Creating Custom Primitives

### Basic Custom Primitive

```python
from tta_dev_primitives import WorkflowPrimitive, WorkflowContext

class MyCustomPrimitive(WorkflowPrimitive[str, dict]):
    """Custom primitive that processes strings."""
    
    async def _execute_impl(
        self,
        data: str,
        context: WorkflowContext
    ) -> dict:
        """Process the input string."""
        
        # Your custom logic here
        processed = data.upper()
        
        return {"result": processed}

# Use it
primitive = MyCustomPrimitive()
result = await primitive.execute("hello", WorkflowContext())
# Result: {"result": "HELLO"}
```

### With Configuration

```python
class ConfigurablePrimitive(WorkflowPrimitive[dict, dict]):
    """Primitive with configuration options."""
    
    def __init__(self, mode: str = "fast", max_retries: int = 3):
        super().__init__()
        self.mode = mode
        self.max_retries = max_retries
    
    async def _execute_impl(
        self,
        data: dict,
        context: WorkflowContext
    ) -> dict:
        """Execute with configured behavior."""
        
        if self.mode == "fast":
            return await self._fast_process(data)
        else:
            return await self._quality_process(data)
    
    async def _fast_process(self, data: dict) -> dict:
        """Fast processing mode."""
        return {"result": "fast", "data": data}
    
    async def _quality_process(self, data: dict) -> dict:
        """Quality processing mode."""
        return {"result": "quality", "data": data}

# Use with different configurations
fast_primitive = ConfigurablePrimitive(mode="fast")
quality_primitive = ConfigurablePrimitive(mode="quality", max_retries=5)
```

---

## Composition Examples

### Sequential Composition

```python
# Define primitives
primitive1 = TextExtractionPrimitive()
primitive2 = EmbeddingPrimitive()
primitive3 = StoragePrimitive()

# Compose sequentially
workflow = primitive1 >> primitive2 >> primitive3

# Execute
result = await workflow.execute({"document": doc}, context)
```

### Parallel Composition

```python
# Define parallel branches
primitive1 = FastLLMPrimitive()
primitive2 = QualityLLMPrimitive()
primitive3 = CachedResponsePrimitive()

# Compose in parallel
workflow = primitive1 | primitive2 | primitive3

# Execute - all run concurrently
results = await workflow.execute({"prompt": "Hello"}, context)
```

### Mixed Composition

```python
# Preprocessing
primitive1 = ValidatePrimitive()

# Parallel processing
primitive2 = AnalysisPrimitive()
primitive3 = ClassificationPrimitive()
primitive4 = ExtractionPrimitive()

# Aggregation
primitive5 = AggregationPrimitive()

# Compose: sequential → parallel → sequential
workflow = (
    primitive1 >>
    (primitive2 | primitive3 | primitive4) >>
    primitive5
)
```

---

## Naming Conventions

### Standard Naming Patterns

1. **Purpose-based:** `CachePrimitive`, `RetryPrimitive`, `FallbackPrimitive`
2. **Operation-based:** `TextExtractionPrimitive`, `EmbeddingPrimitive`
3. **Integration-based:** `OpenAIPrimitive`, `SupabasePrimitive`

### Best Practices

```python
# ✅ Good: Clear purpose
class TextCleaningPrimitive(WorkflowPrimitive):
    """Cleans and normalizes text."""
    pass

# ✅ Good: Descriptive operation
class VectorSearchPrimitive(WorkflowPrimitive):
    """Searches vector database for similar embeddings."""
    pass

# ❌ Bad: Generic name
class Primitive1(WorkflowPrimitive):
    """Does stuff."""  # What stuff?
    pass

# ❌ Bad: Unclear purpose
class HandlerPrimitive(WorkflowPrimitive):
    """Handles things."""  # What things?
    pass
```

---

## Testing Primitives

### Unit Testing

```python
import pytest
from tta_dev_primitives import WorkflowContext

@pytest.mark.asyncio
async def test_primitive1_basic_functionality():
    """Test basic primitive behavior."""
    
    # Arrange
    primitive = MyCustomPrimitive()
    context = WorkflowContext(workflow_id="test")
    input_data = "hello world"
    
    # Act
    result = await primitive.execute(input_data, context)
    
    # Assert
    assert result["result"] == "HELLO WORLD"
    assert "error" not in result

@pytest.mark.asyncio
async def test_primitive1_error_handling():
    """Test primitive error handling."""
    
    primitive = MyCustomPrimitive()
    context = WorkflowContext(workflow_id="test")
    
    with pytest.raises(ValueError):
        await primitive.execute(None, context)  # Should raise
```

### Integration Testing

```python
@pytest.mark.asyncio
async def test_primitive1_in_workflow():
    """Test primitive in composed workflow."""
    
    primitive1 = PreprocessPrimitive()
    primitive2 = MyCustomPrimitive()
    primitive3 = PostprocessPrimitive()
    
    workflow = primitive1 >> primitive2 >> primitive3
    
    result = await workflow.execute({"input": "test"}, WorkflowContext())
    
    assert result["status"] == "completed"
```

---

## Observability

### Automatic Tracing

All primitives automatically create OpenTelemetry spans:

```python
# No explicit tracing needed
primitive1 = MyCustomPrimitive()

# Span created automatically
result = await primitive1.execute(data, context)

# Check traces in Jaeger:
# - Span name: "MyCustomPrimitive.execute"
# - Duration, status, attributes included
```

### Custom Metrics

```python
from prometheus_client import Counter, Histogram

class MetricsPrimitive(WorkflowPrimitive[dict, dict]):
    """Primitive with custom metrics."""
    
    execution_count = Counter(
        'primitive_executions_total',
        'Total primitive executions',
        ['primitive_name']
    )
    
    execution_duration = Histogram(
        'primitive_duration_seconds',
        'Primitive execution duration',
        ['primitive_name']
    )
    
    async def _execute_impl(self, data: dict, context: WorkflowContext) -> dict:
        with self.execution_duration.labels(
            primitive_name=self.__class__.__name__
        ).time():
            result = await self._process(data)
            
            self.execution_count.labels(
                primitive_name=self.__class__.__name__
            ).inc()
            
            return result
```

---

## Related Pages

### Core Concepts

- [[WorkflowPrimitive]] - Base primitive class
- [[TTA.dev/Concepts/Composition]] - Composing primitives
- [[TTA.dev/Concepts/Context Propagation]] - Context in primitives

### Pattern Documentation

- [[TTA.dev/Patterns/Error Handling]] - Error handling patterns
- [[TTA.dev/Patterns/Caching]] - Caching patterns
- [[TTA.dev/Patterns/Sequential Workflow]] - Sequential patterns
- [[TTA.dev/Patterns/Parallel Execution]] - Parallel patterns

### Primitive Categories

- [[TTA Primitives]] - Complete primitive catalog
- [[Recovery Primitives]] - Error handling primitives
- [[Performance Primitives]] - Optimization primitives
- [[Orchestration Primitives]] - Multi-agent primitives

### Examples

- [[TTA.dev/Examples/Basic Workflow]] - Simple primitive usage
- [[TTA.dev/Examples/RAG Workflow]] - Primitives in RAG
- [[TTA.dev/Examples/Multi-Agent Workflow]] - Agent primitives

---

## See Also

- [[Primitive2]] - Second generic primitive reference
- [[Primitive3]] - Third generic primitive reference
- [[Custom Primitives Guide]] - Creating custom primitives

---

**Note:** This is a generic reference page. For specific primitive documentation, see the [[TTA Primitives]] catalog.

**Category:** Reference / Disambiguation
**Status:** Generic placeholder
