# Quick Start: Observability for Primitives, Integrations & Personas

**Get full observability in 5 minutes**

---

## ✅ What You Already Have

Your TTA.dev primitives **already have automatic OpenTelemetry tracing** via `InstrumentedPrimitive`:

```python
from tta_dev_primitives import SequentialPrimitive, RouterPrimitive

# This workflow is ALREADY instrumented - no code changes needed!
workflow = step1 >> RouterPrimitive(...) >> step3

# When you run it, automatic spans created:
# - primitive.Step1
# - primitive.RouterPrimitive
# - primitive.Step3
```

**Zero configuration required for primitive observability!**

---

## 🚀 Enable Full Stack (3 Steps)

### Step 1: Initialize Observability (30 seconds)

```python
from observability_integration import initialize_observability

# At application startup
initialize_observability(
    service_name="tta-dev-copilot",  # Your workspace name
    enable_prometheus=True,
    prometheus_port=9464,
)

# That's it! Now running...
```

**Verify it works:**
```bash
curl http://localhost:9464/metrics | grep tta_
```

### Step 2: Install Grafana Alloy (5 minutes)

```bash
# Get Grafana Cloud token
TOKEN=$(grep GRAFANA_CLOUD_API_KEY ~/.env.tta-dev | cut -d= -f2)

# Run installation script
cd /home/thein/repos/TTA.dev
sudo GRAFANA_CLOUD_TOKEN="$TOKEN" ./scripts/setup-native-observability.sh
```

**What this does:**
- ✅ Installs Grafana Alloy (Linux-native, replaces Docker)
- ✅ Scrapes Prometheus metrics from :9464
- ✅ Collects OTLP traces from :4317/4318
- ✅ Forwards systemd logs
- ✅ Sends everything to Grafana Cloud

**Check it's running:**
```bash
sudo systemctl status alloy
curl http://localhost:12345/metrics | grep alloy_
```

### Step 3: Add Langfuse for LLM Calls (2 minutes)

**For LLM-specific observability (prompts, completions, costs):**

```python
from .hypertool.instrumentation.langfuse_integration import LangfuseIntegration

# Initialize once (uses env vars)
langfuse = LangfuseIntegration()

# Wrap your LLM calls
trace = langfuse.start_trace(
    name="feature-implementation",
    persona="backend-engineer",
    chatmode="coding",
)

# Your LLM call here
response = await openai.chat.completions.create(...)

# Track it
langfuse.create_generation(
    trace=trace,
    name="gpt4-coding",
    model="gpt-4",
    prompt=prompt,
    completion=response.choices[0].message.content,
    usage={"prompt_tokens": 150, "completion_tokens": 800},
)

langfuse.end_trace(trace, output={"code": "..."})
```

**Set environment variables:**
```bash
# Add to ~/.env.tta-dev
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...
LANGFUSE_HOST=https://cloud.langfuse.com
```

---

## 📊 What You Get

### OpenTelemetry (Automatic)

**All TTA.dev primitives automatically traced:**

```python
# This code automatically creates spans:
workflow = (
    input_processor >>
    RouterPrimitive(routes={"fast": llm1, "quality": llm2}) >>
    RetryPrimitive(max_retries=3) >>
    output_formatter
)

# Span hierarchy:
# ├─ primitive.InputProcessor (10ms)
# ├─ primitive.RouterPrimitive (250ms)
# │  └─ llm.gpt-4-mini (240ms)
# ├─ primitive.RetryPrimitive (300ms)
# │  ├─ attempt_1 (failed, 100ms)
# │  ├─ attempt_2 (failed, 100ms)
# │  └─ attempt_3 (success, 100ms)
# └─ primitive.OutputFormatter (5ms)
```

### Grafana Cloud (Infrastructure + Metrics)

**Dashboards:**
- CPU, RAM, disk usage
- Primitive execution rates
- Error rates by primitive type
- Latency percentiles (p50, p95, p99)
- Cost tracking (if instrumented)

**Queries:**
```promql
# Primitive performance
histogram_quantile(0.95,
  rate(primitive_execution_duration_seconds_bucket[5m])
)

# Filter by workspace
{service_name="tta-dev-copilot"}

# Filter by persona
{persona="backend-engineer"}
```

### Langfuse (LLM Analytics)

**Views:**
- **Traces** - Full workflow traces with LLM calls
- **Generations** - All LLM completions with full prompt/completion text
- **Users** - Analytics by persona (backend-engineer, frontend-dev, etc.)
- **Costs** - Token usage and $ breakdown
- **Quality** - Score and evaluate LLM outputs

**Example trace:**
```
Trace: feature-implementation (persona: backend-engineer)
├─ Generation: gpt4-design (150 tokens in, 800 tokens out, $0.02)
├─ Generation: gpt4-implementation (200 tokens in, 1500 tokens out, $0.04)
└─ Generation: gpt4-review (100 tokens in, 300 tokens out, $0.01)

Total cost: $0.07
Total time: 12.5s
```

---

## 🎯 Use Cases

### 1. Debug Slow Workflows

**Grafana Cloud:**
```promql
# Find slowest primitives
topk(5, avg by (primitive_name) (
  primitive_execution_duration_seconds
))
```

**Result:**
```
1. RetryPrimitive - 2.5s avg (3 retries)
2. LLMAnalyzer - 1.8s avg (gpt-4 call)
3. DataFetcher - 0.5s avg (API call)
```

**Langfuse:**
- View trace for slow execution
- See which LLM call took longest
- Check if prompt can be optimized

### 2. Optimize LLM Costs

**Langfuse Dashboard:**
- **Total cost today:** $45.23
- **Most expensive model:** gpt-4 ($32.50 / 72%)
- **Most expensive trace:** feature-implementation ($0.85 avg)

**Action:**
- Switch simple queries from gpt-4 → gpt-4-mini
- Implement caching for repeated prompts
- Use RouterPrimitive to route by complexity

**Expected savings:** 40-60% cost reduction

### 3. Track Persona Performance

**Grafana Cloud query:**
```promql
# Compare persona performance
sum by (persona) (rate(primitive_executions_total[1h]))
```

**Langfuse query:**
- User: `backend-engineer` → 150 LLM calls today
- User: `frontend-dev` → 80 LLM calls today
- Compare quality scores between personas

### 4. Monitor Integration Health

**Grafana Cloud:**
```promql
# OpenAI integration error rate
sum(rate(primitive_executions_total{
  primitive_name=~"OpenAI.*",
  status="error"
}[5m]))
```

**Langfuse:**
- Filter by model: `gpt-4`
- See failed generations
- Review error messages in traces

---

## 📋 Checklist

**Setup:**
- [ ] Run `initialize_observability()` in your app
- [ ] Install Grafana Alloy with `setup-native-observability.sh`
- [ ] Set up Langfuse account and API keys
- [ ] Add Langfuse to LLM calls

**Verify:**
- [ ] Metrics endpoint working: `curl http://localhost:9464/metrics`
- [ ] Alloy running: `sudo systemctl status alloy`
- [ ] Grafana Cloud receiving data: https://theinterneti.grafana.net/
- [ ] Langfuse receiving traces: https://cloud.langfuse.com/

**Use:**
- [ ] Create Grafana dashboards for your primitives
- [ ] Set up alerts for high error rates
- [ ] Track LLM costs in Langfuse
- [ ] Score LLM outputs for quality

---

## 🔗 Next Steps

1. **Read the full guide:** [`UNIFIED_OBSERVABILITY_ARCHITECTURE.md`](UNIFIED_OBSERVABILITY_ARCHITECTURE.md)
2. **Multi-workspace setup:** [`MULTI_WORKSPACE_OBSERVABILITY.md`](MULTI_WORKSPACE_OBSERVABILITY.md)
3. **Langfuse details:** [`../../.hypertool/instrumentation/LANGFUSE_INTEGRATION.md`](../../.hypertool/instrumentation/LANGFUSE_INTEGRATION.md)
4. **Primitives reference:** [`../../PRIMITIVES_CATALOG.md`](../../PRIMITIVES_CATALOG.md)

---

**Questions?**
- Workspace configuration: See [`../troubleshooting/WORKSPACE_CONFIGURATION_FIX.md`](../troubleshooting/WORKSPACE_CONFIGURATION_FIX.md)
- Observability quickstart: See [`../quickstart/OBSERVABILITY_QUICKSTART.md`](../quickstart/OBSERVABILITY_QUICKSTART.md)

---

**Last Updated:** November 15, 2025


---
**Logseq:** [[TTA.dev/Docs/Quickstart/Observability_unified_quickstart]]
