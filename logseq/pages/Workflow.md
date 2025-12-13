# Workflow

**Tag page for workflow patterns, composition, and orchestration**

---

## Overview

A **workflow** in TTA.dev is a composition of primitives that processes data through a series of operations. Workflows are:
- **Composable** - Built from primitive building blocks
- **Type-safe** - Full generic type support
- **Observable** - Automatic tracing and metrics
- **Testable** - Easy to mock and test

**Key operators:**
- `>>` - Sequential composition (step-by-step)
- `|` - Parallel composition (concurrent execution)

**See:** [[TTA.dev/Concepts/Composition]], [[Primitive]]

---

## Workflow Patterns

### Sequential Workflows

**Execute operations in order, passing output to input**

```python
from tta_dev_primitives import SequentialPrimitive

# Using >> operator
workflow = step1 >> step2 >> step3

# Explicit construction
workflow = SequentialPrimitive([step1, step2, step3])
```

**Use Cases:**
- Linear data pipelines
- ETL workflows
- RAG pipelines (embed → search → rerank → generate)
- Multi-stage processing

**See:** [[TTA Primitives/SequentialPrimitive]], [[TTA.dev/Patterns/Sequential Workflow]]

---

### Parallel Workflows

**Execute operations concurrently, collect results**

```python
from tta_dev_primitives import ParallelPrimitive

# Using | operator
workflow = branch1 | branch2 | branch3

# Explicit construction
workflow = ParallelPrimitive([branch1, branch2, branch3])
```

**Use Cases:**
- Multi-provider API calls
- Parallel data processing
- Fan-out/fan-in patterns
- Independent operations

**See:** [[TTA Primitives/ParallelPrimitive]], [[TTA.dev/Patterns/Parallel Execution]]

---

### Conditional Workflows

**Branch execution based on runtime conditions**

```python
from tta_dev_primitives import ConditionalPrimitive

workflow = ConditionalPrimitive(
    condition=lambda data, ctx: data["size"] > 1000,
    then_primitive=slow_processor,
    else_primitive=fast_processor
)
```

**Use Cases:**
- Dynamic routing
- Complexity-based processing
- A/B testing
- Feature flags

**See:** [[TTA Primitives/ConditionalPrimitive]]

---

### Router Workflows

**Dynamic routing to multiple destinations**

```python
from tta_dev_primitives.core import RouterPrimitive

workflow = RouterPrimitive(
    routes={
        "fast": gpt4_mini,
        "balanced": claude_sonnet,
        "quality": gpt4
    },
    router_fn=select_route,
    default="balanced"
)
```

**Use Cases:**
- LLM tier selection (fast/balanced/quality)
- Load balancing
- Multi-model coordination
- Cost optimization

**See:** [[TTA Primitives/RouterPrimitive]]

---

### Mixed Workflows

**Combine sequential and parallel patterns**

```python
# Sequential → Parallel → Sequential
workflow = (
    input_processor >>
    (fast_path | quality_path | cached_path) >>
    aggregator >>
    output_formatter
)
```

**Use Cases:**
- Complex data pipelines
- Multi-stage processing with parallelism
- Hybrid workflows

**See:** [[TTA.dev/Concepts/Composition]]

---

## Pages Tagged with #Workflow

{{query (page-tags [[Workflow]])}}

---

## Workflow Composition

### Basic Composition

**Sequential:**
```python
# Data flows through steps
result = await (step1 >> step2 >> step3).execute(input_data, context)
```

**Parallel:**
```python
# All branches get same input, results collected
results = await (branch1 | branch2 | branch3).execute(input_data, context)
```

---

### Nested Composition

**Compose workflows of workflows:**

```python
# Create sub-workflows
preprocessing = clean_data >> normalize_data >> validate_data
processing = transform_data >> enrich_data
postprocessing = aggregate_results >> format_output

# Combine into main workflow
main_workflow = preprocessing >> processing >> postprocessing
```

---

### Composition with Recovery

**Add resilience to workflows:**

```python
from tta_dev_primitives.recovery import (
    RetryPrimitive,
    FallbackPrimitive,
    TimeoutPrimitive
)

# Layered recovery
workflow = (
    TimeoutPrimitive(preprocessor, timeout_seconds=10) >>
    RetryPrimitive(processor, max_retries=3) >>
    FallbackPrimitive(
        primary=expensive_step,
        fallbacks=[cheap_step, cached_step]
    )
)
```

**See:** [[Recovery]], [[TTA.dev/Patterns/Error Handling]]

---

### Composition with Caching

**Optimize performance:**

```python
from tta_dev_primitives.performance import CachePrimitive

# Cache expensive operations
workflow = (
    input_validator >>
    CachePrimitive(expensive_llm_call, ttl_seconds=3600) >>
    result_formatter
)
```

**See:** [[Performance]], [[TTA.dev/Patterns/Caching]]

---

## Workflow Context

**Every workflow execution receives context for state and tracing:**

```python
from tta_dev_primitives import WorkflowContext

context = WorkflowContext(
    correlation_id="req-123",
    workflow_id="my-workflow",
    data={"user_id": "user-789"}
)

result = await workflow.execute(input_data, context)
```

**Context provides:**
- `correlation_id` - Request tracking across services
- `workflow_id` - Workflow identification
- `metadata` - Custom data dictionary
- `parent_span` - OpenTelemetry trace context

**See:** [[WorkflowContext]], [[TTA.dev/Concepts/Context Propagation]]

---

## Real-World Workflow Examples

### Example 1: RAG Pipeline

```python
from tta_dev_primitives import SequentialPrimitive
from tta_dev_primitives.performance import CachePrimitive

rag_workflow = (
    embed_query >>
    CachePrimitive(search_vectors, ttl_seconds=3600) >>
    rerank_results >>
    generate_response
)
```

**Flow:**
1. Embed user query → vector
2. Search vector database (cached)
3. Rerank by relevance
4. Generate final response

---

### Example 2: Multi-Provider LLM

```python
from tta_dev_primitives.recovery import FallbackPrimitive
from tta_dev_primitives.core import RouterPrimitive

llm_workflow = FallbackPrimitive(
    primary=RouterPrimitive(
        routes={"fast": gpt4_mini, "quality": gpt4},
        router_fn=select_by_complexity
    ),
    fallbacks=[anthropic_claude, google_gemini, cached_response]
)
```

**Flow:**
1. Route to appropriate GPT-4 tier
2. If unavailable → Claude
3. If unavailable → Gemini
4. If unavailable → Cached response

---

### Example 3: Parallel Data Processing

```python
from tta_dev_primitives import ParallelPrimitive

data_pipeline = (
    fetch_data >>
    ParallelPrimitive([
        process_text,
        process_images,
        process_metadata
    ]) >>
    merge_results >>
    store_output
)
```

**Flow:**
1. Fetch data from source
2. Process 3 data types concurrently
3. Merge results
4. Store final output

---

### Example 4: ETL Workflow

```python
# Extract → Transform → Load
etl_workflow = (
    # Extract
    fetch_from_api >>
    parse_response >>

    # Transform
    (
        clean_data |
        enrich_data |
        validate_data
    ) >>
    merge_transformations >>

    # Load
    RetryPrimitive(
        FallbackPrimitive(
            primary=write_to_primary_db,
            fallbacks=[write_to_backup_db]
        ),
        max_retries=3
    )
)
```

---

## Workflow Best Practices

### ✅ DO

**Small, Focused Steps:**
```python
# Good: Each step has clear purpose
workflow = (
    validate_input >>
    extract_features >>
    process_features >>
    format_output
)
```

**Type Hints:**
```python
class MyWorkflow(WorkflowPrimitive[InputModel, OutputModel]):
    """Type-safe workflow."""
    pass
```

**Error Handling at Right Level:**
```python
# Good: Retry at appropriate step
workflow = (
    step1 >>
    RetryPrimitive(flaky_step2) >>  # Only retry flaky step
    step3
)
```

**Descriptive Names:**
```python
# Good: Clear what workflow does
user_registration_workflow = (
    validate_email >>
    create_account >>
    send_welcome_email
)
```

---

### ❌ DON'T

**Don't Break Composition:**
```python
# Bad: Side effects break chain
async def bad_step(data, context):
    result = await process(data)
    await some_side_effect()  # ❌ Hidden side effect
    return result
```

**Don't Skip Context:**
```python
# Bad: Missing context
result = await workflow.execute(data, None)  # ❌ No context
```

**Don't Create God Workflows:**
```python
# Bad: Too many responsibilities
mega_workflow = (
    step1 >> step2 >> step3 >> step4 >> step5 >>
    step6 >> step7 >> step8 >> step9 >> step10
)

# Better: Break into sub-workflows
preprocessing = step1 >> step2 >> step3
processing = step4 >> step5 >> step6
postprocessing = step7 >> step8 >> step9

workflow = preprocessing >> processing >> postprocessing
```

---

## Workflow Observability

**All workflows have automatic observability:**

### Tracing

```python
# Automatic OpenTelemetry spans
with tracer.start_as_current_span("workflow_execution"):
    result = await workflow.execute(data, context)

# Each primitive creates child spans
# Context propagates through entire workflow
```

### Metrics

```promql
# Sequential workflow metrics
sequential_step_duration_seconds{step="step1"}
sequential_total_duration_seconds

# Parallel workflow metrics
parallel_branch_duration_seconds{branch="branch1"}
parallel_total_duration_seconds
```

### Logging

```python
# Structured logging with correlation IDs
logger.info(
    "workflow_complete",
    correlation_id=context.correlation_id,
    duration_ms=duration,
    steps_completed=3
)
```

**See:** [[TTA.dev/Observability]], [[InstrumentedPrimitive]]

---

## Workflow Testing

### Unit Testing

```python
from tta_dev_primitives.testing import MockPrimitive

@pytest.mark.asyncio
async def test_workflow():
    # Mock individual steps
    mock_step1 = MockPrimitive(return_value={"intermediate": "result"})
    mock_step2 = MockPrimitive(return_value={"final": "result"})

    workflow = mock_step1 >> mock_step2
    result = await workflow.execute(input_data, context)

    assert mock_step1.call_count == 1
    assert mock_step2.call_count == 1
    assert result["final"] == "result"
```

### Integration Testing

```python
@pytest.mark.asyncio
async def test_end_to_end_workflow():
    # Test real workflow with all components
    workflow = (
        validate_input >>
        process_data >>
        format_output
    )

    result = await workflow.execute(test_input, context)

    # Verify end-to-end behavior
    assert result["status"] == "success"
    assert "output" in result
```

**See:** [[Testing]], [[TTA.dev/Testing Strategy]]

---

## Workflow Patterns by Use Case

### Data Processing

- [[TTA.dev/Patterns/Sequential Workflow]] - Linear pipelines
- [[TTA.dev/Patterns/Parallel Execution]] - Parallel processing
- ETL patterns

### AI/LLM Workflows

- [[TTA.dev/Patterns/Router]] - Model selection
- RAG pipelines
- Multi-agent coordination

### Error Handling

- [[TTA.dev/Patterns/Error Handling]] - Recovery patterns
- [[Recovery]] - Resilience strategies

### Performance

- [[TTA.dev/Patterns/Caching]] - Caching strategies
- [[Performance]] - Optimization techniques

---

## Related Concepts

- [[Primitive]] - Building blocks
- [[TTA.dev/Concepts/Composition]] - Composition patterns
- [[Recovery]] - Error handling
- [[Performance]] - Optimization
- [[Testing]] - Testing strategies
- [[Production]] - Production patterns

---

## Documentation

- [[TTA.dev/Patterns]] - Pattern documentation
- [[TTA.dev/Examples]] - Working examples
- [[PRIMITIVES_CATALOG]] - Complete primitive reference
- [[AGENTS]] - Agent instructions
- [[README]] - Project overview

---

**Tags:** #workflow #composition #orchestration #patterns #index-page

**Last Updated:** 2025-11-05
**Maintained by:** TTA.dev Team


---
**Logseq:** [[TTA.dev/Logseq/Pages/Workflow]]
