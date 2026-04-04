# Observability Quickstart

Get the TTA.dev observability dashboard running, watch live traces from a real workflow, and
optionally ship those traces to Langfuse for persistent APM.

---

## 1. Prerequisites

| Requirement | Version |
|-------------|---------|
| Python | 3.11+ |
| uv | latest (`pip install uv`) |
| TTA.dev | installed via `./setup.sh` or `uv sync` |

If you haven't set up the repo yet, follow [GETTING_STARTED.md](../GETTING_STARTED.md) first.

---

## 2. Start the Dashboard

```bash
uv run python -m ttadev.observability
```

The entry point is idempotent — if the server is already running on port 8000 it opens the
browser and exits cleanly instead of erroring.

Expected output:

```
TTA.dev Observability Dashboard → http://localhost:8000
Press Ctrl+C to stop.
```

Your default browser opens automatically. The dashboard shows:

- **Session tree** — each workflow run appears as a session; sessions are listed newest-first
  via `GET /api/v2/sessions`.
- **Span timeline** — the individual primitive executions (spans) inside each session, with
  timing bars and status badges.
- **Live updates** — the dashboard subscribes to `WS /ws` and re-renders whenever a new span
  arrives; no manual refresh required.

> **Tip:** The dashboard reads from `.observability/traces.jsonl` (OTEL spans) and
> `.tta/traces/` (file-based collector). Both files accumulate across restarts — traces are
> not cleared when you stop the server.

---

## 3. Run a Workflow and Watch It

Open a second terminal and run this self-contained snippet. No API key required.

```python
# run_demo.py
import asyncio

import ttadev
from ttadev.primitives.core.base import LambdaPrimitive, WorkflowContext
from ttadev.primitives.recovery.retry import RetryPrimitive

# Enable OTel tracing → writes to .observability/traces.jsonl
ttadev.initialize_observability()


async def flaky_task(data: dict, ctx: WorkflowContext) -> dict:
    """Simulate a task that succeeds on the first attempt."""
    await asyncio.sleep(0.1)
    return {**data, "result": "ok"}


async def main() -> None:
    # Wrap any callable as a primitive, then add retry logic
    base = LambdaPrimitive(flaky_task)
    workflow = RetryPrimitive(base, max_attempts=3)

    ctx = WorkflowContext(workflow_id="observability-demo")
    result = await workflow.execute({"input": "hello"}, ctx)
    print("Result:", result)


asyncio.run(main())
```

```bash
uv run python run_demo.py
```

Switch back to the dashboard tab. Within a few seconds a new session labelled
`observability-demo` appears in the session list, with one span for the `RetryPrimitive`
wrapping the `LambdaPrimitive` execution.

---

## 4. Trace Anatomy

Each span in the dashboard corresponds to one `ProcessedSpan` record. The key fields are:

| Field | What it means |
|-------|---------------|
| `trace_id` | Unique identifier for the entire workflow run — every span in one `workflow.execute()` call shares this ID. |
| `span_id` | Identifier for a **single primitive execution** within that run. |
| `primitive_type` | Which primitive class handled this span — e.g. `RetryPrimitive`, `CachePrimitive`, `CircuitBreakerPrimitive`. Inferred from the span name if not set explicitly. |
| `status` | `"success"`, `"error"`, or `"running"` — whether the primitive completed, failed, or is still executing. |
| `duration_ms` | Wall-clock execution time for this span in milliseconds. |
| `provider` | For LLM-backed primitives: the AI provider (`"Anthropic"`, `"OpenAI"`, `"Ollama"`, …). For pure framework spans the value is `"TTA.dev"`. |
| `model` | Model identifier reported by the provider, e.g. `"claude-3-5-sonnet-20241022"`. `"unknown"` for non-LLM spans. |
| `parent_span_id` | Links child spans to their parent, forming the tree you see in the timeline. `None` on root spans. |
| `agent_role` | Which agent (if any) submitted the span — e.g. `"developer"`, `"qa"`. |

You can inspect the raw data directly:

```bash
# List all sessions (newest first)
curl -s http://localhost:8000/api/v2/sessions | python3 -m json.tool

# Spans for the first session
SESSION_ID=$(curl -s http://localhost:8000/api/v2/sessions | python3 -c \
  "import sys, json; print(json.load(sys.stdin)[0]['id'])")
curl -s "http://localhost:8000/api/v2/sessions/${SESSION_ID}/spans" | python3 -m json.tool
```

---

## 5. Connect Langfuse (Optional — External APM)

[Langfuse](https://cloud.langfuse.com) is an open-source LLM observability platform. TTA.dev
ships a separate integration package `tta-apm-langfuse` that wraps any primitive and
forwards traces.

### 5a. Install the integration

```bash
uv pip install -e ttadev/observability/apm/langfuse
```

### 5b. Set credentials

Create a project at [cloud.langfuse.com](https://cloud.langfuse.com) (free tier available),
then export your keys:

```bash
export LANGFUSE_PUBLIC_KEY="pk-lf-..."
export LANGFUSE_SECRET_KEY="sk-lf-..."
export LANGFUSE_BASE_URL="https://cloud.langfuse.com"   # or your self-hosted URL
```

### 5c. Instrument a primitive

Use `LangFuseIntegration.from_env()` — it reads `LANGFUSE_PUBLIC_KEY`,
`LANGFUSE_SECRET_KEY`, and `LANGFUSE_BASE_URL` automatically:

```python
import asyncio

from tta_apm_langfuse import LangFuseIntegration
from ttadev.primitives.core.base import LambdaPrimitive, WorkflowContext
from ttadev.primitives.recovery.retry import RetryPrimitive


async def my_task(data: dict, ctx: WorkflowContext) -> dict:
    await asyncio.sleep(0.05)
    return {**data, "status": "done"}


async def main() -> None:
    # Reads LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY, LANGFUSE_BASE_URL from env
    apm = LangFuseIntegration.from_env()

    # Instrument the primitive — wraps execute() with @observe tracing
    base = LambdaPrimitive(my_task)
    workflow = apm.instrument(RetryPrimitive(base, max_attempts=2))

    ctx = WorkflowContext(workflow_id="langfuse-demo")
    result = await workflow.execute({"hello": "world"}, ctx)
    print("Result:", result)

    # Flush buffered spans before the process exits
    await apm.aflush()


asyncio.run(main())
```

### 5d. Verify in Langfuse UI

1. Open your Langfuse project → **Traces**.
2. A trace named `RetryPrimitive` (or the custom `trace_name` you passed to `instrument()`)
   should appear within ~10 seconds.
3. Click the trace to see the observation tree with `duration_seconds`, `primitive_type`,
   `status`, and any error metadata.

---

## 5e. Session & User Attribution (Automatic)

When `from_env()` is called, TTA.dev auto-populates **session_id** and **user_id** on the
integration singleton so every observation is attributed without manual setup:

| Attribute | Source | Example value |
|-----------|--------|---------------|
| `user_id` | `get_agent_id()` from `ttadev.observability.agent_identity` | `"copilot"`, `"cline"`, `"adam"` |
| `session_id` | Active L0 run ID from `ControlPlaneService` | `"run-abc123"` |

If either source is unavailable the attribute stays `None` — Langfuse simply omits it.

You can also set them explicitly:

```python
apm = LangFuseIntegration.from_env()
apm.user_id = "my-agent"
apm.session_id = "run-xyz"
```

Or per-call on `create_generation()`:

```python
apm.create_generation(
    name="my-gen", model="llama-3", input=prompt, output=reply,
    session_id="run-xyz", user_id="my-agent",
)
```

---

## 5f. Trace URL Logging

After each `create_generation()` call, the integration logs the Langfuse trace URL at
`DEBUG` level so you can jump straight to the trace in the Langfuse UI:

```
DEBUG tta_apm_langfuse.integration Langfuse trace: https://cloud.langfuse.com/project/...
```

Enable debug logging in your script:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

`create_generation()` also returns the trace ID string (or `None` if tracing is off),
which you can pass to other systems:

```python
trace_id = apm.create_generation(name="gen", model="llama-3", input=p, output=r)
print("Trace ID:", trace_id)
```

---

## 5g. Inline Scoring

Score the current trace immediately after a generation — no `trace_id` bookkeeping required:

```python
import asyncio
from tta_apm_langfuse import LangFuseIntegration


async def main() -> None:
    apm = LangFuseIntegration.from_env()

    # Record the LLM generation
    apm.create_generation(
        name="my-gen",
        model="llama-3.3-70b",
        input="Summarise this article …",
        output="The article discusses …",
    )

    # Score immediately — uses score_current_trace() internally
    apm.score_inline(score=0.9, name="quality", comment="Concise and accurate")

    await apm.aflush()


asyncio.run(main())
```

`score_inline()` fails silently — it will never raise even if Langfuse is unreachable.

---

## 5h. L0 Runs as Langfuse Sessions

When your code calls `ControlPlaneService.claim_task()`, TTA.dev automatically binds the
new run's ID as the Langfuse `session_id` on the global singleton.  Every subsequent LLM
call made during that run therefore appears under a single session in the Langfuse UI —
no manual wiring required.

```python
from ttadev.control_plane.service import ControlPlaneService

svc = ControlPlaneService()
result = svc.claim_task("task-123")
# → Langfuse session_id is now result.run.id
# → All LLM generations within this run are grouped under that session
```

The hook is guarded in a `try/except` so a missing or misconfigured Langfuse installation
never breaks the control plane.

---

## 6. Troubleshooting

| Symptom | Likely cause | Fix |
|---------|-------------|-----|
| Dashboard blank — no sessions listed | No workflow has run yet | Run the snippet from §3 and wait ~5 s for ingestion |
| Port 8000 already in use | Another process (or a previous server instance) | `lsof -ti:8000 \| xargs kill` then restart, or use a different machine port forwarding |
| `curl /api/v2/sessions` returns `[]` after running a workflow | OTel exporter writes asynchronously | Wait 5–10 s, then refresh; check `.observability/traces.jsonl` exists |
| Langfuse auth error (`401 Unauthorized`) | Wrong or expired keys | Double-check `LANGFUSE_PUBLIC_KEY` / `LANGFUSE_SECRET_KEY` match the project |
| Langfuse traces never appear | `aflush()` not called before exit | Add `await apm.aflush()` (or `apm.flush()` in sync code) at the end of your script |
| WebSocket not connecting (`WS /ws` errors in browser console) | Browser extension blocking WebSocket upgrades | Try incognito / private mode, or disable extensions |
| Traces accumulate forever | Expected — JSONL files are append-only | Archive or truncate `.observability/traces.jsonl` and `.tta/traces/` manually when needed |

---

## 7. Available API Endpoints

The running server exposes the following routes (full list in `ttadev/observability/server.py`):

```
GET  /                             → dashboard HTML
GET  /api/v2/health                → health + session info
GET  /api/v2/sessions              → all sessions (newest first)
GET  /api/v2/sessions/current      → active session or 404
GET  /api/v2/sessions/{id}         → session detail + provider summary
GET  /api/v2/sessions/{id}/spans   → all spans for a session
GET  /api/v2/primitives            → primitives catalog
GET  /api/v2/projects              → project sessions (newest first)
WS   /ws                           → real-time span / session events
```

---

## Related docs

- [GETTING_STARTED.md](../GETTING_STARTED.md) — full environment setup
- [PRIMITIVES_CATALOG.md](../PRIMITIVES_CATALOG.md) — all available primitives
- [Langfuse consolidation notes](observability/LANGFUSE_CONSOLIDATION.md)
- [Observability span propagation](observability-span-propagation.md)
