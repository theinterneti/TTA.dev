---
title: GitHub Workflows Recommendations for TTA Testing Strategy
tags: #TTA
status: Active
repo: theinterneti/TTA
path: docs/testing/GITHUB_WORKFLOWS_RECOMMENDATIONS.md
created: 2025-11-01
updated: 2025-11-01
---
# [[TTA/Workflows/GitHub Workflows Recommendations for TTA Testing Strategy]]

**Date:** 2025-10-03
**Related Document:** [[TTA/Workflows/TEST_COVERAGE_ANALYSIS|TEST_COVERAGE_ANALYSIS.md]]

---

## Overview

This document provides specific recommendations for modifying and enhancing the existing GitHub Actions workflows to align with the comprehensive testing strategy outlined in the Test Coverage Analysis.

---

## Current Workflow Assessment

### Existing Workflows

1. **`.github/workflows/tests.yml`** - Unit and integration tests with monitoring validation
2. **`.github/workflows/test-integration.yml`** - Comprehensive test battery with Redis
3. **`.github/workflows/e2e-tests.yml`** - Extensive E2E testing with Playwright
4. **`.github/workflows/code-quality.yml`** - Code quality checks
5. **`.github/workflows/security-scan.yml`** - Security scanning
6. **`.github/workflows/simulation-testing.yml`** - Simulation framework tests
7. **`.github/workflows/comprehensive-test-battery.yml`** - Comprehensive test battery

### Strengths

✅ Comprehensive coverage of different test types
✅ Proper use of service containers for databases
✅ Matrix strategy for browser/device testing
✅ Artifact upload for test results
✅ PR commenting with test results
✅ Scheduled runs for comprehensive testing

### Areas for Improvement

⚠️ **Workflow Consolidation:** Multiple overlapping workflows could be streamlined
⚠️ **Test Execution Time:** Some workflows may exceed target times
⚠️ **Mock Fallback:** Not all workflows have clear mock fallback strategies
⚠️ **Phase-based Testing:** No clear separation of Phase 1/2/3 tests
⚠️ **Coverage Reporting:** Coverage reports not consistently aggregated

---

## Recommended Workflow Structure

### Proposed Workflow Organization

```
.github/workflows/
├── pr-validation.yml           # Fast PR validation (< 5 min)
├── main-branch-tests.yml       # Full validation on main (< 30 min)
├── nightly-comprehensive.yml   # Nightly comprehensive tests (< 2 hours)
├── phase1-critical-path.yml    # Phase 1 critical path tests (on-demand)
├── phase2-user-experience.yml  # Phase 2 UX tests (on-demand)
├── phase3-robustness.yml       # Phase 3 robustness tests (on-demand)
├── code-quality.yml            # Code quality checks (keep as-is)
└── security-scan.yml           # Security scanning (keep as-is)
```

---

## Workflow Specifications

### 1. PR Validation Workflow

**File:** `.github/workflows/pr-validation.yml`

**Purpose:** Fast feedback for pull requests (< 5 minutes)

**Triggers:**
- Every pull request to `main` or `develop`

**Jobs:**
1. **Unit Tests** - All unit tests with mocks
2. **Linting** - ruff, mypy, eslint
3. **Security Scan** - Quick security checks
4. **Mock Integration Tests** - Comprehensive test battery with mocks

**Configuration:**

```yaml
name: PR Validation

on:
  pull_request:
    branches: [main, develop]

env:
  PYTHON_VERSION: '3.12'
  NODE_VERSION: '18'

jobs:
  unit-tests:
    runs-on: ubuntu-latest
    timeout-minutes: 5
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v1
      - name: Install dependencies
        run: uv sync --all-extras --dev
      - name: Run unit tests
        run: |
          uv run pytest -q --tb=short \
            -m "not neo4j and not redis and not integration" \
            --junitxml=test-results/unit-tests.xml \
            --cov=src --cov-report=xml:coverage-unit.xml
      - name: Upload results
        uses: actions/upload-artifact@v4
        if: always()
        with:
          name: unit-test-results
          path: |
            test-results/
            coverage-unit.xml

  linting:
    runs-on: ubuntu-latest
    timeout-minutes: 3
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v1
      - name: Install dependencies
        run: uv sync --all-extras --dev
      - name: Run ruff
        run: uv run ruff check .
      - name: Run mypy
        run: uv run mypy src/
        continue-on-error: true  # Don't fail PR on type errors yet
      - name: Run eslint (frontend)
        run: |
          cd src/player_experience/frontend
          npm ci
          npm run lint

  mock-integration-tests:
    runs-on: ubuntu-latest
    timeout-minutes: 5
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v1
      - name: Install dependencies
        run: uv sync --all-extras --dev
      - name: Run comprehensive test battery (mock mode)
        run: |
          python tests/comprehensive_battery/run_comprehensive_tests.py \
            --categories standard \
            --max-concurrent 2 \
            --timeout 300 \
            --log-level WARNING \
            --output-dir ./test-results/mock-integration
        env:
          FORCE_MOCK_MODE: "true"
      - name: Upload results
        uses: actions/upload-artifact@v4
        if: always()
        with:
          name: mock-integration-results
          path: test-results/

  pr-summary:
    runs-on: ubuntu-latest
    needs: [unit-tests, linting, mock-integration-tests]
    if: always()
    steps:
      - uses: actions/checkout@v4
      - name: Download all artifacts
        uses: actions/download-artifact@v4
        with:
          path: artifacts/
      - name: Generate PR comment
        uses: actions/github-script@v7
        with:
          script: |
            const fs = require('fs');
            let comment = '## 🧪 PR Validation Results\n\n';

            // Add job statuses
            const jobs = {
              'Unit Tests': '${{ needs.unit-tests.result }}',
              'Linting': '${{ needs.linting.result }}',
              'Mock Integration': '${{ needs.mock-integration-tests.result }}'
            };

            for (const [name, status] of Object.entries(jobs)) {
              const emoji = status === 'success' ? '✅' : '❌';
              comment += `${emoji} **${name}:** ${status}\n`;
            }

            // Add coverage info if available
            // ... (parse coverage.xml and add to comment)

            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: comment
            });
```

---

### 2. Main Branch Tests Workflow

**File:** `.github/workflows/main-branch-tests.yml`

**Purpose:** Full validation on main branch (< 30 minutes)

**Triggers:**
- Push to `main` branch
- Manual workflow dispatch

**Jobs:**
1. **Unit Tests** - All unit tests
2. **Integration Tests** - Real Neo4j + Redis
3. **Core E2E Tests** - Auth, dashboard, character management
4. **Performance Regression** - Check for performance degradation
5. **Coverage Report** - Aggregate and publish coverage

**Configuration:**

```yaml
name: Main Branch Tests

on:
  push:
    branches: [main]
  workflow_dispatch:

env:
  PYTHON_VERSION: '3.12'
  NODE_VERSION: '18'

jobs:
  unit-tests:
    runs-on: ubuntu-latest
    timeout-minutes: 10
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v1
      - name: Install dependencies
        run: uv sync --all-extras --dev
      - name: Run all unit tests
        run: |
          uv run pytest -q --tb=short \
            -m "not neo4j and not redis and not integration" \
            --junitxml=test-results/unit-tests.xml \
            --cov=src --cov-report=xml:coverage-unit.xml
      - name: Upload coverage
        uses: codecov/codecov-action@v4
        with:
          files: ./coverage-unit.xml
          flags: unit
          name: unit-tests

  integration-tests:
    runs-on: ubuntu-latest
    timeout-minutes: 15
    services:
      neo4j:
        image: neo4j:5-community
        env:
          NEO4J_AUTH: neo4j/testpassword
          NEO4J_ACCEPT_LICENSE_AGREEMENT: "yes"
        ports:
          - 7687:7687
        options: >-
          --health-cmd="/var/lib/neo4j/bin/cypher-shell -u neo4j -p testpassword 'RETURN 1'"
          --health-interval=10s --health-timeout=5s --health-retries=10
      redis:
        image: redis:7-alpine
        ports:
          - 6379:6379
        options: >-
          --health-cmd="redis-cli ping"
          --health-interval=5s --health-timeout=3s --health-retries=10
    env:
      TEST_NEO4J_URI: "bolt://localhost:7687"
      TEST_NEO4J_USERNAME: "neo4j"
      TEST_NEO4J_PASSWORD: "testpassword"
      TEST_REDIS_URI: "redis://localhost:6379/0"
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v1
      - name: Install dependencies
        run: uv sync --all-extras --dev
      - name: Run integration tests
        run: |
          uv run pytest -q --tb=short \
            --neo4j --redis \
            --junitxml=test-results/integration-tests.xml \
            --cov=src --cov-report=xml:coverage-integration.xml
      - name: Upload coverage
        uses: codecov/codecov-action@v4
        with:
          files: ./coverage-integration.xml
          flags: integration
          name: integration-tests

  core-e2e-tests:
    runs-on: ubuntu-latest
    timeout-minutes: 20
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: ${{ env.NODE_VERSION }}
          cache: 'npm'
      - name: Install dependencies
        run: |
          npm ci
          cd src/player_experience/frontend && npm ci
          cd ../../tests/e2e/mocks && npm install
      - name: Install Playwright
        run: npx playwright install --with-deps chromium
      - name: Start mock API
        run: |
          cd tests/e2e/mocks
          npm start &
          timeout 30 bash -c 'until curl -f http://localhost:8000/health; do sleep 2; done'
      - name: Start frontend
        run: |
          cd src/player_experience/frontend
          npm start &
          timeout 60 bash -c 'until curl -f http://localhost:3000; do sleep 2; done'
      - name: Run core E2E tests
        run: |
          npx playwright test \
            tests/e2e/specs/auth.spec.ts \
            tests/e2e/specs/dashboard.spec.ts \
            tests/e2e/specs/character-management.spec.ts \
            --project=chromium \
            --reporter=html,json
      - name: Upload results
        uses: actions/upload-artifact@v4
        if: always()
        with:
          name: e2e-results
          path: |
            test-results/
            playwright-report/

  performance-regression:
    runs-on: ubuntu-latest
    needs: [unit-tests, integration-tests]
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v1
      - name: Install dependencies
        run: uv sync --all-extras --dev
      - name: Run performance regression check
        run: |
          uv run python scripts/performance_regression_check.py \
            --test-results test-results/ \
            --baseline-branch main \
            --threshold 20
        continue-on-error: true
```

---

### 3. Nightly Comprehensive Tests

**File:** `.github/workflows/nightly-comprehensive.yml`

**Purpose:** Full comprehensive testing (< 2 hours)

**Triggers:**
- Scheduled: Daily at 2 AM UTC
- Manual workflow dispatch

**Jobs:**
1. **Full Test Suite** - All tests with real databases
2. **Extended E2E Tests** - All Playwright specs, all browsers
3. **Performance Tests** - Load testing with Locust
4. **Browser Compatibility** - Cross-browser testing
5. **Visual Regression** - Visual regression tests
6. **Simulation Framework** - Simulation tests

**Configuration:**

```yaml
name: Nightly Comprehensive Tests

on:
  schedule:
    - cron: '0 2 * * *'
  workflow_dispatch:

env:
  PYTHON_VERSION: '3.12'
  NODE_VERSION: '18'

jobs:
  full-test-suite:
    runs-on: ubuntu-latest
    timeout-minutes: 45
    services:
      neo4j:
        image: neo4j:5-community
        env:
          NEO4J_AUTH: neo4j/testpassword
          NEO4J_ACCEPT_LICENSE_AGREEMENT: "yes"
        ports:
          - 7687:7687
      redis:
        image: redis:7-alpine
        ports:
          - 6379:6379
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v1
      - name: Install dependencies
        run: uv sync --all-extras --dev
      - name: Run full test suite
        run: |
          uv run pytest --neo4j --redis \
            --cov=src --cov-report=html --cov-report=xml \
            --junitxml=test-results/full-suite.xml
      - name: Upload coverage
        uses: codecov/codecov-action@v4
        with:
          files: ./coverage.xml
          flags: comprehensive
          name: full-suite

  extended-e2e-tests:
    runs-on: ubuntu-latest
    timeout-minutes: 60
    strategy:
      fail-fast: false
      matrix:
        browser: [chromium, firefox, webkit]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: ${{ env.NODE_VERSION }}
      - name: Install dependencies
        run: |
          npm ci
          cd src/player_experience/frontend && npm ci
          cd ../../tests/e2e/mocks && npm install
      - name: Install Playwright
        run: npx playwright install --with-deps ${{ matrix.browser }}
      - name: Start test environment
        run: |
          cd tests/e2e/mocks && npm start &
          cd src/player_experience/frontend && npm start &
          sleep 30
      - name: Run all E2E tests
        run: |
          npx playwright test --project=${{ matrix.browser }} --reporter=html,json
      - name: Upload results
        uses: actions/upload-artifact@v4
        if: always()
        with:
          name: e2e-results-${{ matrix.browser }}
          path: |
            test-results/
            playwright-report/

  performance-tests:
    runs-on: ubuntu-latest
    timeout-minutes: 30
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v1
      - name: Install dependencies
        run: uv sync --all-extras --dev
      - name: Run load tests
        run: |
          cd testing/load_tests
          locust -f locustfile.py \
            --headless \
            --users 100 \
            --spawn-rate 10 \
            --run-time 10m \
            --html=load-test-report.html
      - name: Upload results
        uses: actions/upload-artifact@v4
        with:
          name: performance-results
          path: testing/load_tests/load-test-report.html
```

---

## Implementation Plan

### Phase 1: Workflow Consolidation (Week 1)

1. **Create `pr-validation.yml`** - New fast PR validation workflow
2. **Enhance `tests.yml`** → Rename to `main-branch-tests.yml` and enhance
3. **Create `nightly-comprehensive.yml`** - Consolidate nightly tests
4. **Update branch protection rules** - Require PR validation to pass

### Phase 2: Phase-Specific Workflows (Week 2)

1. **Create `phase1-critical-path.yml`** - On-demand Phase 1 tests
2. **Create `phase2-user-experience.yml`** - On-demand Phase 2 tests
3. **Create `phase3-robustness.yml`** - On-demand Phase 3 tests

### Phase 3: Monitoring and Optimization (Week 3)

1. **Add workflow monitoring** - Track execution times
2. **Optimize slow tests** - Parallelize where possible
3. **Add caching** - Cache dependencies and build artifacts
4. **Add notifications** - Slack/Discord notifications for failures

---

## Success Criteria

- ✅ PR validation completes in < 5 minutes
- ✅ Main branch tests complete in < 30 minutes
- ✅ Nightly tests complete in < 2 hours
- ✅ Test results visible in PR comments
- ✅ Coverage reports published to Codecov
- ✅ Flaky test rate < 1%
- ✅ All workflows use consistent naming and structure

---

**Document Version:** 1.0
**Last Updated:** 2025-10-03
**Status:** Ready for Implementation


---
**Logseq:** [[TTA.dev/Platform_tta_dev/Components/Augment/Core/Kb/Tta___workflows___docs testing github workflows recommendations document]]
