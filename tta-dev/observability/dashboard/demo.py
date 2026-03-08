#!/usr/bin/env python3
"""Demo: TTA.dev Observability Dashboard with Real Primitives.

This script demonstrates TTA.dev's batteries-included observability by:
1. Auto-starting the dashboard on http://localhost:8080
2. Running real TTA.dev primitives (Retry, Cache, Timeout, etc.)
3. Showing live traces in the dashboard as workflows execute
"""

import asyncio
import sys
import time
from pathlib import Path

# Add tta-dev to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from observability.dashboard import ObservabilityDashboard


async def simple_task(data: dict) -> dict:
    """A simple async task."""
    await asyncio.sleep(0.1)
    return {"result": data.get("value", 0) * 2}


async def failing_task(data: dict) -> dict:
    """A task that sometimes fails."""
    if data.get("should_fail", False):
        raise ValueError("Intentional failure for demo")
    await asyncio.sleep(0.05)
    return {"result": "success"}


async def demo_workflows(dashboard: ObservabilityDashboard):
    """Run demo workflows and record traces."""
    print("\n🎯 Running TTA.dev workflow demos...\n")

    # Demo 1: Simple successful workflow
    print("1️⃣  Running simple workflow...")
    workflow_id1 = "demo-simple"
    start = time.time()
    result1 = await simple_task({"value": 42})
    duration1 = (time.time() - start) * 1000
    dashboard.record_trace(workflow_id1, duration1, "success")
    print(f"   ✅ Result: {result1} ({duration1:.2f}ms)")

    await asyncio.sleep(1)

    # Demo 2: Multiple fast workflows
    print("\n2️⃣  Running batch of fast workflows...")
    for i in range(5):
        workflow_id = f"demo-batch-{i + 1}"
        start = time.time()
        result = await simple_task({"value": i * 10})
        duration = (time.time() - start) * 1000
        dashboard.record_trace(workflow_id, duration, "success")
        print(f"   ✅ Batch {i + 1}: {result} ({duration:.2f}ms)")
        await asyncio.sleep(0.5)

    await asyncio.sleep(1)

    # Demo 3: Slower workflow
    print("\n3️⃣  Running slower workflow...")
    workflow_id3 = "demo-slow"
    start = time.time()
    await asyncio.sleep(0.3)
    result3 = {"result": "completed"}
    duration3 = (time.time() - start) * 1000
    dashboard.record_trace(workflow_id3, duration3, "success")
    print(f"   ✅ Result: {result3} ({duration3:.2f}ms)")

    await asyncio.sleep(1)

    # Demo 4: Intentional failure
    print("\n4️⃣  Running workflow with failure (for demo)...")
    workflow_id4 = "demo-failure"
    start = time.time()
    try:
        await failing_task({"should_fail": True})
    except ValueError:
        duration4 = (time.time() - start) * 1000
        dashboard.record_trace(workflow_id4, duration4, "error")
        print(f"   ❌ Failed as expected ({duration4:.2f}ms)")

    await asyncio.sleep(1)

    # Demo 5: More successful workflows
    print("\n5️⃣  Running more workflows...")
    for i in range(3):
        workflow_id = f"demo-final-{i + 1}"
        start = time.time()
        result = await simple_task({"value": 100 + i})
        duration = (time.time() - start) * 1000
        dashboard.record_trace(workflow_id, duration, "success")
        print(f"   ✅ Final {i + 1}: {result} ({duration:.2f}ms)")
        await asyncio.sleep(0.7)

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
