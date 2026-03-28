# Primitives Patterns

Deep reference for TTA.dev primitive composition, operators, and workflow patterns.

## Core Concept

TTA.dev provides composable workflow primitives. Always use them instead of manual async orchestration.

## Composition Operators

- `>>` — Sequential execution (previous output → next input)
- `|` — Parallel execution (same input to all branches)

```python
from ttadev.primitives.core.base import WorkflowContext
from ttadev.primitives.recovery.retry import RetryPrimitive
from ttadev.primitives.recovery.fallback import FallbackPrimitive
from ttadev.primitives.adaptive.cache import AdaptiveCachePrimitive

# Sequential
workflow = AdaptiveCachePrimitive(ttl=3600) >> RetryPrimitive(max_retries=3) >> process_data

# Parallel
workflow = fast_path | slow_path | cached_path

# Combined
workflow = (
    input_processor >>
    (fast_path | slow_path | cached_path) >>
    aggregator
)

# Execute
context = WorkflowContext()
result = await workflow.execute(input_data, context)
```

**Type adaptation:** Use `LambdaPrimitive` to adapt types between sequential steps.

## Available Primitives

| Category | Primitives |
|----------|-----------|
| **Core** | `SequentialPrimitive`, `ParallelPrimitive`, `RouterPrimitive` |
| **Recovery** | `RetryPrimitive`, `FallbackPrimitive`, `TimeoutPrimitive`, `CompensationPrimitive` |
| **Performance** | `MemoryPrimitive` |
| **Adaptive** | `AdaptiveRetryPrimitive`, `AdaptiveFallbackPrimitive`, `AdaptiveTimeoutPrimitive`, `AdaptiveCachePrimitive` |
| **Testing** | `MockPrimitive` |

## Recovery Patterns

```python
from ttadev.primitives.recovery.retry import RetryPrimitive
from ttadev.primitives.recovery.fallback import FallbackPrimitive
from ttadev.primitives.recovery.timeout import TimeoutPrimitive
from ttadev.primitives.recovery.compensation import CompensationPrimitive

# Retry with exponential backoff
workflow = RetryPrimitive(
    primitive=api_call,
    max_retries=3,
    backoff_strategy="exponential",
)

# Fallback chain
workflow = FallbackPrimitive(
    primary=fast_service,
    fallback=slow_service,
)

# Timeout protection
workflow = TimeoutPrimitive(
    primitive=long_running_task,
    timeout_seconds=30.0,
)
```

## Performance Patterns

```python
from ttadev.primitives.adaptive.cache import AdaptiveCachePrimitive

# Adaptive cache with TTL
cached = AdaptiveCachePrimitive(
    primitive=expensive_llm_call,
    ttl_seconds=3600,
)
```

## Anti-Patterns

| ❌ Don't | ✅ Do |
|---------|------|
| Manual async orchestration | `SequentialPrimitive` or `>>` |
| `try/except` with retry loops | `RetryPrimitive` |
| `asyncio.wait_for()` | `TimeoutPrimitive` |
| Manual caching dicts | `AdaptiveCachePrimitive` |
| Global variables for state | `WorkflowContext` |
| Modifying core primitives | Extend via composition |

## State Management

Always pass state via `WorkflowContext`:

```python
from ttadev.primitives.core.base import WorkflowContext

context = WorkflowContext()
result = await workflow.execute(input_data, context)
```

## Key Files

- **Core primitives:** `ttadev/primitives/core/`
- **Recovery:** `ttadev/primitives/recovery/`
- **Adaptive:** `ttadev/primitives/adaptive/`
- **Performance:** `ttadev/primitives/performance/`
- **Testing:** `ttadev/primitives/testing/`
- **Full API reference:** [`PRIMITIVES_CATALOG.md`](../../PRIMITIVES_CATALOG.md)
