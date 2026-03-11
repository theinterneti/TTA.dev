# TTA.dev Observability System Specification

**Status**: Draft  
**Version**: 1.0  
**Last Updated**: 2026-03-09

## Overview

The TTA.dev observability system provides **batteries-included, zero-config** visibility into AI agent workflows, primitives, and tool usage. It must be production-ready, not a demo.

---

## Core Requirements

### 1. Zero Configuration
- Clone repo → Agent sees AGENTS.md → Observability auto-starts
- No manual setup, no external dependencies
- File-based storage (no databases required)

### 2. Hierarchical Execution Model

Every user interaction creates a **trace** with this structure:

```
User Request (thein)
├── Provider: GitHub Copilot
│   ├── Model: Claude Sonnet 4.5
│   │   ├── Agent Role: backend-engineer (optional)
│   │   │   ├── Workflow: build_api_endpoint
│   │   │   │   ├── Primitive: RetryPrimitive
│   │   │   │   ├── Primitive: CachePrimitive
│   │   │   │   └── Tools: [bash, edit, view]
│   │   │   └── Skills: [test-driven-development]
│   │   └── Agent Role: architect
│   │       └── Workflow: review_design
```

### 3. Data Collection

**What to Track:**
- **Provider**: GitHub Copilot, OpenRouter, Ollama, etc.
- **Model**: Claude Sonnet 4.5, GPT-4, Llama, etc.
- **User**: thein, alice, bob
- **Agent Role**: backend-engineer, architect, or none
- **Workflows**: Named workflow executions
- **Primitives**: RetryPrimitive, CachePrimitive, etc.
- **Tools**: bash, edit, view, grep, etc.
- **Skills**: test-driven-development, code-review, etc.
- **Timestamps**: Start, end, duration
- **Status**: success, error, timeout
- **Metadata**: Inputs, outputs, error messages

**Storage:**
- JSON files in `.tta/observability/traces/`
- One file per trace
- Immutable once written

### 4. Web Dashboard

**URL**: `http://localhost:8000`

**Sections:**

1. **Active Agents** (Top)
   - Provider, Model, User, Current Role
   - Real-time status indicator

2. **Recent Traces** (Middle Left)
   - Last 20 traces with status
   - Click to expand hierarchical view
   - Show: User → Provider → Model → Agent → Workflow → Primitives → Tools

3. **Workflow Registry** (Middle Right)
   - All registered workflows
   - Usage count, avg duration, success rate

4. **Primitives Catalog** (Bottom Left)
   - All 68 primitives
   - Paginated, searchable
   - Usage stats per primitive

5. **Code Graph** (Bottom Right)
   - CodeGraphContext integration
   - Interactive dependency visualization
   - Filter by: primitives, workflows, agents

**Real-time Updates:**
- WebSocket connection for live data
- No page refresh required
- Connection status indicator

### 5. Testing Requirements

**Playwright E2E Tests:**
1. Server starts and serves HTML
2. Dashboard loads all sections
3. WebSocket connects successfully
4. Active agents populate correctly
5. Traces display with hierarchy
6. Workflow registry shows data
7. Primitives catalog is searchable
8. Code graph renders and is interactive
9. Real-time updates work when new trace added
10. Drill-down expands trace hierarchy

**All tests must pass before merge.**

---

## Implementation Plan

### Phase 1: Stable Foundation
1. Fix server stability (stop crashes)
2. Implement file-based trace storage
3. Create robust WebSocket handler
4. Write Playwright tests for basic functionality

### Phase 2: Data Collection
1. Instrument primitives to auto-log
2. Add agent role tracking
3. Implement workflow registry
4. Store traces to `.tta/observability/traces/`

### Phase 3: Dashboard Enhancement
1. Build hierarchical trace viewer
2. Add real-time updates via WebSocket
3. Implement drill-down UI
4. Add search/filter capabilities

### Phase 4: Advanced Features
1. Integrate CodeGraphContext visualization
2. Add performance metrics
3. Implement export functionality
4. Add custom dashboards

---

## Architecture

### Components

1. **Instrumentation Layer**
   - Auto-instruments all primitives
   - Captures provider/model/agent context
   - Writes traces to filesystem

2. **Storage Layer**
   - File-based JSON storage
   - Read-only after write (immutable)
   - Automatic cleanup of old traces

3. **API Server** (`observability_server.py`)
   - FastAPI application
   - WebSocket for real-time updates
   - Serves static HTML/JS/CSS

4. **Web Dashboard** (`dashboard.html`)
   - Vanilla JS (no frameworks)
   - Real-time WebSocket updates
   - Responsive design

### Data Flow

```
Primitive Execution
    ↓
Instrumentation captures context
    ↓
Write trace to .tta/observability/traces/{trace_id}.json
    ↓
API server watches for new files
    ↓
WebSocket pushes update to dashboard
    ↓
Dashboard updates UI in real-time
```

---

## Success Criteria

- [ ] Clone repo → Run `uv run python ttadev/ui/observability_server.py` → Dashboard works
- [ ] All 10 Playwright tests pass
- [ ] Server runs for 24+ hours without crashing
- [ ] Traces persist across server restarts
- [ ] Real-time updates work reliably
- [ ] Can see full hierarchy: User → Provider → Model → Agent → Workflow → Primitives → Tools
- [ ] CodeGraph integration works
- [ ] Zero manual configuration required

---

## Non-Goals (For Now)

- Authentication/authorization
- Multi-user support
- Cloud deployment
- Historical analytics beyond 30 days
- Custom metrics/alerting
- Integration with external APM tools
