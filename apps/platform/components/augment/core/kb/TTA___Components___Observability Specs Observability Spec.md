---
title: Primitive Specification: Development Observability
tags: #TTA
status: Active
repo: theinterneti/TTA
path: scripts/observability/specs/observability_spec.md
created: 2025-11-01
updated: 2025-11-01
---
# [[TTA/Components/Primitive Specification: Development Observability]]

**Version:** 1.0
**Status:** Stable
**Location:** `scripts/observability/dev_metrics.py`

---

## Purpose

Track and visualize development operation metrics (tests, builds, quality checks) to identify performance bottlenecks, monitor success rates, and enable data-driven development decisions.

---

## Contract

### Inputs

#### `DevMetricsCollector` Constructor

**Parameters:**
- `metrics_dir: str = ".metrics"` - Directory for metrics storage

#### `start_execution` Method

**Parameters:**
- `name: str` - Name of the operation being tracked
- `metadata: dict | None = None` - Optional metadata to attach

**Returns:** `str` - Execution ID (UUID)

**Side Effects:**
- Creates `ExecutionMetric` object
- Stores in `current_metrics` dict
- Logs start event

#### `end_execution` Method

**Parameters:**
- `exec_id: str` - Execution ID from `start_execution`
- `status: str = "success"` - Status ("success" or "failed")
- `error: str | None = None` - Error message if failed

**Returns:** None

**Side Effects:**
- Calculates duration
- Saves metric to JSONL file
- Removes from `current_metrics`
- Logs completion event

#### `track_execution` Decorator

**Parameters:**
- `name: str` - Name of the operation
- `metadata: dict | None = None` - Optional metadata

**Decorated Function:**
- Can be any callable with any signature
- Exceptions are caught, logged, and re-raised

**Returns:** Decorated function

#### `get_metrics_summary` Method

**Parameters:**
- `days: int = 7` - Number of days to include in summary

**Returns:** `dict[str, Any]` - Summary metrics by operation name

#### `get_recent_metrics` Method

**Parameters:**
- `name: str | None = None` - Optional filter by operation name
- `limit: int = 10` - Maximum number of metrics to return

**Returns:** `list[dict]` - Recent metrics, sorted by timestamp descending

#### `clear_old_metrics` Method

**Parameters:**
- `days_to_keep: int = 30` - Number of days to retain

**Returns:** `int` - Number of files deleted

**Side Effects:**
- Deletes metrics files older than specified days

### Outputs

#### ExecutionMetric Structure

```python
{
    "name": "pytest_unit_tests",
    "started_at": "2025-10-20T10:30:00.000000",
    "ended_at": "2025-10-20T10:30:05.123000",
    "duration_ms": 5123.0,
    "status": "success",  # or "failed"
    "metadata": {
        "suite": "unit",
        "type": "test"
    },
    "error": null  # or error message
}
```

#### Summary Metrics Structure

```python
{
    "pytest_unit_tests": {
        "total_executions": 10,
        "successes": 9,
        "failures": 1,
        "success_rate": 0.9,
        "avg_duration_ms": 5123.0,
        "min_duration_ms": 4500.0,
        "max_duration_ms": 6000.0
    }
}
```

#### File Storage

**Format:** JSONL (JSON Lines)

**Location:** `.metrics/YYYY-MM-DD.jsonl`

**Example:**
```
{"name": "pytest_unit_tests", "started_at": "2025-10-20T10:30:00", ...}
{"name": "ruff_lint", "started_at": "2025-10-20T10:31:00", ...}
```

**Benefits:**
- Append-only (fast writes)
- One metric per line (easy parsing)
- Organized by date (easy cleanup)
- Human-readable (debugging)

### Guarantees

1. **Automatic Tracking**
   - Decorator automatically tracks start/end
   - Duration calculated precisely
   - Exceptions caught and logged

2. **Persistent Storage**
   - Metrics survive process restarts
   - Organized by date for easy management
   - JSONL format for efficient append

3. **Accurate Timing**
   - Uses `datetime.utcnow()` for timestamps
   - Duration in milliseconds (float precision)
   - Timezone-aware (UTC)

4. **Error Handling**
   - Exceptions in tracked functions are caught
   - Error message stored in metric
   - Exception re-raised after logging

5. **Cleanup Support**
   - Old metrics can be deleted
   - Configurable retention period
   - Returns count of deleted files

---

## Usage Patterns

### Pattern 1: Track Function Execution

```python
from observability.dev_metrics import track_execution

@track_execution("pytest_unit_tests", metadata={"suite": "unit"})
def run_unit_tests():
    # Test execution code
    pass
```

**Behavior:**
- Automatically tracks start/end
- Logs duration and status
- Saves to `.metrics/YYYY-MM-DD.jsonl`

### Pattern 2: Manual Tracking

```python
from observability.dev_metrics import get_collector

collector = get_collector()

exec_id = collector.start_execution("custom_operation", metadata={"key": "value"})

try:
    # Your operation
    result = perform_operation()
    collector.end_execution(exec_id, status="success")
except Exception as e:
    collector.end_execution(exec_id, status="failed", error=str(e))
    raise
```

**Behavior:**
- Full control over tracking
- Can add custom metadata
- Explicit error handling

### Pattern 3: View Metrics Summary

```python
from observability.dev_metrics import get_collector

collector = get_collector()
summary = collector.get_metrics_summary(days=7)

for name, metrics in summary.items():
    print(f"{name}:")
    print(f"  Success Rate: {metrics['success_rate']:.1%}")
    print(f"  Avg Duration: {metrics['avg_duration_ms']:.0f}ms")
```

**Behavior:**
- Aggregates metrics for last N days
- Calculates success rates, averages
- Returns summary dictionary

### Pattern 4: Generate Dashboard

```python
from observability.dashboard import generate_dashboard

generate_dashboard(
    output_file="dev_metrics_dashboard.html",
    days=30
)
```

**Behavior:**
- Generates HTML dashboard
- Includes charts (if matplotlib available)
- Shows detailed metrics table

### Pattern 5: Cleanup Old Metrics

```python
from observability.dev_metrics import get_collector

collector = get_collector()
deleted = collector.clear_old_metrics(days_to_keep=30)

print(f"Deleted {deleted} old metrics files")
```

**Behavior:**
- Deletes metrics older than specified days
- Returns count of deleted files
- Prevents metrics directory from growing indefinitely

---

## Integration Points

### With Error Recovery

```python
from primitives.error_recovery import with_retry
from observability.dev_metrics import track_execution

@track_execution("api_call_with_retry")
@with_retry()
def resilient_api_call():
    # Metrics track total time including retries
    pass
```

**Benefit:** See impact of retries on execution time

### With Context Management

```python
from observability.dev_metrics import track_execution
from .augment.context.conversation_manager import AIConversationContextManager

@track_execution("context_save")
def save_conversation_context(session_id):
    manager.save_session(session_id)
```

**Benefit:** Monitor context save performance

### With CI/CD

```yaml
# .github/workflows/metrics-collection.yml
- name: Run tests with metrics
  run: python scripts/observability/examples.py workflow

- name: Generate dashboard
  run: python scripts/observability/examples.py dashboard

- name: Upload dashboard
  uses: actions/upload-artifact@v3
  with:
    name: metrics-dashboard
    path: dev_metrics_dashboard.html
```

**Benefit:** Track CI/CD performance over time

### With Development Scripts

```python
# scripts/dev.sh (Python wrapper)
from observability.dev_metrics import track_execution

@track_execution("dev_lint")
def run_lint():
    subprocess.run(["uvx", "ruff", "check", "src/"])

@track_execution("dev_test")
def run_tests():
    subprocess.run(["uvx", "pytest", "tests/"])
```

**Benefit:** Monitor all development operations

---

## Performance Characteristics

### Time Complexity

- **start_execution:** O(1)
- **end_execution:** O(1) - append to file
- **get_metrics_summary:** O(n*m) where n=days, m=metrics per day
- **get_recent_metrics:** O(n*m) where n=days, m=metrics per day
- **clear_old_metrics:** O(f) where f=number of files

### Space Complexity

- **Per Metric:** ~200-500 bytes (JSON)
- **Per Day:** Depends on operation frequency
- **Total:** Grows linearly with time (cleanup recommended)

### I/O Performance

- **Write:** Append-only (very fast)
- **Read:** Sequential scan (fast for recent data)
- **Cleanup:** File deletion (fast)

**Recommendation:** Run cleanup weekly/monthly to prevent unbounded growth

---

## Testing Considerations

### Unit Tests

```python
def test_track_execution_success():
    @track_execution("test_operation")
    def successful_operation():
        return "success"

    result = successful_operation()
    assert result == "success"

    # Verify metric was saved
    collector = get_collector()
    recent = collector.get_recent_metrics(name="test_operation", limit=1)
    assert len(recent) == 1
    assert recent[0]["status"] == "success"
```

### Integration Tests

```python
def test_metrics_persistence():
    # Create metric
    @track_execution("test_persistence")
    def operation():
        pass

    operation()

    # Verify file exists
    date_str = datetime.utcnow().strftime("%Y-%m-%d")
    metrics_file = Path(f".metrics/{date_str}.jsonl")
    assert metrics_file.exists()

    # Verify content
    with open(metrics_file) as f:
        lines = f.readlines()
        assert any("test_persistence" in line for line in lines)
```

---

## Phase 2 Considerations

When integrating into TTA application:

### LLM API Metrics

```python
@track_execution("llm_api_call", metadata={
    "model": "gpt-4",
    "tokens": 1000,
    "cost": 0.03
})
async def call_llm_api(prompt: str):
    response = await openai.ChatCompletion.create(...)
    return response
```

**Metrics to Track:**
- Latency
- Token usage
- Cost
- Success rate

### Agent Orchestration Metrics

```python
@track_execution("agent_workflow", metadata={
    "agent": "IPA",
    "step": "input_processing"
})
async def execute_agent_step(context):
    result = await agent.process(context)
    return result
```

**Metrics to Track:**
- Agent execution time
- Step-by-step timing
- Success rates per agent
- Workflow completion time

### Database Metrics

```python
@track_execution("redis_query", metadata={
    "operation": "get",
    "key_pattern": "session:*"
})
def query_redis(key: str):
    return redis_client.get(key)
```

**Metrics to Track:**
- Query latency
- Cache hit/miss rates
- Connection pool usage

### User Session Metrics

```python
@track_execution("user_session", metadata={
    "user_id": user_id,
    "session_type": "gameplay"
})
def track_user_session(user_id: str):
    # Track user session duration
    pass
```

**Metrics to Track:**
- Session duration
- User engagement
- Feature usage

### Distributed Tracing Integration

```python
# Integrate with OpenTelemetry
from opentelemetry import trace

@track_execution("traced_operation")
@trace.span("operation")
def traced_operation():
    # Both metrics and traces collected
    pass
```

**Benefits:**
- Correlate metrics with traces
- Distributed system visibility
- End-to-end request tracking

---

## Limitations

1. **Local Storage Only**
   - Metrics stored in local filesystem
   - Not suitable for distributed systems
   - Consider centralized metrics store (Prometheus, InfluxDB) for production

2. **No Real-Time Aggregation**
   - Metrics aggregated on-demand
   - Not suitable for real-time dashboards
   - Consider streaming metrics for production

3. **No Alerting**
   - No built-in alerting on thresholds
   - Manual monitoring required
   - Consider adding alerting for production

4. **Limited Visualization**
   - Basic HTML dashboard
   - No interactive charts
   - Consider Grafana/Kibana for production

5. **No Sampling**
   - All operations tracked
   - Could be high overhead for high-frequency operations
   - Consider sampling for production

---

**Status:** Stable - Ready for production use
**Last Updated:** 2025-10-20
**Next Review:** Before Phase 2 integration


---
**Logseq:** [[TTA.dev/Platform_tta_dev/Components/Augment/Core/Kb/Tta___components___observability specs observability spec]]
