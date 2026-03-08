"""Batteries-included observability dashboard for TTA.dev.

This auto-starting web dashboard displays:
- Real-time workflow traces
- Primitive execution metrics
- Agent activity logs
- System health
"""

import asyncio
from datetime import datetime
from typing import Any

from aiohttp import web


class ObservabilityDashboard:
    """Auto-starting observability dashboard."""

    def __init__(self, host: str = "localhost", port: int = 8080):
        self.host = host
        self.port = port
        self.app = web.Application()
        self.traces: list[dict[str, Any]] = []
        self.metrics: dict[str, Any] = {
            "total_workflows": 0,
            "successful_workflows": 0,
            "failed_workflows": 0,
            "avg_duration_ms": 0.0,
        }
        self._setup_routes()

    def _setup_routes(self):
        """Setup HTTP routes."""
        self.app.router.add_get("/", self.handle_index)
        self.app.router.add_get("/api/traces", self.handle_traces)
        self.app.router.add_get("/api/metrics", self.handle_metrics)
        self.app.router.add_get("/api/health", self.handle_health)

    async def handle_index(self, request: web.Request) -> web.Response:
        """Serve the main dashboard HTML."""
        html = self._generate_dashboard_html()
        return web.Response(text=html, content_type="text/html")

    async def handle_traces(self, request: web.Request) -> web.Response:
        """Return recent traces as JSON."""
        return web.json_response({"traces": self.traces[-100:]})

    async def handle_metrics(self, request: web.Request) -> web.Response:
        """Return current metrics as JSON."""
        return web.json_response(self.metrics)

    async def handle_health(self, request: web.Request) -> web.Response:
        """Health check endpoint."""
        return web.json_response({"status": "healthy", "timestamp": datetime.utcnow().isoformat()})

    def _generate_dashboard_html(self) -> str:
        """Generate the dashboard HTML with embedded CSS and JS."""
        return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>TTA.dev Observability Dashboard</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: #0a0e27;
            color: #e0e6ed;
            padding: 20px;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 30px;
            border-radius: 12px;
            margin-bottom: 30px;
            box-shadow: 0 10px 30px rgba(102, 126, 234, 0.3);
        }
        .header h1 { font-size: 32px; margin-bottom: 10px; }
        .header p { opacity: 0.9; font-size: 16px; }
        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .metric-card {
            background: #1a1f3a;
            padding: 25px;
            border-radius: 12px;
            border-left: 4px solid #667eea;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
        }
        .metric-value { font-size: 36px; font-weight: bold; color: #667eea; margin: 10px 0; }
        .metric-label { color: #9ca3af; font-size: 14px; text-transform: uppercase; }
        .traces-section {
            background: #1a1f3a;
            padding: 30px;
            border-radius: 12px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
        }
        .traces-section h2 { margin-bottom: 20px; font-size: 24px; }
        .trace-item {
            background: #0f1629;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 15px;
            border-left: 4px solid #10b981;
        }
        .trace-item.error { border-left-color: #ef4444; }
        .trace-header { display: flex; justify-content: space-between; margin-bottom: 10px; }
        .trace-id { font-family: monospace; color: #667eea; font-weight: bold; }
        .trace-duration { color: #10b981; }
        .trace-status { padding: 4px 12px; border-radius: 12px; font-size: 12px; font-weight: bold; }
        .status-success { background: #10b98120; color: #10b981; }
        .status-error { background: #ef444420; color: #ef4444; }
        .empty-state {
            text-align: center;
            padding: 60px 20px;
            color: #6b7280;
        }
        .empty-state-icon { font-size: 64px; margin-bottom: 20px; opacity: 0.5; }
        @keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
        .fade-in { animation: fadeIn 0.3s ease-out; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🚀 TTA.dev Observability</h1>
        <p>Real-time monitoring for your AI-native workflows</p>
    </div>

    <div class="metrics-grid">
        <div class="metric-card fade-in">
            <div class="metric-label">Total Workflows</div>
            <div class="metric-value" id="total-workflows">0</div>
        </div>
        <div class="metric-card fade-in">
            <div class="metric-label">Successful</div>
            <div class="metric-value" id="successful-workflows">0</div>
        </div>
        <div class="metric-card fade-in">
            <div class="metric-label">Failed</div>
            <div class="metric-value" id="failed-workflows">0</div>
        </div>
        <div class="metric-card fade-in">
            <div class="metric-label">Avg Duration (ms)</div>
            <div class="metric-value" id="avg-duration">0</div>
        </div>
    </div>

    <div class="traces-section">
        <h2>Recent Traces</h2>
        <div id="traces-container">
            <div class="empty-state">
                <div class="empty-state-icon">📊</div>
                <p>No traces yet. Start using TTA.dev primitives to see data here!</p>
            </div>
        </div>
    </div>

    <script>
        async function fetchMetrics() {
            try {
                const response = await fetch('/api/metrics');
                const data = await response.json();
                document.getElementById('total-workflows').textContent = data.total_workflows;
                document.getElementById('successful-workflows').textContent = data.successful_workflows;
                document.getElementById('failed-workflows').textContent = data.failed_workflows;
                document.getElementById('avg-duration').textContent = data.avg_duration_ms.toFixed(2);
            } catch (error) {
                console.error('Failed to fetch metrics:', error);
            }
        }

        async function fetchTraces() {
            try {
                const response = await fetch('/api/traces');
                const data = await response.json();
                const container = document.getElementById('traces-container');

                if (data.traces.length === 0) {
                    return;
                }

                container.innerHTML = data.traces.map(trace => {
                    const statusClass = trace.status === 'error' ? 'error' : 'success';
                    const statusText = trace.status === 'error' ? 'ERROR' : 'SUCCESS';
                    return `
                        <div class="trace-item ${statusClass} fade-in">
                            <div class="trace-header">
                                <span class="trace-id">${trace.trace_id}</span>
                                <span class="trace-status status-${statusClass}">${statusText}</span>
                            </div>
                            <div class="trace-duration">⏱️ ${trace.duration_ms.toFixed(2)}ms</div>
                            <div style="margin-top: 10px; color: #9ca3af; font-size: 14px;">
                                ${new Date(trace.timestamp).toLocaleString()}
                            </div>
                        </div>
                    `;
                }).join('');
            } catch (error) {
                console.error('Failed to fetch traces:', error);
            }
        }

        // Refresh data every 2 seconds
        setInterval(async () => {
            await fetchMetrics();
            await fetchTraces();
        }, 2000);

        // Initial load
        fetchMetrics();
        fetchTraces();
    </script>
</body>
</html>"""

    async def start(self):
        """Start the dashboard server."""
        runner = web.AppRunner(self.app)
        await runner.setup()
        site = web.TCPSite(runner, self.host, self.port)
        await site.start()
        print(f"🚀 TTA.dev Observability Dashboard running at http://{self.host}:{self.port}")
        print("Press Ctrl+C to stop")

    def record_trace(self, trace_id: str, duration_ms: float, status: str = "success"):
        """Record a workflow trace."""
        self.traces.append(
            {
                "trace_id": trace_id,
                "duration_ms": duration_ms,
                "status": status,
                "timestamp": datetime.utcnow().isoformat(),
            }
        )

        # Update metrics
        self.metrics["total_workflows"] += 1
        if status == "success":
            self.metrics["successful_workflows"] += 1
        else:
            self.metrics["failed_workflows"] += 1

        # Update average duration
        total = sum(t["duration_ms"] for t in self.traces)
        self.metrics["avg_duration_ms"] = total / len(self.traces)


async def main():
    """Start the observability dashboard."""
    dashboard = ObservabilityDashboard()
    await dashboard.start()

    # Keep running
    try:
        await asyncio.Event().wait()
    except KeyboardInterrupt:
        print("\n👋 Shutting down dashboard...")


if __name__ == "__main__":
    asyncio.run(main())
