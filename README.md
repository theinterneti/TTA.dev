# TTA.dev

> **Transform any idea into a production-ready AI-native application with built-in observability.**

TTA.dev (Test-Time Adaptation) provides composable primitives and workflows that make AI coding agents reliable, observable, and production-ready.

## ⚡ 30-Second Quick Start

```bash
# 1. Clone and setup (installs in editable mode)
git clone https://github.com/theinterneti/TTA.dev.git
cd TTA.dev
./setup.sh

# 2. Point your AI agent at the repo - it will:
#    - See AGENTS.md and start using TTA.dev patterns
#    - Auto-instrument all primitives with observability
#    - Display activity in real-time dashboard

# 3. Start the dashboard server, then open:
uv run python ttadev/ui/observability_server.py &
open http://localhost:8000
```

**That's it!** Your AI agent now has enterprise-grade reliability and observability.

## 🎯 What You Get

- **🔄 Resilient Workflows**: Retry, timeout, circuit breaker, fallback primitives
- **📊 Built-in Observability**: Zero-config dashboard showing all agent activity
- **🤖 AI-Native**: Works with Claude, Copilot, Cline, or any coding agent
- **🚀 Batteries Included**: No external services, databases, or complex setup

## 📚 Learn More

- [**Getting Started Guide**](GETTING_STARTED.md) - Complete step-by-step walkthrough
- [**User Journey**](USER_JOURNEY.md) - See the full experience
- [**Primitives Catalog**](PRIMITIVES_CATALOG.md) - All available primitives & API reference
- [**Agent Instructions**](AGENTS.md) - How AI agents use TTA.dev
- [**Contributing**](CONTRIBUTING.md) - Development guide

## License

MIT
