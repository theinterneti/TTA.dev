type:: primitive
category:: Orchestration
status:: documented
generated:: 2025-12-04

# DelegationPrimitive

**Source:** `platform/primitives/src/tta_dev_primitives/orchestration/delegation_primitive.py`

## Overview

Delegates tasks from orchestrator to executor models.

## Usage Examples

```python
from tta_dev_primitives.orchestration import DelegationPrimitive
    from tta_dev_primitives.integrations import GoogleAIStudioPrimitive
    from tta_dev_primitives.core.base import WorkflowContext

    # Create delegation primitive with Gemini Pro executor
    delegation = DelegationPrimitive(
        executor_primitives={
            "gemini-2.5-pro": GoogleAIStudioPrimitive(model="gemini-2.5-pro")
        }
    )

    # Delegate task
    context = WorkflowContext(workflow_id="delegation-demo")
    request = DelegationRequest(
        task_description="Summarize article",
        executor_model="gemini-2.5-pro",
        messages=[{"role": "user", "content": "Summarize: [article text]"}]
    )
    response = await delegation.execute(request, context)

    print(f"Executor: {response.executor_model}")
    print(f"Response: {response.content}")
    print(f"Cost: ${response.cost}")
```

## Related

- [[TTA.dev/Primitives]] - Primitives index
- [[TTA.dev/Primitives/Orchestration]] - Orchestration primitives


---
**Logseq:** [[TTA.dev/_archive/Logseq_backup/Pages_root/Tta.dev___primitives___delegationprimitive]]
