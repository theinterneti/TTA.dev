# Quick Start: Priority Improvements

**Target:** Implement 3 high-impact primitives in Week 1

---

## 1. Router Primitive (Day 1-2)

### File: `src/tta_workflow_primitives/core/routing.py`

```python
"""Routing primitive for intelligent workflow branching."""

from __future__ import annotations

from typing import Any, Callable

from .base import WorkflowContext, WorkflowPrimitive
from ..observability.logging import get_logger

logger = get_logger(__name__)


class RouterPrimitive(WorkflowPrimitive[Any, Any]):
    """
    Route input to appropriate primitive based on routing function.

    Example:
        ```python
        router = RouterPrimitive(
            routes={
                "openai": openai_primitive,
                "anthropic": anthropic_primitive,
                "local": local_llm_primitive
            },
            router_fn=lambda data, ctx: ctx.metadata.get("provider", "openai"),
            default="openai"
        )
        ```
    """

    def __init__(
        self,
        routes: dict[str, WorkflowPrimitive],
        router_fn: Callable[[Any, WorkflowContext], str],
        default: str | None = None
    ):
        """
        Initialize router.

        Args:
            routes: Map of route keys to primitives
            router_fn: Function to determine route from input/context
            default: Default route if router_fn returns unknown key
        """
        self.routes = routes
        self.router_fn = router_fn
        self.default = default

    async def execute(self, input_data: Any, context: WorkflowContext) -> Any:
        """Execute routing logic and invoke selected primitive."""
        # Determine route
        route_key = self.router_fn(input_data, context)

        # Get primitive
        primitive = self.routes.get(route_key)

        # Fallback to default
        if not primitive and self.default:
            route_key = self.default
            primitive = self.routes.get(route_key)

        if not primitive:
            available = ", ".join(self.routes.keys())
            raise ValueError(
                f"No route found for key '{route_key}'. "
                f"Available routes: {available}"
            )

        # Log routing decision
        logger.info(
            "routing_decision",
            route=route_key,
            available_routes=list(self.routes.keys())
        )

        # Execute selected primitive
        return await primitive.execute(input_data, context)
```

### Tests: `tests/test_routing.py`

```python
"""Tests for routing primitive."""

import pytest

from tta_workflow_primitives.core.routing import RouterPrimitive
from tta_workflow_primitives.core.base import WorkflowContext
from tta_workflow_primitives.testing.mocks import MockPrimitive


@pytest.mark.asyncio
async def test_router_basic():
    """Test basic routing."""
    route_a = MockPrimitive("a", return_value={"result": "A"})
    route_b = MockPrimitive("b", return_value={"result": "B"})

    router = RouterPrimitive(
        routes={"a": route_a, "b": route_b},
        router_fn=lambda data, ctx: data["route"]
    )

    context = WorkflowContext()
    result = await router.execute({"route": "a"}, context)

    assert result == {"result": "A"}
    assert route_a.call_count == 1
    assert route_b.call_count == 0


@pytest.mark.asyncio
async def test_router_default():
    """Test default route fallback."""
    default = MockPrimitive("default", return_value={"result": "DEFAULT"})

    router = RouterPrimitive(
        routes={"a": default},
        router_fn=lambda data, ctx: data.get("route", "unknown"),
        default="a"
    )

    context = WorkflowContext()
    result = await router.execute({"route": "unknown"}, context)

    assert result == {"result": "DEFAULT"}


@pytest.mark.asyncio
async def test_router_no_route_error():
    """Test error when no route found."""
    router = RouterPrimitive(
        routes={"a": MockPrimitive("a", return_value={})},
        router_fn=lambda data, ctx: "nonexistent"
    )

    with pytest.raises(ValueError, match="No route found"):
        await router.execute({}, WorkflowContext())
```

---

## 2. Timeout Primitive (Day 2-3)

### File: `src/tta_workflow_primitives/recovery/timeout.py`

```python
"""Timeout enforcement for primitives."""

from __future__ import annotations

import asyncio
from typing import Any

from ..core.base import WorkflowContext, WorkflowPrimitive
from ..observability.logging import get_logger

logger = get_logger(__name__)


class TimeoutError(Exception):
    """Timeout exceeded during execution."""
    pass


class TimeoutPrimitive(WorkflowPrimitive[Any, Any]):
    """
    Enforce execution timeout with optional fallback.

    Example:
        ```python
        workflow = TimeoutPrimitive(
            primitive=slow_operation,
            timeout_seconds=30.0,
            fallback=fast_cached_operation
        )
        ```
    """

    def __init__(
        self,
        primitive: WorkflowPrimitive,
        timeout_seconds: float,
        fallback: WorkflowPrimitive | None = None
    ):
        """
        Initialize timeout primitive.

        Args:
            primitive: Primitive to execute with timeout
            timeout_seconds: Maximum execution time
            fallback: Optional fallback primitive on timeout
        """
        self.primitive = primitive
        self.timeout_seconds = timeout_seconds
        self.fallback = fallback

    async def execute(self, input_data: Any, context: WorkflowContext) -> Any:
        """Execute with timeout enforcement."""
        try:
            result = await asyncio.wait_for(
                self.primitive.execute(input_data, context),
                timeout=self.timeout_seconds
            )

            logger.info(
                "timeout_success",
                primitive=self.primitive.__class__.__name__,
                timeout=self.timeout_seconds
            )

            return result

        except asyncio.TimeoutError:
            logger.warning(
                "timeout_exceeded",
                primitive=self.primitive.__class__.__name__,
                timeout=self.timeout_seconds,
                has_fallback=self.fallback is not None
            )

            if self.fallback:
                logger.info("executing_fallback")
                return await self.fallback.execute(input_data, context)

            raise TimeoutError(
                f"Execution exceeded {self.timeout_seconds}s timeout"
            )
```

### Tests: `tests/test_timeout.py`

```python
"""Tests for timeout primitive."""

import asyncio
import pytest

from tta_workflow_primitives.recovery.timeout import TimeoutPrimitive, TimeoutError
from tta_workflow_primitives.core.base import WorkflowContext, LambdaPrimitive
from tta_workflow_primitives.testing.mocks import MockPrimitive


@pytest.mark.asyncio
async def test_timeout_success():
    """Test successful execution within timeout."""
    fast = LambdaPrimitive(lambda data, ctx: {"result": "fast"})

    timeout_prim = TimeoutPrimitive(
        primitive=fast,
        timeout_seconds=1.0
    )

    result = await timeout_prim.execute({}, WorkflowContext())
    assert result == {"result": "fast"}


@pytest.mark.asyncio
async def test_timeout_exceeded():
    """Test timeout exceeded without fallback."""
    async def slow(data, ctx):
        await asyncio.sleep(2.0)
        return {"result": "slow"}

    slow_prim = LambdaPrimitive(slow)
    timeout_prim = TimeoutPrimitive(
        primitive=slow_prim,
        timeout_seconds=0.1
    )

    with pytest.raises(TimeoutError):
        await timeout_prim.execute({}, WorkflowContext())


@pytest.mark.asyncio
async def test_timeout_with_fallback():
    """Test fallback on timeout."""
    async def slow(data, ctx):
        await asyncio.sleep(2.0)
        return {"result": "slow"}

    slow_prim = LambdaPrimitive(slow)
    fallback = MockPrimitive("fallback", return_value={"result": "fallback"})

    timeout_prim = TimeoutPrimitive(
        primitive=slow_prim,
        timeout_seconds=0.1,
        fallback=fallback
    )

    result = await timeout_prim.execute({}, WorkflowContext())
    assert result == {"result": "fallback"}
    assert fallback.call_count == 1
```

---

## 3. Cache Primitive (Day 3-4)

### File: `src/tta_workflow_primitives/performance/cache.py`

```python
"""Caching primitive for workflow results."""

from __future__ import annotations

import time
from typing import Any, Callable

from ..core.base import WorkflowContext, WorkflowPrimitive
from ..observability.logging import get_logger

logger = get_logger(__name__)


class CachePrimitive(WorkflowPrimitive[Any, Any]):
    """
    Cache primitive execution results.

    Example:
        ```python
        cached = CachePrimitive(
            primitive=expensive_llm_call,
            cache_key_fn=lambda data, ctx: f"{data['prompt']}:{ctx.player_id}",
            ttl_seconds=3600.0
        )
        ```
    """

    def __init__(
        self,
        primitive: WorkflowPrimitive,
        cache_key_fn: Callable[[Any, WorkflowContext], str],
        ttl_seconds: float = 3600.0
    ):
        """
        Initialize cache primitive.

        Args:
            primitive: Primitive to cache
            cache_key_fn: Function to generate cache key
            ttl_seconds: Time-to-live for cached values
        """
        self.primitive = primitive
        self.cache_key_fn = cache_key_fn
        self.ttl_seconds = ttl_seconds
        self._cache: dict[str, tuple[Any, float]] = {}

    async def execute(self, input_data: Any, context: WorkflowContext) -> Any:
        """Execute with caching."""
        # Generate cache key
        cache_key = self.cache_key_fn(input_data, context)

        # Check cache
        if cache_key in self._cache:
            result, timestamp = self._cache[cache_key]
            age = time.time() - timestamp

            if age < self.ttl_seconds:
                logger.info(
                    "cache_hit",
                    key=cache_key,
                    age_seconds=age,
                    ttl=self.ttl_seconds
                )
                return result
            else:
                logger.debug("cache_expired", key=cache_key, age=age)
                del self._cache[cache_key]

        # Cache miss - execute and store
        logger.info("cache_miss", key=cache_key)
        result = await self.primitive.execute(input_data, context)

        self._cache[cache_key] = (result, time.time())
        logger.debug("cache_store", key=cache_key, cache_size=len(self._cache))

        return result

    def clear_cache(self) -> None:
        """Clear all cached values."""
        self._cache.clear()
        logger.info("cache_cleared")

    def get_stats(self) -> dict:
        """Get cache statistics."""
        return {
            "size": len(self._cache),
            "keys": list(self._cache.keys())
        }
```

### Tests: `tests/test_cache.py`

```python
"""Tests for cache primitive."""

import time
import pytest

from tta_workflow_primitives.performance.cache import CachePrimitive
from tta_workflow_primitives.core.base import WorkflowContext
from tta_workflow_primitives.testing.mocks import MockPrimitive


@pytest.mark.asyncio
async def test_cache_hit():
    """Test cache hit on second call."""
    mock = MockPrimitive("test", return_value={"result": "cached"})

    cached = CachePrimitive(
        primitive=mock,
        cache_key_fn=lambda data, ctx: data["key"],
        ttl_seconds=60.0
    )

    # First call - cache miss
    result1 = await cached.execute({"key": "test"}, WorkflowContext())
    assert result1 == {"result": "cached"}
    assert mock.call_count == 1

    # Second call - cache hit
    result2 = await cached.execute({"key": "test"}, WorkflowContext())
    assert result2 == {"result": "cached"}
    assert mock.call_count == 1  # Not called again


@pytest.mark.asyncio
async def test_cache_miss_different_keys():
    """Test cache miss with different keys."""
    mock = MockPrimitive("test", return_value={"result": "value"})

    cached = CachePrimitive(
        primitive=mock,
        cache_key_fn=lambda data, ctx: data["key"],
        ttl_seconds=60.0
    )

    await cached.execute({"key": "a"}, WorkflowContext())
    await cached.execute({"key": "b"}, WorkflowContext())

    assert mock.call_count == 2


@pytest.mark.asyncio
async def test_cache_expiration():
    """Test cache expiration after TTL."""
    mock = MockPrimitive("test", return_value={"result": "value"})

    cached = CachePrimitive(
        primitive=mock,
        cache_key_fn=lambda data, ctx: "key",
        ttl_seconds=0.1  # Very short TTL
    )

    # First call
    await cached.execute({}, WorkflowContext())
    assert mock.call_count == 1

    # Wait for expiration
    time.sleep(0.2)

    # Second call after expiration
    await cached.execute({}, WorkflowContext())
    assert mock.call_count == 2


@pytest.mark.asyncio
async def test_cache_clear():
    """Test cache clearing."""
    mock = MockPrimitive("test", return_value={"result": "value"})

    cached = CachePrimitive(
        primitive=mock,
        cache_key_fn=lambda data, ctx: "key",
        ttl_seconds=60.0
    )

    await cached.execute({}, WorkflowContext())
    assert cached.get_stats()["size"] == 1

    cached.clear_cache()
    assert cached.get_stats()["size"] == 0
```

---

## Usage Example: Combining All Three

```python
"""Example workflow using routing, timeout, and caching."""

from tta_workflow_primitives.core.routing import RouterPrimitive
from tta_workflow_primitives.recovery.timeout import TimeoutPrimitive
from tta_workflow_primitives.performance.cache import CachePrimitive
from tta_workflow_primitives.core.base import LambdaPrimitive

# Define provider-specific primitives
openai_primitive = LambdaPrimitive(lambda data, ctx: call_openai(data))
anthropic_primitive = LambdaPrimitive(lambda data, ctx: call_anthropic(data))
local_primitive = LambdaPrimitive(lambda data, ctx: call_local_llm(data))

# Build workflow with all improvements
workflow = (
    # Route based on cost/speed tradeoff
    RouterPrimitive(
        routes={
            "fast": CachePrimitive(
                TimeoutPrimitive(local_primitive, timeout_seconds=5.0),
                cache_key_fn=lambda d, c: f"local:{d['prompt'][:50]}",
                ttl_seconds=1800.0
            ),
            "balanced": CachePrimitive(
                TimeoutPrimitive(anthropic_primitive, timeout_seconds=30.0),
                cache_key_fn=lambda d, c: f"anthropic:{d['prompt'][:50]}",
                ttl_seconds=3600.0
            ),
            "premium": CachePrimitive(
                TimeoutPrimitive(openai_primitive, timeout_seconds=30.0),
                cache_key_fn=lambda d, c: f"openai:{d['prompt'][:50]}",
                ttl_seconds=3600.0
            )
        },
        router_fn=lambda data, ctx: ctx.metadata.get("tier", "balanced"),
        default="balanced"
    )
)

# Execute
context = WorkflowContext(metadata={"tier": "fast"})
result = await workflow.execute({"prompt": "Tell me a story"}, context)
```

---

## Integration Checklist

- [ ] Add to `__init__.py` exports
- [ ] Update package README
- [ ] Run tests: `pytest tests/test_routing.py tests/test_timeout.py tests/test_cache.py`
- [ ] Update CHANGELOG.md
- [ ] Create migration guide for existing workflows
- [ ] Benchmark performance impact
- [ ] Update documentation site

---

## Performance Targets

| Primitive | Target | Measurement |
|-----------|--------|-------------|
| Router | <5ms overhead | Routing decision time |
| Timeout | <1% false positives | Unnecessary timeouts |
| Cache | >60% hit rate | Production workload |
| Cache | <1ms hit latency | Cache lookup time |

---

## Next Steps (Week 2)

After implementing these 3 primitives:

1. **Context Management** (Day 5-7)
   - ContextFilter
   - ContextManager with pruning

2. **Rate Limiting** (Day 8-10)
   - RateLimitPrimitive
   - Token bucket algorithm

3. **Integration Testing** (Day 11-12)
   - End-to-end workflow tests
   - Performance benchmarks
   - Production rollout plan
