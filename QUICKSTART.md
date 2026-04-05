# TTA.dev Quickstart

> **AI coding agent?** Jump to the [30-second version](#30-second-version) or read
> [`docs/agent-first.md`](docs/agent-first.md) for agent-specific orientation.

---

## 30-second version

No API key required. Works in any clean clone.

```bash
git clone https://github.com/theinterneti/TTA.dev.git
cd TTA.dev
./setup.sh

# Terminal 1 — start the observability dashboard
uv run python -m ttadev.observability

# Terminal 2 — run the 3-agent showcase (mock LLM, no key needed)
uv run pytest tests/integration/test_multi_agent_proof.py -v
```

Open **http://localhost:8000** to watch live traces stream in.

---

## What just happened

The integration test ran a full `feature_dev` pipeline:

```
DeveloperAgent → QAAgent → SecurityAgent
```

Each step was tracked by the L0 control plane, and every span was written to
`.observability/traces.jsonl` and streamed to the dashboard. No API keys, no
external services — the mock LLM returns deterministic responses so the suite
stays CI-safe.

---

## Working with real code — the showcase pipeline

The showcase is a **Smart Code Reviewer** that runs parallel static analysis plus
an LLM review. It's a realistic demonstration of how to compose TTA.dev primitives:

```bash
# Mock mode — no API key
uv run python -m examples.showcase.main examples/resilient_llm_pipeline.py --mock

# Live mode — set GROQ_API_KEY first (free at https://console.groq.com)
GROQ_API_KEY=gsk_... uv run python -m examples.showcase.main examples/resilient_llm_pipeline.py
```

The showcase wires together `ParallelPrimitive`, `RetryPrimitive`, and
`CircuitBreakerPrimitive` with automatic OTel tracing — see
[`examples/showcase/`](examples/showcase/) for the full source.

---

## Step-by-step setup

### 1 — Clone and install

```bash
git clone https://github.com/theinterneti/TTA.dev.git
cd TTA.dev
./setup.sh          # installs deps via uv, prints the proof path
```

### 2 — (Optional) Configure an LLM provider

Copy `.env.example` to `.env` and fill in **one** provider:

| Provider | Speed | Free? |
|----------|-------|-------|
| **Groq** | Fast | Yes — <https://console.groq.com> |
| **Ollama** | Local | Yes — <https://ollama.ai> |
| **OpenRouter** | Many models | Yes (limited) — <https://openrouter.ai> |

```bash
cp .env.example .env
# edit .env and add e.g. GROQ_API_KEY=gsk_...
```

Everything works without a key using mock mode. A key unlocks live LLM calls.

### 3 — Start the observability dashboard

```bash
uv run python -m ttadev.observability
# → http://localhost:8000
```

Verify it's healthy:

```bash
curl http://localhost:8000/api/v2/health
# {"status": "ok", ...}
```

### 4 — Generate trace data

```bash
uv run python scripts/test_realtime_traces.py
```

Expected:
- script exits with no errors
- `.observability/traces.jsonl` is created
- `/api/v2/spans` returns spans (wait a few seconds — ingestion is async)

```bash
curl http://localhost:8000/api/v2/spans | head
```

### 5 — Run the multi-agent proof (no API key)

```bash
uv run pytest tests/integration/test_multi_agent_proof.py -v
```

This runs a documented, repeatable 3-agent workflow with L0 task tracking. It is
the canonical CI-safe proof path.

---

## Build your first primitive workflow

```python
import asyncio

from ttadev.primitives import (
    CachePrimitive,
    RetryPrimitive,
    TimeoutPrimitive,
    WorkflowContext,
)
from ttadev.primitives.core.base import LambdaPrimitive


async def fetch_data(url: str, ctx: WorkflowContext) -> dict:
    """Simulate a small async operation."""
    await asyncio.sleep(0.1)
    return {"url": url, "status": "ok"}


async def main() -> None:
    base = LambdaPrimitive(fetch_data)

    # Compose: timeout wraps cache wraps retry wraps base
    workflow = TimeoutPrimitive(
        CachePrimitive(
            RetryPrimitive(base),
            cache_key_fn=lambda url, ctx: f"{ctx.workflow_id}:{url}",
            ttl_seconds=60.0,
        ),
        timeout_seconds=5.0,
    )

    ctx = WorkflowContext(workflow_id="my-first-workflow")
    result = await workflow.execute("https://example.test", ctx)
    print(result)  # {"url": "https://example.test", "status": "ok"}


if __name__ == "__main__":
    asyncio.run(main())
```

Save as `my_workflow.py` and run with `uv run python my_workflow.py`.

---

## What this proves

| Claim | How verified |
|-------|-------------|
| `ttadev.primitives` composition API works | `test_multi_agent_proof.py` passes |
| Observability server starts | `GET /api/v2/health` returns `{"status": "ok"}` |
| Trace ingestion works | `/api/v2/spans` returns data after `test_realtime_traces.py` |
| 3-agent workflow runs end-to-end with L0 tracking | Integration test output |

---

## What this does not prove yet

- Every path in older docs is up to date
- The repo is fully production-ready end to end
- All LLM integrations work identically across providers

---

## Next reads

| Topic | File |
|-------|------|
| Full setup story + LLM configuration | [`GETTING_STARTED.md`](GETTING_STARTED.md) |
| Agent-first orientation (for coding agents) | [`docs/agent-first.md`](docs/agent-first.md) |
| All primitives with API reference | [`PRIMITIVES_CATALOG.md`](PRIMITIVES_CATALOG.md) |
| Observability deep-dive | [`docs/observability-quickstart.md`](docs/observability-quickstart.md) |
| Vision vs current reality | [`USER_JOURNEY.md`](USER_JOURNEY.md) |
| Implemented vs planned | [`ROADMAP.md`](ROADMAP.md) |
| Agent instructions (AGENTS.md) | [`AGENTS.md`](AGENTS.md) |

---

## Notes

- If `/api/v2/spans` is empty right after the script runs, wait a few seconds and
  retry. The ingestion loop is asynchronous.
- `examples/demo_workflow.py` and `ttadev/hello_world.py` are lightweight demos.
  The canonical proof path is the integration test above.
- Commands referencing `src/...` or `ttadev/ui/observability_server.py` are stale.
  Use `python -m ttadev.observability` instead.
