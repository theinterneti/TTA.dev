"""Integration example showing observability with real workflow primitives."""

import asyncio

from tta_dev_primitives import WorkflowContext
from tta_dev_primitives.core.base import LambdaPrimitive


async def main() -> None:
    """Demonstrate observability with real workflow composition."""
    print("\n" + "=" * 60)
    print("Integration Example: Observability + Workflow Primitives")
    print("=" * 60 + "\n")

    # Create workflow steps
    async def validate_input(data: dict, ctx: WorkflowContext) -> dict:
        """Validate input data."""
        ctx.checkpoint("validation_start")
        await asyncio.sleep(0.02)  # Simulate validation
        ctx.checkpoint("validation_complete")
        return {**data, "validated": True}

    async def enrich_data(data: dict, ctx: WorkflowContext) -> dict:
        """Enrich data with additional information."""
        ctx.checkpoint("enrichment_start")
        await asyncio.sleep(0.03)  # Simulate enrichment
        ctx.checkpoint("enrichment_complete")
        return {**data, "enriched": True, "metadata": {"source": "api"}}

    async def process_data(data: dict, ctx: WorkflowContext) -> dict:
        """Process the enriched data."""
        ctx.checkpoint("processing_start")
        await asyncio.sleep(0.05)  # Simulate processing
        ctx.checkpoint("processing_complete")
        return {**data, "processed": True, "result": "success"}

    # Compose workflow
    validate = LambdaPrimitive(validate_input)
    enrich = LambdaPrimitive(enrich_data)
    process = LambdaPrimitive(process_data)

    workflow = validate >> enrich >> process

    # Create context with observability
    context = WorkflowContext(
        workflow_id="data-pipeline",
        session_id="session-123",
        player_id="user-456",
    )

    # Add custom tags
    context.tags["environment"] = "production"
    context.tags["pipeline_version"] = "2.0"

    print("Starting workflow execution...")
    print(f"Correlation ID: {context.correlation_id}\n")

    # Execute workflow
    input_data = {"query": "process this data", "priority": "high"}
    result = await workflow.execute(input_data, context)

    # Show results
    print("Workflow completed!")
    print(f"Total elapsed time: {context.elapsed_ms():.2f}ms\n")

    print("Checkpoints:")
    for name, timestamp in context.checkpoints:
        elapsed = (timestamp - context.start_time) * 1000
        print(f"  {elapsed:6.2f}ms - {name}")

    print(f"\nFinal result: {result}")

    print("\nOpenTelemetry attributes (for tracing):")
    for key, value in context.to_otel_context().items():
        print(f"  {key}: {value}")

    print("\n" + "=" * 60)
    print("Integration example completed!")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
