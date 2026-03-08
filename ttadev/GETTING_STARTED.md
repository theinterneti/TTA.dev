# Getting Started with TTA.dev

**TTA.dev is a batteries-included framework that makes AI coding agents reliable and observable.**

## 🚀 Quick Start (5 minutes)

### 1. Clone and Setup

```bash
git clone https://github.com/theinterneti/TTA.dev
cd TTA.dev
./setup.sh
```

That's it! Setup automatically:
- Installs `uv` (fast Python package manager)
- Creates virtual environment
- Installs TTA.dev with all primitives
- Sets up observability dashboard

### 2. Start the Observability Dashboard

```bash
cd tta-dev
uv run python ui/observability_server.py
```

Open http://localhost:8000 in your browser. You'll see the real-time dashboard.

### 3. Run Your First Workflow

```bash
uv run python examples/demo_instrumented_workflow.py
```

Watch the dashboard light up with traces showing:
- Sequential workflows (steps run one after another)
- Parallel workflows (steps run concurrently)
- Execution times, success/failure status
- Full span details for debugging

## 📊 What You're Seeing

The dashboard automatically tracks:
- **Every primitive execution** - No manual logging needed
- **Workflow structure** - See how primitives compose
- **Performance metrics** - Duration, success rate
- **Error details** - Full stack traces when things fail

## 🎯 Next Steps

### Build Your First AI Workflow

Create `my_workflow.py`:

```python
import asyncio
from primitives.core.base import WorkflowContext, LambdaPrimitive
from primitives.core.sequential import SequentialPrimitive

async def analyze_code(data: dict, ctx: WorkflowContext) -> dict:
    """Your AI agent logic here."""
    return {"analysis": "Code looks good!"}

async def generate_tests(data: dict, ctx: WorkflowContext) -> dict:
    """Generate tests based on analysis."""
    return {"tests": "test_my_feature.py created"}

async def main():
    workflow = SequentialPrimitive([
        LambdaPrimitive(analyze_code),
        LambdaPrimitive(generate_tests),
    ])
    
    ctx = WorkflowContext(workflow_id="my-first-workflow")
    result = await workflow.execute({"file": "main.py"}, ctx)
    print(result)

if __name__ == "__main__":
    asyncio.run(main())
```

Run it:
```bash
uv run python my_workflow.py
```

The dashboard automatically shows your workflow executing!

### Point Your AI Agent at TTA.dev

1. Clone TTA.dev to your machine
2. Your AI coding agent (Claude, Copilot, Cline) detects `AGENTS.md`
3. Agent starts using TTA.dev primitives automatically
4. Dashboard shows everything your agent builds

### Available Primitives

**Core Workflows:**
- `SequentialPrimitive` - Steps run in order
- `ParallelPrimitive` - Steps run concurrently
- `ConditionalPrimitive` - Branch based on conditions
- `RouterPrimitive` - Route to different handlers

**Recovery:**
- `RetryPrimitive` - Auto-retry with backoff
- `FallbackPrimitive` - Try alternatives on failure
- `CircuitBreakerPrimitive` - Fail fast when service is down

**Performance:**
- `CachePrimitive` - Cache expensive operations
- `TimeoutPrimitive` - Prevent hangs
- `ThrottlePrimitive` - Rate limiting

**All primitives are auto-instrumented** - zero config needed!

## 🔧 Configuration

TTA.dev works out-of-the-box with sensible defaults.

### Environment Variables (Optional)

Create `.env`:
```bash
# OpenTelemetry (optional - dashboard works without this)
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317

# LangFuse integration (optional)
LANGFUSE_PUBLIC_KEY=your_key
LANGFUSE_SECRET_KEY=your_secret
LANGFUSE_HOST=https://cloud.langfuse.com
```

The dashboard works **without any configuration** - it uses in-memory storage by default.

## 📚 Learn More

- **Primitives Catalog**: See `PRIMITIVES_CATALOG.md` for full API reference
- **Agents**: See `AGENTS.md` for multi-agent patterns
- **Examples**: Browse `tta-dev/examples/` for more demos

## 🤝 Integration with AI Agents

### GitHub Copilot
Already configured! Copilot reads `.github/copilot-instructions.md` and knows to use TTA.dev primitives.

### Claude/Cline
Point your agent at this repository. It will discover:
- `.github/agents/` - Custom agent definitions
- `.github/skills/` - Reusable workflows
- `AGENTS.md` - Architecture guidance

### Your Custom Agent
TTA.dev is framework-agnostic. Just import the primitives and use them in your agent code.

## 🎉 What Makes TTA.dev Different?

1. **Batteries Included** - Dashboard + primitives + examples work immediately
2. **Auto-Observable** - No logging code needed, everything is instrumented
3. **Auto-Growing** - Dashboard adapts as your agent builds new features
4. **Framework Agnostic** - Works with any AI agent or LLM provider

## 💡 Tips

- Keep the dashboard open while developing - it's your debugging superpower
- Use `WorkflowContext(workflow_id="descriptive-name")` for easy filtering
- Primitives compose - build complex workflows from simple pieces
- The dashboard persists recent traces even after restart

## 🐛 Troubleshooting

**Dashboard shows "Disconnected"?**
- Restart the server: `uv run python ui/observability_server.py`
- Check port 8000 isn't in use: `lsof -i :8000`

**No traces appearing?**
- Ensure primitives are imported from `primitives.*` package
- Check console for errors
- Verify WebSocket connection in browser dev tools

**Import errors?**
- Run `./setup.sh` again to reinstall
- Check you're in the virtual environment: `source .venv/bin/activate`

## 🚀 Ready to Build!

You now have:
- ✅ Working observability dashboard
- ✅ Battle-tested workflow primitives  
- ✅ Auto-instrumentation (no logging code needed)
- ✅ Real-time visibility into AI agent operations

Start building reliable AI applications with TTA.dev!
