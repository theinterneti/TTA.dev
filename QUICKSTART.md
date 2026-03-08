# TTA.dev Quickstart - See It Working in 60 Seconds

Welcome! This guide gets you from zero to a working, observable AI-native app in under a minute.

## Step 1: Clone and Setup (30 seconds)

```bash
git clone https://github.com/theinterneti/TTA.dev.git
cd TTA.dev
./setup.sh
```

**What just happened?**
- ✅ Installed `uv` (fast Python package manager)
- ✅ Created virtual environment
- ✅ Installed TTA.dev primitives
- ✅ Set up observability infrastructure

## Step 2: Run Hello World (15 seconds)

```bash
# Terminal 1: Start the observability dashboard
uv run python src/observability_ui.py

# Terminal 2: Run the hello world app
uv run python src/hello_world.py
```

## Step 3: See It Work (15 seconds)

1. Open http://localhost:8080 in your browser
2. Watch as the hello world app executes workflows
3. See live traces, metrics, and performance data

**You'll see:**
- 🔍 **Live traces** as the app runs
- ⚡ **Performance metrics** (duration, success rate)
- 🔄 **Primitive composition** (Retry → Cache → Transform)
- 📊 **Real-time updates** via WebSocket

## What Just Happened?

You ran a self-observing application that demonstrates:

1. **TTA.dev Primitives**: Sequential → Retry → Cache → Lambda workflow
2. **Batteries-Included Observability**: Zero configuration, instant visibility
3. **AI-Native Patterns**: Built for AI agents and LLM workflows

## Next Steps

### Build Your Own App

```python
from tta_dev.primitives import WorkflowContext, SequentialPrimitive
from tta_dev.observability import trace_workflow

@trace_workflow
async def my_workflow(input_data: str) -> str:
    workflow = SequentialPrimitive("my-app", [
        # Your primitives here
    ])
    ctx = WorkflowContext(workflow_id="my-workflow")
    return await workflow.execute(input_data, ctx)
```

### Explore Primitives

Check out `src/tta_dev/primitives/` to see:
- `RetryPrimitive` - Automatic retries with backoff
- `CachePrimitive` - Smart caching with TTL
- `CircuitBreakerPrimitive` - Fault tolerance
- `ParallelPrimitive` - Concurrent execution
- `ConditionalPrimitive` - Branching logic

### Point Your AI Agent Here

Your AI coding assistant (GitHub Copilot, Claude, Cline) will automatically:
1. Detect `AGENTS.md` and learn TTA.dev patterns
2. Use primitives correctly in generated code
3. Include observability by default

### Read the Docs

- `README.md` - Full feature overview
- `AGENTS.md` - AI agent integration guide
- `src/tta_dev/primitives/README.md` - Primitive API reference

## Common Commands

```bash
# Run tests
uv run pytest -v

# Check code quality
uv run ruff check .
uv run ruff format .
uvx pyright src/

# Start observability UI
uv run python src/observability_ui.py

# Run hello world
uv run python src/hello_world.py
```

## Troubleshooting

**Dashboard shows "No traces yet"?**
- Make sure `hello_world.py` is running in another terminal
- Check that port 8080 is available

**Import errors?**
- Run `uv sync --all-extras` to reinstall dependencies
- Make sure you're using Python 3.11+

**Want to see more traces?**
- Run `hello_world.py` multiple times
- The second run will show caching in action!

---

**🎉 You're now running TTA.dev!** Build something awesome and let us know what you create.
