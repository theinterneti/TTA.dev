# Primitive Composition Examples

Working examples of TTA.dev primitive composition patterns. All examples are
copy-paste runnable with `tta-dev-primitives` installed.

## Sequential Composition (`>>`)

Chain primitives so the output of each step flows to the next:

```python
import asyncio
from tta_dev_primitives import WorkflowContext, LambdaPrimitive


async def fetch_data(url: str, ctx: WorkflowContext) -> dict:
    """Simulate fetching data from a URL."""
    return {"url": url, "status": 200, "body": "Hello from " + url}


async def extract_body(response: dict, ctx: WorkflowContext) -> str:
    """Extract body from a response dict."""
    return response["body"]


async def to_uppercase(text: str, ctx: WorkflowContext) -> str:
    """Transform text to uppercase."""
    return text.upper()


async def main():
    # Compose three steps sequentially
    workflow = (
        LambdaPrimitive(fetch_data)
        >> LambdaPrimitive(extract_body)
        >> LambdaPrimitive(to_uppercase)
    )

    context = WorkflowContext(workflow_id="sequential-example")
    result = await workflow.execute("https://api.example.com", context)
    print(result)  # "HELLO FROM HTTPS://API.EXAMPLE.COM"


asyncio.run(main())
```

## Parallel Composition (`|`)

Execute primitives concurrently with the same input:

```python
import asyncio
from tta_dev_primitives import WorkflowContext, LambdaPrimitive


async def word_count(text: str, ctx: WorkflowContext) -> dict:
    return {"metric": "words", "value": len(text.split())}


async def char_count(text: str, ctx: WorkflowContext) -> dict:
    return {"metric": "chars", "value": len(text)}


async def line_count(text: str, ctx: WorkflowContext) -> dict:
    return {"metric": "lines", "value": text.count("\n") + 1}


async def main():
    # All three run concurrently on the same input
    analyze = (
        LambdaPrimitive(word_count)
        | LambdaPrimitive(char_count)
        | LambdaPrimitive(line_count)
    )

    context = WorkflowContext(workflow_id="parallel-example")
    results = await analyze.execute("Hello world\nThis is TTA.dev", context)
    for r in results:
        print(f"{r['metric']}: {r['value']}")
    # words: 5, chars: 27, lines: 2


asyncio.run(main())
```

## Retry with Exponential Backoff

Automatically retry transient failures:

```python
import asyncio
import random
from tta_dev_primitives import WorkflowContext, LambdaPrimitive
from tta_dev_primitives.recovery import RetryPrimitive, RetryStrategy


call_count = 0


async def flaky_api(data: str, ctx: WorkflowContext) -> str:
    """Simulate an API that fails 60% of the time."""
    global call_count
    call_count += 1
    if random.random() < 0.6:
        raise ConnectionError(f"Attempt {call_count}: Connection refused")
    return f"Success on attempt {call_count}: {data}"


async def main():
    workflow = RetryPrimitive(
        primitive=LambdaPrimitive(flaky_api),
        strategy=RetryStrategy(
            max_retries=5,
            backoff_base=1.5,
            max_backoff=10.0,
            jitter=True,
        ),
    )

    context = WorkflowContext(workflow_id="retry-example")
    result = await workflow.execute("important-data", context)
    print(result)


asyncio.run(main())
```

## Fallback Pattern

Graceful degradation to an alternative:

```python
import asyncio
from tta_dev_primitives import WorkflowContext, LambdaPrimitive
from tta_dev_primitives.recovery import FallbackPrimitive


async def premium_api(query: str, ctx: WorkflowContext) -> str:
    """Simulate a premium API that is down."""
    raise ConnectionError("Premium API unavailable")


async def free_api(query: str, ctx: WorkflowContext) -> str:
    """Simulate a free fallback API."""
    return f"Free result for: {query}"


async def main():
    workflow = FallbackPrimitive(
        primary=LambdaPrimitive(premium_api),
        fallback=LambdaPrimitive(free_api),
    )

    context = WorkflowContext(workflow_id="fallback-example")
    result = await workflow.execute("What is TTA.dev?", context)
    print(result)  # "Free result for: What is TTA.dev?"


asyncio.run(main())
```

## Timeout with Fallback

Enforce time limits on slow operations:

```python
import asyncio
from tta_dev_primitives import WorkflowContext, LambdaPrimitive
from tta_dev_primitives.recovery import TimeoutPrimitive


async def slow_operation(data: str, ctx: WorkflowContext) -> str:
    """Simulate a slow operation."""
    await asyncio.sleep(10)  # Takes 10 seconds
    return f"Slow result: {data}"


async def fast_fallback(data: str, ctx: WorkflowContext) -> str:
    """Fast cached fallback."""
    return f"Cached result: {data}"


async def main():
    workflow = TimeoutPrimitive(
        primitive=LambdaPrimitive(slow_operation),
        timeout_seconds=2.0,
        fallback=LambdaPrimitive(fast_fallback),
    )

    context = WorkflowContext(workflow_id="timeout-example")
    result = await workflow.execute("query", context)
    print(result)  # "Cached result: query" (timeout triggered fallback)


asyncio.run(main())
```

## Caching Results

Avoid redundant expensive operations:

```python
import asyncio
from tta_dev_primitives import WorkflowContext, LambdaPrimitive
from tta_dev_primitives.performance import CachePrimitive


call_count = 0


async def expensive_computation(data: str, ctx: WorkflowContext) -> str:
    """Simulate an expensive operation."""
    global call_count
    call_count += 1
    await asyncio.sleep(0.1)  # Simulate work
    return f"Result #{call_count} for {data}"


async def main():
    workflow = CachePrimitive(
        primitive=LambdaPrimitive(expensive_computation),
        cache_key_fn=lambda data, ctx: f"cache:{data}",
        ttl_seconds=60.0,
    )

    context = WorkflowContext(workflow_id="cache-example")

    # First call: cache miss, executes the primitive
    result1 = await workflow.execute("input-a", context)
    print(result1)  # "Result #1 for input-a"

    # Second call: cache hit, returns cached result
    result2 = await workflow.execute("input-a", context)
    print(result2)  # "Result #1 for input-a" (cached)

    # Different input: cache miss
    result3 = await workflow.execute("input-b", context)
    print(result3)  # "Result #2 for input-b"

    print(workflow.get_stats())  # {size: 2, hits: 1, misses: 2, ...}


asyncio.run(main())
```

## Dynamic Routing

Route to different primitives based on input:

```python
import asyncio
from tta_dev_primitives import WorkflowContext, LambdaPrimitive
from tta_dev_primitives.core.routing import RouterPrimitive


async def handle_text(data: dict, ctx: WorkflowContext) -> str:
    return f"Processing text: {data['content'][:50]}"


async def handle_image(data: dict, ctx: WorkflowContext) -> str:
    return f"Processing image: {data['content']}"


async def handle_unknown(data: dict, ctx: WorkflowContext) -> str:
    return f"Unknown type: {data.get('type', 'none')}"


def route_by_type(data: dict, ctx: WorkflowContext) -> str:
    return data.get("type", "unknown")


async def main():
    workflow = RouterPrimitive(
        routes={
            "text": LambdaPrimitive(handle_text),
            "image": LambdaPrimitive(handle_image),
            "unknown": LambdaPrimitive(handle_unknown),
        },
        router_fn=route_by_type,
        default="unknown",
    )

    context = WorkflowContext(workflow_id="router-example")

    result = await workflow.execute(
        {"type": "text", "content": "Hello world"}, context
    )
    print(result)  # "Processing text: Hello world"

    result = await workflow.execute(
        {"type": "image", "content": "photo.jpg"}, context
    )
    print(result)  # "Processing image: photo.jpg"


asyncio.run(main())
```

## Composed Resilient Workflow

Combine multiple primitives for production-grade resilience:

```python
import asyncio
from tta_dev_primitives import WorkflowContext, LambdaPrimitive
from tta_dev_primitives.recovery import RetryPrimitive, RetryStrategy, TimeoutPrimitive
from tta_dev_primitives.performance import CachePrimitive


async def call_llm(prompt: str, ctx: WorkflowContext) -> str:
    """Simulate an LLM API call."""
    return f"LLM response to: {prompt[:30]}"


async def main():
    # Build a resilient LLM pipeline:
    # 1. Check cache first
    # 2. If miss, call LLM with retry (3 attempts, exponential backoff)
    # 3. Enforce 30-second timeout on the entire operation
    workflow = CachePrimitive(
        primitive=TimeoutPrimitive(
            primitive=RetryPrimitive(
                primitive=LambdaPrimitive(call_llm),
                strategy=RetryStrategy(max_retries=3, backoff_base=1.0),
            ),
            timeout_seconds=30.0,
        ),
        cache_key_fn=lambda prompt, ctx: f"llm:{hash(prompt)}",
        ttl_seconds=3600.0,
    )

    context = WorkflowContext(workflow_id="resilient-llm")
    result = await workflow.execute("Explain TTA.dev primitives", context)
    print(result)


asyncio.run(main())
```

## Cross-References

- [Specs Index](../reference/specs/README.md) — Formal primitive contracts
- [Primitives Catalog](../../PRIMITIVES_CATALOG.md) — Complete API reference
- [Getting Started](../../GETTING_STARTED.md) — Onboarding guide
