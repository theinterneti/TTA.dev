"""Enhanced observability server with provider/model/agent tracking."""
import json
import asyncio
from pathlib import Path
from aiohttp import web
import aiohttp
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from ttadev.observability.agent_tracker import get_tracker

# Dashboard HTML file
DASHBOARD_FILE = Path(__file__).parent / "dashboard.html"
TRACES_DIR = Path.home() / ".tta" / "traces"

# WebSocket connections
websocket_connections = set()


async def handle_dashboard(request):
    """Serve the dashboard HTML."""
    with open(DASHBOARD_FILE) as f:
        html = f.read()
    return web.Response(text=html, content_type="text/html")


async def handle_api_traces(request):
    """API endpoint for trace data."""
    traces = []
    
    # Read individual JSON trace files
    if TRACES_DIR.exists():
        for trace_file in sorted(TRACES_DIR.glob("*.json"), reverse=True)[:100]:  # Limit to 100 most recent
            try:
                with open(trace_file) as f:
                    trace = json.load(f)
                    traces.append(trace)
            except Exception as e:
                print(f"Error reading {trace_file}: {e}")
    
    # Also read OpenTelemetry JSONL traces
    jsonl_file = Path(".observability/traces.jsonl")
    if jsonl_file.exists():
        try:
            with open(jsonl_file) as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            span = json.loads(line)
                            # Convert OpenTelemetry span to our trace format
                            trace = {
                                "trace_id": span["trace_id"],
                                "timestamp": span["start_time"],
                                "activity_type": "primitive_execution",
                                "provider": "ttadev",
                                "model": "primitives",
                                "agent": span["attributes"].get("primitive.type", "unknown"),
                                "user": "system",
                                "details": {
                                    "primitive": span["name"],
                                    "duration_ns": span["duration_ns"],
                                    "status": span["status"]["status_code"],
                                    "attributes": span["attributes"]
                                }
                            }
                            traces.append(trace)
                        except json.JSONDecodeError:
                            pass
        except Exception as e:
            print(f"Error reading JSONL traces: {e}")
    
    # Add CORS headers
    response = web.json_response(traces)
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response


async def handle_api_stats(request):
    """API endpoint for statistics."""
    traces = []
    
    if TRACES_DIR.exists():
        for trace_file in TRACES_DIR.glob("*.json"):
            try:
                with open(trace_file) as f:
                    traces.append(json.load(f))
            except:
                pass
    
    # Aggregate stats
    providers = {}
    models = {}
    agents = {"none": 0}
    users = {}
    workflows = {}
    
    for trace in traces:
        # Count by provider
        provider = trace.get("provider", "unknown")
        providers[provider] = providers.get(provider, 0) + 1
        
        # Count by model
        model = trace.get("model", "unknown")
        models[model] = models.get(model, 0) + 1
        
        # Count by agent (None means direct user/agent interaction)
        agent = trace.get("agent") or "none"
        agents[agent] = agents.get(agent, 0) + 1
        
        # Count by user
        user = trace.get("user", "unknown")
        users[user] = users.get(user, 0) + 1
        
        # Count workflows
        if trace.get("activity_type") == "workflow_start":
            workflow = trace.get("details", {}).get("workflow", "unknown")
            workflows[workflow] = workflows.get(workflow, 0) + 1
    
    # Add CORS headers
    response = web.json_response({
        "total_traces": len(traces),
        "providers": providers,
        "models": models,
        "agents": agents,
        "users": users,
        "workflows": workflows,
    })
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response


async def handle_api_agents(request):
    """API endpoint for registered agents."""
    agents_dir = Path("/home/thein/repos/TTA.dev/.github/agents")
    agents = []
    
    if agents_dir.exists():
        for agent_file in agents_dir.glob("*.agent.md"):
            try:
                with open(agent_file) as f:
                    content = f.read()
                    # Extract name from filename
                    name = agent_file.stem.replace(".agent", "")
                    agents.append({
                        "name": name,
                        "file": str(agent_file.name),
                        "active": False  # TODO: Track active agents from traces
                    })
            except:
                pass
    
    response = web.json_response(agents)
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response


async def handle_api_primitives(request):
    """API endpoint for available primitives."""
    primitives_dir = Path("/home/thein/repos/TTA.dev/ttadev/primitives")
    primitives = []
    
    if primitives_dir.exists():
        for py_file in primitives_dir.rglob("*.py"):
            if py_file.name.startswith("_"):
                continue
            try:
                # Extract primitive class names
                with open(py_file) as f:
                    content = f.read()
                    if "Primitive" in content:
                        name = py_file.stem
                        primitives.append({
                            "name": name,
                            "file": str(py_file.relative_to(primitives_dir)),
                            "usage_count": 0  # TODO: Count from traces
                        })
            except:
                pass
    
    response = web.json_response(primitives)
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response


async def handle_api_workflows(request):
    """API endpoint for registered workflows."""
    # TODO: Scan for workflow definitions
    workflows = []
    
    response = web.json_response(workflows)
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response


async def handle_api_active_agents(request):
    """API endpoint for currently active agents."""
    tracker = get_tracker()
    active_agents = tracker.get_active_agents(since_minutes=5)
    
    response = web.json_response(active_agents)
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response


async def handle_api_agent_actions(request):
    """API endpoint for recent agent actions."""
    tracker = get_tracker()
    limit = int(request.query.get('limit', 100))
    recent_actions = tracker.get_recent_actions(limit=limit)
    
    response = web.json_response(recent_actions)
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response


async def handle_websocket(request):
    """WebSocket handler for real-time updates."""
    ws = web.WebSocketResponse()
    await ws.prepare(request)
    
    websocket_connections.add(ws)
    print(f"✓ WebSocket client connected. Total connections: {len(websocket_connections)}")
    
    try:
        # Send initial connection confirmation
        await ws.send_json({"type": "connected", "message": "Connected to TTA.dev observability"})
        
        # Keep connection alive and listen for messages
        async for msg in ws:
            if msg.type == aiohttp.WSMsgType.TEXT:
                # Handle ping/pong for keep-alive
                if msg.data == 'ping':
                    await ws.send_str('pong')
            elif msg.type == aiohttp.WSMsgType.ERROR:
                print(f'WebSocket error: {ws.exception()}')
    finally:
        websocket_connections.discard(ws)
        print(f"✓ WebSocket client disconnected. Total connections: {len(websocket_connections)}")
    
    return ws


async def broadcast_to_websockets(data):
    """Broadcast data to all connected WebSocket clients."""
    if not websocket_connections:
        return
    
    dead_connections = set()
    for ws in websocket_connections:
        try:
            await ws.send_json(data)
        except:
            dead_connections.add(ws)
    
    # Clean up dead connections
    websocket_connections.difference_update(dead_connections)


async def watch_traces():
    """Watch for new trace files and broadcast to WebSocket clients."""
    last_traces = set()
    
    while True:
        try:
            if TRACES_DIR.exists():
                current_traces = set(TRACES_DIR.glob("*.json"))
                new_traces = current_traces - last_traces
                
                for trace_file in new_traces:
                    try:
                        with open(trace_file) as f:
                            trace = json.load(f)
                            await broadcast_to_websockets({
                                "type": "new_trace",
                                "trace": trace
                            })
                    except Exception as e:
                        print(f"Error reading new trace {trace_file}: {e}")
                
                last_traces = current_traces
        except Exception as e:
            print(f"Error watching traces: {e}")
        
        await asyncio.sleep(1)  # Check for new traces every second


async def start_server():
    """Start the observability dashboard server."""
    app = web.Application()
    
    # Routes
    app.router.add_get("/", handle_dashboard)
    app.router.add_get("/api/traces", handle_api_traces)
    app.router.add_get("/api/stats", handle_api_stats)
    app.router.add_get("/api/agents", handle_api_agents)
    app.router.add_get("/api/primitives", handle_api_primitives)
    app.router.add_get("/api/workflows", handle_api_workflows)
    app.router.add_get("/api/active_agents", handle_api_active_agents)
    app.router.add_get("/api/agent_actions", handle_api_agent_actions)
    app.router.add_get("/ws", handle_websocket)
    
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", 8000)
    await site.start()
    
    print("✓ Observability dashboard running at http://0.0.0.0:8000")
    print(f"✓ Watching traces in: {TRACES_DIR}")
    print("✓ WebSocket endpoint available at ws://0.0.0.0:8000/ws")
    
    # Start trace watcher in background
    asyncio.create_task(watch_traces())
    
    # Keep running
    while True:
        await asyncio.sleep(3600)


if __name__ == "__main__":
    asyncio.run(start_server())
