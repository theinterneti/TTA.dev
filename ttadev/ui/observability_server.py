"""Enhanced observability server with provider/model/agent tracking."""
import json
import asyncio
from pathlib import Path
from aiohttp import web

# Dashboard HTML file
DASHBOARD_FILE = Path(__file__).parent / "dashboard.html"
TRACES_DIR = Path.home() / ".tta" / "traces"


async def handle_dashboard(request):
    """Serve the dashboard HTML."""
    with open(DASHBOARD_FILE) as f:
        html = f.read()
    return web.Response(text=html, content_type="text/html")


async def handle_api_traces(request):
    """API endpoint for trace data."""
    traces = []
    
    if TRACES_DIR.exists():
        for trace_file in sorted(TRACES_DIR.glob("*.json"), reverse=True)[:100]:  # Limit to 100 most recent
            try:
                with open(trace_file) as f:
                    trace = json.load(f)
                    traces.append(trace)
            except Exception as e:
                print(f"Error reading {trace_file}: {e}")
    
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
    
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", 8000)
    await site.start()
    
    print("✓ Observability dashboard running at http://0.0.0.0:8000")
    print(f"✓ Watching traces in: {TRACES_DIR}")
    
    # Keep running
    while True:
        await asyncio.sleep(3600)


if __name__ == "__main__":
    asyncio.run(start_server())
