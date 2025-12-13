---
applyTo:
  - "pyproject.toml"
  - "uv.lock"
  - "scripts/**"
  - "**/*.sh"
tags: ['general']
description: "UV package manager usage patterns for TTA - prefer uvx for standalone tools"
priority: 5
auto_trigger: "true"
applies_to: "["uv", "uvx", "package manager", "dependencies", "tool execution", "pip", "poetry"]"
category: "tooling"
---

# Package Management: Prefer `uvx` for Tool Execution

**Auto-triggered when**: Working with package management, dependencies, or tool execution.

## Quick Reference

**Default recommendation:** Use `uvx` for standalone development tools (ruff, pyright, pytest)
**Alternative:** Use `uv run` only when tool needs project dependencies or context
**Best practice:** Pin versions in CI/CD for reproducibility

## Context

This project uses UV as the package manager. UV provides two ways to run tools:
1. `uv run <tool>` - Runs tool from project's virtual environment
2. `uvx <tool>` - Runs tool in isolated environment (like `npx` for Node.js)

## When to Use `uvx`

**Prefer `uvx`** for standalone development tools:
- **Linting:** `uvx ruff check src/ tests/`
- **Formatting:** `uvx ruff format src/ tests/`
- **Type Checking:** `uvx pyright src/`
- **Testing:** `uvx pytest tests/`
- **Any standalone tool** that doesn't need project dependencies

## When to Use `uv run`

Use `uv run` when:
- Running project-specific scripts that import project code
- Running tools that need access to project dependencies
- Running custom scripts defined in `pyproject.toml`

## Benefits of `uvx`

1. **No Installation Required:** Tools run without being added to project dependencies
2. **Always Latest:** Can easily test different versions without modifying `pyproject.toml`
3. **Cleaner Dependencies:** Project `pyproject.toml` only contains actual dependencies
4. **Faster CI/CD:** No need to install tools in project environment
5. **Isolation:** Tools run in isolated environments, preventing conflicts

## Examples

### ✅ Correct Usage

```bash
# Linting (standalone tool)
uvx ruff check src/ tests/

# Formatting (standalone tool)
uvx ruff format src/ tests/

# Type checking (standalone tool)
uvx pyright src/

# Testing (standalone tool)
uvx pytest tests/

# With version pinning for reproducibility
uvx ruff@0.13.0 check src/
uvx pyright@1.1.350 src/
```

### ❌ Incorrect Usage

```bash
# Don't use uv run for standalone tools
uv run ruff check src/ tests/      # Use uvx instead
uv run pyright src/                # Use uvx instead
uv run pytest tests/               # Use uvx instead
```

### ⚠️ Special Cases

```bash
# Use uv run for project scripts that import project code
uv run python scripts/migrate_db.py

# Use uv run for tools that need project dependencies
uv run pytest tests/ --cov=src  # If pytest-cov is project dependency

# Use uv run for custom scripts in pyproject.toml
uv run custom-script
```

## Version Pinning Strategy

For reproducible builds, pin tool versions in documentation or CI/CD:

```bash
# In CI/CD workflows
uvx ruff@0.13.0 check src/
uvx pyright@1.1.350 src/
uvx pytest@7.4.0 tests/

# Or use environment variable
export RUFF_VERSION=0.13.0
uvx ruff@$RUFF_VERSION check src/
```

## Convenience Script

The project provides `scripts/dev.sh` which already uses `uvx` internally:

```bash
# These commands use uvx under the hood
./scripts/dev.sh lint
./scripts/dev.sh format
./scripts/dev.sh typecheck
./scripts/dev.sh test
```

## Exceptions

Do NOT suggest `uvx` for:
1. **Project-specific code:** `python -m src.module`
2. **Scripts importing project:** `python scripts/custom_script.py`
3. **Tools requiring project context:** Tools that need to import project modules
4. **Pre-commit hooks:** These use their own virtual environments

## Documentation References

- `docs/dev-workflow-quick-reference.md` - Developer workflow guide
- `docs/tooling-optimization-summary.md` - Tooling decisions and rationale
- `scripts/dev.sh` - Convenience script implementation

---

**Last Updated**: 2025-10-27
**Status**: Active - TTA package management standard


---
**Logseq:** [[TTA.dev/Platform/Agent-context/.github/Instructions/Package-management]]
