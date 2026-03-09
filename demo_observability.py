#!/usr/bin/env python3
"""Demo script to generate observability data."""

import asyncio
import os
from primitives.core import WorkflowContext, LambdaPrimitive
from primitives.composition import SequentialPrimitive
from primitives.recovery import RetryPrimitive, FallbackPrimitive
from primitives.flow_control import ConditionalPrimitive


async def fetch_data(data: dict, ctx: WorkflowContext) -> dict:
    """Simulate fetching data from API."""
    await asyncio.sleep(0.1)
    return {**data, "fetched": True, "count": 42}


async def process_data(data: dict, ctx: WorkflowContext) -> dict:
    """Process the fetched data."""
    await asyncio.sleep(0.05)
    return {**data, "processed": True, "result": data.get("count", 0) * 2}


async def save_data(data: dict, ctx: WorkflowContext) -> dict:
    """Save processed data."""
    await asyncio.sleep(0.03)
    return {**data, "saved": True}


async def main():
    """Run demo workflows to generate telemetry."""
    
    print("🚀 Generating observability data...")
    
    # Build a complex workflow
    workflow = SequentialPrimitive([
        RetryPrimitive(
            LambdaPrimitive(fetch_data),
            max_attempts=3,
            backoff_factor=1.5
        ),
        LambdaPrimitive(process_data),
        FallbackPrimitive(
            LambdaPrimitive(save_data),
            LambdaPrimitive(lambda d, ctx: {**d, "fallback": True})
        )
    ])
    
    # Execute multiple times to generate data
    for i in range(5):
        ctx = WorkflowContext(
            workflow_id=f"demo-workflow-{i}",
            metadata={"iteration": i, "demo": True}
        )
        
        result = await workflow.execute({"request_id": i}, ctx)
        print(f"  ✓ Workflow {i} completed: {result.get('result')}")
        await asyncio.sleep(0.5)
    
    print("\n✅ Generated 5 workflow traces!")
    print(f"📊 Check dashboard at http://localhost:8000")
    print(f"💾 Data stored in: ~/.tta/observability/traces/")


if __name__ == "__main__":
    asyncio.run(main())
