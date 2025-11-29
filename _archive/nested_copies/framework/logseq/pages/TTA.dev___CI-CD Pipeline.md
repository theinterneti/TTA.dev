# TTA.dev/CI-CD Pipeline

**Continuous Integration and Continuous Deployment infrastructure for TTA.dev.**

## Overview

TTA.dev uses GitHub Actions for automated CI/CD with comprehensive validation and testing.

## CI/CD Workflows

### Core Workflows
- **Python Tests** (`.github/workflows/python-tests.yml`) - Unit and integration tests
- **KB Validation** (`.github/workflows/kb-validation.yml`) - Knowledge base validation
- **Quality Checks** (`.github/workflows/quality.yml`) - Linting, formatting, type checking

### Validation Steps

**Python Tests:**
1. Setup Python 3.11+
2. Install dependencies with `uv`
3. Run pytest with coverage
4. Upload coverage reports

**KB Validation:**
1. Parse Logseq pages
2. Extract and validate links
3. Check journal format
4. Validate TODO compliance

**Quality Checks:**
1. Ruff format check
2. Ruff lint check
3. Pyright type checking

## Configuration

### Workflow Files
- `.github/workflows/*.yml` - Workflow definitions
- `pyproject.toml` - Tool configuration (ruff, pytest, coverage)
- `.github/copilot-instructions.md` - Agent instructions

## Related Pages

- [[DevOps]] - DevOps practices overview
- [[TTA.dev/Testing]] - Testing infrastructure
- [[Contributors]] - Contributing guidelines
- [[TTA.dev/Quality Checks]] - Quality validation

## Documentation

- `docs/ci-cd/` - CI/CD documentation
- `docs/CI_CD_REVIEW_COMPLETE.md` - CI/CD review
- `.github/workflows/README.md` - Workflow documentation

## Tags

infrastructure:: ci-cd
automation:: true

- [[Project Hub]]