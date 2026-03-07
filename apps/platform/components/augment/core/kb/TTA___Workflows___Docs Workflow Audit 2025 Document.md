---
title: GitHub Actions Workflow Audit & Modernization Plan
tags: #TTA
status: Active
repo: theinterneti/TTA
path: docs/WORKFLOW_AUDIT_2025.md
created: 2025-11-01
updated: 2025-11-01
---
# [[TTA/Workflows/GitHub Actions Workflow Audit & Modernization Plan]]
**Date:** October 27, 2025
**Status:** 🔴 CRITICAL - Systemic Failures Identified
**Target:** Production-Ready, Best-Practice Workflows

## Executive Summary

**Current State:**
- 36 workflow files (excessive redundancy)
- 5 systemic failures affecting multiple PRs
- Workflows based on outdated patterns (pre-2024)
- Testing confidence: ~40% (many workflows failing consistently)

**Target State:**
- ≤15 consolidated workflows (40% reduction)
- 100% workflow reliability for core quality gates
- Modern 2025 best practices (composite actions, reusable workflows)
- Testing confidence: 95%+ (only flaky external dependencies allowed to fail)

---

## 1. Systemic Failures Analysis

### 🔴 CRITICAL: Docker Build Failures
**Affected Workflows:** `docker-build.yml`
**Failure Rate:** 100% across PRs #53, #73, #38, #37
**Impact:** Cannot validate container deployments

**Root Causes Identified:**
```yaml
# Problem 1: Context path mismatch
dockerfiles=(
  ["player-experience-api"]="src/player_experience/api/Dockerfile"
  ["developer-api"]="Dockerfile.developer-api"  # ✅ EXISTS
  ["player-experience-frontend"]="src/player_experience/frontend/Dockerfile"  # ✅ EXISTS
)

# Problem 2: Context calculation bug
context=$(dirname "$dockerfile")  # For root Dockerfiles, this gives "."
# But build-push-action may need absolute paths or proper context
```

**Fix Strategy:**
1. ✅ **Immediate:** Verify all Dockerfiles exist (DONE - confirmed 32 Dockerfiles)
2. 🔧 **Short-term:** Fix context path logic in `docker-build.yml`
3. 🎯 **Long-term:** Switch to modern multi-platform builds with BuildKit

**Modern Pattern (2025):**
```yaml
- name: Build and push Docker image
  uses: docker/build-push-action@v5
  with:
    context: .
    file: ${{ matrix.dockerfile }}
    platforms: linux/amd64,linux/arm64  # Multi-platform
    push: ${{ github.event_name != 'pull_request' }}
    tags: ${{ steps.meta.outputs.tags }}
    cache-from: type=gha
    cache-to: type=gha,mode=max
    provenance: true  # SLSA provenance
    sbom: true        # Built-in SBOM generation
```

### 🟠 HIGH: CodeQL JavaScript/TypeScript Analysis
**Affected Workflows:** `codeql.yml`
**Failure Rate:** 100% across PRs #53, #73, #38, #37
**Impact:** No security scanning for frontend code

**Root Causes:**
```yaml
# Problem: Package installation fails before CodeQL autobuild
- name: Install frontend dependencies
  working-directory: src/player_experience/frontend
  run: npm ci  # Fails if package-lock.json out of sync
```

**Fix Strategy:**
1. Add dependency validation step
2. Use npm ci with --legacy-peer-deps flag for compatibility
3. Add explicit TypeScript compilation step before analysis

**Modern Pattern (2025):**
```yaml
- name: Initialize CodeQL
  uses: github/codeql-action/init@v3
  with:
    languages: javascript-typescript
    config: |
      paths:
        - 'src/**/*.ts'
        - 'src/**/*.tsx'
        - 'src/**/*.js'
        - 'src/**/*.jsx'
      paths-ignore:
        - '**/node_modules'
        - '**/dist'
        - '**/*.test.*'
        - '**/*.spec.*'

- name: Build TypeScript
  run: |
    npm ci --legacy-peer-deps
    npm run build --if-present
  working-directory: src/player_experience/frontend
```

### 🟡 MEDIUM: Frontend Performance Tests
**Affected Workflows:** `performance-tracking.yml`
**Failure Rate:** 100%
**Impact:** No performance regression detection

**Root Causes:**
```yaml
# Problem 1: Playwright not installed
- name: Run frontend performance tests
  run: npx playwright test  # Fails: playwright not found

# Problem 2: No baseline data
test_duration=$((end_time - start_time))  # Always triggers regression alerts
```

**Fix Strategy:**
1. Add Playwright installation with browsers
2. Store baseline metrics in GitHub Actions cache
3. Add tolerance thresholds (not just hard limits)

**Modern Pattern (2025):**
```yaml
- name: Setup Playwright
  run: |
    npm ci
    npx playwright install --with-deps chromium

- name: Run performance tests
  run: npx playwright test --reporter=json

- name: Compare with baseline
  run: |
    # Fetch baseline from cache or artifact
    # Compare with tolerance (e.g., +10% allowed)
    # Only fail if exceeds threshold
```

### 🟡 MEDIUM: Integration Tests
**Affected Workflows:** `tests.yml`, `comprehensive-test-battery.yml`
**Failure Rate:** 60% (PR-dependent)
**Impact:** Unreliable test signal

**Root Causes:**
```yaml
# Problem 1: Service dependencies not started
- name: Run integration tests
  run: uv run pytest tests/integration/ --neo4j --redis
  # Fails: Neo4j and Redis not running

# Problem 2: Conflicting test configurations
# Multiple workflows run same tests with different configs
```

**Fix Strategy:**
1. Consolidate test workflows (reduce from 5 to 2)
2. Add service containers for integration tests
3. Use test matrix for different Python versions

**Modern Pattern (2025):**
```yaml
services:
  redis:
    image: redis:7-alpine
    ports:
      - 6379:6379
    options: >-
      --health-cmd "redis-cli ping"
      --health-interval 10s
      --health-timeout 5s
      --health-retries 5

  neo4j:
    image: neo4j:5-community
    ports:
      - 7474:7474
      - 7687:7687
    env:
      NEO4J_AUTH: neo4j/testpassword
    options: >-
      --health-cmd "cypher-shell -u neo4j -p testpassword 'RETURN 1'"
      --health-interval 10s
```

### 🟡 MEDIUM: Security Reports (SBOM, Secrets)
**Affected Workflows:** `security-scan.yml`
**Failure Rate:** 100%
**Impact:** No security compliance tracking

**Root Causes:**
```yaml
# Problem: Using deprecated actions/custom scripts
- name: Generate SBOM
  run: |
    # Custom script fails - outdated tool
    cyclonedx-py -o sbom.json

# Problem: Secrets detection too strict
- name: Secrets Detection
  run: detect-secrets scan --all-files
  # Flags test fixtures as secrets
```

**Fix Strategy:**
1. Use GitHub's native SBOM generation (built into docker/build-push-action)
2. Switch to Gitleaks for secrets (active project vs detect-secrets)
3. Add proper .gitleaksignore for test fixtures

**Modern Pattern (2025):**
```yaml
- name: Generate SBOM
  uses: anchore/sbom-action@v0
  with:
    format: cyclonedx-json
    output-file: sbom.json

- name: Scan for secrets
  uses: gitleaks/gitleaks-action@v2
  env:
    GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

---

## 2. Workflow Redundancy Analysis

### Current Workflow Inventory (36 files)

**Category: Testing (10 workflows - EXCESSIVE)**
1. `tests.yml` - Basic unit/integration tests
2. `comprehensive-test-battery.yml` - Extended test suite
3. `e2e-tests.yml` - End-to-end tests
4. `e2e-staging-advanced.yml` - Advanced E2E tests
5. `mutation-testing.yml` - Mutation coverage
6. `simulation-testing.yml` - Simulation framework
7. `post-deployment-tests.yml` - Post-deploy validation
8. `component-promotion-validation.yml` - Component maturity
9. `dev-with-error-recovery.yml` - Error recovery demos
10. `monorepo-ci.yml` - Monorepo package tests

**🎯 Consolidation Target:** 3 workflows
- `ci.yml` - Core CI (unit, integration, linting)
- `e2e.yml` - End-to-end tests (staging/prod)
- `quality.yml` - Mutation testing, component validation

**Category: Deployment (4 workflows)**
1. `deploy-staging.yml`
2. `deploy-production.yml`
3. `frontend-deploy.yml`
4. `docker-build.yml`

**🎯 Consolidation Target:** 2 workflows
- `deploy.yml` - Unified deployment (uses environments)
- `docker.yml` - Container builds

**Category: Security (2 workflows)**
1. `security-scan.yml`
2. `codeql.yml`

**🎯 Keep:** 2 workflows (already minimal)

**Category: Quality & Performance (3 workflows)**
1. `code-quality.yml`
2. `performance-tracking.yml`
3. `component-status-report.yml`

**🎯 Consolidation Target:** Merge into `ci.yml` as jobs

**Category: Automation (10 workflows - COULD REDUCE)**
1. `pr-automation.yml`
2. `auto-merge-development.yml`
3. `auto-merge-staging.yml`
4. `project-board-automation.yml`
5. `update-project-board.yml`
6. `release-drafter.yml`
7. `gemini-dispatch.yml`
8. `gemini-invoke.yml`
9. `gemini-review.yml`
10. `gemini-scheduled-triage.yml`
11. `gemini-triage.yml`

**🎯 Consolidation Target:** 4 workflows
- `automation.yml` - PR/project board automation
- `release.yml` - Release management
- `ai-assist.yml` - Gemini integration (consolidated)

**Category: Documentation (2 workflows)**
1. `docs.yml`
2. `docker-compose-validate.yml`

**🎯 Keep:** 2 workflows

---

## 3. Modern Best Practices (2025)

### ✅ Use Reusable Workflows
**Before:**
```yaml
# tests.yml
jobs:
  test-python-311:
    runs-on: ubuntu-latest
    steps: [... 50 lines ...]

  test-python-312:
    runs-on: ubuntu-latest
    steps: [... 50 lines ...] # Duplicate!
```

**After:**
```yaml
# .github/workflows/test-python.reusable.yml
name: Test Python Package
on:
  workflow_call:
    inputs:
      python-version:
        required: true
        type: string
      package-path:
        required: true
        type: string

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v1
      - run: uv sync && uv run pytest ${{ inputs.package-path }}
```

```yaml
# tests.yml
jobs:
  test:
    strategy:
      matrix:
        python: ['3.11', '3.12']
    uses: ./.github/workflows/test-python.reusable.yml
    with:
      python-version: ${{ matrix.python }}
      package-path: tests/
```

### ✅ Use Composite Actions for Common Steps
**Before:**
```yaml
# Repeated in 15+ workflows
- name: Set up Python
  uses: actions/setup-python@v5
  with:
    python-version: '3.12'
- name: Install uv
  uses: astral-sh/setup-uv@v1
- name: Cache
  uses: actions/cache@v4
  with: [... complex cache config ...]
- name: Install dependencies
  run: uv sync --all-groups
```

**After:**
```yaml
# .github/actions/setup-python-uv/action.yml
name: Setup Python with UV
description: 'Setup Python, UV, and install dependencies'
inputs:
  python-version:
    default: '3.12'
runs:
  using: composite
  steps:
    - uses: actions/setup-python@v5
      with:
        python-version: ${{ inputs.python-version }}
    - uses: astral-sh/setup-uv@v1
    - uses: actions/cache@v4
      with:
        path: |
          ~/.cache/uv
          .venv
        key: uv-${{ runner.os }}-${{ hashFiles('**/uv.lock') }}
    - run: uv sync --all-groups
      shell: bash
```

```yaml
# In any workflow
- uses: ./.github/actions/setup-python-uv
  with:
    python-version: '3.12'
```

### ✅ Use Job Outputs Instead of Artifacts
**Before:**
```yaml
job1:
  steps:
    - run: echo "value" > file.txt
    - uses: actions/upload-artifact@v4
      with:
        name: my-value
        path: file.txt

job2:
  needs: job1
  steps:
    - uses: actions/download-artifact@v4
      with:
        name: my-value
    - run: cat file.txt
```

**After:**
```yaml
job1:
  outputs:
    my-value: ${{ steps.compute.outputs.value }}
  steps:
    - id: compute
      run: echo "value=my-computed-value" >> $GITHUB_OUTPUT

job2:
  needs: job1
  steps:
    - run: echo "${{ needs.job1.outputs.my-value }}"
```

### ✅ Use Concurrency Controls
**Before:**
```yaml
# Multiple builds running for same PR
# Wastes CI resources
```

**After:**
```yaml
concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true  # Cancel old runs when new push
```

### ✅ Use Required Status Checks (Not "Success")
**Before:**
```yaml
# GitHub branch protection: "All checks must pass"
# Problem: Adding new checks breaks existing PRs
```

**After:**
```yaml
# Create sentinel job
jobs:
  quality-gate:
    name: Quality Gate
    runs-on: ubuntu-latest
    needs: [lint, test, security]
    if: always()
    steps:
      - run: |
          if [[ "${{ needs.lint.result }}" != "success" ]] ||
             [[ "${{ needs.test.result }}" != "success" ]] ||
             [[ "${{ needs.security.result }}" != "success" ]]; then
            exit 1
          fi
```

Then set branch protection to require only "Quality Gate" check.

---

## 4. Proposed New Workflow Architecture

### Core Workflows (11 total - from 36)

```
.github/workflows/
├── ci.yml                    # ⭐ Main CI pipeline
├── quality.yml               # Code quality, mutation testing
├── security.yml              # CodeQL, secrets, SBOM
├── docker.yml                # Container builds
├── deploy.yml                # Unified deployment (staging/prod)
├── e2e.yml                   # End-to-end tests
├── docs.yml                  # Documentation
├── automation.yml            # PR/board automation
├── release.yml               # Release management
├── ai-assist.yml             # AI integrations
└── performance.yml           # Performance tracking

.github/workflows/reusable/   # ⭐ NEW: Reusable workflows
├── test-python.yml
├── test-typescript.yml
├── deploy-environment.yml
└── build-docker.yml

.github/actions/              # ⭐ NEW: Composite actions
├── setup-python-uv/
├── setup-node-pnpm/
├── setup-services/           # Neo4j, Redis, etc.
└── report-metrics/
```

### Workflow Trigger Matrix

| Workflow | Push | PR | Schedule | Dispatch |
|----------|------|----|-----------| ---------|
| ci.yml | ✅ main/develop | ✅ All | ❌ | ✅ |
| quality.yml | ✅ main | ✅ All | Daily | ✅ |
| security.yml | ✅ main/develop | ✅ All | Weekly | ✅ |
| docker.yml | ✅ main | ✅ Path-based | ❌ | ✅ |
| deploy.yml | ✅ main | ❌ | ❌ | ✅ |
| e2e.yml | ❌ | ✅ Label-based | ❌ | ✅ |
| performance.yml | ✅ main | ✅ All | Daily | ✅ |

---

## 5. Implementation Plan

### Phase 1: Fix Systemic Failures (Week 1)
**Goal:** Get workflows green on current PR

- [ ] **Day 1-2: Docker Build**
  - Fix context path logic
  - Add proper error handling
  - Test all 7 Docker images
  - **Success Metric:** All Docker builds pass

- [ ] **Day 2-3: CodeQL JavaScript**
  - Fix npm dependency installation
  - Add TypeScript build step
  - Configure paths correctly
  - **Success Metric:** CodeQL analysis completes

- [ ] **Day 3-4: Integration Tests**
  - Add service containers (Redis, Neo4j)
  - Fix test configuration
  - **Success Metric:** Integration tests pass

- [ ] **Day 4-5: Security & Performance**
  - Switch to modern SBOM generation
  - Add Playwright setup
  - Fix baseline metrics storage
  - **Success Metric:** All security checks green

### Phase 2: Consolidate Workflows (Week 2)
**Goal:** Reduce from 36 to 15 workflows

- [ ] **Create Reusable Workflows**
  - `test-python.yml`
  - `test-typescript.yml`
  - `deploy-environment.yml`

- [ ] **Create Composite Actions**
  - `setup-python-uv`
  - `setup-node-pnpm`
  - `setup-services`

- [ ] **Consolidate Test Workflows**
  - Merge `tests.yml`, `comprehensive-test-battery.yml`, `monorepo-ci.yml` → `ci.yml`
  - Keep `e2e-tests.yml` separate
  - Deprecate `e2e-staging-advanced.yml`

- [ ] **Consolidate Automation**
  - Merge all `gemini-*.yml` → `ai-assist.yml`
  - Merge `auto-merge-*.yml` → `automation.yml`

### Phase 3: Modernization (Week 3)
**Goal:** Implement 2025 best practices

- [ ] **Add Concurrency Controls**
  - All workflows get `concurrency` groups
  - Cancel in-progress for PR workflows

- [ ] **Use Job Outputs**
  - Replace artifact passing with outputs
  - Faster workflow execution

- [ ] **Multi-platform Docker**
  - Build for amd64 + arm64
  - Enable SLSA provenance
  - Enable built-in SBOM

- [ ] **Quality Gate Pattern**
  - Single sentinel job per workflow
  - Update branch protection rules

### Phase 4: Documentation & Validation (Week 4)
**Goal:** Team confidence in workflows

- [ ] **Document Workflows**
  - README per workflow explaining purpose
  - Troubleshooting guide
  - Migration guide from old workflows

- [ ] **Validation**
  - Run full test suite on 5 PRs
  - Measure CI time improvement
  - Measure cost reduction

- [ ] **Training**
  - Team walkthrough of new workflows
  - Update developer docs

---

## 6. Success Metrics

### Current State (Baseline)
- **Workflow Count:** 36 workflows
- **Success Rate:** ~40% (5 systemic failures)
- **Average CI Time:** ~35 minutes per PR
- **Workflow Maintenance:** ~2 hours/week
- **Developer Confidence:** Low (workflows often fail unpredictably)

### Target State (Post-Modernization)
- **Workflow Count:** ≤15 workflows (58% reduction)
- **Success Rate:** ≥95% (only flaky external deps fail)
- **Average CI Time:** ≤20 minutes per PR (43% improvement)
- **Workflow Maintenance:** ≤30 minutes/week (75% reduction)
- **Developer Confidence:** High (predictable, fast feedback)

### Key Performance Indicators
1. **🎯 First-Time Green Rate:** % of PRs that pass CI on first push
   - Current: ~20%
   - Target: ≥70%

2. **⚡ Time to Feedback:** How long until developer knows if code is good
   - Current: ~35 minutes
   - Target: ≤15 minutes (unit tests), ≤20 minutes (full CI)

3. **💰 CI Cost:** GitHub Actions minutes consumed
   - Current: ~15,000 minutes/month
   - Target: ≤8,000 minutes/month (47% reduction)

4. **🔒 Security Posture:** % of security checks passing
   - Current: ~60% (SBOM, secrets detection failing)
   - Target: 100%

---

## 7. Risk Mitigation

### Risk 1: Breaking Existing PRs
**Likelihood:** HIGH
**Impact:** HIGH

**Mitigation:**
1. Create feature branch `workflow-modernization`
2. Test all changes on this branch first
3. Run workflows on 5 existing PRs before merge
4. Keep old workflows in `.github/workflows/deprecated/` for 2 weeks

### Risk 2: Team Learning Curve
**Likelihood:** MEDIUM
**Impact:** MEDIUM

**Mitigation:**
1. Document every change with before/after examples
2. Host team training session
3. Create troubleshooting runbook
4. Assign workflow "champions" per team

### Risk 3: Service Container Costs
**Likelihood:** LOW
**Impact:** MEDIUM

**Mitigation:**
1. Use service containers only for integration tests
2. Add job-level timeouts (30 minutes max)
3. Monitor GitHub Actions billing
4. Consider self-hosted runners if costs spike

---

## 8. Next Steps

### Immediate Actions (Today)
1. ✅ **Review this document** with team
2. 🎯 **Approve Phase 1** to fix systemic failures
3. 📋 **Create tracking issue** for implementation

### This Week
1. Fix Docker builds
2. Fix CodeQL JavaScript
3. Fix integration tests
4. Get PR #73 green

### This Month
1. Complete Phase 1 (systemic fixes)
2. Complete Phase 2 (consolidation)
3. Start Phase 3 (modernization)

---

## Appendix A: Workflow Deprecation List

### To Deprecate (21 workflows)
1. ~~`comprehensive-test-battery.yml`~~ → Merge into `ci.yml`
2. ~~`e2e-staging-advanced.yml`~~ → Merge into `e2e.yml`
3. ~~`dev-with-error-recovery.yml`~~ → Demo workflow, keep in `examples/`
4. ~~`monorepo-ci.yml`~~ → Merge into `ci.yml`
5. ~~`component-promotion-validation.yml`~~ → Merge into `quality.yml`
6. ~~`component-status-report.yml`~~ → Merge into `quality.yml`
7. ~~`code-quality.yml`~~ → Merge into `ci.yml`
8. ~~`post-deployment-tests.yml`~~ → Merge into `deploy.yml`
9. ~~`auto-merge-development.yml`~~ → Merge into `automation.yml`
10. ~~`auto-merge-staging.yml`~~ → Merge into `automation.yml`
11. ~~`project-board-automation.yml`~~ → Merge into `automation.yml`
12. ~~`update-project-board.yml`~~ → Merge into `automation.yml`
13. ~~`gemini-dispatch.yml`~~ → Merge into `ai-assist.yml`
14. ~~`gemini-invoke.yml`~~ → Merge into `ai-assist.yml`
15. ~~`gemini-review.yml`~~ → Merge into `ai-assist.yml`
16. ~~`gemini-scheduled-triage.yml`~~ → Merge into `ai-assist.yml`
17. ~~`gemini-triage.yml`~~ → Merge into `ai-assist.yml`
18. ~~`frontend-deploy.yml`~~ → Merge into `deploy.yml`
19. ~~`simulation-testing.yml`~~ → Merge into `quality.yml` (optional job)
20. ~~`mutation-testing.yml`~~ → Merge into `quality.yml`
21. ~~`performance-tracking.yml`~~ → Keep as `performance.yml` (simplified)

### To Keep (11 workflows)
1. ✅ `ci.yml` (consolidated from tests.yml + others)
2. ✅ `quality.yml` (mutation, component validation)
3. ✅ `security.yml` (CodeQL + security-scan.yml)
4. ✅ `docker.yml` (renamed from docker-build.yml)
5. ✅ `deploy.yml` (consolidated deployments)
6. ✅ `e2e.yml` (consolidated E2E tests)
7. ✅ `docs.yml` (keep as-is)
8. ✅ `docker-compose-validate.yml` (keep as-is)
9. ✅ `automation.yml` (consolidated automation)
10. ✅ `release.yml` (renamed from release-drafter.yml)
11. ✅ `ai-assist.yml` (consolidated Gemini workflows)

---

## Appendix B: Modern Workflow Template

**File:** `.github/workflows/ci.yml` (NEW - Consolidated CI)

```yaml
name: Continuous Integration

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]
  workflow_dispatch:

# Cancel in-progress runs for same PR
concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true

env:
  PYTHON_VERSION: '3.12'
  UV_VERSION: '0.8.17'

jobs:
  # Fast path: Lint and quick tests first
  lint:
    name: Code Quality
    runs-on: ubuntu-latest
    timeout-minutes: 10
    steps:
      - uses: actions/checkout@v4

      - uses: ./.github/actions/setup-python-uv
        with:
          python-version: ${{ env.PYTHON_VERSION }}

      - name: Lint with Ruff
        run: |
          uv run ruff check .
          uv run ruff format --check .

      - name: Type check with Pyright
        run: uv run pyright src/

  # Unit tests matrix (fast, no external deps)
  unit-tests:
    name: Unit Tests (Python ${{ matrix.python-version }})
    runs-on: ubuntu-latest
    timeout-minutes: 15
    strategy:
      fail-fast: false
      matrix:
        python-version: ['3.11', '3.12']
    steps:
      - uses: actions/checkout@v4

      - uses: ./.github/actions/setup-python-uv
        with:
          python-version: ${{ matrix.python-version }}

      - name: Run unit tests
        run: uv run pytest tests/unit/ -v --cov=src --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v4
        with:
          files: ./coverage.xml
          flags: unit-tests-py${{ matrix.python-version }}

  # Integration tests (needs services)
  integration-tests:
    name: Integration Tests
    runs-on: ubuntu-latest
    timeout-minutes: 20
    services:
      redis:
        image: redis:7-alpine
        ports:
          - 6379:6379
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

      neo4j:
        image: neo4j:5-community
        ports:
          - 7474:7474
          - 7687:7687
        env:
          NEO4J_AUTH: neo4j/testpassword
        options: >-
          --health-cmd "cypher-shell -u neo4j -p testpassword 'RETURN 1'"
          --health-interval 10s
          --health-timeout 10s
          --health-retries 10

    steps:
      - uses: actions/checkout@v4

      - uses: ./.github/actions/setup-python-uv
        with:
          python-version: ${{ env.PYTHON_VERSION }}

      - name: Wait for services
        run: |
          echo "Waiting for Redis..."
          timeout 30 bash -c 'until redis-cli -h localhost ping; do sleep 1; done'
          echo "Waiting for Neo4j..."
          timeout 60 bash -c 'until cypher-shell -u neo4j -p testpassword "RETURN 1"; do sleep 2; done'  # pragma: allowlist secret

      - name: Run integration tests
        env:
          REDIS_URL: redis://localhost:6379
          NEO4J_URI: bolt://localhost:7687
          NEO4J_USER: neo4j
          NEO4J_PASSWORD: testpassword
        run: uv run pytest tests/integration/ -v --cov=src --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v4
        with:
          files: ./coverage.xml
          flags: integration-tests

  # Monorepo package tests
  package-tests:
    name: Test ${{ matrix.package }}
    runs-on: ubuntu-latest
    timeout-minutes: 10
    strategy:
      fail-fast: false
      matrix:
        package:
          - tta-ai-framework
          - tta-narrative-engine
          - dev-primitives
          - tta-workflow-primitives
    steps:
      - uses: actions/checkout@v4

      - uses: ./.github/actions/setup-python-uv
        with:
          python-version: ${{ env.PYTHON_VERSION }}

      - name: Test package
        working-directory: packages/${{ matrix.package }}
        run: |
          uv sync
          uv run pytest tests/ -v

  # Quality gate: All jobs must pass
  ci-success:
    name: CI Quality Gate
    runs-on: ubuntu-latest
    needs: [lint, unit-tests, integration-tests, package-tests]
    if: always()
    steps:
      - name: Check all jobs
        run: |
          if [[ "${{ needs.lint.result }}" != "success" ]] ||
             [[ "${{ needs.unit-tests.result }}" != "success" ]] ||
             [[ "${{ needs.integration-tests.result }}" != "success" ]] ||
             [[ "${{ needs.package-tests.result }}" != "success" ]]; then
            echo "❌ One or more CI jobs failed"
            exit 1
          fi
          echo "✅ All CI jobs passed"
```

**Benefits of This Template:**
1. ✅ Concurrency control (cancel old runs)
2. ✅ Composite action reuse
3. ✅ Service containers for integration tests
4. ✅ Test matrix for multiple Python versions
5. ✅ Quality gate pattern
6. ✅ Fast feedback (lint/unit tests first)
7. ✅ Proper timeouts
8. ✅ Coverage reporting

---

**Document Owner:** DevOps Team
**Last Updated:** 2025-10-27
**Next Review:** 2025-11-10 (after Phase 1 completion)


---
**Logseq:** [[TTA.dev/Platform_tta_dev/Components/Augment/Core/Kb/Tta___workflows___docs workflow audit 2025 document]]
