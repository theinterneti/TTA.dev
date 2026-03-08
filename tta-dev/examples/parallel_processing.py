#!/usr/bin/env python3
"""
Parallel Processing Example - Speed Up Your Workflows

Process multiple items concurrently and watch them execute
in parallel on the dashboard timeline!
"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from primitives.core import LambdaPrimitive, ParallelPrimitive, WorkflowContext


async def process_item(item: dict, ctx: WorkflowContext) -> dict:
    """Process a single item (simulates API call or computation)."""
    await asyncio.sleep(1)  # Simulate work
    return {"id": item["id"], "processed": True, "value": item["value"] * 2}


async def main():
    # Create parallel processor
    processor = ParallelPrimitive(LambdaPrimitive(process_item))
    
    # Process 5 items concurrently
    items = [{"id": i, "value": i * 10} for i in range(1, 6)]
    
    context = WorkflowContext(workflow_id="parallel-example")
    results = await processor.execute(items, context)
    
    print("\n✨ Results:")
    for result in results:
        print(f"  Item {result['id']}: {result['value']}")
    
    print(f"\n🔍 View parallel execution at: http://localhost:8000\n")


if __name__ == "__main__":
    asyncio.run(main())
