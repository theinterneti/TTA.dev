# Python Pathway

**Language:** Python 3.11+
**Package Manager:** uv
**Status:** Active

## Overview

The Python Pathway provides Python-specific tooling, instructions, workflows, and fixtures for TTA.dev projects.

## Auto-Detection

This pathway activates when any of these files are detected:
- `pyproject.toml`
- `setup.py`
- `requirements.txt`
- `Pipfile`
- `uv.lock`

## Toolchain

### Package Management
- **uv** - Fast Python package manager (primary)
- **pip** - Fallback package installer

### Testing
- **pytest** - Test framework
- **pytest-asyncio** - Async test support
- **pytest-cov** - Coverage reporting
- **pytest-mock** - Mocking utilities

### Code Quality
- **ruff** - Fast Python linter and formatter
- **pyright** - Static type checker
- **mypy** - Alternative type checker

### Build Tools
- **hatchling** - Modern build backend
- **setuptools** - Legacy build support

## Directory Structure

```
python-pathway/
├── README.md                    # This file
├── instructions/
│   ├── uv-workspace.md         # UV workspace management
│   ├── pytest-fixtures.md      # Pytest fixture patterns
│   ├── ruff-config.md          # Ruff configuration
│   └── type-checking.md        # Pyright/mypy setup
├── chatmodes/
│   ├── python-backend-dev.md   # Backend development mode
│   ├── pytest-engineer.md      # Testing specialist mode
│   └── package-maintainer.md   # Package management mode
├── workflows/
│   ├── python-feature.md       # Python feature development
│   ├── python-testing.md       # Python test development
│   └── python-package.md       # Package creation/update
└── fixtures/
    ├── pytest-fixtures.py      # Common pytest fixtures
    ├── async-fixtures.py       # Async test fixtures
    └── mock-fixtures.py        # Mock object fixtures
```

## Activation

### Automatic
The pathway auto-activates when Python project files are detected.

### Manual
```bash
@activate python
```

## Integration Points

- **Universal Agent Context**: Uses language-agnostic patterns
- **GitHub Workflows**: Python-specific CI/CD configurations
- **VS Code Tasks**: Python tool integration

## Resources

- [UV Integration Guide](../../docs/development/UV_INTEGRATION_GUIDE.md)
- [UV Workflow Foundation](../../docs/architecture/UV_WORKFLOW_FOUNDATION.md)
- [Python Testing Guide](../../docs/development/Testing_Guide.md)

## Token Budget

- **Instructions**: ~2,500 tokens
- **Chatmodes**: ~1,500 tokens (on-demand)
- **Workflows**: ~2,000 tokens (on-demand)
- **Fixtures**: ~1,000 tokens
- **Total**: ~7,000 tokens (vs 15,000+ when mixed with other languages)

---

**Last Updated:** October 29, 2025
**Version:** 1.0.0
