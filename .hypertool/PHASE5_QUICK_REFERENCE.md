# Phase 5 Quick Reference: APM & Langfuse Integration

**Fast access guide for implementing observability**

---

## 🚀 Quick Setup (5 minutes)

### Install Dependencies

```bash
# Install observability packages
uv add opentelemetry-api opentelemetry-sdk
uv add opentelemetry-exporter-prometheus
uv add prometheus-client
uv add langfuse

# Verify installation
uv run python -c "import langfuse; print('✅ Langfuse installed')"
```

### Configure Langfuse

```bash
# Sign up at https://langfuse.com or self-host
# Get API keys from Settings → API Keys

# Set environment variables (add to .env)
export LANGFUSE_PUBLIC_KEY="pk-lf-..."
export LANGFUSE_SECRET_KEY="sk-lf-..."
export LANGFUSE_HOST="https://cloud.langfuse.com"
```

### Initialize APM

```python
# File: your_script.py

from observability_integration import initialize_observability

# Initialize OpenTelemetry + Prometheus
initialize_observability(
    service_name="hypertool-persona-system",
    enable_prometheus=True,
    prometheus_port=9464
)

# Verify metrics endpoint
# Open http://localhost:9464/metrics
```

---

## 📊 Key Metrics to Track

### Persona Metrics

```promql
# Total persona switches
sum(hypertool_persona_switches_total)

# Average persona session duration
avg(hypertool_persona_duration_seconds)

# Token usage by persona
sum by (persona) (hypertool_persona_tokens_used_total)

# Remaining token budget
hypertool_persona_token_budget_remaining{persona="backend-engineer"}
```

### Workflow Metrics

```promql
# Workflow stage duration (P95)
histogram_quantile(0.95, rate(hypertool_workflow_stage_duration_seconds_bucket[5m]))

# Quality gate pass rate
sum(rate(hypertool_workflow_quality_gate_total{result="passed"}[5m]))
/
sum(rate(hypertool_workflow_quality_gate_total[5m]))

# Slowest workflow stages
topk(5, avg by (workflow, stage) (hypertool_workflow_stage_duration_seconds))
```

---

## 🔍 Langfuse Usage Patterns

### 1. Trace LLM Calls

```python
from .hypertool.instrumentation.llm_wrapper import ObservableLLM

# Create observable LLM
llm = ObservableLLM(
    persona="backend-engineer",
    chatmode="code-generation",
    model="gpt-4"
)

# Generate with automatic tracing
response = await llm.generate(
    prompt="Create FastAPI endpoint for user CRUD",
    temperature=0.7,
    max_tokens=2000
)

# Results automatically appear in Langfuse UI:
# - Prompt and response
# - Token usage and cost
# - Latency
# - Persona context
```

### 2. Track Workflow Stages

```python
from .hypertool.instrumentation.workflow_tracing import WorkflowTracer

async def my_workflow():
    async with WorkflowTracer("package_release") as tracer:
        # Stage 1: Backend
        result1 = await tracer.trace_stage(
            stage_name="version_bump",
            persona="backend-engineer",
            func=version_bump_task
        )

        # Stage 2: Testing
        result2 = await tracer.trace_stage(
            stage_name="validation",
            persona="testing-specialist",
            func=validation_task
        )

        # Stage 3: DevOps
        result3 = await tracer.trace_stage(
            stage_name="deploy",
            persona="devops-engineer",
            func=deploy_task
        )

# Traces show:
# - Complete workflow timeline
# - Per-stage duration
# - Persona switches
# - Quality gate results
```

### 3. Manage Prompts

```python
from langfuse import Langfuse

langfuse = Langfuse()

# Create prompt in Langfuse UI, then fetch
prompt = langfuse.get_prompt(
    "backend-code-generation",
    label="production"  # or "staging", "experimental"
)

# Use with variables
compiled = prompt.compile(
    task="Create CRUD endpoint",
    framework="FastAPI",
    database="PostgreSQL"
)

# Generate
response = await llm.generate(prompt=compiled)

# Langfuse tracks:
# - Which prompt version was used
# - Performance of each version
# - A/B test results
```

### 4. Create Evaluation Datasets

```python
from .hypertool.instrumentation.langfuse_integration import get_langfuse

langfuse = get_langfuse()

# Create test dataset
dataset_id = langfuse.create_dataset(
    name="backend_code_tests",
    description="Test cases for backend persona",
    items=[
        {
            "input": {"task": "Create CRUD endpoint"},
            "expected_output": {"quality_score": 0.9},
            "metadata": {"persona": "backend-engineer"}
        },
        {
            "input": {"task": "Add authentication middleware"},
            "expected_output": {"quality_score": 0.85},
            "metadata": {"persona": "backend-engineer"}
        }
    ]
)

# Run evaluations against dataset
for item in dataset.items:
    result = await persona.execute(item.input)
    score = evaluate(result, item.expected_output)
    langfuse.score(item.id, score)

# Langfuse shows:
# - Pass/fail rate
# - Quality trends
# - Prompt performance
```

---

## 📈 Grafana Dashboards

### View Persona Overview

1. **Open Grafana:** http://localhost:3000
2. **Import Dashboard:** Use `.hypertool/dashboards/persona_overview.json`
3. **View Panels:**
   - Persona switches timeline
   - Token usage pie chart
   - Average session duration
   - Top chatmodes table

### View Workflow Performance

1. **Import Dashboard:** `.hypertool/dashboards/workflow_performance.json`
2. **View Panels:**
   - Workflow execution time heatmap
   - Quality gate pass rate gauge
   - Stage duration by persona
   - Slow stages alert table

---

## 🚨 Prometheus Alerts

### Check Alert Status

```bash
# View firing alerts
curl http://localhost:9090/api/v1/alerts

# View alert rules
curl http://localhost:9090/api/v1/rules
```

### Common Alerts

| Alert | Trigger | Severity | Action |
|-------|---------|----------|--------|
| **PersonaTokenBudgetExceeded** | Budget < 0 | Warning | Review persona usage, increase budget |
| **HighPersonaSwitchRate** | >10 switches/sec | Info | Check for automation loops |
| **WorkflowQualityGateFailure** | >20% failure rate | Warning | Review failing stage, improve prompts |
| **WorkflowStageSlow** | P95 > 300s | Warning | Optimize slow stage, add caching |

---

## 🔧 Troubleshooting

### Metrics Not Showing

```bash
# Check Prometheus is running
curl http://localhost:9090

# Check metrics endpoint
curl http://localhost:9464/metrics | grep hypertool

# Verify initialization
python -c "from observability_integration import initialize_observability; initialize_observability()"
```

### Langfuse Connection Issues

```bash
# Test Langfuse connection
python -c "
from langfuse import Langfuse
langfuse = Langfuse()
print('✅ Connected to:', langfuse.base_url)
"

# Check environment variables
echo $LANGFUSE_PUBLIC_KEY
echo $LANGFUSE_SECRET_KEY
echo $LANGFUSE_HOST
```

### Traces Not Appearing

```python
# Flush Langfuse events (call at shutdown)
from .hypertool.instrumentation.langfuse_integration import get_langfuse

langfuse = get_langfuse()
langfuse.flush()  # Forces upload of pending traces
```

---

## 💡 Best Practices

### 1. Instrument Early

✅ **DO:** Add metrics at the start of implementation
❌ **DON'T:** Retrofit metrics after deployment

```python
# Good: Metrics from day 1
async def new_feature():
    async with WorkflowTracer("new_feature") as tracer:
        result = await tracer.trace_stage(...)
    return result

# Bad: No metrics, hard to debug later
async def new_feature():
    result = await some_function()
    return result
```

### 2. Use Structured Metadata

✅ **DO:** Include rich context in metadata
❌ **DON'T:** Rely only on metric labels

```python
# Good: Rich metadata
await langfuse.trace_llm_call(
    persona="backend-engineer",
    metadata={
        "workflow": "package_release",
        "stage": "version_bump",
        "user_input": "bump to 0.3.0",
        "quality_gate": "passed"
    }
)

# Bad: Minimal context
await langfuse.trace_llm_call(persona="backend")
```

### 3. Set Quality Gates

✅ **DO:** Define clear success criteria
❌ **DON'T:** Skip validation

```python
# Good: Explicit quality gate
quality_passed = (
    result["test_coverage"] > 0.9 and
    result["type_safety"] is True and
    result["security_scan"] == "passed"
)

collector.record_workflow_stage(
    workflow="feature_dev",
    stage="testing",
    persona="testing-specialist",
    duration_seconds=duration,
    quality_gate_passed=quality_passed
)

# Bad: No quality validation
collector.record_workflow_stage(duration_seconds=duration)
```

### 4. Monitor Cost

✅ **DO:** Track token usage and cost per persona
❌ **DON'T:** Ignore LLM costs

```python
# Good: Cost-aware
response = await llm.generate(prompt=prompt)
cost_usd = response["cost_usd"]

if cost_usd > BUDGET_THRESHOLD:
    logger.warning(f"High cost: ${cost_usd}")

# Bad: Untracked costs
response = await llm.generate(prompt=prompt)
# No cost tracking, budget overruns undetected
```

### 5. Flush on Shutdown

✅ **DO:** Flush Langfuse events before exit
❌ **DON'T:** Lose traces on shutdown

```python
# Good: Flush at shutdown
import atexit
from .hypertool.instrumentation.langfuse_integration import get_langfuse

def cleanup():
    langfuse = get_langfuse()
    langfuse.flush()

atexit.register(cleanup)

# Bad: Events lost
# (No flush, Langfuse buffer not uploaded)
```

---

## 📚 Related Documentation

- **Implementation Plan:** [PHASE5_APM_LANGFUSE_INTEGRATION.md](PHASE5_APM_LANGFUSE_INTEGRATION.md)
- **Langfuse Docs:** https://langfuse.com/docs
- **Prometheus Docs:** https://prometheus.io/docs/
- **OpenTelemetry Docs:** https://opentelemetry.io/docs/

---

## 🎯 Next Steps

### Week 1: Core Metrics

- [ ] Implement PersonaMetricsCollector
- [ ] Add metrics to tta-persona CLI
- [ ] Test metrics collection locally
- [ ] Verify Prometheus scraping

### Week 2: Langfuse Integration

- [ ] Set up Langfuse account
- [ ] Implement LangfuseIntegration class
- [ ] Wrap LLM calls with ObservableLLM
- [ ] Create evaluation datasets

### Week 3: Dashboards & Alerts

- [ ] Import Grafana dashboards
- [ ] Configure Prometheus alert rules
- [ ] Test alert firing
- [ ] Document runbook

---

**Last Updated:** 2025-11-15
**Status:** Ready for Implementation
**Owner:** TTA.dev Team


---
**Logseq:** [[TTA.dev/.hypertool/Phase5_quick_reference]]
