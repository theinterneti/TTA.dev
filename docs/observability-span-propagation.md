# OTel Span Context Propagation

This document explains how TTA.dev primitives propagate OpenTelemetry trace and span IDs
through multi-step, multi-agent workflows using `WorkflowContext`.

## How It Works

Every primitive execution receives a `WorkflowContext` that carries W3C Trace Context
identifiers:

| Field | Description |
|-------|-------------|
| `trace_id` | Hex string — shared across the entire request tree |
| `span_id` | Hex string — identifies **this** span within the trace |
| `parent_span_id` | Hex string — the span that caused this one; `None` for root spans |

### `create_child_context()`

The core propagation mechanism is `WorkflowContext.create_child_context()`:

```python
child_ctx = context.create_child_context()
# child_ctx.parent_span_id == context.span_id   ✅
# child_ctx.trace_id        == context.trace_id  ✅
# child_ctx.correlation_id  == context.correlation_id ✅
```

## SequentialPrimitive

Each step receives its own child context, forming a tree of child spans:

```
root span
  └─ step_0_SomePrimitive   (parent_span_id = root.span_id)
  └─ step_1_OtherPrimitive  (parent_span_id = root.span_id)
  └─ step_2_FinalPrimitive  (parent_span_id = root.span_id)
```

## ParallelPrimitive

Each branch receives its own child context so parallel spans nest correctly:

```
root span
  ├─ branch_0  (parent_span_id = root.span_id)
  ├─ branch_1  (parent_span_id = root.span_id)
  └─ branch_2  (parent_span_id = root.span_id)
```

## Multi-Agent Handoffs

Serialize the span hierarchy with `to_otel_context()`:

```python
otel_attrs = context.to_otel_context()
# {
#   "workflow.span_id":        "aabb...3344",
#   "workflow.parent_span_id": "unknown",
#   "workflow.trace_id":       "0102...0f10",   (if set)
#   "workflow.correlation_id": "uuid-...",
#   "workflow.id":             "my-workflow",
#   "workflow.elapsed_ms":     42.0,
# }

# Receiving agent reconstructs with caller as parent
received_ctx = WorkflowContext(
    workflow_id=otel_attrs["workflow.id"],
    trace_id=otel_attrs.get("workflow.trace_id"),
    parent_span_id=otel_attrs["workflow.span_id"],
    correlation_id=otel_attrs["workflow.correlation_id"],
)
```

## Tests

See `tests/integration/test_otel_span_propagation.py` for five integration tests:

| Test | Verifies |
|------|----------|
| `test_workflow_context_child_has_parent_span_id` | `create_child_context()` wires `parent_span_id` |
| `test_nested_children_form_correct_chain` | root → child → grandchild links correctly |
| `test_sequential_primitive_creates_child_contexts` | each Sequential step gets a child context |
| `test_to_otel_context_includes_span_ids` | `to_otel_context()` exposes span IDs |
| `test_parallel_primitive_creates_child_contexts` | each Parallel branch gets a child context |
