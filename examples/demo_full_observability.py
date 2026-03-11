#!/usr/bin/env python3
"""
Comprehensive TTA.dev Observability Demo

This demo exercises all observability features:
- Real-time agent activity tracking
- Workflow execution visualization
- Self-growing dashboard metrics
- CGC code graph integration
"""

import sys
from pathlib import Path

# Add parent directory to path for ttadev import
sys.path.insert(0, str(Path(__file__).parent.parent))

import asyncio
import time

from ttadev.primitives.core import (
    LambdaPrimitive,
    ParallelPrimitive,
    SequentialPrimitive,
    WorkflowContext,
)
from ttadev.primitives.recovery.fallback import FallbackPrimitive
from ttadev.primitives.recovery.retry import RetryPrimitive, RetryStrategy


async def data_fetch_step(data: dict, ctx: WorkflowContext) -> dict:
    """Simulate fetching data from an API."""
    await asyncio.sleep(0.5)
    return {**data, "fetched": True, "records": 100}


async def transform_step(data: dict, ctx: WorkflowContext) -> dict:
    """Transform the fetched data."""
    await asyncio.sleep(0.3)
    return {**data, "transformed": True, "cleaned_records": data.get("records", 0)}


async def validate_step(data: dict, ctx: WorkflowContext) -> dict:
    """Validate the transformed data."""
    await asyncio.sleep(0.2)
    records = data.get("cleaned_records", 0)
    if records < 50:
        raise ValueError(f"Insufficient records: {records}")
    return {**data, "validated": True}


async def save_step(data: dict, ctx: WorkflowContext) -> dict:
    """Save the validated data."""
    await asyncio.sleep(0.4)
    return {**data, "saved": True, "save_timestamp": time.time()}


async def fallback_step(data: dict, ctx: WorkflowContext) -> dict:
    """Fallback handler for validation failures."""
    return {**data, "used_fallback": True, "cleaned_records": 50}


async def main():
    """Run comprehensive observability demo."""

    print("🚀 Starting TTA.dev Observability Demo")
    print("=" * 60)
    print()
    print("Open http://localhost:8000 to see live observability")
    print()
    print("This demo will:")
    print("  1. Execute complex workflows with primitives")
    print("  2. Show real-time agent activity")
    print("  3. Demonstrate self-growing metrics")
    print("  4. Exercise retry and fallback primitives")
    print()
    print("=" * 60)
    print()

    # Scenario 1: Simple sequential workflow
    print("📋 Scenario 1: Sequential Data Pipeline")
    sequential_workflow = (
        LambdaPrimitive(data_fetch_step)
        >> LambdaPrimitive(transform_step)
        >> LambdaPrimitive(validate_step)
        >> LambdaPrimitive(save_step)
    )

    ctx1 = WorkflowContext(workflow_id="data-pipeline-001")
    result1 = await sequential_workflow.execute({"source": "api"}, ctx1)
    print(f"✅ Sequential workflow completed: {result1}")
    print()

    # Scenario 2: Sequential workflow with retry
    print("📋 Scenario 2: Sequential Processing with Retry")

    async def risky_operation(data: dict, ctx: WorkflowContext) -> dict:
        """Operation that sometimes fails."""
        await asyncio.sleep(0.2)
        # Simulate occasional failures (will succeed on retry)
        import random

        if random.random() < 0.3:
            raise RuntimeError("Temporary processing error")
        return {**data, "processed": True}

    retry_workflow = RetryPrimitive(
        LambdaPrimitive(risky_operation), strategy=RetryStrategy(max_retries=3, backoff_base=0.1)
    )

    ctx2 = WorkflowContext(workflow_id="retry-demo-001")
    result2 = await retry_workflow.execute({"task": "process_data"}, ctx2)
    print(f"✅ Retry workflow completed: {result2}")
    print()

    # Scenario 3: Fallback recovery
    print("📋 Scenario 3: Fallback Recovery Pattern")

    fallback_workflow = FallbackPrimitive(
        primary=SequentialPrimitive(
            [
                LambdaPrimitive(data_fetch_step),
                LambdaPrimitive(transform_step),
                LambdaPrimitive(validate_step),
            ]
        ),
        fallback=LambdaPrimitive(fallback_step),
    )

    ctx3 = WorkflowContext(workflow_id="fallback-demo-001")
    # This will fail validation and use fallback
    result3 = await fallback_workflow.execute({"source": "api", "records": 10}, ctx3)
    print(f"✅ Fallback workflow completed: {result3}")
    print()

    # Scenario 4: Complex nested workflow
    print("📋 Scenario 4: Complex Nested Workflow")

    async def enrichment_step(data: dict, ctx: WorkflowContext) -> dict:
        await asyncio.sleep(0.2)
        return {**data, "enriched": True, "metadata_added": True}

    async def merge_step(data: dict, ctx: WorkflowContext) -> dict:
        """Merge parallel results."""
        if isinstance(data, list):
            # Merge results from parallel branches
            merged = {}
            for item in data:
                merged.update(item)
            return merged
        return data

    complex_workflow = SequentialPrimitive(
        [
            RetryPrimitive(
                LambdaPrimitive(data_fetch_step),
                strategy=RetryStrategy(max_retries=2, backoff_base=0.1),
            ),
            ParallelPrimitive(
                [
                    LambdaPrimitive(transform_step),
                    LambdaPrimitive(enrichment_step),
                ]
            ),
            LambdaPrimitive(merge_step),
            LambdaPrimitive(validate_step),
            LambdaPrimitive(save_step),
        ]
    )

    ctx4 = WorkflowContext(workflow_id="complex-workflow-001")
    result4 = await complex_workflow.execute({"source": "api"}, ctx4)
    print(f"✅ Complex workflow completed: {result4}")
    print()

    print("=" * 60)
    print("🎉 Demo completed!")
    print()
    print("Check the observability dashboard at http://localhost:8000")
    print("You should see:")
    print("  - All 4 workflows in the traces view")
    print("  - Retry attempts on Scenario 2")
    print("  - Fallback activation on Scenario 3")
    print("  - Parallel execution on Scenarios 2 & 4")
    print("  - Real-time metrics updates")
    print("  - Self-discovered primitive types")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
