# GitHub Actions Workflow Rebuild Plan

**Goal**: Rebuild TTA.dev's GitHub Actions workflows to be atomic, explicit, graceful, and simple.

**Created**: 2025-11-05
**Status**: Planning

---

## 🎯 Current State Analysis

### Problems Identified

1. **Too Many Workflows** (20 total)
   - `ci.yml`, `quality-check.yml`, `tests-split.yml` - overlapping concerns
   - Multiple Gemini workflows (`gemini-invoke.yml`, `gemini-dispatch.yml`, `gemini-review.yml`, etc.)
   - Validation workflows that could be consolidated
   - Difficult to understand what runs when

2. **Duplication & Complexity**
   - Setup steps repeated in every workflow (uv install, Python setup)
   - Complex concurrency groups with manual string building
   - Mixed concerns (quality checks run tests, CI runs package installation)
   - No reusable workflows - everything is standalone

3. **Poor Developer Experience**
   - Unclear which workflow failed and why
   - Long-running matrix jobs (3 OS × 2 Python versions = 6 jobs)
   - Workflows trigger on overlapping paths
   - No clear feedback loop

4. **Maintenance Burden**
   - Update uv version in 10+ places
   - Change Python version in multiple workflows
   - Add new quality check? Update multiple files
   - Breaking changes cascade across workflows

---

## 🏗️ Proposed Architecture

### Design Principles

1. **Atomic** - Each workflow does ONE thing well
2. **Explicit** - Clear naming, obvious purpose
3. **Graceful** - Handle failures, provide context
4. **Simple** - Easy to read, easy to maintain
5. **Composable** - Reusable workflows for common patterns

### Industry Best Practices

Based on GitHub Actions documentation and "vibe coder" patterns:

1. **Reusable Workflows** - DRY principle for CI/CD
2. **Composite Actions** - Package common setup steps
3. **Job Dependencies** - Use `needs:` for clear flow
4. **Concurrency Control** - Simple, predictable groups
5. **Path Filters** - Minimal, explicit triggers
6. **Matrix Strategy** - Only where beneficial
7. **Caching** - Dependency caching for speed

---

## 📋 New Workflow Structure

### Core Workflows (Always Run)

```
.github/
├── workflows/
│   ├── pr-validation.yml          # Main PR gate (fast)
│   ├── merge-validation.yml       # Post-merge verification
│   ├── release.yml                # Release automation
│   └── scheduled-maintenance.yml  # Nightly/weekly tasks
├── workflows-reusable/
│   ├── setup-python.yml           # Python + uv setup
│   ├── run-tests.yml              # Test execution
│   ├── quality-checks.yml         # Lint, format, type check
│   └── build-package.yml          # Package building
└── actions/
    ├── setup-tta-env/             # Composite action
    │   └── action.yml
    └── cache-dependencies/
        └── action.yml
```

### Workflow Responsibilities

#### 1. `pr-validation.yml` (PR Gate - FAST)
**Purpose**: Quick validation before merge
**Triggers**: `pull_request` to `main`
**Jobs**:
- **lint** (2min) - Ruff format + check
- **typecheck** (3min) - Pyright on packages/
- **unit-tests** (5min) - Fast unit tests only
- **docs-check** (1min) - Markdown validation

**Total**: ~10 minutes max
**Strategy**: Fail-fast, single OS (Ubuntu), Python 3.12

#### 2. `merge-validation.yml` (Post-Merge - THOROUGH)
**Purpose**: Comprehensive validation after merge
**Triggers**: `push` to `main`
**Jobs**:
- **integration-tests** - Docker services, full integration
- **cross-platform** - Matrix: Ubuntu, macOS, Windows
- **coverage-report** - Upload to Codecov
- **package-install** - Test installation in clean env

**Total**: ~20-30 minutes
**Strategy**: Comprehensive, runs everything

#### 3. `release.yml` (Release Automation)
**Purpose**: Build and publish releases
**Triggers**:
- `workflow_dispatch` (manual)
- `push` tags matching `v*`
**Jobs**:
- **build** - Build distributions
- **test-install** - Verify installability
- **publish-pypi** - Upload to PyPI
- **create-github-release** - Release notes

#### 4. `scheduled-maintenance.yml` (Background Tasks)
**Purpose**: Regular maintenance and monitoring
**Triggers**:
- `schedule: "0 2 * * *"` (nightly)
- `schedule: "0 10 * * 1"` (weekly)
**Jobs**:
- **dependency-audit** - Check for security issues
- **link-checker** - Validate documentation links
- **cleanup-artifacts** - Remove old artifacts
- **benchmark-performance** - Track performance metrics

---

## 🔧 Reusable Workflows

### `setup-python.yml`
```yaml
name: Setup Python Environment

on:
  workflow_call:
    inputs:
      python-version:
        type: string
        default: '3.12'
      install-extras:
        type: boolean
        default: true

jobs:
  setup:
    runs-on: ${{ inputs.os || 'ubuntu-latest' }}
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: ${{ inputs.python-version }}

      - name: Setup uv
        uses: ./.github/actions/setup-tta-env

      - name: Install dependencies
        run: |
          if [ "${{ inputs.install-extras }}" = "true" ]; then
            uv sync --all-extras
          else
            uv sync
          fi
```

### `run-tests.yml`
```yaml
name: Run Tests

on:
  workflow_call:
    inputs:
      test-type:
        type: string
        required: true
        # Options: unit, integration, all
      coverage:
        type: boolean
        default: false

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: ./.github/workflows-reusable/setup-python.yml

      - name: Run tests
        run: |
          case "${{ inputs.test-type }}" in
            unit)
              uv run pytest -m "not integration and not slow" -v
              ;;
            integration)
              uv run pytest -m "integration" -v
              ;;
            all)
              uv run pytest -v
              ;;
          esac

      - name: Upload coverage
        if: inputs.coverage
        uses: codecov/codecov-action@v4
```

### `quality-checks.yml`
```yaml
name: Quality Checks

on:
  workflow_call:
    inputs:
      check-type:
        type: string
        required: true
        # Options: format, lint, typecheck, all

jobs:
  quality:
    runs-on: ubuntu-latest
    steps:
      - uses: ./.github/workflows-reusable/setup-python.yml

      - name: Format check
        if: contains(fromJSON('["format", "all"]'), inputs.check-type)
        run: uv run ruff format --check .

      - name: Lint
        if: contains(fromJSON('["lint", "all"]'), inputs.check-type)
        run: uv run ruff check .

      - name: Type check
        if: contains(fromJSON('["typecheck", "all"]'), inputs.check-type)
        run: uvx pyright packages/
```

---

## 🎬 Composite Actions

### `setup-tta-env/action.yml`
```yaml
name: 'Setup TTA Development Environment'
description: 'Install uv and configure Python environment for TTA.dev'

inputs:
  python-version:
    description: 'Python version to use'
    required: false
    default: '3.12'

runs:
  using: 'composite'
  steps:
    - name: Cache uv
      uses: actions/cache@v4
      with:
        path: ~/.cargo/bin/uv
        key: ${{ runner.os }}-uv-${{ inputs.python-version }}

    - name: Install uv (Unix)
      if: runner.os != 'Windows'
      shell: bash
      run: curl -LsSf https://astral.sh/uv/install.sh | sh

    - name: Install uv (Windows)
      if: runner.os == 'Windows'
      shell: powershell
      run: irm https://astral.sh/uv/install.ps1 | iex

    - name: Add uv to PATH
      shell: bash
      run: echo "$HOME/.cargo/bin" >> $GITHUB_PATH

    - name: Cache dependencies
      uses: actions/cache@v4
      with:
        path: |
          ~/.cache/uv
          .venv
        key: ${{ runner.os }}-python-${{ inputs.python-version }}-${{ hashFiles('uv.lock') }}
```

---

## 📊 Comparison: Before vs After

### Before (Current State)

```
❌ 20 workflow files
❌ Duplicated setup code across all workflows
❌ Unclear workflow responsibilities
❌ Mixed concerns (quality + tests, CI + docs)
❌ 6 matrix jobs for every PR (slow)
❌ Update uv in 10+ places
❌ Hard to debug which workflow failed
```

### After (Proposed State)

```
✅ 4 core workflows + 4 reusable workflows
✅ Shared setup via composite actions
✅ Clear, single-purpose workflows
✅ Separated concerns (PR validation vs post-merge)
✅ Fast PR checks (~10min), thorough post-merge
✅ Update uv in 1 composite action
✅ Explicit workflow names and job names
```

---

## 🚀 Implementation Plan

### Phase 1: Foundation (Week 1)
- [ ] Create composite action: `setup-tta-env`
- [ ] Create composite action: `cache-dependencies`
- [ ] Create reusable workflow: `setup-python.yml`
- [ ] Test composite actions in sandbox workflow

### Phase 2: Core Workflows (Week 1-2)
- [ ] Implement `pr-validation.yml`
- [ ] Implement `merge-validation.yml`
- [ ] Test both workflows on feature branch
- [ ] Compare performance to current workflows

### Phase 3: Reusable Workflows (Week 2)
- [ ] Create `run-tests.yml` (unit, integration, all)
- [ ] Create `quality-checks.yml` (format, lint, typecheck)
- [ ] Create `build-package.yml`
- [ ] Integrate into core workflows

### Phase 4: Migration (Week 3)
- [ ] Disable old workflows (rename to `.disabled`)
- [ ] Monitor new workflows for 1 week
- [ ] Fix any issues discovered
- [ ] Update documentation

### Phase 5: Cleanup (Week 3)
- [ ] Delete old workflows
- [ ] Archive Gemini experiment workflows
- [ ] Update CONTRIBUTING.md with new workflow info
- [ ] Create workflow architecture diagram

---

## 🎯 Success Metrics

### Speed
- **PR validation**: <10 minutes (vs ~20 minutes now)
- **Merge validation**: <30 minutes (comprehensive)
- **Developer feedback**: <2 minutes (lint/format)

### Maintainability
- **Update uv version**: 1 file (vs 10+ files)
- **Add quality check**: 1 reusable workflow
- **Workflow count**: 4 core + 4 reusable (vs 20 standalone)

### Clarity
- **Workflow purpose**: Clear from name
- **Job dependencies**: Explicit via `needs:`
- **Failure identification**: Obvious from job name

---

## 📚 Best Practices Applied

### From GitHub Actions Documentation

1. **Reusable Workflows** ([docs](https://docs.github.com/en/actions/using-workflows/reusing-workflows))
   - ✅ `workflow_call` trigger for reusability
   - ✅ `inputs` and `secrets` for parameterization
   - ✅ Clear separation of concerns

2. **Composite Actions** ([docs](https://docs.github.com/en/actions/creating-actions/creating-a-composite-action))
   - ✅ Package common setup steps
   - ✅ Reduce duplication across workflows
   - ✅ Version control action dependencies

3. **Concurrency Control** ([docs](https://docs.github.com/en/actions/using-jobs/using-concurrency))
   - ✅ Simple group names: `${{ github.workflow }}-${{ github.ref }}`
   - ✅ `cancel-in-progress: true` for PR workflows
   - ✅ `cancel-in-progress: false` for merge workflows

4. **Dependency Caching** ([docs](https://docs.github.com/en/actions/using-workflows/caching-dependencies-to-speed-up-workflows))
   - ✅ Cache uv binary
   - ✅ Cache Python dependencies
   - ✅ Use `hashFiles('uv.lock')` for cache key

5. **Matrix Strategy** ([docs](https://docs.github.com/en/actions/using-jobs/using-a-matrix-for-your-jobs))
   - ✅ Use only when beneficial (post-merge)
   - ✅ Don't use for PR validation (too slow)
   - ✅ `fail-fast: false` for cross-platform tests

6. **Path Filters** ([docs](https://docs.github.com/en/actions/using-workflows/workflow-syntax-for-github-actions#onpushpull_requestpull_request_targetpathspaths-ignore))
   - ✅ Minimal, explicit paths
   - ✅ Avoid running on documentation-only changes
   - ✅ Clear which changes trigger which workflows

### From "Vibe Coder" Patterns

1. **Atomic Workflows** - One clear purpose per workflow
2. **Explicit Naming** - Name tells you exactly what it does
3. **Graceful Failures** - Provide context, don't just fail
4. **Simple Over Clever** - Readable beats clever
5. **Fast Feedback** - Optimize for developer experience

---

## 🔄 Migration Strategy

### Step 1: Parallel Run
Run new workflows alongside old workflows on feature branch:
```yaml
# In pr-validation.yml
on:
  pull_request:
    branches: [feature/workflow-rebuild]
```

### Step 2: Compare Results
Monitor both old and new workflows:
- Check run times
- Verify all checks pass
- Ensure no regressions

### Step 3: Feature Flag
Use workflow file suffix to enable/disable:
```
ci.yml.disabled           # Old workflow (disabled)
pr-validation.yml         # New workflow (active)
```

### Step 4: Gradual Rollout
1. Enable `pr-validation.yml` on all PRs
2. Monitor for 1 week
3. Enable `merge-validation.yml`
4. Monitor for 1 week
5. Disable old workflows
6. Delete after 2 weeks of stability

---

## 📖 Documentation Updates

### Files to Update

1. **CONTRIBUTING.md**
   - New workflow structure
   - How to run workflows locally
   - Troubleshooting guide

2. **README.md**
   - CI/CD badge updates
   - Link to workflow documentation

3. **New: `.github/WORKFLOWS.md`**
   - Complete workflow architecture
   - Workflow trigger conditions
   - Job dependency graph
   - How to add new workflows

4. **New: `.github/workflows/README.md`**
   - Quick reference for workflows
   - Reusable workflow catalog
   - Composite action catalog

---

## 🎨 Visual Architecture

```
┌─────────────────────────────────────────────────┐
│                  Pull Request                   │
└──────────────────┬──────────────────────────────┘
                   │
                   ↓
┌─────────────────────────────────────────────────┐
│           pr-validation.yml (FAST)              │
│  ┌─────────┐  ┌──────────┐  ┌──────────────┐  │
│  │  Lint   │→ │Typecheck │→ │ Unit Tests   │  │
│  │  2min   │  │   3min   │  │    5min      │  │
│  └─────────┘  └──────────┘  └──────────────┘  │
│               Fail Fast ⚡ (~10 min total)      │
└──────────────────┬──────────────────────────────┘
                   │
                   ↓ (on merge)
┌─────────────────────────────────────────────────┐
│        merge-validation.yml (THOROUGH)          │
│  ┌──────────────┐  ┌──────────────────────┐   │
│  │ Integration  │  │  Cross-Platform      │   │
│  │   Tests      │  │  Matrix (3×2)        │   │
│  │   10min      │  │  20min               │   │
│  └──────────────┘  └──────────────────────┘   │
│               Comprehensive 🔍 (~30 min)        │
└──────────────────┬──────────────────────────────┘
                   │
                   ↓ (nightly/weekly)
┌─────────────────────────────────────────────────┐
│     scheduled-maintenance.yml (BACKGROUND)      │
│  ┌──────────┐  ┌──────────┐  ┌──────────────┐ │
│  │ Dep Audit│  │Link Check│  │ Benchmarks   │ │
│  │   5min   │  │   3min   │  │   10min      │ │
│  └──────────┘  └──────────┘  └──────────────┘ │
└─────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────┐
│         Reusable Workflows (Library)            │
│  ┌──────────────┐  ┌──────────────────────┐   │
│  │setup-python  │  │run-tests             │   │
│  │quality-checks│  │build-package         │   │
│  └──────────────┘  └──────────────────────┘   │
└─────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────┐
│        Composite Actions (Building Blocks)      │
│  ┌──────────────┐  ┌──────────────────────┐   │
│  │setup-tta-env │  │cache-dependencies    │   │
│  └──────────────┘  └──────────────────────┘   │
└─────────────────────────────────────────────────┘
```

---

## 🔍 Specific Workflow Examples

### Example: `pr-validation.yml`

```yaml
name: PR Validation

on:
  pull_request:
    branches: [main]
    paths:
      - 'packages/**'
      - 'tests/**'
      - 'pyproject.toml'
      - 'uv.lock'

concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true

jobs:
  lint:
    name: Lint & Format
    runs-on: ubuntu-latest
    timeout-minutes: 5
    steps:
      - uses: actions/checkout@v4
      - uses: ./.github/actions/setup-tta-env
      - run: uv run ruff format --check .
      - run: uv run ruff check .

  typecheck:
    name: Type Check
    runs-on: ubuntu-latest
    timeout-minutes: 5
    steps:
      - uses: actions/checkout@v4
      - uses: ./.github/actions/setup-tta-env
      - run: uvx pyright packages/

  unit-tests:
    name: Unit Tests
    runs-on: ubuntu-latest
    timeout-minutes: 10
    steps:
      - uses: actions/checkout@v4
      - uses: ./.github/actions/setup-tta-env
      - run: |
          uv run pytest -v \
            -m "not integration and not slow" \
            --tb=short

  docs-check:
    name: Documentation
    runs-on: ubuntu-latest
    timeout-minutes: 3
    steps:
      - uses: actions/checkout@v4
      - uses: ./.github/actions/setup-tta-env
      - run: python scripts/docs/check_md.py --all

  # Summary job for branch protection
  pr-gate:
    name: PR Gate
    runs-on: ubuntu-latest
    needs: [lint, typecheck, unit-tests, docs-check]
    if: always()
    steps:
      - name: Check all jobs
        run: |
          if [ "${{ contains(needs.*.result, 'failure') }}" = "true" ]; then
            echo "❌ One or more checks failed"
            exit 1
          fi
          echo "✅ All checks passed"
```

---

## 🎯 Next Steps

1. **Review this plan** - Get feedback from team
2. **Create tracking issue** - GitHub issue for implementation
3. **Set up feature branch** - `feature/workflow-rebuild`
4. **Implement Phase 1** - Composite actions first
5. **Test in isolation** - Validate each component
6. **Gradual rollout** - Replace workflows incrementally

---

## 📞 Questions & Decisions

### To Discuss

1. **Matrix strategy**: Keep cross-platform tests? (macOS, Windows cost money)
2. **Coverage threshold**: Enforce minimum coverage in PR validation?
3. **Integration tests**: Run on every PR or only post-merge?
4. **Gemini workflows**: Archive or integrate into new structure?
5. **MCP validation**: Keep as separate workflow or merge into validation?

### To Decide

- [ ] Python versions to test: 3.11, 3.12, or both?
- [ ] OS matrix: Ubuntu only, or Ubuntu + macOS?
- [ ] Coverage reporting: Every PR or only on merge?
- [ ] Artifact retention: How long to keep test artifacts?

---

**Last Updated**: 2025-11-05
**Author**: GitHub Copilot + Research
**Status**: Awaiting Review
