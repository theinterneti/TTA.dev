"""Production observability server with WebSocket streaming."""

import asyncio
import json
import logging
from pathlib import Path

import aiohttp_cors
from aiohttp import web
from websockets.legacy.server import serve as websocket_serve

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Paths
BASE_DIR = Path(__file__).parent.parent.parent
TRACE_DIR = BASE_DIR / ".observability" / "traces"
UI_DIR = BASE_DIR / "ttadev" / "ui"

# Ensure trace directory exists
TRACE_DIR.mkdir(parents=True, exist_ok=True)

# WebSocket clients
ws_clients = set()


async def websocket_handler(websocket, path):
    """Handle WebSocket connections for real-time trace streaming."""
    ws_clients.add(websocket)
    logger.info(f"WebSocket client connected. Total: {len(ws_clients)}")

    try:
        # Send initial traces
        trace_files = sorted(
            TRACE_DIR.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True
        )
        traces = []
        for trace_file in trace_files[:50]:
            try:
                traces.append(json.loads(trace_file.read_text()))
            except Exception as e:
                logger.error(f"Failed to load {trace_file}: {e}")

        if traces:
            await websocket.send(json.dumps({"type": "initial_traces", "traces": traces}))

        # Keep connection alive
        async for message in websocket:
            # Echo or handle commands if needed
            pass

    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        ws_clients.discard(websocket)
        logger.info(f"WebSocket client disconnected. Total: {len(ws_clients)}")


async def broadcast_new_trace(trace_data):
    """Broadcast new trace to all connected WebSocket clients."""
    if not ws_clients:
        return

    message = json.dumps({"type": "new_trace", "trace": trace_data})
    disconnected = set()

    for client in ws_clients:
        try:
            await client.send(message)
        except Exception as e:
            logger.error(f"Failed to send to client: {e}")
            disconnected.add(client)

    ws_clients.difference_update(disconnected)


async def watch_traces():
    """Watch for new trace files and broadcast them."""
    seen_files = set(TRACE_DIR.glob("*.json"))
    logger.info("Started watching for new traces...")

    while True:
        try:
            current_files = set(TRACE_DIR.glob("*.json"))
            new_files = current_files - seen_files

            for trace_file in new_files:
                try:
                    trace_data = json.loads(trace_file.read_text())
                    await broadcast_new_trace(trace_data)
                    logger.info(f"Broadcasted: {trace_data.get('trace_id', 'unknown')}")
                except Exception as e:
                    logger.error(f"Failed to broadcast {trace_file}: {e}")

            seen_files = current_files
            await asyncio.sleep(0.5)
        except Exception as e:
            logger.error(f"Trace watcher error: {e}")
            await asyncio.sleep(1)


# HTTP handlers
async def serve_dashboard(request):
    """Serve the main dashboard HTML."""
    html_file = UI_DIR / "dashboard.html"
    return web.FileResponse(html_file)


async def get_traces(request):
    """Get all traces."""
    trace_files = sorted(TRACE_DIR.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    traces = []
    for trace_file in trace_files[:100]:
        try:
            traces.append(json.loads(trace_file.read_text()))
        except Exception as e:
            logger.error(f"Failed to load {trace_file}: {e}")
    return web.json_response(traces)


async def main():
    """Start HTTP and WebSocket servers."""
    # HTTP server
    app = web.Application()

    # Setup CORS
    cors = aiohttp_cors.setup(
        app,
        defaults={
            "*": aiohttp_cors.ResourceOptions(
                allow_credentials=True,
                expose_headers="*",
                allow_headers="*",
            )
        },
    )

    # Routes
    app.router.add_get("/", serve_dashboard)
    app.router.add_get("/api/traces", get_traces)
    app.router.add_static("/static", UI_DIR, show_index=False)

    # Apply CORS
    for route in list(app.router.routes()):
        cors.add(route)

    # Start HTTP server
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", 8000)
    await site.start()
    logger.info("HTTP server started on http://0.0.0.0:8000")

    # Start WebSocket server
    await websocket_serve(websocket_handler, "0.0.0.0", 8001)
    logger.info("WebSocket server started on ws://0.0.0.0:8001")

    # Start trace watcher
    asyncio.create_task(watch_traces())

    # Keep running
    await asyncio.Future()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server stopped")
