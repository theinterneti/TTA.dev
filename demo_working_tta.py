#!/usr/bin/env python3
"""
TTA.dev Hello World Demo
This demo shows TTA.dev observing its own execution in real-time.
"""

import asyncio
import sys
from pathlib import Path

# Add tta-dev to path
sys.path.insert(0, str(Path(__file__).parent / "tta-dev"))

from primitives.core import LambdaPrimitive, WorkflowContext
from primitives.recovery.circuit_breaker_primitive import (
    CircuitBreakerConfig,
    CircuitBreakerPrimitive,
)
from primitives.recovery.retry import RetryPrimitive, RetryStrategy

print("🚀 TTA.dev Hello World Demo")
print("=" * 50)
print("Visit http://localhost:5001 to see live observability!")
print("=" * 50)
print()


async def fetch_data(data: dict, ctx: WorkflowContext) -> dict:
    """Simulates fetching data from an API."""
    await asyncio.sleep(0.5)  # Simulate network call
    return {"status": "success", "message": f"Fetched data for: {data.get('query', 'unknown')}"}


async def process_data(data: dict, ctx: WorkflowContext) -> dict:
    """Process the fetched data."""
    await asyncio.sleep(0.3)  # Simulate processing
    return {
        "status": "processed",
        "result": f"Processed: {data.get('message', 'no message')}",
        "count": len(data.get("message", "")),
    }


async def save_data(data: dict, ctx: WorkflowContext) -> dict:
    """Save the processed data."""
    await asyncio.sleep(0.2)  # Simulate database write
    return {"status": "saved", "id": "12345", "data": data}


async def main():
    """Run the demo workflow."""

    # Build a resilient workflow using TTA.dev primitives
    print("📦 Building workflow with TTA.dev primitives...")

    # Step 1: Fetch with retry logic
    retry_strategy = RetryStrategy()
    retry_strategy.max_retries = 3
    fetch_step = RetryPrimitive(
        primitive=LambdaPrimitive(fetch_data),
        strategy=retry_strategy,
    )

    # Step 2: Process with circuit breaker
    process_step = CircuitBreakerPrimitive(
        primitive=LambdaPrimitive(process_data),
        config=CircuitBreakerConfig(failure_threshold=3, recovery_timeout=5.0, success_threshold=2),
    )

    # Step 3: Save the data
    save_step = LambdaPrimitive(save_data)

    # Chain them together
    workflow = fetch_step >> process_step >> save_step

    print("✅ Workflow built!")
    print()

    # Create workflow context with tracing
    context = WorkflowContext(workflow_id="demo-workflow-001")

    # Execute the workflow
    print("🔄 Executing workflow...")
    input_data = {"query": "user_profile", "user_id": "user123"}

    try:
        result = await workflow.execute(input_data, context)
        print("✅ Workflow completed successfully!")
        print(f"   Result: {result}")
        print()
    except Exception as e:
        print(f"❌ Workflow failed: {e}")
        print()

    # Run it again to show workflow chaining
    print("🔄 Running again to demonstrate consistency...")
    try:
        result2 = await workflow.execute(input_data, context)
        print("✅ Second execution complete!")
        print(f"   Result: {result2}")
        print()
    except Exception as e:
        print(f"❌ Second execution failed: {e}")
        print()

    print("=" * 50)
    print("✨ Demo complete! Check http://localhost:5001")
    print("   You should see traces for both workflow executions")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(main())
