# Workflow Rebuild Phase 2: Reusable Workflows

**Date:** November 6, 2025
**Status:** 🚧 **IN PROGRESS**
**Depends On:** Phase 1 (✅ Complete)

---

## Objective

Create reusable workflow components that eliminate duplication and establish a consistent CI/CD foundation for TTA.dev.

**Goal:** Transform the validated Phase 1 workflows into a modular, maintainable system using GitHub's reusable workflow feature.

---

## Phase 1 Success Summary

Before proceeding, here's what we validated:

- ✅ Composite action (`setup-tta-env`) working perfectly (4s setup)
- ✅ PR validation in 25s (40x faster than target)
- ✅ Comprehensive tests in 40-46s (40x faster than target)
- ✅ Matrix strategy proven (Python 3.11 + 3.12)
- ✅ Docker Compose v2 integration working
- ✅ OpenTelemetry + Prometheus tests passing

**Infrastructure is solid. Now we modularize.**

---

## Phase 2 Architecture

### Reusable Workflows to Create

```
.github/workflows/
├── reusable/
│   ├── setup-python.yml          # Python environment setup
│   ├── run-tests.yml              # Test execution (unit/integration/coverage)
│   ├── quality-checks.yml         # Format/lint/type checking
│   └── build-package.yml          # Package building and validation
├── pr-validation.yml              # Calls quality-checks + run-tests (unit)
└── merge-validation.yml           # Calls quality-checks + run-tests (full) + build-package
```

### Why Reusable Workflows?

1. **DRY Principle** - Define once, use everywhere
2. **Centralized Updates** - Fix in one place, applies to all callers
3. **Consistent Behavior** - Same test execution across all workflows
4. **Easy Testing** - Test workflows in isolation
5. **Better Organization** - Clear separation of concerns

---

## Reusable Workflow Specifications

### 1. `setup-python.yml`

**Purpose:** Configure Python environment with caching and dependencies

**Inputs:**
```yaml
inputs:
  python-version:
    description: 'Python version to use'
    required: false
    default: '3.11'
    type: string
  cache-key-suffix:
    description: 'Suffix for cache key (e.g., "unit-tests")'
    required: false
    default: 'default'
    type: string
  install-extras:
    description: 'Install optional dependencies (all/dev/test/docs)'
    required: false
    default: 'all'
    type: string
```

**Outputs:**
```yaml
outputs:
  python-version:
    description: 'Python version installed'
    value: ${{ jobs.setup.outputs.python-version }}
  cache-hit:
    description: 'Whether cache was hit'
    value: ${{ jobs.setup.outputs.cache-hit }}
```

**Implementation:**
- Use composite action `setup-tta-env`
- Add configurable extras installation
- Export outputs for downstream jobs

---

### 2. `run-tests.yml`

**Purpose:** Execute tests with configurable markers, coverage, and matrix

**Inputs:**
```yaml
inputs:
  test-type:
    description: 'Type of tests to run (unit/integration/all)'
    required: true
    type: string
  python-version:
    description: 'Python version (can be JSON array for matrix)'
    required: false
    default: '["3.11", "3.12"]'
    type: string
  coverage:
    description: 'Enable coverage reporting'
    required: false
    default: true
    type: boolean
  pytest-markers:
    description: 'Pytest markers to use (-m argument)'
    required: false
    default: ''
    type: string
  timeout-minutes:
    description: 'Test timeout in minutes'
    required: false
    default: 10
    type: number
```

**Outputs:**
```yaml
outputs:
  test-result:
    description: 'Test execution result (success/failure)'
    value: ${{ jobs.test.outputs.result }}
  coverage-percent:
    description: 'Code coverage percentage'
    value: ${{ jobs.test.outputs.coverage }}
```

**Implementation:**
- Matrix strategy for Python versions
- Conditional coverage upload
- Integration test infrastructure (docker-compose)
- Artifact upload for coverage reports

---

### 3. `quality-checks.yml`

**Purpose:** Run format, lint, and type checking

**Inputs:**
```yaml
inputs:
  python-version:
    description: 'Python version to use'
    required: false
    default: '3.11'
    type: string
  check-format:
    description: 'Run ruff format check'
    required: false
    default: true
    type: boolean
  check-lint:
    description: 'Run ruff lint check'
    required: false
    default: true
    type: boolean
  check-types:
    description: 'Run pyright type check'
    required: false
    default: true
    type: boolean
  fail-on-type-errors:
    description: 'Fail workflow if type errors found'
    required: false
    default: false
    type: boolean
```

**Outputs:**
```yaml
outputs:
  format-result:
    description: 'Format check result'
    value: ${{ jobs.quality.outputs.format-result }}
  lint-result:
    description: 'Lint check result'
    value: ${{ jobs.quality.outputs.lint-result }}
  type-result:
    description: 'Type check result'
    value: ${{ jobs.quality.outputs.type-result }}
  type-error-count:
    description: 'Number of type errors found'
    value: ${{ jobs.quality.outputs.type-errors }}
```

**Implementation:**
- Run checks in parallel when possible
- Continue on type errors (configurable)
- Report type error count as output
- Artifact upload for type check results

---

### 4. `build-package.yml`

**Purpose:** Build and validate Python packages

**Inputs:**
```yaml
inputs:
  package-path:
    description: 'Path to package (e.g., platform/primitives)'
    required: true
    type: string
  python-version:
    description: 'Python version to use'
    required: false
    default: '3.11'
    type: string
  upload-artifact:
    description: 'Upload built package as artifact'
    required: false
    default: true
    type: boolean
  validate-manifest:
    description: 'Validate package manifest'
    required: false
    default: true
    type: boolean
```

**Outputs:**
```yaml
outputs:
  build-result:
    description: 'Build result (success/failure)'
    value: ${{ jobs.build.outputs.result }}
  package-version:
    description: 'Package version built'
    value: ${{ jobs.build.outputs.version }}
  artifact-name:
    description: 'Name of uploaded artifact'
    value: ${{ jobs.build.outputs.artifact }}
```

**Implementation:**
- Use `uv build` for package building
- Validate `pyproject.toml` and manifest
- Upload as GitHub artifact
- Support for monorepo package paths

---

## Updated Workflow Designs

### PR Validation (Using Reusable Workflows)

```yaml
name: PR Validation

on:
  pull_request:
    types: [opened, synchronize, reopened]

concurrency:
  group: pr-${{ github.event.pull_request.number }}
  cancel-in-progress: true

jobs:
  quality-checks:
    uses: ./.github/workflows/reusable/quality-checks.yml
    with:
      python-version: '3.11'
      fail-on-type-errors: false

  unit-tests:
    uses: ./.github/workflows/reusable/run-tests.yml
    with:
      test-type: 'unit'
      python-version: '["3.11"]'
      coverage: false
      pytest-markers: 'not integration and not slow'
```

**Benefits:**
- ✅ 90% less code than current workflow
- ✅ Same behavior as validated Phase 1
- ✅ Easy to add new checks (just add job)
- ✅ Maintainable and testable

---

### Merge Validation (Using Reusable Workflows)

```yaml
name: Merge Validation

on:
  push:
    branches: [main]

jobs:
  quality-checks:
    uses: ./.github/workflows/reusable/quality-checks.yml
    with:
      python-version: '3.11'
      fail-on-type-errors: false

  comprehensive-tests:
    uses: ./.github/workflows/reusable/run-tests.yml
    with:
      test-type: 'unit'
      python-version: '["3.11", "3.12"]'
      coverage: true
      pytest-markers: 'not integration and not slow'

  integration-tests:
    needs: comprehensive-tests
    uses: ./.github/workflows/reusable/run-tests.yml
    with:
      test-type: 'integration'
      python-version: '["3.11"]'
      coverage: false
      pytest-markers: 'integration'

  quality-gates:
    needs: [quality-checks, comprehensive-tests, integration-tests]
    runs-on: ubuntu-latest
    steps:
      - name: All checks passed
        run: echo "✅ All quality gates passed"
```

**Benefits:**
- ✅ 85% less code than current workflow
- ✅ Clear dependency chain
- ✅ Easy to modify (change inputs, not logic)
- ✅ Matrix strategy built-in

---

## Implementation Strategy

### Step 1: Create Reusable Workflows (In Order)

1. **`quality-checks.yml`** - Simplest, no dependencies
2. **`setup-python.yml`** - Used by others (if needed separately)
3. **`run-tests.yml`** - Core testing infrastructure
4. **`build-package.yml`** - Package-specific logic

### Step 2: Test Each Reusable Workflow

Create test workflows in `.github/workflows/test/` that call each reusable workflow with different inputs:

```yaml
# .github/workflows/test/test-quality-checks.yml
name: Test Quality Checks Workflow

on:
  workflow_dispatch:

jobs:
  test-quality-checks:
    uses: ./.github/workflows/reusable/quality-checks.yml
    with:
      python-version: '3.11'
      fail-on-type-errors: false
```

### Step 3: Migrate PR Validation

1. Create new `pr-validation-v2.yml` using reusable workflows
2. Run both old and new workflows in parallel for 1 week
3. Compare results and metrics
4. Swap to v2, disable old workflow

### Step 4: Migrate Merge Validation

1. Create new `merge-validation-v2.yml` using reusable workflows
2. Run both old and new workflows in parallel for 1 week
3. Compare results and metrics
4. Swap to v2, disable old workflow

### Step 5: Cleanup

1. Delete old workflow files
2. Update documentation
3. Archive test workflows

---

## Validation Criteria

Each reusable workflow must:

- [ ] Accept documented inputs
- [ ] Produce documented outputs
- [ ] Work with matrix strategy
- [ ] Handle errors gracefully
- [ ] Complete in <5 minutes (individually)
- [ ] Cache dependencies effectively
- [ ] Work from any caller workflow
- [ ] Pass test workflow execution

---

## Benefits Summary

### Developer Experience

- **Faster PR feedback** - 25s for quality checks
- **Consistent behavior** - Same tests everywhere
- **Easy customization** - Change inputs, not logic
- **Better errors** - Clear workflow names and outputs

### Maintainability

- **DRY compliance** - No duplicated workflow logic
- **Centralized fixes** - Update once, applies everywhere
- **Version control** - Workflow changes tracked in git
- **Easy testing** - Test workflows in isolation

### Performance

- **Maintained speed** - Same 25s PR, 45s merge times
- **Parallel execution** - Jobs run concurrently
- **Smart caching** - Composite action + workflow caching
- **Matrix optimization** - Only necessary combinations

---

## Migration Timeline

### Week 1: Creation (Nov 6-13)
- Create all 4 reusable workflows
- Create test workflows
- Test each in isolation
- Document inputs/outputs

### Week 2: Integration (Nov 13-20)
- Create v2 PR validation workflow
- Create v2 merge validation workflow
- Run old + new in parallel
- Compare metrics

### Week 3: Validation (Nov 20-27)
- Monitor for differences
- Fix any issues
- Collect team feedback
- Approve for migration

### Week 4: Migration (Nov 27-Dec 4)
- Swap to v2 workflows
- Disable old workflows
- Monitor for 1 week
- Delete old workflows

---

## Risk Assessment

### Low Risk
✅ Reusable workflows are GitHub-native feature
✅ Phase 1 validated the actual logic
✅ Can run old + new workflows in parallel
✅ Easy rollback (just disable v2)

### Medium Risk
⚠️ Learning curve for workflow syntax
⚠️ Potential for input/output mismatches
⚠️ Need comprehensive testing

### Mitigation
- Test each workflow in isolation first
- Run old + new in parallel for comparison
- Document all inputs/outputs clearly
- Get team review before migration

---

## Success Metrics

| Metric | Current (Phase 1) | Target (Phase 2) | How to Measure |
|--------|-------------------|------------------|----------------|
| PR Validation Time | 25s | <30s | GitHub Actions runtime |
| Merge Validation Time | 45s | <60s | GitHub Actions runtime |
| Workflow Code Reduction | N/A | >80% | Lines of YAML |
| Reusability | 0 workflows | 4 workflows | Count of reusable workflows |
| Caller Simplification | N/A | <20 lines | PR/merge workflow size |
| Test Coverage | 0% | 100% | Test workflows passing |

---

## Next Actions

### Immediate (This Session)

1. ✅ Create Phase 2 plan (this document)
2. ⏳ Create `quality-checks.yml` reusable workflow
3. ⏳ Create test workflow for quality-checks
4. ⏳ Validate quality-checks works

### Short-term (This Week)

1. Create `run-tests.yml` reusable workflow
2. Create `build-package.yml` reusable workflow
3. Create test workflows for each
4. Create v2 PR validation workflow
5. Create v2 merge validation workflow

### Medium-term (Next 2 Weeks)

1. Run old + new workflows in parallel
2. Collect metrics and compare
3. Get team review
4. Migrate to v2 workflows
5. Cleanup old workflows

---

## Questions for Team Review

Before proceeding with full implementation:

1. **Matrix Strategy:** Should we test on Python 3.11 + 3.12 for all PRs, or only on merge?
2. **Integration Tests:** Run on every PR or only on merge to main?
3. **Type Errors:** Should we fail PRs on type errors, or just report?
4. **Coverage Threshold:** What's the minimum coverage percentage to enforce?
5. **Timeout Values:** Are 10-minute test timeouts appropriate?

---

## Related Documentation

- Phase 1 Validation: `docs/WORKFLOW_REBUILD_VALIDATION_COMPLETE.md`
- Overall Plan: `docs/WORKFLOW_REBUILD_PLAN.md`
- Quick Reference: `docs/WORKFLOW_REBUILD_QUICKSTART.md`
- Diagrams: `docs/WORKFLOW_REBUILD_DIAGRAMS.md`

---

**Ready to proceed with implementation!** 🚀

**Next Step:** Create `quality-checks.yml` reusable workflow and test it.
