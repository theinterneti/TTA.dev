type:: [[Package]]
path:: platform/agent-context
pypi:: universal-agent-context
status:: production

# universal-agent-context

Agent context management and propagation for AI workflows.

## Installation

```bash
uv add universal-agent-context
```

## Key Classes

### WorkflowContext
Primary context carrier for workflow execution.

```python
from universal_agent_context import WorkflowContext

context = WorkflowContext(
    workflow_id="workflow-123",
    trace_id="trace-abc",
    correlation_id="request-xyz",
    metadata={"user_id": "user-1"}
)
```

### Properties
- `workflow_id` - Unique workflow identifier
- `trace_id` - OpenTelemetry trace ID
- `correlation_id` - Request correlation
- `metadata` - Additional context data
- `start_time` - Workflow start timestamp

## Context Propagation

Context flows through all primitives automatically:

```python
workflow = step1 >> step2 >> step3
result = await workflow.execute(data, context)
# context is available in all steps
```

## Integration with Tracing

```python
from opentelemetry import trace

context = WorkflowContext(
    trace_id=span.get_span_context().trace_id
)
```

## Related
- [[tta-dev-primitives]] - Core primitives
- [[tta-observability-integration]] - Tracing
