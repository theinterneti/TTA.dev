# CompensationPrimitive & SagaPrimitive Specification

- **Version:** 1.3.0
- **Status:** Approved
- **Package:** tta-dev-primitives
- **Source:** `platform/primitives/src/tta_dev_primitives/recovery/compensation.py`

## 1. Purpose

`SagaPrimitive` implements the Saga pattern for distributed transactions. It executes
a forward (transaction) primitive and, if the forward fails, automatically executes a
compensation (rollback) primitive to undo side effects.

`CompensationPrimitive` is an alias for `SagaPrimitive` provided for backward compatibility.

## 2. Contract

### 2.1 Type Signature

```python
@dataclass
class CompensationStrategy:
    compensation_primitive: WorkflowPrimitive


class SagaPrimitive(WorkflowPrimitive[Any, Any]):
    def __init__(
        self,
        forward: WorkflowPrimitive,
        compensation: WorkflowPrimitive,
    ): ...


class CompensationPrimitive(SagaPrimitive):
    """Alias for SagaPrimitive — identical behavior."""
    pass
```

### 2.2 Constructor Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `forward` | `WorkflowPrimitive` | *(required)* | Forward transaction primitive |
| `compensation` | `WorkflowPrimitive` | *(required)* | Compensation (rollback) primitive executed on forward failure |

### 2.3 Behavior Invariants

- `execute()` MUST attempt the `forward` primitive first.
- If `forward` succeeds, `execute()` MUST return its result immediately.
- If `forward` fails, `execute()` MUST:
  1. Execute the `compensation` primitive with the same `input_data`.
  2. Re-raise the original forward exception after compensation completes.
- If compensation also fails, `execute()` MUST still re-raise the original forward exception.
- The compensation primitive MUST receive the same `input_data` as the forward primitive.
- Compensation failure MUST be logged but MUST NOT replace the original exception.

### 2.4 Error Contract

| Condition | Exception | Description |
|-----------|-----------|-------------|
| Forward succeeds | *(none)* | Returns forward result |
| Forward fails, compensation succeeds | *(forward exception)* | Original forward exception is re-raised |
| Forward fails, compensation fails | *(forward exception)* | Original forward exception is re-raised; compensation failure is logged |

### 2.5 Observability Contract

**Spans:**

| Span Name | Attributes | Description |
|-----------|------------|-------------|
| `saga.forward` | `saga.execution`, `saga.forward_type`, `saga.status`, `saga.error` | Span for forward attempt |
| `saga.compensation` | `saga.execution`, `saga.compensation_type`, `saga.status`, `saga.compensation_triggered`, `saga.forward_error` | Span for compensation attempt |

**Checkpoints:**

| Checkpoint | When |
|------------|------|
| `saga.start` | Before forward attempt |
| `saga.forward.start` | Before forward executes |
| `saga.forward.end` | After forward completes or fails |
| `saga.compensation.start` | Before compensation executes (only on forward failure) |
| `saga.compensation.end` | After compensation completes or fails |
| `saga.end` | After final result or failure |

**Metrics:** Forward and compensation duration recorded via `metrics_collector.record_execution()`.

**Logging:**

| Event | Level | Description |
|-------|-------|-------------|
| `saga_workflow_start` | INFO | Saga execution begins |
| `saga_forward_success` | INFO | Forward completed successfully |
| `saga_forward_failed` | WARNING | Forward failed, triggering compensation |
| `saga_compensation_triggered` | INFO | Compensation is starting |
| `saga_compensation_success` | INFO | Compensation completed successfully |
| `saga_compensation_failed` | ERROR | Compensation also failed |
| `saga_critical_failure` | ERROR | Both forward and compensation failed |

## 3. Composition Rules

- Standard `>>` and `|` operators apply.
- `SagaPrimitive(A, A_rollback) >> SagaPrimitive(B, B_rollback)` — sequential sagas.
- For multi-step sagas, compose individual `SagaPrimitive` steps sequentially.

## 4. Edge Cases

| Input | Expected Behavior |
|-------|-------------------|
| Forward and compensation are the same primitive | Valid; forward runs, then same primitive runs as compensation |
| Compensation modifies `context.state` | Modifications persist even though the forward exception is re-raised |
| Forward raises `SystemExit` or `KeyboardInterrupt` | May not trigger compensation (depends on exception hierarchy) |

## 5. Cross-References

- [WorkflowPrimitive Spec](workflow-primitive.spec.md) — Base class
- [RetryPrimitive Spec](retry-primitive.spec.md) — Can wrap SagaPrimitive for retry-with-rollback
- [FallbackPrimitive Spec](fallback-primitive.spec.md) — Alternative recovery without rollback
- [Span Schema](../observability/span-schema.spec.md) — Span naming conventions
