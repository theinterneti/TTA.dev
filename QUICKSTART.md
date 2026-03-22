# TTA.dev Quickstart - Current Verified Proof Path

This guide is intentionally narrow: it documents the shortest flow we have re-verified in a clean
clone.

It proves the current foundation works. It does **not** claim that every legacy demo script or
future-facing feature in the repository is ready yet.

## Step 1: Clone and setup

```bash
git clone https://github.com/theinterneti/TTA.dev.git
cd TTA.dev
./setup.sh
```

## Step 2: Start the observability server

In terminal 1:

```bash
uv run python -m ttadev.observability
```

Expected result:

- the dashboard starts on `http://localhost:8000`
- `GET /api/v2/health` returns `{"status": "ok", ...}`

## Step 3: Generate trace data

In terminal 2:

```bash
uv run python scripts/test_realtime_traces.py
```

Expected result:

- the script exits successfully
- `.observability/traces.jsonl` is created
- the server begins exposing spans at `http://localhost:8000/api/v2/spans`

You can check directly with:

```bash
curl http://localhost:8000/api/v2/health
curl http://localhost:8000/api/v2/spans | head
```

## What this proves today

1. the current `ttadev.primitives` composition API works for a basic sequential workflow
2. the `python -m ttadev.observability` entrypoint is valid
3. trace ingestion into the v2 observability API works after a short delay

## What this does **not** prove yet

- that every older public demo script still matches the current primitive APIs
- that every onboarding path in older docs is up to date
- that the repo is fully production-ready end to end

## Recommended next reads

- [`GETTING_STARTED.md`](GETTING_STARTED.md) for the current setup story
- [`USER_JOURNEY.md`](USER_JOURNEY.md) for the long-term vision vs current reality
- [`ROADMAP.md`](ROADMAP.md) for implemented vs planned work

## Notes

- If `/api/v2/spans` is empty immediately after the script runs, wait a few seconds and query it
  again. The ingestion loop is asynchronous.
- Older demo commands that reference `src/...`, `ttadev/ui/observability_server.py`, or
  `ttadev/hello_world.py` may not match the current APIs yet and should not be treated as canonical
  proof paths.
