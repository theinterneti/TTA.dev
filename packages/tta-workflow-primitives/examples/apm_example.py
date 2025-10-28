"""Example: Using APM with workflow primitives.

This example demonstrates how to use OpenTelemetry APM with workflow primitives
to track performance, collect metrics, and export to Prometheus.
"""

import asyncio
import logging
from typing import Any

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import workflow primitives
from tta_workflow_primitives.apm import setup_apm
from tta_workflow_primitives.apm.decorators import trace_workflow, track_metric
from tta_workflow_primitives.apm.instrumented import APMWorkflowPrimitive
from tta_workflow_primitives.core.base import WorkflowContext


# Example 1: Using APMWorkflowPrimitive base class
class DataProcessor(APMWorkflowPrimitive):
    """Example primitive that processes data with APM tracking."""

    async def _execute_impl(
        self, input_data: dict[str, Any], context: WorkflowContext
    ) -> dict[str, Any]:
        """Process the data."""
        logger.info(f"Processing data: {input_data}")

        # Simulate processing
        await asyncio.sleep(0.1)

        result = {
            "processed": True,
            "input_count": len(input_data),
            "output": f"Processed {input_data.get('value', 'unknown')}",
        }

        return result


class DataValidator(APMWorkflowPrimitive):
    """Example primitive that validates data with APM tracking."""

    async def _execute_impl(
        self, input_data: dict[str, Any], context: WorkflowContext
    ) -> dict[str, Any]:
        """Validate the data."""
        logger.info(f"Validating data: {input_data}")

        # Simulate validation
        await asyncio.sleep(0.05)

        is_valid = input_data.get("processed", False)

        if not is_valid:
            raise ValueError("Data validation failed")

        return {**input_data, "validated": True}


# Example 2: Using decorators for custom functions
@trace_workflow("custom_transform")
@track_metric("transform_operations", "counter", "Number of transformations")
async def custom_transform(data: dict[str, Any]) -> dict[str, Any]:
    """Custom transformation with decorators."""
    await asyncio.sleep(0.1)
    return {**data, "transformed": True, "timestamp": "2025-10-26"}


async def main() -> None:
    """Run the APM example."""

    # Step 1: Setup APM
    logger.info("Setting up APM with Prometheus export...")
    setup_apm(
        service_name="apm-example",
        enable_prometheus=True,
        enable_console=True,  # Enable console output for demo
    )

    # Step 2: Create workflow context
    context = WorkflowContext(
        workflow_id="example-workflow-001",
        session_id="session-123",
        metadata={"environment": "development"},
    )

    # Step 3: Create and compose primitives
    processor = DataProcessor(name="processor")
    validator = DataValidator(name="validator")

    # Compose workflow using >> operator
    workflow = processor >> validator

    # Step 4: Execute workflow
    logger.info("Executing workflow...")

    input_data = {"value": "test_data", "priority": "high"}

    try:
        result = await workflow.execute(input_data, context)
        logger.info(f"Workflow result: {result}")
    except Exception as e:
        logger.error(f"Workflow failed: {e}")

    # Step 5: Try with custom function
    logger.info("Running custom transform...")
    transformed = await custom_transform(result)
    logger.info(f"Transformed result: {transformed}")

    # Step 6: Simulate multiple executions for metrics
    logger.info("Running multiple executions for metrics...")
    for i in range(5):
        try:
            test_data = {"value": f"test_{i}", "priority": "normal"}
            await workflow.execute(test_data, context)
            await asyncio.sleep(0.2)
        except Exception as e:
            logger.error(f"Execution {i} failed: {e}")

    logger.info("✓ APM example complete!")
    logger.info("Metrics are being exported to Prometheus on port 9464")
    logger.info("Access metrics at: http://localhost:9464/metrics")


if __name__ == "__main__":
    # Run the example
    asyncio.run(main())

    print("\n" + "=" * 70)
    print("APM Example Summary")
    print("=" * 70)
    print("\n✓ Executed workflow with APM instrumentation")
    print("✓ Collected metrics:")
    print("  - primitive.processor.executions (counter)")
    print("  - primitive.processor.duration (histogram)")
    print("  - primitive.validator.executions (counter)")
    print("  - primitive.validator.duration (histogram)")
    print("  - transform_operations (counter)")
    print("\n✓ Traces captured with OpenTelemetry")
    print("✓ Metrics exported to Prometheus")
    print("\nNext steps:")
    print("1. View metrics: http://localhost:9464/metrics")
    print("2. Import into Prometheus")
    print("3. Create Grafana dashboards")
    print("4. Add to your own workflows!")
