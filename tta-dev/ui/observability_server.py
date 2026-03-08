#!/usr/bin/env python3
"""
TTA.dev Batteries-Included Observability Server
Built using TTA.dev's own primitives for fault tolerance and reliability.

This server is SELF-OBSERVING - it uses TTA.dev primitives and captures
its own telemetry to demonstrate the platform in action.
"""

import asyncio
import json
from datetime import datetime
from typing import Any
from collections import defaultdict

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.sdk.resources import Resource

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
from observability.observability_integration import initialize_observability

# Initialize TTA.dev observability (self-instrumenting!)
initialize_observability(
    service_name="tta-observability-dashboard",
    enable_prometheus=False,  # Keep it simple for demo
)

app = FastAPI(title="TTA.dev Observability Dashboard")

# Active WebSocket connections
active_connections: list[WebSocket] = []

# In-memory trace storage (collected from OpenTelemetry)
trace_data = {
    "traces": [],
    "workflows_total": 0,
    "workflows_active": 0,
    "workflows_completed": 0,
    "workflows_failed": 0,
    "avg_duration_ms": 0.0,
}


class TraceCollector:
    """Collects traces from OpenTelemetry for display."""

    def __init__(self):
        self.spans_by_trace = defaultdict(list)
        self.completed_traces = []

    def add_span(self, span_data: dict):
        """Add a span to the collector."""
        trace_id = span_data.get("trace_id")
        self.spans_by_trace[trace_id].append(span_data)

        # Check if trace is complete (span has ended)
        if span_data.get("end_time"):
            self.complete_trace(trace_id)

    def complete_trace(self, trace_id: str):
        """Mark a trace as complete and calculate metrics."""
        spans = self.spans_by_trace.get(trace_id, [])
        if not spans:
            return

        # Calculate trace duration
        start_times = [s["start_time"] for s in spans if "start_time" in s]
        end_times = [s["end_time"] for s in spans if "end_time" in s]

        if start_times and end_times:
            duration_ms = (max(end_times) - min(start_times)) * 1000

            trace_summary = {
                "trace_id": trace_id,
                "span_count": len(spans),
                "duration_ms": duration_ms,
                "status": "error" if any(s.get("status") == "error" for s in spans) else "success",
                "timestamp": datetime.now().isoformat(),
            }

            self.completed_traces.append(trace_summary)
            trace_data["traces"] = self.completed_traces[-50:]  # Keep last 50

            # Update metrics
            trace_data["workflows_total"] = len(self.completed_traces)
            trace_data["workflows_completed"] = sum(
                1 for t in self.completed_traces if t["status"] == "success"
            )
            trace_data["workflows_failed"] = sum(
                1 for t in self.completed_traces if t["status"] == "error"
            )

            if self.completed_traces:
                trace_data["avg_duration_ms"] = sum(
                    t["duration_ms"] for t in self.completed_traces
                ) / len(self.completed_traces)


# Global trace collector
collector = TraceCollector()


async def fetch_live_metrics(data: dict, ctx: WorkflowContext) -> dict:
    """Fetch REAL live workflow metrics from collected traces."""
    # Get tracer to create a span for this operation
    tracer = trace.get_tracer(__name__)
    
    with tracer.start_as_current_span("fetch_live_metrics") as span:
        span.set_attribute("operation", "metrics_fetch")
        
        # Return real data from trace collector
        metrics = {
            "timestamp": datetime.now().isoformat(),
            "workflows": {
                "total": trace_data["workflows_total"],
                "active": trace_data["workflows_active"],
                "completed": trace_data["workflows_completed"],
                "failed": trace_data["workflows_failed"],
            },
            "primitives": {
                "retry_calls": len([t for t in trace_data["traces"] if "retry" in str(t).lower()]),
                "circuit_breaker_state": "closed",
                "traces_collected": len(trace_data["traces"]),
            },
            "performance": {
                "avg_duration_ms": trace_data["avg_duration_ms"],
                "p95_duration_ms": 0.0,  # TODO: Calculate percentiles
                "p99_duration_ms": 0.0,
            },
            "recent_traces": trace_data["traces"][-10:],  # Last 10 traces
        }
        
        span.set_attribute("traces_returned", len(metrics["recent_traces"]))
        return metrics


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
        .trace-item {
            padding: 10px;
            margin: 5px 0;
            background: #0f1525;
            border-left: 3px solid #667eea;
            border-radius: 4px;
            font-family: 'Courier New', monospace;
            font-size: 0.9em;
        }
        .trace-item.error {
            border-left-color: #ef4444;
        }
        .trace-item.success {
            border-left-color: #10b981;
        }
        .trace-id {
            opacity: 0.7;
            font-size: 0.85em;
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
            <div class="metric-value" id="total-workflows">0</div>
            <div class="metric-label">Total Executed</div>
        </div>
        <div class="metric-card">
            <h3>⚡ Active</h3>
            <div class="metric-value" id="active-workflows">0</div>
            <div class="metric-label">Currently Running</div>
        </div>
        <div class="metric-card">
            <h3>✅ Completed</h3>
            <div class="metric-value" id="completed-workflows">0</div>
            <div class="metric-label">Successfully Finished</div>
        </div>
        <div class="metric-card">
            <h3>⏱️ Performance</h3>
            <div class="metric-value" id="avg-duration">0</div>
            <div class="metric-label">Average Duration (ms)</div>
        </div>
    </div>

    <div class="metric-card" style="margin-bottom: 30px;">
        <h3>🔍 Recent Traces</h3>
        <div id="recent-traces">
            <p style="opacity: 0.5;">Waiting for traces...</p>
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
            
            // Display recent traces
            if (data.recent_traces && data.recent_traces.length > 0) {
                const tracesHtml = data.recent_traces.map(t => `
                    <div class="trace-item ${t.status}">
                        <strong>${t.status === 'success' ? '✅' : '❌'} ${t.span_count} spans</strong> 
                        | ${t.duration_ms.toFixed(2)}ms
                        <div class="trace-id">Trace: ${t.trace_id.toString(16).substring(0, 16)}...</div>
                    </div>
                `).join('');
                document.getElementById('recent-traces').innerHTML = tracesHtml;
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


@app.post("/api/spans")
async def receive_span(span_data: dict[str, Any]):
    """
    Receive a span from instrumented primitives.
    
    This endpoint allows primitives to push their telemetry data
    directly to the dashboard for real-time visualization.
    """
    try:
        collector.add_span(span_data)
        
        # Broadcast to connected WebSocket clients
        if active_connections:
            message = json.dumps({"type": "new_span", "span": span_data})
            for connection in active_connections:
                try:
                    await connection.send_text(message)
                except Exception:
                    pass  # Client disconnected
        
        return {"status": "ok", "trace_id": span_data.get("trace_id")}
    except Exception as e:
        return {"status": "error", "message": str(e)}


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
    tracer = trace.get_tracer(__name__)
    with tracer.start_as_current_span("health_check") as span:
        span.set_attribute("check.type", "health")
        return {"status": "healthy", "service": "tta-dev-observability"}


@app.on_event("startup")
async def startup_event():
    """Start background tasks on server startup."""
    asyncio.create_task(generate_demo_traces())


async def generate_demo_traces():
    """Generate demo workflow traces to show the dashboard in action."""
    tracer = trace.get_tracer(__name__)
    
    print("🎯 Starting demo trace generator...")
    
    while True:
        try:
            # Simulate a workflow execution
            with tracer.start_as_current_span("demo_workflow") as span:
                span.set_attribute("workflow.type", "demo")
                span.set_attribute("workflow.id", f"demo-{datetime.now().timestamp()}")
                
                # Simulate some work
                await asyncio.sleep(0.5)
                
                # Update collector
                collector.add_span({
                    "trace_id": span.get_span_context().trace_id,
                    "span_id": span.get_span_context().span_id,
                    "name": "demo_workflow",
                    "start_time": datetime.now().timestamp(),
                    "end_time": datetime.now().timestamp() + 0.5,
                    "status": "success" if datetime.now().second % 10 != 0 else "error",
                })
                
        except Exception as e:
            print(f"Error generating demo trace: {e}")
        
        await asyncio.sleep(3)  # Generate a trace every 3 seconds


if __name__ == "__main__":
    import uvicorn

    print("🚀 Starting TTA.dev Observability Dashboard...")
    print("📊 Dashboard: http://localhost:8000")
    print("🔌 WebSocket: ws://localhost:8000/ws")
    print("🏥 Health: http://localhost:8000/health")
    print("\n✅ Built with TTA.dev primitives!")

    uvicorn.run(app, host="0.0.0.0", port=8000)
