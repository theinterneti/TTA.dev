#!/usr/bin/env python3
"""
Working TTA.dev metrics generator that properly integrates with Prometheus.

This script demonstrates the correct way to generate TTA.dev metrics
and export them via Prometheus.
"""

import asyncio
import signal
import sys
import time
from pathlib import Path

# Add packages to path
repo_root = Path(__file__).parent.parent
sys.path.insert(0, str(repo_root / "packages"))

from tta_dev_primitives import WorkflowContext
from tta_dev_primitives.core import SequentialPrimitive
from tta_dev_primitives.performance import CachePrimitive
from tta_dev_primitives.recovery import RetryPrimitive
from tta_dev_primitives.observability.enhanced_collector import get_enhanced_metrics_collector
from tta_dev_primitives.observability.prometheus_exporter import TTAPrometheusExporter


class TestPrimitive:
    """Simple test primitive for generating metrics."""

    def __init__(self, name: str, base_delay: float = 0.1):
        self.name = name
        self.base_delay = base_delay

    async def execute(self, input_data: dict, context: WorkflowContext) -> dict:
        """Execute with some realistic processing delay."""
        import random

        # Simulate some work
        delay = self.base_delay + random.uniform(0, 0.05)
        await asyncio.sleep(delay)

        # Occasionally fail to test retry metrics
        if random.random() < 0.1:  # 10% failure rate
            raise Exception(f"Simulated failure in {self.name}")

        return {
            "processed_by": self.name,
            "input_data": input_data,
            "processing_time": delay
        }


async def create_instrumented_workflow():
    """Create a workflow with instrumented primitives."""

    # Create basic primitives
    validator = TestPrimitive("validator", 0.02)
    processor = TestPrimitive("processor", 0.15)
    finalizer = TestPrimitive("finalizer", 0.03)

    # Add caching for interesting cache hit/miss metrics
    cached_processor = CachePrimitive(
        primitive=processor,
        ttl_seconds=60,  # Short TTL for demo
        max_size=10
    )

    # Add retry for failure handling metrics
    reliable_processor = RetryPrimitive(
        primitive=cached_processor,
        max_retries=3,
        backoff_strategy="exponential"
    )

    # Create the workflow
    workflow = SequentialPrimitive([
        validator,
        reliable_processor,
        finalizer
    ])

    return workflow


async def run_continuous_workflow():
    """Run workflow continuously to generate metrics."""

    workflow = await create_instrumented_workflow()
    collector = get_enhanced_metrics_collector()

    print("🚀 Running TTA.dev workflow to generate metrics...")
    print("   - Sequential workflow: validator → cached_processor → finalizer")
    print("   - With retry logic and cache (60s TTL)")
    print("   - 10% simulated failure rate for retry testing")
    print("   - Metrics available at: http://localhost:9464/metrics")
    print()

    run_count = 0

    try:
        while True:
            run_count += 1

            # Create context
            context = WorkflowContext(
                correlation_id=f"test-{run_count}",
                workflow_id=f"metrics-test-{run_count}"
            )

            # Generate mix of cacheable and unique requests
            if run_count % 4 == 0:
                # Repeated request for cache hits
                input_data = {"query": "cached_request", "type": "standard"}
            else:
                # Unique requests
                input_data = {"query": f"request_{run_count}", "type": "unique"}

            try:
                start_time = time.time()
                result = await workflow.execute(input_data, context)
                duration = time.time() - start_time

                print(f"✓ Run {run_count:3d}: {duration*1000:.1f}ms - {result['processed_by']}")

            except Exception as e:
                duration = time.time() - start_time
                print(f"✗ Run {run_count:3d}: {duration*1000:.1f}ms - Failed: {str(e)[:50]}...")

            # Show metrics summary every 10 runs
            if run_count % 10 == 0:
                print(f"\n📊 After {run_count} runs:")
                try:
                    # Get metrics from collector
                    primitives = getattr(collector, 'primitives', {})
                    for name, primitive in primitives.items():
                        if hasattr(primitive, 'total_requests'):
                            print(f"   {name}: {primitive.total_requests} requests")
                except Exception as e:
                    print(f"   (Could not retrieve metrics: {e})")
                print()

            # Vary timing for realistic patterns
            await asyncio.sleep(0.3 if run_count % 5 != 0 else 1.0)

    except KeyboardInterrupt:
        print(f"\n🛑 Completed {run_count} workflow runs")
        return run_count


def start_prometheus_server():
    """Start the Prometheus metrics server."""

    print("📊 Starting Prometheus metrics server...")

    try:
        exporter = TTAPrometheusExporter(port=9464, host="0.0.0.0")
        success = exporter.start()

        if success:
            print("✅ Metrics server started successfully")
            print("🔗 Prometheus scrape endpoint: http://localhost:9464/metrics")
            print("📈 View in Prometheus: http://localhost:9090")
            print()
            return exporter
        else:
            print("❌ Failed to start metrics server")
            return None

    except Exception as e:
        print(f"❌ Error starting metrics server: {e}")
        return None


async def main():
    """Main function that orchestrates metrics generation."""

    print("🎯 TTA.dev Live Metrics Generator")
    print("=================================")
    print()

    # Start Prometheus server
    exporter = start_prometheus_server()
    if not exporter:
        print("❌ Cannot continue without metrics server")
        return

    try:
        # Run workflow continuously
        total_runs = await run_continuous_workflow()
        print(f"✅ Generated metrics from {total_runs} workflow executions")

    except KeyboardInterrupt:
        print("\n🛑 Shutting down gracefully...")
    finally:
        if exporter:
            exporter.stop()
            print("✅ Metrics server stopped")


def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    print(f"\n📡 Received signal {signum} - shutting down...")
    sys.exit(0)


if __name__ == "__main__":
    # Set up signal handling
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Run the main function
    asyncio.run(main())
