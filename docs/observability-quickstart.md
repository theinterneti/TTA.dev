# Observability Quickstart

Get the TTA.dev observability dashboard running, watch live traces from the showcase pipeline,
and optionally ship those traces to Langfuse for persistent LLM-specific APM.

---

## What You Get

| Layer | What it provides |
|-------|-----------------|
| **Local dashboard** (`http://localhost:8000`) | Real-time session tree, per-span timing bars, primitive-type badges, and a WebSocket feed — zero external services required. |
| **Langfuse** (optional) | Persistent LLM-specific telemetry: token counts, cost estimates, model comparisons, prompt versioning, and inline quality scoring. |

The two layers complement each other: the local dashboard gives you instant visibility during
development; Langfuse gives you long-term analytics and LLM evaluation across runs.

---

## 1. Start the Dashboard

```bash
uv run python -m ttadev.observability
```

The entry point is **idempotent** — if the server is already running on port 8000 it opens the
browser tab and exits cleanly instead of erroring.

Alternatively, use the installed script:

```bash
tta-dashboard
```

Expected output:

```
TTA.dev Observability Dashboard → http://localhost:8000
Press Ctrl+C to stop.
```

Your default browser opens automatically to `http://localhost:8000`. The dashboard shows:

- **Session tree** — each workflow run is a session, listed newest-first (`GET /api/v2/sessions`).
- **Span timeline** — the individual primitive executions inside each session, with timing bars
  and status badges (`"success"` / `"error"` / `"running"`).
- **Live updates** — the UI subscribes to `WS /ws` and re-renders when new spans arrive;
  no manual refresh required.

> **Tip:** The dashboard reads from `.observability/traces.jsonl` (OTEL spans) and
> `.tta/traces/` (file-based collector). Both files accumulate across restarts — traces persist
> when you stop and restart the server.

---

## 2. Run the Showcase

The **Smart Code Reviewer** (`examples/showcase/`) is the canonical demonstration workflow.
It runs two static agents in parallel and then calls an LLM router — all wired with TTA.dev
primitives.

Start the dashboard first (§1), then in a second terminal:

```bash
# Review a file in mock mode — no API key required, fully deterministic
uv run python -m examples.showcase.main examples/showcase/router.py --mock
```

To output raw JSON instead of Markdown:

```bash
uv run python -m examples.showcase.main examples/showcase/router.py --mock --json
```

To use a real LLM (requires at least one of `GROQ_API_KEY`, `GEMINI_API_KEY`, or a running
Ollama instance):

```bash
uv run python -m examples.showcase.main path/to/your_file.py
```

**What you'll see in the terminal:**

```markdown
# Code Review: `router.py`

## Security Review
✅ No issues detected.

## Quality Review
- Line 55: `_make_smart_primitive` is missing a return type annotation
...

## LLM Review
[MockLLM/reviewer] Reviewed 90 lines.
No issues found (mock mode — attach an API key for real analysis).
```

Switch to the dashboard tab. Within a few seconds a new session labelled
`showcase-router` appears in the session list with spans for each primitive.

---

## 3. Interpreting Traces

### Span hierarchy

The showcase produces the following span tree for each file review:

```
showcase-{filename}          ← WorkflowContext.workflow_id (root trace)
├── ParallelPrimitive        ← static agents run concurrently
│   ├── SecurityAgent        ← scans for hardcoded secrets, eval/exec, SQL injection
│   └── QAAgent              ← checks docstrings, type hints, line length
└── FallbackPrimitive        ← LLM router with automatic fallback
    └── RetryPrimitive       ← up to 2 retries with 1.5× backoff
        └── smart-router-chat  ← LambdaPrimitive wrapping SmartRouterPrimitive
                                 (Groq → Gemini → Ollama → MockLLM cascade)
```

In `--mock` mode the `FallbackPrimitive` short-circuits directly to `MockLLMPrimitive` and
the `RetryPrimitive`/`smart-router-chat` spans are omitted.

### Key span fields

Each span in the dashboard corresponds to one `ProcessedSpan` record:

| Field | What it means |
|-------|---------------|
| `trace_id` | Shared by every span in one `workflow.execute()` call. |
| `span_id` | Unique to a single primitive execution within that run. |
| `parent_span_id` | Links child spans to their parent, forming the tree. `None` on root spans. |
| `primitive_type` | Which class handled this span — e.g. `ParallelPrimitive`, `RetryPrimitive`, `SecurityAgent`. |
| `status` | `"success"`, `"error"`, or `"running"`. |
| `duration_ms` | Wall-clock time for this span in milliseconds. |
| `provider` | AI provider for LLM spans (`"Groq"`, `"Gemini"`, `"Ollama"`). Framework spans report `"TTA.dev"`. |
| `model` | Model identifier, e.g. `"llama-3.3-70b-versatile"`. `"unknown"` for non-LLM spans. |
| `agent_role` | Which agent submitted the span — e.g. `"developer"`, `"qa"`. |

### What a healthy trace looks like

- `ParallelPrimitive` completes in roughly the time of the **slower** of its two children
  (both agents run concurrently, not sequentially).
- `SecurityAgent` and `QAAgent` are pure-Python static checks — expect `duration_ms < 50`.
- If a real LLM is used, `smart-router-chat` dominates wall time (hundreds of ms to seconds).
- All spans should carry `status: "success"`. An `"error"` status on `FallbackPrimitive`
  means both the primary router **and** the MockLLM fallback failed — extremely unlikely.

### Inspect via API

```bash
# List all sessions (newest first)
curl -s http://localhost:8000/api/v2/sessions | python3 -m json.tool

# Spans for the most recent session
SESSION_ID=$(curl -s http://localhost:8000/api/v2/sessions | \
  python3 -c "import sys, json; print(json.load(sys.stdin)[0]['id'])")
curl -s "http://localhost:8000/api/v2/sessions/${SESSION_ID}/spans" | python3 -m json.tool
```

---

## 4. Connect Langfuse (Optional)

[Langfuse](https://cloud.langfuse.com) is an open-source LLM observability platform. TTA.dev
ships a separate integration package `tta-apm-langfuse` that wraps any primitive and forwards
traces with full LLM metadata (tokens, cost, model comparisons, quality scores).

### 4a. Install the integration

```bash
uv pip install -e ttadev/observability/apm/langfuse
```

### 4b. Set credentials

Create a project at [cloud.langfuse.com](https://cloud.langfuse.com) (free tier available),
then export your keys:

```bash
export LANGFUSE_PUBLIC_KEY="pk-lf-..."
export LANGFUSE_SECRET_KEY="sk-lf-..."
export LANGFUSE_BASE_URL="https://cloud.langfuse.com"   # or your self-hosted URL
```

`from_env()` reads `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`, and `LANGFUSE_BASE_URL`
(falling back to `LANGFUSE_HOST` if `LANGFUSE_BASE_URL` is unset).

### 4c. Instrument a primitive

```python
import asyncio

from tta_apm_langfuse import LangFuseIntegration
from ttadev.primitives.core.base import LambdaPrimitive, WorkflowContext
from ttadev.primitives.recovery.retry import RetryPrimitive


async def my_task(data: dict, ctx: WorkflowContext) -> dict:
    await asyncio.sleep(0.05)
    return {**data, "status": "done"}


async def main() -> None:
    # Reads LANGFUSE_PUBLIC_KEY / LANGFUSE_SECRET_KEY / LANGFUSE_BASE_URL from env
    apm = LangFuseIntegration.from_env()

    # Wrap any primitive — execute() is traced automatically
    base = LambdaPrimitive(my_task)
    workflow = apm.instrument(RetryPrimitive(base, max_attempts=2))

    ctx = WorkflowContext(workflow_id="langfuse-demo")
    result = await workflow.execute({"hello": "world"}, ctx)
    print("Result:", result)

    # Always flush before the process exits
    await apm.aflush()


asyncio.run(main())
```

### 4d. Verify in Langfuse

1. Open your Langfuse project → **Traces**.
2. A trace named `RetryPrimitive` (or the `trace_name` you passed to `instrument()`) appears
   within ~10 seconds.
3. Click the trace to see the observation tree: `duration_seconds`, `primitive_type`, `status`,
   and error metadata on failure.

### 4e. What Langfuse adds vs the local dashboard

| Feature | Local dashboard | Langfuse |
|---------|-----------------|---------|
| Real-time span feed | ✅ | ❌ (async flush) |
| Span tree + timing | ✅ | ✅ |
| Token / cost tracking | ❌ | ✅ |
| Model comparison | ❌ | ✅ |
| Prompt versioning | ❌ | ✅ |
| Inline quality scoring | ❌ | ✅ (`score_inline()`) |
| Long-term retention | file-based | cloud / self-hosted |

### 4f. Session and user attribution (automatic)

`from_env()` auto-populates `session_id` and `user_id` so every observation is attributed
without manual setup:

| Attribute | Source | Example |
|-----------|--------|---------|
| `user_id` | `ttadev.observability.agent_identity.get_agent_id()` | `"copilot"`, `"cline"` |
| `session_id` | Active L0 run ID from `ControlPlaneService` | `"run-abc123"` |

Override explicitly when needed:

```python
apm = LangFuseIntegration.from_env()
apm.user_id = "my-agent"
apm.session_id = "run-xyz"
```

Or per-call on `create_generation()`:

```python
apm.create_generation(
    name="my-gen",
    model="llama-3",
    input=prompt,
    output=reply,
    session_id="run-xyz",
    user_id="my-agent",
)
```

### 4g. Inline scoring

```python
apm.create_generation(
    name="my-gen",
    model="llama-3.3-70b",
    input="Summarise this article …",
    output="The article discusses …",
)
# Score the trace immediately — no trace_id bookkeeping
apm.score_inline(score=0.9, name="quality", comment="Concise and accurate")
await apm.aflush()
```

`score_inline()` is silent on failure — it never raises even if Langfuse is unreachable.

### 4h. Trace URL in logs

After each `create_generation()` call the integration logs the Langfuse trace URL at `DEBUG`
level:

```
DEBUG tta_apm_langfuse.integration Langfuse trace: https://cloud.langfuse.com/project/...
```

Enable it with:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

`create_generation()` also returns the trace ID string (or `None` when tracing is off):

```python
trace_id = apm.create_generation(name="gen", model="llama-3", input=p, output=r)
print("Trace ID:", trace_id)
```

---

## 5. Production Setup

For production environments, route spans to an OpenTelemetry Collector instead of (or in
addition to) the local JSONL file.

### 5a. Configure the OTLP exporter

```bash
export OTEL_EXPORTER_OTLP_ENDPOINT="http://your-collector:4317"
export OTEL_SERVICE_NAME="tta-dev"
export OTEL_TRACES_SAMPLER="parentbased_traceidratio"
export OTEL_TRACES_SAMPLER_ARG="1.0"
```

### 5b. Initialize programmatically

```python
from ttadev.observability.observability_integration.apm_setup import initialize_observability

initialize_observability(
    service_name="tta-dev",
    service_version="1.0.0",
    enable_prometheus=True,   # exposes /metrics on port 9464 for Prometheus scraping
    enable_console_traces=False,  # disable console noise in production
)
```

`initialize_observability()` returns `True` on success and `False` in degraded (no-op) mode
when `opentelemetry-sdk` is not installed — it never raises, so it is safe to call
unconditionally.

### 5c. Prometheus metrics

When `enable_prometheus=True`, a Prometheus scrape endpoint is available at
`http://localhost:9464/metrics`. Key metrics:

| Metric | Type | Description |
|--------|------|-------------|
| `workflow.duration` | Histogram | End-to-end workflow execution time |
| `workflow.success_count` | Counter | Successful completions |
| `workflow.failure_count` | Counter | Failed executions |
| `primitive.retry_count` | Counter | Retries per primitive |
| `cache.hit_rate` | Gauge | Cache hit/miss ratio |

### 5d. Shutdown hook

Always register a shutdown handler to flush pending spans:

```python
import atexit
from ttadev.observability.observability_integration.apm_setup import shutdown_observability

atexit.register(shutdown_observability)
```

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---------|-------------|-----|
| Dashboard blank — no sessions listed | No workflow has run yet | Run the showcase (§2) and wait ~5 s for ingestion |
| Port 8000 already in use | Previous server instance still running | `lsof -ti:8000 \| xargs kill`, then restart |
| `GET /api/v2/sessions` returns `[]` after a run | OTel exporter writes asynchronously | Wait 5–10 s; check `.observability/traces.jsonl` exists |
| Langfuse `401 Unauthorized` | Wrong or expired keys | Verify `LANGFUSE_PUBLIC_KEY` / `LANGFUSE_SECRET_KEY` match your project |
| Langfuse traces never appear | `aflush()` not called before exit | Add `await apm.aflush()` (or `apm.flush()` in sync code) at the end of the script |
| WebSocket errors in browser console | Browser extension blocking WS upgrades | Try incognito mode or disable extensions |
| Traces accumulate indefinitely | JSONL files are append-only by design | Archive or truncate `.observability/traces.jsonl` and `.tta/traces/` manually |

---

## Available API Endpoints

Full route list is in `ttadev/observability/server.py`:

```
GET  /                               → dashboard HTML
GET  /api/v2/health                  → health + session info
GET  /api/v2/sessions                → all sessions (newest first)
GET  /api/v2/sessions/current        → active session or 404
GET  /api/v2/sessions/{id}           → session detail + provider summary
GET  /api/v2/sessions/{id}/spans     → all spans for a session
GET  /api/v2/cgc/{view}              → CGC graph data
GET  /api/v2/cgc/live                → active primitive names (live overlay)
GET  /api/v2/primitives              → primitives catalog
GET  /api/v2/projects                → project sessions (newest first)
GET  /api/v2/projects/{id}           → project session detail
GET  /api/v2/projects/{id}/sessions  → sessions belonging to a project
WS   /ws                             → real-time span / session events
```

---

## Related Docs

- [GETTING_STARTED.md](../GETTING_STARTED.md) — full environment setup
- [QUICKSTART.md](../QUICKSTART.md) — minimal verified proof path
- [PRIMITIVES_CATALOG.md](../PRIMITIVES_CATALOG.md) — all available primitives
- [Langfuse consolidation notes](observability/LANGFUSE_CONSOLIDATION.md)
- [Observability span propagation](observability-span-propagation.md)
- [Agent observability guide](agent-guides/observability-guide.md)
