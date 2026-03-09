#!/usr/bin/env python3
"""Demo script showing live observability of TTA.dev primitives."""

import asyncio
from ttadev.primitives import (
    SequentialPrimitive,
    ParallelPrimitive,
    RetryPrimitive,
    TimeoutPrimitive,
    LambdaPrimitive,
)
from ttadev.primitives.core.base import WorkflowContext
from ttadev.primitives.recovery.retry import RetryStrategy


async def fetch_user(data, ctx):
    """Simulated API call."""
    await asyncio.sleep(0.1)
    return {"user_id": data.get("id"), "name": "John Doe"}


async def fetch_orders(data, ctx):
    """Simulated API call."""
    await asyncio.sleep(0.15)
    return {"orders": [{"id": 1}, {"id": 2}]}


async def fetch_profile(data, ctx):
    """Simulated API call."""
    await asyncio.sleep(0.12)
    return {"profile": {"bio": "Engineer"}}


async def process_data(data, ctx):
    """Process the combined data."""
    await asyncio.sleep(0.05)
    # ParallelPrimitive returns list of results
    if isinstance(data, list):
        return {"processed": True, "parallel_results": data}
    return {"processed": True, "data": data}


async def main():
    print("🚀 Starting TTA.dev observability demo...")
    print("📊 Dashboard: http://localhost:8000")
    print("💾 Spans: .observability/spans/\n")

    # Build a complex workflow
    user_workflow = RetryPrimitive(
        LambdaPrimitive(fetch_user), strategy=RetryStrategy(max_retries=3)
    )

    parallel_fetch = ParallelPrimitive(
        [
            RetryPrimitive(
                LambdaPrimitive(fetch_orders), strategy=RetryStrategy(max_retries=2)
            ),
            TimeoutPrimitive(LambdaPrimitive(fetch_profile), timeout_seconds=5.0),
        ]
    )

    full_workflow = SequentialPrimitive(
        [user_workflow, parallel_fetch, LambdaPrimitive(process_data)]
    )

    # Execute the workflow
    ctx = WorkflowContext(workflow_id="user-data-pipeline")

    print("⚡ Executing workflow...")
    result = await full_workflow.execute({"id": "user-123"}, ctx)

    print("\n✅ Workflow completed!")
    print(f"📋 Result: {result}")
    print("\n🔍 Check the dashboard to see the trace!")


if __name__ == "__main__":
    asyncio.run(main())
