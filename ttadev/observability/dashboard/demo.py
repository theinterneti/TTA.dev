#!/usr/bin/env python3
"""Demo: TTA.dev Observability Dashboard with Real Primitives.

This script demonstrates TTA.dev's batteries-included observability by:
1. Auto-starting the dashboard on http://localhost:8080
2. Running real TTA.dev primitives and workflows
3. Showing live traces in the dashboard as workflows execute
"""

import asyncio
import sys
import time
from pathlib import Path

# Add tta-dev to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from observability.dashboard import ObservabilityDashboard
from primitives.core import LambdaPrimitive, WorkflowContext
from primitives.recovery import RetryPrimitive, RetryStrategy


async def simple_task(data: dict, ctx: WorkflowContext) -> dict:
    """A simple async task."""
    await asyncio.sleep(0.1)
    return {"result": data.get("value", 0) * 2}


async def failing_task(data: dict, ctx: WorkflowContext) -> dict:
    """A task that sometimes fails."""
    if data.get("should_fail", False):
        raise ValueError("Intentional failure for demo")
    await asyncio.sleep(0.05)
    return {"result": "success"}


async def demo_workflows(dashboard: ObservabilityDashboard):
    """Run demo workflows using real TTA.dev primitives."""
    print("\n🎯 Running TTA.dev primitive demos...\n")

    # Demo 1: Simple workflow with LambdaPrimitive
    print("1️⃣  Running LambdaPrimitive workflow...")
    workflow1 = LambdaPrimitive(simple_task)
    ctx1 = WorkflowContext(workflow_id="demo-lambda")
    start = time.time()
    result1 = await workflow1.execute({"value": 42}, ctx1)
    duration1 = (time.time() - start) * 1000
    dashboard.record_trace(ctx1.workflow_id, duration1, "success")
    print(f"   ✅ Result: {result1} ({duration1:.2f}ms)")

    await asyncio.sleep(1)

    # Demo 2: RetryPrimitive with success
    print("\n2️⃣  Running RetryPrimitive workflow (succeeds)...")
    task_primitive = LambdaPrimitive(simple_task)
    workflow2 = RetryPrimitive(
        task_primitive, strategy=RetryStrategy(max_attempts=3, backoff_factor=2.0)
    )
    ctx2 = WorkflowContext(workflow_id="demo-retry-success")
    start = time.time()
    result2 = await workflow2.execute({"value": 100}, ctx2)
    duration2 = (time.time() - start) * 1000
    dashboard.record_trace(ctx2.workflow_id, duration2, "success")
    print(f"   ✅ Result: {result2} ({duration2:.2f}ms)")

    await asyncio.sleep(1)

    # Demo 3: Batch workflows
    print("\n3️⃣  Running batch of workflows...")
    for i in range(5):
        workflow = LambdaPrimitive(simple_task)
        ctx = WorkflowContext(workflow_id=f"demo-batch-{i + 1}")
        start = time.time()
        result = await workflow.execute({"value": i * 10}, ctx)
        duration = (time.time() - start) * 1000
        dashboard.record_trace(ctx.workflow_id, duration, "success")
        print(f"   ✅ Batch {i + 1}: {result} ({duration:.2f}ms)")
        await asyncio.sleep(0.5)

    await asyncio.sleep(1)

    # Demo 4: Intentional failure with RetryPrimitive
    print("\n4️⃣  Running RetryPrimitive workflow (fails after retries)...")
    failing_primitive = LambdaPrimitive(failing_task)
    workflow4 = RetryPrimitive(
        failing_primitive, strategy=RetryStrategy(max_attempts=2, backoff_factor=1.5)
    )
    ctx4 = WorkflowContext(workflow_id="demo-retry-failure")
    start = time.time()
    try:
        await workflow4.execute({"should_fail": True}, ctx4)
    except ValueError:
        duration4 = (time.time() - start) * 1000
        dashboard.record_trace(ctx4.workflow_id, duration4, "error")
        print(f"   ❌ Failed after retries ({duration4:.2f}ms)")

    print("\n✨ All demos complete! Check the dashboard at http://localhost:8080\n")


async def main():
    """Main entry point."""
    print("=" * 70)
    print("🚀 TTA.dev Observability Dashboard Demo")
    print("=" * 70)

    # Start the dashboard
    dashboard = ObservabilityDashboard(host="localhost", port=8080)
    await dashboard.start()

    print("\n📊 Dashboard is live! Open http://localhost:8080 in your browser")
    print("⏳ Starting workflow demos in 3 seconds...\n")

    await asyncio.sleep(3)

    # Run demo workflows
    await demo_workflows(dashboard)

    # Keep running
    print("🔄 Dashboard will continue running. Press Ctrl+C to stop.\n")
    try:
        await asyncio.Event().wait()
    except KeyboardInterrupt:
        print("\n\n👋 Shutting down. Thanks for trying TTA.dev!\n")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
