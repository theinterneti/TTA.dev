#!/usr/bin/env python3
"""Demo of instrumented TTA.dev primitives showing up in observability dashboard."""

import asyncio

from primitives.core.base import LambdaPrimitive, WorkflowContext
from primitives.core.parallel import ParallelPrimitive
from primitives.core.sequential import SequentialPrimitive


async def step1(data: dict, ctx: WorkflowContext) -> dict:
    """First processing step."""
    await asyncio.sleep(0.5)
    return {"step": 1, "value": data.get("value", 0) * 2}


async def step2(data: dict, ctx: WorkflowContext) -> dict:
    """Second processing step."""
    await asyncio.sleep(0.3)
    return {"step": 2, "value": data["value"] + 10}


async def step3(data: dict, ctx: WorkflowContext) -> dict:
    """Third processing step."""
    await asyncio.sleep(0.4)
    return {"step": 3, "value": data["value"] ** 2}


async def main():
    """Run various primitive workflows to demonstrate observability."""

    print("🚀 Running instrumented TTA.dev workflows...")
    print("📊 Open http://localhost:8000 to see traces in real-time!\n")

    # Demo 1: Sequential workflow
    print("1️⃣  Sequential workflow...")
    sequential = SequentialPrimitive(
        [
            LambdaPrimitive(step1),
            LambdaPrimitive(step2),
            LambdaPrimitive(step3),
        ]
    )
    ctx1 = WorkflowContext(workflow_id="sequential-demo")
    result1 = await sequential.execute({"value": 5}, ctx1)
    print(f"   Result: {result1}\n")

    # Demo 2: Parallel workflow
    print("2️⃣  Parallel workflow...")
    parallel = ParallelPrimitive(
        [
            LambdaPrimitive(step1),
            LambdaPrimitive(step2),
            LambdaPrimitive(step3),
        ]
    )
    ctx2 = WorkflowContext(workflow_id="parallel-demo")
    result2 = await parallel.execute({"value": 3}, ctx2)
    print(f"   Results: {result2}\n")

    # Demo 3: Simple success workflow
    print("3️⃣  Another sequential workflow...")
    simple = SequentialPrimitive(
        [
            LambdaPrimitive(step1),
            LambdaPrimitive(step3),
        ]
    )
    ctx3 = WorkflowContext(workflow_id="simple-demo")
    result3 = await simple.execute({"value": 7}, ctx3)
    print(f"   Result: {result3}\n")

    print("✅ All workflows complete! Check the dashboard for traces.")


if __name__ == "__main__":
    asyncio.run(main())
