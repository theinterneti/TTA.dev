# SequentialPrimitive

**Execute workflow steps in sequence, passing output as input to next step.**

## Overview

SequentialPrimitive is a core workflow composition primitive that executes multiple primitives in order, with each step's output becoming the next step's input.

**Import:**
```python
from tta_dev_primitives import SequentialPrimitive
```

## Usage

### Explicit Construction

```python
from tta_dev_primitives import SequentialPrimitive

workflow = SequentialPrimitive([
    step1,
    step2,
    step3
])

result = await workflow.execute(input_data, context)
```

### Using >> Operator (Preferred)

```python
# More readable chaining syntax
workflow = step1 >> step2 >> step3

result = await workflow.execute(input_data, context)
```

## Execution Flow

```
input_data
  ↓
step1.execute(input_data, context)
  ↓
result1
  ↓
step2.execute(result1, context)
  ↓
result2
  ↓
step3.execute(result2, context)
  ↓
final_output
```

## Features

### Automatic Context Propagation

- [[WorkflowContext]] passed through all steps
- Correlation IDs maintained
- Trace spans created for each step

### Built-in Observability

- OpenTelemetry spans: `sequential.step.{name}`
- Metrics: `sequential_step_duration_seconds`
- Structured logging for each step

### Type Safety

```python
from tta_dev_primitives import SequentialPrimitive, WorkflowPrimitive

# Type hints ensure compatibility
step1: WorkflowPrimitive[Input, Intermediate]
step2: WorkflowPrimitive[Intermediate, Output]

# ✅ Types compatible
workflow = step1 >> step2

# ❌ Types incompatible - caught by type checker
workflow = step1 >> incompatible_step
```

## Examples

### Basic RAG Pipeline

```python
from tta_dev_primitives import SequentialPrimitive

rag_pipeline = (
    retrieve_documents >>
    rerank_results >>
    generate_response >>
    format_output
)
```

### With Recovery Patterns

```python
from tta_dev_primitives.recovery import RetryPrimitive, FallbackPrimitive

# Retry on each step, fallback for whole pipeline
workflow = (
    RetryPrimitive(validate_input, max_retries=3) >>
    FallbackPrimitive(
        primary=expensive_llm,
        fallbacks=[cheap_llm, cached_response]
    ) >>
    RetryPrimitive(store_result, max_retries=2)
)
```

## Common Patterns

### Data Transformation Pipeline

```python
workflow = (
    extract_data >>
    transform_data >>
    validate_data >>
    load_data
)
```

### Multi-Stage LLM Workflow

```python
workflow = (
    classify_intent >>
    route_to_expert >>
    generate_response >>
    validate_output >>
    format_for_user
)
```

## Comparison with ParallelPrimitive

| Feature | Sequential | Parallel |
|---------|-----------|----------|
| **Execution** | One at a time | All at once |
| **Data flow** | Output → Input | Same input for all |
| **Use case** | Pipeline | Fan-out |
| **Performance** | Slower (serial) | Faster (concurrent) |
| **Dependencies** | Steps depend on each other | Independent steps |

## Performance Considerations

### When to Use Sequential

- ✅ Steps depend on previous results
- ✅ Order matters
- ✅ Data transformations
- ✅ State updates

### When to Use Parallel

- ✅ Independent operations
- ✅ Multiple data sources
- ✅ Fan-out queries
- ✅ Performance critical

## Related Primitives

### Composition
- [[ParallelPrimitive]] - Concurrent execution
- [[ConditionalPrimitive]] - Conditional branching
- [[RouterPrimitive]] - Dynamic routing

### Recovery
- [[RetryPrimitive]] - Wrap steps with retry
- [[FallbackPrimitive]] - Fallback for whole sequence
- [[TimeoutPrimitive]] - Timeout protection

## Implementation

**Source:** `packages/tta-dev-primitives/src/tta_dev_primitives/core/sequential.py`

**Tests:** `packages/tta-dev-primitives/tests/test_sequential.py`

## Related Documentation

- [[PRIMITIVES CATALOG]] - Complete primitive reference
- [[TTA.dev/Primitives]] - All primitives
- [[TTA.dev/Examples]] - Working examples
- [[TTA.dev/Guides/Workflow Composition]] - Composition patterns

## Tags

primitive:: core
type:: composition
operator:: >>
