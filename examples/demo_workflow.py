"""Demo workflow showing the current TTA.dev primitive APIs in action."""

import asyncio
import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ttadev.primitives import (
    CachePrimitive,
    LambdaPrimitive,
    RetryPrimitive,
    RetryStrategy,
    TimeoutPrimitive,
    WorkflowContext,
)


async def fetch_user_data(user_id: str, ctx: WorkflowContext) -> dict:
    """Simulate fetching user data from an API."""
    print(f"📡 Fetching data for user: {user_id}")
    await asyncio.sleep(0.05)
    return {
        "user_id": user_id,
        "name": f"User {user_id}",
        "status": "active",
        "timestamp": "2026-03-08T19:00:00Z",
    }


async def process_user_data(data: dict, ctx: WorkflowContext) -> dict:
    """Process the fetched user data."""
    print(f"⚙️  Processing data for: {data['name']}")
    await asyncio.sleep(0.03)
    return {
        **data,
        "processed": True,
        "score": 42,
    }


async def main():
    """Run the current demo workflow."""
    print("🚀 TTA.dev Demo Workflow")
    print("=" * 50)
    print()

    fetch_step = LambdaPrimitive(fetch_user_data)
    process_step = LambdaPrimitive(process_user_data)

    cached_fetch = CachePrimitive(
        RetryPrimitive(fetch_step, strategy=RetryStrategy(max_retries=3, backoff_base=2.0)),
        cache_key_fn=lambda user_id, ctx: f"{ctx.workflow_id}:{user_id}",
        ttl_seconds=60.0,
    )
    workflow = TimeoutPrimitive(cached_fetch >> process_step, timeout_seconds=5.0)

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
    print("📊 For live traces, start the observability server in another terminal:")
    print("   uv run python -m ttadev.observability")
    print("   Then open: http://localhost:8000")
    print()
    print("📦 This demo uses the current primitive APIs for retry, cache, and timeout.")
    print()
    print("💡 Tip: Keep the same workflow object alive and rerun it to watch cache hits.")
    print()
    print("📚 The canonical proof path is still:")
    print("   uv run python scripts/test_realtime_traces.py")
    print()
    print("📄 See also:")
    print("   http://localhost:8000")


if __name__ == "__main__":
    asyncio.run(main())
