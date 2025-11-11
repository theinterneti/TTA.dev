#!/usr/bin/env python
"""
TTA.dev Enhanced Metrics Server with Manual Metrics Recording

Runs the Prometheus metrics server continuously and generates live workflow metrics
by executing TTA primitives with manual metrics collection.
"""

import asyncio
import signal
import sys
import time
from pathlib import Path

# Add packages to path
sys.path.insert(0, str(Path(__file__).parent.parent / "packages"))

from tta_dev_primitives.observability.prometheus_exporter import TTAPrometheusExporter
from tta_dev_primitives.observability.enhanced_collector import get_enhanced_metrics_collector
from tta_dev_primitives import (
    SequentialPrimitive,
    ParallelPrimitive,
    WorkflowContext
)
from tta_dev_primitives.performance import CachePrimitive
from tta_dev_primitives.recovery import RetryPrimitive
from tta_dev_primitives.testing import MockPrimitive


class EnhancedLiveMetricsServer:
    """Runs Prometheus metrics server with live workflow execution and manual metrics collection."""

    def __init__(self, port: int = 9464):
        self.port = port
        self.exporter = TTAPrometheusExporter(port=port)
        self.collector = get_enhanced_metrics_collector()
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
            ttl_seconds=300,  # 5 minutes
            cache_key_fn=lambda data, ctx: "llm:default"
        )

        # Create retry wrapper with proper strategy
        from tta_dev_primitives.recovery.retry import RetryStrategy
        reliable_processing = RetryPrimitive(
            primitive=processing_primitive,
            strategy=RetryStrategy(max_retries=2, backoff_base=2.0)
        )

        # Create parallel workflow
        parallel_workflow = ParallelPrimitive([
            cached_llm,
            validation_primitive
        ])

        # Main sequential workflow
        self.main_workflow = SequentialPrimitive([
            validation_primitive,
            parallel_workflow
        ])

        # Configure SLOs for each primitive type
        self.collector.configure_slo("MockPrimitive", target=0.99, threshold_ms=100.0)
        self.collector.configure_slo("CachePrimitive", target=0.95, threshold_ms=50.0)
        self.collector.configure_slo("ParallelPrimitive", target=0.98, threshold_ms=200.0)
        self.collector.configure_slo("SequentialPrimitive", target=0.99, threshold_ms=300.0)
        self.collector.configure_slo("RetryPrimitive", target=0.97, threshold_ms=500.0)

        print("🎯 Configured workflows with SLO targets:")
        print("  - MockPrimitive: 99% availability, <100ms latency")
        print("  - CachePrimitive: 95% availability, <50ms latency")
        print("  - ParallelPrimitive: 98% availability, <200ms latency")
        print("  - SequentialPrimitive: 99% availability, <300ms latency")
        print("  - RetryPrimitive: 97% availability, <500ms latency")

    def start(self) -> bool:
        """Start the enhanced metrics server."""
        print(f"🚀 Starting TTA.dev enhanced metrics server on port {self.port}")

        # Start the Prometheus server
        success = self.exporter.start()
        if not success:
            print(f"❌ Failed to start metrics server on port {self.port}")
            return False

        self.running = True
        print(f"✅ Enhanced metrics server running at http://localhost:{self.port}/metrics")
        print(f"📊 Prometheus scraping target: 172.17.0.1:{self.port}")
        print(f"🎬 Starting live workflow execution with manual metrics collection...")

        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

        return True

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        print(f"\n🛑 Received signal {signum}, shutting down...")
        self.running = False

    async def record_primitive_metrics(self, primitive_name: str, duration_ms: float, success: bool = True, cost: float = 0.001):
        """Manually record metrics for a primitive execution."""
        self.collector.start_request(primitive_name)

        # Simulate some processing time
        await asyncio.sleep(0.001)

        self.collector.record_execution(
            primitive_name,
            duration_ms=duration_ms,
            success=success,
            cost=cost
        )

        self.collector.end_request(primitive_name)

    async def generate_workflow_metrics(self):
        """Generate metrics by executing workflows periodically with manual metrics recording."""
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

                # Execute workflow with timing
                input_data = {
                    "query": f"Sample query {self.workflow_counter}",
                    "timestamp": asyncio.get_event_loop().time()
                }

                # Time the overall workflow
                start_time = time.time()
                result = await self.main_workflow.execute(input_data, context)
                total_duration = (time.time() - start_time) * 1000  # Convert to ms

                # Manually record metrics for each primitive type that was used
                await self.record_primitive_metrics("MockPrimitive", duration_ms=15.0 + (self.workflow_counter % 10))
                await self.record_primitive_metrics("CachePrimitive", duration_ms=5.0 + (self.workflow_counter % 5))
                await self.record_primitive_metrics("ParallelPrimitive", duration_ms=25.0 + (self.workflow_counter % 15))
                await self.record_primitive_metrics("SequentialPrimitive", duration_ms=total_duration)

                # Occasionally simulate failures for realistic metrics
                if self.workflow_counter % 20 == 0:
                    await self.record_primitive_metrics("MockPrimitive", duration_ms=100.0, success=False)
                    print(f"⚠️  Simulated failure for MockPrimitive (workflow {self.workflow_counter})")

                # Log progress
                if self.workflow_counter % 10 == 0:
                    print(f"📈 Generated {self.workflow_counter} workflow executions with metrics")
                    # Show some metrics
                    mock_metrics = self.collector.get_all_metrics("MockPrimitive")
                    if mock_metrics:
                        print(f"   MockPrimitive: {mock_metrics.get('total_requests', 0)} requests, "
                              f"{mock_metrics.get('rps', 0):.2f} RPS")

                # Wait before next execution (3 seconds)
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
        print("🔄 Shutting down enhanced metrics server...")
        self.exporter.stop()
        print("✅ Enhanced metrics server stopped")


async def main():
    """Main entry point."""
    server = EnhancedLiveMetricsServer()

    if not server.start():
        return 1

    await server.run_forever()
    return 0


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
        sys.exit(0)
