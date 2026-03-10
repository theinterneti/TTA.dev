"""WebSocket handler for real-time trace streaming."""

import asyncio
import json
import logging
from pathlib import Path
from typing import Set
from websockets.server import WebSocketServerProtocol

logger = logging.getLogger(__name__)


class TraceStreamer:
    """Streams trace data to connected WebSocket clients in real-time."""
    
    def __init__(self, trace_dir: Path):
        self.trace_dir = trace_dir
        self.clients: Set[WebSocketServerProtocol] = set()
        self._running = False
        
    async def register_client(self, websocket: WebSocketServerProtocol):
        """Register a new WebSocket client."""
        self.clients.add(websocket)
        logger.info(f"Client connected. Total clients: {len(self.clients)}")
        
        # Send initial trace data
        await self._send_initial_traces(websocket)
        
    async def unregister_client(self, websocket: WebSocketServerProtocol):
        """Unregister a WebSocket client."""
        self.clients.discard(websocket)
        logger.info(f"Client disconnected. Total clients: {len(self.clients)}")
        
    async def _send_initial_traces(self, websocket: WebSocketServerProtocol):
        """Send existing traces to newly connected client."""
        try:
            trace_files = sorted(self.trace_dir.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
            traces = []
            
            for trace_file in trace_files[:50]:  # Send last 50 traces
                try:
                    trace_data = json.loads(trace_file.read_text())
                    traces.append(trace_data)
                except Exception as e:
                    logger.error(f"Failed to load trace {trace_file}: {e}")
                    
            if traces:
                await websocket.send(json.dumps({
                    "type": "initial_traces",
                    "traces": traces
                }))
        except Exception as e:
            logger.error(f"Failed to send initial traces: {e}")
            
    async def broadcast_trace(self, trace_data: dict):
        """Broadcast a new trace to all connected clients."""
        if not self.clients:
            return
            
        message = json.dumps({
            "type": "new_trace",
            "trace": trace_data
        })
        
        # Send to all clients, removing disconnected ones
        disconnected = set()
        for client in self.clients:
            try:
                await client.send(message)
            except Exception as e:
                logger.error(f"Failed to send to client: {e}")
                disconnected.add(client)
                
        # Clean up disconnected clients
        self.clients -= disconnected
        
    async def watch_traces(self):
        """Watch for new trace files and broadcast them."""
        self._running = True
        seen_files = set(self.trace_dir.glob("*.json"))
        
        logger.info("Started watching for new traces...")
        
        while self._running:
            try:
                # Check for new files
                current_files = set(self.trace_dir.glob("*.json"))
                new_files = current_files - seen_files
                
                for trace_file in new_files:
                    try:
                        trace_data = json.loads(trace_file.read_text())
                        await self.broadcast_trace(trace_data)
                        logger.info(f"Broadcasted new trace: {trace_data.get('trace_id', 'unknown')}")
                    except Exception as e:
                        logger.error(f"Failed to broadcast trace {trace_file}: {e}")
                        
                seen_files = current_files
                await asyncio.sleep(0.5)  # Check every 500ms
                
            except Exception as e:
                logger.error(f"Error in trace watcher: {e}")
                await asyncio.sleep(1)
                
    def stop(self):
        """Stop watching for traces."""
        self._running = False
