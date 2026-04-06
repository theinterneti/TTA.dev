"""Observability Server — unified server with v2 session-aware API.

Routes:
  GET  /                          → dashboard HTML
  GET  /static/...                → dashboard static assets
  GET  /api/v2/health             → health + session info
  GET  /api/v2/sessions           → list sessions (newest first)
  GET  /api/v2/sessions/current   → active session or 404
  GET  /api/v2/sessions/{id}      → session detail + provider summary
  GET  /api/v2/sessions/{id}/spans → all spans for a session
  GET  /api/v2/langfuse/trace/{trace_id} → proxy generations + scores for one trace
  GET  /api/v2/langfuse/session/cost     → token counts + estimated cost for current session
  GET  /api/v2/langfuse/scores           → recent quality scores (last 10)
  GET  /api/v2/cgc/{view}         → CGC graph data (graceful degradation)
  GET  /api/v2/cgc/live           → active primitive names for live overlay
  GET  /api/v2/primitives         → primitives catalog
  GET  /api/v2/projects           → list project sessions (newest first)
  GET  /api/v2/projects/{id}      → project session detail
  GET  /api/v2/projects/{id}/sessions → sessions belonging to a project
  GET  /api/v2/agents/active      → currently active agents (live agent panel)
  GET  /api/v2/control/tasks      → all tasks with gate status (L0 control plane)
  GET  /api/v2/control/runs       → active agent runs (L0 control plane)
  GET  /api/v2/control/locks      → active workspace + file locks (L0 control plane)
  GET  /api/v2/control/workflows  → workflow steps with timing (L0 control plane)
  WS   /ws                        → real-time span/session/agent events

  Legacy v1 routes preserved for backward compatibility.
"""

import asyncio
import json
import os
import threading
import time
from dataclasses import asdict
from pathlib import Path
from typing import Any

import httpx
from aiohttp import web

from ttadev.control_plane import ControlPlaneService
from ttadev.control_plane.store import ControlPlaneStore
from ttadev.observability.agent_tracker import AgentTracker
from ttadev.observability.cgc_integration import CGCIntegration
from ttadev.observability.collector import TraceCollector
from ttadev.observability.project_session import ProjectSessionManager
from ttadev.observability.session_manager import SessionManager
from ttadev.observability.span_processor import SpanProcessor

DASHBOARD_DIR = Path(__file__).parent / "dashboard"
_HOME_TTA_TRACES = Path.home() / ".tta" / "traces"
_OTEL_JSONL = Path(".observability/traces.jsonl")
_AGENT_TRACKER_JSONL = Path(".observability/agents/current_session.jsonl")

# Primitives catalog (static — reflects the 8 core primitive families)
_PRIMITIVES_CATALOG = [
    {"name": "RetryPrimitive", "description": "Retry with configurable backoff"},
    {"name": "CachePrimitive", "description": "TTL-based result caching"},
    {"name": "TimeoutPrimitive", "description": "Execution timeout wrapper"},
    {"name": "CircuitBreakerPrimitive", "description": "Circuit breaker pattern"},
    {"name": "FallbackPrimitive", "description": "Fallback on failure"},
    {"name": "ParallelPrimitive", "description": "Parallel execution (| operator)"},
    {"name": "SequentialPrimitive", "description": "Sequential execution (>> operator)"},
    {"name": "LambdaPrimitive", "description": "Wrap any callable as a primitive"},
]

# ---------------------------------------------------------------------------
# Langfuse helpers
# ---------------------------------------------------------------------------

# Approximate USD cost per 1 million tokens for common models.
# Input (prompt) cost, Output (completion) cost.
_MODEL_COSTS_PER_1M: dict[str, dict[str, float]] = {
    "gpt-4o": {"input": 2.50, "output": 10.00},
    "gpt-4o-mini": {"input": 0.15, "output": 0.60},
    "gpt-4-turbo": {"input": 10.00, "output": 30.00},
    "gpt-4": {"input": 30.00, "output": 60.00},
    "gpt-3.5-turbo": {"input": 0.50, "output": 1.50},
    "claude-3-5-sonnet": {"input": 3.00, "output": 15.00},
    "claude-3-5-haiku": {"input": 0.80, "output": 4.00},
    "claude-3-opus": {"input": 15.00, "output": 75.00},
    "claude-3-sonnet": {"input": 3.00, "output": 15.00},
    "claude-3-haiku": {"input": 0.25, "output": 1.25},
    "gemini-1.5-pro": {"input": 1.25, "output": 5.00},
    "gemini-1.5-flash": {"input": 0.075, "output": 0.30},
    "gemini-2.0-flash": {"input": 0.10, "output": 0.40},
}


def _langfuse_creds() -> tuple[str, str, str] | None:
    """Return (host, public_key, secret_key) or None if not configured."""
    public_key = os.environ.get("LANGFUSE_PUBLIC_KEY", "")
    secret_key = os.environ.get("LANGFUSE_SECRET_KEY", "")
    if not public_key or not secret_key:
        return None
    host = os.environ.get("LANGFUSE_HOST", "https://cloud.langfuse.com").rstrip("/")
    return host, public_key, secret_key


def _estimate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    """Return estimated USD cost for the given token counts."""
    model_lower = model.lower()
    # Fuzzy-match: find the longest key that is a substring of the model name
    # (longest wins so "gpt-4o-mini" beats "gpt-4o").
    costs: dict[str, float] | None = None
    best_len = 0
    for key, pricing in _MODEL_COSTS_PER_1M.items():
        if key in model_lower and len(key) > best_len:
            costs = pricing
            best_len = len(key)
    if costs is None:
        return 0.0
    return (input_tokens * costs["input"] + output_tokens * costs["output"]) / 1_000_000


class ObservabilityServer:
    """Production-grade observability server with WebSocket support."""

    def __init__(
        self,
        collector: TraceCollector | None = None,
        port: int = 8000,
        data_dir: Path | None = None,
    ) -> None:
        self.collector = collector or TraceCollector()
        self.cgc = CGCIntegration()
        self.port = port
        self._data_dir = Path(data_dir or Path(".tta"))
        self._session_mgr = SessionManager(self._data_dir)
        self._project_mgr = ProjectSessionManager(self._data_dir)
        self._span_proc = SpanProcessor()
        self._cgc_available: bool = False
        self._cgc_probe_time: float = 0.0  # epoch seconds of last probe
        self._CGC_PROBE_TTL: float = 30.0  # re-probe every 30 s
        # Per-file byte offsets for incremental JSONL reads (O(new lines) not O(total))
        self._otel_jsonl_offset: int = 0
        self._tracker_jsonl_offset: int = 0
        # Activity logs are one JSON file per trace — dedup by filename
        self._ingested_activity_files: set[str] = set()
        # Protects all mutable ingest state accessed from the thread-pool executor.
        # _ingest_all_sync() runs inside run_in_executor(); this lock ensures
        # the offset counters and dedup set are never mutated concurrently.
        self._ingest_lock: threading.Lock = threading.Lock()

        self.app = web.Application()
        self.runner: web.AppRunner | None = None
        self.site: web.TCPSite | None = None
        self._websockets: set[web.WebSocketResponse] = set()
        # Live-agent event tracking: agent_key → last-seen epoch seconds
        self._live_agents: dict[str, float] = {}
        self._agent_tracker = AgentTracker()

        self._register_routes()

    # ------------------------------------------------------------------
    # Route registration
    # ------------------------------------------------------------------

    def _register_routes(self) -> None:
        # v2 routes
        self.app.router.add_get("/api/v2/health", self._v2_health)
        self.app.router.add_get("/api/v2/sessions", self._v2_sessions)
        self.app.router.add_get("/api/v2/sessions/current", self._v2_session_current)
        # NOTE: /sessions/current must be registered BEFORE /sessions/{id}
        self.app.router.add_get("/api/v2/spans", self._v2_all_spans)
        self.app.router.add_get("/api/v2/sessions/{id}/spans", self._v2_session_spans)
        self.app.router.add_get("/api/v2/sessions/{id}", self._v2_session_detail)
        self.app.router.add_get("/api/v2/cgc/live", self._v2_cgc_live)
        self.app.router.add_get("/api/v2/cgc/{view}", self._v2_cgc_graph)
        self.app.router.add_get("/api/v2/primitives", self._v2_primitives)
        self.app.router.add_get("/api/v2/control/ownership", self._v2_control_ownership)
        self.app.router.add_get("/api/v2/control/tasks", self._v2_control_tasks)
        self.app.router.add_get("/api/v2/control/runs", self._v2_control_runs)
        self.app.router.add_get("/api/v2/control/locks", self._v2_control_locks)
        self.app.router.add_get("/api/v2/control/workflows", self._v2_control_workflows)
        self.app.router.add_get("/api/v2/projects", self._v2_projects)
        self.app.router.add_get("/api/v2/projects/{id}/sessions", self._v2_project_sessions)
        self.app.router.add_get("/api/v2/projects/{id}/ownership", self._v2_project_ownership)
        self.app.router.add_get("/api/v2/projects/{id}", self._v2_project_detail)
        self.app.router.add_get("/api/v2/sessions/{id}/ownership", self._v2_session_ownership)
        # NOTE: /agents/active must be registered before any wildcard {id} patterns
        self.app.router.add_get("/api/v2/agents/active", self._v2_agents_active)

        # Langfuse proxy routes — gracefully degrade when credentials not set
        # NOTE: /langfuse/session/cost must be registered before /langfuse/trace/{trace_id}
        self.app.router.add_get("/api/v2/langfuse/session/cost", self._v2_langfuse_session_cost)
        self.app.router.add_get("/api/v2/langfuse/scores", self._v2_langfuse_scores)
        self.app.router.add_get("/api/v2/langfuse/trace/{trace_id}", self._v2_langfuse_trace)

        # Static assets (new dashboard)
        if DASHBOARD_DIR.exists():
            self.app.router.add_static("/static", DASHBOARD_DIR, show_index=False)

        # WebSocket
        self.app.router.add_get("/ws", self._handle_websocket)

        # Dashboard HTML
        self.app.router.add_get("/", self._handle_dashboard)

        # Legacy v1 routes (backward compat — do not delete)
        self.app.router.add_get("/api/traces", self._handle_api_traces)
        self.app.router.add_get("/api/cgc/stats", self._handle_cgc_stats)
        self.app.router.add_get("/api/cgc/primitives", self._handle_cgc_primitives)
        self.app.router.add_get("/api/cgc/agents", self._handle_cgc_agents)
        self.app.router.add_get("/api/cgc/workflows", self._handle_cgc_workflows)

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def _init_state(self) -> None:
        """Start session and probe CGC. Call before accepting requests."""
        # Initialise JSONL offsets to current file sizes so the ingestion loop
        # only picks up spans written *after* this server instance starts.
        # Historical spans belong to prior sessions and are not replayed into
        # the live dashboard — they can be loaded via the sessions API instead.
        with self._ingest_lock:
            if _OTEL_JSONL.exists():
                self._otel_jsonl_offset = _OTEL_JSONL.stat().st_size
            if _AGENT_TRACKER_JSONL.exists():
                self._tracker_jsonl_offset = _AGENT_TRACKER_JSONL.stat().st_size
        self._current_session = self._session_mgr.start_session()
        # Probe CGC in background — don't block server startup or graph requests
        asyncio.create_task(self._probe_cgc())
        asyncio.create_task(self._broadcast_loop())
        asyncio.create_task(self._file_ingestion_loop())
        asyncio.create_task(self._agent_expiry_loop())

    async def _probe_cgc(self) -> None:
        """Background task: probe CGC availability and set the flag."""
        self._cgc_available = await self.cgc.is_available()
        self._cgc_probe_time = time.monotonic()

    async def start(self) -> None:
        """Start the server and the current session."""
        await self._init_state()
        self.runner = web.AppRunner(self.app)
        await self.runner.setup()
        self.site = web.TCPSite(self.runner, "0.0.0.0", self.port)
        await self.site.start()

    async def stop(self) -> None:
        """Stop the server and close the current session."""
        self._session_mgr.end_session()
        for ws in list(self._websockets):
            await ws.close()
        if self.site:
            await self.site.stop()
        if self.runner:
            await self.runner.cleanup()

    # ------------------------------------------------------------------
    # v2 route handlers
    # ------------------------------------------------------------------

    async def _v2_health(self, request: web.Request) -> web.Response:
        current = self._session_mgr.get_current()
        return web.json_response(
            {
                "status": "ok",
                "session_id": current.id if current else None,
                "cgc_available": self._cgc_available,
            }
        )

    async def _v2_sessions(self, request: web.Request) -> web.Response:
        sessions = self._session_mgr.list_sessions()
        return web.json_response([asdict(s) for s in sessions])

    async def _v2_session_current(self, request: web.Request) -> web.Response:
        current = self._session_mgr.get_current()
        if current is None:
            return web.json_response({"error": "No active session"}, status=404)
        return web.json_response(asdict(current))

    async def _v2_session_detail(self, request: web.Request) -> web.Response:
        session_id = request.match_info["id"]
        session = self._session_mgr.get_session(session_id)
        if session is None:
            return web.json_response({"error": "Session not found"}, status=404)

        spans = self._session_mgr.get_session_spans(session_id)
        summary = _build_provider_summary(spans)
        return web.json_response({**asdict(session), "provider_summary": summary})

    async def _v2_all_spans(self, request: web.Request) -> web.Response:
        """Return all spans across all sessions, newest first, with session metadata."""
        sessions = self._session_mgr.list_sessions()
        all_spans: list[dict[str, Any]] = []
        for session in sessions:
            for span in self._session_mgr.get_session_spans(session.id):
                d = asdict(span)
                d["_session_id"] = session.id
                d["_session_tool"] = session.agent_tool
                all_spans.append(d)
        all_spans.sort(key=lambda s: s.get("started_at") or "", reverse=True)
        return web.json_response(all_spans[:1000])

    async def _v2_session_spans(self, request: web.Request) -> web.Response:
        session_id = request.match_info["id"]
        spans = self._session_mgr.get_session_spans(session_id)
        return web.json_response([asdict(s) for s in spans])

    async def _v2_cgc_graph(self, request: web.Request) -> web.Response:
        view = request.match_info["view"]

        # Re-probe CGC in background if TTL expired — don't block this request
        now = time.monotonic()
        if now - self._cgc_probe_time > self._CGC_PROBE_TTL:
            self._cgc_probe_time = now  # reset timer to avoid multiple concurrent probes
            asyncio.create_task(self._probe_cgc())

        if not self._cgc_available:
            # Graceful fallback: build graph from ingested span data
            return web.json_response(self._build_span_graph(view))

        try:
            if view == "primitives":
                raw = await self.cgc.get_primitives_graph()
                data = self._normalize_cgc_graph(raw)
            elif view == "agents":
                agents = await self.cgc.get_agent_files()
                data = {
                    "nodes": [
                        {"name": a.get("name", str(i)), "type": "agent"}
                        for i, a in enumerate(agents)
                    ],
                    "edges": [],
                }
            else:  # architecture / dependencies — span-derived (CGC stats have no node/edge structure)
                data = self._build_span_graph(view)
                data["available"] = True
                return web.json_response(data)
            return web.json_response({**data, "available": True})
        except Exception:
            return web.json_response(self._build_span_graph(view))

    async def _v2_cgc_live(self, request: web.Request) -> web.Response:
        current = self._session_mgr.get_current()
        if current is None:
            return web.json_response({"session_id": None, "active_primitives": []})
        names = self._session_mgr.get_recently_active(current.id, within_seconds=30)
        nodes: list[dict[str, Any]] = []
        if self._cgc_available and names:
            nodes = await self.cgc.get_live_nodes(names)
        return web.json_response(
            {
                "session_id": current.id,
                "active_primitives": names,
                "cgc_nodes": nodes,
            }
        )

    async def _v2_primitives(self, request: web.Request) -> web.Response:
        return web.json_response(_PRIMITIVES_CATALOG)

    async def _v2_agents_active(self, request: web.Request) -> web.Response:
        """Return currently active agents for the live agent activity panel.

        Reads the agent registry and returns agents seen in the last 30 seconds.
        Always returns ``{"agents": [...]}`` — never a 404 or error on empty state.
        """
        loop = asyncio.get_running_loop()
        agents = await loop.run_in_executor(None, self._agent_tracker.get_active_agents_for_api)
        return web.json_response({"agents": agents})

    # ------------------------------------------------------------------
    # Langfuse proxy endpoints
    # ------------------------------------------------------------------

    async def _v2_langfuse_trace(self, request: web.Request) -> web.Response:
        """Proxy generations + scores for a single Langfuse trace.

        Returns ``{"available": false, "reason": "..."}`` when credentials are absent
        or Langfuse is unreachable.  Never raises — always returns valid JSON.
        """
        creds = _langfuse_creds()
        if creds is None:
            return web.json_response(
                {"available": False, "reason": "LANGFUSE_PUBLIC_KEY/SECRET_KEY not configured"}
            )
        host, public_key, secret_key = creds
        trace_id = request.match_info["trace_id"]
        try:
            async with httpx.AsyncClient(auth=(public_key, secret_key), timeout=10.0) as client:
                trace_resp, gens_resp, scores_resp = await asyncio.gather(
                    client.get(f"{host}/api/public/traces/{trace_id}"),
                    client.get(
                        f"{host}/api/public/observations",
                        params={"traceId": trace_id, "type": "GENERATION"},
                    ),
                    client.get(f"{host}/api/public/scores", params={"traceId": trace_id}),
                )
            trace_resp.raise_for_status()
            gens_resp.raise_for_status()
            scores_resp.raise_for_status()
            return web.json_response(
                {
                    "available": True,
                    "trace": trace_resp.json(),
                    "generations": gens_resp.json(),
                    "scores": scores_resp.json(),
                }
            )
        except httpx.TimeoutException:
            return web.json_response({"available": False, "reason": "Langfuse request timed out"})
        except httpx.HTTPStatusError as exc:
            return web.json_response(
                {"available": False, "reason": f"Langfuse HTTP {exc.response.status_code}"}
            )
        except Exception as exc:  # noqa: BLE001
            return web.json_response({"available": False, "reason": str(exc)})

    async def _v2_langfuse_session_cost(self, request: web.Request) -> web.Response:
        """Return token counts and estimated USD cost for the current session.

        Queries the most-recent GENERATION observations from Langfuse (up to 50),
        aggregates token counts per model, and estimates cost.  Always returns
        valid JSON — gracefully degrades when Langfuse is not configured.
        """
        creds = _langfuse_creds()
        if creds is None:
            return web.json_response(
                {"available": False, "reason": "LANGFUSE_PUBLIC_KEY/SECRET_KEY not configured"}
            )
        host, public_key, secret_key = creds
        try:
            async with httpx.AsyncClient(auth=(public_key, secret_key), timeout=10.0) as client:
                resp = await client.get(
                    f"{host}/api/public/observations",
                    params={"type": "GENERATION", "limit": 50},
                )
            resp.raise_for_status()
        except httpx.TimeoutException:
            return web.json_response({"available": False, "reason": "Langfuse request timed out"})
        except httpx.HTTPStatusError as exc:
            return web.json_response(
                {"available": False, "reason": f"Langfuse HTTP {exc.response.status_code}"}
            )
        except Exception as exc:  # noqa: BLE001
            return web.json_response({"available": False, "reason": str(exc)})

        data = resp.json()
        observations = data if isinstance(data, list) else data.get("data", [])

        total_input = 0
        total_output = 0
        model_stats: dict[str, dict[str, Any]] = {}

        for obs in observations:
            usage = obs.get("usage") or {}
            model = obs.get("model") or "unknown"
            inp = int(usage.get("input") or usage.get("promptTokens") or 0)
            out = int(usage.get("output") or usage.get("completionTokens") or 0)
            total_input += inp
            total_output += out

            if model not in model_stats:
                model_stats[model] = {"input_tokens": 0, "output_tokens": 0, "cost_usd": 0.0}
            model_stats[model]["input_tokens"] += inp
            model_stats[model]["output_tokens"] += out
            model_stats[model]["cost_usd"] += _estimate_cost(model, inp, out)

        total_cost = sum(s["cost_usd"] for s in model_stats.values())
        top_models = sorted(
            [{"model": m, **s} for m, s in model_stats.items()],
            key=lambda x: x["cost_usd"],
            reverse=True,
        )[:3]

        return web.json_response(
            {
                "available": True,
                "total_input_tokens": total_input,
                "total_output_tokens": total_output,
                "total_tokens": total_input + total_output,
                "estimated_cost_usd": round(total_cost, 6),
                "top_models": top_models,
            }
        )

    async def _v2_langfuse_scores(self, request: web.Request) -> web.Response:
        """Return the 10 most-recent quality scores from Langfuse.

        Always returns valid JSON — gracefully degrades when Langfuse is not
        configured or unreachable.
        """
        creds = _langfuse_creds()
        if creds is None:
            return web.json_response(
                {"available": False, "reason": "LANGFUSE_PUBLIC_KEY/SECRET_KEY not configured"}
            )
        host, public_key, secret_key = creds
        try:
            async with httpx.AsyncClient(auth=(public_key, secret_key), timeout=10.0) as client:
                resp = await client.get(
                    f"{host}/api/public/scores",
                    params={"limit": 10},
                )
            resp.raise_for_status()
        except httpx.TimeoutException:
            return web.json_response({"available": False, "reason": "Langfuse request timed out"})
        except httpx.HTTPStatusError as exc:
            return web.json_response(
                {"available": False, "reason": f"Langfuse HTTP {exc.response.status_code}"}
            )
        except Exception as exc:  # noqa: BLE001
            return web.json_response({"available": False, "reason": str(exc)})

        data = resp.json()
        scores = data if isinstance(data, list) else data.get("data", [])
        return web.json_response({"available": True, "scores": scores})
        """Return active control-plane ownership summaries."""
        service = ControlPlaneService(self._data_dir)
        return web.json_response({"active": service.list_active_ownership()})

    async def _v2_control_ownership(self, request: web.Request) -> web.Response:
        """Return active control-plane ownership summaries."""
        service = ControlPlaneService(self._data_dir)
        return web.json_response({"active": service.list_active_ownership()})

    def _get_control_store(self) -> ControlPlaneStore:
        """Return a ControlPlaneStore rooted at this server's data directory."""
        return ControlPlaneStore(data_dir=self._data_dir)

    async def _v2_control_tasks(self, request: web.Request) -> web.Response:
        """Return all L0 control-plane tasks with gate status.

        Always returns ``{"tasks": [...]}`` — never 404 or error on empty state.
        """
        loop = asyncio.get_running_loop()

        def _load() -> list[dict]:
            store = self._get_control_store()
            return [t.to_dict() for t in store.list_tasks()]

        tasks = await loop.run_in_executor(None, _load)
        return web.json_response({"tasks": tasks})

    async def _v2_control_runs(self, request: web.Request) -> web.Response:
        """Return all active L0 agent runs.

        Always returns ``{"runs": [...]}`` — never 404 or error on empty state.
        """
        loop = asyncio.get_running_loop()

        def _load() -> list[dict]:
            store = self._get_control_store()
            return [r.to_dict() for r in store.list_runs()]

        runs = await loop.run_in_executor(None, _load)
        return web.json_response({"runs": runs})

    async def _v2_control_locks(self, request: web.Request) -> web.Response:
        """Return all active workspace and file locks.

        Always returns ``{"locks": [...]}`` — never 404 or error on empty state.
        """
        loop = asyncio.get_running_loop()

        def _load() -> list[dict]:
            store = self._get_control_store()
            return [lk.to_dict() for lk in store.list_locks()]

        locks = await loop.run_in_executor(None, _load)
        return web.json_response({"locks": locks})

    async def _v2_control_workflows(self, request: web.Request) -> web.Response:
        """Return workflow steps with timing from tasks that carry workflow tracking data.

        Always returns ``{"workflows": [...]}`` — never 404 or error on empty state.
        """
        loop = asyncio.get_running_loop()

        def _load() -> list[dict]:
            store = self._get_control_store()
            result: list[dict] = []
            for task in store.list_tasks():
                if task.workflow is not None:
                    entry = {
                        "task_id": task.id,
                        "task_title": task.title,
                        "workflow": task.workflow.to_dict(),
                    }
                    result.append(entry)
            return result

        workflows = await loop.run_in_executor(None, _load)
        return web.json_response({"workflows": workflows})

    async def _v2_projects(self, request: web.Request) -> web.Response:
        """Return all project sessions, newest first."""
        projects = self._project_mgr.list()
        return web.json_response([asdict(p) for p in projects])

    async def _v2_project_detail(self, request: web.Request) -> web.Response:
        """Return a single project session by ID."""
        project_id = request.match_info["id"]
        proj = self._project_mgr.get_by_id(project_id)
        if proj is None:
            return web.json_response({"error": "Project not found"}, status=404)
        return web.json_response(asdict(proj))

    async def _v2_project_sessions(self, request: web.Request) -> web.Response:
        """Return all sessions belonging to a project."""
        project_id = request.match_info["id"]
        proj = self._project_mgr.get_by_id(project_id)
        if proj is None:
            return web.json_response({"error": "Project not found"}, status=404)
        all_sessions = self._session_mgr.list_sessions()
        matched = [s for s in all_sessions if s.project_id == project_id]
        return web.json_response([asdict(s) for s in matched])

    async def _v2_project_ownership(self, request: web.Request) -> web.Response:
        """Return active ownership summaries for a single project."""
        project_id = request.match_info["id"]
        proj = self._project_mgr.get_by_id(project_id)
        if proj is None:
            return web.json_response({"error": "Project not found"}, status=404)
        service = ControlPlaneService(self._data_dir)
        return web.json_response(
            {
                "project_id": project_id,
                "active": service.list_active_ownership(project_id=project_id),
            }
        )

    async def _v2_session_ownership(self, request: web.Request) -> web.Response:
        """Return active ownership summaries for a single session."""
        session_id = request.match_info["id"]
        session = self._session_mgr.get_session(session_id)
        if session is None:
            return web.json_response({"error": "Session not found"}, status=404)
        service = ControlPlaneService(self._data_dir)
        return web.json_response(
            {
                "session_id": session_id,
                "active": service.list_active_ownership(session_id=session_id),
            }
        )

    def _build_span_graph(self, view: str) -> dict[str, Any]:
        """Build a graph from ingested span data when CGC is unavailable.

        Returns {available: False, source: "spans", nodes: [...], edges: [...]}
        so the frontend can render something useful regardless of CGC status.
        """
        current = self._session_mgr.get_current()
        spans = self._session_mgr.get_session_spans(current.id) if current else []

        nodes: list[dict[str, Any]] = []
        edges: list[dict[str, Any]] = []

        if view == "primitives":
            # Primitive usage frequency
            counts: dict[str, int] = {}
            for span in spans:
                if span.primitive_type:
                    counts[span.primitive_type] = counts.get(span.primitive_type, 0) + 1
            for prim, count in counts.items():
                nodes.append({"name": prim, "type": "primitive", "count": count})
            # Static catalog entries not yet seen
            seen = {n["name"] for n in nodes}
            for entry in _PRIMITIVES_CATALOG:
                if entry["name"] not in seen:
                    nodes.append({"name": entry["name"], "type": "primitive", "count": 0})

        elif view == "agents":
            # Agent role nodes with provider→agent edges
            roles: dict[str, dict[str, Any]] = {}
            edge_keys: set[tuple[str, str]] = set()
            for span in spans:
                if span.agent_role:
                    role = span.agent_role
                    if role not in roles:
                        roles[role] = {
                            "name": role,
                            "type": "agent",
                            "count": 0,
                            "provider": span.provider,
                            "model": span.model,
                        }
                    roles[role]["count"] += 1
                    key = (span.provider, role)
                    if key not in edge_keys:
                        edge_keys.add(key)
                        edges.append({"source": span.provider, "target": role})
                        if span.provider not in {n["name"] for n in nodes}:
                            nodes.append({"name": span.provider, "type": "provider"})
            nodes.extend(roles.values())

        else:  # architecture / dependencies — provider → model hierarchy
            providers: dict[str, set[str]] = {}
            for span in spans:
                p = span.provider or "unknown"
                m = span.model or "unknown"
                providers.setdefault(p, set()).add(m)

            for provider, models in providers.items():
                nodes.append({"name": provider, "type": "provider"})
                for model in models:
                    node_name = f"{provider}/{model}"
                    nodes.append({"name": node_name, "type": "model"})
                    edges.append({"source": provider, "target": node_name})

        return {"available": False, "source": "spans", "nodes": nodes, "edges": edges}

    def _normalize_cgc_graph(self, raw: dict[str, Any]) -> dict[str, Any]:
        """Normalize CGC Cypher result to {nodes, edges} format for D3."""
        # CGC returns rows; extract unique nodes and relationships
        nodes_map: dict[str, dict[str, Any]] = {}
        edges: list[dict[str, Any]] = []

        rows = raw if isinstance(raw, list) else raw.get("rows", raw.get("data", []))

        for row in rows:
            if not isinstance(row, dict):
                continue
            for key, val in row.items():
                if isinstance(val, dict) and "name" in val:
                    name = val["name"]
                    if name and name not in nodes_map:
                        nodes_map[name] = {
                            "name": name,
                            "type": val.get("labels", [key])[0]
                            if isinstance(val.get("labels"), list)
                            else key,
                        }
                elif isinstance(val, dict) and val.get("type") in ("CALLS", "INHERITS", "IMPORTS"):
                    edges.append(
                        {"source": val.get("startNode", ""), "target": val.get("endNode", "")}
                    )

        return {"nodes": list(nodes_map.values()), "edges": edges}

    # ------------------------------------------------------------------
    # Dashboard + WebSocket
    # ------------------------------------------------------------------

    async def _handle_dashboard(self, request: web.Request) -> web.Response:
        index = DASHBOARD_DIR / "index.html"
        if index.exists():
            return web.Response(text=index.read_text(), content_type="text/html")
        # Minimal fallback while Task 10 builds the real dashboard
        return web.Response(
            text=_FALLBACK_HTML,
            content_type="text/html",
        )

    async def _handle_websocket(self, request: web.Request) -> web.WebSocketResponse:
        ws = web.WebSocketResponse()
        await ws.prepare(request)
        self._websockets.add(ws)

        current = self._session_mgr.get_current()
        await ws.send_json(
            {
                "type": "initial_state",
                "session": asdict(current) if current else None,
                "traces": self.collector.get_all_traces(),
            }
        )

        try:
            async for _ in ws:
                pass
        finally:
            self._websockets.discard(ws)

        return ws

    # ------------------------------------------------------------------
    # Legacy v1 handlers (preserved, not modified)
    # ------------------------------------------------------------------

    async def _handle_api_traces(self, request: web.Request) -> web.Response:
        traces = self.collector.get_all_traces()
        return web.json_response({"traces": traces})

    async def _handle_cgc_stats(self, request: web.Request) -> web.Response:
        try:
            stats = await self.cgc.get_repository_stats()
            return web.json_response(stats)
        except Exception as e:
            return web.json_response({"error": str(e)}, status=500)

    async def _handle_cgc_primitives(self, request: web.Request) -> web.Response:
        try:
            graph = await self.cgc.get_primitives_graph()
            return web.json_response(graph)
        except Exception as e:
            return web.json_response({"error": str(e)}, status=500)

    async def _handle_cgc_agents(self, request: web.Request) -> web.Response:
        try:
            agents = await self.cgc.get_agent_files()
            return web.json_response({"agents": agents})
        except Exception as e:
            return web.json_response({"error": str(e)}, status=500)

    async def _handle_cgc_workflows(self, request: web.Request) -> web.Response:
        try:
            workflows = await self.cgc.get_workflow_files()
            return web.json_response({"workflows": workflows})
        except Exception as e:
            return web.json_response({"error": str(e)}, status=500)

    # ------------------------------------------------------------------
    # Background tasks
    # ------------------------------------------------------------------

    async def _broadcast_loop(self) -> None:
        """Broadcast new traces (v1 collector) to WebSocket clients."""
        queue = self.collector.subscribe()
        try:
            while True:
                message = await queue.get()
                for ws in list(self._websockets):
                    try:
                        await ws.send_json(message)
                    except Exception:
                        self._websockets.discard(ws)
        except asyncio.CancelledError:
            self.collector.unsubscribe(queue)
            raise

    async def _agent_expiry_loop(self) -> None:
        """Emit ``agent-end`` WebSocket events for agents that have gone quiet.

        An agent is considered done when it has not produced a new span for
        30 seconds.  The loop ticks every second so the frontend sees the
        card disappear within ≈1 s of the timeout.
        """
        agent_expiry_seconds = 30.0
        while True:
            try:
                await asyncio.sleep(1)
                now = time.time()
                expired = [
                    k
                    for k, ts in list(self._live_agents.items())
                    if now - ts > agent_expiry_seconds
                ]
                for key in expired:
                    del self._live_agents[key]
                    provider, _, model = key.partition(":")
                    msg = {
                        "type": "agent-end",
                        "agent_role": None,
                        "provider": provider,
                        "model": model,
                    }
                    for ws in list(self._websockets):
                        try:
                            await ws.send_json(msg)
                        except Exception:
                            self._websockets.discard(ws)
            except asyncio.CancelledError:
                raise
            except Exception:
                pass

    async def _file_ingestion_loop(self) -> None:
        """Poll file-based span sources every second and ingest new spans.

        All synchronous I/O runs in a thread-pool executor so the event loop
        is never blocked, even when large JSONL files are present.
        """
        loop = asyncio.get_running_loop()
        while True:
            try:
                await asyncio.sleep(1)
                current = self._session_mgr.get_current()
                if current is None:
                    continue

                new_spans = await loop.run_in_executor(None, self._ingest_all_sync)

                for span in new_spans:
                    # Route to agent-specific session when the span carries an
                    # agent_id; fall back to the current session for older spans.
                    if span.agent_id:
                        target = self._session_mgr.get_or_create_agent_session(
                            span.agent_id,
                            span.agent_tool or "unknown",
                            project_id=span.project_id,
                        )
                        if target.id != current.id:
                            # Notify the frontend if we just discovered a new agent
                            if not self._session_mgr.get_session_spans(target.id):
                                for ws in list(self._websockets):
                                    try:
                                        await ws.send_json(
                                            {"type": "session_start", "session": asdict(target)}
                                        )
                                    except Exception:
                                        self._websockets.discard(ws)
                    else:
                        target = current

                    self._session_mgr.add_span(target.id, span)
                    # Broadcast to WebSocket clients
                    msg = {
                        "type": "span_added",
                        "session_id": target.id,
                        "session_tool": target.agent_tool,
                        "span": asdict(span),
                    }
                    for ws in list(self._websockets):
                        try:
                            await ws.send_json(msg)
                        except Exception:
                            self._websockets.discard(ws)

                    # Emit agent-start / agent-step events for the Live panel
                    if span.provider or span.model:
                        agent_key = f"{span.provider or 'unknown'}:{span.model or 'unknown'}"
                        is_new = agent_key not in self._live_agents
                        self._live_agents[agent_key] = time.time()
                        if is_new:
                            agent_event: dict[str, Any] = {
                                "type": "agent-start",
                                "agent_role": span.agent_role,
                                "provider": span.provider or "unknown",
                                "model": span.model or "unknown",
                                "task": span.name,
                                "span_count": 1,
                                "started_at": span.started_at,
                            }
                        else:
                            agent_event = {
                                "type": "agent-step",
                                "agent_role": span.agent_role,
                                "provider": span.provider or "unknown",
                                "model": span.model or "unknown",
                                "action_type": span.primitive_type or span.name,
                                "span_count": len(self._session_mgr.get_session_spans(target.id)),
                            }
                        for ws in list(self._websockets):
                            try:
                                await ws.send_json(agent_event)
                            except Exception:
                                self._websockets.discard(ws)
            except asyncio.CancelledError:
                raise
            except Exception:
                pass  # Never crash the ingestion loop

    def _ingest_all_sync(self) -> list:
        """Collect new spans from all file-based sources (runs in thread executor).

        Acquires ``_ingest_lock`` so that the mutable offset counters and the
        activity-file dedup set are never read/written concurrently if, for
        example, a future caller schedules multiple executor invocations or
        accesses the state from a different thread.
        """
        with self._ingest_lock:
            spans: list = []
            spans.extend(self._ingest_otel_jsonl())
            spans.extend(self._ingest_activity_logs())
            spans.extend(self._ingest_agent_tracker())
            return spans

    def _ingest_otel_jsonl(self) -> list:
        """Read only the bytes appended since the last call (offset-based)."""
        if not _OTEL_JSONL.exists():
            return []
        spans = []
        try:
            file_size = _OTEL_JSONL.stat().st_size
            if file_size < self._otel_jsonl_offset:
                # File was rotated/truncated — reset and re-read from start
                self._otel_jsonl_offset = 0
            if file_size <= self._otel_jsonl_offset:
                return []
            with _OTEL_JSONL.open("rb") as f:
                f.seek(self._otel_jsonl_offset)
                new_bytes = f.read()
                self._otel_jsonl_offset = f.tell()
            for line in new_bytes.decode("utf-8", errors="replace").splitlines():
                if not line.strip():
                    continue
                try:
                    raw = json.loads(line)
                    spans.append(self._span_proc.from_otel_jsonl(raw))
                except Exception:
                    continue
        except Exception:
            pass
        return spans

    def _ingest_activity_logs(self) -> list:
        if not _HOME_TTA_TRACES.exists():
            return []
        spans = []
        for trace_file in _HOME_TTA_TRACES.glob("*.json"):
            key = trace_file.name
            if key in self._ingested_activity_files:
                continue
            try:
                raw = json.loads(trace_file.read_text())
                spans.append(self._span_proc.from_activity_log(raw))
                self._ingested_activity_files.add(key)
            except Exception:
                continue
        return spans

    def _ingest_agent_tracker(self) -> list:
        """Read only the bytes appended since the last call (offset-based)."""
        if not _AGENT_TRACKER_JSONL.exists():
            return []
        spans = []
        try:
            file_size = _AGENT_TRACKER_JSONL.stat().st_size
            if file_size < self._tracker_jsonl_offset:
                self._tracker_jsonl_offset = 0
            if file_size <= self._tracker_jsonl_offset:
                return []
            with _AGENT_TRACKER_JSONL.open("rb") as f:
                f.seek(self._tracker_jsonl_offset)
                new_bytes = f.read()
                self._tracker_jsonl_offset = f.tell()
            for line in new_bytes.decode("utf-8", errors="replace").splitlines():
                if not line.strip():
                    continue
                try:
                    raw = json.loads(line)
                    spans.append(self._span_proc.from_agent_tracker(raw))
                except Exception:
                    continue
        except Exception:
            pass
        return spans


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------


def _build_provider_summary(spans: list) -> dict[str, Any]:
    """Group spans into provider → model → agent_role tree with counts."""
    tree: dict[str, dict[str, dict[str, int]]] = {}
    for span in spans:
        provider = span.provider
        model = span.model
        role = span.agent_role or "(direct)"
        if provider not in tree:
            tree[provider] = {}
        if model not in tree[provider]:
            tree[provider][model] = {}
        tree[provider][model][role] = tree[provider][model].get(role, 0) + 1
    return tree


# ------------------------------------------------------------------
# Fallback HTML (used until Task 10 creates dashboard/index.html)
# ------------------------------------------------------------------

_FALLBACK_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>TTA.dev Observability</title>
  <style>
    body { font-family: system-ui, sans-serif; background: #0a0e27; color: #e0e6ed;
           display: flex; align-items: center; justify-content: center; height: 100vh; margin: 0; }
    .card { text-align: center; padding: 40px; background: #1a1f3a; border-radius: 12px; }
    h1 { color: #667eea; margin-bottom: 8px; }
    .status { color: #10b981; font-size: 0.9em; margin-top: 12px; }
    #ws-status { color: #ef4444; }
  </style>
</head>
<body>
  <div class="card">
    <h1>TTA.dev Observability</h1>
    <p>Dashboard building... v2 UI loads from <code>dashboard/index.html</code></p>
    <p class="status">Server: <strong>running</strong> &nbsp;|&nbsp; WebSocket: <span id="ws-status">connecting...</span></p>
  </div>
  <script>
    const wsProto = location.protocol === 'https:' ? 'wss:' : 'ws:';
    const ws = new WebSocket(`${wsProto}//${location.host}/ws`);
    ws.onopen = () => { document.getElementById('ws-status').textContent = 'connected'; document.getElementById('ws-status').style.color = '#10b981'; };
    ws.onclose = () => { document.getElementById('ws-status').textContent = 'disconnected'; };
  </script>
</body>
</html>"""
