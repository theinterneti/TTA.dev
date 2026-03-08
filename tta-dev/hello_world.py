#!/usr/bin/env python3
"""
TTA.dev Hello World - Self-Observing Demo

This script demonstrates TTA.dev primitives with basic observability.
Run this to see TTA.dev in action!
"""

import asyncio
import time

from primitives.core.base import LambdaPrimitive, WorkflowContext
from primitives.core.sequential import SequentialPrimitive


async def greet(data: dict, ctx: WorkflowContext) -> dict:
    """Greet the user."""
    name = data.get("name", "World")
    print(f"  🤝 Greeting {name}...")
    time.sleep(0.1)  # Simulate some work
    ctx.checkpoint("greeted")
    return {"greeting": f"Hello, {name}!"}


async def add_timestamp(data: dict, ctx: WorkflowContext) -> dict:
    """Add timestamp to the greeting."""
    print(f"  ⏰ Adding timestamp...")
    time.sleep(0.05)  # Simulate some work
    data["timestamp"] = time.time()
    ctx.checkpoint("timestamped")
    return data


async def format_message(data: dict, ctx: WorkflowContext) -> dict:
    """Format the final message."""
    print(f"  📝 Formatting message...")
    time.sleep(0.02)  # Simulate some work
    message = f"{data['greeting']} (generated at {data['timestamp']})"
    ctx.checkpoint("formatted")
    return {"message": message}


async def main():
    """Run the Hello World workflow."""
    print("🚀 TTA.dev Hello World - Primitive Composition Demo")
    print("=" * 60)
    print()
    
    # Build workflow using Sequential composition
    workflow = SequentialPrimitive([
        LambdaPrimitive(greet),
        LambdaPrimitive(add_timestamp),
        LambdaPrimitive(format_message),
    ])
    
    # Execute workflow with context for observability
    context = WorkflowContext(
        workflow_id="hello-world-demo",
        metadata={"demo": True, "version": "1.0"}
    )
    
    print("⚙️  Executing workflow with 3 primitives...")
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
    print("✨ TTA.dev primitives make building observable workflows easy!")


if __name__ == "__main__":
    asyncio.run(main())
