# Functional Specification: CIMergeGate

**Date:** 2026-03-21
**Phase:** 4 — Automation
**Status:** Approved — 2026-03-25
**Depends on:** `DevelopmentCycle` (Phase 3), `SessionAutomation` (Phase 4a, complete)
**Leads to:** Phase 4c — Quality Gates + Multi-model Fallback

---

## Overview

`CIMergeGate` adds a GitHub Actions job that runs affected tests inside an **E2B sandbox** on every pull request to `main`. It closes the gap between local validation (pre-commit `run_changed_tests.py`) and merge-time enforcement: tests that slip past `--no-verify` locally are caught in CI before they land on main.

The job uses the same file-to-test mapping logic as `scripts/run_changed_tests.py`. It degrades gracefully when `E2B_API_KEY` is not configured — the job passes with a notice rather than blocking merges.

---

## Motivation

The current CI (`ci.yml`) runs the full test suite on every PR. `CIMergeGate` adds a complementary, targeted guarantee:

| Check | Scope | Environment | Enforced at |
|-------|-------|-------------|-------------|
| `ci.yml` test suite | Full suite | GitHub runner (same OS) | PR + push |
| `run_changed_tests.py` | Changed files only | Developer machine | Pre-commit (bypassable) |
| **`CIMergeGate` (new)** | **Changed files only** | **E2B isolated sandbox** | **PR (not bypassable)** |

Running in E2B proves the changed code works in a **clean, isolated environment** — not just on the developer's machine with its local state and installed packages.

---

## User Journeys

### Journey 1 — PR opened, affected tests pass in E2B

```
Developer opens PR: feat/add-timeout-to-retry

CIMergeGate job runs:
  Changed files: ttadev/primitives/recovery/retry.py
  Mapped tests:  tests/primitives/recovery/test_retry.py
  Runs in E2B:   pytest tests/primitives/recovery/test_retry.py -x --tb=short
  Result:        ✅ 1 passed

GitHub status check: e2b-validation ✅
PR is mergeable.
```

### Journey 2 — PR opened, affected tests fail in E2B

```
Developer opens PR: fix/cache-key-collision (breaks a test)

CIMergeGate job runs:
  Changed files: ttadev/primitives/adaptive/cache.py
  Mapped tests:  tests/primitives/adaptive/test_cache.py
  Runs in E2B:   pytest tests/... → FAILED (1 error)
  Result:        ❌ 1 failed

GitHub status check: e2b-validation ❌
PR is blocked. Developer sees test output in the Actions log.
```

### Journey 3 — No test files for changed files

```
Developer opens PR: docs/update-readme

CIMergeGate job runs:
  Changed files: README.md, docs/guide.md
  No .py files → no test mapping possible
  Result:        ✅ skipped (no tests to run)

GitHub status check: e2b-validation ✅ (skipped — no tests affected)
```

### Journey 4 — E2B_API_KEY not configured

```
E2B_API_KEY secret not set in repo settings.

CIMergeGate job runs:
  Detects missing key → prints notice: "E2B_API_KEY not set — skipping sandbox validation"
  Exits 0

GitHub status check: e2b-validation ✅ (skipped — no API key)
```

### Journey 5 — E2B unavailable (transient error)

```
E2B cloud has a transient error.

CIMergeGate job runs:
  Sandbox creation fails → caught as exception
  Logs warning: "E2B sandbox unavailable: <error>"
  Exits 0 (does not block merge on infrastructure failures)

GitHub status check: e2b-validation ✅ (degraded — infra error, skipped)
```

### Journey 6 — Multiple changed source files

```
PR changes: ttadev/primitives/memory/agent_memory.py
            ttadev/workflows/development_cycle.py

Mapped tests:
  tests/primitives/memory/test_agent_memory.py
  tests/workflows/test_development_cycle.py

Runs both test files in a single pytest invocation in E2B.
```

---

## Components

### 1. `scripts/run_e2b_tests.py` — CI E2B test runner

A Python script (invoked by the workflow) that:
- Accepts a list of changed file paths via stdin or a file argument
- Maps source files → test files using the same logic as `run_changed_tests.py`
- If no test files: exits 0 with message "no tests affected"
- If `E2B_API_KEY` not set: exits 0 with message "E2B_API_KEY not set — skipping"
- Creates an E2B sandbox, installs project deps, runs pytest on the mapped test files
- Exits with pytest's return code (0 = pass, non-zero = fail)
- On E2B infrastructure error: exits 0 with warning (does not block merge)

### 2. `.github/workflows/e2b-validation.yml` — GitHub Actions workflow

A new workflow file triggered on `pull_request` to `main`:

```yaml
name: E2B Sandbox Validation

on:
  pull_request:
    branches: [main]
    paths:
      - 'ttadev/**'
      - 'tests/**'
      - 'scripts/**'

jobs:
  e2b-validation:
    name: E2B Sandbox Tests
    runs-on: ubuntu-latest
    timeout-minutes: 15

    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0  # need full history for git diff

      - uses: astral-sh/setup-uv@v2

      - name: Install dependencies
        run: uv sync --all-extras

      - name: Get changed files
        id: changed
        run: |
          git diff --name-only origin/main...HEAD -- '*.py' > /tmp/changed_files.txt
          cat /tmp/changed_files.txt

      - name: Run E2B sandbox validation
        env:
          E2B_API_KEY: ${{ secrets.E2B_API_KEY }}
        run: uv run python scripts/run_e2b_tests.py /tmp/changed_files.txt
```

---

## Input/Output Contract

### `scripts/run_e2b_tests.py`

- **Input**: path to a file containing changed `.py` paths (one per line), or `-` for stdin
- **Output**: stdout with status messages; exit code mirrors pytest (0 = pass/skip, non-zero = fail)
- **Side effects**: creates and destroys an E2B sandbox

### Exit codes

| Code | Meaning |
|------|---------|
| 0 | Tests passed, or no tests to run, or E2B unavailable (degraded) |
| 1+ | Tests failed — blocks merge |

---

## Edge Cases

| Scenario | Behaviour |
|----------|-----------|
| No Python files changed | Exit 0 — "no tests affected" |
| No test counterparts found | Exit 0 — "no tests affected" |
| `E2B_API_KEY` not set | Exit 0 — "skipping sandbox validation" |
| E2B sandbox creation fails | Exit 0 with warning — does not block merge on infra error |
| E2B times out | Exit 0 with warning — timeout is not a test failure |
| Tests fail | Exit 1 — blocks merge |
| Changed file is already a test file | Skip (not a source file — tested directly by `ci.yml`) |
| PR changes >20 files | Run all mapped tests in a single pytest invocation |

---

## File Layout

| Action | Path | Purpose |
|--------|------|---------|
| Create | `scripts/run_e2b_tests.py` | CI E2B test runner script |
| Create | `.github/workflows/e2b-validation.yml` | GitHub Actions workflow |
| Create | `tests/scripts/test_run_e2b_tests.py` | Unit tests for the runner script |

No modifications to existing workflows — the new workflow is additive.

---

## Success Criteria

1. `e2b-validation` job appears as a status check on PRs to `main`
2. PR with failing affected tests is blocked from merging
3. PR with passing affected tests (or no affected tests) is not blocked
4. Missing `E2B_API_KEY` secret → job passes with a notice (does not block)
5. E2B infrastructure error → job passes with a warning (does not block)
6. `scripts/run_e2b_tests.py` has 100% test coverage with mocked E2B and file I/O
7. Workflow triggers only on changes to `ttadev/**`, `tests/**`, or `scripts/**`
8. Job completes within 15 minutes (E2B sandbox: ~150ms startup + test execution time)

---

## Out of Scope

- CGC impact analysis in CI (too complex without CGC running in the runner)
- Full test suite in E2B (only affected tests — full suite is already covered by `ci.yml`)
- Making `e2b-validation` a required status check in branch protection (user configures this in GitHub settings)
- Matrix builds across Python versions in E2B (single version — 3.11)
- Caching E2B sandbox state between runs
- Running `scripts/run_changed_tests.py` (local) and `scripts/run_e2b_tests.py` (CI) as a shared library (they stay separate scripts)
