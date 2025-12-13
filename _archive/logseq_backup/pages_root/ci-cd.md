# CI-CD

**Continuous Integration and Continuous Deployment for TTA.dev**

type:: topic
status:: active

---

## Overview

This page documents the **CI/CD pipeline** for the TTA.dev project, including automated testing, building, and deployment workflows.

---

## GitHub Actions Workflows

### Test Workflow

Runs on every push and pull request:

```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
uses: actions/checkout@v4
uses: astral-sh/setup-uv@v4
run: uv sync
run: uv run pytest
```

### Lint Workflow

Runs code quality checks:

```yaml
name: Lint
on: [push, pull_request]
jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
uses: actions/checkout@v4
uses: astral-sh/setup-uv@v4
run: uv run ruff check .
run: uv run mypy .
```

---

## Pre-Commit Hooks

Local CI checks before committing:

```yaml
# .pre-commit-config.yaml
repos:
repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.7.0
    hooks:
id: ruff
id: ruff-format
repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.13.0
    hooks:
id: mypy
```

---

## Deployment Pipeline

### Staging

Automatic deployment on merge to `develop`
Runs integration tests
Deploys to staging environment

### Production

Manual approval required
Runs full test suite
Deploys to production on merge to `main`

---

## Related

[[TTA.dev/Testing]] - Testing strategies
[[TTA.dev/Packages/tta-dev-primitives]] - Main package
[[GitHub Actions]] - Workflow documentation

---

**Tags:** #devops #ci-cd #automation

**Last Updated:** 2025-12-04


---
**Logseq:** [[TTA.dev/_archive/Logseq_backup/Pages_root/Ci-cd]]
