# TTA.dev Example Guide

The maintained demo scripts live at the repository root in [`examples/`](../../examples).

## Current demo commands

```bash
# Terminal 1: start the observability server
uv run python -m ttadev.observability

# Terminal 2: run a lightweight primitive demo
uv run python examples/demo_workflow.py

# Optional: run the hello world variant
uv run python ttadev/hello_world.py
```

## Verified lightweight demos

- `examples/demo_workflow.py` - small retry/cache/timeout workflow using the current API
- `ttadev/hello_world.py` - self-observing hello world workflow using the current API

## Canonical proof path

For the shortest re-verified flow, prefer:

```bash
uv run python -m ttadev.observability
uv run python scripts/test_realtime_traces.py
```

See [`GETTING_STARTED.md`](../../GETTING_STARTED.md) and [`QUICKSTART.md`](../../QUICKSTART.md)
for the current onboarding story.
