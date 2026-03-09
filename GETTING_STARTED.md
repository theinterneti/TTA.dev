# Getting Started with TTA.dev

Welcome! This guide walks you through setting up TTA.dev and building your first AI-native application with built-in observability.

## Prerequisites

- **Python 3.11+** (we support 3.11, 3.12, 3.13, 3.14)
- **Git**
- **An AI coding agent** (Claude Desktop, GitHub Copilot CLI, Cline, etc.)

That's it! No databases, no external services, no complex configuration.

## Step 1: Clone and Setup (2 minutes)

```bash
# Clone the repository
git clone https://github.com/theinterneti/TTA.dev.git
cd TTA.dev

# Run the setup script (installs dependencies via uv)
./setup.sh
```

The setup script will:
- Install `uv` (fast Python package manager) if needed
- Create a virtual environment
- Install TTA.dev in editable mode
- Verify the installation

## Step 2: Point Your AI Agent at TTA.dev

TTA.dev works through your AI coding agent. The agent reads our configuration files and automatically starts using the primitives.

### For GitHub Copilot CLI:

```bash
# Already configured! Just start using it:
cd TTA.dev
# Copilot will read .github/copilot-instructions.md and AGENTS.md
```

### For Claude Desktop (via MCP):

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "ttadev": {
      "command": "uv",
      "args": ["run", "python", "-m", "ttadev.mcp_server"],
      "cwd": "/path/to/TTA.dev"
    }
  }
}
```

### For Cline:

Point Cline at the TTA.dev directory. It will read `AGENTS.md` and start using patterns.

## Step 3: Verify Observability Works

Let's verify everything is working by running a demo workflow:

```bash
# Run the demo (it will auto-start the observability dashboard)
uv run python examples/demo_workflow.py
```

You should see:
1. Terminal output showing the workflow executing
2. A browser tab opening to `http://localhost:8000`
3. The dashboard displaying real-time traces

## Understanding What Just Happened

### Auto-Instrumentation

When you imported TTA.dev primitives:

```python
from ttadev.primitives import RetryPrimitive, TimeoutPrimitive
```

TTA.dev automatically:
- Initialized OpenTelemetry tracing
- Started the file-based span exporter
- Launched the observability dashboard (on first use)

**No manual setup required!**

### The Observability Dashboard

Open `http://localhost:8000` to see:

- **Live Traces**: Every workflow execution in real-time
- **Primitive Usage**: Which primitives are being used
- **Performance Metrics**: Duration, success/failure rates
- **Error Tracking**: Stack traces and error details

The dashboard reads from `.observability/traces/` (auto-created markdown files).

## Step 4: Build Your First Workflow

Let's build a simple workflow that fetches data with retries and caching:

```python
# my_workflow.py
import asyncio
from ttadev.primitives import RetryPrimitive, CachePrimitive, TimeoutPrimitive
from ttadev.core import WorkflowContext

async def fetch_data(url: str, ctx: WorkflowContext) -> dict:
    """Simulate API call"""
    print(f"Fetching {url}...")
    await asyncio.sleep(0.5)
    return {"data": "success", "url": url}

async def main():
    # Build resilient workflow with primitives
    workflow = (
        TimeoutPrimitive(timeout_seconds=5.0)
        >> CachePrimitive(ttl=60)
        >> RetryPrimitive(max_attempts=3)
    )
    
    # Execute with context
    ctx = WorkflowContext(workflow_id="my-first-workflow")
    result = await workflow.execute("https://api.example.com/data", ctx)
    
    print(f"Result: {result}")

if __name__ == "__main__":
    asyncio.run(main())
```

Run it:

```bash
uv run python my_workflow.py
```

Watch the observability dashboard - you'll see:
- TimeoutPrimitive wrapping the execution
- CachePrimitive checking for cached results
- RetryPrimitive handling any failures
- Full trace timeline with durations

## Step 5: Let Your AI Agent Build With TTA.dev

Now the magic happens. Tell your AI agent:

> "Build me a web scraper that retries on failure, caches results, and times out after 10 seconds. Use TTA.dev primitives."

The agent will:
1. Read `AGENTS.md` and understand TTA.dev patterns
2. Use primitives like RetryPrimitive, CachePrimitive, TimeoutPrimitive
3. Auto-instrument everything with observability
4. You can watch it work in real-time on the dashboard!

## Common Patterns

### Pattern 1: Resilient API Calls

```python
from ttadev.primitives import RetryPrimitive, CircuitBreakerPrimitive, TimeoutPrimitive

# Protect against flaky APIs
api_workflow = (
    CircuitBreakerPrimitive(failure_threshold=5, timeout_seconds=60)
    >> TimeoutPrimitive(timeout_seconds=10.0)
    >> RetryPrimitive(max_attempts=3, backoff_factor=2.0)
)
```

### Pattern 2: Caching Expensive Operations

```python
from ttadev.primitives import CachePrimitive

# Cache for 1 hour
cached_workflow = CachePrimitive(ttl=3600) >> expensive_operation
```

### Pattern 3: Fallback Strategies

```python
from ttadev.primitives import FallbackPrimitive

# Try primary, fall back to secondary
resilient_workflow = FallbackPrimitive(
    primary=primary_api_call,
    fallback=backup_api_call
)
```

## Next Steps

- **Explore Primitives**: Check [PRIMITIVES_CATALOG.md](PRIMITIVES_CATALOG.md) for all available primitives
- **Read User Journey**: See [USER_JOURNEY.md](USER_JOURNEY.md) for the complete experience
- **Join Community**: Open issues, contribute primitives, share your workflows
- **Build Something**: Use TTA.dev to build your AI-native application!

## Troubleshooting

### Dashboard Not Starting?

```bash
# Manually start the dashboard
uv run python ttadev/observability/server.py
```

### Import Errors?

```bash
# Reinstall in editable mode
uv pip install -e .
```

### Agent Not Using Primitives?

Make sure your agent can read:
- `.github/copilot-instructions.md` (for Copilot)
- `AGENTS.md` (general agent guidance)
- `PRIMITIVES_CATALOG.md` (primitive reference)

## Support

- **Issues**: https://github.com/theinterneti/TTA.dev/issues
- **Discussions**: https://github.com/theinterneti/TTA.dev/discussions
- **Documentation**: All markdown files in the root directory

---

**Welcome to TTA.dev!** 🚀 Build something amazing.
