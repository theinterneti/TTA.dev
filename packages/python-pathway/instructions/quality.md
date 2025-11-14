---
title: "Quality Tools (ruff, pyright)"
applyTo: "**/*.py"
tags: ["python", "quality", "lint", "types"]
version: "1.0.0"
---

# Quality Tools

This document contains Python-specific quality tooling guidance (linters and type checkers).

## Linters & formatters

- `ruff` for linting and auto-formatting

```bash
# Check for issues
uvx ruff check src/ tests/

# Format in-place
uvx ruff format src/ tests/
```

## Type checking

- `pyright` for fast type analysis

```bash
uvx pyright src/
```

## Secrets detection

- `detect-secrets` (optional) for credential scanning
