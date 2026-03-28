# TTA.dev Observability Note

> [!WARNING]
> This package-local observability document has been superseded by the repository-root proof path.

For current usage, prefer:

- [`../../README.md`](../../README.md)
- [`../../GETTING_STARTED.md`](../../GETTING_STARTED.md)
- [`../../QUICKSTART.md`](../../QUICKSTART.md)

## Supported entrypoint

```bash
uv run python -m ttadev.observability
```

## Supported verification path

```bash
uv run python scripts/test_realtime_traces.py
curl http://localhost:8000/api/v2/health
curl http://localhost:8000/api/v2/spans | head
```

## Deprecated legacy script

An older UI-script entrypoint is deprecated and should not be used for new onboarding material.
