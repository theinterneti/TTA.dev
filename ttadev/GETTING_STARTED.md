# TTA.dev Package-Level Getting Started Note

> [!WARNING]
> This package-local guide is no longer the canonical onboarding document.
>
> Use the repository-root guides instead:
>
> - [`../GETTING_STARTED.md`](../GETTING_STARTED.md)
> - [`../QUICKSTART.md`](../QUICKSTART.md)

## Supported observability entrypoint

Start the dashboard with:

```bash
uv run python -m ttadev.observability
```

The supported verification path then uses:

```bash
uv run python scripts/test_realtime_traces.py
curl http://localhost:8000/api/v2/health
curl http://localhost:8000/api/v2/spans | head
```

## Deprecated path

An older UI-script entrypoint is retained only for compatibility and should not be used for new
docs or onboarding.
