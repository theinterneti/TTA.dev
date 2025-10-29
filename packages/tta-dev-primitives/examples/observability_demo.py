"""Example demonstrating Phase 1 observability features."""

import asyncio

from tta_dev_primitives.core.base import WorkflowContext, WorkflowPrimitive


# Example 1: Using enhanced WorkflowContext
async def example_workflow_context() -> None:
    """Demonstrate WorkflowContext observability features."""
    print("\n=== Example 1: Enhanced WorkflowContext ===\n")

    # Create context with automatic correlation_id
    context = WorkflowContext(
        workflow_id="demo-workflow", session_id="user-session-123", player_id="player-456"
    )

    print(f"Workflow ID: {context.workflow_id}")
    print(f"Session ID: {context.session_id}")
    print(f"Auto-generated Correlation ID: {context.correlation_id}")

    # Add checkpoints
    context.checkpoint("validation_start")
    await asyncio.sleep(0.1)
    context.checkpoint("validation_complete")

    await asyncio.sleep(0.05)
    context.checkpoint("processing_complete")

    # Check elapsed time
    print(f"\nElapsed time: {context.elapsed_ms():.2f}ms")
    print(f"Checkpoints recorded: {len(context.checkpoints)}")

    for name, timestamp in context.checkpoints:
        elapsed = (timestamp - context.start_time) * 1000
        print(f"  - {name}: {elapsed:.2f}ms")

    # Add custom tags and baggage
    context.tags["environment"] = "development"
    context.tags["version"] = "1.0.0"
    context.baggage["user_tier"] = "premium"

    print(f"\nTags: {context.tags}")
    print(f"Baggage: {context.baggage}")


# Example 2: Creating child contexts
async def example_child_context() -> None:
    """Demonstrate child context creation for nested workflows."""
    print("\n=== Example 2: Child Context Creation ===\n")

    # Parent context
    parent = WorkflowContext(
        workflow_id="parent-workflow",
        session_id="session-789",
        trace_id="0123456789abcdef0123456789abcdef",
        span_id="parent-span-id",
    )
    parent.tags["source"] = "api"

    print("Parent context:")
    print(f"  Workflow ID: {parent.workflow_id}")
    print(f"  Trace ID: {parent.trace_id}")
    print(f"  Span ID: {parent.span_id}")
    print(f"  Correlation ID: {parent.correlation_id}")

    # Create child for nested operation
    child = parent.create_child_context()

    print("\nChild context:")
    print(f"  Workflow ID: {child.workflow_id}")
    print(f"  Trace ID: {child.trace_id} (inherited)")
    print(f"  Parent Span ID: {child.parent_span_id} (parent's span becomes parent)")
    print(f"  Correlation ID: {child.correlation_id} (inherited)")
    print(f"  Causation ID: {child.causation_id} (causation chain)")
    print(f"  Tags: {child.tags} (copied)")


# Example 3: OpenTelemetry integration (without actually using OpenTelemetry)
async def example_otel_context() -> None:
    """Demonstrate to_otel_context() for OpenTelemetry integration."""
    print("\n=== Example 3: OpenTelemetry Context Attributes ===\n")

    context = WorkflowContext(
        workflow_id="data-pipeline-123",
        session_id="processing-session-456",
        player_id="user-789",
    )

    await asyncio.sleep(0.05)  # Simulate some work

    # Get OpenTelemetry-compatible attributes
    otel_attrs = context.to_otel_context()

    print("OpenTelemetry attributes for span:")
    for key, value in otel_attrs.items():
        print(f"  {key}: {value}")

    print("\nThese attributes can be attached to OpenTelemetry spans:")
    print("  from opentelemetry import trace")
    print("  span = trace.get_current_span()")
    print("  for key, value in context.to_otel_context().items():")
    print("      span.set_attribute(key, value)")


# Example 4: Using InstrumentedPrimitive (if observability package available)
try:
    from tta_dev_observability.instrumentation.base import InstrumentedPrimitive

    class DataProcessor(InstrumentedPrimitive[dict, dict]):
        """Example instrumented primitive."""

        async def _execute_impl(self, input_data: dict, context: WorkflowContext) -> dict:
            """Process data with automatic instrumentation."""
            # Simulate processing
            await asyncio.sleep(0.05)

            # Add checkpoint in context
            context.checkpoint("data_validated")

            # Return processed data
            return {**input_data, "processed": True, "processor": "DataProcessor"}

    async def example_instrumented_primitive() -> None:
        """Demonstrate InstrumentedPrimitive usage."""
        print("\n=== Example 4: InstrumentedPrimitive ===\n")

        processor = DataProcessor(name="data-processor")
        context = WorkflowContext(workflow_id="instrumented-demo")

        print(f"Primitive name: {processor.name}")
        print("Executing primitive with automatic instrumentation...")

        result = await processor.execute({"data": "test"}, context)

        print(f"Result: {result}")
        print(f"Context now has correlation ID: {context.correlation_id}")
        print(f"Checkpoints: {[name for name, _ in context.checkpoints]}")

        print(
            "\nInstrumentedPrimitive automatically adds:\n"
            "  - Distributed tracing\n"
            "  - Structured logging\n"
            "  - Exception tracking\n"
            "  - Performance metrics"
        )

    OBSERVABILITY_AVAILABLE = True
except ImportError:
    OBSERVABILITY_AVAILABLE = False


async def main() -> None:
    """Run all examples."""
    print("=" * 60)
    print("Phase 1 Observability Foundation Examples")
    print("=" * 60)

    await example_workflow_context()
    await example_child_context()
    await example_otel_context()

    if OBSERVABILITY_AVAILABLE:
        await example_instrumented_primitive()
    else:
        print("\n=== Example 4: InstrumentedPrimitive ===\n")
        print("tta-dev-observability not available.")
        print("Install with: uv pip install -e packages/tta-dev-observability")

    print("\n" + "=" * 60)
    print("All examples completed!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
