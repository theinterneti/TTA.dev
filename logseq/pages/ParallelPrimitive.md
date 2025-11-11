# ParallelPrimitive

**Execute workflow steps concurrently, collecting results from all branches.**

## Overview

ParallelPrimitive is a core workflow composition primitive that executes multiple primitives concurrently, with all branches receiving the same input data.

**Import:**
```python
from tta_dev_primitives import ParallelPrimitive
```

## Usage

### Explicit Construction

```python
from tta_dev_primitives import ParallelPrimitive

workflow = ParallelPrimitive([
    branch1,
    branch2,
    branch3
])

results = await workflow.execute(input_data, context)
# Returns: [result1, result2, result3]
```

### Using | Operator (Preferred)

```python
# More readable parallel syntax
workflow = branch1 | branch2 | branch3

results = await workflow.execute(input_data, context)
```

## Execution Flow

```
        input_data
           ↓
    ┌──────┼──────┐
    ↓      ↓      ↓
 branch1 branch2 branch3
    ↓      ↓      ↓
 result1 result2 result3
    └──────┼──────┘
           ↓
    [result1, result2, result3]
```

## Features

### Concurrent Execution

- All branches execute simultaneously using `asyncio.gather()`
- Returns when all branches complete
- Exceptions in any branch can cancel others (optional)

### Context Propagation

- [[WorkflowContext]] shared across all branches
- Trace spans created for each branch
- Correlation IDs maintained

### Built-in Observability

- OpenTelemetry spans: `parallel.branch.{index}`
- Metrics: `parallel_branch_duration_seconds`
- Concurrent span creation

## Examples

### Multi-Source Data Fetch

```python
from tta_dev_primitives import ParallelPrimitive

# Fetch from multiple sources concurrently
fetch_workflow = (
    fetch_user_profile |
    fetch_recommendations |
    fetch_analytics |
    fetch_notifications
)

results = await fetch_workflow.execute({"user_id": 123}, context)
# Results arrive as soon as all 4 fetches complete
```

### Multi-Model Inference

```python
from tta_dev_primitives.llm import OpenAIPrimitive, AnthropicPrimitive

# Try multiple LLMs and compare
multi_llm = (
    OpenAIPrimitive(model="gpt-4o-mini") |
    AnthropicPrimitive(model="claude-3-haiku") |
    OllamaPrimitive(model="llama3.2")
)

responses = await multi_llm.execute({"prompt": "Explain AI"}, context)
# All 3 LLMs respond, then you can aggregate or select best
```

### With Aggregation

```python
# Parallel execution + aggregation
workflow = (
    (source1 | source2 | source3) >>
    aggregate_results >>
    format_output
)
```

## Common Patterns

### Fan-Out Query

```python
# Query multiple databases in parallel
query_workflow = (
    query_postgres |
    query_mongo |
    query_redis
) >> merge_results
```

### Multi-Provider Fallback

```python
from tta_dev_primitives.recovery import FallbackPrimitive

# Try multiple providers, use first success
workflow = FallbackPrimitive(
    primary=provider1,
    fallbacks=[
        provider2 | provider3,  # Try both in parallel
        local_cache
    ]
)
```

### A/B Testing

```python
# Run multiple variants in parallel
ab_test = (
    variant_a |
    variant_b |
    control
) >> analyze_results
```

## Comparison with SequentialPrimitive

| Feature | Parallel | Sequential |
|---------|----------|-----------|
| **Execution** | All at once | One at a time |
| **Data flow** | Same input for all | Output → Input |
| **Use case** | Fan-out | Pipeline |
| **Performance** | Faster (concurrent) | Slower (serial) |
| **Dependencies** | Independent steps | Steps depend on each other |

## Performance Considerations

### When to Use Parallel

- ✅ Independent operations
- ✅ Multiple data sources
- ✅ I/O-bound operations
- ✅ Multi-model inference

### When to Use Sequential

- ✅ Steps depend on previous results
- ✅ Order matters
- ✅ Data transformations
- ✅ State updates

### Performance Impact

```python
# Sequential: 3 seconds total (1s + 1s + 1s)
sequential = api1 >> api2 >> api3

# Parallel: 1 second total (max of 1s, 1s, 1s)
parallel = api1 | api2 | api3

# 3x speedup for independent operations
```

## Error Handling

### Default Behavior

- If any branch fails, all branches may be cancelled
- Exception propagates to caller

### With Recovery Patterns

```python
from tta_dev_primitives.recovery import RetryPrimitive, FallbackPrimitive

# Retry each branch independently
robust_parallel = (
    RetryPrimitive(branch1, max_retries=3) |
    RetryPrimitive(branch2, max_retries=3) |
    RetryPrimitive(branch3, max_retries=3)
)
```

## Related Primitives

### Composition
- [[SequentialPrimitive]] - Sequential execution
- [[ConditionalPrimitive]] - Conditional branching
- [[RouterPrimitive]] - Dynamic routing

### Recovery
- [[RetryPrimitive]] - Wrap branches with retry
- [[FallbackPrimitive]] - Fallback cascade
- [[TimeoutPrimitive]] - Timeout per branch

## Implementation

**Source:** `packages/tta-dev-primitives/src/tta_dev_primitives/core/parallel.py`

**Tests:** `packages/tta-dev-primitives/tests/test_parallel.py`

## Related Documentation

- [[PRIMITIVES CATALOG]] - Complete primitive reference
- [[TTA.dev/Primitives]] - All primitives
- [[TTA.dev/Examples]] - Working examples
- [[TTA.dev/Guides/Workflow Composition]] - Composition patterns

## Tags

primitive:: core
type:: composition
operator:: |

- [[Project Hub]]