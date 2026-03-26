# Getting Started with TTA.dev

This guide is about the **current repository reality**, not the full long-term vision.

TTA.dev already has a meaningful core: composable primitives, a local observability server, and a
large automated test surface. It does **not** yet mean every historical demo and every aspirational
feature in the repo is fully aligned.

## Prerequisites

- **Python 3.11+**
- **Git**
- an AI coding agent if you want to explore the repo with Copilot, Claude Code, Cline, or similar

## Step 1: Clone and setup

```bash
git clone https://github.com/theinterneti/TTA.dev.git
cd TTA.dev
./setup.sh
```

The setup script installs dependencies with `uv` and prints the currently supported proof path.

## Step 2: Point your coding agent at the repo

Today the most reliable path is simply opening the repository with your coding agent so it can
read:

- `AGENTS.md`
- `.github/copilot-instructions.md`
- `PRIMITIVES_CATALOG.md`

That gives the agent the current repo conventions and workflow patterns.

## Step 3: Verify the current proof path

In terminal 1, start the observability server:

```bash
uv run python -m ttadev.observability
```

In terminal 2, generate trace data with the currently working script:

```bash
uv run python scripts/test_realtime_traces.py
```

Then verify ingestion:

```bash
curl http://localhost:8000/api/v2/health
curl http://localhost:8000/api/v2/spans | head
```

Expected results:

1. the server is reachable on `http://localhost:8000`
2. `scripts/test_realtime_traces.py` exits successfully
3. `.observability/traces.jsonl` exists
4. `/api/v2/spans` returns ingested spans after a short delay

## What this proves

- the current `ttadev.primitives` API can execute a basic workflow
- the current observability entrypoint is `python -m ttadev.observability`
- trace ingestion into the v2 API is functioning

## Step 3b: Run the multi-agent workflow proof (no API key needed)

```bash
uv run pytest tests/integration/test_multi_agent_proof.py -v
```

This proves a 3-agent `feature_dev` workflow (developer → qa → security) with full L0 control-plane
task/step tracking. Uses a deterministic mock LLM — no API keys needed.

To explore via the CLI (requires Ollama or `OPENROUTER_API_KEY`):

```bash
tta workflow run feature_dev --goal "Add a health check endpoint" --track-l0 --no-confirm
tta control task show <task_id>
```

## What is still under repair

- some package-local or historical docs still need cleanup outside the canonical proof path
- some partial integrations and knowledge-base features

The lightweight demo scripts below now run with the current APIs, but they are still supplementary
to the canonical proof path above:

- `uv run python examples/demo_workflow.py`
- `uv run python ttadev/hello_world.py`

## Step 4: Build a small workflow with the current API

```python
import asyncio

from ttadev.primitives import CachePrimitive, RetryPrimitive, TimeoutPrimitive
from ttadev.primitives.core.base import LambdaPrimitive, WorkflowContext


async def fetch_data(url: str, ctx: WorkflowContext) -> dict:
    """Simulate a small async operation."""
    await asyncio.sleep(0.2)
    return {"url": url, "status": "ok"}


async def main() -> None:
    base = LambdaPrimitive(fetch_data)
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
    print(result)


if __name__ == "__main__":
    asyncio.run(main())
```

## Next steps

- read [`QUICKSTART.md`](QUICKSTART.md) for the shortest verified flow
- read [`USER_JOURNEY.md`](USER_JOURNEY.md) for vision vs current reality
- read [`ROADMAP.md`](ROADMAP.md) for what is implemented, partial, and planned
- inspect [`scripts/test_realtime_traces.py`](scripts/test_realtime_traces.py) as the current
  working example

## Troubleshooting

### `/api/v2/spans` is empty

Wait a few seconds and query again. The server ingests `.observability/traces.jsonl`
asynchronously.

### The browser does not open automatically

Open `http://localhost:8000` manually.

### You hit an older demo command from another doc

Prefer the commands in this file or in `QUICKSTART.md`. Some older demo paths are still being
migrated and tracked in GitHub issues.
