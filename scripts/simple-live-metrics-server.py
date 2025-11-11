#!/usr/bin/env python
"""
TTA.dev Simple Live Metrics Server with Direct Prometheus Integration

Simple approach: Generate live TTA metrics directly using prometheus_client
without the complex enhanced collector integration.
"""

import asyncio
import signal
import sys
import time
from pathlib import Path

# Add packages to path
sys.path.insert(0, str(Path(__file__).parent.parent / "packages"))

try:
    from prometheus_client import Counter, Gauge, Histogram, start_http_server
    PROMETHEUS_CLIENT_AVAILABLE = True
except ImportError:
    print("❌ prometheus-client not available. Install with: uv pip install prometheus-client")
    sys.exit(1)

from tta_dev_primitives import (
    SequentialPrimitive,
    ParallelPrimitive,
    WorkflowContext
)
from tta_dev_primitives.performance import CachePrimitive
from tta_dev_primitives.testing import MockPrimitive


class SimpleLiveMetricsServer:
    """Simple live metrics server with direct Prometheus integration."""

    def __init__(self, port: int = 9464):
        self.port = port
        self.running = False
        self.workflow_counter = 0

        # Create Prometheus metrics directly
        self.setup_prometheus_metrics()

        # Create sample workflows
        self.setup_workflows()

    def setup_prometheus_metrics(self):
        """Create Prometheus metrics directly."""

        # Request counters
        self.request_counter = Counter(
            'tta_requests_total',
            'Total requests by primitive type',
            ['primitive_type', 'status']
        )

        # Duration histograms
        self.duration_histogram = Histogram(
            'tta_execution_duration_seconds',
            'Execution duration by primitive type',
            ['primitive_type']
        )

        # Active requests gauge
        self.active_requests = Gauge(
            'tta_active_requests',
            'Active requests by primitive type',
            ['primitive_type']
        )

        # Cache metrics
        self.cache_hits = Counter(
            'tta_cache_hits_total',
            'Cache hits by key',
            ['cache_key']
        )

        self.cache_misses = Counter(
            'tta_cache_misses_total',
            'Cache misses by key',
            ['cache_key']
        )

        self.cache_hit_rate = Gauge(
            'tta_cache_hit_rate',
            'Cache hit rate percentage',
            ['cache_key']
        )

        # Workflow-level metrics
        self.workflow_executions = Counter(
            'tta_workflow_executions_total',
            'Total workflow executions',
            ['workflow_type']
        )

        self.workflow_duration = Histogram(
            'tta_workflow_duration_seconds',
            'Workflow execution duration',
            ['workflow_type']
        )

        print("✅ Created Prometheus metrics:")
        print("  - tta_requests_total")
        print("  - tta_execution_duration_seconds")
        print("  - tta_active_requests")
        print("  - tta_cache_hits_total")
        print("  - tta_cache_misses_total")
        print("  - tta_cache_hit_rate")
        print("  - tta_workflow_executions_total")
        print("  - tta_workflow_duration_seconds")

    def setup_workflows(self):
        """Create sample workflows."""

        # Mock primitives for demo
        validation_primitive = MockPrimitive(
            name="input_validation",
            return_value={"status": "valid"}
        )

        llm_primitive = MockPrimitive(
            name="llm_generation",
            return_value={"response": "Sample response"}
        )

        # Create cached LLM
        cached_llm = CachePrimitive(
            primitive=llm_primitive,
            ttl_seconds=300,  # 5 minutes
            cache_key_fn=lambda data, ctx: "llm:default"
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

        print("🎯 Configured demo workflows:")
        print("  - MockPrimitive (input_validation)")
        print("  - CachePrimitive → MockPrimitive (llm_generation)")
        print("  - ParallelPrimitive → SequentialPrimitive")

    def start(self) -> bool:
        """Start the simple metrics server."""
        print(f"🚀 Starting TTA.dev simple live metrics server on port {self.port}")

        try:
            # Start Prometheus HTTP server
            start_http_server(self.port, addr="0.0.0.0")
            print(f"✅ Prometheus server started on http://0.0.0.0:{self.port}/metrics")
            print(f"📊 Docker scraping target: 172.17.0.1:{self.port}")

            self.running = True

            # Setup signal handlers
            signal.signal(signal.SIGINT, self._signal_handler)
            signal.signal(signal.SIGTERM, self._signal_handler)

            return True

        except Exception as e:
            print(f"❌ Failed to start metrics server: {e}")
            return False

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        print(f"\n🛑 Received signal {signum}, shutting down...")
        self.running = False

    def record_primitive_execution(self, primitive_type: str, duration_seconds: float, success: bool = True):
        """Record metrics for a primitive execution."""

        # Increment request counter
        status = "success" if success else "error"
        self.request_counter.labels(primitive_type=primitive_type, status=status).inc()

        # Record duration
        self.duration_histogram.labels(primitive_type=primitive_type).observe(duration_seconds)

    def simulate_cache_metrics(self, cache_key: str, hit: bool, hit_rate: float):
        """Simulate cache metrics."""
        if hit:
            self.cache_hits.labels(cache_key=cache_key).inc()
        else:
            self.cache_misses.labels(cache_key=cache_key).inc()

        # Update hit rate
        self.cache_hit_rate.labels(cache_key=cache_key).set(hit_rate / 100.0)  # Convert to ratio

    async def generate_workflow_metrics(self):
        """Generate metrics by executing workflows and recording metrics."""

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
                    "timestamp": time.time()
                }

                # Time the overall workflow
                start_time = time.time()
                result = await self.main_workflow.execute(input_data, context)
                total_duration = time.time() - start_time

                # Record workflow metrics
                self.workflow_executions.labels(workflow_type="demo_sequential").inc()
                self.workflow_duration.labels(workflow_type="demo_sequential").observe(total_duration)

                # Record individual primitive metrics (simulated based on workflow)
                self.record_primitive_execution("MockPrimitive", 0.015 + (self.workflow_counter % 10) * 0.001)
                self.record_primitive_execution("CachePrimitive", 0.005 + (self.workflow_counter % 5) * 0.001)
                self.record_primitive_execution("ParallelPrimitive", 0.025 + (self.workflow_counter % 15) * 0.001)
                self.record_primitive_execution("SequentialPrimitive", total_duration)

                # Simulate cache behavior (starts low, grows to high hit rate)
                cache_age = (self.workflow_counter * 3) % 300  # Reset every 5 minutes
                if cache_age < 30:  # First 30 seconds, building up cache
                    hit_rate = min(50 + cache_age * 1.5, 98)
                    cache_hit = cache_age > 5  # First few are misses
                else:  # Steady state with high hit rate
                    hit_rate = 98.0 + (self.workflow_counter % 50) * 0.02
                    cache_hit = True

                self.simulate_cache_metrics("llm:default", cache_hit, hit_rate)

                # Occasionally simulate failures for realistic metrics
                if self.workflow_counter % 50 == 0:
                    self.record_primitive_execution("MockPrimitive", 0.100, success=False)
                    print(f"⚠️  Simulated failure for MockPrimitive (workflow {self.workflow_counter})")

                # Log progress
                if self.workflow_counter % 10 == 0:
                    print(f"📈 Generated {self.workflow_counter} workflow executions")
                    print(f"   Cache hit rate: {hit_rate:.1f}%")
                    print(f"   Workflow duration: {total_duration*1000:.1f}ms")

                # Wait before next execution
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
        print("🔄 Shutting down simple metrics server...")
        print("✅ Simple metrics server stopped")


async def main():
    """Main entry point."""
    server = SimpleLiveMetricsServer()

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
