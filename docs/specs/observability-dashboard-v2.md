# Functional Specification: Observability Dashboard v2

**Status**: APPROVED — Proceed to `/plan`
**Phase**: SDD Phase 1 (`/specify`)
**Author**: Claude Code
**Date**: 2026-03-10
**Supersedes**: `OBSERVABILITY_SPEC.md` (partial), `OBSERVABILITY_DASHBOARD.md`

---

## 1. Problem Statement

The existing dashboard (`ttadev/ui/dashboard.html`) was built without a spec. It has:
- A flat trace list with Provider/Model/Agent as metadata — **not** a navigable hierarchy
- A disconnected static code graph (CGC) that doesn't react to live telemetry
- A primitives *catalog* (what exists) instead of *live usage* (what's running)
- No **Session** concept — no way to group "everything my agents did today"
- Two diverging server implementations (`ttadev/ui/observability_server.py` and `ttadev/observability/server.py`)
- A monolithic 1151-line HTML file that agents cannot reason about or safely modify

The core gap: the existing `OBSERVABILITY_SPEC.md` defines the right hierarchy on paper but it was never built.

---

## 2. Goal

A **batteries-included, zero-config** observability dashboard that gives developers and their AI agents a live, hierarchical view of every session's activity — which providers were used, which models, which workflows, which primitives — integrated with the CGC codebase graph so developers can see their code executing in real time.

### North Star User Story

> *As a developer who just cloned TTA.dev and opened Claude Code, I want to see — without any configuration — a live dashboard that shows me exactly what my AI agents are doing: which provider, which model, which workflow, which primitives, in a session I can navigate. When I click a node in the code graph, I see which of my sessions touched that code.*

---

## 3. User Journeys

### Journey 1: Developer First Clones TTA.dev

1. `git clone` + open Claude Code (or Copilot, Cline, etc.)
2. Agent reads `AGENTS.md` → it includes a note: "Observability dashboard auto-starts. Access at http://localhost:8000."
3. Agent (or developer) runs `uv run python -m ttadev.observability` (or a script in `scripts/`)
4. Browser opens. Dashboard shows: **Session #1** (active), no traces yet.
5. Agent uses a TTA.dev primitive (e.g., `RetryPrimitive`). Within 1 second, the dashboard updates: Session #1 → Anthropic → claude-sonnet-4-6 → RetryPrimitive span appears.
6. The CGC graph node for `RetryPrimitive` pulses briefly.

**Success**: No manual configuration. First trace appears within 1 second of primitive execution.

---

### Journey 2: Developer Reviews Yesterday's Sessions

1. Dashboard loads. Left sidebar shows sessions list: "Session #5 (now)", "Session #4 (yesterday, 2h 15m)", "Session #3 (2 days ago)".
2. Developer clicks Session #4.
3. Right panel shows the session tree:
   - Anthropic → claude-sonnet-4-6 → backend-engineer → CachePrimitive >> RetryPrimitive (3 executions, avg 142ms)
   - OpenRouter → llama-3.1-70b → (no agent role) → direct call
4. Developer clicks on "CachePrimitive >> RetryPrimitive" chain.
5. Span detail panel opens showing timestamps, inputs, outputs, hit/miss, retry counts.

**Success**: Developer can reconstruct exactly what happened in any past session in ≤3 clicks.

---

### Journey 3: Agent Monitors Its Own Work

1. An AI agent (Claude Code) is implementing a feature.
2. Agent calls `GET /api/session/current` → receives current session id, primitive usage summary, any errors.
3. Agent uses this data to self-report: "I've executed 12 workflow steps. 2 retried. 0 errors."
4. Agent can also read `GET /api/sessions` to understand prior patterns.

**Success**: API is usable by agents themselves, not just humans.

---

### Journey 4: Developer Explores Code Graph with Live Context

1. Developer opens CGC "Architecture" view in the dashboard.
2. Graph shows TTA.dev package structure (packages as nodes, dependencies as edges).
3. Developer switches on "Live Overlay" toggle.
4. Nodes that were touched in the current session glow blue; nodes touched in the last 5 minutes pulse.
5. Developer hovers a glowing node → tooltip shows: "RetryPrimitive: 3 executions, 1 retry, 0 errors (Session #5)"
6. Developer clicks a node → right panel filters to show only traces involving that primitive.

**Success**: CGC graph becomes a live execution map, not a static diagram.

---

### Journey 5: Error Debugging

1. A workflow fails with a timeout.
2. Dashboard immediately updates: Session tree shows ❌ on the span.
3. Developer clicks the error span.
4. Detail panel shows: error type, message, stack (if captured), which primitive failed, retry count before failure.
5. CGC graph highlights the failing node in red.

**Success**: From error occurrence to full context in ≤2 clicks.

---

## 4. Core Data Model

### Session

```
Session
  id: str (uuid4)
  started_at: datetime
  ended_at: datetime | None          # None = still active
  agent_tool: str                    # "claude-code" | "copilot" | "cline" | "manual"
  project_path: str
  hostname: str
  summary: str | None               # auto-generated after session ends
```

A **session** begins when the observability server starts (or when the first trace arrives after a configurable idle timeout, e.g., 30 minutes). It ends when the server shuts down or the idle timeout expires.

### Trace Hierarchy (within a session)

```
Session
└── ProviderGroup (one per unique provider in session)
     └── ModelGroup (one per unique model per provider)
          └── WorkflowExecution
               id: str (trace_id from OTEL)
               workflow_id: str
               chain_description: str    # e.g., "CachePrimitive >> RetryPrimitive"
               agent_role: str | None    # "backend-engineer" | None
               started_at: datetime
               duration_ms: float
               status: "success" | "error" | "running"
               └── Span (one per primitive call)
                    span_id: str
                    name: str             # primitive class name or function name
                    primitive_type: str | None
                    started_at: datetime
                    duration_ms: float
                    status: "success" | "error"
                    attributes: dict
                    parent_span_id: str | None
```

### Key Fields per Span (from OTEL attributes)

| Field | OTEL Attribute | Description |
|-------|---------------|-------------|
| `provider` | `ai.provider` | Anthropic, OpenRouter, Ollama |
| `model` | `ai.model` | claude-sonnet-4-6, llama-3.1 |
| `agent_role` | `tta.agent.role` | backend-engineer, architect |
| `primitive_type` | `tta.primitive.type` | RetryPrimitive, CachePrimitive |
| `workflow_id` | `tta.workflow.id` | user-defined workflow name |
| `chain` | `tta.workflow.chain` | "CachePrimitive >> RetryPrimitive" |
| `retry_count` | `tta.retry.count` | number of retries attempted |
| `cache_hit` | `tta.cache.hit` | true/false |
| `tokens_used` | `ai.tokens.total` | token count (if provider emits) |
| `cost_usd` | `ai.cost.usd` | estimated cost (if provider emits) |

---

## 5. Dashboard Layout

### 5.1 Overall Structure

```
┌──────────────────────────────────────────────────────────────────┐
│  Header: TTA.dev Observability  ●Connected  [Session: #5 (live)] │
├────────────────┬─────────────────────────────────────────────────┤
│  Sessions      │  Main Panel (context-sensitive)                  │
│  Sidebar       │                                                   │
│  (collapsible) │                                                   │
│                │                                                   │
│  ● Session #5  │                                                   │
│    (now, 12m)  │                                                   │
│  ○ Session #4  │                                                   │
│    (yesterday) │                                                   │
│  ○ Session #3  │                                                   │
│                │                                                   │
├────────────────┴─────────────────────────────────────────────────┤
│  CGC Graph (full width, resizable, collapsible)                   │
│  [Architecture] [Dependencies] [Primitives] [Agents]  Live: ON   │
└──────────────────────────────────────────────────────────────────┘
```

### 5.2 Session Sidebar

- Sessions listed newest-first, active session at top with a live pulse indicator
- Each session shows: agent tool icon, duration, trace count, status (all ok / N errors)
- Clicking a session loads it into the Main Panel

### 5.3 Main Panel — Session View

When a session is selected:

```
Session #5  ●  claude-code  started 12m ago
─────────────────────────────────────────────────────
Provider Tree:
  ▶ Anthropic  (14 calls)
       claude-sonnet-4-6  (14 calls, 2.3s avg)
           backend-engineer  (11)  architect  (3)
  ▶ OpenRouter  (2 calls)
       llama-3.1-70b  (2 calls, 8.1s avg)

Live Metrics:
  Primitives used: RetryPrimitive ×5, CachePrimitive ×3
  Cache hits: 67%   Retries: 2   Errors: 0
  Total tokens: ~4,200   Est. cost: ~$0.012

Recent Spans: [list, clickable, most recent first]
```

### 5.4 Span Detail Panel (slide-in on click)

- Full execution chain: Provider → Model → Agent → Workflow → Primitive
- Span attributes as key/value table
- Error details (if errored)
- Raw OTEL JSON (expandable, for debugging)

### 5.5 CGC Graph — Live Overlay Mode

- Default: static architecture view (existing behavior)
- Live mode ON: nodes visited in current session glow blue; nodes with errors glow red
- Hover: shows execution count + last duration
- Click: filters Main Panel to traces touching that node
- "Heartbeat" pulse on nodes active in the last 30 seconds

---

## 6. API Contract

All endpoints under `/api/v2/` (v1 routes preserved for backward compatibility during transition).

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/v2/sessions` | List all sessions, newest first |
| `GET` | `/api/v2/sessions/current` | Active session (or 404) |
| `GET` | `/api/v2/sessions/{id}` | Session detail + provider tree |
| `GET` | `/api/v2/sessions/{id}/spans` | All spans in a session |
| `GET` | `/api/v2/primitives` | Primitives catalog |
| `GET` | `/api/v2/cgc/{view}` | CGC graph data for a view |
| `GET` | `/api/v2/cgc/live` | Nodes active in current session (for overlay) |
| `GET` | `/api/v2/health` | Server health check |
| `WS`  | `/ws` | Real-time events (session updates, new spans) |

### WebSocket Event Types

```json
{ "type": "span_added",    "session_id": "...", "span": { ... } }
{ "type": "session_start", "session": { ... } }
{ "type": "session_end",   "session_id": "...", "summary": { ... } }
{ "type": "metrics",       "session_id": "...", "metrics": { ... } }
```

---

## 7. Batteries-Included: Auto-Start Mechanism

### 7.1 Entry Point

```bash
uv run python -m ttadev.observability
# OR
uv run python scripts/dashboard.py
```

Both launch the unified server on port 8000 and open the browser.

### 7.2 AGENTS.md Integration — Instruction-Based Start (Q1 decision)

Session auto-start is **instruction-based**: `AGENTS.md` and each agent definition file (e.g., `.github/agents/backend-engineer.agent.md`) include a mandatory "Before You Begin" section that tells agents to start the dashboard as their first action.

```markdown
## Before You Begin
Start the observability dashboard (if not already running):
  uv run python -m ttadev.observability
Dashboard: http://localhost:8000
This gives you and the user live visibility into all workflow executions.
```

This is simpler and more reliable than environment-variable sniffing. Agents that read `AGENTS.md` will run the command at session start. The server is idempotent — if already running, the command exits cleanly with a "already running" message.

**Session boundaries**: A session = one server uptime. Server start → session start. `Ctrl+C` → session end. No idle timeout needed. This is simple, predictable, and matches how developers actually work.

### 7.3 Primitive Auto-Instrumentation

All `InstrumentedPrimitive` subclasses already emit OTEL spans. The dashboard server runs an OTEL collector on `localhost:4317`. Primitives send spans there automatically. No extra code needed in user workflows.

### 7.4 Session Lifecycle

- Session starts when server starts (generates a uuid, records start time)
- Session ends when server shuts down (records end time, writes summary)
- `agent_tool` detected from environment with graceful fallback to "unknown":
  - `CLAUDE_CODE=1` → "claude-code"
  - `TERM_PROGRAM=vscode` + copilot env → "copilot"
  - `TTA_AGENT_TOOL=<name>` env var overrides all detection (documented override)
- Sessions persisted to `.tta/sessions/{id}.json` so history survives server restart

---

## 8. Server Unification

The two existing servers are merged into one canonical implementation:

**Keep**: `ttadev/observability/server.py` (has `TraceCollector`, `CGCIntegration`, clean abstractions)
**Delete**: `ttadev/ui/observability_server.py` (ad-hoc, file-reading approach)

The unified server will:
- Accept OTEL spans on `localhost:4317` (gRPC) AND file-based spans from `~/.tta/traces/*.json`
- Serve the dashboard HTML + static assets
- Manage WebSocket connections
- Implement all `/api/v2/` routes

---

## 9. Dashboard Code Structure

The monolithic `dashboard.html` is split:

```
ttadev/observability/dashboard/
  __init__.py
  server.py              # Unified server (existing, extended)
  session_manager.py     # Session lifecycle, storage, queries
  span_processor.py      # OTEL span → our data model
  cgc_bridge.py          # CGC graph queries + live overlay
  static/
    index.html           # Shell (~100 lines, loads JS modules)
    js/
      app.js             # Main app controller
      session-tree.js    # Sessions sidebar component
      session-detail.js  # Session main panel
      span-detail.js     # Span detail slide-in
      cgc-graph.js       # D3 graph + live overlay (from code-graph.js)
    css/
      dashboard.css      # Extracted styles
```

---

## 10. Success Criteria

| # | Criterion | Verifiable By |
|---|-----------|---------------|
| 1 | Running `uv run python -m ttadev.observability` starts the server with no errors | `uv run python -m ttadev.observability --check` |
| 2 | Dashboard loads in browser with Sessions sidebar visible | Playwright E2E |
| 3 | A `RetryPrimitive` execution appears in the dashboard within 1s | E2E test with demo workflow |
| 4 | Session → Provider → Model hierarchy is navigable via sidebar + main panel | Playwright E2E |
| 5 | CGC graph loads and "Live Overlay" toggle works | Playwright E2E |
| 6 | Clicking a span opens the detail panel with correct fields | Playwright E2E |
| 7 | `/api/v2/sessions` returns valid JSON with correct shape | Unit + integration test |
| 8 | `/api/v2/sessions/current` returns 404 when no active session | Unit test |
| 9 | Old `/api/traces` route still works (backward compat) | Integration test |
| 10 | 100% test coverage on new Python modules | `uv run pytest --cov` |

---

## 11. Out of Scope (v2)

- Authentication / multi-user support
- Cloud/remote dashboard hosting
- Cost tracking beyond estimates from token counts
- Replay of past sessions
- LangFuse or other external APM integration
- Mobile-responsive layout
- Alerting / notifications

---

## 12. Decisions (Signed Off 2026-03-10)

| # | Question | Decision |
|---|----------|----------|
| Q1 | Session boundaries | **Instruction-based start** — `AGENTS.md` tells agents to run the server. Session = server uptime. |
| Q2 | Agent tool detection | **Env detection + `TTA_AGENT_TOOL` override** — try to detect, fall back to "unknown", doc the override |
| Q3 | CGC dependency | **Graceful degradation** — graph shows "CGC not available" if unreachable |
| Q4 | File structure | **`ttadev/observability/dashboard/`** — colocate with the server |
| Q5 | v1 route compat | **Keep v1 routes** until demo scripts updated in Phase 3 tasks |

## 13. Approval

- [x] All Q1–Q5 decisions resolved
- [x] Data model fields reviewed
- [x] API routes reviewed
- [x] Dashboard layout reviewed
- [x] Out-of-scope acceptable

**APPROVED. Proceed to `/plan`.**
