---
title: "Python Tooling & Package Management"
applyTo: "**/*.py"
tags: ["python", "tooling", "uv"]
version: "1.0.0"
---

# Tooling (Python)

This file documents the primary Python toolchain used by the Python pathway. Keep universal package management guidance in `packages/universal-agent-context` and reference this file for Python-specific commands.

## Package manager

- Primary: `uv` (workspace-aware)
- Helper: `uvx` (standalone utility runner)

Use `uv sync` to install workspace dependencies and `uv run`/`uvx` to execute tools:

```bash
# Sync the workspace (fast)
uv sync --all-extras

# Run a tool within the project environment
uv run pytest -v

# Run a standalone tool
uvx pyright src/
```

## Python project files (marker files)

- `pyproject.toml` (primary)
- `requirements.txt` (legacy)
- `pytest.ini`
- `uv.lock`

## Recommendations

- Keep `pyproject.toml` as the canonical project configuration
- Use workspace packages for local packages (workspace = true)
- Prefer `uv sync` in CI for fast dependency resolution
