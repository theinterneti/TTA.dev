#!/usr/bin/env python3
"""Test real TTA.dev workflow with observability."""

import asyncio
import sys
from pathlib import Path

# Add packages to path
sys.path.insert(
    0, str(Path(__file__).parent / "packages" / "tta-dev-primitives" / "src")
)

from tta_dev_primitives import WorkflowContext
from tta_dev_primitives.core.base import WorkflowPrimitive
from tta_dev_primitives.performance.cache import CachePrimitive
from tta_dev_primitives.recovery.retry import RetryPrimitive, RetryStrategy


class DataProcessorPrimitive(WorkflowPrimitive[dict, dict]):
    """Simulate data processing."""

    async def execute(self, input_data: dict, context: WorkflowContext) -> dict:
        """Process input data."""
        await asyncio.sleep(0.1)  # Simulate processing
        return {
            "processed": True,
            "data": input_data.get("data", ""),
            "count": len(input_data.get("data", "")),
        }


class ValidatorPrimitive(WorkflowPrimitive[dict, dict]):
    """Validate processed data."""

    async def execute(self, input_data: dict, context: WorkflowContext) -> dict:
        """Validate data."""
        await asyncio.sleep(0.05)
        return {**input_data, "validated": True, "timestamp": "2025-11-15"}


class EnricherPrimitive(WorkflowPrimitive[dict, dict]):
    """Enrich data with metadata."""

    async def execute(self, input_data: dict, context: WorkflowContext) -> dict:
        """Add enrichment."""
        await asyncio.sleep(0.05)
        return {
            **input_data,
            "enriched": True,
            "metadata": {"version": "1.0", "source": "test"},
        }


async def test_sequential_workflow():
    """Test sequential workflow with observability."""
    print("🔄 Testing Sequential Workflow...")

    # Build workflow: process → validate → enrich
    workflow = DataProcessorPrimitive() >> ValidatorPrimitive() >> EnricherPrimitive()

    # Execute with context
    context = WorkflowContext(
        workflow_id="test-sequential-001",
        correlation_id="test-run-001",
    )

    result = await workflow.execute(
        {"data": "Hello TTA.dev observability!"},
        context,
    )

    print(f"✅ Sequential workflow result: {result}")
    return result


async def test_parallel_workflow():
    """Test parallel workflow with observability."""
    print("\n🔄 Testing Parallel Workflow...")

    # Build parallel branches
    workflow = DataProcessorPrimitive() | ValidatorPrimitive() | EnricherPrimitive()

    context = WorkflowContext(
        workflow_id="test-parallel-001",
        correlation_id="test-run-002",
    )

    result = await workflow.execute(
        {"data": "Parallel test data"},
        context,
    )

    print(f"✅ Parallel workflow result: {len(result)} branches completed")
    return result


async def test_retry_workflow():
    """Test retry primitive with observability."""
    print("\n🔄 Testing Retry Workflow...")

    # Wrap processor in retry
    processor = DataProcessorPrimitive()
    retry_processor = RetryPrimitive(
        primitive=processor,
        strategy=RetryStrategy(max_retries=3, backoff_base=2.0, jitter=True),
    )

    context = WorkflowContext(
        workflow_id="test-retry-001",
        correlation_id="test-run-003",
    )

    result = await retry_processor.execute(
        {"data": "Retry test data"},
        context,
    )

    print(f"✅ Retry workflow result: {result}")
    return result


async def test_cache_workflow():
    """Test cache primitive with observability."""
    print("\n🔄 Testing Cache Workflow...")

    # Wrap processor with cache
    processor = DataProcessorPrimitive()
    cached_processor = CachePrimitive(
        primitive=processor,
        cache_key_fn=lambda data, ctx: str(data.get("data", "")),
        ttl_seconds=60.0,
    )

    context = WorkflowContext(
        workflow_id="test-cache-001",
        correlation_id="test-run-004",
    )

    input_data = {"data": "Cache test data"}

    # First call - cache miss
    print("  First call (cache miss)...")
    result1 = await cached_processor.execute(input_data, context)
    print(f"  Result: {result1}")

    # Second call - cache hit
    print("  Second call (cache hit)...")
    result2 = await cached_processor.execute(input_data, context)
    print(f"  Result: {result2}")

    print("✅ Cache workflow completed")
    return result2


async def test_complex_workflow():
    """Test complex nested workflow."""
    print("\n🔄 Testing Complex Nested Workflow...")

    # Build complex workflow with retry and cache
    processor = DataProcessorPrimitive()
    validator = ValidatorPrimitive()
    enricher = CachePrimitive(
        primitive=EnricherPrimitive(),
        cache_key_fn=lambda data, ctx: str(ctx.workflow_id),
        ttl_seconds=60.0,
    )

    # Sequential workflow with retry and cache
    workflow = (
        RetryPrimitive(
            primitive=processor,
            strategy=RetryStrategy(max_retries=2, backoff_base=1.5),
        )
        >> validator
        >> enricher  # Cached enrichment
    )

    context = WorkflowContext(
        workflow_id="test-complex-001",
        correlation_id="test-run-005",
    )

    result = await workflow.execute(
        {"data": "Complex workflow test"},
        context,
    )

    print(f"✅ Complex workflow result: {result}")
    return result


async def main():
    """Run all workflow tests."""
    print("=" * 60)
    print("🚀 TTA.dev Observability Test Suite")
    print("=" * 60)
    print()
    print("📊 Metrics will be available at:")
    print("   - Local: http://localhost:9464/metrics")
    print("   - Grafana Cloud: https://theinterneti.grafana.net/")
    print()
    print("🔍 Query in Grafana Cloud:")
    print("   tta_workflow_executions_total")
    print("   tta_primitive_executions_total")
    print("   tta_execution_duration_seconds")
    print()
    print("=" * 60)
    print()

    try:
        # Run all tests
        await test_sequential_workflow()
        await test_parallel_workflow()
        await test_retry_workflow()
        await test_cache_workflow()
        await test_complex_workflow()

        print("\n" + "=" * 60)
        print("✅ All workflow tests completed successfully!")
        print("=" * 60)
        print()
        print("📈 Check your metrics:")
        print("   1. Local: curl http://localhost:9464/metrics | grep tta_")
        print("   2. Grafana Cloud: https://theinterneti.grafana.net/explore")
        print()
        print("🎯 Expected metrics:")
        print("   - 5+ workflow executions")
        print("   - 10+ primitive executions")
        print("   - Latency distributions (p50, p95, p99)")
        print("   - Cache hit/miss ratios")
        print()

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
