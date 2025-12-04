# TTA.dev Copilot Instructions

## Package Manager

**Use `uv`, never `pip` or `poetry`**

```bash
uv sync --all-extras        # Install dependencies
uv run pytest -v            # Run tests
uv run ruff format .        # Format code
uv run ruff check . --fix   # Lint code
```

## Python Standards

- Python 3.11+ required
- Type hints: `str | None` not `Optional[str]`
- Dicts: `dict[str, Any]` not `Dict[str, Any]`
- Type check: `uvx pyright platform/`

## Testing

- Framework: pytest with AAA pattern (Arrange, Act, Assert)
- Async tests: `@pytest.mark.asyncio`
- Mocking: `MockPrimitive` from `tta_dev_primitives.testing`
- Coverage: 80% minimum, 100% for new code

## Code Style

- Formatter: Ruff (100 char line length)
- Docstrings: Google style
- All public functions must have docstrings

## Workflow Primitives

**Always use primitives for workflows. Never write manual retry/timeout loops.**

```python
# ✅ Use primitives
workflow = CachePrimitive(ttl=3600) >> RetryPrimitive(max_retries=3) >> process

# ❌ Don't write manual loops
for attempt in range(3):  # Never do this
    try: ...
```

## Security

- Never log secrets (even partially)
- URL validation: use `urlparse()`, not substring checks
- Run `uv run python scripts/security_scan.py` before committing

## Quick Reference

| Task | Command |
|------|---------|
| Install deps | `uv sync --all-extras` |
| Run tests | `uv run pytest -v` |
| Format | `uv run ruff format .` |
| Lint | `uv run ruff check . --fix` |
| Type check | `uvx pyright platform/` |
| All checks | Run format, lint, typecheck, test in sequence |

## Documentation

- [AGENTS.md](../AGENTS.md) - Quick reference for agents
- [PRIMITIVES_CATALOG.md](../PRIMITIVES_CATALOG.md) - Complete primitive API
- [GETTING_STARTED.md](../GETTING_STARTED.md) - Setup guide
