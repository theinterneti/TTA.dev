# ParallelPrimitive Specification

- **Version:** 1.3.0
- **Status:** Approved
- **Package:** tta-dev-primitives
- **Source:** `platform/primitives/src/tta_dev_primitives/core/parallel.py`

## 1. Purpose

`ParallelPrimitive` executes a list of primitives concurrently, giving each the same input,
and collects all results into a list. It is the implementation behind the `|` composition operator.

## 2. Contract

### 2.1 Type Signature

```python
class ParallelPrimitive(InstrumentedPrimitive[Any, list[Any]]):
    def __init__(self, primitives: list[WorkflowPrimitive]): ...
    async def _execute_impl(self, input_data: Any, context: WorkflowContext) -> list[Any]: ...
```

### 2.2 Constructor Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `primitives` | `list[WorkflowPrimitive]` | *(required)* | List of primitives to execute concurrently |

### 2.3 Behavior Invariants

- The constructor MUST raise `ValueError` if `primitives` is empty.
- `execute()` MUST pass the same `input_data` to every primitive.
- Each branch MUST receive its own child context via `context.create_child_context()`.
- `execute()` MUST use `asyncio.gather()` for concurrent execution.
- `execute()` MUST return a `list` of results in the same order as the `primitives` list.
- If any branch raises an exception, the exception MUST propagate (fail-fast).
- The `|` operator MUST flatten nested `ParallelPrimitive` instances
  (e.g., `ParallelPrimitive([A, B]) | C` → `ParallelPrimitive([A, B, C])`).

### 2.4 Error Contract

| Condition | Exception | Description |
|-----------|-----------|-------------|
| Empty `primitives` list | `ValueError` | Constructor rejects empty parallel sets |
| Any branch raises | *(propagated)* | First exception from `asyncio.gather()` propagates |

### 2.5 Observability Contract

**Spans:**

| Span Name | Attributes | Description |
|-----------|------------|-------------|
| `parallel.branch_{idx}` | `branch.index`, `branch.name`, `branch.primitive_type`, `branch.total_branches`, `branch.status`, `branch.error` | One span per branch |

**Checkpoints:**

| Checkpoint | When |
|------------|------|
| `parallel.fan_out` | Before concurrent execution begins |
| `parallel.branch_{idx}.start` | Before each branch executes |
| `parallel.branch_{idx}.end` | After each branch completes |
| `parallel.fan_in` | After all branches complete |

**Metrics:** Per-branch execution duration recorded via `metrics_collector.record_execution()`.

## 3. Composition Rules

- `ParallelPrimitive | other` MUST flatten: appends `other` to the internal list.
- `ParallelPrimitive >> other` creates a `SequentialPrimitive` (standard behavior).

## 4. Edge Cases

| Input | Expected Behavior |
|-------|-------------------|
| Single-element list | Returns `[result]` (single-element list) |
| All branches return `None` | Returns `[None, None, ...]` |
| Branch modifies `context.state` | Changes are isolated per child context |
| One branch is slow | Other branches are not blocked; result ordering matches primitive ordering |

## 5. Cross-References

- [WorkflowPrimitive Spec](workflow-primitive.spec.md) — Base class and `|` operator
- [SequentialPrimitive Spec](sequential-primitive.spec.md) — Sequential counterpart
- [Span Schema](../observability/span-schema.spec.md) — Span naming conventions
