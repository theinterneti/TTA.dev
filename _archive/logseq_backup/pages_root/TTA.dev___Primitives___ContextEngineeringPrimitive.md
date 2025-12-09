type:: primitive
category:: Core
status:: documented
generated:: 2025-12-04

# ContextEngineeringPrimitive

**Source:** `platform/primitives/src/tta_dev_primitives/core/context_engineering.py`

## Overview

Engineer optimal context for AI agent tasks.

## Usage Examples

```python
from tta_dev_primitives.core.context_engineering import (
        ContextEngineeringPrimitive,
        ContextRequest,
    )

    # Create context engineer
    engineer = ContextEngineeringPrimitive(
        max_tokens=100_000,
        include_examples=True,
    )

    # Request context for test generation
    request: ContextRequest = {
        "task": "Generate pytest tests for RetryPrimitive",
        "target_class": RetryPrimitive,
        "task_type": "test_generation",
        "quality_threshold": 0.9,
    }

    # Engineer optimal context
    bundle = await engineer.execute(request, WorkflowContext())

    # Use with LLM
    llm_result = await llm.execute({"prompt": bundle.content}, context)
```

## Related

- [[TTA.dev/Primitives]] - Primitives index
- [[TTA.dev/Primitives/Core]] - Core primitives
