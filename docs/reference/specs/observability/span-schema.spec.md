# OpenTelemetry Span Schema Specification

- **Version:** 1.0.0
- **Status:** Approved
- **Package:** tta-dev-primitives (observability module)
- **Source:** `platform/primitives/src/tta_dev_primitives/observability/`

## 1. Purpose

This specification defines the OpenTelemetry span schema for all TTA.dev primitives.
Every instrumented primitive emits spans following these naming conventions, attribute
schemas, and parent-child relationships.

## 2. Span Naming Convention

All spans MUST follow the pattern: `{category}.{operation}` where:
- `category` is the primitive family (e.g., `primitive`, `sequential`, `parallel`, `retry`, `fallback`, `saga`)
- `operation` is the specific operation (e.g., `step_0`, `branch_1`, `attempt_2`, `primary`, `forward`)

## 3. Base Span: InstrumentedPrimitive

All primitives extending `InstrumentedPrimitive` emit a root span.

| Field | Value |
|-------|-------|
| **Span Name** | `primitive.{name}` |
| **Source** | `observability/instrumented_primitive.py` |

**Attributes:**

| Attribute | Type | Description |
|-----------|------|-------------|
| `primitive.name` | string | Name of the primitive instance |
| `primitive.type` | string | Class name of the primitive |
| `primitive.status` | string | `"success"` or `"error"` |
| `primitive.error` | string | Error message (only on failure) |
| `workflow.id` | string | From `context.workflow_id` |
| `session.id` | string | From `context.session_id` |
| `correlation.id` | string | From `context.correlation_id` |

**Events:**

| Event | When | Attributes |
|-------|------|------------|
| `exception` | On failure | Standard OTel exception attributes |

**Links:** Linked to parent context via `create_linked_span()` using `WorkflowContext` trace fields.

## 4. Sequential Spans

| Field | Value |
|-------|-------|
| **Span Name** | `sequential.step_{i}` (where `i` is the 0-based step index) |
| **Parent** | The `InstrumentedPrimitive` root span |

**Attributes:**

| Attribute | Type | Description |
|-----------|------|-------------|
| `step.index` | int | 0-based step index |
| `step.name` | string | Name of the step primitive |
| `step.primitive_type` | string | Class name of the step primitive |
| `step.total_steps` | int | Total number of steps in the sequence |
| `step.status` | string | `"success"` or `"error"` |
| `step.error` | string | Error message (only on failure) |

## 5. Parallel Spans

| Field | Value |
|-------|-------|
| **Span Name** | `parallel.branch_{idx}` (where `idx` is the 0-based branch index) |
| **Parent** | The `InstrumentedPrimitive` root span |

**Attributes:**

| Attribute | Type | Description |
|-----------|------|-------------|
| `branch.index` | int | 0-based branch index |
| `branch.name` | string | Name of the branch primitive |
| `branch.primitive_type` | string | Class name of the branch primitive |
| `branch.total_branches` | int | Total number of parallel branches |
| `branch.status` | string | `"success"` or `"error"` |
| `branch.error` | string | Error message (only on failure) |

## 6. Conditional / Switch Spans

| Field | Value |
|-------|-------|
| **Span Name** | `conditional.branch_{branch_name}` or `switch.{case_name}` |
| **Parent** | The workflow root span |

**Attributes (Conditional):**

| Attribute | Type | Description |
|-----------|------|-------------|
| `branch.name` | string | `"then"` or `"else"` |
| `branch.condition_result` | bool | Result of the condition evaluation |
| `branch.primitive_type` | string | Class name of the selected branch |
| `branch.status` | string | `"success"` or `"error"` |
| `branch.error` | string | Error message (only on failure) |

**Attributes (Switch):**

| Attribute | Type | Description |
|-----------|------|-------------|
| `case.name` | string | Name of the selected case |
| `case.key` | string | Key returned by the selector function |
| `case.primitive_type` | string | Class name of the selected case |
| `case.status` | string | `"success"` or `"error"` |
| `case.error` | string | Error message (only on failure) |

## 7. Retry Spans

| Field | Value |
|-------|-------|
| **Span Name** | `retry.attempt_{i}` (where `i` is the 0-based attempt index) |
| **Parent** | The workflow root span |

**Attributes:**

| Attribute | Type | Description |
|-----------|------|-------------|
| `retry.attempt` | int | Current attempt number |
| `retry.max_attempts` | int | Maximum number of attempts |
| `retry.primitive_type` | string | Class name of the retried primitive |
| `retry.status` | string | `"success"` or `"error"` |
| `retry.succeeded_on_attempt` | int | Attempt number that succeeded (only on success) |
| `retry.error` | string | Error message (only on failure) |

## 8. Fallback Spans

| Field | Value |
|-------|-------|
| **Span Names** | `fallback.primary`, `fallback.fallback` |
| **Parent** | The workflow root span |

**Attributes:**

| Attribute | Type | Description |
|-----------|------|-------------|
| `fallback.execution` | string | `"primary"` or `"fallback"` |
| `fallback.primary_type` | string | Class name of primary primitive |
| `fallback.fallback_type` | string | Class name of fallback primitive |
| `fallback.status` | string | `"success"` or `"error"` |
| `fallback.used_fallback` | bool | Whether fallback was triggered |
| `fallback.error` | string | Error message (only on failure) |
| `fallback.primary_error` | string | Primary error (only in fallback span) |

## 9. Saga Spans

| Field | Value |
|-------|-------|
| **Span Names** | `saga.forward`, `saga.compensation` |
| **Parent** | The workflow root span |

**Attributes:**

| Attribute | Type | Description |
|-----------|------|-------------|
| `saga.execution` | string | `"forward"` or `"compensation"` |
| `saga.forward_type` | string | Class name of forward primitive |
| `saga.compensation_type` | string | Class name of compensation primitive |
| `saga.status` | string | `"success"` or `"error"` |
| `saga.compensation_triggered` | bool | Whether compensation was triggered |
| `saga.error` | string | Error message (only on failure) |
| `saga.forward_error` | string | Forward error (only in compensation span) |

## 10. Span Hierarchy Rules

- Composed primitives (`>>`, `|`) MUST create child spans under the parent's span.
- Each branch in a `ParallelPrimitive` MUST create an independent child span.
- `create_child_context()` MUST propagate `trace_id` and set `parent_span_id` to the current `span_id`.
- All spans MUST set status to `OK` on success and `ERROR` on failure.
- All spans MUST record exceptions using `span.record_exception()`.

## 11. Graceful Degradation

- All span creation MUST be conditional on OpenTelemetry being available.
- If `opentelemetry` is not installed, primitive execution MUST proceed without tracing.
- Span creation failures MUST NOT cause primitive execution to fail.

## 12. Cross-References

- [Metrics Catalog](metrics-catalog.spec.md) — Companion metrics specification
- [Context Propagation](context-propagation.spec.md) — W3C Trace Context propagation
- [WorkflowPrimitive Spec](../primitives/workflow-primitive.spec.md) — WorkflowContext trace fields
