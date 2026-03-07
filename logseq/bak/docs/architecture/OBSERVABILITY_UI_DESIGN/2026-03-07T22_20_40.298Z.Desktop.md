# TTA.dev Observability UI Design

**Lightweight, LangSmith-inspired visibility for TTA.dev workflows**

**Created:** November 10, 2025  
**Status:** Design Phase

---

## Overview

### Problem Statement

Current observability requires:
- Manual navigation to Jaeger UI (http://localhost:16686)
- Separate Prometheus UI (http://localhost:9090)
- Grafana dashboards (http://localhost:3000)
- No integration with VS Code development workflow
- Complex setup for simple trace viewing

### Inspiration: LangSmith

**What we like about LangSmith:**
- Single UI for all observability
- Trace timeline with nested steps
- Clear input/output visibility
- Real-time updates
- Integrated into development workflow

**What we'll simplify:**
- No cloud service (local-first)
- No complex deployment system
- Focus on development workflow only
- SQLite instead of distributed database
- Simple REST API instead of complex GraphQL

---

## Architecture

### High-Level Design

```
┌─────────────────────────────────────────────────────────┐
│                     VS Code Editor                      │
│  ┌─────────────────────────────────────────────────┐   │
│  │  TTA.dev Observability Panel (Webview)          │   │
│  │  ┌────────────┐ ┌────────────┐ ┌────────────┐  │   │
│  │  │   Traces   │ │  Metrics   │ │  Config    │  │   │
│  │  └────────────┘ └────────────┘ └────────────┘  │   │
│  │                                                  │   │
│  │  [Timeline View of Primitive Execution]         │   │
│  │  [Performance Metrics Cards]                    │   │
│  │  [Error Highlighting and Details]               │   │
│  └─────────────────────────────────────────────────┘   │
└───────────────────────┬─────────────────────────────────┘
                        │ WebSocket/REST
                        ↓
┌─────────────────────────────────────────────────────────┐
│           TTA Observability Service (FastAPI)           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │Trace Collector│  │ SQLite Store │  │  REST API    │  │
│  │  (OTLP recv) │  │   (Traces)   │  │ (Queries)    │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
└───────────────────────┬─────────────────────────────────┘
                        │ OpenTelemetry
                        ↓
┌─────────────────────────────────────────────────────────┐
│         TTA.dev Application (Your Code)                 │
│  ┌──────────────────────────────────────────────────┐  │
│  │  Primitives with InstrumentedPrimitive base      │  │
│  │  → Automatic span creation                        │  │
│  │  → Metric recording                               │  │
│  │  → Context propagation                            │  │
│  └──────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

### Component Breakdown

#### 1. Observability Service (`tta-observability-ui`)

**Tech Stack:**
- FastAPI for REST API
- SQLite for trace storage
- OpenTelemetry SDK for trace collection
- WebSocket for real-time updates

**Key Features:**
- OTLP receiver endpoint (compatible with existing setup)
- Simple trace storage (no complex Jaeger setup needed)
- REST API for trace queries
- Real-time WebSocket for live updates
- Prometheus scraping (reuse existing metrics)

#### 2. Web UI (Embedded in VS Code)

**Tech Stack:**
- Vanilla HTML/CSS/JavaScript (no build step)
- D3.js or similar for trace timeline
- WebSocket client for live updates
- VS Code Webview API for embedding

**Key Views:**

**a. Trace Timeline View:**
```
┌─────────────────────────────────────────────────────┐
│ Trace: workflow_execution_abc123                   │
│ Duration: 2.5s | Status: ✅ Success                │
├─────────────────────────────────────────────────────┤
│                                                     │
│  ▼ CachePrimitive           [====]     50ms       │
│  ▼ RouterPrimitive          [======]   100ms      │
│  ▼ RetryPrimitive                                 │
│     ├─ Attempt 1 (failed)   [===]      75ms      │
│     └─ Attempt 2 (success)  [====]     80ms      │
│  ▼ ParallelPrimitive                              │
│     ├─ Branch 1             [=========] 200ms     │
│     ├─ Branch 2             [======]   150ms     │
│     └─ Branch 3             [=======]  180ms     │
│                                                     │
└─────────────────────────────────────────────────────┘
```

**b. Metrics Dashboard:**
```
┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐
│  Cache Hit Rate  │ │  Avg Latency     │ │  Error Rate      │
│      87%         │ │     125ms        │ │      2.1%        │
└──────────────────┘ └──────────────────┘ └──────────────────┘

┌─────────────────────────────────────────────────────────┐
│ Primitive Usage (Last 100 traces)                      │
│ [Bar chart showing primitive call counts]              │
└─────────────────────────────────────────────────────────┘
```

**c. Error View:**
```
┌─────────────────────────────────────────────────────────┐
│ ❌ RetryPrimitive - All attempts exhausted              │
│ Trace: workflow_abc123                                  │
│                                                          │
│ Attempts:                                                │
│   1. TimeoutError: Request timed out after 5s           │
│   2. ConnectionError: Failed to connect                 │
│   3. TimeoutError: Request timed out after 5s           │
│                                                          │
│ [View Full Trace] [Jump to Code] [Copy Stack Trace]    │
└─────────────────────────────────────────────────────────┘
```

#### 3. VS Code Extension Integration

**Commands:**
- `TTA: Open Observability Dashboard` - Open webview panel
- `TTA: View Latest Trace` - Show most recent execution
- `TTA: View Trace by ID` - Search for specific trace
- `TTA: Toggle Auto-Refresh` - Live updates on/off

**Status Bar:**
```
[TTA: ✅ 5 traces | ⚡ 125ms avg | 💰 $0.05]
```

---

## Data Model

### Trace Storage (SQLite)

```sql
-- Traces table
CREATE TABLE traces (
    trace_id TEXT PRIMARY KEY,
    workflow_name TEXT,
    start_time TIMESTAMP,
    end_time TIMESTAMP,
    duration_ms INTEGER,
    status TEXT, -- 'success', 'error', 'timeout'
    error_message TEXT,
    context_data JSON, -- WorkflowContext metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Spans table (primitives)
CREATE TABLE spans (
    span_id TEXT PRIMARY KEY,
    trace_id TEXT,
    parent_span_id TEXT,
    primitive_type TEXT, -- 'CachePrimitive', 'RetryPrimitive', etc.
    primitive_name TEXT,
    start_time TIMESTAMP,
    end_time TIMESTAMP,
    duration_ms INTEGER,
    status TEXT,
    attributes JSON, -- Span attributes
    events JSON, -- Span events
    FOREIGN KEY (trace_id) REFERENCES traces(trace_id)
);

-- Metrics table (aggregated)
CREATE TABLE metrics (
    metric_id INTEGER PRIMARY KEY AUTOINCREMENT,
    primitive_type TEXT,
    metric_name TEXT,
    value REAL,
    timestamp TIMESTAMP,
    labels JSON
);
```

### REST API Endpoints

```
GET  /api/traces                    # List recent traces
GET  /api/traces/{trace_id}         # Get trace details
GET  /api/traces/{trace_id}/spans   # Get spans for trace
GET  /api/metrics/summary           # Current metrics summary
GET  /api/metrics/timeseries        # Time-series data
GET  /api/primitives/stats          # Primitive usage stats
WS   /ws/traces                     # Real-time trace updates
```

---

## Implementation Phases

### Phase 1: Core Service (Week 1)

**Goal:** Working trace collector and storage

```bash
packages/tta-observability-ui/
├── src/
│   ├── __init__.py
│   ├── collector.py      # OTLP trace receiver
│   ├── storage.py        # SQLite storage
│   ├── api.py            # FastAPI REST endpoints
│   └── models.py         # Data models
├── pyproject.toml
├── README.md
└── tests/
```

**Deliverables:**
- [x] FastAPI service running on port 8765
- [x] OTLP trace collection from existing primitives
- [x] SQLite storage with schema above
- [x] Basic REST API for trace queries

### Phase 2: Web UI (Week 2)

**Goal:** Simple HTML dashboard

```bash
packages/tta-observability-ui/
├── ui/
│   ├── index.html        # Main dashboard
│   ├── traces.html       # Trace timeline view
│   ├── metrics.html      # Metrics dashboard
│   ├── app.css           # Styling
│   └── app.js            # Logic + WebSocket
```

**Deliverables:**
- [x] Trace timeline visualization
- [x] Metrics cards and charts
- [x] Error highlighting
- [x] Real-time updates via WebSocket

### Phase 3: VS Code Integration (Week 3)

**Goal:** Embedded observability panel

```bash
.vscode/
├── extensions/
│   └── tta-observability/
│       ├── package.json
│       ├── extension.js
│       └── webview/
│           └── (reuse UI from Phase 2)
```

**Deliverables:**
- [x] VS Code webview panel
- [x] Commands for opening traces
- [x] Status bar integration
- [x] Settings for service URL/port

### Phase 4: Polish & Documentation (Week 4)

**Deliverables:**
- [x] Documentation in `docs/observability/UI_GUIDE.md`
- [x] Update AGENTS.md with new features
- [x] Example workflows showing UI usage
- [x] Performance optimization
- [x] Error handling improvements

---

## Key Design Decisions

### 1. SQLite vs. Distributed Database

**Decision:** SQLite for development, optional PostgreSQL for production

**Rationale:**
- Zero setup for developers
- Fast queries for local development
- Easy backup and portability
- Can upgrade to PostgreSQL if needed

### 2. Embedded UI vs. Separate Server

**Decision:** Hybrid - FastAPI service + VS Code embedded webview

**Rationale:**
- Service runs independently (can use from terminal too)
- VS Code integration for seamless workflow
- Browser fallback for non-VS Code users

### 3. Real-time vs. Polling

**Decision:** WebSocket for real-time, with fallback to polling

**Rationale:**
- WebSocket provides best UX
- Fallback ensures compatibility
- Optional (can disable for performance)

### 4. Trace Storage Duration

**Decision:** Keep last 1000 traces, configurable retention

**Rationale:**
- Development needs recent history
- Avoid unbounded growth
- Easy to export important traces

---

## Comparison with Existing Tools

| Feature | TTA.dev UI | Jaeger | LangSmith |
|---------|-----------|--------|-----------|
| Setup Complexity | ⭐ Low | ⭐⭐⭐ High | ⭐⭐ Medium |
| VS Code Integration | ✅ Native | ❌ Browser only | ❌ Browser only |
| Local-First | ✅ Yes | ⚠️ Docker needed | ❌ Cloud service |
| Primitive-Aware | ✅ Yes | ❌ Generic spans | ⚠️ LLM-focused |
| Real-time Updates | ✅ WebSocket | ⚠️ Limited | ✅ Yes |
| Cost Tracking | ✅ Built-in | ❌ No | ✅ Yes |
| Metrics Integration | ✅ Prometheus | ⚠️ Separate | ✅ Built-in |

---

## Success Metrics

**Phase 1:**
- [ ] Collect 100% of traces from instrumented primitives
- [ ] Sub-100ms query latency for trace retrieval
- [ ] Zero-config startup (SQLite auto-created)

**Phase 2:**
- [ ] Trace timeline renders in <1s for 100-span trace
- [ ] Real-time updates with <500ms latency
- [ ] Error traces highlighted within 1s of occurrence

**Phase 3:**
- [ ] Open dashboard in VS Code with single command
- [ ] Status bar updates within 2s of trace completion
- [ ] Webview loads in <2s

**Phase 4:**
- [ ] Documentation covers all features
- [ ] 5+ working examples
- [ ] Community feedback positive

---

## Future Enhancements

**Phase 5 (Optional):**
- [ ] Export traces to Jaeger format
- [ ] Distributed tracing across services
- [ ] Cost breakdown by LLM provider
- [ ] Custom metric dashboards
- [ ] Alert configuration UI
- [ ] Trace comparison tool
- [ ] Performance regression detection

---

## Getting Started (After Implementation)

### For Developers

```python
# 1. Start observability service
uv run tta-observability-ui

# 2. Initialize in your app
from observability_integration import initialize_observability

initialize_observability(
    service_name="my-app",
    enable_tta_ui=True,  # NEW: Enable TTA UI collection
    tta_ui_endpoint="http://localhost:8765"
)

# 3. Open VS Code dashboard
# Command Palette → "TTA: Open Observability Dashboard"
```

### For Users

```bash
# Start the UI server
docker run -p 8765:8765 tta-observability-ui

# Or local install
uv pip install tta-observability-ui
tta-observability-ui start
```

---

## Related Documentation

- [[TTA.dev/Observability]] - Observability overview
- [[tta-observability-integration]] - OpenTelemetry integration
- [[InstrumentedPrimitive]] - Primitive tracing
- `docs/integration/observability-integration.md` - Integration guide

---

**Next Steps:**

1. Review this design with team
2. Create `tta-observability-ui` package
3. Implement Phase 1 (collector + storage)
4. Build Phase 2 (web UI)
5. Integrate Phase 3 (VS Code)

**Questions to Resolve:**

- [ ] Should we support remote deployment (team observability)?
- [ ] Authentication/authorization needed?
- [ ] Trace retention policy preferences?
- [ ] Custom primitive visualization needs?

---

**Last Updated:** November 10, 2025  
**Status:** Design Complete - Ready for Implementation
