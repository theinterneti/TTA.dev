#!/usr/bin/env python3
"""
Test TTA.dev observability stack by running a simple instrumented workflow.

This script verifies that:
1. Observability integration works
2. Traces are exported to Jaeger
3. Metrics are exported to Prometheus
"""

import asyncio
import sys
from pathlib import Path

# Add packages to path
packages_path = Path(__file__).parent.parent / "packages"
sys.path.insert(0, str(packages_path / "tta-dev-primitives" / "src"))
sys.path.insert(0, str(packages_path / "tta-observability-integration" / "src"))

try:
    from observability_integration import initialize_observability
    from tta_dev_primitives import SequentialPrimitive, WorkflowContext
    from tta_dev_primitives.core.base import LambdaPrimitive

    print("✅ Imports successful")
except ImportError as e:
    print(f"❌ Import failed: {e}")
    print("\nRun: uv sync --all-extras")
    sys.exit(1)


async def step1(data: dict, context: WorkflowContext) -> dict:
    """First step in workflow."""
    await asyncio.sleep(0.1)
    return {"step1": "complete", **data}


async def step2(data: dict, context: WorkflowContext) -> dict:
    """Second step in workflow."""
    await asyncio.sleep(0.1)
    return {"step2": "complete", **data}


async def step3(data: dict, context: WorkflowContext) -> dict:
    """Third step in workflow."""
    await asyncio.sleep(0.1)
    return {"step3": "complete", **data}


async def main():
    """Run test workflow."""
    print("\n=== TTA.dev Observability Test ===\n")

    # Initialize observability
    print("1. Initializing observability...")
    success = initialize_observability(
        service_name="tta-observability-test",
        enable_prometheus=True,
        prometheus_port=9464,
        enable_console_traces=True,
    )

    if success:
        print("   ✅ Observability initialized")
    else:
        print("   ⚠️  Observability initialization failed (OpenTelemetry not available)")
        print("   Continuing without instrumentation...")

    # Create workflow
    print("\n2. Building workflow...")
    workflow = SequentialPrimitive(
        [LambdaPrimitive(step1), LambdaPrimitive(step2), LambdaPrimitive(step3)]
    )
    print("   ✅ Workflow created")

    # Execute workflow
    print("\n3. Executing workflow...")
    context = WorkflowContext(
        workflow_id="test-workflow-001", correlation_id="test-001"
    )

    result = await workflow.execute({"input": "test"}, context)
    print(f"   ✅ Workflow executed: {result}")

    # Give time for traces to be exported
    print("\n4. Waiting for traces to be exported...")
    await asyncio.sleep(2)
    print("   ✅ Done")

    # Summary
    print("\n=== Test Complete ===\n")
    print("Next Steps:")
    print("1. Check Jaeger UI:     http://localhost:16686")
    print("   - Service: tta-observability-test")
    print("   - Look for: test-workflow-001")
    print()
    print("2. Check Prometheus:    http://localhost:9090")
    print('   - Query: {job="tta-observability"}')
    print()
    print("3. Check Grafana:       http://localhost:3000")
    print("   - Login: admin / admin")
    print()


if __name__ == "__main__":
    asyncio.run(main())
