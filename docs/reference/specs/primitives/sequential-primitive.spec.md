# SequentialPrimitive Specification

- **Version:** 1.3.0
- **Status:** Approved
- **Package:** tta-dev-primitives
- **Source:** `platform/primitives/src/tta_dev_primitives/core/sequential.py`

## 1. Purpose

`SequentialPrimitive` executes a list of primitives in order, passing the output of each
step as the input to the next. It is the implementation behind the `>>` composition operator.

## 2. Contract

### 2.1 Type Signature

```python
class SequentialPrimitive(InstrumentedPrimitive[Any, Any]):
    def __init__(self, primitives: list[WorkflowPrimitive]): ...
    async def _execute_impl(self, input_data: Any, context: WorkflowContext) -> Any: ...
```

### 2.2 Constructor Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `primitives` | `list[WorkflowPrimitive]` | *(required)* | Ordered list of primitives to execute sequentially |

### 2.3 Behavior Invariants

- The constructor MUST raise `ValueError` if `primitives` is empty.
- `execute()` MUST pass `input_data` to the first primitive.
- For each subsequent primitive, `execute()` MUST pass the output of the previous primitive as input.
- `execute()` MUST return the output of the last primitive.
- If any primitive raises an exception, execution MUST stop immediately and the exception MUST propagate.
- The `>>` operator MUST flatten nested `SequentialPrimitive` instances
  (e.g., `SequentialPrimitive([A, B]) >> C` → `SequentialPrimitive([A, B, C])`).

### 2.4 Error Contract

| Condition | Exception | Description |
|-----------|-----------|-------------|
| Empty `primitives` list | `ValueError` | Constructor rejects empty sequences |
| Any step raises | *(propagated)* | The exception from the failing step propagates unchanged |

### 2.5 Observability Contract

**Spans:**

| Span Name | Attributes | Description |
|-----------|------------|-------------|
| `sequential.step_{i}` | `step.index`, `step.name`, `step.primitive_type`, `step.total_steps`, `step.status`, `step.error` | One span per step |

**Checkpoints:**

| Checkpoint | When |
|------------|------|
| `sequential.step_{i}.start` | Before each step executes |
| `sequential.step_{i}.end` | After each step completes |

**Metrics:** Per-step execution duration recorded via `metrics_collector.record_execution()`.

## 3. Composition Rules

- `SequentialPrimitive >> other` MUST flatten: appends `other` to the internal list.
- `SequentialPrimitive | other` creates a `ParallelPrimitive` (standard behavior).

## 4. Edge Cases

| Input | Expected Behavior |
|-------|-------------------|
| Single-element list | Behaves as pass-through for that one primitive |
| Step returns `None` | `None` is passed as input to the next step |
| Step modifies `context.state` | Modifications are visible to subsequent steps |

## 5. Cross-References

- [WorkflowPrimitive Spec](workflow-primitive.spec.md) — Base class and `>>` operator
- [ParallelPrimitive Spec](parallel-primitive.spec.md) — Parallel counterpart
- [Span Schema](../observability/span-schema.spec.md) — Span naming conventions
