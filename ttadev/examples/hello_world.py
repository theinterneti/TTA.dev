#!/usr/bin/env python3
"""
Hello World Example - Your First TTA.dev Workflow

This demonstrates the basics:
- Creating simple primitives with LambdaPrimitive
- Chaining them with >> operator
- Observing execution in the dashboard
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from primitives.core import LambdaPrimitive, WorkflowContext


async def greet(name: str, ctx: WorkflowContext) -> str:
    """Simple greeting function."""
    return f"Hello, {name}!"


async def exclaim(message: str, ctx: WorkflowContext) -> str:
    """Add excitement to the message."""
    return f"{message} Welcome to TTA.dev! 🚀"


async def main():
    # Build the workflow
    workflow = LambdaPrimitive(greet) >> LambdaPrimitive(exclaim)

    # Execute with observability
    context = WorkflowContext(workflow_id="hello-world")
    result = await workflow.execute("World", context)

    print(f"\n✨ Result: {result}")
    print("🔍 View trace at: http://localhost:8000\n")


if __name__ == "__main__":
    asyncio.run(main())
