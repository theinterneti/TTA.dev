# GitHub Actions Workflow Rebuild - Quick Start Guide

**For**: Implementing the new workflow architecture
**See Also**:
- Full Plan: [`WORKFLOW_REBUILD_PLAN.md`](./WORKFLOW_REBUILD_PLAN.md)
- Summary: [`WORKFLOW_REBUILD_SUMMARY.md`](./WORKFLOW_REBUILD_SUMMARY.md)
- Diagrams: [`WORKFLOW_REBUILD_DIAGRAMS.md`](./WORKFLOW_REBUILD_DIAGRAMS.md)

---

## 🎯 Implementation Checklist

### Phase 1: Foundation (Week 1)

#### Create Composite Action: setup-tta-env

```bash
mkdir -p .github/actions/setup-tta-env
```

Create `.github/actions/setup-tta-env/action.yml`:

```yaml
name: 'Setup TTA Development Environment'
description: 'Install uv and configure Python for TTA.dev'

inputs:
  python-version:
    description: 'Python version'
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

    - name: Add to PATH
      shell: bash
      run: echo "$HOME/.cargo/bin" >> $GITHUB_PATH

    - name: Cache dependencies
      uses: actions/cache@v4
      with:
        path: |
          ~/.cache/uv
          .venv
        key: ${{ runner.os }}-py${{ inputs.python-version }}-${{ hashFiles('uv.lock') }}
```

- [ ] Create action file
- [ ] Test in sandbox workflow
- [ ] Verify caching works
- [ ] Document usage

#### Test Composite Action

Create `.github/workflows/test-composite-action.yml`:

```yaml
name: Test Composite Action

on:
  workflow_dispatch:

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: ./.github/actions/setup-tta-env
      - run: uv --version
      - run: uv sync --all-extras
      - run: uv run pytest --version
```

- [ ] Run workflow manually
- [ ] Check cache behavior
- [ ] Verify setup speed
- [ ] Delete test workflow

---

### Phase 2: Core Workflows (Week 1-2)

#### Create pr-validation.yml

Create `.github/workflows/pr-validation.yml`:

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
      - run: uv sync --all-extras
      - run: uv run ruff format --check .
      - run: uv run ruff check .

  typecheck:
    name: Type Check
    runs-on: ubuntu-latest
    timeout-minutes: 5
    steps:
      - uses: actions/checkout@v4
      - uses: ./.github/actions/setup-tta-env
      - run: uv sync --all-extras
      - run: uvx pyright packages/

  unit-tests:
    name: Unit Tests
    runs-on: ubuntu-latest
    timeout-minutes: 10
    steps:
      - uses: actions/checkout@v4
      - uses: ./.github/actions/setup-tta-env
      - run: uv sync --all-extras
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
      - run: uv sync --all-extras
      - run: python scripts/docs/check_md.py --all

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

- [ ] Create workflow file
- [ ] Test on feature branch
- [ ] Verify all jobs run
- [ ] Check timing (~10 min?)
- [ ] Update branch protection rules

#### Create merge-validation.yml

Create `.github/workflows/merge-validation.yml`:

```yaml
name: Merge Validation

on:
  push:
    branches: [main]
    paths:
      - 'packages/**'
      - 'tests/**'
      - 'pyproject.toml'
      - 'uv.lock'

concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: false  # Don't cancel on main

jobs:
  integration-tests:
    name: Integration Tests
    runs-on: ubuntu-latest
    timeout-minutes: 30
    steps:
      - uses: actions/checkout@v4
      - uses: ./.github/actions/setup-tta-env
      - run: uv sync --all-extras

      - name: Start Docker services
        run: |
          cd platform/primitives
          docker compose -f docker-compose.integration.yml up -d
          sleep 10

      - name: Run integration tests
        env:
          RUN_INTEGRATION: true
        run: uv run pytest -v -m "integration"

      - name: Stop services
        if: always()
        run: |
          cd platform/primitives
          docker compose -f docker-compose.integration.yml down -v

  cross-platform:
    name: Cross-Platform Tests
    runs-on: ${{ matrix.os }}
    timeout-minutes: 20
    strategy:
      fail-fast: false
      matrix:
        os: [ubuntu-latest, macos-latest, windows-latest]
        python-version: ['3.11', '3.12']

    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
      - uses: ./.github/actions/setup-tta-env
        with:
          python-version: ${{ matrix.python-version }}
      - run: uv sync --all-extras
      - run: uv run pytest -v -m "not integration and not slow"

  coverage:
    name: Coverage Report
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: ./.github/actions/setup-tta-env
      - run: uv sync --all-extras
      - run: |
          uv run pytest \
            -m "not integration and not slow" \
            --cov=packages \
            --cov-report=xml

      - uses: codecov/codecov-action@v4
        with:
          token: ${{ secrets.CODECOV_TOKEN }}
          files: ./coverage.xml
          fail_ci_if_error: false

  package-install:
    name: Package Installation Test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: ./.github/actions/setup-tta-env
      - run: uv sync --all-extras
      - run: uv pip install -e platform/primitives/
```

- [ ] Create workflow file
- [ ] Test on main branch
- [ ] Verify all jobs run
- [ ] Check timing (~30 min?)
- [ ] Monitor for failures

---

### Phase 3: Reusable Workflows (Week 2)

#### Directory Structure

```bash
mkdir -p .github/workflows-reusable
```

#### Create setup-python.yml

Create `.github/workflows-reusable/setup-python.yml`:

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
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ inputs.python-version }}
      - uses: ./.github/actions/setup-tta-env
        with:
          python-version: ${{ inputs.python-version }}
      - name: Install dependencies
        run: |
          if [ "${{ inputs.install-extras }}" = "true" ]; then
            uv sync --all-extras
          else
            uv sync
          fi
```

- [ ] Create reusable workflow
- [ ] Test with caller workflow
- [ ] Verify inputs work
- [ ] Document usage

---

### Phase 4: Migration (Week 3)

#### Disable Old Workflows

```bash
# Rename old workflows
cd .github/workflows
mv ci.yml ci.yml.disabled
mv quality-check.yml quality-check.yml.disabled
mv tests-split.yml tests-split.yml.disabled
# ... repeat for all old workflows

git add .
git commit -m "chore: Disable old workflows for migration"
git push
```

- [ ] Rename old workflows to `.disabled`
- [ ] Commit changes
- [ ] Monitor new workflows for 1 week
- [ ] Document any issues

#### Monitor for Issues

```bash
# Check workflow runs
gh run list --workflow=pr-validation.yml --limit 20

# Check for failures
gh run list --workflow=pr-validation.yml --status=failure

# View specific run
gh run view <run-id>
```

- [ ] Monitor daily
- [ ] Fix issues promptly
- [ ] Update documentation
- [ ] Collect feedback

---

### Phase 5: Cleanup (Week 3)

#### Delete Old Workflows

```bash
cd .github/workflows
rm *.disabled

git add .
git commit -m "chore: Remove old workflows after successful migration"
git push
```

- [ ] Delete .disabled files
- [ ] Update CONTRIBUTING.md
- [ ] Update README.md badges
- [ ] Create architecture diagram

#### Update Documentation

Files to update:

1. **CONTRIBUTING.md**

```markdown
## CI/CD Workflows

We use GitHub Actions with an atomic, focused workflow structure:

- **pr-validation.yml** - Fast validation on every PR (~10 min)
- **merge-validation.yml** - Thorough checks after merge (~30 min)
- **release.yml** - Automated releases
- **scheduled-maintenance.yml** - Background tasks

See `.github/workflows/README.md` for details.
```

2. **README.md**

```markdown
[![PR Validation](https://github.com/theinterneti/TTA.dev/workflows/PR%20Validation/badge.svg)](https://github.com/theinterneti/TTA.dev/actions/workflows/pr-validation.yml)
```

3. **Create .github/workflows/README.md**

See full template in `WORKFLOW_REBUILD_PLAN.md`

- [ ] Update CONTRIBUTING.md
- [ ] Update README.md
- [ ] Create .github/workflows/README.md
- [ ] Create architecture diagram

---

## 🧪 Testing Strategy

### Test Each Component Independently

1. **Composite Action**

```bash
# Create test workflow
gh workflow run test-composite-action.yml

# Check results
gh run list --workflow=test-composite-action.yml --limit 1
```

2. **PR Validation**

```bash
# Create test branch
git checkout -b test/pr-validation

# Make change
echo "# Test" >> README.md
git add README.md
git commit -m "test: PR validation"
git push -u origin test/pr-validation

# Create PR
gh pr create --title "Test PR Validation" --body "Testing new workflow"

# Watch workflow
gh run watch
```

3. **Merge Validation**

```bash
# Merge test PR
gh pr merge --merge

# Watch workflow on main
gh run list --workflow=merge-validation.yml --limit 1
gh run watch <run-id>
```

---

## 📊 Success Metrics

Track these metrics during migration:

### Speed

```bash
# Before (average of last 10 runs)
gh run list --workflow=ci.yml --limit 10 --json durationMs

# After (average of last 10 runs)
gh run list --workflow=pr-validation.yml --limit 10 --json durationMs
```

**Target**: PR validation < 10 minutes

### Reliability

```bash
# Check failure rate
gh run list --workflow=pr-validation.yml --limit 100 --json status | \
  jq '[.[] | select(.status == "completed")] | group_by(.conclusion) | map({conclusion: .[0].conclusion, count: length})'
```

**Target**: >95% success rate

### Maintainability

- [ ] Update uv version in 1 place (composite action)
- [ ] Add new quality check in 1 place (reusable workflow)
- [ ] Workflow purpose clear from name

---

## 🆘 Troubleshooting

### Common Issues

#### 1. Cache Not Working

```yaml
# Debug cache behavior
- name: Debug cache
  run: |
    echo "Cache key: ${{ runner.os }}-py${{ inputs.python-version }}-${{ hashFiles('uv.lock') }}"
    ls -la ~/.cache/uv || echo "No uv cache"
    ls -la .venv || echo "No venv"
```

#### 2. Composite Action Not Found

```yaml
# Make sure to checkout first
- uses: actions/checkout@v4
- uses: ./.github/actions/setup-tta-env  # Now available
```

#### 3. Workflows Not Triggering

```yaml
# Check path filters
on:
  pull_request:
    paths:
      - 'packages/**'  # Make sure changed files match
```

#### 4. Concurrency Issues

```yaml
# Debug concurrency group
- name: Debug concurrency
  run: |
    echo "Workflow: ${{ github.workflow }}"
    echo "Ref: ${{ github.ref }}"
    echo "Group: ${{ github.workflow }}-${{ github.ref }}"
```

---

## 📋 Pre-Launch Checklist

Before disabling old workflows:

- [ ] All new workflows tested on feature branch
- [ ] Timing targets met (PR < 10 min, merge < 30 min)
- [ ] Caching working correctly
- [ ] All required checks passing
- [ ] Branch protection rules updated
- [ ] Documentation updated
- [ ] Team notified of changes

---

## 🔄 Rollback Plan

If issues arise:

```bash
# Quick rollback
cd .github/workflows
mv ci.yml.disabled ci.yml
mv quality-check.yml.disabled quality-check.yml
# ... repeat for needed workflows

git add .
git commit -m "revert: Rollback to old workflows"
git push

# Update branch protection to use old workflows
# Settings > Branches > main > Edit > Status checks
```

---

**Quick Links**:

- Full Plan: [`WORKFLOW_REBUILD_PLAN.md`](./WORKFLOW_REBUILD_PLAN.md)
- Summary: [`WORKFLOW_REBUILD_SUMMARY.md`](./WORKFLOW_REBUILD_SUMMARY.md)
- Diagrams: [`WORKFLOW_REBUILD_DIAGRAMS.md`](./WORKFLOW_REBUILD_DIAGRAMS.md)

**Implementation Status**:

- [ ] Phase 1: Foundation
- [ ] Phase 2: Core Workflows
- [ ] Phase 3: Reusable Workflows
- [ ] Phase 4: Migration
- [ ] Phase 5: Cleanup
