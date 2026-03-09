#!/usr/bin/env python3
"""Simple demo showcasing TTA.dev primitives with observability."""

import asyncio

from primitives import (
    LambdaPrimitive,
    RetryPrimitive,
    RetryStrategy,
    SequentialPrimitive,
    WorkflowContext,
)


async def fetch_user(data: dict, ctx: WorkflowContext) -> dict:
    """Fetch user profile."""
    await asyncio.sleep(0.1)
    return {**data, "user": {"name": "Alice", "email": "alice@example.com"}}


async def fetch_settings(data: dict, ctx: WorkflowContext) -> dict:
    """Fetch user settings."""
    await asyncio.sleep(0.15)
    return {**data, "settings": {"theme": "dark", "notifications": True}}


async def enrich_profile(data: dict, ctx: WorkflowContext) -> dict:
    """Enrich profile with computed data."""
    await asyncio.sleep(0.1)
    user = data.get("user", {})
    return {
        **data,
        "enriched": {"display_name": user.get("name", "Unknown").upper()},
    }


async def main():
    """Run simple instrumented demo."""
    print("🚀 TTA.dev Simple Demo - Watch the observability dashboard!\n")

    # Create workflow with different primitive types
    print("📊 Building workflow...")
    print("  1. Fetch user data")
    print("  2. Fetch settings data")
    print("  3. Enrich combined profile")
    print()

    # Step 1: Fetch user
    fetch_user_step = LambdaPrimitive(fetch_user)

    # Step 2: Fetch settings (with retry for resilience)
    fetch_settings_step = RetryPrimitive(
        LambdaPrimitive(fetch_settings),
        strategy=RetryStrategy(max_attempts=3, backoff_factor=2.0),
    )

    # Step 3: Enrich profile
    enrich_step = LambdaPrimitive(enrich_profile)

    # Combine into sequential workflow
    workflow = SequentialPrimitive([fetch_user_step, fetch_settings_step, enrich_step])

    # Execute
    print("⚡ Executing workflow...")
    print("=" * 60)

    ctx = WorkflowContext(workflow_id="simple_demo")
    result = await workflow.execute({"user_id": 12345}, ctx)

    print("=" * 60)
    print("\n✅ Workflow completed!")
    print(f"📊 Result: {result}")
    print("\n🔍 Check http://localhost:8000 to see:")
    print("   - Sequential workflow execution")
    print("   - Retry instrumentation")
    print("   - Timing and duration for each step")
    print("   - Full trace tree")


if __name__ == "__main__":
    asyncio.run(main())
