type:: primitive
category:: Orchestration
status:: documented
generated:: 2025-12-04

# TaskClassifierPrimitive

**Source:** `platform/primitives/src/tta_dev_primitives/orchestration/task_classifier_primitive.py`

## Overview

Classifies tasks to determine the best model for execution.

This primitive analyzes task characteristics and recommends the most appropriate
model based on complexity, requirements, and cost optimization goals.

**Classification Logic:**
- Simple tasks → Groq (ultra-fast, free)
- Moderate tasks → Gemini Pro (flagship quality, free)
- Complex reasoning → DeepSeek R1 (on par with o1, free)
- Expert tasks → Claude Sonnet 4.5 (paid, highest quality)



Attributes:
    prefer_free: If True, prefer free models when quality is sufficient

## Usage Example

```python
from tta_dev_primitives.orchestration import TaskClassifierPrimitive
    from tta_dev_primitives.core.base import WorkflowContext

    # Create classifier
    classifier = TaskClassifierPrimitive()

    # Classify task
    context = WorkflowContext(workflow_id="classify-demo")
    request = TaskClassifierRequest(
        task_description="Summarize this article in 3 bullet points",
        user_preferences={"prefer_free": True}
    )
    classification = await classifier.execute(request, context)

    print(f"Recommended: {classification.recommended_model}")
    print(f"Reasoning: {classification.reasoning}")
    print(f"Cost: ${classification.estimated_cost}")
```

## Related

- [[TTA.dev/Primitives]] - Primitives index
- [[TTA.dev/Primitives/Orchestration]] - Orchestration primitives
