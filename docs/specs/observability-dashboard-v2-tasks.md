# Task Breakdown: Observability Dashboard v2

**Phase**: SDD Phase 3 (`/tasks`)
**Plan**: `docs/specs/observability-dashboard-v2-plan.md`
**Date**: 2026-03-10

Tasks are ordered by dependency (topological sort). No task may begin until all tasks it depends on are ✅.

---

## Group 1 — Foundation (no dependencies)

### Task 1 — `ProcessedSpan` dataclass + `SpanProcessor` (RED)
**Depends on**: nothing
**File**: `tests/unit/test_span_processor.py`

Write failing tests for `SpanProcessor` covering all three input formats and all attribute extractors. Do not write any implementation yet.

**Acceptance tests:**
- `test_from_otel_jsonl_extracts_provider` — OTEL span with `ai.provider = "anthropic"` → `span.provider == "anthropic"`
- `test_from_otel_jsonl_extracts_model` — OTEL span with `ai.model = "claude-sonnet-4-6"` → `span.model == "claude-sonnet-4-6"`
- `test_from_otel_jsonl_extracts_agent_role` — span with `tta.agent.role = "backend-engineer"` → `span.agent_role == "backend-engineer"`
- `test_from_otel_jsonl_missing_fields_fallback` — span with no `ai.provider` → `span.provider == "unknown"`
- `test_from_activity_log_basic` — `{"provider": "github_copilot", "model": "claude-sonnet-4.5", "agent": "architect"}` → correct `ProcessedSpan`
- `test_from_activity_log_no_agent` — `agent: null` → `span.agent_role is None`
- `test_from_agent_tracker_basic` — AgentTracker record → correct `ProcessedSpan`
- `test_extract_primitive_type_retry` — span name `"retry.execute"` → `"RetryPrimitive"`
- `test_extract_primitive_type_cache` — span name `"cache.execute"` → `"CachePrimitive"`
- `test_extract_primitive_type_unknown` — span name `"my_custom_fn"` → `None`
- `test_extract_primitive_type_from_attribute` — `tta.primitive.type = "CircuitBreakerPrimitive"` takes priority over name inference

- [ ] Tests written, all failing (RED confirmed)

---

### Task 2 — `SpanProcessor` implementation (GREEN)
**Depends on**: Task 1
**Files**: `ttadev/observability/span_processor.py`

Implement `ProcessedSpan` dataclass and `SpanProcessor` class until all Task 1 tests pass.

**Acceptance**: All 11 Task 1 tests pass. `uv run ruff check` + `uvx pyright` clean.

- [ ] `ProcessedSpan` dataclass defined with all fields from plan §2.1
- [ ] `SpanProcessor.from_otel_jsonl()` implemented
- [ ] `SpanProcessor.from_activity_log()` implemented
- [ ] `SpanProcessor.from_agent_tracker()` implemented
- [ ] All attribute extractors implemented with fallbacks
- [ ] Primitive type inference table complete (8 patterns from plan §2.2)
- [ ] All Task 1 tests GREEN
- [ ] Ruff + Pyright clean

---

## Group 2 — Core Python (depends on Group 1)

### Task 3 — `SessionManager` (RED)
**Depends on**: Task 2 (`ProcessedSpan`)
**File**: `tests/unit/test_session_manager.py`

Write failing tests for `SessionManager` using a `tmp_path` fixture for file I/O.

**Acceptance tests:**
- `test_start_session_creates_metadata_file` — `start_session()` creates `.tta/sessions/{id}.json` with correct fields
- `test_start_session_returns_session_with_id` — returned `Session.id` is a valid UUID4
- `test_end_session_sets_ended_at` — `end_session()` updates `ended_at` in the persisted file
- `test_get_current_returns_active_session` — after `start_session()`, `get_current()` returns that session
- `test_get_current_returns_none_after_end` — after `end_session()`, `get_current()` returns `None`
- `test_list_sessions_newest_first` — three sessions created sequentially → list is newest-first
- `test_add_span_persists_to_jsonl` — `add_span()` appends to `.tta/sessions/{id}/spans.jsonl`
- `test_get_session_spans_returns_all` — after 3 `add_span()` calls, `get_session_spans()` returns all 3
- `test_get_active_primitive_names_deduplicates` — two spans with same primitive type → list has one entry
- `test_get_recently_active_filters_by_time` — span added 60s ago not included with `within_seconds=30`
- `test_detect_agent_tool_env_override` — `TTA_AGENT_TOOL=copilot` env var → `"copilot"` in session metadata
- `test_detect_agent_tool_fallback` — no env vars set → `"unknown"`

- [ ] Tests written, all failing (RED confirmed)

---

### Task 4 — `SessionManager` implementation (GREEN)
**Depends on**: Task 3
**File**: `ttadev/observability/session_manager.py`

Implement `Session` dataclass and `SessionManager` class until all Task 3 tests pass.

**Acceptance**: All 12 Task 3 tests pass. Ruff + Pyright clean.

- [ ] `Session` dataclass defined
- [ ] Storage layout: `.tta/sessions/{id}.json` + `.tta/sessions/{id}/spans.jsonl`
- [ ] `start_session()` — generates uuid4, detects agent_tool, persists metadata
- [ ] `end_session()` — sets `ended_at`, re-persists
- [ ] `get_current()` — returns session without `ended_at`, or `None`
- [ ] `list_sessions()` — reads all `{id}.json` files, sorts by `started_at` desc
- [ ] `add_span()` — appends `ProcessedSpan` as JSON line to spans.jsonl
- [ ] `get_session_spans()` — reads and deserializes spans.jsonl
- [ ] `get_active_primitive_names()` — unique primitive types across all session spans
- [ ] `get_recently_active()` — filters spans by `started_at` within N seconds
- [ ] `_detect_agent_tool()` — checks `TTA_AGENT_TOOL` env, then `CLAUDE_CODE`, then `TERM_PROGRAM`, else `"unknown"`
- [ ] All Task 3 tests GREEN
- [ ] Ruff + Pyright clean

---

### Task 5 — `CGCIntegration` extensions (RED → GREEN)
**Depends on**: nothing (parallel-safe with Tasks 3–4)
**Files**: `tests/unit/test_cgc_integration_extended.py`, `ttadev/observability/cgc_integration.py`

Write tests, then implement. Can be done as combined RED/GREEN since CGC is mocked.

**Acceptance tests:**
- `test_is_available_returns_false_on_timeout` — mock CGC to raise `asyncio.TimeoutError` → `is_available()` returns `False`
- `test_is_available_returns_false_on_exception` — mock CGC to raise `ConnectionError` → `is_available()` returns `False`
- `test_is_available_returns_true_on_success` — mock CGC returns stats dict → `is_available()` returns `True`
- `test_get_live_nodes_maps_primitive_names` — input `["RetryPrimitive"]` → returns list containing a node with `name == "RetryPrimitive"` (or empty list if CGC not available — no crash)
- `test_is_available_uses_3s_timeout` — verify `asyncio.wait_for` is called with `timeout=3.0`

**Implementation**: add `is_available()` and `get_live_nodes()` to `CGCIntegration`.

- [ ] Tests written
- [ ] `is_available()` implemented with 3s timeout and broad exception catch
- [ ] `get_live_nodes()` implemented (returns empty list gracefully if CGC unavailable)
- [ ] All 5 tests GREEN
- [ ] Ruff + Pyright clean

---

## Group 3 — Server Integration (depends on Groups 1–2)

### Task 6 — `server.py` v2 routes + session wiring + ingestion loop
**Depends on**: Tasks 2, 4, 5
**File**: `ttadev/observability/server.py`

Extend `ObservabilityServer` with v2 routes, session lifecycle, static file serving, and the file ingestion loop.

**Sub-tasks (all verified by Task 7 integration tests):**

- [ ] `ObservabilityServer.__init__` instantiates `SessionManager` and `SpanProcessor`
- [ ] `ObservabilityServer.__init__` registers all `/api/v2/` routes (list from plan §2.4)
- [ ] `/api/v2/health` returns `{"status": "ok", "session_id": "...", "cgc_available": bool}`
- [ ] `/api/v2/sessions` returns `list[Session]` newest-first (JSON-serializable)
- [ ] `/api/v2/sessions/current` returns current session or 404
- [ ] `/api/v2/sessions/{id}` returns session + provider tree summary
- [ ] `/api/v2/sessions/{id}/spans` returns all `ProcessedSpan`s for that session
- [ ] `/api/v2/cgc/{view}` delegates to `CGCIntegration`, returns `{"available": false}` if CGC down
- [ ] `/api/v2/cgc/live` returns list of currently active primitive names for current session
- [ ] `/api/v2/primitives` returns primitives catalog (static list from existing logic)
- [ ] Static file route: `GET /static/...` serves `ttadev/observability/dashboard/` directory
- [ ] `start()` calls `session_manager.start_session()` before accepting requests
- [ ] `stop()` calls `session_manager.end_session()`
- [ ] `_file_ingestion_loop()` polls every 1s:
  - `.observability/traces.jsonl` (OTEL) → `SpanProcessor.from_otel_jsonl()`
  - `~/.tta/traces/*.json` (ActivityLogger) → `SpanProcessor.from_activity_log()`
  - `.observability/agents/current_session.jsonl` (AgentTracker) → `SpanProcessor.from_agent_tracker()`
- [ ] New spans broadcast via WebSocket as `{"type": "span_added", "session_id": "...", "span": {...}}`
- [ ] `_handle_dashboard()` serves `ttadev/observability/dashboard/index.html`
- [ ] All v1 routes (`/api/traces`, `/api/cgc/stats`, etc.) preserved unchanged
- [ ] Ruff + Pyright clean

---

### Task 7 — Integration tests for v2 server
**Depends on**: Task 6
**Files**: `tests/integration/test_server_v2.py`, `tests/integration/test_file_ingestion.py`

**`test_server_v2.py` acceptance tests:**
- `test_health_endpoint` — `GET /api/v2/health` returns 200 with `status == "ok"`
- `test_sessions_endpoint_empty` — fresh server → `GET /api/v2/sessions` returns `[]`
- `test_current_session_exists` — server started → `GET /api/v2/sessions/current` returns 200 with a session object
- `test_session_detail_endpoint` — `GET /api/v2/sessions/{current_id}` returns correct session
- `test_session_spans_empty` — no spans yet → `GET /api/v2/sessions/{id}/spans` returns `[]`
- `test_cgc_live_endpoint` — `GET /api/v2/cgc/live` returns 200 (either data or `{"available": false}`)
- `test_primitives_endpoint` — `GET /api/v2/primitives` returns non-empty list
- `test_v1_traces_still_works` — `GET /api/traces` returns 200 (backward compat)
- `test_dashboard_served` — `GET /` returns HTML containing `TTA.dev`
- `test_websocket_connects` — WS `/ws` connects and receives `initial_state` message

**`test_file_ingestion.py` acceptance tests:**
- `test_otel_jsonl_ingested` — write a valid OTEL span to `.observability/traces.jsonl`, wait 2s → `GET /api/v2/sessions/{id}/spans` includes it
- `test_activity_log_ingested` — write a valid JSON file to `~/.tta/traces/`, wait 2s → span appears in session
- `test_duplicate_spans_not_ingested_twice` — same file content read twice → only one span in session

- [ ] All integration tests GREEN
- [ ] Server starts and stops cleanly in test fixtures

---

## Group 4 — Entry Point + AGENTS.md (parallel-safe)

### Task 8 — `__main__.py` + `pyproject.toml`
**Depends on**: Task 6
**Files**: `ttadev/observability/__main__.py`, `ttadev/pyproject.toml`

- [ ] `__main__.py` written per plan §2.5
- [ ] `_port_in_use()` correctly detects occupied port
- [ ] If port free: starts server, prints URL, opens browser
- [ ] If port in use: prints "already running" message, opens browser, exits 0
- [ ] `pyproject.toml` adds `ttadev-dashboard = "ttadev.observability.__main__:main"` to `[project.scripts]`
- [ ] `uv run python -m ttadev.observability --help` (or just running it) does not crash on import

**Acceptance test** (`tests/unit/test_main_entry.py`):
- `test_port_in_use_detects_open_port` — bind a socket, call `_port_in_use(port)` → `True`
- `test_port_in_use_detects_free_port` — no socket on port → `False`

- [ ] Tests GREEN, Ruff + Pyright clean

---

### Task 9 — `AGENTS.md` + agent file updates
**Depends on**: nothing (documentation only)
**Files**: `AGENTS.md`, `.github/agents/*.agent.md`

Add "Before You Begin" section to each file per plan §6.

- [ ] `AGENTS.md` — "Before You Begin" block added near top (after intro paragraph, before Quick Reference table)
- [ ] `.github/agents/backend-engineer.agent.md` — section added
- [ ] `.github/agents/frontend-engineer.agent.md` — section added
- [ ] `.github/agents/devops-engineer.agent.md` — section added
- [ ] `.github/agents/testing-specialist.agent.md` — section added
- [ ] `.github/agents/observability-expert.agent.md` — section added
- [ ] `.github/agents/architect.agent.md` — section added
- [ ] Content is identical across all files (copy-paste consistent)

---

## Group 5 — Frontend (depends on Group 3)

### Task 10 — `dashboard/index.html` + `dashboard/css/dashboard.css`
**Depends on**: Task 6 (static file route must exist)
**Files**: `ttadev/observability/dashboard/index.html`, `ttadev/observability/dashboard/css/dashboard.css`

- [ ] `index.html` is the lean shell from plan §2.6 (~100 lines max)
- [ ] Loads D3.js from CDN, loads `dashboard.css`, loads `app.js` as `type="module"`
- [ ] Has exactly these placeholder elements: `#app-header`, `#session-tree`, `#session-detail`, `#span-detail` (hidden), `#cgc-graph-section`
- [ ] `dashboard.css` migrated and cleaned from `ttadev/ui/dashboard.html` inline styles
- [ ] Dark purple theme preserved (`#0a0e27` background, `#667eea` accent)
- [ ] CSS uses sensible class names (not inline styles as in old dashboard)
- [ ] `GET /` → browser renders the HTML shell without JS errors in console

---

### Task 11 — `dashboard/js/app.js`
**Depends on**: Task 10
**File**: `ttadev/observability/dashboard/js/app.js`

Main controller — owns WebSocket connection, event bus, and header rendering.

- [ ] Connects to `ws://{host}/ws` on load
- [ ] Implements lightweight `EventEmitter` (on/emit) used by all other modules
- [ ] Renders header: title, connection status indicator, current session badge
- [ ] On WS open: emits `connected` event, updates header status to "Connected"
- [ ] On WS close: emits `disconnected`, updates header, attempts reconnect (max 5, exponential backoff)
- [ ] On WS message `span_added`: emits `spanAdded` with span data
- [ ] On WS message `session_start`: emits `sessionStarted`
- [ ] On WS message `session_end`: emits `sessionEnded`
- [ ] Fetches `/api/v2/health` on load; if `cgc_available: false` emits `cgcUnavailable`
- [ ] Exports `app` singleton (for other modules to import)

---

### Task 12 — `dashboard/js/session-tree.js`
**Depends on**: Task 11
**File**: `ttadev/observability/dashboard/js/session-tree.js`

Sessions sidebar component.

- [ ] On init: fetches `GET /api/v2/sessions`, renders list in `#session-tree`
- [ ] Active session shown at top with pulsing green dot
- [ ] Each session item shows: agent tool icon, start time (relative), duration, span count, error count
- [ ] Clicking a session emits `sessionSelected` event on the app event bus
- [ ] On `sessionStarted` WS event: prepends new session to list without full reload
- [ ] On `sessionEnded` WS event: updates session item (removes active indicator)
- [ ] Selected session has visible active state (highlight)

---

### Task 13 — `dashboard/js/session-detail.js`
**Depends on**: Task 11
**File**: `ttadev/observability/dashboard/js/session-detail.js`

Main panel — Provider → Model → Workflow → Agent hierarchy.

- [ ] On `sessionSelected` event: fetches `GET /api/v2/sessions/{id}/spans`, builds and renders hierarchy
- [ ] Hierarchy groups spans by: provider → model → workflow_id (or "direct") → agent_role
- [ ] Each group shows: call count, avg duration, error count
- [ ] Live metrics strip below hierarchy: unique primitives used (with counts), cache hit rate (if applicable), total errors
- [ ] On `spanAdded` event (current session only): incrementally updates the tree without full re-render
- [ ] Clicking a span row in the list emits `spanSelected` event
- [ ] Empty state when no session is selected: "Select a session to view details"

---

### Task 14 — `dashboard/js/span-detail.js`
**Depends on**: Task 11
**File**: `ttadev/observability/dashboard/js/span-detail.js`

Slide-in detail panel for individual spans.

- [ ] On `spanSelected` event: populates and shows `#span-detail` panel
- [ ] Shows execution chain: Provider → Model → Agent → Workflow → Primitive
- [ ] Shows all `ProcessedSpan` fields as a key/value table
- [ ] Error section (if `status == "error"`): shows `attributes.error.message` and `attributes.error.type`
- [ ] "Raw JSON" expandable section showing full span attributes
- [ ] Close button / clicking outside hides the panel (sets `hidden`)

---

### Task 15 — `dashboard/js/cgc-graph.js`
**Depends on**: Tasks 11, 5 (CGC extensions must be deployed)
**File**: `ttadev/observability/dashboard/js/cgc-graph.js`

D3 force-directed graph migrated from `ttadev/ui/static/js/code-graph.js` with live overlay.

- [ ] Migrates existing `CodeGraph` class from `code-graph.js` (keep all existing view types: architecture, dependencies, primitives, agents)
- [ ] Adds `liveOverlay` boolean property (default: false)
- [ ] "Live" toggle button in graph toolbar (replaces the plain view buttons row)
- [ ] When `liveOverlay = true` and a `spanAdded` event fires:
  - Look up the span's `primitive_type` in the current graph nodes
  - Apply `.node-active` CSS class to matching node for 3 seconds, then remove
- [ ] On `cgcUnavailable` event: render "CGC not available — run `uv run cgc mcp start`" message in graph section instead of loading spinner
- [ ] Node tooltip on hover: shows name, type, (in live mode) execution count from current session
- [ ] Clicking a node emits `cgcNodeSelected` with node data; `session-detail.js` listens and filters spans

---

## Group 6 — End-to-End Tests (depends on Group 5)

### Task 16 — Playwright E2E tests
**Depends on**: Tasks 10–15 (full frontend), Task 7 (server)
**File**: `tests/e2e/test_dashboard_v2.py` (new file; existing `test_observability_dashboard.py` is kept but not modified)

**Acceptance tests (from spec §10):**
- `test_dashboard_loads` — `GET /` renders `#session-tree`, `#session-detail`, `#cgc-graph-section` visible
- `test_session_sidebar_shows_active` — current session appears in sidebar with active indicator
- `test_websocket_connects` — connection status in header shows "Connected"
- `test_span_appears_after_primitive_execution` — execute a `RetryPrimitive` via test fixture → span appears in `#session-detail` within 3s
- `test_session_navigation` — create two sessions (via server fixture), click session #1 in sidebar → `#session-detail` updates
- `test_span_detail_panel` — click a span in session-detail → `#span-detail` becomes visible with correct provider shown
- `test_cgc_degradation` — start server with CGC unavailable → `#cgc-graph-section` shows "CGC not available" message, no JS errors
- `test_v1_api_still_works` — `GET /api/traces` returns 200

Server fixture: starts `ObservabilityServer` in a subprocess (same pattern as `test_observability_dashboard.py`).

- [ ] All 8 E2E tests GREEN
- [ ] No JS console errors in any test

---

## Group 7 — Phase 3 Cleanup (non-blocking, do after Group 6)

### Task 17 — Deprecate old server + update demo scripts
**Depends on**: Task 16 (all tests green)
**Files**: `ttadev/ui/observability_server.py`, root-level `demo_*.py` scripts

- [ ] `ttadev/ui/observability_server.py` — add deprecation warning to `main()`:
  ```python
  import warnings
  warnings.warn("ttadev-ui is deprecated. Use `python -m ttadev.observability` instead.", DeprecationWarning)
  ```
- [ ] `demo_agent_tracking.py` — update any hardcoded `/api/active_agents` calls to `/api/v2/sessions/current`
- [ ] `demo_live_observability.py` — same update
- [ ] Verify `uv run pytest` still passes after updates

- [ ] All tests still GREEN after cleanup

---

## Summary

| Group | Tasks | Deliverable |
|-------|-------|------------|
| 1 | 1–2 | `SpanProcessor` + `ProcessedSpan` |
| 2 | 3–5 | `SessionManager` + `CGCIntegration` extensions |
| 3 | 6–7 | Extended server with v2 API + integration tests |
| 4 | 8–9 | Entry point + AGENTS.md updates |
| 5 | 10–15 | Full frontend (HTML/CSS/JS) |
| 6 | 16 | E2E Playwright test suite |
| 7 | 17 | Cleanup / deprecation |

**Total**: 17 tasks across 7 groups.

**Minimum viable milestone** (dashboard usable): Tasks 1–13 complete (Groups 1–5 partial).
**Full spec complete**: Tasks 1–16 complete (Groups 1–6).
**Clean repo**: All 17 tasks complete.
