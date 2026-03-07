# Automated Testing Plan for Phase 5 Validation

**Created:** 2025-11-15
**Status:** Design Phase
**Goal:** Automate manual testing of Hypertool instrumentation across 3 AI agent workflows

---

## 🎯 Testing Objective

Validate that Phase 5 instrumentation (Prometheus metrics, OpenTelemetry tracing, Langfuse LLM observability, Grafana dashboards, alerts) works correctly across:

1. **Augment Workflow** - Feature implementation
2. **Cline Workflow** - Bug fixing
3. **GitHub Copilot Workflow** - Package release

---

## 🤔 Automation Feasibility Analysis

### Option 1: VS Code Extension API Automation ⚠️ **LIMITED**

**Capabilities:**
- ✅ Can launch VS Code via CLI: `code /path/to/workspace`
- ✅ Can install extensions: `code --install-extension <id>`
- ✅ Can execute commands: `code --command <command-id>`
- ❌ **Cannot directly interact with chat panels** (Copilot/Cline/Augment)
- ❌ **No official API for sending messages to agent extensions**

**Why It Won't Work:**
- GitHub Copilot, Cline, and Augment chat panels are **webview-based UI**
- No programmatic API to send messages to these panels
- VS Code Extension API doesn't expose chat interaction methods
- Would require **reverse engineering** webview communication (fragile, unsupported)

**Verdict:** ❌ **Not feasible for agent chat automation**

---

### Option 2: Python Test Harness ✅ **RECOMMENDED**

**Approach:** Create Python test scripts that directly invoke the instrumentation code, simulating agent workflows.

**Why This Works:**
- ✅ **Direct code access** - We control the persona switching, metrics, tracing
- ✅ **Repeatable** - Can run in CI/CD, no manual intervention
- ✅ **Observable** - Can verify metrics, traces, Langfuse entries programmatically
- ✅ **Fast** - No VS Code startup overhead
- ✅ **Debuggable** - Standard Python testing tools (pytest, assertions)

**Implementation:**
```python
# Test script simulates agent workflow
from hypertool.instrumentation import PersonaMetricsCollector, WorkflowTracer, LangfuseIntegration

async def test_augment_workflow():
    """Simulate Augment feature-implementation workflow."""
    # 1. Setup instrumentation
    metrics = PersonaMetricsCollector.get_instance()
    tracer = WorkflowTracer.get_instance()
    langfuse = LangfuseIntegration.get_instance()

    # 2. Simulate workflow stages
    with tracer.start_workflow("augment-feature-implementation"):
        # Stage 1: Requirements analysis (product-manager persona)
        metrics.record_switch("product-manager", "augment", "feature-implementation")
        with tracer.start_stage("requirements-analysis"):
            # Simulate LLM call with ObservableLLM
            await simulate_llm_call("Analyze requirements...", persona="product-manager")

        # Stage 2: Implementation (backend-engineer persona)
        metrics.record_switch("backend-engineer", "augment", "feature-implementation")
        with tracer.start_stage("implementation"):
            await simulate_llm_call("Implement feature...", persona="backend-engineer")

        # Stage 3: Quality gate
        with tracer.start_stage("quality-gate"):
            tracer.record_quality_gate("code-review", passed=True)

    # 3. Verify observability
    assert metrics.get_metric("hypertool_persona_switches_total") > 0
    assert langfuse.has_traces_for_user("product-manager")
    assert langfuse.has_traces_for_user("backend-engineer")
```

**Verdict:** ✅ **Best approach for automated testing**

---

### Option 3: Hybrid Approach (Manual + Automated) 🔀 **PRAGMATIC**

**Manual Testing:** Run real workflows in VS Code for **qualitative validation**
- User experience verification
- Dashboard visualization checks
- Alert triggering (manual budget exhaustion)
- Langfuse UI review

**Automated Testing:** Python test harness for **quantitative validation**
- Metric accuracy
- Trace completeness
- Langfuse persona-user mapping
- Alert rule correctness (via PromQL queries)

**Verdict:** ✅ **Recommended for comprehensive validation**

---

## 📋 Recommended Testing Strategy

### Phase 1: Automated Validation (2 hours)

**Create Python test harness:**
```
.hypertool/instrumentation/test_automated_workflows.py
```

**Test Coverage:**

1. **Augment Workflow Simulation** (30 mins)
   - Persona transitions: product-manager → backend-engineer → devops-engineer
   - Workflow stages: requirements → implementation → deployment
   - Quality gates: requirements-complete, code-review, deployment-ready
   - Metrics: switches, duration, tokens, quality gates
   - Tracing: workflow span, stage spans, persona attributes
   - Langfuse: 3 users (personas), LLM traces with metadata

2. **Cline Workflow Simulation** (30 mins)
   - Persona transitions: backend-engineer → testing-specialist → observability-expert
   - Workflow stages: bug-analysis → fix → validation
   - Quality gates: root-cause-found, fix-validated, metrics-verified
   - Metrics: Same as Augment
   - Tracing: Bug-fix workflow span with error metadata
   - Langfuse: Debug-focused LLM calls

3. **GitHub Copilot Workflow Simulation** (30 mins)
   - Persona transitions: devops-engineer → testing-specialist
   - Workflow stages: version-bump → quality-check → publish
   - Quality gates: tests-passed, docs-updated, package-published
   - Metrics: Minimal token usage (automated workflow)
   - Tracing: Release workflow span
   - Langfuse: CI/CD LLM calls

4. **Observability Verification** (30 mins)
   - Query Prometheus metrics via API
   - Verify alert rules trigger correctly (simulated threshold violations)
   - Check Langfuse for expected traces
   - Validate OpenTelemetry spans in memory exporter

**Success Criteria:**
- ✅ All 18 persona switches recorded correctly
- ✅ All 9 workflow stages traced
- ✅ All 9 quality gates recorded
- ✅ Langfuse has 6-9 distinct users (personas)
- ✅ Prometheus metrics available via `/metrics` endpoint
- ✅ No instrumentation errors or warnings

---

### Phase 2: Manual Dashboard Validation (1 hour)

**Setup:**
```bash
# Start Prometheus + Grafana stack
docker-compose -f .hypertool/instrumentation/docker-compose.test.yml up -d

# Import dashboards
./scripts/import_dashboards.sh

# Run automated tests to generate metrics
pytest .hypertool/instrumentation/test_automated_workflows.py -v
```

**Manual Checks:**

1. **Persona Overview Dashboard** (20 mins)
   - Open: http://localhost:3000/d/hypertool-persona-overview
   - Verify:
     - ✅ Persona Switch Rate panel shows activity
     - ✅ Persona Duration Distribution shows color gradient
     - ✅ Token Usage by Persona shows bars for tested personas
     - ✅ Token Budget Remaining shows gauges
     - ✅ Top Persona Transitions shows test transitions

2. **Workflow Performance Dashboard** (20 mins)
   - Open: http://localhost:3000/d/hypertool-workflow-performance
   - Verify:
     - ✅ Workflow Stage Duration shows p95/p50 lines
     - ✅ Quality Gate Success Rate shows 100% (all passed)
     - ✅ Failed Quality Gates shows empty (no failures)
     - ✅ Slowest Workflow Stages shows test stages
     - ✅ Workflow Execution Trends shows pass/fail rates

3. **Prometheus Alerts** (20 mins)
   - Open: http://localhost:9090/alerts
   - Verify:
     - ✅ All 7 Hypertool alerts loaded
     - ✅ No alerts firing (normal operation)

   - **Trigger alerts manually:**
     ```python
     # Trigger TokenBudgetExceeded
     metrics.update_budget("backend-engineer", -100)

     # Trigger HighQualityGateFailureRate
     for _ in range(10):
         tracer.record_quality_gate("test-gate", passed=False)
     ```

   - Verify:
     - ✅ Alerts fire after evaluation period
     - ✅ Alert annotations have correct runbook links
     - ✅ Alerts show correct labels (persona, workflow, etc.)

**Success Criteria:**
- ✅ Both dashboards display real data
- ✅ All panels render without errors
- ✅ Alerts can be manually triggered
- ✅ Dashboard filters (workflow, persona) work correctly

---

### Phase 3: Langfuse UI Validation (30 mins)

**Setup:**
```bash
# Ensure Langfuse credentials are set
export LANGFUSE_PUBLIC_KEY="..."
export LANGFUSE_SECRET_KEY="..."

# Run tests to generate traces
pytest .hypertool/instrumentation/test_automated_workflows.py -v
```

**Manual Checks:**

1. **Langfuse Cloud Dashboard** (15 mins)
   - Open: https://cloud.langfuse.com
   - Navigate to: Traces → Filter by metadata
   - Verify:
     - ✅ Traces exist for test runs
     - ✅ Personas show as distinct users
     - ✅ Workflow metadata attached (workflow, stage, chatmode)
     - ✅ Token counts accurate
     - ✅ Latency captured

2. **Persona Analytics** (15 mins)
   - Navigate to: Users
   - Verify:
     - ✅ Each persona appears as a user
     - ✅ Token usage per persona matches Prometheus
     - ✅ LLM call counts reasonable
     - ✅ Model usage distribution visible

**Success Criteria:**
- ✅ All test personas visible in Langfuse
- ✅ Traces include workflow/stage metadata
- ✅ Token counts match between Langfuse and Prometheus
- ✅ No errors in Langfuse integration

---

## 🛠️ Implementation Files

### File 1: Automated Test Harness

**File:** `.hypertool/instrumentation/test_automated_workflows.py` (~400 lines)

**Structure:**
```python
"""
Automated testing for Phase 5 Hypertool instrumentation.

Tests:
- test_augment_feature_implementation_workflow
- test_cline_bug_fix_workflow
- test_github_copilot_release_workflow
- test_prometheus_metrics_collection
- test_alert_rules_triggering
- test_langfuse_integration
"""

import pytest
import asyncio
from typing import Any
from hypertool.instrumentation import (
    PersonaMetricsCollector,
    WorkflowTracer,
    LangfuseIntegration,
    ObservableLLM
)

# Fixtures
@pytest.fixture
async def clean_instrumentation():
    """Reset instrumentation between tests."""
    # Reset singleton state
    PersonaMetricsCollector._instance = None
    WorkflowTracer._instance = None
    LangfuseIntegration._instance = None
    yield
    # Cleanup after test

# Test: Augment Workflow
@pytest.mark.asyncio
async def test_augment_feature_implementation_workflow():
    """Simulate Augment feature-implementation workflow."""
    # Implementation...

# Test: Cline Workflow
@pytest.mark.asyncio
async def test_cline_bug_fix_workflow():
    """Simulate Cline bug-fix workflow."""
    # Implementation...

# Test: GitHub Copilot Workflow
@pytest.mark.asyncio
async def test_github_copilot_release_workflow():
    """Simulate GitHub Copilot package-release workflow."""
    # Implementation...

# Test: Metrics
@pytest.mark.asyncio
async def test_prometheus_metrics_collection():
    """Verify Prometheus metrics are collected correctly."""
    # Implementation...

# Test: Alerts
@pytest.mark.asyncio
async def test_alert_rules_triggering():
    """Verify alert rules can be triggered."""
    # Implementation...

# Test: Langfuse
@pytest.mark.asyncio
async def test_langfuse_integration():
    """Verify Langfuse integration works."""
    # Implementation...
```

---

### File 2: Test Utilities

**File:** `.hypertool/instrumentation/test_utils.py` (~150 lines)

**Utilities:**
```python
"""Test utilities for instrumentation validation."""

async def simulate_llm_call(
    prompt: str,
    persona: str,
    chatmode: str,
    model: str = "gpt-4-mini"
) -> dict[str, Any]:
    """Simulate an LLM call with instrumentation."""
    # Use ObservableLLM to create trace
    # Return simulated response

def query_prometheus_metrics(
    metric_name: str,
    labels: dict[str, str] | None = None
) -> float:
    """Query Prometheus metrics via HTTP API."""
    # Call http://localhost:9090/api/v1/query
    # Return metric value

def verify_langfuse_trace_exists(
    user: str,
    workflow: str | None = None
) -> bool:
    """Check if Langfuse has traces for user/workflow."""
    # Query Langfuse API
    # Return True if trace exists

def trigger_alert(alert_name: str):
    """Manually trigger an alert for testing."""
    # Manipulate metrics to exceed thresholds
    # Wait for alert evaluation period
```

---

### File 3: Dashboard Import Script

**File:** `.hypertool/scripts/import_dashboards.sh` (~50 lines)

**Script:**
```bash
#!/bin/bash
# Import Grafana dashboards for testing

GRAFANA_URL="http://localhost:3000"
GRAFANA_API_KEY="${GRAFANA_API_KEY:-admin}"  # Default for test instance

# Import Persona Overview Dashboard
curl -X POST "$GRAFANA_URL/api/dashboards/db" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $GRAFANA_API_KEY" \
  -d @.hypertool/instrumentation/dashboards/persona_overview.json

# Import Workflow Performance Dashboard
curl -X POST "$GRAFANA_URL/api/dashboards/db" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $GRAFANA_API_KEY" \
  -d @.hypertool/instrumentation/dashboards/workflow_performance.json

echo "✅ Dashboards imported successfully"
echo "📊 View at: $GRAFANA_URL/dashboards"
```

---

### File 4: Docker Compose for Testing

**File:** `.hypertool/instrumentation/docker-compose.test.yml` (~100 lines)

**Stack:**
```yaml
version: '3.8'

services:
  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.test.yml:/etc/prometheus/prometheus.yml
      - ./persona_alerts.yml:/etc/prometheus/rules/persona_alerts.yml
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--web.enable-lifecycle'
    networks:
      - hypertool-test

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
      - GF_AUTH_ANONYMOUS_ENABLED=true
    volumes:
      - grafana-storage:/var/lib/grafana
    networks:
      - hypertool-test

  # Optional: Jaeger for distributed tracing
  jaeger:
    image: jaegertracing/all-in-one:latest
    ports:
      - "16686:16686"  # UI
      - "4318:4318"    # OTLP HTTP
    networks:
      - hypertool-test

networks:
  hypertool-test:
    driver: bridge

volumes:
  grafana-storage:
```

---

### File 5: Prometheus Test Config

**File:** `.hypertool/instrumentation/prometheus.test.yml` (~30 lines)

**Config:**
```yaml
global:
  scrape_interval: 5s
  evaluation_interval: 5s

rule_files:
  - /etc/prometheus/rules/persona_alerts.yml

scrape_configs:
  - job_name: 'hypertool'
    static_configs:
      - targets: ['host.docker.internal:9464']  # Hypertool metrics endpoint
    scrape_interval: 5s
```

---

## 🚀 Execution Plan

### Day 1: Automated Testing Setup (2-3 hours)

**Tasks:**
1. ✅ Create `test_automated_workflows.py` with all 3 workflow simulations
2. ✅ Create `test_utils.py` with helper functions
3. ✅ Create `docker-compose.test.yml` for observability stack
4. ✅ Create `import_dashboards.sh` for Grafana setup
5. ✅ Run tests, verify all pass
6. ✅ Document any issues found

**Deliverables:**
- Working test suite (pytest passing)
- Metrics visible in Prometheus
- Traces in Langfuse
- Test report (AUTOMATED_TESTING_RESULTS.md)

---

### Day 2: Manual Dashboard Validation (1 hour)

**Tasks:**
1. ✅ Start observability stack: `docker-compose up -d`
2. ✅ Import dashboards: `./scripts/import_dashboards.sh`
3. ✅ Run tests to generate data: `pytest -v`
4. ✅ Review both Grafana dashboards
5. ✅ Manually trigger alerts, verify runbook links
6. ✅ Check Langfuse UI for persona analytics

**Deliverables:**
- Screenshots of dashboards with data
- Alert firing verification
- Langfuse persona analytics review
- Manual testing report (MANUAL_VALIDATION_RESULTS.md)

---

### Day 3: Iteration & Wrap-up (1-2 hours)

**Tasks:**
1. ✅ Fix any issues found in testing
2. ✅ Re-run tests to verify fixes
3. ✅ Update documentation based on findings
4. ✅ Create final Phase 5 summary
5. ✅ Plan next phase (if any improvements needed)

**Deliverables:**
- Bug fixes (if any)
- Updated documentation
- Phase 5 final summary (PHASE5_COMPLETE.md)
- Next phase plan

---

## 📊 Success Metrics

### Automated Testing

| Metric | Target | Measurement |
|--------|--------|-------------|
| Test Coverage | 100% of instrumentation | pytest coverage report |
| Persona Switches | 18 recorded | Prometheus query |
| Workflow Stages | 9 traced | OpenTelemetry spans |
| Quality Gates | 9 recorded | Metrics count |
| Langfuse Users | 6-9 personas | Langfuse API |
| Alert Rules | 7 loaded | Prometheus API |
| Test Runtime | < 5 minutes | pytest duration |

### Manual Validation

| Item | Target | Status |
|------|--------|--------|
| Dashboard Panels | 10 visible with data | Visual check |
| Alert Triggering | All 7 can fire | Manual test |
| Langfuse Traces | Present for all personas | UI check |
| Token Accuracy | Langfuse = Prometheus | Comparison |
| Runbook Links | All 7 work | Click test |

---

## 🎯 Recommendation

**Primary Strategy:** ✅ **Option 2 (Python Test Harness) + Option 3 (Hybrid Manual)**

**Why:**
1. **Automated tests** provide repeatable, fast validation
2. **Manual checks** ensure dashboards/alerts work end-to-end
3. **No VS Code automation complexity** (fragile, unsupported)
4. **CI/CD ready** - Automated tests can run in GitHub Actions
5. **Realistic** - Simulates agent workflows without actual agents

**Time Estimate:**
- Automated test setup: 2-3 hours
- Manual validation: 1 hour
- Iteration: 1-2 hours
- **Total: 4-6 hours** (vs original 8-10 hours for full manual)

---

## 📝 Next Steps

1. **Approve this plan** - User confirmation
2. **Create test files** - Implement test harness
3. **Run automated tests** - Verify instrumentation
4. **Manual validation** - Dashboard/alert checks
5. **Document results** - Create test reports
6. **Phase 5 wrap-up** - Final summary

**Status:** ✅ **Ready to implement automated testing approach**


---
**Logseq:** [[TTA.dev/.hypertool/Automated_testing_plan]]
