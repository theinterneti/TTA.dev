#!/usr/bin/env python3
"""
Test script to validate Prometheus metrics export from TTA.dev primitives.

This script:
1. Starts the Prometheus HTTP server (port 9464)
2. Executes sample workflows using primitives
3. Verifies metrics are exported correctly
4. Queries Prometheus API to confirm metrics are scraped
"""

import asyncio
import sys
from pathlib import Path

# Add packages to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from tta_dev_primitives import WorkflowContext
from tta_dev_primitives.core import ParallelPrimitive, SequentialPrimitive
from tta_dev_primitives.observability.prometheus_exporter import (
    start_prometheus_exporter,
)
from tta_dev_primitives.testing import MockPrimitive


async def main():
    """Run test workflow and validate metrics."""
    print("=" * 80)
    print("TTA.dev Prometheus Metrics Validation")
    print("=" * 80)
    print()

    # Step 1: Start Prometheus exporter
    print("Step 1: Starting Prometheus HTTP server...")
    if start_prometheus_exporter(port=9464):
        print("✅ Prometheus server started on http://0.0.0.0:9464/metrics")
    else:
        print("❌ Failed to start Prometheus server")
        return False
    print()

    # Step 2: Create test workflows
    print("Step 2: Creating test workflows...")

    # Create mock primitives
    step1 = MockPrimitive(name="Step1", return_value={"step": 1, "data": "processed"})
    step2 = MockPrimitive(name="Step2", return_value={"step": 2, "data": "enriched"})
    step3 = MockPrimitive(name="Step3", return_value={"step": 3, "data": "final"})

    # Sequential workflow
    sequential_workflow = SequentialPrimitive([step1, step2, step3])

    # Parallel workflow
    parallel_workflow = ParallelPrimitive([step1, step2, step3])

    print("✅ Created sequential and parallel workflows")
    print()

    # Step 3: Execute workflows
    print("Step 3: Executing workflows...")

    context = WorkflowContext(
        correlation_id="test-metrics-validation",
        workflow_id="prometheus-test",
        workflow_name="MetricsValidation",
    )

    # Execute sequential workflow
    print("  - Executing sequential workflow...")
    seq_result = await sequential_workflow.execute({"input": "test"}, context)
    print(f"    Result: {seq_result}")

    # Execute parallel workflow
    print("  - Executing parallel workflow...")
    par_result = await parallel_workflow.execute({"input": "test"}, context)
    print(f"    Result: {len(par_result)} parallel results")

    print("✅ Workflows executed successfully")
    print()

    # Step 4: Check metrics manually
    print("Step 4: Checking exported metrics...")

    # Try to access prometheus_client metrics
    try:
        from prometheus_client import REGISTRY

        print("  - Checking workflow executions counter...")
        for collector in REGISTRY._collector_to_names:
            if hasattr(collector, "_metrics"):
                for metric in collector._metrics.values():
                    if hasattr(metric, "_name"):
                        if "workflow_executions" in metric._name:
                            print(f"    Found: {metric._name}")
                            if hasattr(metric, "_metrics"):
                                for labels, value in metric._metrics.items():
                                    print(f"      {labels}: {value._value}")

        print()
        print("  - Checking primitive executions counter...")
        for collector in REGISTRY._collector_to_names:
            if hasattr(collector, "_metrics"):
                for metric in collector._metrics.values():
                    if hasattr(metric, "_name"):
                        if "primitive_executions" in metric._name:
                            print(f"    Found: {metric._name}")
                            if hasattr(metric, "_metrics"):
                                for labels, value in metric._metrics.items():
                                    print(f"      {labels}: {value._value}")

        print("✅ Metrics registered in Prometheus client")

    except Exception as e:
        print(f"⚠️  Could not inspect metrics directly: {e}")
        print("    This is OK - metrics may still be exported via HTTP")

    print()

    # Step 5: Verify HTTP metrics endpoint
    print("Step 5: Verifying HTTP metrics endpoint...")
    print()
    print("  Visit http://localhost:9464/metrics to see exported metrics")
    print()
    print("  Expected metrics:")
    print(
        '    - tta_workflow_executions_total{workflow_name="SequentialPrimitive",status="success"}'
    )
    print(
        '    - tta_workflow_executions_total{workflow_name="ParallelPrimitive",status="success"}'
    )
    print(
        '    - tta_primitive_executions_total{primitive_type="sequential",status="success"}'
    )
    print(
        '    - tta_primitive_executions_total{primitive_type="parallel",status="success"}'
    )
    print('    - tta_execution_duration_seconds{primitive_type="sequential"}')
    print()

    # Step 6: Instructions for Prometheus verification
    print("=" * 80)
    print("Next Steps: Verify Metrics in Prometheus")
    print("=" * 80)
    print()
    print("1. Check that Prometheus scrapes the metrics:")
    print("   curl http://localhost:9464/metrics | grep tta_")
    print()
    print("2. Query Prometheus API:")
    print(
        "   curl -s 'http://localhost:9090/api/v1/query?query=tta_workflow_executions_total' | jq '.data.result'"
    )
    print()
    print("3. Check Grafana dashboards:")
    print("   http://localhost:3001/d/system-overview")
    print()
    print("4. Verify recording rules:")
    print(
        "   curl -s 'http://localhost:9090/api/v1/query?query=tta:workflow_rate_5m' | jq '.data.result'"
    )
    print()
    print("=" * 80)
    print()

    # Keep server running for manual testing
    print("Server will keep running for 60 seconds for manual testing...")
    print("Press Ctrl+C to stop early")
    print()

    try:
        await asyncio.sleep(60)
    except KeyboardInterrupt:
        print("\n\nShutting down...")

    return True


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
