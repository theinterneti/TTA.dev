# TTA.dev Primitive Patterns

**Component:** Agentic Primitives
**Purpose:** Core design patterns for workflow primitives
**Last Updated:** October 30, 2025

---

## Overview

This document describes the core design patterns used in TTA.dev's agentic primitives. These patterns enable composable, type-safe, and observable workflows.

### Core Patterns

1. **WorkflowPrimitive Pattern** - Base abstraction for all primitives
2. **Composition Pattern** - Sequential and parallel composition
3. **Recovery Pattern** - Retry, fallback, timeout, compensation
4. **Performance Pattern** - Caching and optimization
5. **Observability Pattern** - Automatic tracing and metrics

---

## Pattern 1: WorkflowPrimitive Base

### Intent

Provide a consistent interface for all workflow components with automatic observability and type safety.

### Structure

```python
from abc import ABC, abstractmethod
from typing import Generic, TypeVar

TInput = TypeVar("TInput")
TOutput = TypeVar("TOutput")

class WorkflowPrimitive(ABC, Generic[TInput, TOutput]):
    """Base class for all workflow primitives."""

    async def execute(
        self,
        context: WorkflowContext,
        input_data: TInput
    ) -> TOutput:
        """Public interface - adds observability."""
        # Observability hooks (tracing, metrics, logging)
        return await self._execute_impl(context, input_data)

    @abstractmethod
    async def _execute_impl(
        self,
        context: WorkflowContext,
        input_data: TInput
    ) -> TOutput:
        """Subclasses implement actual logic here."""
        pass

    def __rshift__(self, other):
        """>> operator for sequential composition."""
        return SequentialPrimitive([self, other])

    def __or__(self, other):
        """| operator for parallel composition."""
        return ParallelPrimitive([self, other])
```

### Benefits

- ✅ **Type Safety** - Generic types enforce correct composition
- ✅ **Automatic Observability** - All primitives traced automatically
- ✅ **Composability** - Operator overloading for intuitive composition
- ✅ **Extensibility** - Easy to add new primitives
- ✅ **Testability** - Clear interface for mocking

### Usage Example

```python
class LLMPrimitive(WorkflowPrimitive[str, str]):
    """Call LLM with prompt."""

    def __init__(self, model: str):
        self.model = model

    async def _execute_impl(
        self,
        context: WorkflowContext,
        input_data: str
    ) -> str:
        # Call LLM API
        response = await call_llm(self.model, input_data)
        return response.text

# Usage
llm = LLMPrimitive(model="gpt-4")
result = await llm.execute(context, "What is AI?")
```

---

## Pattern 2: Composition

### Sequential Composition

**Intent:** Execute primitives one after another, passing output to input.

**Operator:** `>>`

**Implementation:**

```python
class SequentialPrimitive(WorkflowPrimitive[TInput, TOutput]):
    """Execute primitives in sequence."""

    def __init__(self, primitives: list[WorkflowPrimitive]):
        self.primitives = primitives

    async def _execute_impl(
        self,
        context: WorkflowContext,
        input_data: TInput
    ) -> TOutput:
        result = input_data
        for primitive in self.primitives:
            result = await primitive.execute(context, result)
        return result
```

**Usage:**

```python
# Chain operations
workflow = (
    input_validator >>
    llm_processor >>
    output_formatter
)

# Type-safe: Editor checks types match
# input_validator: WorkflowPrimitive[str, dict]
# llm_processor: WorkflowPrimitive[dict, dict]
# output_formatter: WorkflowPrimitive[dict, str]
# workflow: WorkflowPrimitive[str, str]
```

### Parallel Composition

**Intent:** Execute primitives concurrently, collect all results.

**Operator:** `|`

**Implementation:**

```python
import asyncio

class ParallelPrimitive(WorkflowPrimitive[TInput, list[Any]]):
    """Execute primitives in parallel."""

    def __init__(self, primitives: list[WorkflowPrimitive]):
        self.primitives = primitives

    async def _execute_impl(
        self,
        context: WorkflowContext,
        input_data: TInput
    ) -> list[Any]:
        # Execute all primitives concurrently
        tasks = [
            primitive.execute(context, input_data)
            for primitive in self.primitives
        ]
        results = await asyncio.gather(*tasks)
        return list(results)
```

**Usage:**

```python
# Parallel execution
workflow = (
    input_processor >>
    (fast_llm | slow_llm | cached_llm) >>
    result_aggregator
)

# All three LLMs execute concurrently
# result_aggregator receives list of 3 results
```

### Mixed Composition

**Pattern:** Combine sequential and parallel patterns

```python
workflow = (
    # Sequential: Step 1
    input_validator >>

    # Parallel: Step 2 (3 branches)
    (
        sentiment_analyzer |
        entity_extractor |
        summarizer
    ) >>

    # Sequential: Step 3
    result_combiner >>

    # Sequential: Step 4
    output_formatter
)

# Execution flow:
# 1. input_validator (sequential)
# 2. sentiment_analyzer, entity_extractor, summarizer (parallel)
# 3. result_combiner (sequential, receives list from step 2)
# 4. output_formatter (sequential)
```

---

## Pattern 3: Conditional Routing

### ConditionalPrimitive

**Intent:** Branch execution based on runtime conditions.

**Implementation:**

```python
class ConditionalPrimitive(WorkflowPrimitive[TInput, TOutput]):
    """Execute different primitives based on condition."""

    def __init__(
        self,
        condition: Callable[[WorkflowContext, TInput], bool],
        true_primitive: WorkflowPrimitive[TInput, TOutput],
        false_primitive: WorkflowPrimitive[TInput, TOutput],
    ):
        self.condition = condition
        self.true_primitive = true_primitive
        self.false_primitive = false_primitive

    async def _execute_impl(
        self,
        context: WorkflowContext,
        input_data: TInput
    ) -> TOutput:
        if self.condition(context, input_data):
            return await self.true_primitive.execute(context, input_data)
        else:
            return await self.false_primitive.execute(context, input_data)
```

**Usage:**

```python
# Route based on input size
workflow = ConditionalPrimitive(
    condition=lambda ctx, data: len(data) < 1000,
    true_primitive=fast_processor,
    false_primitive=batch_processor,
)
```

### RouterPrimitive

**Intent:** Dynamic routing to multiple destinations.

**Implementation:**

```python
class RouterPrimitive(WorkflowPrimitive[TInput, TOutput]):
    """Route to different primitives based on runtime logic."""

    def __init__(
        self,
        routes: dict[str, WorkflowPrimitive[TInput, TOutput]],
        selector: Callable[[WorkflowContext, TInput], str],
        default_route: str | None = None,
    ):
        self.routes = routes
        self.selector = selector
        self.default_route = default_route

    async def _execute_impl(
        self,
        context: WorkflowContext,
        input_data: TInput
    ) -> TOutput:
        # Select route
        route_name = self.selector(context, input_data)

        # Get primitive
        primitive = self.routes.get(
            route_name,
            self.routes.get(self.default_route) if self.default_route else None
        )

        if not primitive:
            raise ValueError(f"Unknown route: {route_name}")

        # Execute
        return await primitive.execute(context, input_data)
```

**Usage:**

```python
# LLM selection based on complexity
def select_llm(context, data):
    if context.data.get("priority") == "high":
        return "quality"
    elif len(data) < 100:
        return "fast"
    else:
        return "balanced"

router = RouterPrimitive(
    routes={
        "fast": gpt4_mini,
        "balanced": gpt35_turbo,
        "quality": gpt4,
    },
    selector=select_llm,
    default_route="balanced"
)
```

---

## Pattern 4: Recovery Patterns

### Retry Pattern

**Intent:** Retry failed operations with backoff.

**Implementation:**

```python
class RetryPrimitive(WorkflowPrimitive[TInput, TOutput]):
    """Retry primitive with exponential backoff."""

    def __init__(
        self,
        primitive: WorkflowPrimitive[TInput, TOutput],
        max_retries: int = 3,
        backoff_strategy: str = "exponential",
        initial_delay: float = 1.0,
    ):
        self.primitive = primitive
        self.max_retries = max_retries
        self.backoff_strategy = backoff_strategy
        self.initial_delay = initial_delay

    async def _execute_impl(
        self,
        context: WorkflowContext,
        input_data: TInput
    ) -> TOutput:
        last_exception = None

        for attempt in range(self.max_retries + 1):
            try:
                return await self.primitive.execute(context, input_data)
            except Exception as e:
                last_exception = e

                if attempt < self.max_retries:
                    delay = self._calculate_delay(attempt)
                    await asyncio.sleep(delay)
                    continue
                else:
                    raise last_exception

    def _calculate_delay(self, attempt: int) -> float:
        if self.backoff_strategy == "exponential":
            return self.initial_delay * (2 ** attempt)
        elif self.backoff_strategy == "linear":
            return self.initial_delay * (attempt + 1)
        else:
            return self.initial_delay
```

**Usage:**

```python
# Retry API calls
api_call_with_retry = RetryPrimitive(
    primitive=api_call,
    max_retries=3,
    backoff_strategy="exponential",
    initial_delay=1.0
)

# Retries: 1s, 2s, 4s delays
```

### Fallback Pattern

**Intent:** Provide alternative when primary fails.

**Implementation:**

```python
class FallbackPrimitive(WorkflowPrimitive[TInput, TOutput]):
    """Try primary, fallback if fails."""

    def __init__(
        self,
        primary: WorkflowPrimitive[TInput, TOutput],
        fallbacks: list[WorkflowPrimitive[TInput, TOutput]],
    ):
        self.primary = primary
        self.fallbacks = fallbacks

    async def _execute_impl(
        self,
        context: WorkflowContext,
        input_data: TInput
    ) -> TOutput:
        # Try primary
        try:
            return await self.primary.execute(context, input_data)
        except Exception as primary_error:
            # Try fallbacks in order
            for fallback in self.fallbacks:
                try:
                    return await fallback.execute(context, input_data)
                except Exception:
                    continue

            # All failed
            raise primary_error
```

**Usage:**

```python
# LLM with fallbacks
llm_with_fallback = FallbackPrimitive(
    primary=gpt4,
    fallbacks=[gpt35_turbo, local_llm, cached_response]
)

# Tries GPT-4 → GPT-3.5 → Local → Cache
```

### Timeout Pattern

**Intent:** Abort operation if takes too long.

**Implementation:**

```python
class TimeoutPrimitive(WorkflowPrimitive[TInput, TOutput]):
    """Execute with timeout."""

    def __init__(
        self,
        primitive: WorkflowPrimitive[TInput, TOutput],
        timeout_seconds: float,
    ):
        self.primitive = primitive
        self.timeout_seconds = timeout_seconds

    async def _execute_impl(
        self,
        context: WorkflowContext,
        input_data: TInput
    ) -> TOutput:
        try:
            return await asyncio.wait_for(
                self.primitive.execute(context, input_data),
                timeout=self.timeout_seconds
            )
        except asyncio.TimeoutError:
            raise TimeoutError(
                f"Operation timed out after {self.timeout_seconds}s"
            )
```

**Usage:**

```python
# Timeout for slow operations
fast_llm = TimeoutPrimitive(
    primitive=llm_call,
    timeout_seconds=5.0
)
```

---

## Pattern 5: Performance Patterns

### Cache Pattern

**Intent:** Cache expensive operation results.

**Implementation:**

```python
from collections import OrderedDict
from time import time

class CachePrimitive(WorkflowPrimitive[TInput, TOutput]):
    """LRU cache with TTL."""

    def __init__(
        self,
        primitive: WorkflowPrimitive[TInput, TOutput],
        max_size: int = 1000,
        ttl_seconds: float | None = None,
    ):
        self.primitive = primitive
        self.cache: OrderedDict = OrderedDict()
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds

    async def _execute_impl(
        self,
        context: WorkflowContext,
        input_data: TInput
    ) -> TOutput:
        # Create cache key
        key = self._make_key(input_data)

        # Check cache
        if key in self.cache:
            value, timestamp = self.cache[key]

            # Check TTL
            if self.ttl_seconds is None or (time() - timestamp) < self.ttl_seconds:
                # Cache hit - move to end (LRU)
                self.cache.move_to_end(key)
                return value
            else:
                # Expired - remove
                del self.cache[key]

        # Cache miss - execute
        result = await self.primitive.execute(context, input_data)

        # Store in cache
        self.cache[key] = (result, time())
        self.cache.move_to_end(key)

        # Evict if over size
        if len(self.cache) > self.max_size:
            self.cache.popitem(last=False)

        return result

    def _make_key(self, input_data: TInput) -> str:
        """Create cache key from input."""
        import hashlib
        import json

        # Hash input data
        data_str = json.dumps(input_data, sort_keys=True)
        return hashlib.md5(data_str.encode()).hexdigest()
```

**Usage:**

```python
# Cache LLM responses
cached_llm = CachePrimitive(
    primitive=expensive_llm,
    max_size=1000,
    ttl_seconds=3600  # 1 hour
)
```

---

## Pattern 6: Testing Pattern

### Mock Pattern

**Intent:** Replace primitives with mocks for testing.

**Implementation:**

```python
class MockPrimitive(WorkflowPrimitive[TInput, TOutput]):
    """Mock primitive for testing."""

    def __init__(
        self,
        return_value: TOutput | None = None,
        side_effect: Callable | Exception | None = None,
    ):
        self.return_value = return_value
        self.side_effect = side_effect
        self.call_count = 0
        self.calls: list[tuple[WorkflowContext, TInput]] = []

    async def _execute_impl(
        self,
        context: WorkflowContext,
        input_data: TInput
    ) -> TOutput:
        self.call_count += 1
        self.calls.append((context, input_data))

        if self.side_effect:
            if isinstance(self.side_effect, Exception):
                raise self.side_effect
            elif callable(self.side_effect):
                return await self.side_effect(context, input_data)

        return self.return_value
```

**Usage:**

```python
import pytest

@pytest.mark.asyncio
async def test_workflow():
    # Create mock
    mock_llm = MockPrimitive(
        return_value={"response": "mocked output"}
    )

    # Build workflow with mock
    workflow = input_processor >> mock_llm >> output_formatter

    # Execute
    result = await workflow.execute(context, input_data)

    # Assert
    assert mock_llm.call_count == 1
    assert result["response"] == "mocked output"
```

---

## Pattern 7: Compensation (Saga)

### Intent

Handle distributed transactions with compensating actions.

### Implementation

```python
class CompensationPrimitive(WorkflowPrimitive[TInput, TOutput]):
    """Execute with compensation on failure."""

    def __init__(
        self,
        primitive: WorkflowPrimitive[TInput, TOutput],
        compensate: Callable[[WorkflowContext, TInput], Any],
    ):
        self.primitive = primitive
        self.compensate = compensate

    async def _execute_impl(
        self,
        context: WorkflowContext,
        input_data: TInput
    ) -> TOutput:
        try:
            result = await self.primitive.execute(context, input_data)
            return result
        except Exception as e:
            # Execute compensation
            await self.compensate(context, input_data)
            raise
```

### Usage

```python
# Saga pattern for distributed transaction
async def compensate_payment(context, data):
    # Rollback payment
    await payment_service.refund(data["payment_id"])

payment_step = CompensationPrimitive(
    primitive=process_payment,
    compensate=compensate_payment
)

workflow = (
    validate_order >>
    payment_step >>  # Rolls back if later step fails
    create_shipment >>
    send_confirmation
)
```

---

## Pattern Combinations

### Example: Production-Ready LLM Call

```python
# Combine multiple patterns
production_llm = (
    TimeoutPrimitive(
        primitive=RetryPrimitive(
            primitive=FallbackPrimitive(
                primary=CachePrimitive(
                    primitive=gpt4,
                    max_size=1000,
                    ttl_seconds=3600
                ),
                fallbacks=[gpt35_turbo, local_llm]
            ),
            max_retries=3,
            backoff_strategy="exponential"
        ),
        timeout_seconds=30.0
    )
)

# Features:
# 1. Cached (1 hour TTL, 1000 item LRU)
# 2. Fallback to GPT-3.5 or local if GPT-4 fails
# 3. Retry up to 3 times with exponential backoff
# 4. Timeout after 30 seconds
```

---

## Best Practices

### Primitive Design

1. **Single Responsibility** - Each primitive does one thing
2. **Immutability** - Primitives are immutable after construction
3. **Type Safety** - Use generic types for input/output
4. **Async by Default** - All operations are async

### Composition

1. **Use Operators** - `>>` and `|` for intuitive composition
2. **Type Check** - Let editor check type compatibility
3. **Clear Structure** - Use parentheses for complex compositions
4. **Test Incrementally** - Test primitives individually first

### Error Handling

1. **Let Errors Propagate** - Don't catch unless handling
2. **Use Recovery Primitives** - Retry, Fallback for automatic recovery
3. **Record Errors** - All errors traced automatically
4. **Compensate When Needed** - Use CompensationPrimitive for distributed transactions

### Performance

1. **Cache Expensive Operations** - Use CachePrimitive
2. **Parallel When Possible** - Use `|` for independent operations
3. **Timeout Long Operations** - Use TimeoutPrimitive
4. **Monitor Performance** - Metrics tracked automatically

---

## Related Documentation

- **Primitives Catalog:** [`PRIMITIVES_CATALOG.md`](../../PRIMITIVES_CATALOG.md)
- **Package README:** [`packages/tta-dev-primitives/README.md`](../../packages/tta-dev-primitives/README.md)
- **Examples:** [`packages/tta-dev-primitives/examples/`](../../packages/tta-dev-primitives/examples/)
- **Decision Records:** [`DECISION_RECORDS.md`](DECISION_RECORDS.md)

---

**Last Updated:** October 30, 2025
**Maintainer:** TTA.dev Core Team


---
**Logseq:** [[TTA.dev/_archive/Nested_copies/Framework/Docs/Architecture/Primitive_patterns]]
