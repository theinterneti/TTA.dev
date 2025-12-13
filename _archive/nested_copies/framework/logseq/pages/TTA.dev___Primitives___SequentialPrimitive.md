# SequentialPrimitive

type:: [[Primitive]]
category:: [[Core Workflow]]
package:: [[TTA.dev/Packages/tta-dev-primitives]]
status:: [[Stable]]
version:: 1.0.0
test-coverage:: 100
complexity:: [[Low]]
python-class:: `SequentialPrimitive`
import-path:: `from tta_dev_primitives import SequentialPrimitive`
related-primitives:: [[TTA.dev/Primitives/ParallelPrimitive]], [[TTA.dev/Primitives/ConditionalPrimitive]], [[TTA.dev/Primitives/RouterPrimitive]]

---

## Overview

- id:: sequential-primitive-overview
  Execute primitives in sequence, where each primitive's output becomes the next primitive's input. The fundamental building block for linear workflows.

  **Think of it as:** A pipeline where data flows through each step one at a time.

---

## Use Cases

- id:: sequential-primitive-use-cases
  - **Data pipelines:** Input → Validate → Process → Transform → Output
  - **LLM chains:** Build Prompt → Generate Response → Refine Content → Format Output
  - **API workflows:** Fetch Data → Validate Schema → Store → Send Notification
  - **Content processing:** Load Document → Extract Text → Analyze Sentiment → Generate Summary

---

## Key Benefits

- id:: sequential-primitive-benefits
  - ✅ **Type-safe composition** with `>>` operator (natural and intuitive)
  - ✅ **Automatic context propagation** via [[WorkflowContext]]
  - ✅ **Built-in observability** - automatic span creation for each step
  - ✅ **Error propagation** - fails fast on any error with full stack trace
  - ✅ **Memory efficient** - processes one step at a time, no buffering

---

## API Reference

- id:: sequential-primitive-api

### Constructor

```python
SequentialPrimitive(
    primitives: list[WorkflowPrimitive[Any, Any]]
)
```

**Parameters:**
- `primitives`: List of workflow primitives to execute in order

**Returns:** A new `SequentialPrimitive` instance

### Using the >> Operator (Recommended)

```python
# Chain primitives naturally - much cleaner!
workflow = step1 >> step2 >> step3

# Equivalent to:
workflow = SequentialPrimitive([step1, step2, step3])
```

### Execution

```python
result = await workflow.execute(context, input_data)
```

---

## Examples

### Basic Sequential Workflow

- id:: sequential-basic-example

```python
{{embed ((standard-imports))}}

# Define three simple steps
async def step1(data, context):
    return {"stage": 1, "value": data * 2}

async def step2(data, context):
    return {"stage": 2, "value": data["value"] + 10}

async def step3(data, context):
    return {"stage": 3, "value": data["value"] ** 2}

# Compose with >> operator
workflow = (
    LambdaPrimitive(step1) >>
    LambdaPrimitive(step2) >>
    LambdaPrimitive(step3)
)

# Execute
context = WorkflowContext(correlation_id="example-001")
result = await workflow.execute(input_data=5, context=context)

# Result: {"stage": 3, "value": 400}
# Calculation: ((5*2)+10)^2 = (10+10)^2 = 20^2 = 400
```

### LLM Content Pipeline

- id:: sequential-llm-chain

```python
from tta_dev_primitives import SequentialPrimitive, LambdaPrimitive

# Real-world: LLM content generation pipeline
workflow = (
    prompt_builder >>           # Build prompt from user input
    llm_generator >>            # Generate content with LLM
    content_refiner >>          # Refine and improve output
    grammar_checker >>          # Check grammar and style
    output_formatter            # Format for final delivery
)

context = WorkflowContext(
    correlation_id="content-gen-001",
    data={"user_id": "user-123"}
)

result = await workflow.execute(
    input_data={"topic": "AI workflows", "length": "500 words"},
    context=context
)
```

### Data Validation Pipeline

- id:: sequential-validation-pipeline

```python
# Multi-stage data validation workflow
workflow = (
    schema_validator >>         # Validate JSON schema
    business_rule_validator >>  # Check business logic
    security_scanner >>         # Scan for security issues
    data_enricher >>            # Add additional metadata
    database_writer             # Store validated data
)

result = await workflow.execute(
    input_data=raw_data,
    context=context
)
```

---

## Composition Patterns

- id:: sequential-composition-patterns

### Sequential → Parallel

```python
# Linear steps followed by parallel processing
workflow = (
    input_validator >>
    data_fetcher >>
    (processor1 | processor2 | processor3) >>  # Parallel processing
    result_aggregator
)
```

### Nested Sequential Workflows

```python
# Sub-workflows as steps
preprocessing = step1 >> step2 >> step3
main_processing = step4 >> step5 >> step6
postprocessing = step7 >> step8 >> step9

workflow = preprocessing >> main_processing >> postprocessing
```

### Sequential with Error Recovery

```python
from tta_dev_primitives.recovery import RetryPrimitive, FallbackPrimitive

# Add retry to any step
reliable_step = RetryPrimitive(
    primitive=unreliable_api_call,
    max_retries=3,
    backoff_strategy="exponential"
)

workflow = step1 >> reliable_step >> step3
```

---

## Related Content

### Works Well With

- [[TTA.dev/Primitives/ParallelPrimitive]] - Follow sequential with parallel processing
- [[TTA.dev/Primitives/RouterPrimitive]] - Route to different sequential chains
- [[TTA.dev/Primitives/RetryPrimitive]] - Wrap sequential steps for resilience
- [[TTA.dev/Primitives/ConditionalPrimitive]] - Add branching logic within sequence

### Used In Examples

{{query (and [[Example]] [[SequentialPrimitive]])}}

### Referenced By

{{query (and (mentions [[TTA.dev/Primitives/SequentialPrimitive]]))}}

---

## Implementation Notes

- id:: sequential-implementation-notes

### Performance Characteristics

- **Execution:** Sequential (one step at a time)
- **Memory:** O(1) - no buffering, processes immediately
- **Latency:** Sum of all step latencies
- **Observability overhead:** ~1-2ms per step for span creation

### Best Practices

✅ **Keep steps focused** - Each step should do one thing well (Single Responsibility)
✅ **Use WorkflowContext** - Pass shared state via context, not global variables
✅ **Add retry logic** - Wrap with [[TTA.dev/Primitives/RetryPrimitive]] for unreliable operations
✅ **Monitor spans** - Each step creates a child span for observability
✅ **Type hints** - Use generic types for type safety: `WorkflowPrimitive[InputType, OutputType]`

### Edge Cases

⚠️ **Empty primitives list** - Raises `ValueError` at construction time
⚠️ **Type mismatches** - Output of step N must match input type of step N+1
⚠️ **Exceptions** - Any step failure stops workflow immediately (fail-fast)
⚠️ **Context propagation** - Context is passed to all steps, immutable by default

---

## Testing

### Example Test

```python
import pytest
from tta_dev_primitives import SequentialPrimitive, LambdaPrimitive, WorkflowContext
from tta_dev_primitives.testing import MockPrimitive

@pytest.mark.asyncio
async def test_sequential_workflow():
    # Create mock primitives
    mock_step1 = MockPrimitive(return_value={"step": 1, "value": 10})
    mock_step2 = MockPrimitive(return_value={"step": 2, "value": 20})
    mock_step3 = MockPrimitive(return_value={"step": 3, "value": 30})

    # Compose workflow
    workflow = mock_step1 >> mock_step2 >> mock_step3

    # Execute
    context = WorkflowContext(correlation_id="test-001")
    result = await workflow.execute(input_data="test", context=context)

    # Verify
    assert result["value"] == 30
    assert mock_step1.call_count == 1
    assert mock_step2.call_count == 1
    assert mock_step3.call_count == 1
```

---

## Observability

### Tracing

Each step creates a child span:

```
workflow_execution (parent span)
├── step1 (child span)
├── step2 (child span)
└── step3 (child span)
```

### Metrics

- `workflow.execution.duration` - Total execution time
- `workflow.step.duration` - Per-step execution time
- `workflow.execution.count` - Execution count by status

### Logging

```python
# Structured logs for each step
logger.info(
    "step_executed",
    step_name="validator",
    duration_ms=12.34,
    status="success"
)
```

---

## Comparison to Alternatives

### vs Manual Async/Await

❌ **Manual:**
```python
async def workflow(input_data):
    result1 = await step1(input_data)
    result2 = await step2(result1)
    return await step3(result2)
```

✅ **SequentialPrimitive:**
```python
workflow = step1 >> step2 >> step3
result = await workflow.execute(input_data, context)
```

**Benefits:** Automatic observability, error handling, context propagation

### vs asyncio.gather (Sequential)

❌ **asyncio.gather (sequential ordering):**
```python
results = []
for step in steps:
    result = await step(results[-1] if results else input_data)
    results.append(result)
```

✅ **SequentialPrimitive:**
```python
workflow = SequentialPrimitive(steps)
result = await workflow.execute(input_data, context)
```

**Benefits:** Cleaner code, type safety, built-in observability

---

## Metadata

**Source Code:** [sequential.py](https://github.com/theinterneti/TTA.dev/blob/main/packages/tta-dev-primitives/src/tta_dev_primitives/core/sequential.py)
**Tests:** [test_sequential.py](https://github.com/theinterneti/TTA.dev/blob/main/packages/tta-dev-primitives/tests/test_sequential.py)
**Examples:** [basic_sequential.py](https://github.com/theinterneti/TTA.dev/blob/main/packages/tta-dev-primitives/examples/basic_sequential.py)

**Created:** [[2025-10-30]]
**Last Updated:** [[2025-10-30]]
**Test Coverage:** 100%
**Status:** [[Stable]] - Production Ready


---
**Logseq:** [[TTA.dev/_archive/Nested_copies/Framework/Logseq/Pages/Tta.dev___primitives___sequentialprimitive]]
