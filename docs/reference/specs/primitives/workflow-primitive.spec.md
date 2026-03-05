# WorkflowPrimitive & WorkflowContext Specification

- **Version:** 1.3.0
- **Status:** Approved
- **Package:** tta-dev-primitives
- **Source:** `platform/primitives/src/tta_dev_primitives/core/base.py`

## 1. Purpose

`WorkflowPrimitive[T, U]` is the abstract base class for all TTA.dev workflow primitives.
It defines the universal `execute()` contract and composition operators (`>>`, `|`) that
enable primitives to be chained into complex workflows.

`WorkflowContext` is a Pydantic `BaseModel` that carries execution metadata, tracing context,
and state through a workflow. Every primitive receives a context and may read or update it.

## 2. WorkflowContext Contract

### 2.1 Type Signature

```python
class WorkflowContext(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
```

### 2.2 Constructor Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `workflow_id` | `str \| None` | `None` | Unique identifier for the workflow instance |
| `session_id` | `str \| None` | `None` | Session identifier for grouping related workflows |
| `player_id` | `str \| None` | `None` | User/agent identifier |
| `metadata` | `dict[str, Any]` | `{}` | Arbitrary metadata passed through the workflow |
| `state` | `dict[str, Any]` | `{}` | Mutable state shared across primitives in a workflow |
| `trace_id` | `str \| None` | `None` | W3C Trace Context trace ID (32-char hex) |
| `span_id` | `str \| None` | `None` | W3C Trace Context span ID (16-char hex) |
| `parent_span_id` | `str \| None` | `None` | Parent span ID for distributed tracing |
| `trace_flags` | `int` | `1` | W3C Trace Context flags (1 = sampled) |
| `correlation_id` | `str` | `uuid4()` | Unique ID correlating related operations |
| `causation_id` | `str \| None` | `None` | ID of the event that caused this workflow |
| `baggage` | `dict[str, str]` | `{}` | W3C Baggage key-value pairs propagated across services |
| `tags` | `dict[str, str]` | `{}` | Custom tags for filtering and grouping |
| `start_time` | `float` | `time.time()` | Workflow start timestamp (epoch seconds) |
| `checkpoints` | `list[tuple[str, float]]` | `[]` | Named timing checkpoints `(name, timestamp)` |

### 2.3 Behavior Invariants

- `checkpoint(name)` MUST append `(name, time.time())` to `checkpoints`.
- `elapsed_ms()` MUST return `(time.time() - start_time) * 1000`.
- `create_child_context()` MUST return a new `WorkflowContext` that inherits `workflow_id`,
  `session_id`, `player_id`, `trace_id`, `span_id` (as `parent_span_id`), `trace_flags`,
  `correlation_id`, `baggage`, and `tags` from the parent.
- `create_child_context()` MUST generate a new `correlation_id` for the child.
- `to_otel_context()` MUST return a `dict` containing `workflow.id`, `session.id`, `player.id`,
  `correlation.id`, `causation.id`, and all `tags` prefixed with `tag.`.

## 3. WorkflowPrimitive Contract

### 3.1 Type Signature

```python
class WorkflowPrimitive(Generic[T, U], ABC):
    @abstractmethod
    async def execute(self, input_data: T, context: WorkflowContext) -> U: ...
```

### 3.2 Behavior Invariants

- `execute()` MUST be an async method accepting `input_data` of type `T` and `context` of type `WorkflowContext`.
- `execute()` MUST return a value of type `U`.
- `execute()` MAY raise any exception; callers MUST handle exceptions appropriately.
- Implementations MUST NOT modify `input_data`; they SHOULD treat it as immutable.
- Implementations MAY read and write `context.state` and `context.metadata`.

### 3.3 Composition Operators

| Operator | Signature | Returns | Semantics |
|----------|-----------|---------|-----------|
| `>>` | `WorkflowPrimitive[T, U] >> WorkflowPrimitive[U, V]` | `SequentialPrimitive[T, V]` | Sequential: output of left becomes input of right |
| `\|` | `WorkflowPrimitive[T, U] \| WorkflowPrimitive[T, U]` | `ParallelPrimitive[T, list[U]]` | Parallel: both receive same input, results collected |

- `>>` MUST create a `SequentialPrimitive` wrapping both operands.
- `|` MUST create a `ParallelPrimitive` wrapping both operands.
- Both operators MUST flatten nested compositions (e.g., `(A >> B) >> C` → `SequentialPrimitive([A, B, C])`).

## 4. LambdaPrimitive Contract

### 4.1 Type Signature

```python
class LambdaPrimitive(WorkflowPrimitive[T, U]):
    def __init__(self, func: Callable[[T, WorkflowContext], U | Awaitable[U]]): ...
```

### 4.2 Behavior Invariants

- MUST accept both sync and async functions.
- MUST detect async at init time via `asyncio.iscoroutinefunction()`.
- MUST call the wrapped function with `(input_data, context)`.
- MUST NOT catch exceptions from the wrapped function.

## 5. Edge Cases

| Input | Expected Behavior |
|-------|-------------------|
| `WorkflowContext()` with no arguments | All fields use defaults; `correlation_id` is auto-generated UUID |
| `create_child_context()` called multiple times | Each child gets independent `correlation_id` |
| `>> operator` with non-WorkflowPrimitive | `TypeError` raised by Python |
| `LambdaPrimitive(sync_fn)` | Sync function called directly (not awaited) |

## 6. Cross-References

- [SequentialPrimitive Spec](sequential-primitive.spec.md)
- [ParallelPrimitive Spec](parallel-primitive.spec.md)
- [Span Schema](../observability/span-schema.spec.md) — Observability for InstrumentedPrimitive
- [Context Propagation](../observability/context-propagation.spec.md) — W3C Trace Context
