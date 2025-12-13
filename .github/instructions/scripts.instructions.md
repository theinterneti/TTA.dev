---
applyTo: "scripts/**/*.py"
description: "Automation scripts - use primitives for orchestration and reliability"
---

# Scripts Guidelines

## Core Principle

**Use primitives for orchestration. Never write manual retry/timeout loops.**

## Primitive Selection

| Need | Primitive |
|------|-----------|
| Multiple sequential steps | `SequentialPrimitive` |
| Concurrent operations | `ParallelPrimitive` |
| Transient failure handling | `RetryPrimitive` |
| Hang protection | `TimeoutPrimitive` |
| Result caching | `CachePrimitive` |
| Fallback strategy | `FallbackPrimitive` |

## Basic Pattern

```python
#!/usr/bin/env python3
"""Script using primitives for orchestration."""

import asyncio
from tta_dev_primitives import (
    ParallelPrimitive,
    RetryPrimitive,
    TimeoutPrimitive,
    LambdaPrimitive,
    WorkflowContext,
)

async def process_item(data: dict, ctx: WorkflowContext) -> dict:
    """Process a single item."""
    return {"result": data["value"] * 2}

def build_workflow():
    """Build resilient workflow."""
    return TimeoutPrimitive(
        RetryPrimitive(
            LambdaPrimitive(process_item),
            max_attempts=3,
            backoff_factor=2.0
        ),
        timeout_seconds=30.0
    )

async def main():
    workflow = build_workflow()
    context = WorkflowContext(workflow_id="script-run")
    result = await workflow.execute({"value": 42}, context)
    print(result)

if __name__ == "__main__":
    asyncio.run(main())
```

## Anti-Patterns

```python
# ❌ Wrong: Manual retry loop
for attempt in range(3):
    try:
        result = await api_call()
        break
    except Exception:
        await asyncio.sleep(2 ** attempt)

# ✅ Correct: Use RetryPrimitive
workflow = RetryPrimitive(api_call, max_attempts=3, backoff_factor=2.0)
result = await workflow.execute(data, context)
```

## Script Structure

```python
#!/usr/bin/env python3
"""Brief description of script purpose."""

import asyncio
from tta_dev_primitives import WorkflowContext, ...

def build_workflow():
    """Build the workflow graph."""
    ...

async def main():
    """Entry point."""
    ...

if __name__ == "__main__":
    asyncio.run(main())
```

## Validation

```bash
uv run ruff format scripts/
uv run ruff check scripts/ --fix
uv run python scripts/your_script.py
```


---
**Logseq:** [[TTA.dev/.github/Instructions/Scripts.instructions]]
