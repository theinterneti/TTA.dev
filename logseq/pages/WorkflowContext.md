# WorkflowContext

**Core context object for managing workflow state and observability.**

## Overview

`WorkflowContext` is the foundational context object passed through all TTA.dev workflow primitives. It provides:

- **State Management**: Share data across workflow steps
- **Observability**: Trace IDs, correlation IDs, span context
- **Metadata**: User IDs, request metadata, custom attributes

## Usage

```python
from tta_dev_primitives import WorkflowContext

# Create context
context = WorkflowContext(
    correlation_id="req-123",
    data={"user_id": "user-789"}
)

# Execute workflow with context
result = await workflow.execute(input_data, context)
```

## Key Properties

- **correlation_id**: Unique ID for request tracing
- **user_id**: User making the request
- **data**: Dictionary of workflow-specific state
- **span_context**: OpenTelemetry span context

## Related Pages

- [[TTA.dev/Primitives/WorkflowPrimitive]] - Base primitive using context
- [[TTA.dev/Observability]] - Context propagation for tracing
- [[TTA.dev/Guides/Context Management]] - Best practices

## Documentation

See: `packages/tta-dev-primitives/src/tta_dev_primitives/core/base.py`

## Tags

concept:: workflow-context
type:: core-infrastructure

- [[Project Hub]]