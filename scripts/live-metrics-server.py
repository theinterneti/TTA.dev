#!/usr/bin/env python
"""
TTA.dev Metrics Server with Live Workflow Generation

Runs the Prometheus metrics server continuously and generates live workflow metrics
by executing TTA primitives in the same process.
"""

import asyncio
import signal
import sys
from pathlib import Path

# Add packages to path
sys.path.insert(0, str(Path(__file__).parent.parent / "packages"))

from tta_dev_primitives.observability.prometheus_exporter import TTAPrometheusExporter
from tta_dev_primitives import (
    SequentialPrimitive,
    ParallelPrimitive,
    WorkflowContext
)
from tta_dev_primitives.performance import CachePrimitive
from tta_dev_primitives.recovery import RetryPrimitive
from tta_dev_primitives.testing import MockPrimitive


class LiveMetricsServer:
    """Runs Prometheus metrics server with live workflow execution."""

    def __init__(self, port: int = 9464):
        self.port = port
        self.exporter = TTAPrometheusExporter(port=port)
        self.running = False
        self.workflow_counter = 0

        # Create sample workflows with metrics collection
        self.setup_workflows()

    def setup_workflows(self):
        """Create sample workflows that generate metrics."""

        # Mock primitives for demo
        validation_primitive = MockPrimitive(
            name="input_validation",
            return_value={"status": "valid"}
        )

        llm_primitive = MockPrimitive(
            name="llm_generation",
            return_value={"response": "Sample response"}
        )

        processing_primitive = MockPrimitive(
            name="data_enrichment",
            return_value={"processed": True}
        )

        # Create cached LLM
        cached_llm = CachePrimitive(
            primitive=llm_primitive,
            cache_key_fn=lambda data, ctx: f"llm:{data.get('query', 'default')}",
            ttl_seconds=300
        )

        # Create parallel workflow (skip retry for now to get basic metrics)
        parallel_workflow = ParallelPrimitive([
            cached_llm,
            processing_primitive
        ])

        # Create sequential workflow
        self.main_workflow = SequentialPrimitive([
            validation_primitive,
            parallel_workflow
        ])

    async def start(self):
        """Start the metrics server."""
        print(f"🚀 Starting TTA.dev live metrics server on port {self.port}")

        # Start the Prometheus server
        success = self.exporter.start()
        if not success:
            print(f"❌ Failed to start metrics server on port {self.port}")
            return False

        self.running = True
        print(f"✅ Metrics server running at http://localhost:{self.port}/metrics")
        print(f"📊 Prometheus scraping target: 172.17.0.1:{self.port}")

        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

        return True

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        print(f"\n🛑 Received signal {signum}, shutting down...")
        self.running = False

    async def generate_workflow_metrics(self):
        """Generate metrics by executing workflows periodically."""
        while self.running:
            try:
                self.workflow_counter += 1

                # Create workflow context
                context = WorkflowContext(
                    correlation_id=f"metrics-gen-{self.workflow_counter}",
                    data={
                        "workflow_id": f"live-workflow-{self.workflow_counter}"
                    }
                )

                # Execute workflow
                input_data = {
                    "query": f"Sample query {self.workflow_counter}",
                    "timestamp": asyncio.get_event_loop().time()
                }

                result = await self.main_workflow.execute(input_data, context)

                # Log progress
                if self.workflow_counter % 10 == 0:
                    print(f"📈 Generated {self.workflow_counter} workflow executions")

                # Wait before next execution (2-5 seconds)
                await asyncio.sleep(3)

            except Exception as e:
                print(f"⚠️  Error executing workflow: {e}")
                await asyncio.sleep(5)

    async def run_forever(self):
        """Keep the server running and generate metrics."""
        try:
            # Start metrics generation
            metrics_task = asyncio.create_task(self.generate_workflow_metrics())

            # Wait for shutdown
            while self.running:
                await asyncio.sleep(1)

            # Cancel metrics generation
            metrics_task.cancel()
            try:
                await metrics_task
            except asyncio.CancelledError:
                pass

        except KeyboardInterrupt:
            print("\n🛑 Keyboard interrupt received, shutting down...")
        finally:
            await self.shutdown()

    async def shutdown(self):
        """Clean shutdown."""
        print("🔄 Shutting down live metrics server...")
        self.exporter.stop()
        print("✅ Live metrics server stopped")


async def main():
    """Main entry point."""
    server = LiveMetricsServer()

    success = await server.start()
    if not success:
        sys.exit(1)

    print("\n" + "="*60)
    print("  TTA.dev Live Metrics Server Running")
    print("="*60)
    print(f"📊 Metrics endpoint: http://localhost:9464/metrics")
    print(f"🔍 Prometheus target: 172.17.0.1:9464")
    print(f"📈 Grafana dashboards: http://localhost:3000")
    print(f"🔄 Generating live workflow metrics every 3 seconds")
    print("\nPress Ctrl+C to stop")
    print("="*60)

    await server.run_forever()


if __name__ == "__main__":
    asyncio.run(main())
