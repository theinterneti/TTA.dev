# TTA.dev Observability UI

**Lightweight, LangSmith-inspired observability for TTA.dev workflows**

## Overview

TTA Observability UI provides a simple, integrated observability experience for TTA.dev applications. Unlike Jaeger or complex APM tools, it's designed specifically for TTA.dev primitives and embeds directly into VS Code.

### Key Features

- **🎯 Primitive-Aware**: Understands TTA.dev workflow primitives
- **⚡ Zero-Config**: SQLite storage, no complex setup
- **🔗 VS Code Integration**: Embedded webview panel
- **📊 Real-Time**: WebSocket updates for live trace viewing
- **💰 Cost Tracking**: Built-in LLM cost analysis
- **🎨 Simple**: Clean UI focused on development workflow

### Inspiration

Inspired by LangSmith's excellent UX, simplified for local-first development.

---

## Quick Start

### Installation

```bash
# From source
cd packages/tta-observability-ui
uv sync

# Install globally
uv pip install -e .
```

### Start the Service

```bash
# Start observability server
tta-observability-ui start

# Or with uvicorn directly
uv run uvicorn tta_observability_ui.api:app --port 8765
```

### Initialize in Your App

```python
from observability_integration import initialize_observability

# Enable TTA UI collection
success = initialize_observability(
    service_name="my-app",
    enable_prometheus=True,
    enable_tta_ui=True,  # NEW!
    tta_ui_endpoint="http://localhost:8765"
)
```

### View Traces

**Option 1: VS Code (Recommended)**
```
Command Palette → "TTA: Open Observability Dashboard"
```

**Option 2: Browser**
```
Open http://localhost:8765
```

---

## Architecture

```
┌─────────────────────────────────────────────┐
│          Your TTA.dev Application           │
│  ┌──────────────────────────────────────┐  │
│  │ InstrumentedPrimitive (auto-tracing) │  │
│  └───────────────┬──────────────────────┘  │
└──────────────────┼─────────────────────────┘
                   │ OTLP/HTTP
                   ↓
┌─────────────────────────────────────────────┐
│        TTA Observability UI Service         │
│  ┌─────────┐  ┌─────────┐  ┌───────────┐  │
│  │Collector│→ │ SQLite  │→ │  REST API │  │
│  │ (OTLP)  │  │ Storage │  │(+WebSocket)│ │
│  └─────────┘  └─────────┘  └───────────┘  │
└──────────────────┬──────────────────────────┘
                   │ REST/WS
                   ↓
┌─────────────────────────────────────────────┐
│         Web UI (Browser or VS Code)         │
│  [Trace Timeline] [Metrics] [Errors]        │
└─────────────────────────────────────────────┘
```

---

## Features

### Trace Timeline View

Visualize workflow execution with nested primitive calls:

```
Trace: workflow_abc123 (2.5s ✅)
  ▼ CachePrimitive         [====]      50ms
  ▼ RouterPrimitive        [======]    100ms
  ▼ RetryPrimitive
     ├─ Attempt 1 (failed) [===]       75ms
     └─ Attempt 2 (success)[====]      80ms
  ▼ ParallelPrimitive
     ├─ Branch 1           [=========] 200ms
     ├─ Branch 2           [======]    150ms
     └─ Branch 3           [=======]   180ms
```

### Metrics Dashboard

Real-time metrics for your primitives:

- Cache hit rate
- Average latency by primitive type
- Error rate
- LLM cost tracking
- Primitive usage stats

### Error Highlighting

Automatic detection and highlighting of:

- Failed retries
- Timeout exceptions
- Circuit breaker trips
- Fallback activations

---

## API Reference

### REST Endpoints

```python
# List recent traces
GET /api/traces?limit=100

# Get trace details
GET /api/traces/{trace_id}

# Get spans for trace
GET /api/traces/{trace_id}/spans

# Metrics summary
GET /api/metrics/summary

# Primitive stats
GET /api/primitives/stats
```

### WebSocket

```javascript
// Connect to real-time trace updates
const ws = new WebSocket('ws://localhost:8765/ws/traces');

ws.onmessage = (event) => {
    const trace = JSON.parse(event.data);
    console.log('New trace:', trace);
};
```

---

## Configuration

### Environment Variables

```bash
# Service configuration
export TTA_UI_PORT=8765
export TTA_UI_HOST="0.0.0.0"

# Storage
export TTA_UI_DB_PATH="./tta_traces.db"
export TTA_UI_RETENTION_HOURS=24

# Features
export TTA_UI_ENABLE_WEBSOCKET=true
export TTA_UI_MAX_TRACES=1000
```

### Programmatic Configuration

```python
from tta_observability_ui import start_service

await start_service(
    port=8765,
    db_path="./traces.db",
    retention_hours=24,
    max_traces=1000,
    enable_websocket=True
)
```

---

## VS Code Integration

### Installation

The VS Code extension is included in the main TTA.dev workspace.

### Commands

- `TTA: Open Observability Dashboard` - Open webview panel
- `TTA: View Latest Trace` - Show most recent execution
- `TTA: View Trace by ID` - Search for specific trace
- `TTA: Toggle Auto-Refresh` - Enable/disable live updates

### Status Bar

Shows current observability status:

```
[TTA: ✅ 5 traces | ⚡ 125ms avg | 💰 $0.05]
```

---

## Examples

### Basic Usage

```python
from observability_integration import initialize_observability
from tta_dev_primitives import WorkflowContext
from tta_dev_primitives.recovery import RetryPrimitive

# Initialize observability with UI
initialize_observability(
    service_name="my-workflow",
    enable_tta_ui=True
)

# Create workflow
async def my_operation(data, context):
    return {"result": "processed"}

workflow = RetryPrimitive(
    primitive=my_operation,
    max_retries=3
)

# Execute - traces automatically appear in UI
context = WorkflowContext(trace_id="demo-123")
result = await workflow.execute({"input": "test"}, context)

# View in UI: http://localhost:8765
```

### Custom Metrics

```python
from tta_observability_ui.client import record_metric

# Record custom metrics that appear in dashboard
await record_metric(
    name="custom_operation_duration",
    value=125.5,
    primitive_type="CustomPrimitive",
    labels={"environment": "production"}
)
```

---

## Development

### Setup

```bash
cd packages/tta-observability-ui
uv sync --all-extras
```

### Run Tests

```bash
uv run pytest -v
```

### Type Checking

```bash
uvx pyright src/
```

### Start Dev Server

```bash
uv run uvicorn tta_observability_ui.api:app --reload --port 8765
```

---

## Troubleshooting

### Service Won't Start

```bash
# Check port availability
lsof -i :8765

# Use different port
TTA_UI_PORT=8766 tta-observability-ui start
```

### No Traces Appearing

```python
# Verify OTLP endpoint
import httpx

response = await httpx.post(
    "http://localhost:8765/v1/traces",
    json={"test": "trace"}
)
print(response.status_code)  # Should be 200
```

### WebSocket Connection Failed

```javascript
// Check WebSocket endpoint
const ws = new WebSocket('ws://localhost:8765/ws/traces');

ws.onerror = (error) => {
    console.error('WebSocket error:', error);
};
```

---

## Comparison with Other Tools

| Feature | TTA UI | Jaeger | LangSmith | Prometheus |
|---------|--------|--------|-----------|------------|
| Setup | ⭐ Easy | ⭐⭐⭐ Complex | ⭐⭐ Medium | ⭐⭐ Medium |
| VS Code | ✅ Yes | ❌ No | ❌ No | ❌ No |
| Local-First | ✅ Yes | ⚠️ Docker | ❌ Cloud | ✅ Yes |
| Primitive-Aware | ✅ Yes | ❌ No | ⚠️ LLM-focused | ❌ No |
| Real-Time | ✅ Yes | ⚠️ Limited | ✅ Yes | ⚠️ Polling |
| Cost Tracking | ✅ Yes | ❌ No | ✅ Yes | ❌ No |

---

## Roadmap

### Phase 1: Core Service ✅
- [x] OTLP trace collection
- [x] SQLite storage
- [x] REST API
- [x] Basic web UI

### Phase 2: Enhanced UI 🚧
- [ ] Trace timeline visualization
- [ ] Metrics dashboard
- [ ] Error highlighting
- [ ] WebSocket real-time updates

### Phase 3: VS Code Integration 📋
- [ ] Webview panel
- [ ] Commands
- [ ] Status bar
- [ ] Settings

### Phase 4: Advanced Features 💭
- [ ] Cost breakdown by LLM
- [ ] Performance regression detection
- [ ] Custom dashboards
- [ ] Alert configuration

---

## Contributing

See [CONTRIBUTING.md](../../CONTRIBUTING.md) for development guidelines.

## License

MIT - See [LICENSE](../../LICENSE)

## Related Documentation

- **Architecture**: `docs/architecture/OBSERVABILITY_UI_DESIGN.md`
- **Integration Guide**: `docs/integration/observability-integration.md`
- **Primitives**: `packages/tta-dev-primitives/README.md`

---

**Last Updated:** November 10, 2025  
**Status:** Phase 1 Implementation  
**Maintainer:** TTA.dev Team
