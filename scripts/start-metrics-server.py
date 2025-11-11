#!/usr/bin/env python3
"""
Start the TTA.dev Prometheus metrics server.

This script starts a persistent Prometheus metrics server that exports
TTA.dev primitive metrics on port 9464.
"""

import asyncio
import signal
import sys
from pathlib import Path

# Add packages to path
repo_root = Path(__file__).parent.parent
sys.path.insert(0, str(repo_root / "packages"))

from tta_dev_primitives.observability.prometheus_exporter import TTAPrometheusExporter
from tta_dev_primitives.observability.enhanced_collector import EnhancedMetricsCollector


class MetricsServerService:
    """Service to run the Prometheus metrics server."""

    def __init__(self):
        self.exporter = None
        self.running = False

    async def start(self):
        """Start the metrics server."""
        try:
            # Create collector and exporter
            collector = EnhancedMetricsCollector()
            self.exporter = TTAPrometheusExporter(collector)

            # Start the HTTP server
            await self.exporter.start()
            print("✅ Prometheus metrics server started on http://0.0.0.0:9464/metrics")
            print("📊 Available metrics:")
            print("  - tta_workflow_primitive_duration_seconds")
            print("  - tta_workflow_slo_compliance_ratio")
            print("  - tta_workflow_error_budget_remaining")
            print("  - tta_workflow_requests_total")
            print("  - tta_workflow_active_requests")
            print("  - tta_workflow_cost_total")
            print("  - tta_workflow_savings_total")
            print("  - tta_workflow_rps")
            print()
            print("🔗 Integration:")
            print("  - Prometheus scrape: http://localhost:9464/metrics")
            print("  - Grafana datasource: http://prometheus:9090")
            print("  - Manual check: curl http://localhost:9464/metrics")
            print()
            print("Press Ctrl+C to stop the server")

            self.running = True

            # Keep running
            while self.running:
                await asyncio.sleep(1)

        except Exception as e:
            print(f"❌ Error starting metrics server: {e}")
            sys.exit(1)

    async def stop(self):
        """Stop the metrics server."""
        print("\n🛑 Stopping metrics server...")
        self.running = False
        if self.exporter:
            await self.exporter.stop()
        print("✅ Metrics server stopped")


async def main():
    """Main service function."""
    service = MetricsServerService()

    # Handle signals for graceful shutdown
    def signal_handler():
        print("\n📡 Received shutdown signal")
        asyncio.create_task(service.stop())

    # Set up signal handlers
    if sys.platform != 'win32':
        loop = asyncio.get_event_loop()
        for sig in (signal.SIGTERM, signal.SIGINT):
            loop.add_signal_handler(sig, signal_handler)

    try:
        await service.start()
    except KeyboardInterrupt:
        await service.stop()


if __name__ == "__main__":
    asyncio.run(main())
