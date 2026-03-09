#!/usr/bin/env python3
"""
TTA.dev Batteries-Included Observability Server
Built using TTA.dev's own primitives for fault tolerance and reliability.

This server is SELF-OBSERVING - it uses TTA.dev primitives and captures
its own telemetry to demonstrate the platform in action.
"""

import asyncio
import json

# Import TTA.dev primitives
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from opentelemetry import trace

sys.path.insert(0, str(Path(__file__).parent.parent))

from observability.observability_integration import initialize_observability
from primitives.core import LambdaPrimitive, WorkflowContext
from primitives.recovery.circuit_breaker_primitive import (
    CircuitBreakerConfig,
    CircuitBreakerPrimitive,
)
from primitives.recovery.retry import RetryPrimitive, RetryStrategy

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


def load_traces_from_db():
    """Load existing traces from SQLite database."""
    import sqlite3

    db_path = Path(".tta/traces.db")
    if not db_path.exists():
        print("ℹ️  No database found, starting fresh")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Load all spans
    cursor.execute("""
        SELECT trace_id, span_name, primitive_type, start_time, end_time, 
               duration_ms, status, attributes
        FROM spans
        ORDER BY start_time DESC
        LIMIT 100
    """)

    rows = cursor.fetchall()
    print(f"📊 Loading {len(rows)} spans from database...")

    for row in rows:
        span_data = {
            "trace_id": row[0],
            "name": row[1],
            "primitive_type": row[2],
            "start_time": row[3],
            "end_time": row[4],
            "duration_ms": row[5],
            "status": row[6],
            "attributes": json.loads(row[7]) if row[7] else {},
        }
        collector.add_span(span_data)

    conn.close()
    print(f"✓ Loaded {len(collector.completed_traces)} traces from database")


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
    """Serve the enhanced observability dashboard."""
    dashboard_path = Path(__file__).parent / "dashboard.html"
    return HTMLResponse(
        content=dashboard_path.read_text(),
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
    # Load historical data from database
    await load_historical_data()
    # Start demo trace generator
    asyncio.create_task(generate_demo_traces())


async def load_historical_data():
    """Load historical traces from persistent storage on startup."""
    try:
        from observability.collector import trace_collector

        print("📊 Loading historical traces from database...")
        recent_spans = trace_collector.get_recent_spans(limit=100)

        if recent_spans:
            print(f"✅ Loaded {len(recent_spans)} historical spans")
            # Group spans by trace_id
            traces_by_id = defaultdict(list)
            for span in recent_spans:
                traces_by_id[span.get("trace_id", "default")].append(span)

            # Convert to trace format
            for trace_id, spans in traces_by_id.items():
                trace_start = min(s["start_time"] for s in spans)
                trace_end = max(s["end_time"] for s in spans)
                duration = (trace_end - trace_start) * 1000

                has_error = any(s.get("status") == "error" for s in spans)

                trace_collector_instance.completed_traces.append(
                    {
                        "trace_id": trace_id,
                        "start_time": trace_start,
                        "end_time": trace_end,
                        "duration_ms": duration,
                        "status": "error" if has_error else "ok",
                        "spans": spans,
                    }
                )

            print(f"✅ Reconstructed {len(traces_by_id)} historical traces")
        else:
            print("ℹ️  No historical data found - starting fresh")

    except Exception as e:
        print(f"⚠️  Failed to load historical data: {e}")
        print("   Continuing with empty state...")


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
                collector.add_span(
                    {
                        "trace_id": span.get_span_context().trace_id,
                        "span_id": span.get_span_context().span_id,
                        "name": "demo_workflow",
                        "start_time": datetime.now().timestamp(),
                        "end_time": datetime.now().timestamp() + 0.5,
                        "status": "success" if datetime.now().second % 10 != 0 else "error",
                    }
                )

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

    # Load existing traces from database
    load_traces_from_db()

    uvicorn.run(app, host="0.0.0.0", port=8000)
