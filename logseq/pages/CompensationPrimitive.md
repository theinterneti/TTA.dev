# CompensationPrimitive

**Saga pattern implementation for distributed transactions with automatic rollback on failure.**

## Overview

`CompensationPrimitive` implements the saga pattern, executing a sequence of operations where each operation has a compensation (rollback) function. If any operation fails, all previously completed operations are automatically compensated in reverse order.

**Source:** `packages/tta-dev-primitives/src/tta_dev_primitives/recovery/compensation.py`

## Basic Usage

```python
from tta_dev_primitives.recovery import CompensationPrimitive
from tta_dev_primitives import WorkflowContext

# Define operations with compensation functions
async def create_user(data: dict, context: WorkflowContext) -> dict:
    """Create user in database."""
    user_id = await db.create_user(data["email"])
    return {"user_id": user_id, **data}

async def rollback_user_creation(data: dict, context: WorkflowContext) -> None:
    """Delete user if later steps fail."""
    await db.delete_user(data["user_id"])

async def send_welcome_email(data: dict, context: WorkflowContext) -> dict:
    """Send welcome email."""
    await email_service.send(data["email"], "Welcome!")
    return {**data, "email_sent": True}

async def rollback_email(data: dict, context: WorkflowContext) -> None:
    """Log email rollback (email can't be unsent)."""
    await db.log_event(f"Email rollback for {data['email']}")

async def activate_subscription(data: dict, context: WorkflowContext) -> dict:
    """Activate user subscription."""
    await subscription_service.activate(data["user_id"])
    return {**data, "subscription_active": True}

async def rollback_subscription(data: dict, context: WorkflowContext) -> None:
    """Deactivate subscription."""
    await subscription_service.deactivate(data["user_id"])

# Build compensation workflow
workflow = CompensationPrimitive(
    primitives=[
        (create_user, rollback_user_creation),
        (send_welcome_email, rollback_email),
        (activate_subscription, rollback_subscription)
    ]
)

# Execute
context = WorkflowContext(correlation_id="signup-123")
try:
    result = await workflow.execute(
        {"email": "user@example.com"},
        context
    )
    # All steps completed successfully
except Exception as e:
    # If any step failed, all previous steps were compensated
    logger.error("signup_failed", error=str(e))
```

## Key Concepts

### Saga Pattern

**Distributed transaction pattern for long-running workflows:**

```
Step 1 → Step 2 → Step 3 → ... → Complete
  ↓         ↓         ↓
Comp 1    Comp 2    Comp 3    (if failure)
```

**Use cases:**
- Multi-service transactions
- Payment processing workflows
- User registration flows
- Order fulfillment pipelines

### Compensation Functions

**Undo operations when later steps fail:**

```python
# Forward operation
async def reserve_inventory(data, context):
    item_id = await inventory.reserve(data["product_id"], data["quantity"])
    return {**data, "item_id": item_id}

# Compensation (rollback)
async def release_inventory(data, context):
    await inventory.release(data["item_id"])
```

**Guidelines:**
- Compensation functions should be idempotent
- Log all compensations for audit
- Some operations can't be undone (log instead)
- Compensations execute in **reverse order**

### Execution Order

**Forward (success):**
```
Step 1 → Step 2 → Step 3 → Complete
```

**Rollback (failure at Step 3):**
```
Step 1 ✓ → Step 2 ✓ → Step 3 ✗
                         ↓
         Comp 2 ← Comp 1
```

**Compensation order:** Reverse of execution order

## Configuration

### Basic Configuration

```python
CompensationPrimitive(
    primitives=[
        (operation1, compensation1),
        (operation2, compensation2),
        (operation3, None)  # No compensation needed
    ]
)
```

**Parameters:**
- `primitives`: List of (operation, compensation) tuples
- `compensation` can be `None` if no rollback needed

### Advanced Configuration

```python
CompensationPrimitive(
    primitives=[
        (op1, comp1),
        (op2, comp2)
    ],
    continue_on_compensation_failure=True,  # Don't stop on compensation errors
    log_compensations=True                  # Log all compensation attempts
)
```

## Real-World Examples

### Example 1: E-commerce Order Processing

```python
async def reserve_inventory(data, context):
    """Reserve product inventory."""
    reservation_id = await inventory_service.reserve(
        product_id=data["product_id"],
        quantity=data["quantity"]
    )
    return {**data, "reservation_id": reservation_id}

async def release_inventory(data, context):
    """Release reserved inventory."""
    await inventory_service.release(data["reservation_id"])

async def charge_payment(data, context):
    """Charge customer payment."""
    charge_id = await payment_service.charge(
        customer_id=data["customer_id"],
        amount=data["amount"]
    )
    return {**data, "charge_id": charge_id}

async def refund_payment(data, context):
    """Refund payment."""
    await payment_service.refund(data["charge_id"])

async def ship_order(data, context):
    """Ship the order."""
    tracking_id = await shipping_service.ship(
        address=data["address"],
        items=[data["product_id"]]
    )
    return {**data, "tracking_id": tracking_id}

async def cancel_shipment(data, context):
    """Cancel shipment (if possible)."""
    await shipping_service.cancel(data["tracking_id"])

# Complete order workflow with compensation
order_workflow = CompensationPrimitive(
    primitives=[
        (reserve_inventory, release_inventory),
        (charge_payment, refund_payment),
        (ship_order, cancel_shipment)
    ]
)
```

### Example 2: User Onboarding Flow

```python
async def create_auth_account(data, context):
    """Create authentication account."""
    auth_id = await auth_service.create_account(
        email=data["email"],
        password=data["password"]
    )
    return {**data, "auth_id": auth_id}

async def delete_auth_account(data, context):
    """Delete authentication account."""
    await auth_service.delete_account(data["auth_id"])

async def create_profile(data, context):
    """Create user profile."""
    profile_id = await profile_service.create(
        auth_id=data["auth_id"],
        name=data["name"]
    )
    return {**data, "profile_id": profile_id}

async def delete_profile(data, context):
    """Delete user profile."""
    await profile_service.delete(data["profile_id"])

async def send_verification_email(data, context):
    """Send verification email."""
    await email_service.send_verification(data["email"])
    return {**data, "verification_sent": True}

async def log_verification_rollback(data, context):
    """Log verification rollback (can't unsend email)."""
    await audit_log.log(
        event="verification_rollback",
        user_id=data.get("auth_id"),
        email=data["email"]
    )

onboarding_workflow = CompensationPrimitive(
    primitives=[
        (create_auth_account, delete_auth_account),
        (create_profile, delete_profile),
        (send_verification_email, log_verification_rollback)
    ]
)
```

### Example 3: Multi-Service Data Sync

```python
async def sync_to_primary_db(data, context):
    """Sync to primary database."""
    primary_id = await primary_db.insert(data["record"])
    return {**data, "primary_id": primary_id}

async def rollback_primary_db(data, context):
    """Delete from primary database."""
    await primary_db.delete(data["primary_id"])

async def sync_to_cache(data, context):
    """Sync to cache layer."""
    await cache.set(f"record:{data['primary_id']}", data["record"])
    return data

async def clear_cache(data, context):
    """Clear from cache."""
    await cache.delete(f"record:{data['primary_id']}")

async def sync_to_search_index(data, context):
    """Sync to search index."""
    await search_service.index(data["record"])
    return data

async def remove_from_search_index(data, context):
    """Remove from search index."""
    await search_service.delete(data["primary_id"])

sync_workflow = CompensationPrimitive(
    primitives=[
        (sync_to_primary_db, rollback_primary_db),
        (sync_to_cache, clear_cache),
        (sync_to_search_index, remove_from_search_index)
    ]
)
```

## Observability

### Automatic Metrics

```promql
# Compensation executions
compensation_total{primitive="OrderWorkflow"}

# Compensation failures
compensation_failures_total{primitive="OrderWorkflow"}

# Compensation duration
compensation_duration_seconds{step="reserve_inventory"}
```

### Automatic Spans

OpenTelemetry spans for compensation flow:

```
compensation_workflow.execute
  ├─ step_1.forward
  ├─ step_2.forward
  ├─ step_3.forward (FAILED)
  ├─ step_2.compensate
  └─ step_1.compensate
```

### Structured Logging

```json
{
  "event": "compensation_started",
  "primitive": "OrderWorkflow",
  "step": "charge_payment",
  "compensation_reason": "shipping_failed"
}
{
  "event": "compensation_completed",
  "step": "charge_payment",
  "duration_ms": 234.5
}
```

## Best Practices

### 1. Make Compensations Idempotent

```python
# ✅ Good - idempotent compensation
async def release_inventory(data, context):
    if await inventory.is_reserved(data["reservation_id"]):
        await inventory.release(data["reservation_id"])

# ❌ Bad - fails if already released
async def release_inventory(data, context):
    await inventory.release(data["reservation_id"])  # Throws if not reserved
```

### 2. Log All Compensations

```python
async def rollback_operation(data, context):
    logger.info(
        "compensation_executing",
        operation="create_user",
        user_id=data.get("user_id"),
        reason="later_step_failed"
    )
    await db.delete_user(data["user_id"])
```

### 3. Handle Irreversible Operations

```python
# Some operations can't be undone - log instead
async def send_notification(data, context):
    await notification_service.send(data["user_id"], "Welcome!")
    return data

async def log_notification_sent(data, context):
    """Can't unsend notification - log for audit."""
    await audit_log.log(
        event="notification_rollback_attempted",
        user_id=data["user_id"],
        note="Notification was sent but later steps failed"
    )
```

### 4. Combine with Other Primitives

```python
from tta_dev_primitives.recovery import RetryPrimitive, TimeoutPrimitive

# Add retry to individual steps
reliable_order = CompensationPrimitive(
    primitives=[
        (RetryPrimitive(reserve_inventory, max_retries=3), release_inventory),
        (TimeoutPrimitive(charge_payment, timeout=10), refund_payment),
        (ship_order, cancel_shipment)
    ]
)
```

## Testing

```python
import pytest

@pytest.mark.asyncio
async def test_successful_workflow():
    """Test all steps complete successfully."""
    workflow = CompensationPrimitive([
        (step1, comp1),
        (step2, comp2)
    ])

    result = await workflow.execute({"value": 42}, context)
    assert result["value"] == 42
    # No compensations should be called

@pytest.mark.asyncio
async def test_compensation_on_failure():
    """Test compensations run when step fails."""
    compensations_called = []

    async def comp1(data, context):
        compensations_called.append("comp1")

    async def failing_step(data, context):
        raise ValueError("Step failed")

    workflow = CompensationPrimitive([
        (step1, comp1),
        (failing_step, None)
    ])

    with pytest.raises(ValueError):
        await workflow.execute({}, context)

    assert "comp1" in compensations_called
```

## Related Documentation

- [[RetryPrimitive]] - Retry with backoff
- [[FallbackPrimitive]] - Graceful degradation
- [[SequentialPrimitive]] - Sequential composition
- [[PRIMITIVES CATALOG]] - All primitives

## External Resources

- [Saga Pattern](https://microservices.io/patterns/data/saga.html) - Pattern documentation
- [Distributed Transactions](https://martinfowler.com/articles/patterns-of-distributed-systems/saga.html) - Martin Fowler

## Source Code

**File:** `packages/tta-dev-primitives/src/tta_dev_primitives/recovery/compensation.py`

## Tags

primitive:: recovery
type:: pattern
pattern:: saga
feature:: distributed-transactions
feature:: rollback
