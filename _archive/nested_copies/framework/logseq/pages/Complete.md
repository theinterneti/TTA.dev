# Complete

**Status indicator for completed workflows and tasks**

---

## Overview

"Complete" is a status marker used throughout TTA.dev to indicate finished states of workflows, tasks, and operations. This page documents completion patterns and verification methods.

---

## Completion States

### Workflow Completion

Workflows transition through states:

```
not-started → in-progress → complete | failed | timeout
```

**Example:**

```python
from tta_dev_primitives import WorkflowContext, WorkflowStatus

context = WorkflowContext(
    workflow_id="task-123",
    status=WorkflowStatus.IN_PROGRESS
)

# Execute workflow
result = await workflow.execute(data, context)

# Update status
context.status = WorkflowStatus.COMPLETE

# Check completion
assert context.is_complete()
```

### Task Completion in Logseq

Tasks use completion markers in journals:

```markdown
- TODO Implement feature #dev-todo
  status:: in-progress

- DOING Working on tests #dev-todo
  status:: in-progress

- DONE Feature complete #dev-todo
  status:: complete
  completed:: [[2025-11-03]]
```

---

## Verification Patterns

### Pattern 1: Async Workflow Completion

```python
import asyncio
from tta_dev_primitives import WorkflowContext

async def wait_for_completion(
    workflow_id: str,
    timeout_seconds: float = 30.0
) -> bool:
    """Wait for workflow to complete."""
    start_time = asyncio.get_event_loop().time()

    while True:
        context = await get_workflow_context(workflow_id)

        if context.is_complete():
            return True

        if context.is_failed():
            raise WorkflowError(f"Workflow {workflow_id} failed")

        elapsed = asyncio.get_event_loop().time() - start_time
        if elapsed > timeout_seconds:
            raise TimeoutError(f"Workflow {workflow_id} did not complete")

        await asyncio.sleep(1.0)

# Usage
await wait_for_completion("workflow-123")
```

### Pattern 2: Batch Completion Checking

```python
async def check_batch_complete(workflow_ids: list[str]) -> dict[str, bool]:
    """Check completion status of multiple workflows."""
    results = {}

    for workflow_id in workflow_ids:
        context = await get_workflow_context(workflow_id)
        results[workflow_id] = context.is_complete()

    return results

# Usage
statuses = await check_batch_complete([
    "workflow-1",
    "workflow-2",
    "workflow-3"
])

all_complete = all(statuses.values())
```

---

## Completion Callbacks

### Register Completion Handlers

```python
from tta_dev_primitives import WorkflowPrimitive, WorkflowContext

class CallbackPrimitive(WorkflowPrimitive):
    """Primitive with completion callback."""

    def __init__(self, on_complete: callable):
        super().__init__()
        self.on_complete = on_complete

    async def _execute_impl(self, data: dict, context: WorkflowContext) -> dict:
        try:
            result = await self.process(data, context)

            # Call completion handler
            await self.on_complete(result, context)

            return result
        except Exception as e:
            await self.on_complete(None, context, error=e)
            raise

# Usage
async def handle_complete(result, context, error=None):
    if error:
        logger.error(f"Workflow {context.workflow_id} failed: {error}")
    else:
        logger.info(f"Workflow {context.workflow_id} complete: {result}")
        # Send notification, update database, etc.

workflow = CallbackPrimitive(on_complete=handle_complete)
```

---

## Completion Metrics

### Track Completion Rates

```promql
# Prometheus queries for completion tracking

# Completion rate over time
rate(workflow_completions_total[5m])

# Success vs failure ratio
workflow_completions_total{status="complete"} /
workflow_completions_total

# Average time to completion
histogram_quantile(0.95,
  workflow_completion_duration_seconds_bucket
)
```

### Grafana Dashboard

```json
{
  "dashboard": {
    "title": "Workflow Completion",
    "panels": [
      {
        "title": "Completion Rate",
        "targets": [
          {
            "expr": "rate(workflow_completions_total[5m])"
          }
        ]
      },
      {
        "title": "Time to Complete",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, workflow_completion_duration_seconds_bucket)"
          }
        ]
      }
    ]
  }
}
```

---

## Completion Guarantees

### At-Least-Once Completion

```python
from tta_dev_primitives.recovery import RetryPrimitive

# Retry until complete
workflow = RetryPrimitive(
    primitive=process_step,
    max_retries=3,
    backoff_strategy="exponential"
)

# Guarantees completion or raises exception
result = await workflow.execute(data, context)
```

### At-Most-Once Completion

```python
from tta_dev_primitives.recovery import TimeoutPrimitive

# Complete once or timeout
workflow = TimeoutPrimitive(
    primitive=process_step,
    timeout_seconds=30.0
)

try:
    result = await workflow.execute(data, context)
except TimeoutError:
    # Handle incomplete workflow
    logger.warning("Workflow did not complete in time")
```

### Exactly-Once Completion

```python
# Use idempotency key for exactly-once semantics
context = WorkflowContext(
    workflow_id="task-123",
    idempotency_key="unique-operation-id"
)

# Check if already completed
if await is_already_complete(context.idempotency_key):
    return await get_cached_result(context.idempotency_key)

# Execute and mark complete
result = await workflow.execute(data, context)
await mark_complete(context.idempotency_key, result)
```

---

## Completion Events

### Publish Completion Events

```python
from tta_dev_primitives.observability import EventPublisher

publisher = EventPublisher()

# Publish completion event
await publisher.publish({
    "event_type": "workflow.complete",
    "workflow_id": context.workflow_id,
    "timestamp": datetime.utcnow(),
    "duration_seconds": 12.5,
    "result": result
})
```

### Subscribe to Completion Events

```python
async def handle_workflow_complete(event: dict):
    """Handle workflow completion events."""
    workflow_id = event["workflow_id"]
    duration = event["duration_seconds"]

    logger.info(f"Workflow {workflow_id} completed in {duration}s")

    # Trigger dependent workflows
    await trigger_dependent_workflows(workflow_id)

# Subscribe
publisher.subscribe("workflow.complete", handle_workflow_complete)
```

---

## Testing Completion

### Unit Tests

```python
import pytest
from tta_dev_primitives import WorkflowContext

@pytest.mark.asyncio
async def test_workflow_completes():
    """Test workflow completes successfully."""
    context = WorkflowContext(workflow_id="test")

    result = await workflow.execute({"input": "test"}, context)

    assert result is not None
    assert context.is_complete()

@pytest.mark.asyncio
async def test_workflow_completion_callback():
    """Test completion callback is called."""
    callback_called = False

    async def on_complete(result, context):
        nonlocal callback_called
        callback_called = True

    workflow = CallbackPrimitive(on_complete=on_complete)
    await workflow.execute({"input": "test"}, context)

    assert callback_called
```

---

## Related Concepts

- [[WorkflowContext]] - Context with status tracking
- [[WorkflowPrimitive]] - Base primitive with completion semantics
- [[TODO Management System]] - Task completion tracking

---

## Related Documentation

- [[TTA.dev/Testing]] - Testing completion scenarios
- [[TTA.dev/Observability]] - Monitoring completion metrics

---

**Status:** Production pattern
**Category:** Workflow patterns

- [[Project Hub]]