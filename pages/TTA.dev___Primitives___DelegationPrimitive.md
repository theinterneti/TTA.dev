type:: primitive
category:: Orchestration
status:: documented
generated:: 2025-12-04

# DelegationPrimitive

**Source:** `platform/primitives/src/tta_dev_primitives/orchestration/delegation_primitive.py`

## Overview

Delegates tasks from orchestrator to executor models.

This primitive enables the orchestrator-executor pattern where a high-quality
orchestrator model (e.g., Claude Sonnet 4.5) delegates execution to appropriate
executor models (e.g., free flagship models) for cost optimization.

**Orchestrator-Executor Pattern:**
1. Orchestrator analyzes task and determines best executor
2. Orchestrator creates detailed instructions for executor
3. DelegationPrimitive routes task to executor model
4. Executor executes task and returns result
5. Orchestrator validates/refines result if needed

**Cost Optimization:**
- Orchestrator handles planning/validation (small token usage)
- Executor handles bulk execution (large token usage, free models)
- Result: 80%+ cost reduction while maintaining quality



Attributes:
    executor_primitives: Map of model names to executor primitives

## Usage Example

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
