# Hypertool Alert Runbook

**Alert Investigation and Resolution Guide**

This runbook provides detailed investigation steps and resolution procedures for all Hypertool Prometheus alerts.

---

## Table of Contents

1. [Token Budget Exceeded](#token-budget-exceeded)
2. [High Quality Gate Failure Rate](#high-quality-gate-failure-rate)
3. [Excessive Persona Switching](#excessive-persona-switching)
4. [Slow Workflow Stage](#slow-workflow-stage)
5. [Token Budget Depletion Predicted](#token-budget-depletion-predicted)
6. [Hypertool Metrics Not Reported](#hypertool-metrics-not-reported)
7. [Langfuse Integration Failing](#langfuse-integration-failing)

---

## Alert 1: Token Budget Exceeded

### Description

**Alert Name:** `TokenBudgetExceeded`
**Severity:** Critical
**Category:** Cost

Fires when a persona has consumed more tokens than its allocated budget (`hypertool_persona_token_budget_remaining < 0`).

### Impact

- **Financial:** Increased LLM API costs beyond budget
- **Performance:** Potential rate limiting from LLM provider
- **Planning:** Budget forecasts invalid

### Investigation Steps

#### 1. Identify the Persona

```bash
# Check which persona(s) are over budget
curl -s 'http://localhost:9090/api/v1/query?query=hypertool_persona_token_budget_remaining' | jq '.data.result[] | select(.value[1] | tonumber < 0)'
```

**Expected Output:**
```json
{
  "metric": {
    "persona": "backend-engineer"
  },
  "value": [1699564800, "-250"]  // -250 tokens over budget
}
```

#### 2. Check Langfuse for Usage Patterns

1. Open Langfuse UI: `https://cloud.langfuse.com` (or your self-hosted instance)
2. Filter by user = persona name (e.g., "backend-engineer")
3. Sort traces by token usage (descending)
4. Look for:
   - Unusually large prompts
   - Excessive completion lengths
   - Repeated similar calls (caching opportunity)
   - Unexpected chatmodes using this persona

#### 3. Query Prometheus for Token Details

```promql
# Total tokens used by persona in last hour
sum(increase(hypertool_persona_tokens_used_total{persona="backend-engineer"}[1h])) by (chatmode, model)

# Compare to budget
hypertool_persona_token_budget_remaining{persona="backend-engineer"}
```

#### 4. Review Recent Changes

Check if token usage spike correlates with:
- New chatmode deployment
- Prompt template changes
- Model upgrades (e.g., GPT-3.5 → GPT-4)
- Increased workflow frequency

### Root Causes

| Cause | Indicators | Likelihood |
|-------|-----------|------------|
| **Prompt bloat** | Large prompt token counts in Langfuse | High |
| **Inefficient caching** | Repeated identical prompts | Medium |
| **Unexpected usage** | New chatmode not in budget planning | Medium |
| **Budget too low** | Consistent overage with normal usage | Low |
| **Model change** | Recent switch to higher-token model | Low |

### Resolution

#### Quick Fix (Immediate)

**Option A: Increase Budget**

```python
# In persona_metrics.py
self._token_budgets = {
    "backend-engineer": 2500,  # Increased from 2000
    # ...
}
```

Then restart the application.

**Option B: Reduce Usage**

1. **Optimize prompts:** Remove unnecessary context
2. **Enable caching:** Use `CachePrimitive` for repeated queries
3. **Switch models:** Use cheaper model tier where appropriate

#### Long-Term Fix

1. **Analyze Usage Patterns**
   ```python
   # Create dashboard panel
   sum(increase(hypertool_persona_tokens_used_total[7d])) by (persona, chatmode)
   ```

2. **Adjust Budgets Based on Data**
   - Calculate p95 daily usage
   - Add 20% buffer
   - Update `_token_budgets` mapping

3. **Implement Dynamic Budgets**
   ```python
   # Future enhancement: Load budgets from config
   budgets = load_budgets_from_config("budgets.yml")
   ```

4. **Set Up Cost Tracking**
   - Add cost-per-token metrics
   - Create budget burn rate alerts
   - Implement monthly cost caps

### Prevention

- [ ] Monitor daily token usage trends
- [ ] Set up `TokenBudgetDepletionPredicted` alert
- [ ] Regular prompt optimization reviews
- [ ] Caching strategy for common queries
- [ ] Budget review every sprint

### Related Alerts

- `TokenBudgetDepletionPredicted` - Early warning
- `ExcessivePersonaSwitching` - May contribute to token waste

---

## Alert 2: High Quality Gate Failure Rate

### Description

**Alert Name:** `HighQualityGateFailureRate`
**Severity:** Warning
**Category:** Quality

Fires when quality gate failure rate exceeds 20% for a workflow stage over 5 minutes.

### Impact

- **Quality:** Lower output quality reaching users
- **Cost:** Increased retries consume more tokens
- **Performance:** Slower workflow execution due to retries
- **Reliability:** Workflows may fail completely if retries exhausted

### Investigation Steps

#### 1. Identify Failing Stage

```promql
# Find stages with >20% failure rate
(
  sum(rate(hypertool_workflow_quality_gate_total{result="fail"}[5m])) by (workflow, stage)
  /
  sum(rate(hypertool_workflow_quality_gate_total[5m])) by (workflow, stage)
) > 0.20
```

#### 2. Check Langfuse for Failed Generations

1. Open Langfuse UI
2. Filter:
   - User = persona for this stage
   - Session metadata: `workflow` = failing workflow, `stage` = failing stage
3. Look for patterns in failed generations:
   - Incomplete outputs
   - Malformed code
   - Missing required sections
   - Format violations

#### 3. Review Quality Gate Criteria

```python
# Find quality gate definition
grep -r "quality_gate" .augment/workflows/
```

Check if criteria are:
- Too strict for current model capabilities
- Misaligned with actual task requirements
- Recently changed

#### 4. Compare Model Performance

```promql
# Quality gate pass rate by model
sum(rate(hypertool_workflow_quality_gate_total{result="pass"}[1h])) by (model)
/
sum(rate(hypertool_workflow_quality_gate_total[1h])) by (model)
```

### Root Causes

| Cause | Indicators | Likelihood |
|-------|-----------|------------|
| **Model degradation** | Sudden drop in pass rate | Medium |
| **Stricter criteria** | Recent quality gate update | High |
| **Prompt issues** | Poor prompt engineering | High |
| **Wrong model tier** | Fast model for complex task | Medium |
| **Input quality** | Bad data feeding into stage | Low |

### Resolution

#### Quick Fix

**Option A: Relax Quality Criteria (Temporary)**

```python
# In workflow definition
quality_gate = {
    "min_lines": 5,  # Reduced from 10
    "required_sections": ["overview"],  # Reduced requirements
}
```

**Option B: Switch to Higher-Tier Model**

```python
# In chatmode config
stages = {
    "implementation": {
        "persona": "backend-engineer",
        "model": "gpt-4",  # Upgraded from gpt-4-mini
        "budget": 2500,    # Increased budget
    }
}
```

#### Long-Term Fix

1. **Prompt Engineering Session**
   - Review failed outputs in Langfuse
   - Identify common failure patterns
   - Enhance prompts with:
     - Clearer instructions
     - Examples of good outputs
     - Explicit format requirements

2. **Quality Gate Calibration**
   ```python
   # Analyze historical data
   SELECT
     quality_gate_criteria,
     pass_rate,
     avg_retry_count
   FROM quality_gate_history
   WHERE workflow = 'feature-implementation'
   GROUP BY quality_gate_criteria
   ```

3. **A/B Testing**
   - Run parallel workflows with different prompts/models
   - Measure quality gate pass rates
   - Adopt best-performing configuration

4. **Feedback Loop**
   ```python
   # Add to Langfuse trace
   trace.metadata = {
       "quality_gate_result": "fail",
       "failure_reason": "Missing code examples",
       "retry_count": 2
   }
   ```

### Prevention

- [ ] Regular prompt reviews
- [ ] Quality gate metrics dashboard
- [ ] A/B testing for critical stages
- [ ] Model performance monitoring
- [ ] Prompt version control

### Related Alerts

- `SlowWorkflowStage` - Retries increase duration
- `TokenBudgetExceeded` - Retries consume extra tokens

---

## Alert 3: Excessive Persona Switching

### Description

**Alert Name:** `ExcessivePersonaSwitching`
**Severity:** Warning
**Category:** Performance

Fires when persona switch rate exceeds 2 switches per second over 5 minutes.

### Impact

- **Quality:** Frequent context changes reduce coherence
- **Efficiency:** Repeated context loading wastes tokens
- **Performance:** Overhead from switching logic
- **Cost:** Increased token usage from context loading

### Investigation Steps

#### 1. Check Switch Rate

```promql
# Current switch rate
sum(rate(hypertool_persona_switches_total[1m]))

# Switches by transition
sum(rate(hypertool_persona_switches_total[5m])) by (from_persona, to_persona, chatmode)
```

#### 2. Identify Switching Patterns

```bash
# Query Grafana dashboard
# Look for oscillating patterns (A → B → A → B)
```

Common patterns:
- **Oscillation:** backend → testing → backend → testing (infinite loop)
- **Scatter:** Rapid switching across many personas (poor routing)
- **Chatmode thrashing:** Switching on every user message

#### 3. Review Chatmode Logic

```python
# Find chatmode switching logic
grep -r "switch_persona" .augment/
grep -r "get_next_persona" .cline/
```

Check for:
- Conditions that trigger switches too frequently
- Missing state to remember previous persona
- Incorrect chatmode detection

#### 4. Check OpenTelemetry Traces

```bash
# Query Jaeger for traces with many persona switches
# Filter: operation_name = "persona_switch"
# Sort by: span count (descending)
```

### Root Causes

| Cause | Indicators | Likelihood |
|-------|-----------|------------|
| **Infinite loop** | A → B → A → B pattern | High |
| **Over-eager routing** | Switch on every message | High |
| **Missing state** | No memory of recent persona | Medium |
| **Bug in chatmode** | Incorrect chatmode detection | Medium |
| **Intentional design** | Workflow requires frequent switches | Low |

### Resolution

#### Quick Fix

**Add Cooldown Period**

```python
# In persona switching logic
class PersonaSwitcher:
    def __init__(self):
        self._last_switch_time = {}
        self._cooldown_seconds = 5  # Minimum time between switches

    def switch_persona(self, from_persona, to_persona, chatmode):
        # Check cooldown
        now = time.time()
        last_switch = self._last_switch_time.get(chatmode, 0)

        if now - last_switch < self._cooldown_seconds:
            logger.debug(f"Cooldown active, skipping switch to {to_persona}")
            return from_persona  # Keep current persona

        # Proceed with switch
        self._last_switch_time[chatmode] = now
        return to_persona
```

#### Long-Term Fix

1. **State Management**
   ```python
   # Add to WorkflowContext
   context.persona_history = []  # Track recent personas
   context.tasks_completed_by_persona = {
       "backend-engineer": ["design_api", "implement_endpoints"]
   }
   ```

2. **Batching Strategy**
   ```python
   # Group similar tasks
   tasks_for_backend = [
       "design_api",
       "implement_endpoints",
       "add_validation"
   ]

   # Switch persona only when changing task type
   ```

3. **Smarter Routing**
   ```python
   def should_switch_persona(current_persona, next_task, context):
       # Only switch if task truly requires different persona
       required_persona = get_persona_for_task(next_task)

       # Check if current persona can handle it
       if current_persona in PERSONA_CAPABILITIES[next_task]:
           return False  # Current persona is capable

       return required_persona != current_persona
   ```

### Prevention

- [ ] Cooldown timers on persona switches
- [ ] State tracking for persona history
- [ ] Task batching by persona type
- [ ] Unit tests for switching logic
- [ ] Dashboard monitoring switch patterns

### Related Alerts

- `TokenBudgetExceeded` - Switching wastes tokens
- `SlowWorkflowStage` - Overhead from switching

---

## Alert 4: Slow Workflow Stage

### Description

**Alert Name:** `SlowWorkflowStage`
**Severity:** Warning
**Category:** Performance

Fires when p95 duration for a workflow stage exceeds 5 minutes (300 seconds) over 10 minutes.

### Impact

- **User Experience:** Slow responses frustrate users
- **Cost:** Longer running time = more compute costs
- **Throughput:** Reduces number of workflows that can run concurrently
- **SLA:** May breach performance SLAs

### Investigation Steps

#### 1. Identify Slow Stage

```promql
# Find stages with p95 > 300s
histogram_quantile(
  0.95,
  sum(rate(hypertool_workflow_stage_duration_seconds_bucket[5m])) by (le, workflow, stage)
) > 300
```

#### 2. Check Langfuse for Slow LLM Calls

1. Open Langfuse UI
2. Filter by workflow + stage
3. Sort by duration (descending)
4. Look for:
   - Very long prompts (high input tokens)
   - Very long completions (high output tokens)
   - Multiple retries
   - Model timeouts

#### 3. Analyze OpenTelemetry Traces

```bash
# Query Jaeger
# Operation: workflow stage name
# Min duration: 300s
```

Identify bottlenecks:
- LLM API latency
- Quality gate validation time
- File I/O operations
- Network calls

#### 4. Check Model Performance

```promql
# LLM call duration by model
histogram_quantile(
  0.95,
  sum(rate(langfuse_generation_duration_seconds_bucket[5m])) by (le, model)
)
```

### Root Causes

| Cause | Indicators | Likelihood |
|-------|-----------|------------|
| **Large prompts** | High input token count | High |
| **Long completions** | High output token count | High |
| **Model latency** | Slow API response times | Medium |
| **Quality gate retries** | Multiple attempts | Medium |
| **Sequential bottleneck** | Lack of parallelization | Low |

### Resolution

#### Quick Fix

**Option A: Reduce Prompt Size**

```python
# Truncate context
context_window = 4000  # tokens
prompt = truncate_context(prompt, max_tokens=context_window)
```

**Option B: Switch to Faster Model**

```python
# Use turbo/mini variant
model = "gpt-4-turbo"  # Instead of "gpt-4"
```

**Option C: Parallelize**

```python
# If stage has independent sub-tasks
results = await asyncio.gather(
    process_subtask_1(),
    process_subtask_2(),
    process_subtask_3()
)
```

#### Long-Term Fix

1. **Prompt Optimization**
   - Remove unnecessary context
   - Use more concise instructions
   - Implement prompt compression techniques

2. **Model Tier Strategy**
   ```python
   # Use different models for different stages
   STAGE_MODEL_MAPPING = {
       "quick_review": "gpt-4-mini",      # Fast, cheap
       "implementation": "gpt-4-turbo",   # Balanced
       "architecture": "gpt-4",           # Quality critical
   }
   ```

3. **Caching Strategy**
   ```python
   # Cache expensive LLM calls
   @cache(ttl=3600)
   def generate_boilerplate(framework: str) -> str:
       return llm.generate(f"Create {framework} boilerplate")
   ```

4. **Streaming Responses**
   ```python
   # Start processing partial results
   async for chunk in llm.stream(prompt):
       await process_chunk(chunk)  # Don't wait for complete response
   ```

### Prevention

- [ ] Prompt length monitoring
- [ ] Model latency tracking
- [ ] Regular performance reviews
- [ ] Caching for repeated patterns
- [ ] Parallel execution where possible

### Related Alerts

- `HighQualityGateFailureRate` - Retries increase duration
- `TokenBudgetExceeded` - Large prompts consume budget

---

## Alert 5: Token Budget Depletion Predicted

### Description

**Alert Name:** `TokenBudgetDepletionPredicted`
**Severity:** Info
**Category:** Cost

Fires when linear prediction indicates persona will exceed budget within 1 hour.

### Impact

- **Financial:** Advance warning of budget overrun
- **Planning:** Time to adjust budgets or usage
- **Prevention:** Avoid hard stops from budget exhaustion

### Investigation Steps

#### 1. Check Prediction

```promql
# Predicted budget in 1 hour
predict_linear(
  hypertool_persona_token_budget_remaining[30m],
  3600
)
```

#### 2. Identify Usage Spike

```promql
# Token usage rate (last 30 min vs previous hour)
sum(rate(hypertool_persona_tokens_used_total[30m])) by (persona)
/
sum(rate(hypertool_persona_tokens_used_total[1h] offset 1h)) by (persona)
```

Ratio > 1.5 indicates significant spike.

#### 3. Check Active Workflows

```bash
# Query OpenTelemetry
# Find: active traces using this persona
# Check: what chatmode/workflow is driving usage
```

### Root Causes

| Cause | Indicators | Likelihood |
|-------|-----------|------------|
| **Expected spike** | Large feature implementation | High |
| **Unexpected usage** | New chatmode/workflow active | Medium |
| **Caching disabled** | Repeated calls not cached | Medium |
| **Budget too low** | Prediction always triggers | Low |

### Resolution

#### Proactive Actions

1. **Verify if Expected**
   - Check current active workflows
   - Confirm if usage spike is intentional
   - No action needed if expected

2. **Increase Budget (If Needed)**
   ```python
   # Temporary increase
   collector.persona_token_budget.labels(persona="backend-engineer").set(3000)
   ```

3. **Enable Caching**
   ```python
   # If not already enabled
   llm_call = CachePrimitive(llm_call, ttl=3600)
   ```

4. **Monitor**
   - Watch actual budget in next hour
   - Confirm prediction accuracy
   - Adjust alert threshold if false positives

### Prevention

- [ ] Right-size budgets based on typical usage
- [ ] Enable caching for all LLM calls
- [ ] Set up budget alerts with graduated severity
- [ ] Review prediction accuracy monthly

---

## Alert 6: Hypertool Metrics Not Reported

### Description

**Alert Name:** `HypertoolMetricsNotReported`
**Severity:** Critical
**Category:** Availability

Fires when Prometheus cannot scrape Hypertool metrics for 2 minutes.

### Impact

- **Observability:** Blind to persona operations
- **Alerting:** Other alerts won't fire
- **Debugging:** Cannot diagnose issues

### Investigation Steps

#### 1. Check Process Status

```bash
# Is Hypertool running?
ps aux | grep hypertool

# Check recent crashes
journalctl -u hypertool --since "5 minutes ago"
```

#### 2. Verify Metrics Endpoint

```bash
# Test metrics endpoint
curl http://localhost:9464/metrics

# Expected: Prometheus metrics
# Actual error: Connection refused / timeout / 404
```

#### 3. Check Prometheus Config

```bash
# Verify scrape config
cat /etc/prometheus/prometheus.yml | grep -A5 hypertool

# Check Prometheus targets
curl http://localhost:9090/api/v1/targets | jq '.data.activeTargets[] | select(.labels.job=="hypertool")'
```

#### 4. Review Application Logs

```bash
# Check for errors
tail -100 /var/log/hypertool/app.log | grep -i error

# Look for:
# - Prometheus client errors
# - Port binding failures
# - Crashes during metrics export
```

### Root Causes

| Cause | Indicators | Likelihood |
|-------|-----------|------------|
| **Process crash** | No process running | High |
| **Port conflict** | Cannot bind to 9464 | Medium |
| **Network issue** | Prometheus can't reach endpoint | Low |
| **Metrics disabled** | Feature flag turned off | Low |

### Resolution

#### Quick Fix

**Restart Application**

```bash
# Systemd
sudo systemctl restart hypertool

# Docker
docker restart hypertool

# Manual
./restart-hypertool.sh
```

#### Investigation

1. **Check Port Availability**
   ```bash
   # Is port 9464 in use?
   sudo lsof -i :9464

   # Kill conflicting process if needed
   sudo kill -9 <PID>
   ```

2. **Verify Metrics Configuration**
   ```python
   # In code
   from prometheus_client import start_http_server
   start_http_server(9464)  # Ensure this is called
   ```

3. **Check Firewall**
   ```bash
   # Ensure port 9464 is open
   sudo ufw allow 9464/tcp
   ```

### Prevention

- [ ] Health check monitoring
- [ ] Auto-restart on crash
- [ ] Alerting on process down
- [ ] Redundant metrics exporters

---

## Alert 7: Langfuse Integration Failing

### Description

**Alert Name:** `LangfuseIntegrationFailing`
**Severity:** Warning
**Category:** Observability

Fires when LLM calls are being made but no Langfuse traces are created.

### Impact

- **Observability:** Missing LLM call details
- **Debugging:** Cannot diagnose LLM issues
- **Optimization:** Cannot optimize prompts

### Investigation Steps

#### 1. Verify Token Usage

```promql
# LLM calls are happening
sum(rate(hypertool_persona_tokens_used_total[5m])) > 0
```

#### 2. Check Langfuse Metrics

```promql
# But no Langfuse traces
absent(langfuse_trace_created_total)
```

#### 3. Test Langfuse Connection

```bash
# Check environment variables
echo $LANGFUSE_PUBLIC_KEY
echo $LANGFUSE_SECRET_KEY
echo $LANGFUSE_HOST

# Test API
curl -H "Authorization: Bearer $LANGFUSE_SECRET_KEY" \
     $LANGFUSE_HOST/api/public/traces
```

#### 4. Check Application Logs

```bash
grep -i langfuse /var/log/hypertool/app.log | tail -50

# Look for:
# - "Langfuse disabled"
# - Authentication errors
# - Connection timeouts
```

### Root Causes

| Cause | Indicators | Likelihood |
|-------|-----------|------------|
| **Missing credentials** | Env vars not set | High |
| **Wrong credentials** | Auth errors in logs | High |
| **Network issue** | Connection timeouts | Medium |
| **SDK not installed** | Import errors | Medium |
| **Graceful degradation** | "Langfuse disabled" logs | Low |

### Resolution

#### Quick Fix

**Set Environment Variables**

```bash
export LANGFUSE_PUBLIC_KEY="pk-lf-..."
export LANGFUSE_SECRET_KEY="sk-lf-..."
export LANGFUSE_HOST="https://cloud.langfuse.com"

# Restart application
sudo systemctl restart hypertool
```

#### Investigation

1. **Verify SDK Installation**
   ```bash
   pip list | grep langfuse

   # If missing
   pip install langfuse
   ```

2. **Test Integration**
   ```python
   # Quick test script
   from langfuse import Langfuse

   client = Langfuse(
       public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
       secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
       host=os.getenv("LANGFUSE_HOST")
   )

   trace = client.trace(name="test")
   print(f"Trace ID: {trace.id}")  # Should print trace ID
   ```

3. **Check Network**
   ```bash
   # Can reach Langfuse?
   curl -I https://cloud.langfuse.com

   # Check proxy settings if behind firewall
   echo $HTTP_PROXY
   echo $HTTPS_PROXY
   ```

### Prevention

- [ ] Config validation on startup
- [ ] Health check for Langfuse
- [ ] Alerting on integration failures
- [ ] Fallback to local logging if Langfuse unavailable

---

## General Troubleshooting Tips

### Quick Diagnostic Commands

```bash
# Check all Hypertool metrics
curl http://localhost:9464/metrics | grep hypertool

# Query Prometheus
curl 'http://localhost:9090/api/v1/query?query=hypertool_persona_token_budget_remaining'

# Check active alerts
curl http://localhost:9090/api/v1/alerts

# View Langfuse traces
open https://cloud.langfuse.com
```

### Common Issues

| Symptom | Likely Cause | Quick Fix |
|---------|--------------|-----------|
| All metrics zero | Metrics not initialized | Restart application |
| Budget not updating | Token tracking disabled | Enable PersonaMetricsCollector |
| No Langfuse traces | Missing credentials | Set env vars |
| High alert noise | Thresholds too sensitive | Adjust alert rules |

### Escalation Path

1. **Level 1:** Check this runbook
2. **Level 2:** Review application logs
3. **Level 3:** Check Grafana dashboards
4. **Level 4:** Contact development team

---

**Last Updated:** 2025-11-15
**Version:** 1.0
**Maintained by:** Hypertool Team


---
**Logseq:** [[TTA.dev/.hypertool/Instrumentation/Alert_runbook]]
