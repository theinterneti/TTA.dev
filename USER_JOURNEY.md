# TTA.dev User Journey

This file now separates **vision** from **current reality**.

## The story

TTA.dev exists because the future TTA product needs reusable AI devops tools that do not really
exist yet in a form a solo builder can simply adopt. So TTA.dev is the workshop: primitives,
observability, workflows, and agent guidance intended to make building TTA possible.

That means this repository should be read as:

- a serious foundation with working pieces
- an honest work in progress
- not yet the finished TTA product

## Current verified experience

The most honest journey we can support today is:

1. clone the repo and run `./setup.sh`
2. open the repo with your coding agent so it can read `AGENTS.md` and repo instructions
3. start the observability server with `uv run python -m ttadev.observability`
4. run `uv run python scripts/test_realtime_traces.py`
5. verify spans through `http://localhost:8000/api/v2/spans`

That journey proves:

- the current primitive composition API works for a simple workflow
- the observability server starts successfully
- trace data is emitted and ingested by the v2 API

## What is already real

- composable primitives in `ttadev/primitives/`
- agent and workflow building blocks in `ttadev/agents/` and `ttadev/workflows/`
- a working observability server entrypoint at `python -m ttadev.observability`
- a large automated test suite around the current core

## What is still aspirational

These are still directionally important, but they are **not** part of the current “works today”
story:

- polished public demo scripts for every major feature
- a fully self-discovering dashboard that automatically adapts to everything an agent builds
- fully aligned docs, roadmap, and examples
- complete knowledge-base and integration surfaces
- “production-ready from day 1” as a blanket statement across the whole repo

## Near-term success criteria

For the next stage, success looks like:

1. one canonical onboarding path that remains green
2. docs that clearly separate verified behavior from future goals
3. repaired or replaced demo scripts that match the current primitive APIs
4. fewer type-checking failures in the main package

## Longer-term vision

The long-term goal is still ambitious:

- AI agents clone the repo and immediately work within TTA.dev patterns
- workflows are observable by default
- development primitives replace ad-hoc retry/timeout/coordination code
- TTA.dev becomes the reusable foundation that the future TTA product can depend on

That vision remains valid. The important change is that we now document it as a vision rather than
as something fully achieved already.
