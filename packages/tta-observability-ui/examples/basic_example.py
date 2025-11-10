"""Integration example showing how to use TTA Observability UI."""

import asyncio

from tta_dev_primitives import WorkflowContext
from tta_dev_primitives.recovery import RetryPrimitive


async def unreliable_operation(data: dict, context: WorkflowContext) -> dict:
    """Simulated unreliable operation."""
    import random

    if random.random() < 0.3:  # 30% failure rate
        raise Exception("Random failure!")

    await asyncio.sleep(0.1)
    return {"result": f"processed: {data.get('input')}"}


async def main():
    """Run example workflow with observability."""
    print("🔍 TTA Observability UI Integration Example")
    print("=" * 60)

    # Initialize observability
    print("\n1. Initializing observability...")
    try:
        from observability_integration import initialize_observability

        success = initialize_observability(
            service_name="observability-example",
            enable_prometheus=True,
            enable_tta_ui=True,  # Enable TTA UI collection
            tta_ui_endpoint="http://localhost:8765",
        )
        print(f"   ✅ Observability initialized: {success}")
    except ImportError:
        print("   ⚠️  observability_integration not available, using basic mode")

    # Create workflow with retry primitive
    print("\n2. Creating workflow with RetryPrimitive...")
    workflow = RetryPrimitive(
        primitive=unreliable_operation,
        max_retries=3,
        backoff_strategy="exponential",
        initial_delay=0.1,
    )
    print("   ✅ Workflow created")

    # Execute workflow
    print("\n3. Executing workflow...")
    context = WorkflowContext(
        correlation_id="example-001",
        data={"user_id": "user-123", "environment": "development"},
    )

    try:
        result = await workflow.execute({"input": "test data"}, context)
        print(f"   ✅ Execution succeeded: {result}")
    except Exception as e:
        print(f"   ❌ Execution failed: {e}")

    # Show where to view traces
    print("\n4. View traces:")
    print("   📊 TTA UI: http://localhost:8765")
    print("   📊 API: http://localhost:8765/api/traces")
    print("   📊 Metrics: http://localhost:8765/api/metrics/summary")

    print("\n" + "=" * 60)
    print("Example complete! Check the URLs above to see traces.")


if __name__ == "__main__":
    asyncio.run(main())
