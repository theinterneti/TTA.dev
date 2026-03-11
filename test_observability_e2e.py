#!/usr/bin/env python3
"""End-to-end test: Generate traces and verify they appear in UI."""

import asyncio
import sys

sys.path.insert(0, "/home/thein/repos/TTA.dev/tta-dev")

from primitives.base import WorkflowContext
from primitives.lambda_primitive import LambdaPrimitive
from primitives.sequential import SequentialPrimitive


async def step1(data: dict, ctx: WorkflowContext) -> dict:
    """First step."""
    await asyncio.sleep(0.1)
    return {"step": 1, "value": data.get("value", 0) + 1}


async def step2(data: dict, ctx: WorkflowContext) -> dict:
    """Second step."""
    await asyncio.sleep(0.1)
    return {"step": 2, "value": data["value"] * 2}


async def step3(data: dict, ctx: WorkflowContext) -> dict:
    """Third step that fails."""
    await asyncio.sleep(0.1)
    if data["value"] > 5:
        raise ValueError("Value too large!")
    return {"step": 3, "value": data["value"] + 10}


async def main():
    print("🧪 Testing TTA.dev observability end-to-end...\n")

    # Build workflow
    workflow = SequentialPrimitive(
        [
            LambdaPrimitive(step1),
            LambdaPrimitive(step2),
            LambdaPrimitive(step3),
        ]
    )

    # Test 1: Successful execution
    print("✅ Test 1: Successful workflow...")
    ctx1 = WorkflowContext(workflow_id="test-success")
    try:
        result = await workflow.execute({"value": 1}, ctx1)
        print(f"   Result: {result}")
        print(f"   Trace ID: {ctx1.trace_id}")
    except Exception as e:
        print(f"   ❌ Failed: {e}")

    await asyncio.sleep(1)

    # Test 2: Failed execution
    print("\n❌ Test 2: Failed workflow...")
    ctx2 = WorkflowContext(workflow_id="test-failure")
    try:
        result = await workflow.execute({"value": 5}, ctx2)
        print(f"   Result: {result}")
    except Exception as e:
        print(f"   Expected error: {e}")
        print(f"   Trace ID: {ctx2.trace_id}")

    print("\n🎯 Check the UI at http://localhost:8000")
    print("   You should see 2 traces (1 success, 1 failure)")


if __name__ == "__main__":
    asyncio.run(main())
