# Technical Plan: Observability Dashboard v2

**Status**: Draft — Awaiting Approval
**Phase**: SDD Phase 2 (`/plan`)
**Spec**: `docs/specs/observability-dashboard-v2.md`
**Date**: 2026-03-10

---

## 1. Packages Affected

| Package / Module | Change |
|-----------------|--------|
| `ttadev/observability/server.py` | **Extend** — add v2 API routes, static file serving, session wiring |
| `ttadev/observability/collector.py` | **Unchanged** — existing `TraceCollector` + `ObservabilityCollector` kept as-is |
| `ttadev/observability/cgc_integration.py` | **Extend** — add `is_available()` + `get_live_nodes()` for graceful degradation and live overlay |
| `ttadev/observability/__init__.py` | **Extend** — export new `SessionManager`, `SpanProcessor` |
| `ttadev/pyproject.toml` | **Extend** — add `python -m ttadev.observability` entry point |
| `AGENTS.md` + `.github/agents/*.agent.md` | **Extend** — add "Before You Begin" dashboard start instruction |

**New modules (all under `ttadev/observability/`):**

| New File | Purpose |
|----------|---------|
| `__main__.py` | Entry point — `python -m ttadev.observability`, idempotent, opens browser |
| `session_manager.py` | Session lifecycle, persistence, span indexing, hierarchy queries |
| `span_processor.py` | Normalize spans from OTEL JSONL / `~/.tta/traces/*.json` / agent tracker into unified model |
| `dashboard/index.html` | Lean HTML shell (~100 lines), loads JS modules |
| `dashboard/js/app.js` | Wires all components, owns WebSocket connection |
| `dashboard/js/session-tree.js` | Sessions sidebar — list, active indicator, click-to-select |
| `dashboard/js/session-detail.js` | Main panel — Provider→Model→Workflow hierarchy tree |
| `dashboard/js/span-detail.js` | Slide-in panel — span attributes, chain, error details |
| `dashboard/js/cgc-graph.js` | D3 force graph + live overlay (migrated + extended from `ui/static/js/code-graph.js`) |
| `dashboard/css/dashboard.css` | All styles (migrated + cleaned from `ui/dashboard.html`) |

**Deprecated (not deleted yet — Phase 3):**

| File | Status |
|------|--------|
| `ttadev/ui/observability_server.py` | Deprecated — entry point `ttadev-ui` preserved, routes migrated to v2 server |
| `ttadev/ui/dashboard.html` | Deprecated — stays for v1 `ttadev-ui` script; new dashboard is the default |

---

## 2. New Modules — Design Detail

### 2.1 `session_manager.py`

```python
@dataclass
class Session:
    id: str                    # uuid4
    started_at: str            # ISO 8601
    ended_at: str | None
    agent_tool: str            # "claude-code" | "copilot" | "cline" | "unknown"
    project_path: str
    hostname: str

@dataclass
class ProcessedSpan:
    span_id: str
    trace_id: str
    parent_span_id: str | None
    name: str
    provider: str              # extracted from attributes
    model: str                 # extracted from attributes
    agent_role: str | None     # extracted from attributes
    workflow_id: str | None
    primitive_type: str | None # extracted from span name / attributes
    started_at: str            # ISO 8601
    duration_ms: float
    status: str                # "success" | "error" | "running"
    attributes: dict[str, Any]

class SessionManager:
    def __init__(self, data_dir: Path)

    # Lifecycle
    def start_session(self) -> Session
    def end_session(self) -> None

    # Queries
    def get_current(self) -> Session | None
    def list_sessions(self) -> list[Session]              # newest first
    def get_session(self, id: str) -> Session | None
    def get_session_spans(self, id: str) -> list[ProcessedSpan]

    # Span ingestion (called by server on each new trace)
    def add_span(self, session_id: str, span: ProcessedSpan) -> None

    # For CGC live overlay
    def get_active_primitive_names(self, session_id: str) -> list[str]
    def get_recently_active(self, session_id: str, within_seconds: int = 30) -> list[str]

    # Private
    def _detect_agent_tool(self) -> str     # env detection + TTA_AGENT_TOOL override
    def _persist_session(self, s: Session) -> None   # .tta/sessions/{id}.json
    def _persist_span(self, session_id: str, span: ProcessedSpan) -> None
```

**Storage layout:**
```
.tta/
  sessions/
    {session_id}.json          # Session metadata
    {session_id}/
      spans.jsonl              # Append-only span log
```

No database. All file-based. `list_sessions()` reads the `sessions/` directory and sorts by `started_at`.

---

### 2.2 `span_processor.py`

Three input formats exist in the wild. `SpanProcessor` normalizes all of them into `ProcessedSpan`.

```python
class SpanProcessor:
    # Format 1: OTEL JSONL (.observability/traces.jsonl)
    def from_otel_jsonl(self, raw: dict[str, Any]) -> ProcessedSpan

    # Format 2: ActivityLogger JSON (~/.tta/traces/{uuid}.json)
    def from_activity_log(self, raw: dict[str, Any]) -> ProcessedSpan

    # Format 3: AgentTracker JSONL (.observability/agents/current_session.jsonl)
    def from_agent_tracker(self, raw: dict[str, Any]) -> ProcessedSpan

    # Attribute extractors (shared logic)
    def extract_provider(self, raw: dict[str, Any]) -> str
    def extract_model(self, raw: dict[str, Any]) -> str
    def extract_agent_role(self, raw: dict[str, Any]) -> str | None
    def extract_primitive_type(self, name: str, attrs: dict[str, Any]) -> str | None
```

**OTEL attribute → field mapping:**

| `ProcessedSpan` field | OTEL attribute | Activity log field | Fallback |
|-----------------------|---------------|-------------------|---------|
| `provider` | `ai.provider` | `provider` | `"unknown"` |
| `model` | `ai.model` | `model` | `"unknown"` |
| `agent_role` | `tta.agent.role` | `agent` | `None` |
| `workflow_id` | `tta.workflow.id` | — | `None` |
| `primitive_type` | `tta.primitive.type` | — | inferred from span name |

Primitive type inference (name-based, same logic as existing `extractPrimitiveType` JS function, now in Python):
```python
_PRIMITIVE_PATTERNS = [
    ("retry", "RetryPrimitive"),
    ("circuit", "CircuitBreakerPrimitive"),
    ("cache", "CachePrimitive"),
    ("timeout", "TimeoutPrimitive"),
    ("fallback", "FallbackPrimitive"),
    ("parallel", "ParallelPrimitive"),
    ("sequential", "SequentialPrimitive"),
    ("lambda", "LambdaPrimitive"),
]
```

---

### 2.3 `cgc_integration.py` — Extensions

Add two methods to the existing `CGCIntegration` class:

```python
async def is_available(self) -> bool:
    """Probe CGC MCP server. Returns False on any error (graceful degradation)."""
    try:
        await asyncio.wait_for(self.get_repository_stats(), timeout=3.0)
        return True
    except Exception:
        return False

async def get_live_nodes(self, primitive_names: list[str]) -> list[dict[str, Any]]:
    """Return CGC node stubs for the given primitive class names.
    Used by live overlay — maps runtime primitive names → CGC graph nodes."""
    ...
```

The `is_available()` check is called once at server startup and cached. Result included in `/api/v2/health`.

---

### 2.4 `server.py` — Extensions

Add to `ObservabilityServer.__init__`:

```python
self.session_manager = SessionManager(Path(".tta"))
self.span_processor = SpanProcessor()

# v2 routes
self.app.router.add_get("/api/v2/sessions",          self._v2_sessions)
self.app.router.add_get("/api/v2/sessions/current",  self._v2_session_current)
self.app.router.add_get("/api/v2/sessions/{id}",     self._v2_session_detail)
self.app.router.add_get("/api/v2/sessions/{id}/spans", self._v2_session_spans)
self.app.router.add_get("/api/v2/cgc/{view}",        self._v2_cgc_graph)
self.app.router.add_get("/api/v2/cgc/live",          self._v2_cgc_live)
self.app.router.add_get("/api/v2/health",            self._v2_health)
self.app.router.add_get("/api/v2/primitives",        self._v2_primitives)

# Static assets for new dashboard
self.app.router.add_static("/static", DASHBOARD_DIR / "static")

# v1 routes (compat — preserved, not deleted)
self.app.router.add_get("/api/traces",         self._handle_api_traces)   # existing
self.app.router.add_get("/api/cgc/stats",      self._handle_cgc_stats)    # existing
...
```

Override `_handle_dashboard` to serve the new `dashboard/index.html`.

The `start()` method gains:
```python
async def start(self) -> None:
    self.session = self.session_manager.start_session()
    # ... existing startup ...
    # Poll file-based traces and ingest into session
    asyncio.create_task(self._file_ingestion_loop())
```

The `_file_ingestion_loop` polls:
- `.observability/traces.jsonl` (OTEL spans)
- `~/.tta/traces/*.json` (ActivityLogger files)
- `.observability/agents/current_session.jsonl` (AgentTracker)

New spans are processed via `SpanProcessor`, added to `SessionManager`, and broadcast via WebSocket.

---

### 2.5 `__main__.py`

```python
"""python -m ttadev.observability — idempotent dashboard launcher."""
import asyncio, socket, sys, webbrowser
from pathlib import Path

PORT = 8000

def _port_in_use(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("localhost", port)) == 0

async def _run() -> None:
    from ttadev.observability.server import ObservabilityServer
    server = ObservabilityServer(port=PORT)
    await server.start()
    print(f"TTA.dev Dashboard → http://localhost:{PORT}")
    webbrowser.open(f"http://localhost:{PORT}")
    try:
        await asyncio.Event().wait()
    except (KeyboardInterrupt, asyncio.CancelledError):
        print("\nShutting down...")
        await server.stop()

def main() -> None:
    if _port_in_use(PORT):
        print(f"Dashboard already running → http://localhost:{PORT}")
        webbrowser.open(f"http://localhost:{PORT}")
        sys.exit(0)
    asyncio.run(_run())

if __name__ == "__main__":
    main()
```

---

### 2.6 Frontend — `dashboard/index.html`

Lean HTML shell. All logic is in JS modules.

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>TTA.dev Observability</title>
  <link rel="stylesheet" href="/static/css/dashboard.css">
  <script src="https://d3js.org/d3.v7.min.js"></script>
</head>
<body>
  <header id="app-header"><!-- rendered by app.js --></header>
  <div id="app-layout">
    <nav id="session-tree"><!-- rendered by session-tree.js --></nav>
    <main id="session-detail"><!-- rendered by session-detail.js --></main>
    <aside id="span-detail" hidden><!-- rendered by span-detail.js --></aside>
  </div>
  <section id="cgc-graph-section"><!-- rendered by cgc-graph.js --></section>
  <script type="module" src="/static/js/app.js"></script>
</body>
</html>
```

### 2.7 Frontend — JS Module Responsibilities

| Module | Owns | API calls |
|--------|------|-----------|
| `app.js` | WebSocket, event bus, shared state | `/api/v2/health` |
| `session-tree.js` | Sessions sidebar, selection state | `GET /api/v2/sessions` |
| `session-detail.js` | Provider→Model→Workflow→Agent tree, live metrics | `GET /api/v2/sessions/{id}`, `GET /api/v2/sessions/{id}/spans` |
| `span-detail.js` | Slide-in panel, span attributes | (data passed by app.js event) |
| `cgc-graph.js` | D3 force graph, live overlay toggle | `GET /api/v2/cgc/{view}`, `GET /api/v2/cgc/live` |

Communication between modules uses a lightweight event bus (custom `EventEmitter` in `app.js`) — no external state library.

**WebSocket events handled by `app.js`, re-emitted to components:**
- `span_added` → session-detail.js updates tree; cgc-graph.js pulses node
- `session_start` → session-tree.js prepends new session
- `session_end` → session-tree.js marks session ended

---

## 3. Data Flow

```
Primitive execution (RetryPrimitive)
  ↓ InstrumentedPrimitive emits OTEL span
  ↓ Written to .observability/traces.jsonl

server._file_ingestion_loop() polls (every 1s)
  ↓ SpanProcessor.from_otel_jsonl()
  ↓ → ProcessedSpan
  ↓ SessionManager.add_span(current_session_id, span)
  ↓ Persisted to .tta/sessions/{id}/spans.jsonl
  ↓ WebSocket broadcast → {"type": "span_added", "span": {...}}

Browser: app.js receives span_added
  ↓ session-detail.js: update Provider→Model tree
  ↓ cgc-graph.js: pulse "RetryPrimitive" node (if in current view)
```

---

## 4. Composition with Existing Primitives

The observability primitives already emit OTEL spans via `InstrumentedPrimitive`. **No changes needed to primitives code.** The dashboard is purely a consumer.

Relevant primitive chain example (what the dashboard will visualize):
```python
workflow = CachePrimitive(ttl=3600) >> RetryPrimitive(max_retries=3) >> call_api
result = await workflow.execute(data, WorkflowContext(workflow_id="fetch-user"))
```

This produces spans: `cache.execute`, `retry.execute`, `call_api` — with `tta.workflow.id = "fetch-user"`. The session detail panel will show:

```
Anthropic
  └── claude-sonnet-4-6
       └── fetch-user  (3 spans, 142ms avg)
            ├── CachePrimitive  — hit: false, 0ms
            ├── RetryPrimitive  — retries: 1, 180ms
            └── call_api        — 162ms
```

---

## 5. External Dependencies

No new dependencies required. All needed packages already in `ttadev/pyproject.toml`:

| Package | Already present | Used for |
|---------|----------------|---------|
| `aiohttp` | ✅ | Server, WebSocket |
| `aiofiles` | ✅ (via observability) | Async file I/O |
| `opentelemetry-sdk` | ✅ | OTEL span parsing |
| `mcp` | ✅ (via cgc_integration) | CGC MCP client |

D3.js v7 loaded from CDN (existing pattern in the codebase). No npm build step.

---

## 6. `AGENTS.md` + Agent File Changes

Add the following section to `AGENTS.md` (top of file, after the intro paragraph) and to each file in `.github/agents/`:

```markdown
## Before You Begin

Start the observability dashboard (idempotent — safe to run if already running):

```bash
uv run python -m ttadev.observability
```

Dashboard: http://localhost:8000
This provides live visibility into all primitive executions and workflow sessions.
```

---

## 7. `pyproject.toml` Changes

```toml
[project.scripts]
ttadev = "ttadev.cli:main"
ttadev-ui = "ttadev.ui.observability_server:main"     # preserved (deprecated)
ttadev-dashboard = "ttadev.observability.__main__:main"  # new canonical entry point
```

And add `__main__.py` discovery by ensuring `ttadev/observability/` is in the `packages` list (already is via `observability`).

---

## 8. Test Strategy

### Unit tests (`tests/unit/`)

| Test file | What it tests |
|-----------|--------------|
| `test_session_manager.py` | `start_session()`, `end_session()`, `add_span()`, `list_sessions()`, `get_active_primitive_names()`, agent tool detection |
| `test_span_processor.py` | All three `from_*` methods, each attribute extractor, primitive type inference |
| `test_cgc_integration_extended.py` | `is_available()` returns False on timeout; `get_live_nodes()` maps names → nodes |

### Integration tests (`tests/integration/`)

| Test file | What it tests |
|-----------|--------------|
| `test_server_v2.py` | All `/api/v2/` routes return correct shape; v1 routes still work |
| `test_file_ingestion.py` | Write a `.json` trace file, verify it appears in session within 2s |

### E2E tests (`tests/e2e/` or extend `tests/test_observability_dashboard.py`)

| Test | What it tests |
|------|--------------|
| `test_dashboard_loads` | Dashboard renders with sessions sidebar visible |
| `test_session_appears` | Execute a `RetryPrimitive`, verify span appears in dashboard within 1s |
| `test_session_navigation` | Click a session in sidebar → main panel updates |
| `test_cgc_degradation` | CGC unavailable → graph shows "CGC not available", no crash |
| `test_span_detail` | Click a span → detail panel opens with correct fields |

---

## 9. Migration Path (No Breakage)

| Phase | Action |
|-------|--------|
| **Now (v2 build)** | New routes under `/api/v2/`. New dashboard at `/`. v1 routes preserved. Old `ttadev-ui` still works. |
| **Phase 3 (cleanup)** | Update demo scripts to use `/api/v2/`. Delete `ttadev/ui/observability_server.py`. Merge `ttadev/ui/` static assets into `ttadev/observability/dashboard/`. |

---

## 10. File Map — What Gets Created / Modified

```
CREATED:
  ttadev/observability/__main__.py
  ttadev/observability/session_manager.py
  ttadev/observability/span_processor.py
  ttadev/observability/dashboard/
    index.html
    js/app.js
    js/session-tree.js
    js/session-detail.js
    js/span-detail.js
    js/cgc-graph.js
    css/dashboard.css
  tests/unit/test_session_manager.py
  tests/unit/test_span_processor.py
  tests/unit/test_cgc_integration_extended.py
  tests/integration/test_server_v2.py
  tests/integration/test_file_ingestion.py

MODIFIED:
  ttadev/observability/server.py         (add v2 routes + session wiring + static)
  ttadev/observability/cgc_integration.py (add is_available + get_live_nodes)
  ttadev/observability/__init__.py        (export SessionManager, SpanProcessor)
  ttadev/pyproject.toml                   (add ttadev-dashboard script)
  AGENTS.md                               (add Before You Begin section)
  .github/agents/*.agent.md               (add Before You Begin section)

DEPRECATED (Phase 3 cleanup):
  ttadev/ui/observability_server.py
  ttadev/ui/dashboard.html
```

---

## 11. Risks & Mitigations

| Risk | Mitigation |
|------|-----------|
| CGC MCP process is slow to spawn per-call | `is_available()` cached at startup; live overlay uses lightweight node name matching only |
| Three span formats create edge cases | Dedicated `SpanProcessor` with tests for each format + unknown format fallback |
| D3 graph gets slow with many nodes | Limit live overlay to session primitives (typically <20 unique primitive types) |
| v1 routes used by tests we don't know about | CI runs full test suite; v1 routes are never deleted in this phase |
| File ingestion loop misses spans written before server starts | On startup, ingest all existing files in `.observability/traces.jsonl` and `~/.tta/traces/` retroactively into current session |

---

## 12. Approval Checklist

- [ ] File structure is correct — no missing or extraneous modules
- [ ] `ProcessedSpan` fields cover all data needed by the dashboard
- [ ] Three-format ingestion strategy is acceptable (no fourth source we missed)
- [ ] D3 vanilla JS approach (no framework) is acceptable for the frontend
- [ ] Migration path (v1 preserved, v2 added) is acceptable
- [ ] Test strategy covers the spec's 10 success criteria

**Once approved, proceed to `/tasks`.**
