# Manual Testing Plan - Phase 5 APM Integration

**Purpose:** Validate all Hypertool workflows with APM instrumentation

**Date:** 2025-11-15
**Phase:** Phase 5 Week 3 - Manual Testing
**Estimated Duration:** 2-3 hours

---

## Testing Environment Setup

### Prerequisites

1. **Observability Stack Running:**
   ```bash
   # Check if Prometheus is running
   curl http://localhost:9090/-/healthy

   # Check if Grafana is running
   curl http://localhost:3000/api/health

   # If not running, start with:
   docker-compose -f docker-compose.test.yml up -d
   ```

2. **Langfuse Setup:**
   ```bash
   # Verify environment variables
   echo $LANGFUSE_PUBLIC_KEY
   echo $LANGFUSE_SECRET_KEY
   echo $LANGFUSE_HOST

   # If missing, add to .env:
   # LANGFUSE_PUBLIC_KEY=pk-lf-...
   # LANGFUSE_SECRET_KEY=sk-lf-...
   # LANGFUSE_HOST=https://cloud.langfuse.com
   ```

3. **Python Dependencies:**
   ```bash
   # Install required packages
   uv sync --all-extras

   # Verify Langfuse SDK
   python -c "import langfuse; print(f'Langfuse {langfuse.__version__}')"
   ```

---

## Test 1: Baseline Test - test_instrumented_workflow.py

**Purpose:** Verify all APM components work together

**Duration:** 5-10 minutes

### Execution Steps

1. **Run the test workflow:**
   ```bash
   cd /home/thein/repos/TTA.dev
   python -m .hypertool.instrumentation.test_instrumented_workflow
   ```

2. **Expected Output:**
   ```
   🚀 Starting Package Release Workflow
   ============================================================

   📝 Stage 1: Version Bump
      Persona: backend-engineer
      ✅ Backend task completed: Update version to 1.2.0
      📊 Tokens: 650
      💰 Budget remaining: 1350

   🧪 Stage 2: Quality Validation
      Persona: testing-specialist
      ✅ Testing task completed: Run full test suite
      📊 Tokens: 720
      💰 Budget remaining: 780

   🚀 Stage 3: Deployment
      Persona: devops-engineer
      ✅ DevOps task completed: Deploy: Deploy to production
      📊 Tokens: 550
      💰 Budget remaining: 1250

   ✅ Workflow Complete
   ```

3. **Verification Checklist:**

   - [ ] No Python errors or exceptions
   - [ ] All 3 personas switched successfully
   - [ ] Token budgets decreased appropriately
   - [ ] Workflow completed successfully
   - [ ] Langfuse trace URL printed (if configured)

### Data Validation

1. **Prometheus Metrics:**
   ```bash
   # Query persona switch count
   curl -G http://localhost:9090/api/v1/query \
     --data-urlencode 'query=hypertool_persona_switches_total'

   # Query token usage
   curl -G http://localhost:9090/api/v1/query \
     --data-urlencode 'query=hypertool_token_usage_total'

   # Query workflow duration
   curl -G http://localhost:9090/api/v1/query \
     --data-urlencode 'query=hypertool_workflow_stage_duration_seconds_sum'
   ```

2. **Expected Metrics:**
   - `hypertool_persona_switches_total` >= 2 (2 switches in workflow)
   - `hypertool_token_usage_total` >= 1920 (650 + 720 + 550)
   - `hypertool_workflow_stage_duration_seconds_count` = 3 (3 stages)

3. **Grafana Dashboards:**
   - Open http://localhost:3000
   - Navigate to "Persona Overview" dashboard
   - Verify data appears in all 5 panels
   - Navigate to "Workflow Performance" dashboard
   - Verify workflow stages appear

4. **Langfuse UI:**
   - Open https://cloud.langfuse.com (or your Langfuse instance)
   - Go to "Traces" section
   - Find trace named "package-release-workflow"
   - Verify:
     - Trace has 3 generations (one per stage)
     - Each generation shows persona and chatmode
     - Token counts match expected values
     - No errors in trace

### Issues to Watch For

- **Missing metrics:** Check Prometheus targets at http://localhost:9090/targets
- **No Langfuse traces:** Verify env vars and internet connectivity
- **Import errors:** Ensure `uv sync --all-extras` completed
- **Port conflicts:** Check if 9464 (Prometheus) is available

---

## Test 2: Augment Workflow - Feature Implementation

**Purpose:** Test real-world feature development workflow

**Duration:** 45-60 minutes

**Workflow File:** `.augment/workflows/feature-implementation-hypertool.prompt.md`

### Test Scenario

**Feature to Implement:** Add a simple health check endpoint

**Personas Used:**
1. Backend Engineer (API design)
2. Frontend Engineer (UI for health status - optional)
3. Testing Specialist (test implementation)

### Pre-Test Setup

1. **Create test branch:**
   ```bash
   git checkout -b test/manual-testing-feature-implementation
   ```

2. **Document start time:**
   ```bash
   echo "Test started: $(date)" >> .hypertool/testing_log.txt
   ```

### Execution Steps

1. **Stage 1: API Design (Backend Engineer)**

   **Persona Switch:**
   ```bash
   # Simulated - in real workflow, agent would switch
   echo "Switching to backend-engineer for API design"
   ```

   **Tasks:**
   - Create `packages/tta-dev-primitives/src/tta_dev_primitives/health.py`
   - Implement health check function:
     ```python
     from datetime import datetime
     from typing import Dict, Any

     async def get_health_status() -> Dict[str, Any]:
         """Return system health status."""
         return {
             "status": "healthy",
             "timestamp": datetime.utcnow().isoformat(),
             "version": "1.0.0",
             "components": {
                 "primitives": "ok",
                 "observability": "ok",
             }
         }
     ```

   **Verification:**
   - [ ] File created successfully
   - [ ] Code follows TTA.dev style (type hints, docstrings)
   - [ ] No import errors

2. **Stage 2: UI Component (Frontend Engineer)**

   **Persona Switch:**
   ```bash
   echo "Switching to frontend-engineer for UI"
   ```

   **Tasks:**
   - Create example health check display (simplified)
   - Document UI integration approach

   **Verification:**
   - [ ] Design documented
   - [ ] Integration points identified

3. **Stage 3: Testing (Testing Specialist)**

   **Persona Switch:**
   ```bash
   echo "Switching to testing-specialist for tests"
   ```

   **Tasks:**
   - Create test file:
     ```python
     # packages/tta-dev-primitives/tests/test_health.py
     import pytest
     from tta_dev_primitives.health import get_health_status

     @pytest.mark.asyncio
     async def test_health_status():
         """Test health check returns expected structure."""
         result = await get_health_status()

         assert result["status"] == "healthy"
         assert "timestamp" in result
         assert "version" in result
         assert "components" in result
     ```

   - Run tests:
     ```bash
     uv run pytest packages/tta-dev-primitives/tests/test_health.py -v
     ```

   **Verification:**
   - [ ] Test file created
   - [ ] Tests pass
   - [ ] Coverage acceptable

### APM Validation

1. **Metrics Check:**
   ```bash
   # Should show 2 persona switches
   curl -G http://localhost:9090/api/v1/query \
     --data-urlencode 'query=hypertool_persona_switches_total{workflow="feature_implementation"}'
   ```

2. **Grafana Check:**
   - View "Persona Overview" dashboard
   - Verify switches: backend-engineer → frontend-engineer → testing-specialist
   - Check token usage per persona

3. **Langfuse Check:**
   - Find trace named "feature-implementation-workflow"
   - Verify all stages captured
   - Review LLM calls made during implementation

### Success Criteria

- [ ] Feature implemented successfully
- [ ] All tests pass
- [ ] APM metrics captured correctly
- [ ] Persona switches recorded
- [ ] Token budgets tracked
- [ ] No errors in logs
- [ ] Workflow completed in expected time (< 60 min)

### Cleanup

```bash
# Revert test changes if not keeping
git reset --hard HEAD
git checkout agent/augment
git branch -D test/manual-testing-feature-implementation
```

---

## Test 3: Cline Workflow - Bug Fix

**Purpose:** Test bug investigation and fix workflow

**Duration:** 30-45 minutes

**Workflow File:** `.cline/workflows/bug-fix-hypertool.prompt.md`

### Test Scenario

**Simulated Bug:** Health check function returns incorrect timestamp format

**Personas Used:**
1. Observability Expert (investigation)
2. Backend Engineer (fix)
3. Testing Specialist (regression tests)

### Pre-Test Setup

1. **Create test branch:**
   ```bash
   git checkout -b test/manual-testing-bug-fix
   ```

2. **Introduce the bug:**
   ```python
   # Modify packages/tta-dev-primitives/src/tta_dev_primitives/health.py
   # Change timestamp format to introduce bug
   async def get_health_status() -> Dict[str, Any]:
       return {
           "status": "healthy",
           "timestamp": datetime.utcnow().strftime("%Y-%m-%d"),  # Bug: wrong format
           "version": "1.0.0",
       }
   ```

### Execution Steps

1. **Stage 1: Investigation (Observability Expert)**

   **Persona Switch:**
   ```bash
   echo "Switching to observability-expert for investigation"
   ```

   **Tasks:**
   - Review error logs (simulated)
   - Check Prometheus metrics
   - Identify root cause:
     ```
     Root Cause: timestamp format changed from ISO8601 to date-only
     Impact: Downstream systems expecting full timestamp failing
     ```

   **Verification:**
   - [ ] Root cause identified
   - [ ] Impact documented
   - [ ] Investigation notes recorded

2. **Stage 2: Fix (Backend Engineer)**

   **Persona Switch:**
   ```bash
   echo "Switching to backend-engineer for fix"
   ```

   **Tasks:**
   - Fix the bug:
     ```python
     async def get_health_status() -> Dict[str, Any]:
         return {
             "status": "healthy",
             "timestamp": datetime.utcnow().isoformat(),  # Fixed
             "version": "1.0.0",
             "components": {
                 "primitives": "ok",
                 "observability": "ok",
             }
         }
     ```

   - Add validation to prevent regression

   **Verification:**
   - [ ] Bug fixed
   - [ ] Validation added
   - [ ] Code reviewed

3. **Stage 3: Regression Tests (Testing Specialist)**

   **Persona Switch:**
   ```bash
   echo "Switching to testing-specialist for regression tests"
   ```

   **Tasks:**
   - Add regression test:
     ```python
     @pytest.mark.asyncio
     async def test_health_timestamp_format():
         """Ensure timestamp is ISO8601 format."""
         result = await get_health_status()

         # Verify ISO8601 format (includes time)
         assert "T" in result["timestamp"]
         assert result["timestamp"].endswith("Z") or "+" in result["timestamp"]

         # Verify parseable
         from datetime import datetime
         datetime.fromisoformat(result["timestamp"].replace("Z", "+00:00"))
     ```

   - Run all tests:
     ```bash
     uv run pytest packages/tta-dev-primitives/tests/test_health.py -v
     ```

   **Verification:**
   - [ ] Regression test added
   - [ ] All tests pass
   - [ ] Bug confirmed fixed

### APM Validation

1. **Metrics:**
   ```bash
   curl -G http://localhost:9090/api/v1/query \
     --data-urlencode 'query=hypertool_persona_switches_total{workflow="bug_fix"}'
   ```

2. **Grafana:**
   - View "Workflow Performance" dashboard
   - Check quality gate success rate
   - Verify no failed gates

3. **Langfuse:**
   - Find trace "bug-fix-workflow"
   - Review investigation LLM calls
   - Verify fix implementation calls

### Success Criteria

- [ ] Bug identified correctly
- [ ] Fix implemented successfully
- [ ] Regression tests added
- [ ] All tests pass
- [ ] APM captured all stages
- [ ] No errors in workflow

### Cleanup

```bash
git reset --hard HEAD
git checkout agent/augment
git branch -D test/manual-testing-bug-fix
```

---

## Test 4: GitHub Copilot Workflow - Package Release

**Purpose:** Test package release workflow

**Duration:** 30-45 minutes

**Workflow File:** `.github/workflows/package-release-hypertool.prompt.md`

### Test Scenario

**Release:** Bump patch version for tta-dev-primitives

**Personas Used:**
1. Backend Engineer (version bump)
2. Testing Specialist (validation)
3. DevOps Engineer (deployment)

### Pre-Test Setup

1. **Create release branch:**
   ```bash
   git checkout -b test/manual-testing-release
   ```

2. **Note current version:**
   ```bash
   grep "^version" packages/tta-dev-primitives/pyproject.toml
   ```

### Execution Steps

1. **Stage 1: Version Bump (Backend Engineer)**

   **Persona Switch:**
   ```bash
   echo "Switching to backend-engineer for version bump"
   ```

   **Tasks:**
   - Update version in pyproject.toml:
     ```bash
     # From 1.0.0 to 1.0.1 (example)
     sed -i 's/version = "1.0.0"/version = "1.0.1"/' \
       packages/tta-dev-primitives/pyproject.toml
     ```

   - Update CHANGELOG.md:
     ```markdown
     ## [1.0.1] - 2025-11-15

     ### Fixed
     - Health check timestamp format

     ### Changed
     - Improved APM instrumentation
     ```

   - Create git tag:
     ```bash
     git add packages/tta-dev-primitives/pyproject.toml CHANGELOG.md
     git commit -m "chore: Bump version to 1.0.1"
     git tag -a v1.0.1 -m "Release 1.0.1"
     ```

   **Verification:**
   - [ ] Version updated
   - [ ] Changelog updated
   - [ ] Git tag created

2. **Stage 2: Quality Validation (Testing Specialist)**

   **Persona Switch:**
   ```bash
   echo "Switching to testing-specialist for validation"
   ```

   **Tasks:**
   - Run full test suite:
     ```bash
     uv run pytest packages/tta-dev-primitives/tests/ -v --cov
     ```

   - Type check:
     ```bash
     uvx pyright packages/tta-dev-primitives/
     ```

   - Lint check:
     ```bash
     uv run ruff check packages/tta-dev-primitives/
     ```

   **Verification:**
   - [ ] All tests pass
   - [ ] Type checks pass
   - [ ] Lint checks pass
   - [ ] Coverage acceptable

3. **Stage 3: Deployment (DevOps Engineer)**

   **Persona Switch:**
   ```bash
   echo "Switching to devops-engineer for deployment"
   ```

   **Tasks:**
   - Build package:
     ```bash
     cd packages/tta-dev-primitives
     uv build
     ```

   - Verify build artifacts:
     ```bash
     ls -lh dist/
     ```

   - (Simulated) Publish to PyPI:
     ```bash
     echo "Would run: uv publish --token $PYPI_TOKEN"
     echo "Simulating successful publish..."
     ```

   **Verification:**
   - [ ] Package builds successfully
   - [ ] Build artifacts present
   - [ ] Publish simulated successfully

### APM Validation

1. **Full Workflow Metrics:**
   ```bash
   # Query all workflow metrics
   curl -G http://localhost:9090/api/v1/query \
     --data-urlencode 'query=hypertool_workflow_stage_duration_seconds_sum{workflow="package_release"}'
   ```

2. **Quality Gate Metrics:**
   ```bash
   curl -G http://localhost:9090/api/v1/query \
     --data-urlencode 'query=hypertool_quality_gate_status{workflow="package_release"}'
   ```

3. **Grafana:**
   - View both dashboards
   - Verify complete workflow trace
   - Check all quality gates passed

4. **Langfuse:**
   - Find trace "package-release-workflow"
   - Verify all 3 stages present
   - Review quality validation calls

### Success Criteria

- [ ] Version bumped successfully
- [ ] All quality checks pass
- [ ] Package builds successfully
- [ ] APM captured full workflow
- [ ] All quality gates green
- [ ] No errors in any stage

### Cleanup

```bash
git reset --hard HEAD
git tag -d v1.0.1
git checkout agent/augment
git branch -D test/manual-testing-release
```

---

## Test 5: Alert Validation

**Purpose:** Verify Prometheus alerts trigger correctly

**Duration:** 20-30 minutes

### Alert Tests

1. **TokenBudgetExceeded Alert**

   **Trigger:**
   ```python
   # Temporarily modify test workflow to exceed budget
   # Set backend-engineer budget to 100 (will exceed)
   collector.set_token_budget("backend-engineer", 100)
   collector.record_token_usage("backend-engineer", "test", "gpt-4", 650)
   ```

   **Verify:**
   ```bash
   # Check alert status
   curl http://localhost:9090/api/v1/alerts | jq '.data.alerts[] | select(.labels.alertname=="TokenBudgetExceeded")'
   ```

   **Expected:** Alert fires within 1 minute

2. **HighQualityGateFailureRate Alert**

   **Trigger:**
   ```python
   # Record multiple failed quality gates
   for _ in range(5):
       collector.record_quality_gate("test", "stage", "persona", False)
   ```

   **Verify:** Alert fires within 5 minutes

3. **ExcessivePersonaSwitching Alert**

   **Trigger:**
   ```python
   # Rapidly switch personas
   for i in range(10):
       collector.switch_persona(f"persona-{i}", f"persona-{i+1}", "test")
       await asyncio.sleep(0.1)
   ```

   **Verify:** Alert fires within 1 minute

### Alert Runbook Validation

- [ ] Each alert has runbook entry
- [ ] Runbook procedures clear
- [ ] Investigation steps actionable
- [ ] Resolution procedures tested

---

## Test Summary Template

After completing all tests, fill out this summary:

### Test Execution Summary

**Date:** 2025-11-15
**Duration:** _____ hours
**Tester:** _____

### Results

| Test | Status | Duration | Issues Found | Notes |
|------|--------|----------|--------------|-------|
| Baseline (test_instrumented_workflow) | ⬜ Pass ⬜ Fail | ___ min | ___ | |
| Augment (Feature Implementation) | ⬜ Pass ⬜ Fail | ___ min | ___ | |
| Cline (Bug Fix) | ⬜ Pass ⬜ Fail | ___ min | ___ | |
| GitHub Copilot (Release) | ⬜ Pass ⬜ Fail | ___ min | ___ | |
| Alert Validation | ⬜ Pass ⬜ Fail | ___ min | ___ | |

### APM Component Results

| Component | Status | Notes |
|-----------|--------|-------|
| PersonaMetricsCollector | ⬜ Working ⬜ Issues | |
| WorkflowTracer | ⬜ Working ⬜ Issues | |
| LangfuseIntegration | ⬜ Working ⬜ Issues | |
| ObservableLLM | ⬜ Working ⬜ Issues | |
| Prometheus Metrics | ⬜ Working ⬜ Issues | |
| Grafana Dashboards | ⬜ Working ⬜ Issues | |
| Alert Rules | ⬜ Working ⬜ Issues | |

### Issues Discovered

1. **Issue:** _____
   - **Severity:** ⬜ Critical ⬜ High ⬜ Medium ⬜ Low
   - **Component:** _____
   - **Reproduction:** _____
   - **Fix Status:** _____

2. **Issue:** _____
   - **Severity:** ⬜ Critical ⬜ High ⬜ Medium ⬜ Low
   - **Component:** _____
   - **Reproduction:** _____
   - **Fix Status:** _____

### Recommendations

- [ ] Recommendation 1: _____
- [ ] Recommendation 2: _____
- [ ] Recommendation 3: _____

### Next Steps

- [ ] Address critical issues
- [ ] Document all findings
- [ ] Update workflows based on feedback
- [ ] Schedule follow-up testing

---

## Appendix: Troubleshooting

### Common Issues

1. **Metrics not appearing in Prometheus:**
   - Check http://localhost:9464/metrics shows data
   - Verify Prometheus scrape config includes :9464
   - Restart Prometheus if needed

2. **Langfuse traces not appearing:**
   - Verify env vars set: `echo $LANGFUSE_PUBLIC_KEY`
   - Check internet connectivity
   - Review Langfuse project settings

3. **Grafana dashboards empty:**
   - Wait 10-15 seconds for data to populate
   - Refresh browser
   - Check Prometheus data source connected

4. **Import errors:**
   - Run `uv sync --all-extras`
   - Check virtual environment activated
   - Verify Python version >= 3.11

### Debug Commands

```bash
# Check all services
docker-compose -f docker-compose.test.yml ps

# View Prometheus logs
docker-compose -f docker-compose.test.yml logs prometheus

# View Grafana logs
docker-compose -f docker-compose.test.yml logs grafana

# Test Langfuse connection
python -c "from langfuse import Langfuse; l = Langfuse(); print('Connected')"

# Query all Hypertool metrics
curl http://localhost:9090/api/v1/label/__name__/values | jq '.data[] | select(contains("hypertool"))'
```

---

**End of Manual Testing Plan**


---
**Logseq:** [[TTA.dev/.hypertool/Instrumentation/Manual_testing_plan]]
