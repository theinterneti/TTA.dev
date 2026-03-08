# TTA.dev Observability Dashboard

**Batteries-included real-time monitoring for your AI-native workflows.**

## Features

- 🚀 **Auto-starting** - Minimal configuration needed
- 📊 **Real-time metrics** - Total/successful/failed workflows, avg duration
- 🔍 **Live traces** - See every primitive execution as it happens
- 🎨 **Beautiful UI** - Dark mode dashboard with auto-refresh

## Quick Start

```bash
# Run the demo (uses uv to manage dependencies)
uv run python tta-dev/observability/dashboard/demo.py
```

Open http://localhost:8080 in your browser and watch the magic! ✨

## Usage in Your Code

```python
import asyncio
import time

from ttadev.observability.dashboard import ObservabilityDashboard
from ttadev.primitives.core import WorkflowContext, LambdaPrimitive
from ttadev.primitives.recovery import RetryPrimitive, RetryStrategy


async def my_task(data: dict, ctx: WorkflowContext) -> str:
    """Example async task."""
    await asyncio.sleep(0.1)
    return "ok"


async def main() -> None:
    # Start the dashboard
    dashboard = ObservabilityDashboard()
    await dashboard.start()

    # Use TTA.dev primitives as normal
    task_primitive = LambdaPrimitive(my_task)
    workflow = RetryPrimitive(
        task_primitive,
        strategy=RetryStrategy(max_attempts=3),
    )
    ctx = WorkflowContext(workflow_id="my-workflow")

    # Execute and record the trace
    data = {"input": "value"}
    start = time.time()
    result = await workflow.execute(data, ctx)
    duration_ms = (time.time() - start) * 1000

    dashboard.record_trace(ctx.workflow_id, duration_ms, "success")
    print("Result:", result)

    # Cleanup
    await dashboard.stop()


if __name__ == "__main__":
    asyncio.run(main())
```

## API Endpoints

- `GET /` - Dashboard UI
- `GET /api/metrics` - Current metrics as JSON
- `GET /api/traces` - Recent traces (last 100)
- `GET /api/health` - Health check

## Architecture

The dashboard uses:
- **aiohttp** for async web server (dependency declared in pyproject.toml)
- **Embedded HTML/CSS/JS** for simplified deployment
- **Auto-refresh** every 2 seconds for real-time updates
- **deque with maxlen** to cap memory usage at 100 traces

Requires `aiohttp>=3.9.0` - install via `uv sync` or `pip install aiohttp`.

## Future Enhancements

- [ ] WebSocket streaming for instant updates
- [ ] Span waterfall visualization
- [ ] Export traces to OpenTelemetry collectors
- [ ] Multi-agent activity correlation
- [ ] Custom dashboards via config
