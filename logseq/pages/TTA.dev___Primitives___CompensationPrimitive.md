# CompensationPrimitive

type:: [[Primitive]]
category:: [[Recovery]]
status:: [[Stable]]
version:: 0.1.0
package:: [[tta-dev-primitives]]
test-coverage:: 100%
complexity:: [[High]]
import-path:: from tta_dev_primitives.recovery import SagaPrimitive

---

## Overview

- id:: compensation-primitive-overview
  **CompensationPrimitive** (also known as **SagaPrimitive**) implements the Saga pattern for distributed transactions. Executes a forward operation and automatically runs a compensation (rollback) operation if the forward operation fails. Essential for maintaining consistency across distributed systems and multi-step workflows where partial failures require cleanup.

---

## Use Cases

- **Distributed Transactions** - Coordinate operations across multiple services
- **Multi-Step Workflows** - Rollback previous steps if later step fails
- **Payment Processing** - Refund on failure
- **Resource Allocation** - Free resources if allocation chain fails
- **Database Operations** - Rollback changes on validation failure
- **External API Orchestration** - Cleanup side effects if workflow fails

---

## Key Benefits

- **Consistency** - Maintain system consistency despite failures
- **Automatic Rollback** - Compensation runs automatically on failure
- **Distributed Coordination** - Works across service boundaries
- **Error Transparency** - Original error propagates after compensation
- **Full Observability** - Logs and traces both forward and compensation
- **Composability** - Chain multiple sagas for complex transactions

---

## API Reference

### Constructor

```python
def __init__(
    self,
    forward: WorkflowPrimitive,
    compensation: WorkflowPrimitive
)
```

**Parameters:**
- `forward` (WorkflowPrimitive) - Forward transaction primitive
- `compensation` (WorkflowPrimitive) - Compensation primitive (runs on failure)

**Returns:** SagaPrimitive instance

### Execute Method

```python
async def execute(self, input_data: Any, context: WorkflowContext) -> Any
```

**Parameters:**
- `input_data` (Any) - Input data for the forward operation
- `context` (WorkflowContext) - Workflow context

**Returns:** Output from forward primitive (if successful)

**Raises:** Original exception after running compensation

**Behavior:**
1. Execute forward primitive
2. If success → return result
3. If failure → run compensation, then raise original error

---

## Examples

### Example 1: Database Transaction with Rollback

- id:: compensation-database-example

```python
from tta_dev_primitives.recovery import SagaPrimitive
from tta_dev_primitives import LambdaPrimitive, WorkflowContext

# Forward: Create user record
create_user = LambdaPrimitive(lambda data, ctx: {
    "user_id": db.create_user(data["email"], data["name"]),
    **data
})

# Compensation: Delete user record
delete_user = LambdaPrimitive(lambda data, ctx:
    db.delete_user(data["user_id"]) if "user_id" in data else None
)

# Saga: Auto-rollback on failure
user_creation_saga = SagaPrimitive(
    forward=create_user,
    compensation=delete_user
)

context = WorkflowContext()

try:
    result = await user_creation_saga.execute(
        {"email": "user@example.com", "name": "John"},
        context
    )
    # Success: User created
    print(f"Created user: {result['user_id']}")

except Exception as e:
    # Failure: User automatically deleted (compensated)
    print(f"Failed and rolled back: {e}")
```

### Example 2: Payment Processing

- id:: compensation-payment-example

```python
# Forward: Charge credit card
charge_card = LambdaPrimitive(lambda data, ctx: {
    "charge_id": payment_provider.charge(data["card"], data["amount"]),
    **data
})

# Compensation: Refund charge
refund_card = LambdaPrimitive(lambda data, ctx:
    payment_provider.refund(data["charge_id"]) if "charge_id" in data else None
)

# Saga: Auto-refund on failure
payment_saga = SagaPrimitive(
    forward=charge_card,
    compensation=refund_card
)

# If order processing fails after payment, refund automatically
try:
    payment_result = await payment_saga.execute(
        {"card": "tok_visa", "amount": 4999},  # $49.99
        context
    )
    # Continue with order processing
    await process_order(payment_result)

except Exception as e:
    # Payment was automatically refunded
    logger.error(f"Order failed, payment refunded: {e}")
```

### Example 3: Multi-Service Saga Chain

- id:: compensation-chain-example

```python
# Saga 1: Inventory reservation
reserve_inventory = LambdaPrimitive(lambda data, ctx: inventory_service.reserve(data))
release_inventory = LambdaPrimitive(lambda data, ctx: inventory_service.release(data))
inventory_saga = SagaPrimitive(reserve_inventory, release_inventory)

# Saga 2: Payment processing
charge_payment = LambdaPrimitive(lambda data, ctx: payment_service.charge(data))
refund_payment = LambdaPrimitive(lambda data, ctx: payment_service.refund(data))
payment_saga = SagaPrimitive(charge_payment, refund_payment)

# Saga 3: Shipping label creation
create_shipping = LambdaPrimitive(lambda data, ctx: shipping_service.create_label(data))
cancel_shipping = LambdaPrimitive(lambda data, ctx: shipping_service.cancel_label(data))
shipping_saga = SagaPrimitive(create_shipping, cancel_shipping)

# Chain sagas: Each compensates on failure
order_workflow = inventory_saga >> payment_saga >> shipping_saga

# If shipping fails:
# 1. Shipping compensation runs (cancel label)
# 2. Payment compensation runs (refund)
# 3. Inventory compensation runs (release)
# System returns to consistent state!
```

### Example 4: Resource Allocation

- id:: compensation-resource-example

```python
# Forward: Allocate GPU resources
allocate_gpu = LambdaPrimitive(lambda data, ctx: {
    "gpu_id": gpu_cluster.allocate(data["model_size"]),
    **data
})

# Compensation: Free GPU
free_gpu = LambdaPrimitive(lambda data, ctx:
    gpu_cluster.free(data["gpu_id"]) if "gpu_id" in data else None
)

# Saga: Auto-free GPU on failure
gpu_saga = SagaPrimitive(
    forward=allocate_gpu,
    compensation=free_gpu
)

# Use GPU for inference
try:
    allocation = await gpu_saga.execute({"model_size": "7B"}, context)
    result = await run_inference(allocation["gpu_id"], prompt)

except Exception as e:
    # GPU automatically freed
    logger.error(f"Inference failed, GPU freed: {e}")
```

### Example 5: External API Coordination

- id:: compensation-api-coordination

```python
# Forward: Create resources in 3 services
create_in_service_a = LambdaPrimitive(lambda data, ctx: service_a.create(data))
create_in_service_b = LambdaPrimitive(lambda data, ctx: service_b.create(data))
create_in_service_c = LambdaPrimitive(lambda data, ctx: service_c.create(data))

# Compensation: Delete resources
delete_from_service_a = LambdaPrimitive(lambda data, ctx: service_a.delete(data.get("id_a")))
delete_from_service_b = LambdaPrimitive(lambda data, ctx: service_b.delete(data.get("id_b")))
delete_from_service_c = LambdaPrimitive(lambda data, ctx: service_c.delete(data.get("id_c")))

# Build saga chain
saga_a = SagaPrimitive(create_in_service_a, delete_from_service_a)
saga_b = SagaPrimitive(create_in_service_b, delete_from_service_b)
saga_c = SagaPrimitive(create_in_service_c, delete_from_service_c)

# Sequential execution with compensation
workflow = saga_a >> saga_b >> saga_c

# If service C fails:
# - Service C compensation runs (no-op, nothing created)
# - Service B compensation runs (deletes resource)
# - Service A compensation runs (deletes resource)
# All services back to original state!
```

---

## Composition Patterns

### Sequential Saga Chain

- id:: compensation-pattern-sequential

```python
# Each step compensates on failure
workflow = saga1 >> saga2 >> saga3 >> saga4

# Failure at saga3:
# 1. saga3 compensation runs
# 2. saga2 compensation runs
# 3. saga1 compensation runs
# Chain unwinds in reverse order
```

### Saga with Retry

- id:: compensation-pattern-retry

```python
from tta_dev_primitives.recovery import RetryPrimitive

# Retry forward operation before compensation
saga_with_retry = SagaPrimitive(
    forward=RetryPrimitive(operation, max_retries=3),
    compensation=rollback_operation
)

# Only compensates if all retries fail
```

### Nested Sagas

- id:: compensation-pattern-nested

```python
# Inner saga
inner_saga = SagaPrimitive(inner_forward, inner_compensation)

# Outer saga (contains inner saga as forward operation)
outer_saga = SagaPrimitive(
    forward=inner_saga,
    compensation=outer_compensation
)

# Compensation order: inner first, then outer
```

---

## Best Practices

### Designing Compensation Logic

✅ **Idempotent compensations** - Safe to run multiple times
✅ **Check before compensation** - Only compensate if forward succeeded
✅ **Store compensation data** - Forward operation should capture IDs needed for compensation
✅ **Log compensation execution** - Track when compensation runs
✅ **Test compensation paths** - Unit tests for rollback scenarios

### Idempotency Example

```python
# Good: Idempotent compensation
delete_user = LambdaPrimitive(lambda data, ctx:
    db.delete_user(data["user_id"]) if data.get("user_id") and db.user_exists(data["user_id"]) else None
)

# Bad: Not idempotent (errors if user already deleted)
delete_user_bad = LambdaPrimitive(lambda data, ctx:
    db.delete_user(data["user_id"])  # Throws error if user doesn't exist
)
```

### What to Compensate

✅ **Compensate:** Database writes, API calls, resource allocations
✅ **Don't compensate:** Read operations, idempotent operations
✅ **Partial compensation:** If forward partially succeeded, compensate only completed parts

### Don'ts

❌ Don't swallow compensation errors (log and alert)
❌ Don't make compensation fail (must be reliable)
❌ Don't forget compensation data (store IDs in data object)
❌ Don't compensate non-reversible operations (think carefully)
❌ Don't use for simple retry (use RetryPrimitive instead)

---

## Error Handling

### Compensation Failure

If compensation fails, the system logs the error but re-raises the original exception:

```python
try:
    result = await saga.execute(input_data, context)
except Exception as original_error:
    # Compensation was attempted
    # If compensation failed, it's logged but doesn't mask original error
    raise  # Original error propagates
```

### Monitoring Compensation

```python
# Check if compensation ran
compensation_count = context.metadata.get("compensation_count", 0)

# Alert if compensation runs frequently
if compensation_count > threshold:
    alert_team("High compensation rate - investigate failures")
```

---

## Real-World Example: E-Commerce Order Processing

```python
from tta_dev_primitives import SequentialPrimitive
from tta_dev_primitives.recovery import SagaPrimitive, RetryPrimitive
from tta_dev_primitives import LambdaPrimitive

# Step 1: Validate inventory
check_inventory = LambdaPrimitive(lambda data, ctx: {
    **data,
    "inventory_valid": inventory_service.check_availability(data["items"])
})

# Step 2: Reserve inventory (with compensation)
reserve_items = LambdaPrimitive(lambda data, ctx: {
    **data,
    "reservation_id": inventory_service.reserve(data["items"])
})
release_items = LambdaPrimitive(lambda data, ctx:
    inventory_service.release(data.get("reservation_id"))
)
inventory_saga = SagaPrimitive(reserve_items, release_items)

# Step 3: Charge payment (with compensation and retry)
charge_card = LambdaPrimitive(lambda data, ctx: {
    **data,
    "charge_id": payment_service.charge(data["payment_method"], data["amount"])
})
refund_card = LambdaPrimitive(lambda data, ctx:
    payment_service.refund(data.get("charge_id"))
)
# Retry payment 3 times before compensation
payment_saga = SagaPrimitive(
    forward=RetryPrimitive(charge_card, max_retries=3),
    compensation=refund_card
)

# Step 4: Create shipping label (with compensation)
create_label = LambdaPrimitive(lambda data, ctx: {
    **data,
    "tracking_id": shipping_service.create_label(data["address"])
})
cancel_label = LambdaPrimitive(lambda data, ctx:
    shipping_service.cancel(data.get("tracking_id"))
)
shipping_saga = SagaPrimitive(create_label, cancel_label)

# Step 5: Send confirmation email (no compensation needed)
send_email = LambdaPrimitive(lambda data, ctx:
    email_service.send_confirmation(data["email"], data)
)

# Complete order workflow
order_workflow = (
    check_inventory >>
    inventory_saga >>
    payment_saga >>
    shipping_saga >>
    send_email
)

# Execution scenarios:

# Success: All steps complete
order_result = await order_workflow.execute(order_data, context)

# Failure at shipping:
# 1. Shipping compensation runs (cancel label - no-op, not created yet)
# 2. Payment compensation runs (refund charge)
# 3. Inventory compensation runs (release reservation)
# Customer charged nothing, inventory released, order failed cleanly

# Failure at payment (after 3 retries):
# 1. Payment compensation runs (no-op, charge failed)
# 2. Inventory compensation runs (release reservation)
# Inventory released, customer not charged, order failed cleanly
```

---

## Testing

### Testing Saga Pattern

```python
import pytest
from tta_dev_primitives.recovery import SagaPrimitive
from tta_dev_primitives.testing import MockPrimitive
from tta_dev_primitives import WorkflowContext

@pytest.mark.asyncio
async def test_saga_success():
    forward_mock = MockPrimitive(return_value={"result": "success"})
    compensation_mock = MockPrimitive()

    saga = SagaPrimitive(forward_mock, compensation_mock)

    result = await saga.execute("input", WorkflowContext())

    assert result["result"] == "success"
    assert forward_mock.call_count == 1
    assert compensation_mock.call_count == 0  # Not called on success

@pytest.mark.asyncio
async def test_saga_compensation_on_failure():
    # Forward fails
    forward_mock = MockPrimitive(side_effect=ValueError("Forward failed"))
    compensation_mock = MockPrimitive(return_value=None)

    saga = SagaPrimitive(forward_mock, compensation_mock)

    with pytest.raises(ValueError, match="Forward failed"):
        await saga.execute("input", WorkflowContext())

    assert forward_mock.call_count == 1
    assert compensation_mock.call_count == 1  # Called on failure!
```

---

## Related Content

### Recovery Primitives

{{query (and (page-property type [[Primitive]]) (page-property category [[Recovery]]))}}

### Complementary Patterns

- [[TTA.dev/Primitives/RetryPrimitive]] - Retry before compensation
- [[TTA.dev/Primitives/FallbackPrimitive]] - Alternative to compensation
- [[TTA.dev/Guides/Error Handling Patterns]] - Comprehensive error handling

---

## Advanced Topics

### Saga vs Retry vs Fallback

**When to use each:**

- **Saga** - Need to undo side effects (database writes, API calls)
- **Retry** - Transient failures (network issues, rate limits)
- **Fallback** - Degrade gracefully (use cache, simpler alternative)

### Combining All Three

```python
# Ultimate resilience: Retry → Saga → Fallback
retry_operation = RetryPrimitive(operation, max_retries=3)

saga = SagaPrimitive(
    forward=retry_operation,
    compensation=rollback_operation
)

workflow = FallbackPrimitive(
    primary=saga,
    fallbacks=[degraded_service]
)

# Pattern:
# 1. Try operation (retry up to 3 times)
# 2. If all retries fail, compensate
# 3. If compensation fails, use degraded service
```

---

## References

- **GitHub Source:** [`platform/primitives/src/tta_dev_primitives/recovery/compensation.py`](https://github.com/theinterneti/TTA.dev/blob/main/platform/primitives/src/tta_dev_primitives/recovery/compensation.py)
- **Tests:** [`platform/primitives/tests/recovery/test_compensation.py`](https://github.com/theinterneti/TTA.dev/blob/main/platform/primitives/tests/recovery/test_compensation.py)
- **Saga Pattern:** [Microservices.io - Saga Pattern](https://microservices.io/patterns/data/saga.html)

---

**Created:** [[2025-10-30]]
**Last Updated:** [[2025-10-30]]
**Category:** [[Recovery]]
**Complexity:** [[High]]
**Also Known As:** SagaPrimitive
