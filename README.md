# TTA.dev

> **Experimental foundation for AI-native workflow primitives, observability, and agent-first
> dev tooling.**

TTA.dev exists to build the reusable AI devops tools that the future TTA product will rely on.
The repository has a real, tested core today, but it is still aspirational overall and should not
yet be read as a finished product.

## Verified proof path

The commands below were re-verified in a clean clone on `2026-03-22`.

```bash
# 1. Clone and install dependencies
git clone https://github.com/theinterneti/TTA.dev.git
cd TTA.dev
./setup.sh

# 2. Terminal 1: start the observability server
uv run python -m ttadev.observability

# 3. Terminal 2: generate trace data
uv run python scripts/test_realtime_traces.py

# 4. Optional: inspect the emitted spans directly
curl http://localhost:8000/api/v2/health
curl http://localhost:8000/api/v2/spans | head
```

That flow currently proves:

- the observability server starts on `http://localhost:8000`
- a workflow can execute successfully with current primitives
- trace data is written to `.observability/traces.jsonl`
- the server ingests those traces and exposes them via `/api/v2/spans`

## What works today

- **Composable primitives** for sequencing, parallelism, retries, timeouts, caching, and more
- **A local observability server** with a working v2 API and dashboard entrypoint
- **Agent and workflow foundations** in `ttadev/agents/` and `ttadev/workflows/`
- **A substantial automated test suite** covering a large portion of the current core

## What is still in progress

- some older demo scripts and onboarding commands are being migrated to the current API
- documentation and roadmap language are being aligned to actual repository state
- type-checking still fails in several areas
- some integrations and knowledge-base surfaces remain partial or stubbed

## Learn more

- [**Getting Started Guide**](GETTING_STARTED.md) - current, step-by-step setup and proof path
- [**Quickstart**](QUICKSTART.md) - shortest honest verification flow
- [**User Journey**](USER_JOURNEY.md) - vision plus current-reality framing
- [**Roadmap**](ROADMAP.md) - what is implemented, partial, and still aspirational
- [**Primitives Catalog**](PRIMITIVES_CATALOG.md) - available primitives and API surface
- [**Agent Instructions**](AGENTS.md) - how AI agents are expected to work in this repo
- [**Contributing**](CONTRIBUTING.md) - development guide

## License

MIT
