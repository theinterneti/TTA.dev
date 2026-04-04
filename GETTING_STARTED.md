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

## Step 1.5: Configure your LLM provider

All LLM provider options are documented in `.env.example` — copy it to get started:

```bash
cp .env.example .env
```

Then pick **one** free provider (no credit card required):

| Provider | Speed | Setup |
|----------|-------|-------|
| **Groq** (recommended) | Fast | Get a free key at <https://console.groq.com>, add `GROQ_API_KEY=...` to `.env` |
| **OpenRouter** | Many models | Get a free key at <https://openrouter.ai>, add `OPENROUTER_API_KEY=...` to `.env` |
| **Ollama** (local, no internet) | Medium | Install at <https://ollama.ai>, then `ollama pull <model>` — TTA.dev auto-detects what's installed |

### Installing Ollama

If you choose the local Ollama option (no API key, no internet required for inference), install it first:

**macOS**
```bash
brew install ollama
```

**Linux**
```bash
curl -fsSL https://ollama.ai/install.sh | sh
```

**Windows**

Download and run the installer from <https://ollama.ai>.

**Start the Ollama daemon** (required before pulling models or running TTA.dev):
```bash
ollama serve
```

> On macOS the menu-bar app starts the daemon automatically. On Linux/Windows, run the command above in a separate terminal or configure it as a system service.

**Pull at least one model** (TTA.dev auto-detects what's installed, but needs at least one):
```bash
ollama pull gemma3:4b   # good default — fast and capable
# other options: llama3.2:3b  phi4-mini:latest  qwen2.5:7b
```

**Verify Ollama is working:**
```bash
ollama list   # should show the model(s) you pulled
```

---

TTA.dev automatically picks the first model returned by `ollama list`. To pin a specific model,
set `OLLAMA_MODEL` in your `.env`:

```bash
# Override auto-detection — use whichever model you have pulled
OLLAMA_MODEL=qwen2.5:7b    # or llama3.2:3b, phi4-mini:latest, gemma3:4b …
```

To force local-only mode with Ollama (auto-detects installed model):
```bash
export LLM_FORCE_PROVIDER=ollama
# Optionally pin a model; if unset, the first result of `ollama list` is used:
# export OLLAMA_MODEL=gemma3:4b
```

To verify your configuration:
```bash
uv run tta models advise --task-type coding
```

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
tta workflow run feature_dev --goal "Add a health check endpoint" --track-l0
tta control task show <task_id>
```

## Step 3c: Start the MCP server for coding agents

The TTA.dev MCP server gives coding agents (Claude Desktop, Copilot, Cline, etc.) 43 tools
for code analysis, workflow control, and LLM advisor access:

```bash
# Start in stdio mode (for IDE integration):
uv run tta-mcp

# Start in HTTP mode (for remote access):
uv run tta-mcp --transport sse --port 8080
```

**VS Code / Copilot** — already configured in `.vscode/settings.json`. Reload the window to activate.

**Claude Desktop** — add to `~/Library/Application Support/Claude/claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "tta-dev": {
      "command": "uv",
      "args": ["run", "--directory", "/path/to/TTA.dev", "tta-mcp"]
    }
  }
}
```

## What is still under repair

- some package-local or historical docs still need cleanup outside the canonical proof path
- some partial integrations and knowledge-base features

The lightweight demo scripts below now run with the current APIs, but they are still supplementary
to the canonical proof path above:

- `uv run python examples/demo_workflow.py`
- `uv run python ttadev/hello_world.py`

## Step 3d: Enable Langfuse APM (optional)

Langfuse is the APM integration available in v0.2 — it records execution traces for every workflow
primitive so you can inspect timing, errors, and LLM calls in the Langfuse UI.

> **Note:** The OTel Collector → Tempo → Grafana pipeline is **not** implemented in v0.2.
> Langfuse is the current APM integration. Grafana stack support is planned for a future release.

### 1. Get free Langfuse keys

Sign up at <https://cloud.langfuse.com> (free tier — no credit card required) and copy your
`Public Key` and `Secret Key` from the project settings.

### 2. Add keys to `.env`

```bash
# Langfuse APM — traces your workflow executions
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...
# LANGFUSE_HOST=https://cloud.langfuse.com  # optional, this is the default
```

### 3. Instrument your workflow

```python
from tta_apm_langfuse import LangFuseIntegration

# Reads LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY, LANGFUSE_HOST from env
apm = LangFuseIntegration.from_env()

# Wrap any primitive — tracing is automatic
instrumented = apm.instrument(my_workflow)
result = await instrumented.execute(data, context)
apm.flush()  # ensure traces are sent before process exit
```

Then open <https://cloud.langfuse.com> to see the trace timeline for every execution.

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

## Observability

Start the dashboard with `uv run python -m ttadev.observability` (port 8000). It shows live
session trees, span timelines, and WebSocket-streamed updates as workflows execute. For a
detailed walkthrough — including trace anatomy, Langfuse integration, and troubleshooting —
see 📖 **[docs/observability-quickstart.md](docs/observability-quickstart.md)**.

## Troubleshooting

### `/api/v2/spans` is empty

Wait a few seconds and query again. The server ingests `.observability/traces.jsonl`
asynchronously.

### The browser does not open automatically

Open `http://localhost:8000` manually.

### You hit an older demo command from another doc

Prefer the commands in this file or in `QUICKSTART.md`. Some older demo paths are still being
migrated and tracked in GitHub issues.
