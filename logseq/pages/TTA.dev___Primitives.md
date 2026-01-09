type:: [[Catalog]]
description:: Complete reference for all workflow primitives

# TTA.dev Primitives Catalog

## Core Primitives

### WorkflowPrimitive
- **Import:** `from tta_dev_primitives import WorkflowPrimitive`
- **Description:** Base class for all workflow primitives
- **Type Parameters:** `WorkflowPrimitive[TInput, TOutput]`

### SequentialPrimitive
- **Import:** `from tta_dev_primitives import SequentialPrimitive`
- **Operator:** `>>`
- **Description:** Execute primitives in sequence

### ParallelPrimitive
- **Import:** `from tta_dev_primitives import ParallelPrimitive`
- **Operator:** `|`
- **Description:** Execute primitives concurrently

## Recovery Primitives

### RetryPrimitive
- **Import:** `from tta_dev_primitives.recovery import RetryPrimitive`
- **Description:** Automatic retry with exponential backoff
- **Parameters:**
  - `max_retries: int` - Maximum retry attempts
  - `backoff_strategy: str` - "exponential" or "linear"
  - `initial_delay: float` - Initial delay in seconds

### FallbackPrimitive
- **Import:** `from tta_dev_primitives.recovery import FallbackPrimitive`
- **Description:** Graceful degradation with fallback cascade
- **Parameters:**
  - `primary: WorkflowPrimitive` - Primary primitive
  - `fallbacks: list` - Fallback primitives in order

### TimeoutPrimitive
- **Import:** `from tta_dev_primitives.recovery import TimeoutPrimitive`
- **Description:** Circuit breaker with timeout
- **Parameters:**
  - `timeout_seconds: float` - Timeout duration
  - `raise_on_timeout: bool` - Whether to raise exception

### CircuitBreakerPrimitive
- **Import:** `from tta_dev_primitives.recovery import CircuitBreakerPrimitive`
- **Description:** Prevent cascade failures
- **Parameters:**
  - `failure_threshold: int` - Failures to open circuit
  - `recovery_timeout: float` - Seconds until half-open

## Performance Primitives

### CachePrimitive
- **Import:** `from tta_dev_primitives.performance import CachePrimitive`
- **Description:** LRU cache with TTL
- **Parameters:**
  - `ttl_seconds: int` - Time to live
  - `max_size: int` - Maximum cache entries

### MemoryPrimitive
- **Import:** `from tta_dev_primitives.performance import MemoryPrimitive`
- **Description:** Conversational memory with hybrid storage
- **Parameters:**
  - `max_size: int` - Maximum memory entries
  - `redis_url: str` - Optional Redis connection

## Usage Example

```python
from tta_dev_primitives import WorkflowContext
from tta_dev_primitives.recovery import RetryPrimitive, FallbackPrimitive
from tta_dev_primitives.performance import CachePrimitive

# Compose workflow
workflow = (
    CachePrimitive(ttl=3600) >>
    RetryPrimitive(max_retries=3) >>
    FallbackPrimitive(primary=gpt4, fallbacks=[claude, gemini])
)

# Execute
context = WorkflowContext(workflow_id="demo")
result = await workflow.execute(data, context)
```

## Related Pages
- [[TTA.dev/Packages]] - Package overview
- [[TTA.dev/Architecture]] - System design
