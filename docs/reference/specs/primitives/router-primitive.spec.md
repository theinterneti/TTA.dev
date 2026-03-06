# RouterPrimitive Specification

- **Version:** 1.3.0
- **Status:** Approved
- **Package:** tta-dev-primitives
- **Source:** `platform/primitives/src/tta_dev_primitives/core/routing.py`

## 1. Purpose

`RouterPrimitive` dynamically routes input to one of several named primitives based on a
user-supplied routing function. It enables branching workflows where the execution path
is determined at runtime.

## 2. Contract

### 2.1 Type Signature

```python
class RouterPrimitive(WorkflowPrimitive[Any, Any]):
    def __init__(
        self,
        routes: dict[str, WorkflowPrimitive],
        router_fn: Callable[[Any, WorkflowContext], str],
        default: str | None = None,
    ): ...
```

### 2.2 Constructor Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `routes` | `dict[str, WorkflowPrimitive]` | *(required)* | Map of route keys to primitives |
| `router_fn` | `Callable[[Any, WorkflowContext], str]` | *(required)* | Function that returns a route key |
| `default` | `str \| None` | `None` | Default route key if `router_fn` returns an unknown key |

### 2.3 Behavior Invariants

- `execute()` MUST call `router_fn(input_data, context)` to determine the route key.
- If the route key exists in `routes`, `execute()` MUST execute the corresponding primitive.
- If the route key does NOT exist and `default` is set, `execute()` MUST use the `default` route.
- If the route key does NOT exist and `default` is `None`, `execute()` MUST raise `ValueError`.
- `execute()` MUST append the selected route key to `context.state["routing_history"]`.

### 2.4 Error Contract

| Condition | Exception | Description |
|-----------|-----------|-------------|
| Unknown route key, no default | `ValueError` | `"Route '{key}' not found and no default route configured"` |
| `router_fn` raises | *(propagated)* | Exception from the routing function propagates |
| Selected primitive raises | *(propagated)* | Exception from the routed primitive propagates |

### 2.5 Observability Contract

**Logging:**

| Event | Level | Fields |
|-------|-------|--------|
| `routing_decision` | INFO | `route`, `available_routes`, `workflow_id` |

**State tracking:** Route key appended to `context.state["routing_history"]` list.

## 3. Composition Rules

- Standard `>>` and `|` operators apply (no special flattening).
- `RouterPrimitive` MAY be composed with recovery primitives (e.g., `RetryPrimitive(RouterPrimitive(...))`).

## 4. Edge Cases

| Input | Expected Behavior |
|-------|-------------------|
| `router_fn` returns empty string | Looks up `""` in routes; raises `ValueError` if not found |
| `routes` dict is empty | Any call raises `ValueError` (no routes to match) |
| `default` key not in `routes` | `KeyError` when attempting to look up the default |
| `router_fn` returns key matching `default` | Routes normally to that primitive |

## 5. Cross-References

- [WorkflowPrimitive Spec](workflow-primitive.spec.md) — Base class
- [Retry Primitive Spec](retry-primitive.spec.md) — Often composed with Router for resilience
- [Span Schema](../observability/span-schema.spec.md) — Span naming conventions
