#!/usr/bin/env python3
"""
Retry Pattern Example - Handling Failures Gracefully

Shows how to handle transient failures with exponential backoff.
Watch the retries in real-time on the dashboard!
"""

import asyncio
import random
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from ttadev.primitives.core import LambdaPrimitive, WorkflowContext
from ttadev.primitives.recovery import RetryPrimitive


async def flaky_api_call(data: dict, ctx: WorkflowContext) -> dict:
    """Simulates an API that fails 60% of the time."""
    if random.random() < 0.6:
        raise Exception("API temporarily unavailable")
    return {"status": "success", "data": data}


async def main():
    # Wrap the flaky operation with retry logic
    from ttadev.primitives.recovery.retry import RetryStrategy

    resilient_api = RetryPrimitive(
        primitive=LambdaPrimitive(flaky_api_call),
        strategy=RetryStrategy(max_retries=5, backoff_base=2.0),
    )

    context = WorkflowContext(workflow_id="retry-example")

    try:
        result = await resilient_api.execute({"user_id": 123}, context)
        print(f"\n✅ Success: {result}")
    except Exception as e:
        print(f"\n❌ Failed after retries: {e}")

    print("🔍 View retries at: http://localhost:8000\n")


if __name__ == "__main__":
    asyncio.run(main())
