type:: [[Package]]
path:: platform/primitives
pypi:: tta-dev-primitives
status:: production

# tta-dev-primitives

Core workflow primitives for building composable AI applications.

## Installation

```bash
uv add tta-dev-primitives
```

## Key Modules

### Core (`tta_dev_primitives.core`)
- `WorkflowPrimitive` - Base class
- `SequentialPrimitive` - Chain execution
- `ParallelPrimitive` - Concurrent execution
- `ConditionalPrimitive` - Branching logic
- `RouterPrimitive` - Dynamic routing

### Recovery (`tta_dev_primitives.recovery`)
- `RetryPrimitive` - Retry with backoff
- `FallbackPrimitive` - Graceful degradation
- `TimeoutPrimitive` - Circuit breaker
- `CircuitBreakerPrimitive` - Failure protection
- `CompensationPrimitive` - Saga pattern

### Performance (`tta_dev_primitives.performance`)
- `CachePrimitive` - LRU cache with TTL
- `MemoryPrimitive` - Conversational memory

### Testing (`tta_dev_primitives.testing`)
- `MockPrimitive` - Mock for testing

## Quick Example

```python
from tta_dev_primitives import WorkflowContext
from tta_dev_primitives.recovery import RetryPrimitive
from tta_dev_primitives.performance import CachePrimitive

# Compose
workflow = CachePrimitive(ttl=3600) >> RetryPrimitive(max_retries=3) >> call_llm

# Execute
result = await workflow.execute({"prompt": "Hello"}, WorkflowContext())
```

## File Structure

```
platform/primitives/
├── src/tta_dev_primitives/
│   ├── __init__.py
│   ├── core/
│   ├── recovery/
│   ├── performance/
│   ├── orchestration/
│   └── testing/
├── tests/
└── pyproject.toml
```

## Related
- [[TTA.dev/Primitives]] - Full catalog
- [[tta-observability-integration]] - Tracing
