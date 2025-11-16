# GitHub Actions Workflows - Consolidated & Optimized

## Overview

This directory contains GitHub Actions workflows for TTA.dev. The workflows have been consolidated from 30+ files into 4 core workflows for improved performance, reliability, and maintainability.

## Core Workflows

### 1. 🚀 Pull Request Validation (`consolidated-pr-validation.yml`)

**Purpose:** Fast feedback for pull requests  
**Trigger:** PR opened, synchronized, reopened  
**Duration:** ~5 minutes  
**Jobs:**
- Quality checks (format, lint, types)
- Unit tests (Python 3.12, Ubuntu only)
- PR summary

**Why it's fast:**
- Single platform (Ubuntu)
- Single Python version (3.12)
- Unit tests only (no integration tests)
- Parallel job execution

**When it runs:**
- Every PR update
- Skips documentation-only changes

### 2. ✅ Merge Gate (`consolidated-merge-gate.yml`)

**Purpose:** Comprehensive validation before merge  
**Trigger:** Push to main/develop  
**Duration:** ~15-20 minutes  
**Jobs:**
- Quality validation
- Comprehensive tests (Python 3.11, 3.12)
- Integration tests (main only)
- Documentation validation
- Package validation
- Security scans

**Why it's comprehensive:**
- Multi-version testing
- Integration tests included
- Security scanning
- Package build validation

**When it runs:**
- After merge to main/develop
- Not blocking PRs

### 3. 🌐 Platform Compatibility (`consolidated-platform-compatibility.yml`)

**Purpose:** Cross-platform compatibility testing  
**Trigger:** Nightly, manual, or push to main (core packages)  
**Duration:** ~20-30 minutes  
**Jobs:**
- Matrix builds (Ubuntu, macOS, Windows × Python 3.11, 3.12)
- Platform compatibility summary

**Why it's separate:**
- Matrix builds are expensive (6 combinations)
- Not needed for every PR
- Runs nightly to catch platform issues

**When it runs:**
- Nightly at 2 AM UTC
- Manual trigger via workflow_dispatch
- Push to main affecting core packages

### 4. 🤖 AI Code Review (`consolidated-ai-review.yml`)

**Purpose:** Automated code review with fallback  
**Trigger:** PR opened, synchronized, reopened  
**Duration:** ~5-10 minutes  
**Jobs:**
- Check Gemini availability
- Gemini review (with retry and timeout)
- Fallback static analysis
- Review summary

**Why it's reliable:**
- Circuit breaker pattern
- Fallback to static analysis if Gemini unavailable
- Timeout protection (8 minutes max)
- Graceful degradation

**When it runs:**
- Every PR update (Python files only)
- Falls back if API unavailable

## Performance Comparison

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| PR Validation Time | 20 min | 5 min | **75% faster** |
| Merge Validation Time | 30 min | 15-20 min | **33-50% faster** |
| GitHub Actions Minutes (per PR) | 50 min | 10-15 min | **70-80% reduction** |
| Workflow Files to Maintain | 30+ | 4 core | **87% reduction** |
| Workflow Success Rate | ~90% | >95% (target 99%) | **5%+ improvement** |

## Workflow Optimizations

### Caching Strategy

All workflows use intelligent caching:

1. **uv binary cache** (`.github/actions/setup-tta-env`)
   ```yaml
   path: ~/.cargo/bin/uv
   key: ${{ runner.os }}-uv-0.5.x
   ```

2. **Python dependencies cache**
   ```yaml
   path: |
     ~/.cache/uv
     .venv
   key: ${{ runner.os }}-python-${{ matrix.python-version }}-${{ hashFiles('uv.lock') }}
   ```

3. **Coverage results** (saved as artifacts)
   ```yaml
   retention-days: 30
   ```

### Parallelization

Jobs run in parallel where possible:

**PR Validation:**
```
quality-checks (parallel) → unit-tests → pr-summary
```

**Merge Gate:**
```
quality-validation ─┬→ comprehensive-tests → integration-tests
                    ├→ docs-validation
                    └→ package-validation
                    ↓
                merge-gate-summary
```

### Path-based Triggering

Workflows skip execution for irrelevant changes:

```yaml
paths-ignore:
  - '**.md'
  - 'docs/**'
  - 'logseq/**'
  - 'archive/**'
```

### Concurrency Control

Workflows use concurrency groups to cancel outdated runs:

```yaml
concurrency:
  group: pr-${{ github.event.pull_request.number }}
  cancel-in-progress: true
```

## Reusable Workflows

These workflows can be called by other workflows:

### `reusable-run-tests.yml`

Generic test runner with configurable options:

```yaml
jobs:
  test:
    uses: ./.github/workflows/reusable-run-tests.yml
    with:
      test-type: 'unit'
      python-versions: '["3.11", "3.12"]'
      coverage: true
```

**Inputs:**
- `test-type`: unit/integration/all
- `python-versions`: JSON array of versions
- `coverage`: Enable coverage reporting
- `pytest-markers`: Custom pytest markers
- `timeout-minutes`: Test timeout

### `reusable-quality-checks.yml`

Generic quality checker:

```yaml
jobs:
  quality:
    uses: ./.github/workflows/reusable-quality-checks.yml
    with:
      python-version: '3.11'
      check-format: true
      check-lint: true
      check-types: true
```

**Inputs:**
- `python-version`: Python version to use
- `check-format`: Run ruff format check
- `check-lint`: Run ruff lint check
- `check-types`: Run pyright type check
- `fail-on-type-errors`: Fail workflow on type errors

### `reusable-build-package.yml`

Package builder for releases:

```yaml
jobs:
  build:
    uses: ./.github/workflows/reusable-build-package.yml
```

## Utility Workflows

### Testing & Validation

- `test-gemini-api-key.yml` - Manual Gemini API testing
- `test-gemini-cli-no-mcp.yml` - Gemini CLI testing
- `test-gemini-keys.yml` - API key validation
- `test-mcp-versions.yml` - MCP server version testing
- `test-quality-checks.yml` - Workflow testing
- `list-gemini-models.yml` - List available Gemini models

### Continuous Validation

- `kb-validation.yml` - Knowledge base validation
- `mcp-validation.yml` - MCP validation
- `secrets-validation.yml` - Secrets validation
- `validate-todos.yml` - TODO compliance

### Monitoring

- `pr-health-monitoring.yml` - PR health tracking

### Setup

- `auto-assign-copilot.yml` - Auto-assign reviewer
- `copilot-setup-steps.yml` - Copilot setup

## Deprecated Workflows

These workflows are deprecated and will be removed after validation:

| Old Workflow | Replacement | Status |
|--------------|-------------|--------|
| `pr-validation.yml` | `consolidated-pr-validation.yml` | ⚠️ Deprecated |
| `pr-validation-v2.yml` | `consolidated-pr-validation.yml` | ⚠️ Deprecated |
| `merge-validation.yml` | `consolidated-merge-gate.yml` | ⚠️ Deprecated |
| `merge-validation-v2.yml` | `consolidated-merge-gate.yml` | ⚠️ Deprecated |
| `ci.yml` | Multiple (split by purpose) | ⚠️ Deprecated |
| `quality-check.yml` | Multiple (split by context) | ⚠️ Deprecated |
| `orchestration-pr-review.yml` | `consolidated-ai-review.yml` | ⚠️ Deprecated |
| `gemini-dispatch.yml` | `consolidated-ai-review.yml` | ⚠️ Deprecated |
| `gemini-triage.yml` | `consolidated-ai-review.yml` | ⚠️ Deprecated |

See [MIGRATION_PLAN.md](MIGRATION_PLAN.md) for detailed migration strategy.

## Security Best Practices

All workflows follow security best practices:

### Minimal Permissions

```yaml
permissions:
  contents: read
  pull-requests: write
  issues: write
```

### Token Scoping

Different workflows use different tokens:
- GitHub token for basic operations
- App token for AI reviews
- Service account for GCP operations

### Secret Handling

- Secrets never logged or exposed
- Validation workflows check secret availability
- Continue-on-error for missing secrets

### Audit Trail

- Comprehensive job summaries
- Detailed logging
- Artifact retention for debugging

## Troubleshooting

### PR Validation Fails

1. Check quality checks (format, lint, types)
2. Run locally: `uv run ruff format --check . && uv run ruff check . && uv run pyright packages/`
3. Fix issues and push

### Merge Gate Fails

1. Check comprehensive test results
2. Run locally: `uv run pytest -v -m "not integration"`
3. Fix failing tests

### AI Review Doesn't Run

1. Check if Gemini API is configured
2. Fallback static analysis should run automatically
3. Check workflow summary for details

### Platform Compatibility Fails

1. Check which platform/Python combination failed
2. Run tests locally on that platform
3. Fix platform-specific issues

## Manual Workflow Triggers

Some workflows can be triggered manually:

### Trigger Platform Compatibility

```bash
gh workflow run consolidated-platform-compatibility.yml
```

### Trigger Gemini API Test

```bash
gh workflow run test-gemini-api-key.yml
```

### List Gemini Models

```bash
gh workflow run list-gemini-models.yml
```

## Monitoring & Metrics

Track these metrics to ensure optimization success:

- **PR validation time** (target: < 5 min)
- **Merge validation time** (target: < 20 min)
- **Workflow success rate** (target: > 99%)
- **GitHub Actions minutes usage** (target: 70% reduction)

View metrics in GitHub Actions dashboard.

## Future Enhancements

### Phase 2: Performance Optimization (Planned)
- [ ] Selective test execution based on changed files
- [ ] Advanced caching strategies
- [ ] Further parallelization

### Phase 3: Reliability Enhancement (Planned)
- [ ] MCP server health checks
- [ ] Enhanced retry mechanisms
- [ ] Circuit breaker patterns for all external services

### Phase 4: Security Hardening (Planned)
- [ ] Automated secret rotation
- [ ] Enhanced permissions model
- [ ] AI agent action auditing

## Contributing

When adding or modifying workflows:

1. Follow the consolidated workflow pattern
2. Use reusable workflows where possible
3. Add comprehensive job summaries
4. Include proper error handling
5. Document changes in this README
6. Test locally before pushing

## Questions?

See [MIGRATION_PLAN.md](MIGRATION_PLAN.md) for detailed migration strategy and timeline.

---

**Last Updated:** November 15, 2025  
**Status:** ✅ Phase 1 Complete - Consolidation  
**Next:** Phase 2 - Performance Optimization
