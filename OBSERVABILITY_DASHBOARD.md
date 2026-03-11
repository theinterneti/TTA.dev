# TTA.dev Observability Dashboard

**Zero-config, batteries-included observability for AI agent workflows**

## Quick Start

```bash
# 1. Start CGC (Code Graph Context) - optional but recommended
uv run --python 3.12 cgc watch .
uv run --python 3.12 cgc mcp start

# 2. Start observability dashboard
uv run python ttadev/ui/observability_server.py

# 3. Open browser
open http://localhost:8000
```

## Features

### 1. **Hierarchical Agent Tracking**
See the complete execution chain:
```
Provider (GitHub Copilot) →
  Model (Claude Sonnet 4.5) →
    Agent (backend-engineer) →
      Workflow (build_api_endpoint) →
        Primitives (RetryPrimitive, CachePrimitive) →
          Tools (bash, edit, view)
```

### 2. **Interactive Code Graph**
- Visualize your codebase structure
- See primitives, workflows, and agents
- Powered by CodeGraphContext (CGC)
- Click nodes to drill down

### 3. **Real-Time Updates**
- WebSocket streaming of agent activity
- Live workflow execution monitoring
- Automatic UI updates as code runs

### 4. **Workflow Registry**
- See all active workflows
- Track workflow execution counts
- Monitor success/failure rates

### 5. **Primitive Catalog**
- Browse all available primitives
- Search and filter by category
- Pagination for large catalogs

## Architecture

```
┌─────────────────────┐
│   Your AI Agent     │ (GitHub Copilot, etc.)
└──────────┬──────────┘
           │ uses
           ▼
┌─────────────────────┐
│  TTA.dev Primitives │ (auto-instrumented)
└──────────┬──────────┘
           │ emits traces
           ▼
┌─────────────────────┐
│ OpenTelemetry Spans │ → .observability/traces.jsonl
└──────────┬──────────┘
           │ reads
           ▼
┌─────────────────────┐
│ Observability Server│ (aiohttp + WebSocket)
└──────────┬──────────┘
           │ serves
           ▼
┌─────────────────────┐
│   Dashboard UI      │ (D3.js + WebSocket)
└─────────────────────┘
```

## Data Storage

All observability data is stored locally:

```
.observability/
├── traces.jsonl          # OpenTelemetry spans
└── workflows.json        # Workflow registry

~/.tta/
└── traces/               # Individual trace files
    ├── trace_001.json
    ├── trace_002.json
    └── ...
```

## Testing

We use Playwright for automated UI testing:

```bash
# Run all dashboard tests
uv run pytest tests/ui/test_observability_ui.py -v

# Test specific feature
uv run pytest tests/ui/test_observability_ui.py::test_cgc_graph_loads -v
```

## API Endpoints

- `GET /` - Dashboard UI
- `GET /api/traces` - Get all traces
- `GET /api/agents` - Get active agents
- `GET /api/workflows` - Get workflow registry
- `GET /api/primitives` - Get primitive catalog
- `GET /api/cgc/graph` - Get code graph from CGC
- `WS /ws` - WebSocket for real-time updates

## Customization

### Add Custom Metrics

```python
from ttadev.observability.agent_tracker import track_agent_activity

# Track your agent's work
track_agent_activity(
    provider="openrouter",
    model="anthropic/claude-3.5-sonnet",
    agent="my-custom-agent",
    user="thein",
    activity_type="workflow_start",
    details={"workflow_name": "my_workflow"}
)
```

### Extend the UI

Edit `ttadev/ui/dashboard.html` to add custom visualizations.

## Troubleshooting

### Dashboard won't start
```bash
# Kill any existing servers
pkill -f observability_server.py

# Check if port 8000 is in use
lsof -i :8000

# Start with logging
uv run python ttadev/ui/observability_server.py 2>&1 | tee server.log
```

### No traces showing
```bash
# Check if traces directory exists
ls -la .observability/
ls -la ~/.tta/traces/

# Generate test traces
uv run python -c "
from ttadev.primitives.core.base import WorkflowContext
from ttadev.primitives.core.lambda_primitive import LambdaPrimitive

async def test_fn(data, ctx):
    return {'result': 'test'}

primitive = LambdaPrimitive(test_fn)
context = WorkflowContext(workflow_id='test')

import asyncio
asyncio.run(primitive.execute({'input': 'test'}, context))
"
```

### CGC graph not loading
```bash
# Verify CGC is installed and indexed
uv run --python 3.12 cgc list

# Re-index if needed
uv run --python 3.12 cgc watch .
```

## Development

### Run tests with coverage
```bash
uv run pytest tests/ui/ -v --cov=ttadev/ui --cov-report=html
```

### Debug with Playwright
```python
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False, slow_mo=1000)
    page = browser.new_page()
    page.goto('http://localhost:8000')
    page.pause()  # Opens inspector
```

## Future Enhancements

- [ ] Distributed tracing across multiple agents
- [ ] Performance analytics and bottleneck detection
- [ ] Cost tracking per provider/model
- [ ] Custom dashboards per project
- [ ] Export traces to external APM (Datadog, New Relic)
- [ ] Slack/Discord notifications for errors

## Learn More

- [OBSERVABILITY_SPEC.md](./OBSERVABILITY_SPEC.md) - Technical specification
- [PRIMITIVES_CATALOG.md](./PRIMITIVES_CATALOG.md) - Available primitives
- [AGENTS.md](./AGENTS.md) - Custom agent documentation
