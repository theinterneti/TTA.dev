#!/usr/bin/env python3
"""TTA.dev Hello World demo using the current primitives and observability APIs."""

import asyncio
import sys
import time
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import ttadev
from ttadev.primitives import (
    LambdaPrimitive,
    RetryPrimitive,
    RetryStrategy,
    SequentialPrimitive,
    WorkflowContext,
)


async def fetch_data(data: dict, ctx: WorkflowContext) -> dict:
    """Simulate fetching data from an API."""
    name = data.get("name", "World")
    print(f"  📡 Fetching data for {name}...")
    await asyncio.sleep(0.1)  # Simulate API call
    ctx.checkpoint("data_fetched")
    return {"greeting": f"Hello, {name}!", "user_id": 12345}


async def enrich_data(data: dict, ctx: WorkflowContext) -> dict:
    """Enrich the data with additional info."""
    print("  ✨ Enriching data...")
    await asyncio.sleep(0.05)  # Simulate processing
    data["timestamp"] = time.time()
    data["enriched"] = True
    ctx.checkpoint("data_enriched")
    return data


async def format_response(data: dict, ctx: WorkflowContext) -> dict:
    """Format the final response."""
    print("  📝 Formatting response...")
    await asyncio.sleep(0.02)  # Simulate formatting
    message = f"{data['greeting']} (User: {data['user_id']}, Time: {data['timestamp']:.0f})"
    ctx.checkpoint("response_formatted")
    return {"message": message, "success": True}


async def main():
    """Run the Hello World workflow with observability."""
    print("🚀 TTA.dev Hello World - Auto-Instrumented Workflow")
    print("=" * 60)
    print("📊 Dashboard: http://localhost:8000")
    print()

    # Explicit opt-in keeps observability behavior aligned with the current package API.
    print("🔍 Initializing observability...")
    ttadev.initialize_observability()
    print()

    # Build workflow with resilience primitives
    fetch = LambdaPrimitive(fetch_data)
    enrich = LambdaPrimitive(enrich_data)
    format_step = LambdaPrimitive(format_response)

    # Add retry capability to fetch step
    resilient_fetch = RetryPrimitive(
        fetch,
        strategy=RetryStrategy(max_retries=3, backoff_base=2.0),
    )

    # Compose workflow: resilient_fetch >> enrich >> format
    workflow = SequentialPrimitive(
        [
            resilient_fetch,
            enrich,
            format_step,
        ]
    )

    # Execute workflow with observability context
    context = WorkflowContext(
        workflow_id="hello-world-demo",
        session_id="demo-session",
        tags={"environment": "demo", "version": "1.0"},
        metadata={"demo": True},
    )

    print("⚙️  Executing instrumented workflow...")
    print()
    result = await workflow.execute({"name": "TTA.dev User"}, context)

    print()
    print("✅ Workflow complete!")
    print(f"📝 Result: {result['message']}")
    print(f"⏱️  Total Duration: {context.elapsed_ms():.2f}ms")
    print()
    print("📊 Checkpoints:")
    for name, timestamp in context.checkpoints:
        elapsed = (timestamp - context.start_time) * 1000
        print(f"   • {name}: {elapsed:.2f}ms")
    print()
    print("🎯 Check the dashboard to see:")
    print("   • Individual primitive spans (RetryPrimitive, LambdaPrimitive, etc.)")
    print("   • Execution durations and status")
    print("   • Context tags and metadata")
    print("   • Real-time workflow visualization")
    print()
    print("✨ TTA.dev: Build fast, scale when viral!")


if __name__ == "__main__":
    asyncio.run(main())
