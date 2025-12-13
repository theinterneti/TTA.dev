# WorkflowPrimitive

type:: [[Primitive]]
category:: [[Core]]
status:: [[Stable]]
version:: 0.1.0
package:: [[tta-dev-primitives]]
test-coverage:: 100%
complexity:: [[High]]
import-path:: from tta_dev_primitives import WorkflowPrimitive

---

## Overview

- id:: workflow-primitive-overview
  **WorkflowPrimitive** is the base class for all composable workflow primitives in TTA.dev. It defines the interface for execution and provides composition operators (`>>` for sequential, `|` for parallel) that make building complex workflows intuitive and type-safe. This is the foundational primitive that all other primitives extend.

---

## Use Cases

- **Custom Primitive Development** - Extend WorkflowPrimitive to create new primitive types
- **Framework Foundation** - Base class providing composition operators
- **Type Safety** - Generic typing ensures input/output type correctness
- **Operator Overloading** - Enable `>>` and `|` operators for workflow composition
- **Context Propagation** - Pass WorkflowContext through execution chain

---

## Key Benefits

- **Composability** - All primitives share same interface and operators
- **Type Safety** - Generic `WorkflowPrimitive[InputType, OutputType]` ensures correctness
- **Abstraction** - Hide complexity behind simple execute() interface
- **Extensibility** - Easy to create custom primitives by extending base class
- **Observability** - WorkflowContext carries trace IDs and correlation data

---

## API Reference

### Base Class

```python
class WorkflowPrimitive(Generic[T, U], ABC):
    """Base class for composable workflow primitives."""

    @abstractmethod
    async def execute(self, input_data: T, context: WorkflowContext) -> U:
        """Execute the primitive with input data and context."""
        pass

    def __rshift__(self, other: WorkflowPrimitive[U, V]) -> WorkflowPrimitive[T, V]:
        """Chain primitives sequentially: self >> other."""
        pass

    def __or__(self, other: WorkflowPrimitive[T, U]) -> WorkflowPrimitive[T, list[U]]:
        """Execute primitives in parallel: self | other."""
        pass
```

### WorkflowContext

```python
class WorkflowContext(BaseModel):
    """Context passed through workflow execution."""

    # Core identifiers
    workflow_id: str | None
    session_id: str | None
    correlation_id: str  # Auto-generated UUID
    metadata: dict[str, Any]
    state: dict[str, Any]

    # Distributed tracing (W3C Trace Context)
    trace_id: str | None  # OpenTelemetry trace ID
    span_id: str | None   # Current span ID
    parent_span_id: str | None
    trace_flags: int = 1  # Sampled

    # Observability
    baggage: dict[str, str]  # W3C Baggage
    tags: dict[str, str]

    # Timing
    start_time: float
    checkpoints: list[tuple[str, float]]

    def checkpoint(self, name: str) -> None:
        """Record a timing checkpoint."""

    def elapsed_ms(self) -> float:
        """Get elapsed time in milliseconds."""

    def create_child_context(self) -> WorkflowContext:
        """Create child context for nested workflows."""

    def to_otel_context(self) -> dict[str, Any]:
        """Convert to OpenTelemetry span attributes."""
```

---

## Examples

### Example 1: Creating a Custom Primitive

- id:: workflow-primitive-custom-example

```python
from tta_dev_primitives import WorkflowPrimitive, WorkflowContext

class UpperCasePrimitive(WorkflowPrimitive[str, str]):
    """Convert input to uppercase."""

    async def execute(self, input_data: str, context: WorkflowContext) -> str:
        context.checkpoint("uppercase_start")
        result = input_data.upper()
        context.checkpoint("uppercase_complete")
        return result

# Use it
uppercase = UpperCasePrimitive()
context = WorkflowContext(workflow_id="demo")
result = await uppercase.execute("hello", context)
# Output: "HELLO"
```

### Example 2: Using LambdaPrimitive (Simple Wrapper)

- id:: workflow-primitive-lambda-example

```python
from tta_dev_primitives import LambdaPrimitive, WorkflowContext

# Quick transformation without defining a class
double = LambdaPrimitive(lambda x, ctx: x * 2)
add_ten = LambdaPrimitive(lambda x, ctx: x + 10)

# Compose using >> operator
workflow = double >> add_ten

context = WorkflowContext()
result = await workflow.execute(5, context)
# Output: 20 (5 * 2 = 10, then 10 + 10 = 20)
```

### Example 3: WorkflowContext with Tracing

- id:: workflow-primitive-context-tracing

```python
from tta_dev_primitives import WorkflowContext
import uuid

# Create context with correlation ID
context = WorkflowContext(
    workflow_id="user-signup-flow",
    session_id="session-abc123",
    correlation_id=str(uuid.uuid4()),
    metadata={
        "user_id": "user-789",
        "request_type": "signup"
    },
    tags={
        "environment": "production",
        "version": "1.0"
    }
)

# Execute workflow
result = await workflow.execute(input_data, context)

# Check timing
elapsed = context.elapsed_ms()
print(f"Workflow took {elapsed:.2f}ms")

# Checkpoints
for name, timestamp in context.checkpoints:
    print(f"Checkpoint: {name} at {timestamp}")
```

### Example 4: Child Context for Nested Workflows

- id:: workflow-primitive-child-context

```python
from tta_dev_primitives import WorkflowContext

# Parent workflow context
parent_context = WorkflowContext(
    workflow_id="main-workflow",
    correlation_id="req-12345",
    trace_id="abc123",
    span_id="span-001"
)

# Create child context for sub-workflow
child_context = parent_context.create_child_context()

# Child inherits trace context
assert child_context.trace_id == parent_context.trace_id
assert child_context.correlation_id == parent_context.correlation_id
assert child_context.parent_span_id == parent_context.span_id  # Parent's span becomes child's parent

# Execute sub-workflow with child context
sub_result = await sub_workflow.execute(data, child_context)
```

### Example 5: OpenTelemetry Integration

- id:: workflow-primitive-otel-integration

```python
from tta_dev_primitives import WorkflowPrimitive, WorkflowContext
from opentelemetry import trace

class TracedPrimitive(WorkflowPrimitive[str, str]):
    """Primitive with OpenTelemetry tracing."""

    async def execute(self, input_data: str, context: WorkflowContext) -> str:
        tracer = trace.get_tracer(__name__)

        with tracer.start_as_current_span("traced_operation") as span:
            # Add workflow context as span attributes
            for key, value in context.to_otel_context().items():
                span.set_attribute(key, value)

            # Add custom attributes
            span.set_attribute("input_length", len(input_data))

            # Do work
            result = input_data.upper()

            # Record event
            span.add_event("processing_complete")

            return result
```

---

## Composition Patterns

### Sequential Composition (>> operator)

- id:: workflow-primitive-sequential-composition

```python
# Chain primitives in sequence
workflow = primitive1 >> primitive2 >> primitive3

# Equivalent to:
from tta_dev_primitives import SequentialPrimitive
workflow = SequentialPrimitive([primitive1, primitive2, primitive3])
```

### Parallel Composition (| operator)

- id:: workflow-primitive-parallel-composition

```python
# Execute primitives in parallel
workflow = primitive1 | primitive2 | primitive3

# Equivalent to:
from tta_dev_primitives import ParallelPrimitive
workflow = ParallelPrimitive([primitive1, primitive2, primitive3])
```

### Mixed Composition

- id:: workflow-primitive-mixed-composition

```python
# Complex workflows mixing sequential and parallel
workflow = (
    input_validator >>
    (fast_llm | slow_llm | cached_llm) >>  # Parallel
    result_aggregator >>
    output_formatter
)
```

---

## Best Practices

### Creating Custom Primitives

✅ **Extend WorkflowPrimitive** with proper type hints
✅ **Use WorkflowContext** for state and tracing
✅ **Add checkpoints** for timing analysis
✅ **Handle errors gracefully** with try/except
✅ **Document input/output types** in docstrings
✅ **Keep execute() focused** on single responsibility

### Using WorkflowContext

✅ **Always pass context** through entire workflow
✅ **Use correlation_id** for request tracking
✅ **Add checkpoints** at key milestones
✅ **Store metadata** for debugging
✅ **Create child contexts** for nested workflows
✅ **Convert to OTEL attributes** for observability

### Don'ts

❌ Don't modify input_data in place (immutability)
❌ Don't use global state (use context.state)
❌ Don't ignore context parameter
❌ Don't forget async/await
❌ Don't swallow exceptions without logging

---

## Design Philosophy

### Why This Matters

- id:: workflow-primitive-philosophy

The WorkflowPrimitive design enables:

1. **Composability** - Small, focused primitives combine into complex workflows
2. **Reusability** - Same primitives work in different contexts
3. **Type Safety** - Compiler catches type mismatches at design time
4. **Testability** - Each primitive tests independently with MockPrimitive
5. **Observability** - Built-in context propagation for tracing

### Core Principles

**Single Responsibility** - Each primitive does one thing well

**Composition over Inheritance** - Build complex behavior by combining primitives

**Immutability** - Primitives don't modify input, they return new output

**Context Propagation** - WorkflowContext flows through entire execution chain

**Operator Overloading** - `>>` and `|` make composition intuitive

---

## Type Safety

### Generic Type Parameters

```python
from tta_dev_primitives import WorkflowPrimitive

# Input: str, Output: int
class ParseIntPrimitive(WorkflowPrimitive[str, int]):
    async def execute(self, input_data: str, context: WorkflowContext) -> int:
        return int(input_data)

# Input: int, Output: str
class FormatPrimitive(WorkflowPrimitive[int, str]):
    async def execute(self, input_data: int, context: WorkflowContext) -> str:
        return f"Result: {input_data}"

# Composition is type-safe
workflow: WorkflowPrimitive[str, str] = ParseIntPrimitive() >> FormatPrimitive()

# This works
result = await workflow.execute("42", context)  # "Result: 42"

# This would fail type check
# result = await workflow.execute(42, context)  # Type error!
```

---

## Related Content

### All Primitives

{{query (page-property type [[Primitive]])}}

### Core Primitives

{{query (and (page-property type [[Primitive]]) (page-property category [[Core]]))}}

### Extending WorkflowPrimitive

Related primitives that extend the base class:
- [[TTA.dev/Primitives/SequentialPrimitive]] - Sequential execution
- [[TTA.dev/Primitives/ParallelPrimitive]] - Parallel execution
- [[TTA.dev/Primitives/ConditionalPrimitive]] - Conditional branching
- [[TTA.dev/Primitives/RouterPrimitive]] - Dynamic routing
- [[TTA.dev/Primitives/RetryPrimitive]] - Retry with backoff
- [[TTA.dev/Primitives/FallbackPrimitive]] - Graceful degradation
- [[TTA.dev/Primitives/CachePrimitive]] - Result caching
- [[TTA.dev/Primitives/TimeoutPrimitive]] - Circuit breaker
- [[TTA.dev/Primitives/CompensationPrimitive]] - Saga pattern
- [[TTA.dev/Primitives/MockPrimitive]] - Testing mocks

---

## Advanced Topics

### Abstract Base Class

WorkflowPrimitive is an Abstract Base Class (ABC) requiring `execute()` implementation:

```python
from abc import ABC, abstractmethod

class WorkflowPrimitive(Generic[T, U], ABC):
    @abstractmethod
    async def execute(self, input_data: T, context: WorkflowContext) -> U:
        """Must be implemented by subclasses."""
        pass
```

### Operator Overloading Implementation

The magic methods enable operator syntax:

```python
def __rshift__(self, other):
    """Enable >> operator for sequential composition."""
    return SequentialPrimitive([self, other])

def __or__(self, other):
    """Enable | operator for parallel composition."""
    return ParallelPrimitive([self, other])
```

---

## Testing Custom Primitives

```python
import pytest
from tta_dev_primitives import WorkflowContext

@pytest.mark.asyncio
async def test_custom_primitive():
    primitive = MyCustomPrimitive()
    context = WorkflowContext(workflow_id="test")

    result = await primitive.execute("input", context)

    assert result == "expected output"
    assert len(context.checkpoints) > 0  # Check timing
```

---

## References

- **GitHub Source:** [`packages/tta-dev-primitives/src/tta_dev_primitives/core/base.py`](https://github.com/theinterneti/TTA.dev/blob/main/packages/tta-dev-primitives/src/tta_dev_primitives/core/base.py)
- **Tests:** [`packages/tta-dev-primitives/tests/test_base.py`](https://github.com/theinterneti/TTA.dev/blob/main/packages/tta-dev-primitives/tests/test_base.py)

---

**Created:** [[2025-10-30]]
**Last Updated:** [[2025-10-30]]
**Category:** [[Core]]
**Complexity:** [[High]]


---
**Logseq:** [[TTA.dev/_archive/Nested_copies/Framework/Logseq/Pages/Tta.dev___primitives___workflowprimitive]]
