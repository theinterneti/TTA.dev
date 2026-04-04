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
- **An L0 developer control plane** for local task, run, gate, lock, and ownership coordination
- **A documented L0-backed workflow proof path** via
  `tta workflow run feature_dev --track-l0`
- **A substantial automated test suite** covering a large portion of the current core

## What is still in progress

- broader example coverage beyond the narrow proof path is still catching up
- some package-local and historical docs still need follow-up cleanup for full consistency
- type-checking still fails in several areas
- some integrations and knowledge-base surfaces remain partial or stubbed
- the first documented multi-agent proof path exists, but the repo still needs
  broader workflow coverage and stronger validation of what is stable vs experimental

## Learn more

- [**Getting Started Guide**](GETTING_STARTED.md) - current, step-by-step setup and proof path
- [**Quickstart**](QUICKSTART.md) - shortest honest verification flow
- 📖 **[Observability Quickstart →](docs/observability-quickstart.md)** — start the dashboard, watch live traces, connect Langfuse
- [**User Journey**](USER_JOURNEY.md) - vision plus current-reality framing
- [**Roadmap**](ROADMAP.md) - what is implemented, partial, and still aspirational
- [**Primitives Catalog**](PRIMITIVES_CATALOG.md) - available primitives and API surface
- [**Agent Instructions**](AGENTS.md) - how AI agents are expected to work in this repo
- [**Contributing**](CONTRIBUTING.md) - development guide
- [**Feature Dev + L0 Example**](docs/examples/feature-dev-l0-workflow.md) - run
  the current proof workflow and inspect it through `tta control`
- [**Resilient LLM pipeline**](examples/resilient_llm_pipeline.py) — Groq wrapped in retry + circuit breaker + OTel tracing

## License

MIT
