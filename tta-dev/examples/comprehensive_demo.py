#!/usr/bin/env python3
"""Comprehensive demo showcasing all TTA.dev instrumented primitives."""

import asyncio
from primitives import (
    SequentialPrimitive,
    ParallelPrimitive,
    ConditionalPrimitive,
    RetryPrimitive,
    RetryStrategy,
    FallbackPrimitive,
    WorkflowContext,
    LambdaPrimitive,
)


async def fetch_user_data(data: dict, ctx: WorkflowContext) -> dict:
    """Simulate fetching user data from a database."""
    await asyncio.sleep(0.1)
    return {"user_id": data["id"], "name": "Alice", "email": "alice@example.com"}


async def fetch_orders(data: dict, ctx: WorkflowContext) -> dict:
    """Simulate fetching user orders."""
    await asyncio.sleep(0.15)
    return {"orders": [{"id": 1, "total": 99.99}, {"id": 2, "total": 149.99}]}


async def fetch_preferences(data: dict, ctx: WorkflowContext) -> dict:
    """Simulate fetching user preferences."""
    await asyncio.sleep(0.12)
    return {"theme": "dark", "notifications": True}


async def validate_user(data: dict, ctx: WorkflowContext) -> bool:
    """Check if user data is valid."""
    return data.get("user_id") is not None


async def send_email(data: dict, ctx: WorkflowContext) -> dict:
    """Send email notification."""
    await asyncio.sleep(0.2)
    return {**data, "email_sent": True}


async def send_sms(data: dict, ctx: WorkflowContext) -> dict:
    """Send SMS notification as fallback."""
    await asyncio.sleep(0.15)
    return {**data, "sms_sent": True}


async def main():
    """Run comprehensive demo workflow."""
    print("🚀 Starting TTA.dev Comprehensive Demo\n")
    
    # Step 1: Parallel data fetching
    print("📊 Creating parallel data fetching workflow...")
    fetch_workflow = ParallelPrimitive(
        [
            LambdaPrimitive(fetch_user_data),
            LambdaPrimitive(fetch_orders),
            LambdaPrimitive(fetch_preferences),
        ]
    )
    
    # Step 2: Add retry resilience
    print("🔄 Wrapping with retry primitive (max 3 attempts)...")
    resilient_fetch = RetryPrimitive(
        fetch_workflow, strategy=RetryStrategy(max_retries=3, backoff_base=2.0)
    )
    
    # Step 3: Conditional notification with fallback
    print("📧 Setting up conditional notification with email → SMS fallback...")
    notification = ConditionalPrimitive(
        condition=lambda data, ctx: validate_user(data, ctx),
        then_primitive=FallbackPrimitive(
            LambdaPrimitive(send_email),
            LambdaPrimitive(send_sms),
        ),
        else_primitive=LambdaPrimitive(lambda d, c: {**d, "skipped": True}),
    )
    
    # Step 4: Complete sequential pipeline
    print("⚡ Assembling sequential pipeline...\n")
    pipeline = SequentialPrimitive([resilient_fetch, notification])
    
    # Execute workflow
    ctx = WorkflowContext(workflow_id="user_onboarding_demo")
    print(f"🎯 Executing workflow: {ctx.workflow_id}")
    print("=" * 60)
    
    result = await pipeline.execute({"id": 12345}, ctx)
    
    print("=" * 60)
    print(f"\n✅ Workflow completed successfully!")
    print(f"📊 Result: {result}")
    print(f"\n🔍 Check the observability dashboard at http://localhost:8000")
    print(f"   You should see:")
    print(f"   - Parallel execution of fetch operations")
    print(f"   - Retry attempts (if any failures)")
    print(f"   - Conditional branching based on validation")
    print(f"   - Fallback from email to SMS (if email fails)")


if __name__ == "__main__":
    asyncio.run(main())
