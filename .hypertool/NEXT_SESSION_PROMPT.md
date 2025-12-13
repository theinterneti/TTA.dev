# Next Session: Phase 5 Automated Testing & Validation

**Session Date:** TBD
**Previous Session:** 2025-11-15 (Phase 5 Weeks 1, 2, 3 Complete)
**Current Branch:** `agent/augment`

---

## 🎯 Session Objective

Complete **Phase 5 (APM & Langfuse Integration)** by executing:
1. **Automated Testing:** Python test harness for workflow validation (2-3 hours)
2. **Manual Dashboard Validation:** Verify Grafana/Prometheus/Langfuse (1 hour)
3. **Feedback Documentation:** Document findings and create iteration plan (1 hour)
4. **Phase 5 Wrap-Up:** Final summary and next phase planning (30 mins)

**New Strategy:** ✅ Automated Python tests instead of manual VS Code agent interaction (see `AUTOMATED_TESTING_PLAN.md`)

---

## 📊 Current State (What's Already Done)

### ✅ Phase 5 Week 1 Complete (100%)

**Core APM Infrastructure:**
- `PersonaMetricsCollector` (332 lines) - 6 Prometheus metrics for persona tracking
- `WorkflowTracer` (317 lines) - OpenTelemetry integration for workflow spans
- `test_instrumented_workflow.py` (208 lines) - Working test workflow
- All code has graceful degradation, full type hints, async support

### ✅ Phase 5 Week 2 Complete (100%)

**Langfuse Integration:**
- `LangfuseIntegration` (389 lines) - Core integration class
- `ObservableLLM` (306 lines) - Automatic LLM tracing wrapper
- `LANGFUSE_INTEGRATION.md` (500+ lines) - Comprehensive documentation
- Persona-as-user pattern for analytics
- Graceful degradation when Langfuse unavailable

### ✅ Phase 5 Week 3 Complete (100%)

**Dashboards & Alerts:**
- `dashboards/persona_overview.json` (380 lines) - 5 panels for persona operations
- `dashboards/workflow_performance.json` (520 lines) - 5 panels for workflow metrics
- `persona_alerts.yml` (280 lines) - 7 Prometheus alerts configured
- `ALERT_RUNBOOK.md` (850+ lines) - Comprehensive troubleshooting guide

**Multi-Agent Workflow Files:**
- `.augment/workflows/feature-implementation-hypertool.prompt.md` (318 lines)
- `.cline/workflows/bug-fix-hypertool.prompt.md` (175 lines)
- `.github/workflows/package-release-hypertool.prompt.md` (145 lines)

**Metrics Available:**
- `hypertool_persona_switches_total` - Track persona transitions
- `hypertool_persona_duration_seconds` - Time in each persona
- `hypertool_persona_tokens_used_total` - Token consumption
- `hypertool_persona_token_budget_remaining` - Budget tracking
- `hypertool_workflow_stage_duration_seconds` - Stage execution time
- `hypertool_workflow_quality_gate_total` - Quality gate results

**Documentation:**
- `PHASE5_APM_LANGFUSE_INTEGRATION.md` - Complete technical design
- `PHASE5_QUICK_REFERENCE.md` - Fast-access guide
- `PHASE5_PLANNING_COMPLETE.md` - Executive summary
- `PHASE5_IMPLEMENTATION_WEEK1_COMPLETE.md` - Week 1 summary
- `PHASE5_SUMMARY.md` - Full implementation summary

**Key Files:**
```
.hypertool/instrumentation/
├── __init__.py                           (exports PersonaMetricsCollector, WorkflowTracer)
├── persona_metrics.py                    (332 lines - Prometheus metrics)
├── workflow_tracing.py                   (317 lines - OpenTelemetry tracing)
└── test_instrumented_workflow.py         (208 lines - test workflow)
```

---

## 🚀 Priority Tasks for Next Session

### Task 1: Create Automated Test Harness (Priority 1 - 2 hours)

**Objective:** Build Python test suite to validate all Phase 5 instrumentation automatically.

**Files to Create:**

1. `.hypertool/instrumentation/test_automated_workflows.py` (~400 lines)
   - Test: Augment feature-implementation workflow simulation
   - Test: Cline bug-fix workflow simulation
   - Test: GitHub Copilot release workflow simulation
   - Test: Prometheus metrics collection verification
   - Test: Alert rules triggering validation
   - Test: Langfuse integration checks

2. `.hypertool/instrumentation/test_utils.py` (~150 lines)
   - Utility: `simulate_llm_call()` - Mock LLM with instrumentation
   - Utility: `query_prometheus_metrics()` - Query Prometheus API
   - Utility: `verify_langfuse_trace_exists()` - Check Langfuse traces
   - Utility: `trigger_alert()` - Manually trigger alerts for testing

3. `.hypertool/instrumentation/docker-compose.test.yml` (~100 lines)
   - Service: Prometheus (with alert rules loaded)
   - Service: Grafana (for dashboard import)
   - Service: Jaeger (optional, for distributed tracing)
   - Networks: `hypertool-test` bridge network

4. `.hypertool/scripts/import_dashboards.sh` (~50 lines)
   - Import Persona Overview Dashboard to Grafana
   - Import Workflow Performance Dashboard to Grafana
   - Verify import success

**Implementation Approach:**

```python
# test_automated_workflows.py structure
import pytest
import asyncio
from hypertool.instrumentation import (
    PersonaMetricsCollector,
    WorkflowTracer,
    LangfuseIntegration,
    ObservableLLM
)

@pytest.mark.asyncio
async def test_augment_feature_implementation_workflow():
    """
    Simulate Augment workflow:
    - Persona switches: product-manager → backend-engineer → devops-engineer
    - Workflow stages: requirements → implementation → deployment
    - Quality gates: requirements-complete, code-review, deployment-ready
    - LLM calls: 6-8 calls across personas
    - Expected metrics: All switches, stages, gates recorded
    """
    metrics = PersonaMetricsCollector.get_instance()
    tracer = WorkflowTracer.get_instance()
    langfuse = LangfuseIntegration.get_instance()

    with tracer.start_workflow("augment-feature-implementation"):
        # Stage 1: Requirements (product-manager)
        metrics.record_switch("product-manager", "augment", "feature-implementation")
        with tracer.start_stage("requirements-analysis"):
            await simulate_llm_call("Analyze requirements", persona="product-manager")
            tracer.record_quality_gate("requirements-complete", passed=True)

        # Stage 2: Implementation (backend-engineer)
        metrics.record_switch("backend-engineer", "augment", "feature-implementation")
        with tracer.start_stage("implementation"):
            await simulate_llm_call("Implement feature", persona="backend-engineer")
            tracer.record_quality_gate("code-review", passed=True)

        # Stage 3: Deployment (devops-engineer)
        metrics.record_switch("devops-engineer", "augment", "feature-implementation")
        with tracer.start_stage("deployment"):
            await simulate_llm_call("Deploy feature", persona="devops-engineer")
            tracer.record_quality_gate("deployment-ready", passed=True)

    # Verify observability
    assert metrics.get_metric_value("hypertool_persona_switches_total") >= 3
    assert langfuse.has_traces_for_user("product-manager")
    assert langfuse.has_traces_for_user("backend-engineer")
    assert langfuse.has_traces_for_user("devops-engineer")
```

**Success Criteria:**
- ✅ All tests pass (pytest exit code 0)
- ✅ 18 persona switches recorded across 3 workflows
- ✅ 9 workflow stages traced
- ✅ 9 quality gates recorded
- ✅ Langfuse has 6-9 distinct persona users
- ✅ Prometheus `/metrics` endpoint returns Hypertool metrics
- ✅ No instrumentation errors or warnings

**Time Estimate:** 2 hours

---

### Task 2: Manual Dashboard Validation (Priority 1 - 1 hour)

**Objective:** Verify Grafana dashboards, Prometheus alerts, and Langfuse UI work correctly with real data.

**Prerequisites:**
```bash
# Start observability stack
cd .hypertool/instrumentation
docker-compose -f docker-compose.test.yml up -d

# Import dashboards
./scripts/import_dashboards.sh

# Run automated tests to generate data
pytest test_automated_workflows.py -v
```

**Validation Steps:**

1. **Persona Overview Dashboard** (20 mins)
   - URL: http://localhost:3000/d/hypertool-persona-overview
   - Verify:
     - ✅ Persona Switch Rate panel shows activity
     - ✅ Persona Duration Distribution shows heatmap
     - ✅ Token Usage by Persona shows bars
     - ✅ Token Budget Remaining shows gauges
     - ✅ Top Persona Transitions table populated

2. **Workflow Performance Dashboard** (20 mins)
   - URL: http://localhost:3000/d/hypertool-workflow-performance
   - Verify:
     - ✅ Workflow Stage Duration shows p95/p50
     - ✅ Quality Gate Success Rate shows 100%
     - ✅ Failed Quality Gates empty (no failures)
     - ✅ Slowest Workflow Stages table populated
     - ✅ Workflow Execution Trends shows pass/fail

3. **Prometheus Alerts** (20 mins)
   - URL: http://localhost:9090/alerts
   - Verify:
     - ✅ All 7 Hypertool alerts loaded
     - ✅ No alerts firing (normal operation)

   - **Manually trigger alerts:**
     ```python
     # In Python REPL or test script
     from hypertool.instrumentation import PersonaMetricsCollector
     metrics = PersonaMetricsCollector.get_instance()

     # Trigger TokenBudgetExceeded
     metrics.update_budget("backend-engineer", -100)

     # Wait 1-2 minutes for evaluation
     # Check http://localhost:9090/alerts
     ```

   - Verify:
     - ✅ TokenBudgetExceeded alert fires
     - ✅ Alert has correct labels (persona, component)
     - ✅ Alert annotations include runbook link
     - ✅ Runbook link works (markdown file opens)

**Success Criteria:**
- ✅ Both dashboards display data without errors
- ✅ All 10 panels render correctly
- ✅ Dashboard filters (workflow, persona) functional
- ✅ At least 1 alert can be manually triggered
- ✅ Alert runbook links work

**Time Estimate:** 1 hour

---

### Task 3: Langfuse UI Validation (Priority 2 - 30 mins)

**Objective:** Verify Langfuse receives traces and displays persona analytics.

**Prerequisites:**
```bash
# Ensure Langfuse credentials set
export LANGFUSE_PUBLIC_KEY="pk-lf-..."
export LANGFUSE_SECRET_KEY="sk-lf-..."

# Run tests to generate traces
pytest test_automated_workflows.py -v
```

**Validation Steps:**

1. **Langfuse Traces** (15 mins)
   - URL: https://cloud.langfuse.com
   - Navigate: Traces → Filter by metadata
   - Verify:
     - ✅ Traces exist for test workflows
     - ✅ Each persona shows as distinct user
     - ✅ Metadata includes: workflow, stage, chatmode
     - ✅ Token counts accurate
     - ✅ Latency captured

2. **Persona Analytics** (15 mins)
   - Navigate: Users
   - Verify:
     - ✅ 6-9 persona users visible
     - ✅ Token usage per persona matches Prometheus
     - ✅ LLM call counts reasonable
     - ✅ Model usage distribution visible

**Success Criteria:**
- ✅ All test personas in Langfuse as users
- ✅ Traces include workflow/stage metadata
- ✅ Token counts: Langfuse ≈ Prometheus (within 5%)
- ✅ No errors in Langfuse integration logs

**Time Estimate:** 30 mins

---

### Task 4: Document Testing Results (Priority 1 - 1 hour)

**Objective:** Create comprehensive test reports for automated and manual validation.

**Files to Create:**

1. `.hypertool/AUTOMATED_TESTING_RESULTS.md` (~300 lines)
   - Test execution summary (pass/fail counts)
   - Metrics collected (with sample values)
   - Langfuse traces summary
   - Issues found (if any)
   - Screenshots of test output

2. `.hypertool/MANUAL_VALIDATION_RESULTS.md` (~200 lines)
   - Dashboard screenshots (both dashboards)
   - Alert triggering evidence (screenshots)
   - Langfuse UI screenshots (persona analytics)
   - Issues found (if any)
   - Recommendations for improvements

**Success Criteria:**
- ✅ Complete test reports created
- ✅ Screenshots included for visual validation
- ✅ All issues documented with severity
- ✅ Recommendations for next steps clear

**Time Estimate:** 1 hour

---

### Task 5: Phase 5 Final Wrap-Up (Priority 2 - 30 mins)

**Objective:** Create comprehensive Phase 5 completion summary and plan next steps.

**Files to Create:**

1. `.hypertool/PHASE5_COMPLETE.md` (~400 lines)
   - Executive summary (what was built, time invested, results)
   - Complete deliverables checklist (all weeks)
   - Key achievements and metrics
   - Production readiness assessment
   - Known limitations and future work
   - Next phase recommendations

**Success Criteria:**
- ✅ Complete Phase 5 summary document
- ✅ All deliverables validated
- ✅ Clear next steps for production deployment
- ✅ Lessons learned documented

**Time Estimate:** 30 mins

---

## 📚 Reference: Testing Plan Details

**Full Testing Plan:** `.hypertool/AUTOMATED_TESTING_PLAN.md`

**Key Decisions:**
- ✅ **Automated Python tests** instead of VS Code agent interaction (not feasible)
- ✅ **Hybrid approach**: Automated validation + manual dashboard checks
- ✅ **Docker Compose** for local observability stack
- ✅ **Pytest** for test framework with async support
- ✅ **Prometheus API** for metrics verification
- ✅ **Langfuse API** for trace validation

**Why This Approach:**
1. **Repeatable** - Can run in CI/CD without manual intervention
2. **Fast** - No VS Code startup overhead
3. **Comprehensive** - Tests all instrumentation layers
4. **Debuggable** - Standard Python testing tools
5. **Realistic** - Simulates agent workflows accurately

---

## 🎯 Session Success Criteria

**Must Complete:**
- ✅ Automated test harness created and passing
- ✅ All 3 workflow simulations working
- ✅ Prometheus metrics verified via API
- ✅ Langfuse traces validated
- ✅ Both Grafana dashboards displaying data
- ✅ At least 1 alert manually triggered
- ✅ Test reports documented with screenshots

**Nice to Have:**
- ✅ All 7 alerts tested
- ✅ Performance benchmarks (test runtime)
- ✅ CI/CD integration for tests
- ✅ Iteration plan for improvements

---

## ⏱️ Time Estimate

| Task | Estimated Time |
|------|---------------|
| Automated Test Harness | 2 hours |
| Manual Dashboard Validation | 1 hour |
| Langfuse UI Validation | 30 mins |
| Document Results | 1 hour |
| Phase 5 Wrap-Up | 30 mins |
| **Total** | **5 hours** |

**Original Estimate:** 8-10 hours (manual agent testing)
**New Estimate:** 5 hours (automated testing)
**Savings:** 3-5 hours (40-50% faster!)

---

**Requirements:**
- Singleton pattern (like PersonaMetricsCollector)
- Graceful degradation if Langfuse unavailable
- Integration with PersonaMetricsCollector
- Support for persona-as-user pattern
- Automatic trace/span creation
- Error handling and logging

**Key Methods:**
```python
class LangfuseIntegration:
    def __init__(self, public_key: str | None = None, secret_key: str | None = None):
        """Initialize Langfuse with API keys from env vars or params."""
        pass

    def start_trace(self, name: str, persona: str, chatmode: str) -> TraceContext:
        """Start a new Langfuse trace with persona as user."""
        pass

    def start_span(self, trace: TraceContext, name: str, **kwargs) -> SpanContext:
        """Start a span within a trace."""
        pass

    def end_span(self, span: SpanContext, output: Any = None, **kwargs):
        """End a span and record output."""
        pass

    def end_trace(self, trace: TraceContext, **kwargs):
        """End a trace and flush to Langfuse."""
        pass

    def record_generation(
        self,
        trace: TraceContext,
        model: str,
        prompt: str,
        completion: str,
        tokens: dict,
        persona: str
    ):
        """Record an LLM generation with persona metadata."""
        pass
```

**Environment Variables:**
- `LANGFUSE_PUBLIC_KEY` - Langfuse public key
- `LANGFUSE_SECRET_KEY` - Langfuse secret key
- `LANGFUSE_HOST` - Langfuse host (default: <https://cloud.langfuse.com>)

#### Step 2: Create ObservableLLM Wrapper (~130 lines)

**File:** `.hypertool/instrumentation/observable_llm.py`

**Requirements:**
- Wraps any LLM call with automatic tracing
- Records: model, prompt, completion, tokens, latency, persona
- Updates PersonaMetricsCollector token usage
- Creates Langfuse generation events
- Supports async and sync functions
- Error capture and retry tracking

**Key Methods:**
```python
class ObservableLLM:
    def __init__(
        self,
        llm_function: Callable,
        persona: str,
        chatmode: str,
        langfuse: LangfuseIntegration | None = None,
        metrics: PersonaMetricsCollector | None = None
    ):
        """Wrap an LLM function with observability."""
        pass

    async def __call__(self, prompt: str, **kwargs) -> str:
        """Call LLM with automatic tracing and metrics."""
        pass
```

**Usage Example:**
```python
from .langfuse_integration import LangfuseIntegration
from .observable_llm import ObservableLLM

# Setup
langfuse = LangfuseIntegration()
metrics = get_persona_metrics()

# Wrap LLM
observable_gpt4 = ObservableLLM(
    llm_function=gpt4_mini,
    persona="backend-engineer",
    chatmode="feature-implementation",
    langfuse=langfuse,
    metrics=metrics
)

# Use (automatic tracing + metrics)
response = await observable_gpt4("Write a FastAPI endpoint for user login")
```

#### Step 3: Update Test Workflow

**File:** `.hypertool/instrumentation/test_instrumented_workflow.py`

**Changes:**
- Import LangfuseIntegration and ObservableLLM
- Wrap mock LLM tasks with ObservableLLM
- Start Langfuse trace at workflow start
- End trace at workflow completion
- Add persona metadata to all generations

#### Step 4: Documentation

**File:** `.hypertool/instrumentation/LANGFUSE_INTEGRATION.md`

**Sections:**
- Setup instructions (API keys, SDK installation)
- LangfuseIntegration class usage
- ObservableLLM wrapper usage
- Persona-as-user pattern explanation
- Viewing traces in Langfuse UI
- Common queries and analytics
- Troubleshooting

### Success Criteria
- [ ] Langfuse SDK installed
- [ ] LangfuseIntegration class created (180 lines)
- [ ] ObservableLLM wrapper created (130 lines)
- [ ] Test workflow updated to use Langfuse
- [ ] Test execution shows traces in Langfuse UI
- [ ] Persona metadata visible in Langfuse
- [ ] Documentation complete

### Estimated Time
8-12 hours

---

## 🎨 Task 2: Week 3 - Dashboards & Alerts (Priority 2)

### Objective
Create Grafana dashboards and Prometheus alerts for Hypertool monitoring.

### Pre-Requisites
1. **Prometheus and Grafana Running:**
   ```bash
   docker-compose -f docker-compose.test.yml up -d
   ```
2. **Metrics available at:** <http://localhost:9464/metrics>
3. **Grafana UI at:** <http://localhost:3000>

### Implementation Steps

#### Step 1: Create Persona Overview Dashboard

**File:** `.hypertool/instrumentation/dashboards/persona_overview.json`

**Panels:**
1. **Persona Switch Rate** (Graph)
   - Query: `rate(hypertool_persona_switches_total[5m])`
   - Group by: `from_persona`, `to_persona`

2. **Persona Duration Distribution** (Heatmap)
   - Query: `hypertool_persona_duration_seconds`
   - Group by: `persona`

3. **Token Usage by Persona** (Bar Chart)
   - Query: `sum by (persona) (hypertool_persona_tokens_used_total)`

4. **Token Budget Remaining** (Gauge)
   - Query: `hypertool_persona_token_budget_remaining`
   - Group by: `persona`

5. **Top Persona Transitions** (Table)
   - Query: `topk(10, sum by (from_persona, to_persona) (hypertool_persona_switches_total))`

#### Step 2: Create Workflow Performance Dashboard

**File:** `.hypertool/instrumentation/dashboards/workflow_performance.json`

**Panels:**
1. **Workflow Stage Duration** (Graph)
   - Query: `hypertool_workflow_stage_duration_seconds`
   - Group by: `workflow`, `stage`

2. **Quality Gate Success Rate** (Single Stat)
   - Query: `sum(hypertool_workflow_quality_gate_total{result="passed"}) / sum(hypertool_workflow_quality_gate_total)`

3. **Failed Quality Gates** (Table)
   - Query: `hypertool_workflow_quality_gate_total{result="failed"}`

4. **Slowest Workflow Stages** (Table)
   - Query: `topk(10, avg by (workflow, stage) (hypertool_workflow_stage_duration_seconds))`

5. **Workflow Execution Trends** (Graph)
   - Query: `rate(hypertool_workflow_quality_gate_total[5m])`

#### Step 3: Configure Prometheus Alerts

**File:** `.hypertool/instrumentation/alerts/persona_alerts.yml`

**Alerts:**
1. **TokenBudgetExceeded**
   - Condition: `hypertool_persona_token_budget_remaining < 0`
   - Severity: warning
   - Message: "Persona {{ $labels.persona }} has exceeded token budget"

2. **HighQualityGateFailureRate**
   - Condition: `rate(hypertool_workflow_quality_gate_total{result="failed"}[10m]) > 0.2`
   - Severity: critical
   - Message: "Quality gate failure rate > 20% for {{ $labels.workflow }}"

3. **ExcessivePersonaSwitching**
   - Condition: `rate(hypertool_persona_switches_total[5m]) > 2`
   - Severity: warning
   - Message: "High persona switch rate detected (> 2/min)"

4. **SlowWorkflowStage**
   - Condition: `hypertool_workflow_stage_duration_seconds > 300`
   - Severity: warning
   - Message: "Workflow {{ $labels.workflow }} stage {{ $labels.stage }} took > 5 minutes"

#### Step 4: Create Alert Runbook

**File:** `.hypertool/instrumentation/ALERT_RUNBOOK.md`

**For Each Alert:**
- Description and severity
- Potential causes
- Investigation steps
- Resolution actions
- Escalation path

#### Step 5: Import Dashboards to Grafana

**Script:** `.hypertool/instrumentation/scripts/import_dashboards.py`

```python
import requests
import json

def import_dashboard(dashboard_file: str, grafana_url: str, api_key: str):
    """Import dashboard JSON to Grafana."""
    # Implementation
    pass
```

### Success Criteria
- [ ] Persona Overview dashboard created (JSON)
- [ ] Workflow Performance dashboard created (JSON)
- [ ] 4 Prometheus alerts configured
- [ ] Dashboards imported to Grafana
- [ ] Alerts visible in Prometheus UI
- [ ] Alert runbook documented
- [ ] Test alert firing with simulated data

### Estimated Time
6-8 hours

---

## 🧪 Task 3: Manual Testing (Priority 3)

### Objective
Validate all workflows with real scenarios and gather feedback.

### Test Cases

#### Test 1: Augment - Feature Implementation

**Workflow File:** `.augment/workflows/feature-implementation-hypertool.prompt.md`

**Scenario:** Implement a new REST API endpoint for user profile updates

**Steps:**
1. Open Augment with workflow file
2. Execute Stage 1 (backend-engineer):
   - Design API models (Pydantic)
   - Create endpoint structure
   - Validate token usage ~800
3. Execute Stage 2 (frontend-engineer):
   - Create React components
   - Implement state management
   - Validate token usage ~900
4. Execute Stage 3 (testing-specialist):
   - Write pytest tests
   - Run coverage
   - Validate token usage ~700

**Validation:**
- [ ] Persona switching works correctly
- [ ] Token tracking accurate
- [ ] Metrics visible at <http://localhost:9464/metrics>
- [ ] Quality gates recorded
- [ ] Total time < 6 hours

#### Test 2: Cline - Bug Fix

**Workflow File:** `.cline/workflows/bug-fix-hypertool.prompt.md`

**Scenario:** Fix a memory leak in the cache primitive

**Steps:**
1. Open Cline with workflow file
2. Execute Stage 1 (observability-expert):
   - Query Loki logs for memory patterns
   - Analyze Prometheus metrics
   - Identify root cause
   - Validate token usage ~800
3. Execute Stage 2 (backend-engineer):
   - Implement fix with proper cleanup
   - Add error handling
   - Validate token usage ~900
4. Execute Stage 3 (testing-specialist):
   - Create regression test
   - Run full test suite
   - Validate token usage ~600

**Validation:**
- [ ] Observability tools used correctly
- [ ] Root cause identified
- [ ] Fix implemented successfully
- [ ] Tests pass
- [ ] Total time < 2 hours

#### Test 3: GitHub Copilot - Package Release

**Workflow File:** `.github/workflows/package-release-hypertool.prompt.md`

**Scenario:** Release tta-dev-primitives v1.1.0

**Steps:**
1. Open GitHub Copilot with workflow file
2. Execute Stage 1 (backend-engineer):
   - Bump version with uv
   - Update CHANGELOG.md
   - Create git tag
   - Validate token usage ~600
3. Execute Stage 2 (testing-specialist):
   - Run pytest suite
   - Run pyright type checks
   - Run security scan
   - Validate token usage ~500
4. Execute Stage 3 (devops-engineer):
   - Build package with uv
   - Publish to PyPI
   - Verify installation
   - Validate token usage ~700

**Validation:**
- [ ] Version bumped correctly
- [ ] All quality checks pass
- [ ] Package published successfully
- [ ] Total time < 30 minutes

### Feedback Collection

**Document:** `.hypertool/MANUAL_TESTING_FEEDBACK.md`

**For Each Test:**
- What worked well?
- What was confusing?
- Token estimates accurate?
- Persona switching smooth?
- Metrics helpful?
- Improvements needed?

### Success Criteria
- [ ] All 3 workflows executed successfully
- [ ] Metrics collected for all executions
- [ ] Feedback documented
- [ ] Issues identified and logged
- [ ] Iteration plan created

### Estimated Time
2-3 hours

---

## 📋 Pre-Session Checklist

Before starting the next session, ensure you have:

### Access & Credentials
- [ ] Langfuse account created (cloud or self-hosted)
- [ ] Langfuse API keys available (public + secret)
- [ ] Docker running (for Prometheus + Grafana)
- [ ] Grafana credentials (default: admin/admin)

### Environment Setup
- [ ] TTA.dev repository cloned and up-to-date
- [ ] On branch: `agent/augment`
- [ ] uv installed and configured
- [ ] Python 3.11+ available

### Documentation Review
- [ ] Read `.hypertool/PHASE5_APM_LANGFUSE_INTEGRATION.md`
- [ ] Review `.hypertool/PHASE5_QUICK_REFERENCE.md`
- [ ] Check `.hypertool/PHASE5_SUMMARY.md`

### Test Current Implementation
- [ ] Run test workflow:
  ```bash
  python -m .hypertool.instrumentation.test_instrumented_workflow
  ```
- [ ] View metrics:
  ```bash
  curl http://localhost:9464/metrics | grep hypertool
  ```

---

## 🎯 Session Goals

### Must Complete (Priority 1)
- [ ] Langfuse SDK installed
- [ ] LangfuseIntegration class implemented
- [ ] ObservableLLM wrapper implemented
- [ ] Test workflow updated with Langfuse
- [ ] LLM traces visible in Langfuse UI

### Should Complete (Priority 2)
- [ ] Persona Overview dashboard created
- [ ] Workflow Performance dashboard created
- [ ] 4 Prometheus alerts configured
- [ ] Dashboards imported to Grafana
- [ ] Alert runbook documented

### Nice to Have (Priority 3)
- [ ] All 3 workflows tested manually
- [ ] Feedback collected
- [ ] Issues documented
- [ ] Iteration plan created

---

## 📝 Session Prompt for Agent

```
Hi! I'm continuing work on TTA.dev Hypertool Phase 5 implementation.

**Context:**
- Week 1 (Core APM Metrics) is 100% complete
- PersonaMetricsCollector and WorkflowTracer are working
- 3 multi-agent workflow files are created
- All code is in .hypertool/instrumentation/

**This Session Goals:**
1. Implement Langfuse Integration (Week 2)
2. Create Grafana Dashboards & Prometheus Alerts (Week 3)
3. Execute manual testing with real workflows

**Start with:**
Please review the current implementation in .hypertool/instrumentation/ and confirm all Week 1 deliverables are present. Then let's begin Week 2 - Langfuse Integration.

**Reference:**
- See .hypertool/NEXT_SESSION_PROMPT.md for complete task breakdown
- See .hypertool/PHASE5_SUMMARY.md for Week 1 summary
- See .hypertool/PHASE5_APM_LANGFUSE_INTEGRATION.md for technical design

Let's get started!
```

---

## 🔗 Key Files Reference

### Implementation Files (Week 1)
- `.hypertool/instrumentation/__init__.py` - Package initialization
- `.hypertool/instrumentation/persona_metrics.py` - PersonaMetricsCollector (332 lines)
- `.hypertool/instrumentation/workflow_tracing.py` - WorkflowTracer (317 lines)
- `.hypertool/instrumentation/test_instrumented_workflow.py` - Test workflow (208 lines)

### Workflow Files (Week 1)
- `.augment/workflows/feature-implementation-hypertool.prompt.md` (318 lines)
- `.cline/workflows/bug-fix-hypertool.prompt.md` (175 lines)
- `.github/workflows/package-release-hypertool.prompt.md` (145 lines)

### Documentation (Week 1)
- `.hypertool/PHASE5_APM_LANGFUSE_INTEGRATION.md` - Technical design
- `.hypertool/PHASE5_QUICK_REFERENCE.md` - Quick reference
- `.hypertool/PHASE5_PLANNING_COMPLETE.md` - Executive summary
- `.hypertool/PHASE5_IMPLEMENTATION_WEEK1_COMPLETE.md` - Week 1 details
- `.hypertool/PHASE5_SUMMARY.md` - Complete summary
- `.hypertool/NEXT_SESSION_PROMPT.md` - This file

### To Be Created (Week 2-3)
- `.hypertool/instrumentation/langfuse_integration.py` - NEW
- `.hypertool/instrumentation/observable_llm.py` - NEW
- `.hypertool/instrumentation/dashboards/persona_overview.json` - NEW
- `.hypertool/instrumentation/dashboards/workflow_performance.json` - NEW
- `.hypertool/instrumentation/alerts/persona_alerts.yml` - NEW
- `.hypertool/instrumentation/LANGFUSE_INTEGRATION.md` - NEW
- `.hypertool/instrumentation/ALERT_RUNBOOK.md` - NEW
- `.hypertool/MANUAL_TESTING_FEEDBACK.md` - NEW

---

## 💡 Tips for Success

### Langfuse Integration
- Start with LangfuseIntegration class (simpler)
- Test with simple LLM call before full workflow
- Use Langfuse cloud for fastest setup
- Check Langfuse UI frequently during development
- Persona metadata is critical for analytics

### Dashboard Creation
- Use Grafana UI to prototype panels
- Export JSON after manual creation
- Test queries in Prometheus before adding to dashboard
- Keep dashboards simple and focused
- Add helpful descriptions to all panels

### Alert Configuration
- Start with warning-level alerts
- Test alert firing with mock data
- Document runbook BEFORE implementing alerts
- Use reasonable thresholds (avoid false positives)
- Test alert resolution workflow

### Manual Testing
- Use real scenarios (not toy examples)
- Document everything (screenshots, metrics, feedback)
- Time each workflow execution
- Compare to estimates in workflow files
- Note any friction points for iteration

---

**Ready to Continue!** 🚀

This prompt contains everything needed to pick up where we left off. Week 1 is complete and production-ready. Week 2-3 implementation will complete Phase 5 and provide full observability for the Hypertool persona system.

**Estimated Total Time for Next Session:** 16-23 hours
- Week 2: 8-12 hours
- Week 3: 6-8 hours
- Testing: 2-3 hours

**Expected Completion:** Phase 5 fully implemented and validated.


---
**Logseq:** [[TTA.dev/.hypertool/Next_session_prompt]]
