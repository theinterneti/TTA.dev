#!/usr/bin/env python3
"""Simple test to verify Prometheus metrics are exported correctly."""

import asyncio
from tta_dev_primitives import WorkflowContext
from tta_dev_primitives.core import SequentialPrimitive
from tta_dev_primitives.testing import MockPrimitive
from tta_dev_primitives.observability.prometheus_exporter import start_prometheus_exporter


async def main():
    # Start Prometheus exporter
    print("Starting Prometheus exporter on port 9464...")
    start_prometheus_exporter(port=9464)

    # Create simple workflow
    print("Creating workflow...")
    step1 = MockPrimitive(name="Step1", return_value={"result": "success"})
    workflow = SequentialPrimitive([step1])

    # Execute workflow
    print("Executing workflow...")
    context = WorkflowContext(workflow_id="simple-test")
    result = await workflow.execute({"input": "test"}, context)
    print(f"Result: {result}")

    # Check metrics
    print("\nMetrics should now be available at http://localhost:9464/metrics")
    print("Run: curl http://localhost:9464/metrics | grep tta_")

    # Keep server running
    print("\nServer running... Press Ctrl+C to stop")
    try:
        await asyncio.sleep(300)
    except KeyboardInterrupt:
        print("\nStopping...")


if __name__ == "__main__":
    asyncio.run(main())
