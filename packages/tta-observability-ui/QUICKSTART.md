# TTA Observability UI - Quick Start Guide

**Get started with lightweight observability in 5 minutes**

---

## Prerequisites

- Python 3.11+
- `uv` package manager
- TTA.dev workspace set up

---

## Installation

### Option 1: From Source (Recommended for Development)

```bash
# Navigate to package directory
cd packages/tta-observability-ui

# Install dependencies
uv sync

# Install package in development mode
uv pip install -e .
```

### Option 2: Add to Workspace

```bash
# Add to pyproject.toml workspace members
# Already included in TTA.dev workspace!
```

---

## Quick Start

### Step 1: Start the Observability Service

**Terminal 1:**
```bash
# Start the service
tta-observability-ui start

# Or with custom configuration
tta-observability-ui start --port 8765 --log-level info
```

You should see:
```
╔══════════════════════════════════════════════════════════════╗
║            🔍 TTA Observability UI                          ║
╚══════════════════════════════════════════════════════════════╝

📍 Service URL:    http://0.0.0.0:8765
📊 API Docs:       http://0.0.0.0:8765/docs
🔌 OTLP Endpoint:  http://0.0.0.0:8765/v1/traces
💬 WebSocket:      ws://0.0.0.0:8765/ws/traces
```

### Step 2: Run the Example

**Terminal 2:**
```bash
# Run the integration example
cd packages/tta-observability-ui
uv run python examples/basic_example.py
```

### Step 3: View Traces

Open your browser to: **http://localhost:8765**

You should see:
- Service status
- API endpoints
- Integration instructions

**View Traces:**
- List traces: http://localhost:8765/api/traces
- Metrics: http://localhost:8765/api/metrics/summary
- Primitive stats: http://localhost:8765/api/primitives/stats

---

## Integration with Your Application

### Enable TTA UI in Your Code

```python
from observability_integration import initialize_observability

# Initialize with TTA UI enabled
initialize_observability(
    service_name="my-app",
    enable_prometheus=True,
    enable_tta_ui=True,  # ← Enable TTA UI
    tta_ui_endpoint="http://localhost:8765"
)
```

### Use Primitives as Normal

```python
from tta_dev_primitives import WorkflowContext
from tta_dev_primitives.recovery import RetryPrimitive

# Create workflow
workflow = RetryPrimitive(
    primitive=your_operation,
    max_retries=3
)

# Execute - traces automatically sent to TTA UI
context = WorkflowContext(correlation_id="my-trace")
result = await workflow.execute(data, context)
```

### View Traces

Traces are automatically sent to the TTA UI service and can be viewed at:
- http://localhost:8765/api/traces

---

## API Examples

### List Recent Traces

```bash
curl http://localhost:8765/api/traces?limit=10
```

Response:
```json
{
  "traces": [
    {
      "trace_id": "abc123",
      "workflow_name": "my_workflow",
      "status": "success",
      "duration_ms": 250,
      "span_count": 5
    }
  ],
  "total": 10,
  "limit": 10,
  "offset": 0
}
```

### Get Trace Details

```bash
curl http://localhost:8765/api/traces/abc123
```

Response includes full trace with all spans!

### Get Metrics Summary

```bash
curl http://localhost:8765/api/metrics/summary
```

Response:
```json
{
  "total_traces": 50,
  "success_rate": 0.92,
  "avg_duration_ms": 125.5,
  "error_rate": 0.08,
  "primitive_usage": {
    "CachePrimitive": 20,
    "RetryPrimitive": 15,
    "RouterPrimitive": 10
  }
}
```

---

## Advanced Configuration

### Custom Database Path

```bash
tta-observability-ui start --db-path ./my_traces.db
```

### Development Mode

```bash
# Auto-reload on code changes
tta-observability-ui start --reload --log-level debug
```

### Bind to Specific Host

```bash
# Only localhost
tta-observability-ui start --host 127.0.0.1
```

---

## WebSocket Real-Time Updates

### JavaScript Client

```javascript
const ws = new WebSocket('ws://localhost:8765/ws/traces');

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log('New trace update:', data);
};

ws.onopen = () => {
    console.log('Connected to TTA UI WebSocket');
};
```

### Python Client

```python
import asyncio
import websockets

async def watch_traces():
    async with websockets.connect('ws://localhost:8765/ws/traces') as ws:
        async for message in ws:
            print(f"Trace update: {message}")

asyncio.run(watch_traces())
```

---

## Troubleshooting

### Service Won't Start

**Error:** `Address already in use`

**Solution:**
```bash
# Check what's using port 8765
lsof -i :8765

# Use different port
tta-observability-ui start --port 9000
```

### No Traces Appearing

**Check:**
1. Service is running: `curl http://localhost:8765/health`
2. Application has TTA UI enabled
3. OTLP endpoint correct: `http://localhost:8765/v1/traces`

**Debug:**
```bash
# Run service with debug logging
tta-observability-ui start --log-level debug
```

### Database Issues

**Reset database:**
```bash
# Remove existing database
rm tta_traces.db

# Restart service
tta-observability-ui start
```

---

## Next Steps

1. **Try the Example:** Run `examples/basic_example.py`
2. **Integrate Your App:** Add `enable_tta_ui=True`
3. **Explore API:** Check http://localhost:8765/docs
4. **Wait for UI:** Phase 2 will add interactive dashboard!

---

## Architecture Overview

```
Your App → InstrumentedPrimitive → OTLP → TTA UI Service → SQLite → REST API → You!
```

**Benefits:**
- ✅ Zero-config SQLite storage
- ✅ Real-time WebSocket updates
- ✅ Primitive-aware trace visualization
- ✅ Works alongside Jaeger/Prometheus
- ✅ Local-first (no cloud dependency)

---

## Getting Help

- **Documentation:** `packages/tta-observability-ui/README.md`
- **Architecture:** `docs/architecture/OBSERVABILITY_UI_DESIGN.md`
- **Issues:** https://github.com/theinterneti/TTA.dev/issues

---

**Last Updated:** November 10, 2025  
**Package Version:** 0.1.0  
**Status:** Phase 1 Complete - API and Service Ready
