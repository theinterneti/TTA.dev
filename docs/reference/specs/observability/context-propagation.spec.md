# Context Propagation Specification

- **Version:** 1.0.0
- **Status:** Approved
- **Package:** tta-dev-primitives (observability module)
- **Source:** `platform/primitives/src/tta_dev_primitives/observability/context_propagation.py`

## 1. Purpose

This specification defines how W3C Trace Context and W3C Baggage are propagated through
TTA.dev workflows. It covers injection (writing trace data to `WorkflowContext`), extraction
(reading trace data from `WorkflowContext`), span linking, and baggage propagation.

## 2. W3C Trace Context Fields

| Field | Type | Format | Description |
|-------|------|--------|-------------|
| `trace_id` | `str` | 32-character hex (128-bit) | Unique trace identifier |
| `span_id` | `str` | 16-character hex (64-bit) | Current span identifier |
| `parent_span_id` | `str \| None` | 16-character hex (64-bit) | Parent span identifier |
| `trace_flags` | `int` | Integer (default 1) | W3C trace flags; 1 = sampled |

These fields are stored on `WorkflowContext` and propagated through `create_child_context()`.

## 3. Injection Contract

Function: `inject_trace_context(context: WorkflowContext) -> WorkflowContext`

### Behavior Invariants

- MUST extract the current active OpenTelemetry span.
- MUST validate that the span is recording and has a valid span context.
- MUST set `context.trace_id` to the span's trace ID as a 32-character hex string.
- MUST set `context.span_id` to the span's span ID as a 16-character hex string.
- MUST set `context.trace_flags` to the span's trace flags.
- If no active span exists, MUST return the context unmodified.
- MUST NOT raise exceptions; failures MUST be handled silently.

## 4. Extraction Contract

Function: `extract_trace_context(context: WorkflowContext) -> SpanContext | None`

### Behavior Invariants

- MUST read `trace_id`, `span_id`, and `trace_flags` from `WorkflowContext`.
- MUST parse `trace_id` as a 128-bit integer from hex.
- MUST parse `span_id` as a 64-bit integer from hex.
- MUST return a `SpanContext` with the parsed values.
- If any field is missing or invalid, MUST return `None`.
- MUST NOT raise exceptions; invalid input MUST return `None`.

## 5. Span Linking Contract

Function: `create_linked_span(tracer, name: str, context: WorkflowContext) -> Span`

### Behavior Invariants

- MUST create a new span linked to the parent context extracted from `WorkflowContext`.
- MUST update `WorkflowContext` with the new span's `trace_id`, `span_id`, and `parent_span_id`.
- If no parent context can be extracted, MUST create a root span.
- The link between parent and child MUST use OpenTelemetry `Link` objects.

## 6. Baggage Propagation Contract

### Propagate: `propagate_baggage(context: WorkflowContext) -> None`

- MUST iterate over `context.baggage` dict entries.
- MUST set each key-value pair as OpenTelemetry baggage using `opentelemetry.baggage.set_baggage()`.
- MUST NOT modify `context.baggage`.
- If `opentelemetry.baggage` is unavailable, MUST degrade silently.

### Extract: `extract_baggage(context: WorkflowContext) -> WorkflowContext`

- MUST read all baggage from the current OpenTelemetry context.
- MUST update `context.baggage` with the extracted key-value pairs.
- MUST return the updated context.
- If no baggage exists, MUST return the context unchanged.

## 7. Child Context Propagation

When `WorkflowContext.create_child_context()` is called:

- The child MUST inherit: `workflow_id`, `session_id`, `player_id`, `trace_id`, `trace_flags`, `baggage`, `tags`.
- The child MUST set `parent_span_id` to the parent's `span_id`.
- The child MUST generate a new `correlation_id`.
- The child MUST NOT inherit: `state`, `checkpoints`, `metadata` (these are fresh).

## 8. Graceful Degradation

- All propagation functions MUST work without OpenTelemetry installed.
- If `opentelemetry` is not available, injection and extraction MUST be no-ops.
- Baggage propagation MUST silently skip if `opentelemetry.baggage` is unavailable.
- Context propagation failures MUST NOT affect primitive execution.

## 9. Cross-References

- [Span Schema](span-schema.spec.md) — Span definitions that use propagated context
- [Metrics Catalog](metrics-catalog.spec.md) — Metrics that reference trace context
- [WorkflowPrimitive Spec](../primitives/workflow-primitive.spec.md) — WorkflowContext field definitions
