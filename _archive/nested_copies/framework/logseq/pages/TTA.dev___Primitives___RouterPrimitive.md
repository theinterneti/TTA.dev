# RouterPrimitive

type:: [[Primitive]]
category:: [[Core Workflow]]
package:: [[TTA.dev/Packages/tta-dev-primitives]]
status:: [[Stable]]
version:: 1.0.0
test-coverage:: 100
complexity:: [[Medium]]
python-class:: `RouterPrimitive`
import-path:: `from tta_dev_primitives import RouterPrimitive`
related-primitives:: [[TTA.dev/Primitives/ConditionalPrimitive]], [[TTA.dev/Primitives/SequentialPrimitive]]

---

## Overview

- id:: router-primitive-overview
  Dynamically route execution to different primitives based on input data, context, or custom logic. The intelligent routing pattern for adaptive workflows.

  **Think of it as:** A smart switch that chooses the best path based on conditions (like routing traffic to different servers).

---

## Use Cases

- id:: router-primitive-use-cases
  - **LLM selection:** Route to GPT-4 for complex queries, GPT-4-mini for simple ones
  - **Cost optimization:** Choose between expensive and cheap services based on budget
  - **Load balancing:** Distribute requests across multiple backends
  - **A/B testing:** Route users to different variants
  - **Feature flags:** Route to new features based on user flags
  - **Regional routing:** Route to nearest data center
  - **Tiered processing:** Fast path vs. slow path based on urgency

---

## Key Benefits

- id:: router-primitive-benefits
  - ✅ **Dynamic routing** - Choose destination at runtime based on conditions
  - ✅ **Custom routing logic** - Flexible routing function (lambda or callable)
  - ✅ **Type-safe routes** - Each route is a WorkflowPrimitive
  - ✅ **Default fallback** - Specify default route if no match
  - ✅ **Built-in observability** - Trace which route was taken
  - ✅ **Composable** - Routes can be complex workflows themselves

---

## API Reference

- id:: router-primitive-api

### Constructor

```python
RouterPrimitive(
    routes: dict[str, WorkflowPrimitive[T, U]],
    routing_fn: Callable[[T, WorkflowContext], str],
    default_route: str | None = None
)
```

**Parameters:**

- `routes`: Dictionary mapping route names to primitives
- `routing_fn`: Function that returns route name based on input and context
- `default_route`: Route name to use if routing_fn returns unknown route

**Returns:** A new `RouterPrimitive` instance

### Execution

```python
result = await router.execute(context, input_data)
# Routing function determines which route to take
```

---

## Examples

### LLM Selection Router

- id:: router-llm-selection

```python
{{embed ((standard-imports))}}

# Define LLM primitives
gpt4 = LambdaPrimitive(lambda data, ctx: call_gpt4(data))
gpt4_mini = LambdaPrimitive(lambda data, ctx: call_gpt4_mini(data))
claude = LambdaPrimitive(lambda data, ctx: call_claude(data))

# Routing logic based on query complexity
def route_by_complexity(data, context):
    query = data.get("query", "")

    # Simple heuristics
    if len(query) < 50:
        return "fast"  # Short query -> cheap model
    elif "code" in query.lower() or "analyze" in query.lower():
        return "quality"  # Code/analysis -> best model
    else:
        return "balanced"  # Default -> balanced model

# Create router
router = RouterPrimitive(
    routes={
        "fast": gpt4_mini,
        "quality": gpt4,
        "balanced": claude
    },
    routing_fn=route_by_complexity,
    default_route="balanced"
)

context = WorkflowContext(correlation_id="llm-route-001")
result = await router.execute(
    input_data={"query": "Explain quantum computing in detail"},
    context=context
)

# Routed to "quality" (GPT-4) due to complexity
```

### Cost-Based Routing

- id:: router-cost-optimization

```python
# Route based on budget remaining
def route_by_budget(data, context):
    budget_remaining = context.data.get("budget_remaining", 0)

    if budget_remaining > 100:
        return "premium"  # Plenty of budget -> best service
    elif budget_remaining > 10:
        return "standard"  # Some budget -> balanced service
    else:
        return "economy"  # Low budget -> cheap service

router = RouterPrimitive(
    routes={
        "premium": expensive_llm,
        "standard": balanced_llm,
        "economy": cheap_llm
    },
    routing_fn=route_by_budget,
    default_route="economy"
)
```

### Feature Flag Routing

- id:: router-feature-flags

```python
# Route based on feature flags
def route_by_feature_flag(data, context):
    user_id = context.data.get("user_id")

    # Check if user has new feature enabled
    if is_beta_user(user_id):
        return "new_algorithm"
    else:
        return "stable_algorithm"

router = RouterPrimitive(
    routes={
        "new_algorithm": experimental_workflow,
        "stable_algorithm": production_workflow
    },
    routing_fn=route_by_feature_flag,
    default_route="stable_algorithm"
)
```

---

## Composition Patterns

- id:: router-composition-patterns

### Router with Complex Routes

```python
# Each route can be a complex workflow
fast_route = (
    fast_validator >>
    fast_processor >>
    fast_formatter
)

quality_route = (
    deep_validator >>
    (llm_processor | human_review) >>
    quality_formatter
)

router = RouterPrimitive(
    routes={
        "fast": fast_route,
        "quality": quality_route
    },
    routing_fn=choose_route,
    default_route="fast"
)
```

### Sequential with Router

```python
# Route in middle of workflow
workflow = (
    input_validator >>
    data_enricher >>
    router >>  # Dynamic routing here
    result_aggregator >>
    output_formatter
)
```

### Router with Fallback

```python
from tta_dev_primitives.recovery import FallbackPrimitive

# Add fallback to each route
primary_route = FallbackPrimitive(
    primary=expensive_service,
    fallbacks=[cheap_service]
)

router = RouterPrimitive(
    routes={"primary": primary_route, "backup": backup_service},
    routing_fn=choose_route,
    default_route="backup"
)
```

---

## Routing Strategies

- id:: router-strategies

### Content-Based Routing

```python
def route_by_content(data, context):
    if "urgent" in data.get("tags", []):
        return "high_priority"
    elif "batch" in data.get("tags", []):
        return "low_priority"
    else:
        return "normal_priority"
```

### Load-Based Routing

```python
def route_by_load(data, context):
    # Check current load on services
    service1_load = get_service_load("service1")
    service2_load = get_service_load("service2")

    # Route to less loaded service
    return "service1" if service1_load < service2_load else "service2"
```

### Round-Robin Routing

```python
counter = 0

def round_robin_route(data, context):
    global counter
    routes = ["service1", "service2", "service3"]
    route = routes[counter % len(routes)]
    counter += 1
    return route
```

### Time-Based Routing

```python
def route_by_time(data, context):
    hour = datetime.now().hour

    # Use cheaper services during off-peak hours
    if 0 <= hour < 6:  # Night
        return "economy"
    elif 9 <= hour < 17:  # Business hours
        return "premium"
    else:
        return "standard"
```

---

## Related Content

### Works Well With

- [[TTA.dev/Primitives/ConditionalPrimitive]] - Simple if/else routing
- [[TTA.dev/Primitives/FallbackPrimitive]] - Add fallback to routes
- [[TTA.dev/Primitives/RetryPrimitive]] - Retry failed routes
- [[TTA.dev/Primitives/CachePrimitive]] - Cache routed results

### Used In Examples

{{query (and [[Example]] [[RouterPrimitive]])}}

### Referenced By

{{query (and (mentions [[TTA.dev/Primitives/RouterPrimitive]]))}}

---

## Performance Considerations

- id:: router-performance

### Routing Overhead

- **Routing function:** Should be fast (<1ms typically)
- **No caching:** Routing decision made on every execution
- **Context access:** routing_fn has access to full context

### Optimization Tips

✅ **Simple routing logic** - Keep routing function lightweight
✅ **Cache routing decisions** - If deterministic, cache in [[TTA.dev/Primitives/CachePrimitive]]
✅ **Avoid I/O in routing_fn** - Don't make API calls in routing function
✅ **Pre-compute when possible** - Pass routing hints in context

---

## Best Practices

✅ **Explicit route names** - Use descriptive route names ("fast", "quality", not "route1")
✅ **Always set default_route** - Graceful fallback for unknown routes
✅ **Document routing logic** - Comment the routing function clearly
✅ **Test all routes** - Ensure each route is reachable and works
✅ **Monitor route distribution** - Track which routes are used most

❌ **Don't do I/O in routing_fn** - Routing function should be pure and fast
❌ **Don't modify input** - Routing function should not mutate input data
❌ **Don't have too many routes** - More than 5-10 routes gets complex

---

## Testing

### Example Test

```python
import pytest
from tta_dev_primitives import RouterPrimitive, WorkflowContext
from tta_dev_primitives.testing import MockPrimitive

@pytest.mark.asyncio
async def test_router_selection():
    # Create mock routes
    fast_route = MockPrimitive(return_value="fast_result")
    slow_route = MockPrimitive(return_value="slow_result")

    # Simple routing function
    def route_fn(data, ctx):
        return "fast" if data["speed"] == "fast" else "slow"

    # Create router
    router = RouterPrimitive(
        routes={"fast": fast_route, "slow": slow_route},
        routing_fn=route_fn,
        default_route="fast"
    )

    # Test fast route
    context = WorkflowContext(correlation_id="test-001")
    result = await router.execute(
        input_data={"speed": "fast"},
        context=context
    )
    assert result == "fast_result"
    assert fast_route.call_count == 1
    assert slow_route.call_count == 0

    # Test slow route
    result = await router.execute(
        input_data={"speed": "slow"},
        context=context
    )
    assert result == "slow_result"
    assert slow_route.call_count == 1
```

---

## Observability

### Tracing

Router adds route information to span:

```
workflow_execution (parent span)
└── router_execution (span)
    ├── route_selected: "fast"
    ├── route_count: 3
    └── fast_route_execution (child span)
```

### Metrics

- `router.route_selection_count` - Count by route name
- `router.routing_duration` - Time spent in routing function
- `router.default_route_usage` - How often default route is used

---

## Metadata

**Source Code:** [router.py](https://github.com/theinterneti/TTA.dev/blob/main/packages/tta-dev-primitives/src/tta_dev_primitives/core/router.py)
**Tests:** [test_router.py](https://github.com/theinterneti/TTA.dev/blob/main/packages/tta-dev-primitives/tests/test_router.py)
**Examples:** [router_llm_selection.py](https://github.com/theinterneti/TTA.dev/blob/main/packages/tta-dev-primitives/examples/router_llm_selection.py)

**Created:** [[2025-10-30]]
**Last Updated:** [[2025-10-30]]
**Test Coverage:** 100%
**Status:** [[Stable]] - Production Ready


---
**Logseq:** [[TTA.dev/_archive/Nested_copies/Framework/Logseq/Pages/Tta.dev___primitives___routerprimitive]]
