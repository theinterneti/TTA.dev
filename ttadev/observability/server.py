"""Observability Server - Serves dashboard and provides WebSocket/HTTP APIs."""

import asyncio
import json
from pathlib import Path
from typing import Any

from aiohttp import web
from ttadev.observability.collector import TraceCollector
from ttadev.observability.cgc_integration import CGCIntegration


class ObservabilityServer:
    """Production-grade observability server with WebSocket support."""
    
    def __init__(self, collector: TraceCollector | None = None, port: int = 8000):
        """Initialize server.
        
        Args:
            collector: TraceCollector instance (creates new if None)
            port: Port to listen on
        """
        self.collector = collector or TraceCollector()
        self.cgc = CGCIntegration()
        self.port = port
        self.app = web.Application()
        self.runner: web.AppRunner | None = None
        self.site: web.TCPSite | None = None
        self._websockets: set[web.WebSocketResponse] = set()
        
        # Setup routes
        self.app.router.add_get("/", self._handle_dashboard)
        self.app.router.add_get("/api/traces", self._handle_api_traces)
        self.app.router.add_get("/api/cgc/stats", self._handle_cgc_stats)
        self.app.router.add_get("/api/cgc/primitives", self._handle_cgc_primitives)
        self.app.router.add_get("/api/cgc/agents", self._handle_cgc_agents)
        self.app.router.add_get("/api/cgc/workflows", self._handle_cgc_workflows)
        self.app.router.add_get("/ws", self._handle_websocket)
    
    async def start(self) -> None:
        """Start the server."""
        self.runner = web.AppRunner(self.app)
        await self.runner.setup()
        self.site = web.TCPSite(self.runner, "0.0.0.0", self.port)
        await self.site.start()
        
        # Start broadcast task
        asyncio.create_task(self._broadcast_loop())
    
    async def stop(self) -> None:
        """Stop the server."""
        # Close all websockets
        for ws in list(self._websockets):
            await ws.close()
        
        if self.site:
            await self.site.stop()
        if self.runner:
            await self.runner.cleanup()
    
    async def _handle_dashboard(self, request: web.Request) -> web.Response:
        """Serve dashboard HTML."""
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>TTA.dev Observability</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                h1 { color: #333; }
                .status { padding: 10px; margin: 10px 0; border-radius: 5px; }
                .connected { background: #d4edda; color: #155724; }
                .disconnected { background: #f8d7da; color: #721c24; }
                #traces { margin-top: 20px; }
                .trace { padding: 10px; margin: 5px 0; background: #f0f0f0; border-radius: 3px; }
            </style>
        </head>
        <body>
            <h1>TTA.dev Observability Dashboard</h1>
            <div id="status" class="status disconnected">Disconnected</div>
            <div id="traces"></div>
            <script>
                const ws = new WebSocket(`ws://${window.location.host}/ws`);
                const statusEl = document.getElementById('status');
                const tracesEl = document.getElementById('traces');
                
                ws.onopen = () => {
                    statusEl.textContent = 'Connected';
                    statusEl.className = 'status connected';
                };
                
                ws.onclose = () => {
                    statusEl.textContent = 'Disconnected';
                    statusEl.className = 'status disconnected';
                };
                
                ws.onmessage = (event) => {
                    const data = JSON.parse(event.data);
                    if (data.type === 'new_trace') {
                        const div = document.createElement('div');
                        div.className = 'trace';
                        div.textContent = `Trace ${data.trace.trace_id}: ${data.trace.spans.length} spans`;
                        tracesEl.insertBefore(div, tracesEl.firstChild);
                    }
                };
            </script>
        </body>
        </html>
        """
        return web.Response(text=html, content_type="text/html")
    
    async def _handle_api_traces(self, request: web.Request) -> web.Response:
        """API endpoint to get all traces."""
        traces = self.collector.get_all_traces()
        return web.json_response({"traces": traces})
    
    async def _handle_cgc_stats(self, request: web.Request) -> web.Response:
        """API endpoint for CGC repository statistics."""
        try:
            stats = await self.cgc.get_repository_stats()
            return web.json_response(stats)
        except Exception as e:
            return web.json_response({"error": str(e)}, status=500)
    
    async def _handle_cgc_primitives(self, request: web.Request) -> web.Response:
        """API endpoint for CGC primitives graph."""
        try:
            graph = await self.cgc.get_primitives_graph()
            return web.json_response(graph)
        except Exception as e:
            return web.json_response({"error": str(e)}, status=500)
    
    async def _handle_cgc_agents(self, request: web.Request) -> web.Response:
        """API endpoint for CGC agent files."""
        try:
            agents = await self.cgc.get_agent_files()
            return web.json_response({"agents": agents})
        except Exception as e:
            return web.json_response({"error": str(e)}, status=500)
    
    async def _handle_cgc_workflows(self, request: web.Request) -> web.Response:
        """API endpoint for CGC workflow files."""
        try:
            workflows = await self.cgc.get_workflow_files()
            return web.json_response({"workflows": workflows})
        except Exception as e:
            return web.json_response({"error": str(e)}, status=500)
    
    async def _handle_websocket(self, request: web.Request) -> web.WebSocketResponse:
        """Handle WebSocket connections."""
        ws = web.WebSocketResponse()
        await ws.prepare(request)
        
        self._websockets.add(ws)
        
        # Send initial state
        await ws.send_json({
            "type": "initial_state",
            "traces": self.collector.get_all_traces()
        })
        
        try:
            async for msg in ws:
                pass  # Just keep connection alive
        finally:
            self._websockets.discard(ws)
        
        return ws
    
    async def _broadcast_loop(self) -> None:
        """Broadcast new traces to all connected WebSocket clients."""
        queue = self.collector.subscribe()
        
        try:
            while True:
                message = await queue.get()
                
                # Broadcast to all connected clients
                for ws in list(self._websockets):
                    try:
                        await ws.send_json(message)
                    except Exception:
                        self._websockets.discard(ws)
        except asyncio.CancelledError:
            self.collector.unsubscribe(queue)
            raise
