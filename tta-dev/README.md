# TTA.dev - Batteries-Included Workflow Framework

**Reliable workflow primitives + automatic observability for AI coding agents**

## Quick Start

```bash
# Clone and setup
git clone https://github.com/yourusername/TTA.dev
cd TTA.dev
./setup.sh

# Start observability UI
tta-dev-ui

# Point your AI agent at this repo - it auto-detects AGENTS.md and starts using primitives
```

## What You Get

### 1. Workflow Primitives
Production-ready building blocks that just work:

```python
from tta_dev.primitives import RetryPrimitive, TimeoutPrimitive, CachePrimitive
from tta_dev.core import WorkflowContext

# Compose primitives
workflow = (
    TimeoutPrimitive(timeout_seconds=30) >>
    RetryPrimitive(max_attempts=3) >>
    CachePrimitive(ttl=3600) >>
    your_function
)

# Execute with automatic observability
ctx = WorkflowContext(workflow_id="my-workflow")
result = await workflow.execute(data, ctx)
```

**Available Primitives:**
- `RetryPrimitive` - Automatic retries with exponential backoff
- `TimeoutPrimitive` - Execution time limits
- `CachePrimitive` - Result caching with TTL
- `CircuitBreakerPrimitive` - Fault isolation
- `FallbackPrimitive` - Graceful degradation
- `ParallelPrimitive` - Concurrent execution
- `SequentialPrimitive` - Serial composition
- `ConditionalPrimitive` - Conditional branching
- `RouterPrimitive` - Dynamic routing

### 2. Automatic Observability

**Zero-config monitoring** - traces, metrics, and logs are captured automatically:

```python
# Just use primitives - observability happens automatically
workflow = RetryPrimitive(api_call, max_attempts=3)
result = await workflow.execute(data, ctx)  # <- Traced, timed, logged
```

View everything at `http://localhost:8080` - the UI auto-updates as your agent builds new workflows.

### 3. AI Agent Integration

Drop-in support for GitHub Copilot, Claude, Cline, and other CLI agents:

- **`.github/agents/`** - Custom agent personas
- **`.github/skills/`** - Reusable agent skills
- **`AGENTS.md`** - Global agent coordination guide

Your AI agent automatically detects these and starts using TTA.dev primitives for reliable workflows.

## Architecture

```
tta-dev/
├── primitives/        # Core workflow building blocks
├── observability/     # Auto-instrumentation + telemetry
├── core/              # Shared context, types, base classes
├── agents/            # AI agent definitions
├── skills/            # Reusable agent procedures
├── ui/                # Observability web interface
└── integrations/      # External system connectors
```

## Development

```bash
# Run quality checks
uv run ruff format .
uv run ruff check . --fix
uvx pyright tta-dev/

# Run tests
uv run pytest -v

# Run with coverage
uv run pytest --cov=primitives --cov=observability --cov=core
```

## Documentation

- **[GETTING_STARTED.md](../GETTING_STARTED.md)** - Setup and first workflow
- **[PRIMITIVES_CATALOG.md](../PRIMITIVES_CATALOG.md)** - Complete primitive reference
- **[AGENTS.md](../AGENTS.md)** - AI agent coordination guide
- **[USER_JOURNEY.md](../USER_JOURNEY.md)** - End-to-end walkthrough

## Philosophy

1. **Batteries-included** - Clone, run `./setup.sh`, start building
2. **Observable by default** - See everything your workflows do
3. **AI-native** - Built for agent collaboration
4. **Production-ready** - Proper error handling, retries, timeouts, circuit breakers

## License

MIT
