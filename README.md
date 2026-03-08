# TTA.dev

**Batteries-included AI workflow framework with built-in observability**

## Quick Start

```bash
# 1. Clone and setup
git clone https://github.com/theinterneti/TTA.dev
cd TTA.dev
./setup.sh

# 2. Activate environment
source .venv/bin/activate

# 3. Start observability UI
python -m tta-dev.ui.app

# 4. Run demo
python demo_working_tta.py
```

Visit http://localhost:5001 to see your workflows in real-time!

## What You Get

✅ **Workflow Primitives** - Retry, timeout, cache, circuit breaker, fallback  
✅ **Built-in Observability** - Auto-instrumented tracing with live UI  
✅ **Production Ready** - Sampling, error tracking, performance metrics  
✅ **AI-Native** - Works with any AI coding agent (Claude, Copilot, Cline)

## Architecture

```
tta-dev/
├── primitives/      # Workflow building blocks
├── observability/   # Auto-instrumentation
├── ui/             # Live dashboard
├── agents/         # AI agent configurations
├── skills/         # Reusable workflows
└── integrations/   # LLM providers (Ollama, OpenRouter, etc.)
```

## Documentation

- [User Journey](USER_JOURNEY.md) - Complete walkthrough
- [Primitives Catalog](PRIMITIVES_CATALOG.md) - API reference
- [Contributing](CONTRIBUTING.md) - Development guide

## License

MIT
