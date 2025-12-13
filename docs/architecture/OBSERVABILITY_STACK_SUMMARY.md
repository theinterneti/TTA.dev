# TTA.dev Observability Stack Summary

**Current State & Enhancement: Visibility Improvement**

**Created:** November 10, 2025
**Status:** Phase 1 Implementation Complete

---

## Current Observability Stack

### Existing Infrastructure

**tta-observability-integration** (Production Ready ✅)
- OpenTelemetry tracing with automatic span creation
- Prometheus metrics export (port 9464)
- Grafana dashboard integration
- Jaeger distributed tracing support
- Graceful degradation when OTel unavailable

**Docker Compose Stack** (`docker-compose.integration.yml`)
```
Services Running:
├─ Jaeger UI         → http://localhost:16686 (Trace visualization)
├─ Prometheus        → http://localhost:9090  (Metrics queries)
├─ Grafana           → http://localhost:3000  (Dashboards)
├─ OTEL Collector    → ports 4317/4318        (Trace ingestion)
└─ Pushgateway       → port 9091              (Short-lived metrics)
```

**Core Features:**
- ✅ Automatic span creation for all `InstrumentedPrimitive` executions
- ✅ Prometheus metrics for primitive execution duration, count, errors
- ✅ Context propagation across distributed workflows
- ✅ Structured logging with correlation IDs
- ✅ Graceful degradation (works without OTel infrastructure)

---

## Problem Statement

### What We Have vs. What We Need

**Current Workflow (Complex):**
1. Start Docker stack: `docker-compose -f docker-compose.integration.yml up`
2. Run application with observability
3. Open Jaeger in browser (http://localhost:16686)
4. Search for traces by service name
5. Click through multiple UIs (Jaeger, Prometheus, Grafana)
6. Switch between browser tabs and VS Code

**LangSmith Workflow (Simple):**
1. Run application with LangSmith enabled
2. View traces automatically in integrated UI
3. See execution timeline, input/output, errors
4. All in one place, real-time updates

**Our Gap:**
- ❌ No integrated UI within VS Code
- ❌ Requires manual navigation to separate UIs
- ❌ No primitive-specific visualization
- ❌ No LLM cost tracking visibility
- ❌ Complex Docker setup for simple development

---

## New Solution: TTA Observability UI

### Package: `tta-observability-ui`

**Goal:** LangSmith-inspired, simple, local-first observability integrated with VS Code

### Architecture

```
┌────────────────────────────────────────────────────────────┐
│                    VS Code Editor                          │
│  ┌──────────────────────────────────────────────────────┐ │
│  │  TTA Observability Panel                             │ │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐                │ │
│  │  │ Traces  │ │ Metrics │ │ Config  │                │ │
│  │  └─────────┘ └─────────┘ └─────────┘                │ │
│  │                                                       │ │
│  │  [Real-time trace timeline]                          │ │
│  │  [Primitive call graph]                              │ │
│  │  [Error highlighting]                                │ │
│  └──────────────────────────────────────────────────────┘ │
└────────────────────────┬───────────────────────────────────┘
                         │ WebSocket + REST
                         ↓
┌────────────────────────────────────────────────────────────┐
│         TTA Observability Service (FastAPI)                │
│  Port: 8765                                                │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐      │
│  │ OTLP         │ │    SQLite    │ │   REST API   │      │
│  │ Collector    │→│   Storage    │→│  + WebSocket │      │
│  │              │ │              │ │              │      │
│  └──────────────┘ └──────────────┘ └──────────────┘      │
└────────────────────────┬───────────────────────────────────┘
                         │ OpenTelemetry (existing)
                         ↓
┌────────────────────────────────────────────────────────────┐
│          Your TTA.dev Application                          │
│  Uses: InstrumentedPrimitive (already working!)           │
└────────────────────────────────────────────────────────────┘
```

### Key Features

**1. Zero-Config Storage**
- SQLite database (no Postgres/Docker needed)
- Auto-created on first run
- Stores last 1000 traces (configurable)
- 24-hour retention by default

**2. Simple Integration**
```python
from observability_integration import initialize_observability

# Just add one flag!
initialize_observability(
    service_name="my-app",
    enable_prometheus=True,
    enable_tta_ui=True,  # ← NEW!
    tta_ui_endpoint="http://localhost:8765"
)

# Everything else works automatically!
```

**3. VS Code Native**
- Command: `TTA: Open Observability Dashboard`
- Embedded webview panel
- Status bar indicator: `[TTA: ✅ 5 traces | ⚡ 125ms avg]`
- Real-time updates via WebSocket

**4. Primitive-Aware**
- Knows about CachePrimitive, RetryPrimitive, etc.
- Shows retry attempts, cache hits, fallback activations
- LLM cost tracking (when enabled)
- Error highlighting with stack traces

**5. Browser Fallback**
- Works in browser: http://localhost:8765
- Same UI as VS Code panel
- No extension needed for basic usage

---

## Implementation Status

### Phase 1: Core Service ✅ IN PROGRESS

**Files Created:**
```
packages/tta-observability-ui/
├── pyproject.toml                     ✅ Package configuration
├── README.md                          ✅ User documentation
└── src/tta_observability_ui/
    ├── __init__.py                    ✅ Package exports
    ├── models.py                      ✅ Data models (Trace, Span, MetricRecord)
    ├── storage.py                     ✅ SQLite storage layer
    ├── collector.py                   ✅ OTLP trace collector
    ├── api.py                         🚧 FastAPI REST endpoints
    └── cli.py                         🚧 CLI for service management
```

**What Works:**
- ✅ Trace and span data models
- ✅ SQLite storage with schema
- ✅ OTLP trace collection and parsing
- ✅ Automatic cleanup of old traces
- ✅ Metrics aggregation

**TODO:**
- [ ] FastAPI REST API endpoints
- [ ] WebSocket real-time updates
- [ ] CLI: `tta-observability-ui start`
- [ ] Integration with existing `initialize_observability()`

### Phase 2: Web UI 📋 NOT STARTED

```
packages/tta-observability-ui/ui/
├── index.html        # Dashboard home
├── traces.html       # Trace timeline view
├── metrics.html      # Metrics dashboard
├── app.css           # Styling
└── app.js            # Logic + WebSocket client
```

**Features to Build:**
- [ ] Trace timeline visualization (D3.js or similar)
- [ ] Metrics cards and charts
- [ ] Error view with stack traces
- [ ] Search and filter traces
- [ ] Real-time updates

### Phase 3: VS Code Integration 📋 NOT STARTED

```
.vscode/extensions/tta-observability/
├── package.json
├── extension.js
└── webview/
    └── (reuse UI from Phase 2)
```

**Features to Build:**
- [ ] Webview panel
- [ ] Commands: Open dashboard, view trace by ID
- [ ] Status bar integration
- [ ] Settings for service URL/port

---

## Comparison: Current vs. New

| Feature | Current Stack | TTA UI | Advantage |
|---------|--------------|---------|-----------|
| **Setup** | Docker compose + 5 services | Single Python service | 90% simpler |
| **Storage** | Jaeger (Cassandra/ES) | SQLite | Zero config |
| **Access** | Browser tabs | VS Code panel | Integrated |
| **Primitive-Aware** | Generic spans | Knows TTA primitives | Better UX |
| **Real-time** | Refresh needed | WebSocket | Live updates |
| **LLM Costs** | Not tracked | Built-in | Visibility |
| **Learning Curve** | High (3 tools) | Low (1 UI) | Faster onboarding |

---

## Integration with Existing Stack

### Keep Both Systems ✅

**Existing Stack (Production):**
- Keep Jaeger for distributed tracing
- Keep Prometheus for production metrics
- Keep Grafana for custom dashboards
- Use for production/staging environments

**TTA UI (Development):**
- Use for local development
- Use for debugging workflows
- Use for learning TTA primitives
- Use for quick iteration

### How They Work Together

```python
# Initialize both!
from observability_integration import initialize_observability

initialize_observability(
    service_name="my-app",

    # Production stack (existing)
    enable_prometheus=True,        # Grafana dashboards
    otlp_endpoint="http://jaeger:4317",  # Distributed tracing

    # Development UI (new)
    enable_tta_ui=True,            # Local observability
    tta_ui_endpoint="http://localhost:8765"
)

# Both work simultaneously!
# - Jaeger gets distributed traces
# - TTA UI gets local development traces
# - Prometheus gets metrics from both
```

---

## Next Steps

### Immediate (This Week)

1. **Complete Phase 1:**
   - [ ] Finish `api.py` with REST endpoints
   - [ ] Implement WebSocket for real-time updates
   - [ ] Create `cli.py` for service management
   - [ ] Test OTLP integration with existing primitives

2. **Documentation:**
   - [ ] Add to `AGENTS.md` - visibility section
   - [ ] Update `MCP_SERVERS.md` if using MCP
   - [ ] Create usage examples

3. **Testing:**
   - [ ] Unit tests for collector and storage
   - [ ] Integration test with real workflow
   - [ ] Performance test (1000 traces)

### Short Term (Next 2 Weeks)

4. **Phase 2: Web UI**
   - [ ] HTML dashboard with trace timeline
   - [ ] Metrics visualization
   - [ ] Error highlighting
   - [ ] Real-time WebSocket client

5. **Phase 3: VS Code Extension**
   - [ ] Webview panel
   - [ ] Commands and keybindings
   - [ ] Status bar integration

### Long Term (Next Month)

6. **Advanced Features:**
   - [ ] Cost breakdown by LLM provider
   - [ ] Performance regression detection
   - [ ] Custom metric dashboards
   - [ ] Export to Jaeger format
   - [ ] Team sharing (optional cloud sync)

---

## Design Decisions

### Why SQLite?

**Pros:**
- ✅ Zero configuration
- ✅ Fast for local development
- ✅ Easy backup (just copy file)
- ✅ Portable
- ✅ Good enough for 1000 traces

**Cons:**
- ❌ Not for distributed teams (use Jaeger)
- ❌ Limited concurrent writes (fine for dev)

**Decision:** SQLite for dev, can add Postgres later if needed

### Why Separate Service?

**Pros:**
- ✅ Works with or without VS Code
- ✅ Can access from browser
- ✅ Independent lifecycle
- ✅ Easy to debug

**Cons:**
- ❌ One more process to manage

**Decision:** Separate service with auto-start option in VS Code

### Why Not Just Use Jaeger?

**Jaeger is Great For:**
- Production distributed tracing
- Large-scale deployments
- Team collaboration

**TTA UI is Better For:**
- Local development
- Understanding TTA primitives
- Quick debugging
- Learning workflows

**Decision:** Use both! They complement each other.

---

## Success Metrics

**Phase 1:**
- [ ] Collect 100% of traces from instrumented primitives
- [ ] Query latency < 100ms for trace retrieval
- [ ] Zero-config SQLite auto-creation works
- [ ] Service starts in < 2 seconds

**Phase 2:**
- [ ] Timeline renders 100-span trace in < 1s
- [ ] Real-time updates < 500ms latency
- [ ] Error highlighting within 1s

**Phase 3:**
- [ ] Dashboard opens in VS Code with 1 command
- [ ] Status bar updates within 2s
- [ ] Webview loads in < 2s

---

## Related Documentation

- **Design:** `docs/architecture/OBSERVABILITY_UI_DESIGN.md`
- **Existing Stack:** `docs/integration/observability-integration.md`
- **Integration Tests:** `platform/primitives/tests/integration/README_INTEGRATION_TESTS.md`
- **Package README:** `packages/tta-observability-ui/README.md`

---

## Questions & Answers

**Q: Will this replace Jaeger?**
A: No! Use TTA UI for development, Jaeger for production.

**Q: Do I need Docker?**
A: No for TTA UI (just Python). Yes for production stack (Jaeger/Prometheus).

**Q: Can I use this with existing code?**
A: Yes! Just add `enable_tta_ui=True` to `initialize_observability()`.

**Q: What about cost tracking?**
A: Phase 2 will add LLM cost visualization when using LLM primitives.

**Q: Can my team use it?**
A: Phase 1-3 is local-only. Later phases may add team sharing.

---

**Status:** Phase 1 implementation in progress
**ETA:** Phase 1 complete by November 12, 2025
**Next Review:** After Phase 1 completion


---
**Logseq:** [[TTA.dev/Docs/Architecture/Observability_stack_summary]]
