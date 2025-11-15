# Workflow Composition

type:: [[Guide]]
category:: [[Advanced Topics]]
difficulty:: [[Intermediate]]
estimated-time:: 30 minutes
target-audience:: [[Developers]], [[AI Engineers]]

---

## Overview

- id:: workflow-composition-overview
  **Workflow Composition** is the art of combining simple primitives into powerful AI systems using TTA.dev's intuitive operators (`>>` for sequential, `|` for parallel). This guide teaches you advanced composition patterns, common architectures, and best practices for building production-ready workflows.

---

## Prerequisites

{{embed ((prerequisites-full))}}

**Should have read:**
- [[TTA.dev/Guides/Agentic Primitives]] - Core concepts
- [[TTA.dev/Guides/Getting Started]] - Basic setup

**Should understand:**
- Sequential vs parallel execution
- How operators work (`>>`, `|`)
- WorkflowContext usage

---

## The Two Fundamental Operators

### Sequential: `>>` (Then)

- id:: workflow-composition-sequential-operator

**Pattern:** `A >> B >> C`

**Meaning:** "Execute A, **then** use A's output as B's input, **then** use B's output as C's input"

**When to use:**
- Steps depend on previous results
- Data flows through transformations
- Each step adds/modifies data

**Example:**

```python
# Data flows: input → validate → process → format → output
workflow = (
    input_validator >>    # Output: {"valid": true, "data": {...}}
    data_processor >>     # Output: {"processed": true, "result": {...}}
    result_formatter >>   # Output: {"formatted": "...", "metadata": {...}}
    output_generator      # Output: final result
)
```

### Parallel: `|` (And)

- id:: workflow-composition-parallel-operator

**Pattern:** `A | B | C`

**Meaning:** "Execute A **and** B **and** C concurrently with same input"

**When to use:**
- Steps are independent
- Can run simultaneously
- Want to compare/aggregate results

**Example:**

```python
# All receive same input, run concurrently
workflow = (
    gpt4_analysis |       # Analyzes input
    claude_analysis |     # Also analyzes input (same data)
    local_llm_analysis    # Also analyzes input (same data)
)
# Returns: [gpt4_result, claude_result, local_result]
```

---

## Composition Patterns

### Pattern 1: Linear Pipeline

- id:: workflow-composition-linear-pipeline

**Structure:** `A >> B >> C >> D`

**Use case:** Each step processes previous step's output

```python
from tta_dev_primitives import SequentialPrimitive, LambdaPrimitive

# Text processing pipeline
workflow = (
    LambdaPrimitive(lambda text, ctx: text.strip()) >>        # Clean whitespace
    LambdaPrimitive(lambda text, ctx: text.lower()) >>        # Lowercase
    LambdaPrimitive(lambda text, ctx: tokenize(text)) >>      # Tokenize
    LambdaPrimitive(lambda tokens, ctx: analyze(tokens))      # Analyze
)

result = await workflow.execute("  Hello World  ", context)
# "hello world" → ["hello", "world"] → analysis
```

### Pattern 2: Fan-Out Aggregation

- id:: workflow-composition-fan-out

**Structure:** `A >> (B | C | D) >> E`

**Use case:** Process data through multiple paths, then combine

```python
# LLM comparison: Ask 3 LLMs, compare responses
workflow = (
    input_processor >>                           # Prepare prompt
    (gpt4 | claude | llama) >>                  # Ask all 3 LLMs
    LambdaPrimitive(lambda results, ctx: {      # Aggregate
        "gpt4": results[0],
        "claude": results[1],
        "llama": results[2],
        "consensus": find_consensus(results)
    })
)
```

### Pattern 3: Conditional Branching

- id:: workflow-composition-conditional-branch

**Structure:** `A >> ConditionalPrimitive(condition, B, C) >> D`

**Use case:** Route based on data characteristics

```python
from tta_dev_primitives import ConditionalPrimitive

def is_complex(data: str, ctx: WorkflowContext) -> bool:
    return len(data) > 500 or "technical" in data.lower()

# Router: Simple queries → fast LLM, complex → powerful LLM
workflow = (
    input_validator >>
    ConditionalPrimitive(
        condition=is_complex,
        then_primitive=gpt4,          # Complex queries
        else_primitive=gpt4_mini      # Simple queries
    ) >>
    output_formatter
)
```

### Pattern 4: Multi-Stage with Recovery

- id:: workflow-composition-recovery

**Structure:** Combine sequential with retry/fallback/cache

```python
from tta_dev_primitives.recovery import RetryPrimitive, FallbackPrimitive
from tta_dev_primitives.performance import CachePrimitive

# Stage 1: Fetch data (with retry)
fetch_data = RetryPrimitive(
    LambdaPrimitive(lambda req, ctx: api_call(req)),
    max_retries=3
)

# Stage 2: Process (with cache and fallback)
process_data = CachePrimitive(
    FallbackPrimitive(
        primary=expensive_processor,
        fallbacks=[cheap_processor]
    ),
    ttl_seconds=3600
)

# Stage 3: Format (simple)
format_output = LambdaPrimitive(lambda data, ctx: format_for_ui(data))

# Complete workflow
workflow = fetch_data >> process_data >> format_output
```

### Pattern 5: Parallel Independent Tasks

- id:: workflow-composition-parallel-independent

**Structure:** `(A | B | C)` with different operations

```python
# Parallel data enrichment
enrich_with_user_data = LambdaPrimitive(lambda id, ctx: fetch_user(id))
enrich_with_preferences = LambdaPrimitive(lambda id, ctx: fetch_preferences(id))
enrich_with_history = LambdaPrimitive(lambda id, ctx: fetch_history(id))

# Fetch all data in parallel
workflow = (
    enrich_with_user_data |
    enrich_with_preferences |
    enrich_with_history
)

results = await workflow.execute(user_id, context)
# [user_data, preferences, history] - all fetched concurrently
```

### Pattern 6: Nested Conditionals (Decision Tree)

- id:: workflow-composition-decision-tree

**Structure:** Conditionals within conditionals

```python
# Authentication + Authorization flow
is_authenticated = ConditionalPrimitive(
    condition=lambda data, ctx: data.get("token") is not None,
    then_primitive=validate_token,
    else_primitive=return_401
)

has_premium = ConditionalPrimitive(
    condition=lambda data, ctx: data.get("subscription") == "premium",
    then_primitive=premium_features,
    else_primitive=free_features
)

# Nested: Auth → then check premium
workflow = (
    input_parser >>
    is_authenticated >>
    has_premium >>
    response_builder
)
```

---

## Real-World Architectures

### Architecture 1: Content Moderation System

```python
from tta_dev_primitives import ConditionalPrimitive, LambdaPrimitive
from tta_dev_primitives.recovery import TimeoutPrimitive

# Stage 1: Safety analysis (with timeout)
safety_check = TimeoutPrimitive(
    LambdaPrimitive(lambda content, ctx: analyze_safety(content)),
    timeout_seconds=5.0
)

# Stage 2: Conditional routing
def is_safe(data: dict, ctx: WorkflowContext) -> bool:
    return data.get("safety_score", 0) > 0.8

def needs_review(data: dict, ctx: WorkflowContext) -> bool:
    score = data.get("safety_score", 0)
    return 0.5 <= score <= 0.8

# Review decision
review_router = ConditionalPrimitive(
    condition=needs_review,
    then_primitive=send_to_human_review,
    else_primitive=auto_reject
)

# Safety router
safety_router = ConditionalPrimitive(
    condition=is_safe,
    then_primitive=auto_approve,
    else_primitive=review_router
)

# Complete moderation pipeline
moderation_system = safety_check >> safety_router

# Usage
result = await moderation_system.execute({"text": "User content..."}, context)
# Output: {"status": "approved"} or {"status": "pending_review"} or {"status": "rejected"}
```

### Architecture 2: Multi-Model LLM Orchestra

```python
from tta_dev_primitives import ParallelPrimitive
from tta_dev_primitives.recovery import TimeoutPrimitive, RetryPrimitive

# Each LLM with timeout and retry
gpt4_reliable = TimeoutPrimitive(
    RetryPrimitive(gpt4_call, max_retries=2),
    timeout_seconds=30.0
)

claude_reliable = TimeoutPrimitive(
    RetryPrimitive(claude_call, max_retries=2),
    timeout_seconds=30.0
)

llama_reliable = TimeoutPrimitive(
    RetryPrimitive(llama_call, max_retries=2),
    timeout_seconds=20.0
)

# Aggregator: Find consensus
def aggregate_responses(results: list, ctx: WorkflowContext) -> dict:
    # Extract successful responses (some might have timed out)
    valid_responses = [r for r in results if r is not None]

    if not valid_responses:
        return {"error": "All models failed"}

    # Find common themes
    return {
        "responses": valid_responses,
        "consensus": find_common_answer(valid_responses),
        "count": len(valid_responses)
    }

aggregator = LambdaPrimitive(aggregate_responses)

# Orchestra: Parallel LLMs → Aggregate
llm_orchestra = (
    (gpt4_reliable | claude_reliable | llama_reliable) >>
    aggregator
)

result = await llm_orchestra.execute("Explain quantum computing", context)
```

### Architecture 3: Resilient Data Pipeline

```python
from tta_dev_primitives.performance import CachePrimitive
from tta_dev_primitives.recovery import (
    RetryPrimitive,
    FallbackPrimitive,
    TimeoutPrimitive,
    SagaPrimitive
)

# Stage 1: Fetch from primary DB (with retry and timeout)
primary_db_fetch = TimeoutPrimitive(
    RetryPrimitive(
        LambdaPrimitive(lambda query, ctx: primary_db.query(query)),
        max_retries=3
    ),
    timeout_seconds=5.0
)

# Fallback to replica
replica_db_fetch = TimeoutPrimitive(
    LambdaPrimitive(lambda query, ctx: replica_db.query(query)),
    timeout_seconds=5.0
)

# Fallback to cache
cache_fetch = LambdaPrimitive(lambda query, ctx: cache.get(query))

# Resilient fetch with fallback chain
resilient_fetch = FallbackPrimitive(
    primary=primary_db_fetch,
    fallbacks=[replica_db_fetch, cache_fetch]
)

# Stage 2: Transform data (with cache)
transform_data = CachePrimitive(
    LambdaPrimitive(lambda data, ctx: expensive_transformation(data)),
    ttl_seconds=3600
)

# Stage 3: Write to analytics DB (with saga for rollback)
write_analytics = SagaPrimitive(
    forward=LambdaPrimitive(lambda data, ctx: analytics_db.write(data)),
    compensation=LambdaPrimitive(lambda data, ctx: analytics_db.delete(data.get("id")))
)

# Complete pipeline
data_pipeline = (
    resilient_fetch >>
    transform_data >>
    write_analytics
)

# Guarantees:
# ✅ Fetch succeeds even if primary DB down
# ✅ Transform cached for 1 hour
# ✅ Analytics write rolled back on failure
```

---

## Advanced Patterns

### Dynamic Primitive Selection

```python
from tta_dev_primitives import RouterPrimitive

# Route based on request characteristics
def select_processor(data: dict, ctx: WorkflowContext) -> str:
    if data.get("priority") == "urgent":
        return "fast"
    elif data.get("quality") == "high":
        return "accurate"
    else:
        return "balanced"

processor_router = RouterPrimitive(
    routes={
        "fast": fast_processor,      # Low latency, lower quality
        "accurate": accurate_processor,  # High latency, high quality
        "balanced": balanced_processor   # Medium both
    },
    route_selector=select_processor
)

workflow = input_validator >> processor_router >> output_formatter
```

### Parallel with Different Inputs

```python
# Process multiple items in parallel
async def process_batch(items: list, ctx: WorkflowContext) -> list:
    # Create workflow
    processor = item_processor

    # Execute for each item in parallel
    tasks = [processor.execute(item, ctx) for item in items]
    results = await asyncio.gather(*tasks)

    return results

batch_processor = LambdaPrimitive(process_batch)

# Usage
results = await batch_processor.execute(
    [item1, item2, item3, item4],
    context
)
```

### Layered Error Handling

```python
# Layer 1: Timeout on individual operations
timeout_op = TimeoutPrimitive(operation, timeout_seconds=10.0)

# Layer 2: Retry transient failures
retry_op = RetryPrimitive(timeout_op, max_retries=3)

# Layer 3: Fallback on persistent failures
fallback_op = FallbackPrimitive(
    primary=retry_op,
    fallbacks=[backup_operation]
)

# Layer 4: Cache successful results
cached_op = CachePrimitive(fallback_op, ttl_seconds=3600)

# This operation will:
# 1. Check cache first (instant)
# 2. If miss, execute with 10s timeout
# 3. Retry up to 3 times on timeout/failure
# 4. Fallback to backup if all retries fail
# 5. Cache successful result
```

---

## Best Practices

### Composition Guidelines

✅ **Keep workflows readable** - Use parentheses for clarity

```python
# Good: Clear grouping
workflow = (
    input_stage >>
    (process_a | process_b | process_c) >>
    aggregation_stage >>
    output_stage
)

# Bad: Hard to read
workflow = input_stage >> process_a | process_b | process_c >> aggregation_stage >> output_stage
```

✅ **Name intermediate workflows**

```python
# Good: Named stages
fetch_stage = fetch_data >> validate_data
process_stage = (analyze | enrich | transform)
output_stage = format_result >> send_response

workflow = fetch_stage >> process_stage >> output_stage

# Bad: Everything inline (hard to understand)
workflow = fetch_data >> validate_data >> (analyze | enrich | transform) >> format_result >> send_response
```

✅ **Add recovery at right level**

```python
# Good: Retry at individual operation
reliable_fetch = RetryPrimitive(fetch_operation, max_retries=3)
workflow = reliable_fetch >> process_data

# Bad: Retry entire workflow (retries processing too)
workflow = RetryPrimitive(fetch_operation >> process_data, max_retries=3)
```

### Performance Considerations

✅ **Parallelize independent operations**

```python
# Good: Parallel
workflow = (fetch_user | fetch_preferences | fetch_history) >> combine

# Bad: Sequential (3x slower)
workflow = fetch_user >> fetch_preferences >> fetch_history >> combine
```

✅ **Cache expensive operations**

```python
# Good: Cache at right level
cached_llm = CachePrimitive(llm_call, ttl_seconds=3600)
workflow = input_prep >> cached_llm >> output_format

# Bad: Cache entire workflow (includes non-cacheable steps)
workflow = CachePrimitive(input_prep >> llm_call >> output_format, ttl_seconds=3600)
```

### Don'ts

❌ Don't create overly deep nesting (refactor to named stages)
❌ Don't mix error handling strategies (choose one approach)
❌ Don't parallelize dependent operations
❌ Don't forget to handle parallel failures
❌ Don't cache everything (only expensive operations)

---

## Testing Compositions

### Testing Sequential Workflows

```python
import pytest
from tta_dev_primitives.testing import MockPrimitive

@pytest.mark.asyncio
async def test_sequential_workflow():
    # Mock each stage
    stage1 = MockPrimitive(return_value={"step": 1})
    stage2 = MockPrimitive(return_value={"step": 2})
    stage3 = MockPrimitive(return_value={"step": 3})

    # Compose
    workflow = stage1 >> stage2 >> stage3

    # Execute
    result = await workflow.execute("input", WorkflowContext())

    # Verify
    assert result["step"] == 3
    assert stage1.call_count == 1
    assert stage2.call_count == 1
    assert stage3.call_count == 1
```

### Testing Parallel Workflows

```python
@pytest.mark.asyncio
async def test_parallel_workflow():
    # Mock parallel branches
    branch1 = MockPrimitive(return_value="result1")
    branch2 = MockPrimitive(return_value="result2")
    branch3 = MockPrimitive(return_value="result3")

    # Compose
    workflow = branch1 | branch2 | branch3

    # Execute
    results = await workflow.execute("input", WorkflowContext())

    # Verify all executed
    assert results == ["result1", "result2", "result3"]
    assert branch1.call_count == 1
    assert branch2.call_count == 1
    assert branch3.call_count == 1
```

---

## Common Mistakes

### Mistake 1: Sequential When Should Be Parallel

```python
# ❌ Bad: Sequential (slow)
workflow = fetch_user >> fetch_posts >> fetch_comments
# Takes: 100ms + 200ms + 150ms = 450ms total

# ✅ Good: Parallel (fast)
workflow = fetch_user | fetch_posts | fetch_comments
# Takes: max(100ms, 200ms, 150ms) = 200ms total
```

### Mistake 2: Parallel When Should Be Sequential

```python
# ❌ Bad: Parallel (will fail - step2 needs step1's output)
workflow = step1 | step2 | step3

# ✅ Good: Sequential
workflow = step1 >> step2 >> step3
```

### Mistake 3: Over-Caching

```python
# ❌ Bad: Caching everything
workflow = CachePrimitive(
    parse_input >> validate >> process >> format,
    ttl_seconds=3600
)

# ✅ Good: Cache only expensive operation
cached_process = CachePrimitive(process, ttl_seconds=3600)
workflow = parse_input >> validate >> cached_process >> format
```

---

## Next Steps

- **Handle errors:** [[TTA.dev/Guides/Error Handling Patterns]]
- **Add observability:** [[TTA.dev/Guides/Observability]]
- **Optimize costs:** [[TTA.dev/Guides/Cost Optimization]]
- **Test workflows:** [[TTA.dev/Guides/Testing Workflows]]

---

## Related Content

### Core Primitives

{{query (and (page-property type [[Primitive]]) (page-property category [[Core]]))}}

### Essential Guides

- [[TTA.dev/Guides/Agentic Primitives]] - Core concepts
- [[TTA.dev/Guides/Error Handling Patterns]] - Recovery strategies
- [[TTA.dev/Guides/Getting Started]] - Basic setup

---

## Key Takeaways

1. **Sequential (`>>`)** - For dependent steps, data flows through
2. **Parallel (`|`)** - For independent steps, same input to all
3. **Mix operators** - Create complex workflows from simple patterns
4. **Name stages** - Make workflows readable
5. **Add recovery at right level** - Don't over-retry
6. **Test compositions** - Mock primitives for unit tests

---

**Created:** [[2025-10-30]]
**Last Updated:** [[2025-10-30]]
**Estimated Time:** 30 minutes
**Difficulty:** [[Intermediate]]
