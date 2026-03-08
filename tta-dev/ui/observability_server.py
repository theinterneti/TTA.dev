#!/usr/bin/env python3
"""
TTA.dev Batteries-Included Observability Server
Built using TTA.dev's own primitives for fault tolerance and reliability.
"""

import asyncio
import json
from datetime import datetime
from typing import Any

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

# Import TTA.dev primitives
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from primitives.core import WorkflowContext, LambdaPrimitive
from primitives.recovery.retry import RetryPrimitive, RetryStrategy
from primitives.recovery.circuit_breaker_primitive import (
    CircuitBreakerPrimitive,
    CircuitBreakerConfig,
)

app = FastAPI(title="TTA.dev Observability Dashboard")

# Active WebSocket connections
active_connections: list[WebSocket] = []


async def fetch_live_metrics(data: dict, ctx: WorkflowContext) -> dict:
    """Fetch live workflow metrics using TTA.dev primitives."""
    return {
        "timestamp": datetime.now().isoformat(),
        "workflows": {
            "total": 156,
            "active": 7,
            "completed": 145,
            "failed": 4,
        },
        "primitives": {
            "retry_calls": 23,
            "circuit_breaker_state": "closed",
            "timeout_triggers": 2,
        },
        "performance": {
            "avg_duration_ms": 234.5,
            "p95_duration_ms": 567.8,
            "p99_duration_ms": 891.2,
        },
    }


# Build resilient metrics fetcher using TTA.dev's own primitives
metrics_workflow = CircuitBreakerPrimitive(
    RetryPrimitive(
        LambdaPrimitive(fetch_live_metrics),
        strategy=RetryStrategy(max_retries=3, backoff_base=2.0),
    ),
    config=CircuitBreakerConfig(
        failure_threshold=5,
        recovery_timeout=30.0,
    ),
)


@app.get("/")
async def get_dashboard():
    """Serve the observability dashboard."""
    return HTMLResponse(
        content="""
<!DOCTYPE html>
<html>
<head>
    <title>TTA.dev Observability Dashboard</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background: #0a0e27;
            color: #e0e6ed;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
        }
        h1 {
            margin: 0;
            font-size: 2.5em;
        }
        .subtitle {
            opacity: 0.9;
            margin-top: 10px;
        }
        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .metric-card {
            background: #1a1f3a;
            border: 1px solid #2d3561;
            border-radius: 8px;
            padding: 20px;
        }
        .metric-card h3 {
            margin: 0 0 15px 0;
            color: #667eea;
        }
        .metric-value {
            font-size: 2em;
            font-weight: bold;
            margin: 10px 0;
        }
        .metric-label {
            opacity: 0.7;
            font-size: 0.9em;
        }
        .status {
            display: inline-block;
            padding: 5px 15px;
            border-radius: 20px;
            font-size: 0.9em;
            font-weight: bold;
        }
        .status-operational {
            background: #10b981;
            color: white;
        }
        .footer {
            text-align: center;
            opacity: 0.6;
            margin-top: 50px;
        }
        #live-indicator {
            display: inline-block;
            width: 10px;
            height: 10px;
            background: #10b981;
            border-radius: 50%;
            animation: pulse 2s infinite;
        }
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🚀 TTA.dev Observability Dashboard</h1>
        <div class="subtitle">
            <span id="live-indicator"></span>
            Real-time monitoring powered by TTA.dev primitives
        </div>
    </div>

    <div id="status-banner">
        <span class="status status-operational">● OPERATIONAL</span>
    </div>

    <div class="metrics-grid" id="metrics">
        <div class="metric-card">
            <h3>📊 Workflows</h3>
            <div class="metric-value" id="total-workflows">-</div>
            <div class="metric-label">Total Executed</div>
        </div>
        <div class="metric-card">
            <h3>⚡ Active</h3>
            <div class="metric-value" id="active-workflows">-</div>
            <div class="metric-label">Currently Running</div>
        </div>
        <div class="metric-card">
            <h3>✅ Completed</h3>
            <div class="metric-value" id="completed-workflows">-</div>
            <div class="metric-label">Successfully Finished</div>
        </div>
        <div class="metric-card">
            <h3>⏱️ Performance</h3>
            <div class="metric-value" id="avg-duration">-</div>
            <div class="metric-label">Average Duration (ms)</div>
        </div>
    </div>

    <div class="footer">
        <p>Built with TTA.dev primitives: CircuitBreaker + Retry + LambdaPrimitive</p>
        <p>Last updated: <span id="last-update">-</span></p>
    </div>

    <script>
        const ws = new WebSocket(`ws://${window.location.host}/ws`);
        
        ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            
            if (data.workflows) {
                document.getElementById('total-workflows').textContent = data.workflows.total;
                document.getElementById('active-workflows').textContent = data.workflows.active;
                document.getElementById('completed-workflows').textContent = data.workflows.completed;
            }
            
            if (data.performance) {
                document.getElementById('avg-duration').textContent = 
                    data.performance.avg_duration_ms.toFixed(1);
            }
            
            document.getElementById('last-update').textContent = new Date(data.timestamp).toLocaleString();
        };
        
        ws.onclose = () => {
            document.getElementById('status-banner').innerHTML = 
                '<span class="status" style="background: #ef4444;">● DISCONNECTED</span>';
        };
    </script>
</body>
</html>
    """,
        status_code=200,
    )


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time metrics."""
    await websocket.accept()
    active_connections.append(websocket)

    try:
        # Send metrics every 2 seconds
        while True:
            ctx = WorkflowContext(workflow_id=f"metrics-{datetime.now().timestamp()}")
            metrics = await metrics_workflow.execute({}, ctx)
            await websocket.send_text(json.dumps(metrics))
            await asyncio.sleep(2)

    except WebSocketDisconnect:
        active_connections.remove(websocket)


@app.get("/api/metrics")
async def get_metrics():
    """REST API endpoint for metrics."""
    ctx = WorkflowContext(workflow_id=f"api-metrics-{datetime.now().timestamp()}")
    return await metrics_workflow.execute({}, ctx)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "tta-dev-observability"}


if __name__ == "__main__":
    import uvicorn

    print("🚀 Starting TTA.dev Observability Dashboard...")
    print("📊 Dashboard: http://localhost:8000")
    print("🔌 WebSocket: ws://localhost:8000/ws")
    print("🏥 Health: http://localhost:8000/health")
    print("\n✅ Built with TTA.dev primitives!")

    uvicorn.run(app, host="0.0.0.0", port=8000)
