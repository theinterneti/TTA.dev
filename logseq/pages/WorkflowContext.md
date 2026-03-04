description:: Primary context carrier for workflow execution

# WorkflowContext

The `WorkflowContext` class is the primary context carrier for all TTA.dev workflow executions.

## Import

```python
from tta_dev_primitives import WorkflowContext
```

## Usage

```python
context = WorkflowContext(
    workflow_id="my-workflow",
    trace_id="trace-abc",
    metadata={"user_id": "user-1"}
)
result = await workflow.execute(data, context)
```

## Key Properties

- `workflow_id` - Unique workflow identifier
- `trace_id` - OpenTelemetry trace ID
- `correlation_id` - Request correlation ID
- `metadata` - Additional context data

## Related Pages
- [[tta-dev-primitives]] - Package documentation
- [[TTA.dev/Primitives]] - Full primitives catalog
