#!/usr/bin/env python
"""
Persistent TTA.dev Metrics Server

Runs the Prometheus metrics server continuously and generates sample workflow metrics
for demonstration and development purposes.
"""

import asyncio
import signal
import sys
from pathlib import Path

# Add packages to path
sys.path.insert(0, str(Path(__file__).parent.parent / "packages"))

from tta_dev_primitives.observability.prometheus_exporter import TTAPrometheusExporter


class PersistentMetricsServer:
    """Runs Prometheus metrics server with continuous sample data."""

    def __init__(self, port: int = 9464):
        self.port = port
        self.exporter = TTAPrometheusExporter(port=port)
        self.running = False

    async def start(self):
        """Start the metrics server."""
        print(f"🚀 Starting TTA.dev metrics server on port {self.port}")

        # Start the Prometheus server
        success = self.exporter.start()
        if not success:
            print(f"❌ Failed to start metrics server on port {self.port}")
            return False

        self.running = True
        print(f"✅ Metrics server running at http://localhost:{self.port}/metrics")
        print(f"📊 Prometheus scraping target: host.docker.internal:{self.port}")

        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

        return True

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        print(f"\n🛑 Received signal {signum}, shutting down...")
        self.running = False

    async def run_forever(self):
        """Keep the server running."""
        try:
            while self.running:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            print("\n🛑 Keyboard interrupt received, shutting down...")
        finally:
            await self.shutdown()

    async def shutdown(self):
        """Clean shutdown."""
        print("🔄 Shutting down metrics server...")
        self.exporter.stop()
        print("✅ Metrics server stopped")


async def main():
    """Main entry point."""
    server = PersistentMetricsServer()

    success = await server.start()
    if not success:
        sys.exit(1)

    print("\n" + "="*60)
    print("  TTA.dev Metrics Server Running")
    print("="*60)
    print(f"📊 Metrics endpoint: http://localhost:9464/metrics")
    print(f"🔍 Prometheus target: host.docker.internal:9464")
    print(f"📈 Grafana dashboards: http://localhost:3000")
    print("\nPress Ctrl+C to stop")
    print("="*60)

    await server.run_forever()


if __name__ == "__main__":
    asyncio.run(main())
