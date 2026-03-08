# TTA.dev Batteries-Included Observability

## 🎯 Overview

TTA.dev provides **zero-config, persistent observability** out of the box. Just clone the repo and start coding - all your workflows, primitives, and agent activities are automatically tracked and visualized.

## ✨ Key Features

### 1. **Persistent Storage**
- All telemetry data is automatically saved to `.tta/traces.db`
- Data survives dashboard restarts
- View historical traces from days/weeks/months ago

### 2. **Zero Configuration**
- No setup required - works immediately
- No external services needed (Jaeger, Zipkin, etc.)
- No environment variables to configure

### 3. **Automatic Instrumentation**
- All `WorkflowPrimitive` executions are automatically traced
- Workflows, retries, fallbacks, circuit breakers - all visible
- Agent actions and decisions are captured

### 4. **Real-Time Dashboard**
- Live web UI at `http://localhost:8000`
- See workflows executing in real-time
- Historical data loaded on startup

### 5. **Self-Observing**
- The dashboard itself uses TTA.dev primitives
- Demonstrates the platform while running
- Meta: observability that observes itself!

## 🚀 Quick Start

### Step 1: Start the Dashboard

```bash
cd TTA.dev
uv run python tta-dev/ui/observability_server.py
```

The dashboard starts at `http://localhost:8000`

### Step 2: Run Your Code

Any code using TTA.dev primitives is automatically instrumented:

```python
from primitives.core import WorkflowContext, LambdaPrimitive
from primitives.recovery.retry import RetryPrimitive, RetryStrategy
from observability.auto_instrument import auto_instrument_primitives

# Enable auto-instrumentation
auto_instrument_primitives()

async def my_operation(data: dict, ctx: WorkflowContext) -> dict:
    # Your logic here
    return {"result": "success"}

# This workflow is automatically traced!
workflow = RetryPrimitive(
    primitive=LambdaPrimitive(my_operation),
    strategy=RetryStrategy.EXPONENTIAL,
    max_attempts=3
)

result = await workflow.execute({"input": "data"}, WorkflowContext())
```

### Step 3: View the Data

Open `http://localhost:8000` in your browser. You'll see:

- **Real-time traces** as they execute
- **Historical data** from previous runs
- **Workflow visualizations** showing primitives and timing
- **Error tracking** with stack traces
- **Performance metrics** (duration, retry counts, etc.)

## 📊 Data Architecture

### Storage Layer

```
.tta/traces.db (SQLite)
├── spans table
│   ├── span_id (PRIMARY KEY)
│   ├── trace_id (FK to traces)
│   ├── parent_span_id
│   ├── name (primitive name)
│   ├── primitive_type
│   ├── start_time / end_time
│   ├── duration_ms
│   ├── status (ok | error)
│   └── attributes (JSON)
│
└── Indexed by:
    ├── trace_id (for grouping)
    └── created_at (for time-series queries)
```

### Data Flow

```
Your Code
    ↓
WorkflowPrimitive.execute()
    ↓
Auto-Instrumentation (decorator)
    ↓
TraceCollector.collect_span()
    ├→ Persist to SQLite (.tta/traces.db)
    └→ Send to Dashboard (WebSocket, best-effort)
        ↓
    Dashboard UI (real-time + historical)
```

## 🔍 What Gets Captured?

### For Each Primitive Execution

- **Identity**: Primitive type, name, trace ID
- **Timing**: Start time, end time, duration (ms)
- **Status**: Success or error (with stack traces)
- **Context**: Workflow ID, tags, metadata
- **Relationships**: Parent-child spans (workflow composition)

### For Workflows

- **Composition**: Which primitives were used
- **Ordering**: Sequential vs parallel execution
- **Retries**: How many attempts, backoff timing
- **Failures**: Where failures occurred, recovery actions
- **Circuit Breaker**: State transitions, failure thresholds

## 🎨 Dashboard Features

### Real-Time View

- Live trace stream as workflows execute
- WebSocket updates (< 500ms latency)
- Color-coded status (green = success, red = error)

### Historical View

- Automatically loads last 100 traces on startup
- Time-series visualization
- Filter by status, primitive type, workflow
- Click to expand full trace details

### Metrics Panel

- Total workflows executed
- Success / failure rates
- Average duration
- Retry counts
- Active workflows

## 🛠️ Advanced Usage

### Manual Instrumentation

For non-primitive code:

```python
from observability.auto_instrument import trace_workflow

@trace_workflow("data_processing_pipeline")
async def process_data(data: dict) -> dict:
    # Your custom logic here
    return processed_data
```

### Custom Attributes

Add metadata to traces:

```python
context = WorkflowContext(
    workflow_id="user-signup",
    tags={
        "user_id": "12345",
        "environment": "production",
        "feature_flag": "new_ui_enabled"
    }
)

result = await workflow.execute(data, context)
```

### Querying Historical Data

```python
from observability.collector import trace_collector

# Get recent spans
spans = trace_collector.get_recent_spans(limit=100)

# Filter by criteria
error_spans = [s for s in spans if s["status"] == "error"]
slow_spans = [s for s in spans if s["duration_ms"] > 1000]
```

## 🏗️ Production Considerations

### Data Retention

The SQLite database grows over time. For production:

```python
# Set up periodic cleanup (e.g., via cron)
import sqlite3
from datetime import datetime, timedelta

conn = sqlite3.connect(".tta/traces.db")
cursor = conn.cursor()

# Delete spans older than 30 days
cutoff = datetime.now() - timedelta(days=30)
cursor.execute("DELETE FROM spans WHERE created_at < ?", (cutoff,))
conn.commit()
```

### Sampling

For high-throughput systems, consider sampling:

```python
from observability.sampling import AdaptiveSampler

# Only trace 10% of requests
sampler = AdaptiveSampler(sample_rate=0.1)

if sampler.should_sample(context):
    # Execute with tracing
    result = await workflow.execute(data, context)
```

### Dashboard Scaling

For multiple developers/machines:

1. Run dashboard on shared server
2. Configure `TraceCollector.dashboard_url` to point to it
3. All data flows to central SQLite database
4. (Future: Add PostgreSQL backend for true multi-user support)

## 🐛 Troubleshooting

### Dashboard Shows "Disconnected"

- Check if server is running: `ps aux | grep observability_server`
- Restart: `uv run python tta-dev/ui/observability_server.py`
- Check port 8000 isn't in use: `lsof -i :8000`

### No Traces Appearing

- Verify auto-instrumentation is enabled: `auto_instrument_primitives()`
- Check database exists: `ls -lh .tta/traces.db`
- Run test: `uv run python tta-dev/test_persistent.py`

### Old Data Not Loading

- Check database permissions: `chmod 644 .tta/traces.db`
- Verify `load_historical_data()` runs on startup (check logs)

## 🎯 Roadmap

- [ ] Export to OpenTelemetry Protocol (OTLP)
- [ ] LangFuse integration for LLM traces
- [ ] PostgreSQL backend for multi-user deployments
- [ ] Advanced filtering and search
- [ ] Trace diff/comparison tools
- [ ] Slack/email alerts on errors
- [ ] Performance regression detection

## 📚 Learn More

- [Primitives Catalog](../PRIMITIVES_CATALOG.md) - All instrumented primitives
- [User Journey](../USER_JOURNEY.md) - End-to-end walkthrough
- [Getting Started](../GETTING_STARTED.md) - Setup guide
- [Examples](examples/) - Working code samples

---

**Questions?** Open an issue or check our [documentation](https://tta.dev/docs)
