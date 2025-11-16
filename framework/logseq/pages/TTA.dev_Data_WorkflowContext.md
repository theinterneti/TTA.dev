# TTA.dev/Data/WorkflowContext

type:: [D] DataSchema
status:: stable
tags:: #migration-v2, #data-schema, #workflow-context
context-level:: 3-Technical
created-date:: [[2025-11-12]]
last-updated:: [[2025-11-12]]
migrated:: true
migration-date:: [[2025-11-12]]
migration-version:: 2.0
source-file:: packages/tta-dev-primitives/src/tta_dev_primitives/workflow_context.py
base-class:: BaseModel
used-by:: [[TTA.dev/Primitives/Core/WorkflowPrimitive]], [[TTA.dev/Primitives/Recovery/RetryPrimitive]], [[TTA.dev/Primitives/Performance/CachePrimitive]]
fields:: correlation_id, workflow_id, data, start_time, end_time, error
validation:: Immutable context, data is a dict[str, Any]

---

## Overview

The `WorkflowContext` is a fundamental data schema in TTA.dev, serving as an immutable carrier for shared state and metadata throughout a workflow's execution. It ensures consistent context propagation for observability, error handling, and data flow across various primitives.

---

## Fields

- `correlation_id` (str): A unique identifier for a specific request or execution flow.
- `workflow_id` (str | None): An identifier for the overall workflow definition.
- `data` (dict[str, Any]): A dictionary for arbitrary key-value pairs to store workflow-specific data.
- `start_time` (datetime): Timestamp when the context was created or workflow started.
- `end_time` (datetime | None): Timestamp when the workflow completed.
- `error` (dict[str, Any] | None): Details of any error encountered during workflow execution.

---

## Usage

`WorkflowContext` instances are typically created at the start of a workflow and passed to each primitive's `execute` method. Primitives can read from and add to the context's `data` field, but the context itself is designed to be immutable to prevent unexpected side effects.

```python
from tta_dev_primitives import WorkflowContext

# Create a new context
context = WorkflowContext(
    correlation_id="req-123",
    data={"user_id": "user-789"}
)

# Accessing data
user_id = context.data.get("user_id")

# Creating a new context with updated data (immutability)
new_context = context.model_copy(update={"data": {"new_key": "new_value"}})
```

---

## Related Content

- [[TTA.dev/Concepts/Observability]]
- [[TTA.dev/Concepts/Composition]]
- [[TTA.dev/Primitives/Core/WorkflowPrimitive]]

---

## Tags

#data-schema #workflow-context #context-management #observability
