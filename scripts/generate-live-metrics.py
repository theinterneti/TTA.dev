#!/usr/bin/env python3
"""
Simple TTA.dev workflow to generate metrics for observability testing.

This script runs a basic workflow that generates real TTA.dev metrics
and keeps a metrics server running so Prometheus can scrape them.
"""

import asyncio
import signal
import sys
from pathlib import Path

# Add packages to path
repo_root = Path(__file__).parent.parent
sys.path.insert(0, str(repo_root / "packages"))

from tta_dev_primitives import WorkflowContext, SequentialPrimitive
from tta_dev_primitives.performance import CachePrimitive
from tta_dev_primitives.recovery import RetryPrimitive, TimeoutPrimitive
from tta_dev_primitives.observability.enhanced_collector import EnhancedMetricsCollector
from tta_dev_primitives.observability.prometheus_exporter import TTAPrometheusExporter


class SimpleWorkflowPrimitive:
    """Simple primitive that generates realistic metrics."""

    def __init__(self, name: str, base_delay: float = 0.1):
        self.name = name
        self.base_delay = base_delay

    async def execute(self, input_data: dict, context: WorkflowContext) -> dict:
        """Execute with some realistic processing time."""
        import random
        await asyncio.sleep(self.base_delay + random.uniform(0, 0.1))
        return {
            "result": f"Processed by {self.name}",
            "input_size": len(str(input_data)),
            "timestamp": context.correlation_id
        }


async def create_test_workflow():
    """Create a workflow that generates interesting metrics."""

    # Create some primitives
    validator = SimpleWorkflowPrimitive("validator", 0.01)
    processor = SimpleWorkflowPrimitive("processor", 0.2)
    enricher = SimpleWorkflowPrimitive("enricher", 0.05)

    # Add caching and retry for more interesting metrics
    cached_processor = CachePrimitive(
        primitive=processor,
        ttl_seconds=300,
        max_size=100
    )

    reliable_processor = RetryPrimitive(
        primitive=cached_processor,
        max_retries=3,
        backoff_strategy="exponential"
    )

    timeout_processor = TimeoutPrimitive(
        primitive=reliable_processor,
        timeout_seconds=5.0
    )

    # Create sequential workflow
    workflow = SequentialPrimitive([
        validator,
        timeout_processor,
        enricher
    ])

    return workflow


async def generate_metrics_continuously():
    """Run workflows continuously to generate metrics."""

    workflow = await create_test_workflow()
    run_count = 0

    print("🚀 Generating TTA.dev metrics...")
    print("   - Sequential workflow with cache, retry, and timeout")
    print("   - Metrics will show up in Prometheus at http://localhost:9090")
    print("   - Press Ctrl+C to stop")
    print()

    try:
        while True:
            run_count += 1
            context = WorkflowContext(
                correlation_id=f"metrics-test-{run_count}",
                workflow_id=f"metrics-workflow-{run_count}"
            )

            # Mix of cache hits and misses
            if run_count % 3 == 0:
                input_data = {"query": "repeated query", "run": run_count}  # Cache hit
            else:
                input_data = {"query": f"unique query {run_count}", "run": run_count}  # Cache miss

            try:
                result = await workflow.execute(input_data, context)
                print(f"✓ Run {run_count:3d}: {result['result'][:50]}...")
            except Exception as e:
                print(f"✗ Run {run_count:3d}: Failed - {e}")

            # Vary the frequency to create interesting patterns
            if run_count % 10 == 0:
                await asyncio.sleep(2)  # Occasional pause
            else:
                await asyncio.sleep(0.5)  # Regular frequency

    except KeyboardInterrupt:
        print(f"\n🛑 Stopped after {run_count} runs")


async def start_metrics_server_and_generate():
    """Start metrics server and generate continuous metrics."""

    print("📊 Starting TTA.dev Metrics Generation")
    print("=====================================")

    # Set up metrics collection
    collector = EnhancedMetricsCollector()
    exporter = TTAPrometheusExporter(collector)

    try:
        # Start metrics server
        await exporter.start()
        print("✅ Metrics server started on http://0.0.0.0:9464/metrics")
        print("🔗 Prometheus will scrape from: http://host.docker.internal:9464/metrics")
        print()

        # Generate metrics continuously
        await generate_metrics_continuously()

    except KeyboardInterrupt:
        print("\n🛑 Shutting down...")
    finally:
        await exporter.stop()
        print("✅ Metrics server stopped")


def main():
    """Main entry point."""

    # Handle signals gracefully
    def signal_handler(signum, frame):
        print(f"\n📡 Received signal {signum}")
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Run the metrics generation
    asyncio.run(start_metrics_server_and_generate())


if __name__ == "__main__":
    main()
