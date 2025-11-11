# TTA.dev/Examples/Basic Workflow

**Foundational workflow patterns demonstrating TTA.dev primitives.**

## Overview

Basic workflow examples show fundamental patterns for composing primitives into reliable AI workflows.

**Source:** `packages/tta-dev-primitives/examples/basic_workflow.py`

## Example 1: Simple Sequential Workflow

```python
from tta_dev_primitives import SequentialPrimitive, WorkflowContext

async def validate_input(data: dict, context: WorkflowContext) -> dict:
    """Validate input data."""
    if not data.get("text"):
        raise ValueError("Missing 'text' field")
    return data

async def process_text(data: dict, context: WorkflowContext) -> dict:
    """Process text with LLM."""
    # Your LLM call here
    return {"result": data["text"].upper()}

async def format_output(data: dict, context: WorkflowContext) -> dict:
    """Format final output."""
    return {"formatted": f"Result: {data['result']}"}

# Compose workflow
workflow = validate_input >> process_text >> format_output

# Execute
context = WorkflowContext(correlation_id="example-1")
result = await workflow.execute({"text": "hello"}, context)
# {"formatted": "Result: HELLO"}
```

**Key concepts:**
- [[SequentialPrimitive]] with `>>` operator
- [[WorkflowContext]] for tracing
- Simple function-based primitives

## Example 2: Parallel Data Fetching

```python
from tta_dev_primitives import ParallelPrimitive

async def fetch_user_profile(data: dict, context: WorkflowContext) -> dict:
    """Fetch user profile from API."""
    return {"profile": {"name": "User", "age": 30}}

async def fetch_recommendations(data: dict, context: WorkflowContext) -> dict:
    """Fetch recommendations from service."""
    return {"recommendations": ["Item 1", "Item 2"]}

async def fetch_analytics(data: dict, context: WorkflowContext) -> dict:
    """Fetch analytics data."""
    return {"analytics": {"visits": 42, "clicks": 15}}

# Execute all concurrently
workflow = ParallelPrimitive([
    fetch_user_profile,
    fetch_recommendations,
    fetch_analytics
])

result = await workflow.execute({"user_id": 123}, context)
# [
#   {"profile": {...}},
#   {"recommendations": [...]},
#   {"analytics": {...}}
# ]
```

**Key concepts:**
- [[ParallelPrimitive]] with `|` operator
- Concurrent execution with `asyncio.gather()`
- Independent operations

## Example 3: Conditional Branching

```python
from tta_dev_primitives import ConditionalPrimitive

async def fast_processor(data: dict, context: WorkflowContext) -> dict:
    """Fast processing for simple inputs."""
    return {"result": f"Fast: {data['text']}"}

async def slow_processor(data: dict, context: WorkflowContext) -> dict:
    """Thorough processing for complex inputs."""
    return {"result": f"Slow: {data['text']}"}

# Route based on input length
workflow = ConditionalPrimitive(
    condition=lambda data, ctx: len(data.get("text", "")) < 100,
    then_primitive=fast_processor,
    else_primitive=slow_processor
)

# Short text → fast path
result = await workflow.execute({"text": "hi"}, context)
# {"result": "Fast: hi"}

# Long text → slow path
result = await workflow.execute({"text": "a" * 200}, context)
# {"result": "Slow: aaaa..."}
```

**Key concepts:**
- [[ConditionalPrimitive]] for if/else logic
- Lambda condition functions
- Dynamic routing

## Example 4: Basic Caching

```python
from tta_dev_primitives.performance import CachePrimitive

async def expensive_llm_call(data: dict, context: WorkflowContext) -> dict:
    """Expensive LLM operation."""
    # Simulate expensive call
    await asyncio.sleep(2)
    return {"response": f"Processed: {data['prompt']}"}

# Cache results for 1 hour
workflow = CachePrimitive(
    primitive=expensive_llm_call,
    ttl_seconds=3600,
    max_size=100
)

# First call: slow (2s)
result = await workflow.execute({"prompt": "hello"}, context)

# Second call: instant (cache hit)
result = await workflow.execute({"prompt": "hello"}, context)
```

**Key concepts:**
- [[CachePrimitive]] for cost reduction
- TTL-based expiration
- LRU eviction

## Example 5: Retry on Failure

```python
from tta_dev_primitives.recovery import RetryPrimitive

async def flaky_api_call(data: dict, context: WorkflowContext) -> dict:
    """API that sometimes fails."""
    # Simulate 50% failure rate
    if random.random() < 0.5:
        raise Exception("API error")
    return {"result": "success"}

# Retry up to 3 times with exponential backoff
workflow = RetryPrimitive(
    primitive=flaky_api_call,
    max_retries=3,
    backoff_strategy="exponential",
    initial_delay=1.0
)

# Automatically retries on failure
result = await workflow.execute({}, context)
```

**Key concepts:**
- [[RetryPrimitive]] for resilience
- Exponential backoff
- Automatic retry logic

## Example 6: Fallback Chain

```python
from tta_dev_primitives.recovery import FallbackPrimitive

async def primary_api(data: dict, context: WorkflowContext) -> dict:
    """Primary API (might fail)."""
    raise Exception("Primary unavailable")

async def backup_api(data: dict, context: WorkflowContext) -> dict:
    """Backup API."""
    return {"result": "backup", "source": "backup"}

async def cache_response(data: dict, context: WorkflowContext) -> dict:
    """Cached response as last resort."""
    return {"result": "cached", "source": "cache"}

# Try primary, then backup, then cache
workflow = FallbackPrimitive(
    primary=primary_api,
    fallbacks=[backup_api, cache_response]
)

# Automatically falls back on failure
result = await workflow.execute({}, context)
# {"result": "backup", "source": "backup"}
```

**Key concepts:**
- [[FallbackPrimitive]] for graceful degradation
- Cascade pattern
- High availability

## Example 7: Timeout Protection

```python
from tta_dev_primitives.recovery import TimeoutPrimitive

async def slow_operation(data: dict, context: WorkflowContext) -> dict:
    """Operation that might hang."""
    await asyncio.sleep(60)  # Very slow
    return {"result": "done"}

# Timeout after 5 seconds
workflow = TimeoutPrimitive(
    primitive=slow_operation,
    timeout_seconds=5.0,
    raise_on_timeout=True
)

# Raises TimeoutError after 5s
try:
    result = await workflow.execute({}, context)
except asyncio.TimeoutError:
    print("Operation timed out")
```

**Key concepts:**
- [[TimeoutPrimitive]] for circuit breaking
- Timeout protection
- Resource management

## Example 8: Mixed Composition

```python
# Combine multiple patterns
workflow = (
    validate_input >>
    CachePrimitive(ttl=3600) >>
    RetryPrimitive(max_retries=3) >>
    (fast_path | slow_path | cached_path) >>
    aggregate_results >>
    format_output
)

# Sequential → Cache → Retry → Parallel → Sequential
result = await workflow.execute(data, context)
```

**Key concepts:**
- Operator chaining
- Multiple primitive types
- Complex workflows

## Running the Examples

```bash
# Run from repository root
cd packages/tta-dev-primitives/examples
uv run python basic_workflow.py

# Run specific example function
uv run python -c "
from basic_workflow import example_1_simple_sequential
import asyncio
asyncio.run(example_1_simple_sequential())
"
```

## Related Examples

- [[TTA.dev/Examples/RAG Workflow]] - Production RAG pattern
- [[TTA.dev/Examples/Cost Tracking Workflow]] - Cost optimization
- [[TTA.dev/Examples/Multi-Agent Workflow]] - Agent coordination
- [[TTA.dev/Examples/Streaming Workflow]] - Real-time streaming

## Documentation

- [[PRIMITIVES CATALOG]] - Complete primitive reference
- [[GETTING STARTED]] - Quick start guide
- [[SequentialPrimitive]] - Sequential composition
- [[ParallelPrimitive]] - Parallel execution
- [[ConditionalPrimitive]] - Conditional branching

## Source Code

**File:** `packages/tta-dev-primitives/examples/basic_workflow.py`

## Tags

example:: basic-workflow
type:: tutorial
audience:: beginners
primitives:: sequential, parallel, conditional, cache, retry, fallback, timeout

- [[Project Hub]]