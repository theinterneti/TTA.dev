# TTA.dev UI Assets

This directory contains dashboard assets and legacy compatibility scripts for the observability UI.

## Supported server entrypoint

Use the unified observability entrypoint:

```bash
uv run python -m ttadev.observability
```

Then open `http://localhost:8000`.

## Current API surface

- `GET /api/v2/health`
- `GET /api/v2/spans`
- `GET /api/v2/sessions`
- `WS /ws`

## Legacy compatibility

`ttadev/ui/observability_server.py` is deprecated and retained only as a compatibility path for
older tooling.
