# ParallelPrimitive

type:: [[Primitive]]
category:: [[Core Workflow]]
package:: [[TTA.dev/Packages/tta-dev-primitives]]
status:: [[Stable]]
version:: 1.0.0
test-coverage:: 100
complexity:: [[Medium]]
python-class:: `ParallelPrimitive`
import-path:: `from tta_dev_primitives import ParallelPrimitive`
related-primitives:: [[TTA.dev/Primitives/SequentialPrimitive]], [[TTA.dev/Primitives/RouterPrimitive]]

---

## Overview

- id:: parallel-primitive-overview
  Execute multiple primitives concurrently, where all primitives receive the same input and results are collected together.

  **Think of it as:** Fan-out pattern - one input splits into multiple parallel branches, then fan-in to collect results.

---

## Use Cases

- id:: parallel-primitive-use-cases
  - **Multi-LLM comparison:** Query GPT-4, Claude, and Llama simultaneously
  - **Data fetching:** Fetch from multiple APIs concurrently
  - **Parallel processing:** Process different aspects of data simultaneously
  - **A/B testing:** Run multiple variants concurrently
  - **Redundancy:** Send same request to multiple services for reliability

---

## Key Benefits

- id:: parallel-primitive-benefits
  - ✅ **Concurrent execution** - All branches run in parallel using asyncio.gather
  - ✅ **Type-safe composition** with `|` operator (natural and intuitive)
  - ✅ **Automatic context propagation** - Same [[WorkflowContext]] passed to all branches
  - ✅ **Built-in observability** - Parallel spans show concurrent execution
  - ✅ **Error handling** - Choose fail-fast or collect-all-results mode
  - ✅ **Performance boost** - Latency = max(branch_latencies), not sum

---

## API Reference

- id:: parallel-primitive-api

### Constructor

```python
ParallelPrimitive(
    primitives: list[WorkflowPrimitive[T, U]],
    fail_fast: bool = True
)
```

**Parameters:**
- `primitives`: List of workflow primitives to execute in parallel
- `fail_fast`: If True, raise on first error; if False, collect all results/errors

**Returns:** A new `ParallelPrimitive` instance

### Using the | Operator (Recommended)

```python
# Chain primitives naturally - much cleaner!
workflow = branch1 | branch2 | branch3

# Equivalent to:
workflow = ParallelPrimitive([branch1, branch2, branch3])
```

### Execution

```python
results = await workflow.execute(context, input_data)
# Returns: list of results from each branch
```

---

## Examples

### Multi-LLM Comparison

- id:: parallel-llm-comparison

```python
{{embed ((standard-imports))}}

# Query multiple LLMs in parallel
gpt4_query = LambdaPrimitive(lambda data, ctx: call_gpt4(data))
claude_query = LambdaPrimitive(lambda data, ctx: call_claude(data))
llama_query = LambdaPrimitive(lambda data, ctx: call_llama(data))

workflow = gpt4_query | claude_query | llama_query

context = WorkflowContext(correlation_id="llm-compare-001")
results = await workflow.execute(
    input_data={"prompt": "Explain quantum computing"},
    context=context
)

# Results: [gpt4_response, claude_response, llama_response]
# Execution time: max(gpt4_time, claude_time, llama_time)
```

### Parallel Data Fetching

- id:: parallel-data-fetching

```python
# Fetch from multiple APIs concurrently
fetch_user = LambdaPrimitive(lambda data, ctx: fetch_user_api(data["user_id"]))
fetch_orders = LambdaPrimitive(lambda data, ctx: fetch_orders_api(data["user_id"]))
fetch_preferences = LambdaPrimitive(lambda data, ctx: fetch_prefs_api(data["user_id"]))

workflow = fetch_user | fetch_orders | fetch_preferences

context = WorkflowContext(correlation_id="data-fetch-001")
results = await workflow.execute(
    input_data={"user_id": "user-123"},
    context=context
)

# Combine results
user_profile = {
    "user": results[0],
    "orders": results[1],
    "preferences": results[2]
}
```

---

## Composition Patterns

- id:: parallel-composition-patterns

### Sequential → Parallel → Sequential

```python
# Common pattern: preprocess, parallel process, aggregate
workflow = (
    input_validator >>
    data_fetcher >>
    (processor1 | processor2 | processor3) >>  # Parallel
    result_aggregator >>
    output_formatter
)
```

### Nested Parallel

```python
# Parallel within parallel
branch1 = sub_step1 | sub_step2
branch2 = sub_step3 | sub_step4

workflow = branch1 | branch2
# Result: All 4 sub-steps execute in parallel
```

### Parallel with Fallback

```python
from tta_dev_primitives.recovery import FallbackPrimitive

# Try all services in parallel, use first successful
fast_llm = FallbackPrimitive(primary=gpt4_mini, fallbacks=[])
quality_llm = FallbackPrimitive(primary=gpt4, fallbacks=[])
local_llm = FallbackPrimitive(primary=llama, fallbacks=[])

workflow = fast_llm | quality_llm | local_llm
```

---

## Error Handling

- id:: parallel-error-handling

### Fail-Fast Mode (Default)

```python
# Raises exception on first failure
workflow = ParallelPrimitive([step1, step2, step3], fail_fast=True)

try:
    results = await workflow.execute(input_data, context)
except Exception as e:
    # First failure stops all other branches
    logger.error(f"Workflow failed: {e}")
```

### Collect-All Mode

```python
# Collects all results, including errors
workflow = ParallelPrimitive([step1, step2, step3], fail_fast=False)

results = await workflow.execute(input_data, context)

# Results contains successes and exceptions
for i, result in enumerate(results):
    if isinstance(result, Exception):
        logger.error(f"Branch {i} failed: {result}")
    else:
        logger.info(f"Branch {i} succeeded: {result}")
```

---

## Related Content

### Works Well With

- [[TTA.dev/Primitives/SequentialPrimitive]] - Use sequential before/after parallel
- [[TTA.dev/Primitives/RouterPrimitive]] - Route to different parallel branches
- [[TTA.dev/Primitives/FallbackPrimitive]] - Add fallback to parallel branches
- [[TTA.dev/Primitives/CachePrimitive]] - Cache parallel branch results

### Used In Examples

{{query (and [[Example]] [[ParallelPrimitive]])}}

### Referenced By

{{query (and (mentions [[TTA.dev/Primitives/ParallelPrimitive]]))}}

---

## Performance Characteristics

- id:: parallel-performance

### Execution Time

- **Best case:** `max(branch_latencies)` - all branches same speed
- **Worst case:** `max(branch_latencies)` + overhead (~5-10ms)
- **Speedup:** Up to Nx faster than sequential (N = number of branches)

### Memory Usage

- **Memory:** O(N) where N = number of branches
- **Buffering:** Results buffered until all complete
- **Peak memory:** All branches running simultaneously

### Concurrency

- **asyncio.gather:** Uses asyncio for concurrent execution
- **True parallelism:** Only if branches do async I/O
- **CPU-bound:** Won't help with CPU-bound tasks (use ProcessPoolExecutor)

---

## Best Practices

✅ **Use for I/O-bound tasks** - Network calls, database queries, API calls
✅ **Same input type** - All branches must accept same input type
✅ **Independent branches** - Branches should not depend on each other
✅ **Consider fail_fast** - Use `fail_fast=False` if you need all results
✅ **Aggregate results** - Follow with aggregation step to combine results

❌ **Don't use for CPU-bound** - Won't provide speedup for pure computation
❌ **Don't share state** - Branches shouldn't modify shared mutable state
❌ **Don't assume order** - Results in list, but execution order non-deterministic

---

## Testing

### Example Test

```python
import pytest
from tta_dev_primitives import ParallelPrimitive, WorkflowContext
from tta_dev_primitives.testing import MockPrimitive

@pytest.mark.asyncio
async def test_parallel_execution():
    # Create mock primitives with delays
    mock1 = MockPrimitive(return_value="result1", delay=0.1)
    mock2 = MockPrimitive(return_value="result2", delay=0.1)
    mock3 = MockPrimitive(return_value="result3", delay=0.1)

    # Compose workflow
    workflow = mock1 | mock2 | mock3

    # Execute
    context = WorkflowContext(correlation_id="test-001")
    start = time.time()
    results = await workflow.execute(input_data="test", context=context)
    duration = time.time() - start

    # Verify parallel execution (should take ~0.1s, not 0.3s)
    assert results == ["result1", "result2", "result3"]
    assert duration < 0.2  # Parallel, not sequential
    assert all(m.call_count == 1 for m in [mock1, mock2, mock3])
```

---

## Observability

### Tracing

Parallel branches create sibling spans:

```
workflow_execution (parent span)
├── branch1 (sibling span) ---
├── branch2 (sibling span) --- All concurrent
└── branch3 (sibling span) ---
```

### Metrics

- `workflow.parallel.duration` - Total parallel execution time
- `workflow.parallel.branch_count` - Number of parallel branches
- `workflow.parallel.success_rate` - Percentage of successful branches

---

## Metadata

**Source Code:** [parallel.py](https://github.com/theinterneti/TTA.dev/blob/main/packages/tta-dev-primitives/src/tta_dev_primitives/core/parallel.py)
**Tests:** [test_parallel.py](https://github.com/theinterneti/TTA.dev/blob/main/packages/tta-dev-primitives/tests/test_parallel.py)
**Examples:** [parallel_execution.py](https://github.com/theinterneti/TTA.dev/blob/main/packages/tta-dev-primitives/examples/parallel_execution.py)

**Created:** [[2025-10-30]]
**Last Updated:** [[2025-10-30]]
**Test Coverage:** 100%
**Status:** [[Stable]] - Production Ready
