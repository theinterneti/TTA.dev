# TTA.dev Observability Dashboard

**Batteries-included real-time monitoring for your AI-native workflows.**

## Features

- 🚀 **Auto-starting** - No configuration needed
- 📊 **Real-time metrics** - Total/successful/failed workflows, avg duration
- 🔍 **Live traces** - See every primitive execution as it happens
- 🎨 **Beautiful UI** - Dark mode dashboard with auto-refresh
- 🔌 **Zero dependencies** - Single Python file, runs anywhere

## Quick Start

```bash
# Run the demo
python3 tta-dev/observability/dashboard/demo.py
```

Open http://localhost:8080 in your browser and watch the magic! ✨

## Usage in Your Code

```python
from tta_dev.observability.dashboard import ObservabilityDashboard
from tta_dev.primitives import RetryPrimitive, WorkflowContext

# Start the dashboard
dashboard = ObservabilityDashboard()
await dashboard.start()

# Use TTA.dev primitives as normal
workflow = RetryPrimitive(my_task, max_attempts=3)
ctx = WorkflowContext(workflow_id="my-workflow")

# Execute and record the trace
start = time.time()
result = await workflow.execute(data, ctx)
duration_ms = (time.time() - start) * 1000

dashboard.record_trace(ctx.workflow_id, duration_ms, "success")
```

## API Endpoints

- `GET /` - Dashboard UI
- `GET /api/metrics` - Current metrics as JSON
- `GET /api/traces` - Recent traces (last 100)
- `GET /api/health` - Health check

## Architecture

The dashboard is a single-file Python application using:
- **aiohttp** for async web server
- **Embedded HTML/CSS/JS** for zero-dependency deployment
- **Auto-refresh** every 2 seconds for real-time updates

No external databases, no complex setup - just run it!

## Future Enhancements

- [ ] WebSocket streaming for instant updates
- [ ] Span waterfall visualization
- [ ] Export traces to OpenTelemetry collectors
- [ ] Multi-agent activity correlation
- [ ] Custom dashboards via config
