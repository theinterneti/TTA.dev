# TTA.dev Technical Context

## Technologies Used
- **Package Manager:** uv (NOT pip, NOT poetry)
- **Python Version:** 3.11+
- **Testing:** pytest + pytest-asyncio
- **Linting:** ruff
- **Type Checking:** pyright
- **Tracing:** OpenTelemetry
- **Metrics:** Prometheus

## Development Setup
```bash
uv sync --all-extras
uv run pytest -v
uv run ruff format .
uv run ruff check . --fix
uvx pyright packages/
```

## Technical Constraints
- Python 3.11+ required for modern type hints
- Use `str | None` NOT `Optional[str]`
- 100% test coverage required
- All primitives must use WorkflowContext
