"""FastAPI REST API for TTA Observability UI."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from .collector import TraceCollector
from .models import MetricRecord, MetricsSummary, TraceListResponse
from .storage import TraceStorage

logger = logging.getLogger(__name__)

# Get path to UI directory
UI_DIR = Path(__file__).parent.parent.parent / "ui"


# Request/Response Models
class OTLPTraceRequest(BaseModel):
    """OTLP trace data."""

    resourceSpans: list[dict[str, Any]]


class WebSocketManager:
    """Manages WebSocket connections for real-time updates."""

    def __init__(self):
        """Initialize WebSocket manager."""
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket) -> None:
        """Accept new WebSocket connection."""
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(
            "WebSocket client connected", extra={"count": len(self.active_connections)}
        )

    def disconnect(self, websocket: WebSocket) -> None:
        """Remove WebSocket connection."""
        self.active_connections.remove(websocket)
        logger.info(
            "WebSocket client disconnected",
            extra={"count": len(self.active_connections)},
        )

    async def broadcast(self, message: dict[str, Any]) -> None:
        """Broadcast message to all connected clients."""
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                logger.exception("Error broadcasting to WebSocket client")
                self.disconnect(connection)


# Global state
storage: TraceStorage | None = None
collector: TraceCollector | None = None
ws_manager = WebSocketManager()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    global storage, collector

    # Startup
    logger.info("Starting TTA Observability UI service")
    storage = TraceStorage()
    await storage.initialize()
    collector = TraceCollector(storage)
    logger.info("Service started successfully")

    yield

    # Shutdown
    logger.info("Shutting down TTA Observability UI service")
    if collector:
        await collector.finalize_traces()
    logger.info("Service shutdown complete")


# Create FastAPI app
app = FastAPI(
    title="TTA Observability UI",
    description="Lightweight observability for TTA.dev workflows",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Health check
@app.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy", "service": "tta-observability-ui"}


# OTLP Endpoint
@app.post("/v1/traces")
async def receive_otlp_traces(request: OTLPTraceRequest) -> dict[str, str]:
    """
    Receive OTLP trace data from OpenTelemetry SDK.

    This endpoint is compatible with the OTLP/HTTP protocol.
    """
    if not collector:
        raise HTTPException(status_code=503, detail="Collector not initialized")

    try:
        # Process OTLP data
        await collector.collect_otlp_trace(request.dict())

        # Broadcast update to WebSocket clients
        await ws_manager.broadcast({"type": "trace_update", "status": "new_trace"})

        return {"status": "success"}
    except Exception as e:
        logger.exception("Error processing OTLP trace")
        raise HTTPException(status_code=500, detail=str(e)) from e


# Trace Endpoints
@app.get("/api/traces", response_model=TraceListResponse)
async def list_traces(
    limit: int = 100,
    offset: int = 0,
    status: str | None = None,
) -> TraceListResponse:
    """List recent traces with pagination."""
    if not storage:
        raise HTTPException(status_code=503, detail="Storage not initialized")

    try:
        traces = await storage.list_traces(limit=limit, offset=offset, status=status)
        total = len(traces)  # TODO: Add count query to storage

        return TraceListResponse(
            traces=traces,
            total=total,
            limit=limit,
            offset=offset,
        )
    except Exception as e:
        logger.exception("Error listing traces")
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.get("/api/traces/{trace_id}")
async def get_trace(trace_id: str) -> dict[str, Any]:
    """Get detailed trace by ID."""
    if not storage:
        raise HTTPException(status_code=503, detail="Storage not initialized")

    try:
        trace = await storage.get_trace(trace_id)
        if not trace:
            raise HTTPException(status_code=404, detail="Trace not found")

        return trace.dict()
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error getting trace")
        raise HTTPException(status_code=500, detail=str(e)) from e


# Metrics Endpoints
@app.get("/api/metrics/summary", response_model=MetricsSummary)
async def get_metrics_summary() -> MetricsSummary:
    """Get aggregated metrics summary."""
    if not storage:
        raise HTTPException(status_code=503, detail="Storage not initialized")

    try:
        stats = await storage.get_stats()

        return MetricsSummary(
            total_traces=stats["total_traces"],
            success_rate=stats["success_rate"],
            avg_duration_ms=stats["avg_duration_ms"],
            error_rate=1.0 - stats["success_rate"],
            primitive_usage=stats["primitive_usage"],
        )
    except Exception as e:
        logger.exception("Error getting metrics summary")
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.post("/api/metrics")
async def record_metric(metric: MetricRecord) -> dict[str, str]:
    """Record a custom metric."""
    if not storage:
        raise HTTPException(status_code=503, detail="Storage not initialized")

    try:
        await storage.save_metric(metric)
        return {"status": "success"}
    except Exception as e:
        logger.exception("Error recording metric")
        raise HTTPException(status_code=500, detail=str(e)) from e


# Primitives Stats Endpoint
@app.get("/api/primitives/stats")
async def get_primitives_stats() -> dict[str, Any]:
    """Get statistics for each primitive type."""
    if not storage:
        raise HTTPException(status_code=503, detail="Storage not initialized")

    try:
        stats = await storage.get_stats()
        return {
            "primitive_usage": stats["primitive_usage"],
            "total_calls": sum(stats["primitive_usage"].values()),
        }
    except Exception as e:
        logger.exception("Error getting primitive stats")
        raise HTTPException(status_code=500, detail=str(e)) from e


# WebSocket Endpoint
@app.websocket("/ws/traces")
async def websocket_endpoint(websocket: WebSocket) -> None:
    """WebSocket endpoint for real-time trace updates."""
    await ws_manager.connect(websocket)

    try:
        while True:
            # Keep connection alive and listen for client messages
            data = await websocket.receive_text()
            # Echo back for now (can add commands later)
            await websocket.send_json({"type": "pong", "message": data})
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)


# Static Files & UI
@app.get("/", response_class=HTMLResponse)
async def root() -> HTMLResponse:
    """Serve the main UI dashboard."""
    index_path = UI_DIR / "index.html"
    if not index_path.exists():
        # Fallback to basic status page if UI not found
        return HTMLResponse(content=_get_fallback_html(), status_code=200)

    with open(index_path) as f:
        return HTMLResponse(content=f.read(), status_code=200)


@app.get("/app.css")
async def serve_css() -> HTMLResponse:
    """Serve CSS file."""
    css_path = UI_DIR / "app.css"
    if css_path.exists():
        with open(css_path) as f:
            return HTMLResponse(content=f.read(), media_type="text/css")
    return HTMLResponse(content="", status_code=404)


@app.get("/app.js")
async def serve_js() -> HTMLResponse:
    """Serve JavaScript file."""
    js_path = UI_DIR / "app.js"
    if js_path.exists():
        with open(js_path) as f:
            return HTMLResponse(content=f.read(), media_type="application/javascript")
    return HTMLResponse(content="", status_code=404)


def _get_fallback_html() -> str:
    """Generate fallback HTML when UI files are not found."""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>TTA Observability UI</title>
        <style>
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                margin: 0;
                padding: 20px;
                background: #1e1e1e;
                color: #d4d4d4;
            }
            .container {
                max-width: 1200px;
                margin: 0 auto;
            }
            h1 {
                color: #4ec9b0;
            }
            .status {
                background: #264f78;
                padding: 20px;
                border-radius: 8px;
                margin-bottom: 20px;
            }
            .card {
                background: #252526;
                padding: 15px;
                border-radius: 8px;
                margin-bottom: 10px;
            }
            .success { color: #4ec9b0; }
            .error { color: #f48771; }
            a {
                color: #4fc1ff;
                text-decoration: none;
            }
            a:hover {
                text-decoration: underline;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🔍 TTA Observability UI</h1>
            
            <div class="status">
                <h2>Service Status</h2>
                <p class="success">✅ Service is running</p>
                <p>📊 Collecting traces from TTA.dev workflows</p>
            </div>

            <div class="card">
                <h3>📖 API Endpoints</h3>
                <ul>
                    <li><a href="/api/traces">GET /api/traces</a> - List traces</li>
                    <li><a href="/api/metrics/summary">GET /api/metrics/summary</a> - Metrics summary</li>
                    <li><a href="/api/primitives/stats">GET /api/primitives/stats</a> - Primitive statistics</li>
                    <li><a href="/health">GET /health</a> - Health check</li>
                </ul>
            </div>

            <div class="card">
                <h3>🔌 Integration</h3>
                <p>Send traces to: <code>POST http://localhost:8765/v1/traces</code></p>
                <p>WebSocket: <code>ws://localhost:8765/ws/traces</code></p>
            </div>

            <div class="card">
                <h3>📚 Documentation</h3>
                <p>
                    Full documentation: 
                    <a href="/docs" target="_blank">FastAPI Docs</a> | 
                    <a href="/redoc" target="_blank">ReDoc</a>
                </p>
                <p>
                    See: <code>packages/tta-observability-ui/README.md</code>
                </p>
            </div>

            <div class="card">
                <h3>🎯 Next Steps</h3>
                <ol>
                    <li>Initialize observability in your app:
                        <pre style="background: #1e1e1e; padding: 10px; border-radius: 4px;">
from observability_integration import initialize_observability

initialize_observability(
    service_name="my-app",
    enable_tta_ui=True,
    tta_ui_endpoint="http://localhost:8765"
)</pre>
                    </li>
                    <li>Run your workflow with primitives</li>
                    <li>View traces in the API endpoints above</li>
                    <li>Coming soon: Interactive dashboard UI!</li>
                </ol>
            </div>
        </div>
    </body>
    </html>
    """


# Cleanup endpoint
@app.post("/api/cleanup")
async def cleanup_old_traces() -> dict[str, Any]:
    """Trigger cleanup of old traces."""
    if not storage:
        raise HTTPException(status_code=503, detail="Storage not initialized")

    try:
        deleted = await storage.cleanup_old_traces()
        return {"status": "success", "deleted_count": deleted}
    except Exception as e:
        logger.exception("Error cleaning up traces")
        raise HTTPException(status_code=500, detail=str(e)) from e
