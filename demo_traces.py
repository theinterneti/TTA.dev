#!/usr/bin/env python3
"""Generate demo traces for the observability dashboard."""

import asyncio
import sys
from pathlib import Path

# Add tta-dev to path
sys.path.insert(0, str(Path(__file__).parent / "tta-dev"))

from observability.observability_integration import initialize_observability
from primitives.core import LambdaPrimitive, WorkflowContext
from primitives.recovery.circuit_breaker_primitive import (
    CircuitBreakerConfig,
    CircuitBreakerPrimitive,
)
from primitives.recovery.retry import RetryPrimitive, RetryStrategy


async def sample_task(data: dict, ctx: WorkflowContext) -> dict:
    """A sample task that processes data."""
    await asyncio.sleep(0.1)  # Simulate work
    return {"result": data["value"] * 2, "processed": True}


async def sometimes_fails(data: dict, ctx: WorkflowContext) -> dict:
    """A task that fails 30% of the time."""
    import random

    if random.random() < 0.3:
        raise ValueError("Random failure for testing")
    await asyncio.sleep(0.05)
    return {"status": "success", "data": data}


async def generate_traces():
    """Generate various traces to demonstrate the dashboard."""
    print("🚀 Generating demo traces for observability dashboard...")
    print("📊 Open http://localhost:8000 to see live traces")
    print("Press Ctrl+C to stop\n")

    # Initialize observability
    initialize_observability(service_name="demo-trace-generator")

    # Create workflows
    simple_workflow = LambdaPrimitive(sample_task)

    retry_workflow = RetryPrimitive(
        LambdaPrimitive(sometimes_fails),
        strategy=RetryStrategy(max_retries=3, backoff_base=2.0),
    )

    circuit_breaker_workflow = CircuitBreakerPrimitive(
        LambdaPrimitive(sample_task),
        config=CircuitBreakerConfig(failure_threshold=3, recovery_timeout=5.0, success_threshold=2),
    )

    workflows = [
        ("simple", simple_workflow),
        ("retry", retry_workflow),
        ("circuit-breaker", circuit_breaker_workflow),
    ]

    counter = 0
    try:
        while True:
            for name, workflow in workflows:
                counter += 1
                ctx = WorkflowContext(workflow_id=f"{name}-{counter}")

                try:
                    result = await workflow.execute({"value": counter}, ctx)
                    print(f"✓ {name}-{counter}: {result}")
                except Exception as e:
                    print(f"✗ {name}-{counter}: {e}")

                await asyncio.sleep(2)  # Wait between traces

    except KeyboardInterrupt:
        print("\n👋 Stopped generating traces")


if __name__ == "__main__":
    asyncio.run(generate_traces())
