#!/usr/bin/env python
"""
TTA.dev Jaeger Tracing Demo

This demo shows how TTA.dev primitives generate traces that appear in Jaeger.
"""

import asyncio
import time
from pathlib import Path
import sys

# Add packages to path
sys.path.insert(0, str(Path(__file__).parent.parent / "packages"))

from tta_dev_primitives import (
    SequentialPrimitive,
    ParallelPrimitive,
    WorkflowContext
)
from tta_dev_primitives.testing import MockPrimitive
from tta_dev_primitives.performance import CachePrimitive

# Initialize OpenTelemetry
try:
    from observability_integration import initialize_observability

    print("🔧 Initializing observability with Jaeger tracing...")
    success = initialize_observability(
        service_name="tta-jaeger-demo",
        enable_prometheus=False  # Don't conflict with existing metrics server
    )

    if success:
        print("✅ OpenTelemetry initialized - traces will appear in Jaeger!")
    else:
        print("⚠️  OpenTelemetry init failed, but demo will still run")

except ImportError:
    print("⚠️  observability_integration not available - traces may not appear")


async def run_jaeger_demo():
    """Run workflows that generate traces for Jaeger."""

    print("\n🚀 Starting Jaeger tracing demo...")
    print("📍 View traces at: http://localhost:16686")
    print("🔍 Look for service: 'tta-jaeger-demo'")

    # Create demo primitives
    user_input = MockPrimitive(
        name="user_input_processor",
        return_value={"input": "What is TTA.dev?"}
    )

    llm_call = MockPrimitive(
        name="llm_api_call",
        return_value={"response": "TTA.dev is a workflow orchestration framework"}
    )

    # Add some artificial delay to make traces more visible
    cached_llm = CachePrimitive(
        primitive=llm_call,
        ttl_seconds=300,
        cache_key_fn=lambda data, ctx: f"demo:{hash(str(data))}"
    )

    response_formatter = MockPrimitive(
        name="response_formatter",
        return_value={"formatted": "**TTA.dev** is a workflow orchestration framework"}
    )

    # Create complex workflow
    workflow = SequentialPrimitive([
        user_input,
        ParallelPrimitive([
            cached_llm,
            MockPrimitive(name="context_retriever", return_value={"context": "technical"})
        ]),
        response_formatter
    ])

    # Execute multiple workflows with different contexts
    for i in range(10):
        print(f"\n📊 Executing workflow {i+1}/10...")

        context = WorkflowContext(
            correlation_id=f"jaeger-demo-{i+1}",
            data={
                "user_id": f"user-{i % 3 + 1}",  # Vary users
                "session_id": f"session-{i // 2 + 1}",  # Vary sessions
                "request_type": "demo"
            }
        )

        start_time = time.time()

        try:
            result = await workflow.execute(
                {"query": f"Demo query {i+1}"},
                context
            )

            duration = (time.time() - start_time) * 1000
            print(f"   ✅ Completed in {duration:.1f}ms")

        except Exception as e:
            print(f"   ❌ Error: {e}")

        # Small delay between workflows
        await asyncio.sleep(0.5)

    print(f"\n🎯 Demo completed! Generated 10 traced workflows")
    print(f"📍 View traces in Jaeger: http://localhost:16686")
    print(f"🔍 Service name: 'tta-jaeger-demo'")
    print(f"🏷️  Look for correlation IDs: jaeger-demo-1 through jaeger-demo-10")

    # Keep running briefly to ensure traces are sent
    print(f"\n⏳ Waiting 5 seconds for traces to be sent...")
    await asyncio.sleep(5)
    print(f"✅ Traces should now be visible in Jaeger!")


if __name__ == "__main__":
    asyncio.run(run_jaeger_demo())
