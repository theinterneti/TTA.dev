"""
Demo workflow showing TTA.dev batteries-included observability.

This example demonstrates:
- Auto-instrumentation of primitives
- Real-time observability dashboard
- Composable workflow patterns
- Zero-config setup

Run: uv run python examples/demo_workflow.py
Then open: http://localhost:8000
"""

import asyncio

from ttadev.primitives import CachePrimitive, RetryPrimitive, TimeoutPrimitive
from ttadev.primitives.core.base import WorkflowContext


async def fetch_user_data(user_id: str, ctx: WorkflowContext) -> dict:
    """Simulate fetching user data from an API."""
    print(f"📡 Fetching data for user: {user_id}")
    await asyncio.sleep(0.5)  # Simulate network delay
    return {
        "user_id": user_id,
        "name": f"User {user_id}",
        "status": "active",
        "timestamp": "2026-03-08T19:00:00Z",
    }


async def process_user_data(data: dict, ctx: WorkflowContext) -> dict:
    """Process the fetched user data."""
    print(f"⚙️  Processing data for: {data['name']}")
    await asyncio.sleep(0.3)  # Simulate processing
    return {
        **data,
        "processed": True,
        "score": 42,
    }


async def main():
    print("🚀 TTA.dev Demo Workflow")
    print("=" * 50)
    print()

    # Build a resilient workflow with composable primitives
    workflow = (
        TimeoutPrimitive(timeout_seconds=5.0, name="API Timeout")
        >> CachePrimitive(ttl=60, name="User Cache")
        >> RetryPrimitive(max_attempts=3, backoff_factor=2.0, name="Retry Handler")
        >> process_user_data
    )

    # Execute for multiple users
    user_ids = ["user_123", "user_456", "user_789"]

    for user_id in user_ids:
        ctx = WorkflowContext(workflow_id=f"fetch-{user_id}")

        print(f"\n📋 Executing workflow for {user_id}...")
        result = await workflow.execute(user_id, ctx)
        print(f"✅ Result: {result}")

    print()
    print("=" * 50)
    print("🎉 Demo Complete!")
    print()
    print("📊 View the observability dashboard at:")
    print("   http://localhost:8000")
    print()
    print("💡 Tip: Run this script again and watch the cache hit!")


if __name__ == "__main__":
    asyncio.run(main())
