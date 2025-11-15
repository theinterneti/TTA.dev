"""Test the TTA Observability UI with live data.

This example:
1. Starts workflows that generate traces
2. Sends them to the TTA UI service
3. Verifies they appear in the dashboard

Prerequisites:
    - TTA UI service running: tta-observability-ui start
    - Dashboard open: http://localhost:8765
"""

import asyncio
import random

from tta_dev_primitives import SequentialPrimitive, WorkflowContext, WorkflowPrimitive
from tta_dev_primitives.recovery import FallbackPrimitive, RetryPrimitive


class SimulatedAPICall(WorkflowPrimitive[dict, dict]):
    """Simulates an unreliable API call."""

    def __init__(self, name: str, failure_rate: float = 0.3, delay_ms: int = 100):
        """Initialize simulated API.

        Args:
            name: Name of the API
            failure_rate: Probability of failure (0.0 - 1.0)
            delay_ms: Simulated latency in milliseconds
        """
        super().__init__()
        self.name = name
        self.failure_rate = failure_rate
        self.delay_ms = delay_ms

    async def execute(self, data: dict, context: WorkflowContext) -> dict:
        """Execute simulated API call."""
        # Simulate network latency
        await asyncio.sleep(self.delay_ms / 1000.0)

        # Randomly fail
        if random.random() < self.failure_rate:
            raise Exception(f"{self.name} API temporarily unavailable")

        return {
            "api": self.name,
            "status": "success",
            "data": data.get("query", ""),
            "response_time_ms": self.delay_ms,
        }


async def generate_traces():
    """Generate various workflow patterns to display in UI."""
    # Initialize observability
    try:
        from observability_integration import initialize_observability

        success = initialize_observability(
            service_name="ui-test-app",
            enable_prometheus=False,  # Don't need Prometheus for this test
            enable_tta_ui=True,
            tta_ui_endpoint="http://localhost:8765",
        )

        if not success:
            print("⚠️  Observability not initialized - traces won't appear in UI")
            print("Make sure tta-observability-ui service is running!")
            return
    except ImportError:
        print("⚠️  observability_integration not available - using basic logging")

    print("🚀 Generating test traces for TTA UI...")
    print("📊 Open dashboard: http://localhost:8765")
    print()

    # Pattern 1: Simple Retry (will show retry attempts in timeline)
    print("1️⃣  Testing RetryPrimitive...")
    retry_workflow = RetryPrimitive(
        primitive=SimulatedAPICall("primary-api", failure_rate=0.5, delay_ms=50),
        max_retries=3,
        backoff_strategy="exponential",
        initial_delay=0.1,
    )

    context = WorkflowContext(data={"test": "retry_pattern"})
    try:
        result = await retry_workflow.execute({"query": "test data"}, context)
        print(f"   ✅ Success after retries: {result['api']}")
    except Exception as e:
        print(f"   ❌ Failed after retries: {e}")

    # Pattern 2: Fallback Chain (will show primary → fallback in timeline)
    print("\n2️⃣  Testing FallbackPrimitive...")
    fallback_workflow = FallbackPrimitive(
        primary=SimulatedAPICall("primary-api", failure_rate=0.8, delay_ms=100),
        fallbacks=[
            SimulatedAPICall("backup-api-1", failure_rate=0.5, delay_ms=80),
            SimulatedAPICall("backup-api-2", failure_rate=0.2, delay_ms=60),
        ],
    )

    context = WorkflowContext(data={"test": "fallback_pattern"})
    try:
        result = await fallback_workflow.execute({"query": "fallback test"}, context)
        print(f"   ✅ Succeeded with: {result['api']}")
    except Exception as e:
        print(f"   ❌ All fallbacks failed: {e}")

    # Pattern 3: Sequential Steps (will show step1 → step2 → step3)
    print("\n3️⃣  Testing SequentialPrimitive...")
    sequential = SequentialPrimitive(
        steps=[
            SimulatedAPICall("auth-service", failure_rate=0.1, delay_ms=30),
            SimulatedAPICall("data-service", failure_rate=0.2, delay_ms=80),
            SimulatedAPICall("analytics-service", failure_rate=0.1, delay_ms=50),
        ]
    )

    context = WorkflowContext(data={"test": "sequential_pattern"})
    try:
        result = await sequential.execute({"query": "sequential test"}, context)
        print(f"   ✅ All steps completed: {result[-1]['api']}")
    except Exception as e:
        print(f"   ❌ Pipeline failed: {e}")

    # Pattern 4: Complex nested workflow
    print("\n4️⃣  Testing Complex Nested Workflow...")
    complex_workflow = SequentialPrimitive(
        steps=[
            SimulatedAPICall("input-validator", failure_rate=0.1, delay_ms=20),
            RetryPrimitive(
                primitive=SimulatedAPICall(
                    "flaky-processor", failure_rate=0.4, delay_ms=60
                ),
                max_retries=2,
            ),
            FallbackPrimitive(
                primary=SimulatedAPICall("primary-db", failure_rate=0.6, delay_ms=100),
                fallbacks=[
                    SimulatedAPICall("cache-service", failure_rate=0.2, delay_ms=30)
                ],
            ),
            SimulatedAPICall("output-formatter", failure_rate=0.1, delay_ms=25),
        ]
    )

    context = WorkflowContext(data={"test": "complex_pattern"})
    try:
        result = await complex_workflow.execute({"query": "complex test"}, context)
        print("   ✅ Complex workflow succeeded")
    except Exception as e:
        print(f"   ❌ Complex workflow failed: {e}")

    # Generate multiple traces rapidly to test real-time updates
    print("\n5️⃣  Generating rapid-fire traces (watch UI update in real-time)...")
    simple_workflow = SimulatedAPICall("rapid-test", failure_rate=0.3, delay_ms=20)

    for i in range(10):
        context = WorkflowContext(data={"test": f"rapid_{i}"})
        try:
            await simple_workflow.execute({"query": f"rapid test {i}"}, context)
            print(f"   Trace {i + 1}/10: ✅", end="\r")
        except Exception:
            print(f"   Trace {i + 1}/10: ❌", end="\r")
        await asyncio.sleep(0.5)  # Small delay to see updates

    print("\n\n✨ Test complete!")
    print("📊 Check the dashboard at http://localhost:8765")
    print()
    print("Expected UI behavior:")
    print("  ✅ Overview tab shows 14+ traces")
    print("  ✅ Success rate should be 60-80%")
    print("  ✅ Timeline shows retry attempts, fallbacks, sequential steps")
    print("  ✅ Click any trace to see detailed span breakdown")
    print("  ✅ Primitives tab shows usage statistics")
    print("  ✅ Real-time updates as each trace completes")


if __name__ == "__main__":
    asyncio.run(generate_traces())
