#!/usr/bin/env python3
"""Demo workflow that shows live execution in the observability dashboard."""

import asyncio

from ttadev.primitives.core.lambda_primitive import LambdaPrimitive

from ttadev.primitives.core.base import WorkflowContext
from ttadev.primitives.core.sequential import SequentialPrimitive
from ttadev.primitives.recovery.retry import RetryPrimitive
from ttadev.primitives.recovery.timeout import TimeoutPrimitive


async def data_fetch(data: dict, ctx: WorkflowContext) -> dict:
    """Simulate fetching data from an API."""
    await asyncio.sleep(0.5)
    return {"data": data.get("query", "default"), "source": "api"}


async def data_transform(data: dict, ctx: WorkflowContext) -> dict:
    """Transform the fetched data."""
    await asyncio.sleep(0.3)
    return {"transformed": data["data"].upper(), "count": len(data["data"])}


async def data_validate(data: dict, ctx: WorkflowContext) -> dict:
    """Validate the transformed data."""
    await asyncio.sleep(0.2)
    return {"valid": data["count"] > 0, **data}


async def data_save(data: dict, ctx: WorkflowContext) -> dict:
    """Save the validated data."""
    await asyncio.sleep(0.4)
    return {"saved": True, "id": "123", **data}


async def run_demo():
    """Run a demo workflow that generates observable traces."""
    print("🚀 Starting live workflow demo...")
    print("📊 Open http://localhost:8000 to see real-time execution!\n")

    # Build a complex workflow with multiple stages
    fetch = RetryPrimitive(
        LambdaPrimitive(data_fetch, name="FetchData"), max_attempts=3, name="RetryableFetch"
    )

    transform = LambdaPrimitive(data_transform, name="TransformData")
    validate = LambdaPrimitive(data_validate, name="ValidateData")
    save = TimeoutPrimitive(
        LambdaPrimitive(data_save, name="SaveData"), timeout_seconds=2.0, name="TimedSave"
    )

    # Sequential pipeline
    pipeline = SequentialPrimitive([fetch, transform, validate, save], name="DataPipeline")

    # Run it multiple times to show activity
    for i in range(5):
        print(f"🔄 Executing workflow iteration {i + 1}/5...")
        context = WorkflowContext(workflow_id=f"demo-workflow-{i + 1}")

        try:
            result = await pipeline.execute({"query": f"test-data-{i + 1}"}, context)
            print(f"✅ Iteration {i + 1} completed: {result}\n")
        except Exception as e:
            print(f"❌ Iteration {i + 1} failed: {e}\n")

        # Small delay between iterations
        await asyncio.sleep(1)

    print("✨ Demo completed! Check the dashboard for execution history.")


if __name__ == "__main__":
    asyncio.run(run_demo())
