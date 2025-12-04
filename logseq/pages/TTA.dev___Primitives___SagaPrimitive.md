# SagaPrimitive

type:: [[Primitive]]
category:: [[Recovery]]
package:: [[TTA.dev/Packages/tta-dev-primitives]]
status:: [[Stable]]
version:: 1.0.0
test-coverage:: 95
complexity:: [[Medium]]
python-class:: `SagaPrimitive`
import-path:: `from tta_dev_primitives.recovery import SagaPrimitive`
related-primitives:: [[TTA.dev/Primitives/CompensationPrimitive]], [[TTA.dev/Primitives/FallbackPrimitive]], [[TTA.dev/Primitives/RetryPrimitive]]

---

## Overview

- id:: saga-primitive-overview
  Implements the Saga pattern for maintaining consistency across distributed operations. Executes a forward transaction and automatically runs compensation (rollback) on failure.

  **Think of it as:** A transaction manager that ensures either all steps complete successfully, or previous steps are properly undone.

---

## Use Cases

- id:: saga-primitive-use-cases
  - **Distributed transactions:** Maintain consistency across services
  - **State management:** Rollback world/game state on errors
  - **Multi-step workflows:** Ensure atomic execution of related operations
  - **API orchestration:** Undo previous API calls on failure
  - **Data consistency:** Keep data synchronized across systems

---

## Key Benefits

- id:: saga-primitive-benefits
  - ✅ **Automatic rollback** - Compensation runs on any failure
  - ✅ **Composable** - Works with all TTA.dev primitives
  - ✅ **Observable** - Full tracing of forward and compensation steps
  - ✅ **Type-safe** - Generic types for input/output
  - ✅ **Async support** - Both forward and compensation are async

---

## API Reference

- id:: saga-primitive-api

### Constructor

```python
SagaPrimitive(
    forward: WorkflowPrimitive,      # Main operation
    compensation: WorkflowPrimitive  # Rollback operation
)
```

**Note:** `CompensationPrimitive` is an alias for `SagaPrimitive`.

---

## Examples

### Basic Saga

- id:: saga-basic-example

```python
from tta_dev_primitives.recovery import SagaPrimitive
from tta_dev_primitives import WorkflowContext

# Create saga with forward and compensation
saga = SagaPrimitive(
    forward=update_world_state,
    compensation=rollback_world_state
)

context = WorkflowContext(correlation_id="saga-001")
result = await saga.execute({"action": "create_item"}, context)
```

### Multi-Step Saga

- id:: saga-multi-step-example

```python
# Chain multiple sagas for complex transactions
create_order = SagaPrimitive(
    forward=create_order_primitive,
    compensation=cancel_order_primitive
)

reserve_inventory = SagaPrimitive(
    forward=reserve_stock_primitive,
    compensation=release_stock_primitive
)

charge_payment = SagaPrimitive(
    forward=charge_card_primitive,
    compensation=refund_card_primitive
)

# Full workflow - if any step fails, previous steps are compensated
workflow = create_order >> reserve_inventory >> charge_payment
```

### With State Rollback

- id:: saga-state-example

```python
async def update_game_state(data, context):
    """Forward: Apply game state change."""
    return await game_service.apply_change(data)

async def rollback_game_state(data, context):
    """Compensation: Revert game state."""
    return await game_service.revert_change(data)

saga = SagaPrimitive(
    forward=LambdaPrimitive(update_game_state),
    compensation=LambdaPrimitive(rollback_game_state)
)
```

---

## Saga Pattern Flow

- id:: saga-pattern-flow

```
┌─────────────────────────────────────────┐
│           Execute Forward               │
└─────────────────┬───────────────────────┘
                  │
         ┌────────┴────────┐
         │                 │
    ✅ Success        ❌ Failure
         │                 │
         ▼                 ▼
┌─────────────────┐ ┌─────────────────┐
│  Return Result  │ │ Run Compensation│
└─────────────────┘ └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │  Re-raise Error │
                    └─────────────────┘
```

---

## Best Practices

- id:: saga-best-practices

✅ **Idempotent compensation** - Compensation should be safe to run multiple times
✅ **Log all steps** - Essential for debugging saga failures
✅ **Test compensation paths** - Verify rollback works correctly
✅ **Use with timeouts** - Combine with TimeoutPrimitive for long operations

❌ **Don't assume compensation succeeds** - Handle compensation failures too
❌ **Don't skip observability** - Sagas need detailed tracing

---

## Related Content

### Works Well With

- [[TTA.dev/Primitives/RetryPrimitive]] - Retry before triggering compensation
- [[TTA.dev/Primitives/TimeoutPrimitive]] - Timeout long-running sagas
- [[TTA.dev/Primitives/FallbackPrimitive]] - Alternative execution paths

---

## Metadata

**Source Code:** [compensation.py](https://github.com/theinterneti/TTA.dev/blob/main/platform/primitives/src/tta_dev_primitives/recovery/compensation.py)

**Created:** [[2025-12-04]]
**Last Updated:** [[2025-12-04]]
**Status:** [[Stable]] - Production Ready
