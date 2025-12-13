# Unified Observability Architecture for TTA.dev

**Complete observability across Primitives, Integrations, and Personas**

**Last Updated:** November 15, 2025
**Status:** Production-Ready

---

## 🎯 Overview

TTA.dev provides **three layers of observability** that work together:

1. **OpenTelemetry (Built-in)** - All primitives automatically traced
2. **Grafana Cloud** - Infrastructure metrics, logs, traces
3. **Langfuse** - LLM-specific observability (prompts, completions, costs)

This architecture supports:
- ✅ **TTA.dev Primitives** - Sequential, Parallel, Router, Retry workflows
- ✅ **Integrations** - OpenAI, Anthropic, Supabase, E2B, etc.
- ✅ **Persona Switching** - Hypertool context changes
- ✅ **Multi-Workspace** - Different service names per workspace

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  TTA.dev Application (Primitives + Integrations)            │
│                                                              │
│  ┌────────────────────┐  ┌──────────────────────┐          │
│  │ InstrumentedPrimitive │  │ Integrations (LLM) │          │
│  │ - Sequential        │  │ - OpenAI           │          │
│  │ - Parallel          │  │ - Anthropic        │          │
│  │ - Router            │  │ - Supabase         │          │
│  │ - Retry             │  │ - E2B              │          │
│  └─────────┬───────────┘  └──────────┬───────────┘          │
│            │                          │                      │
│            v                          v                      │
│  ┌──────────────────────────────────────────────────┐       │
│  │     OpenTelemetry SDK (Auto-Instrumentation)     │       │
│  │     - Spans, Traces, Context Propagation         │       │
│  └────────────┬──────────────────┬──────────────────┘       │
│               │                   │                          │
└───────────────┼───────────────────┼──────────────────────────┘
                │                   │
                v                   v
    ┌──────────────────┐  ┌─────────────────────────┐
    │ Grafana Alloy    │  │ Langfuse                │
    │ (Local Agent)    │  │ (LLM Observability)     │
    │                  │  │                         │
    │ - Scrapes :9464  │  │ - Traces LLM calls      │
    │ - OTLP :4317/8   │  │ - Tracks prompts        │
    │ - Systemd logs   │  │ - Cost analytics        │
    └────────┬─────────┘  └──────────┬──────────────┘
             │                        │
             v                        v
    ┌─────────────────────┐  ┌───────────────────┐
    │ Grafana Cloud       │  │ Langfuse Cloud    │
    │ - Prometheus        │  │ - Prompt mgmt     │
    │ - Loki (logs)       │  │ - Token costs     │
    │ - Tempo (traces)    │  │ - Quality scores  │
    └─────────────────────┘  └───────────────────┘
```

---

## 📊 Observability Matrix

### What Each Layer Tracks

| Aspect | OpenTelemetry | Grafana Alloy | Langfuse |
|--------|---------------|---------------|----------|
| **Primitive Execution** | ✅ Spans, timing | ✅ Metrics | ❌ N/A |
| **Infrastructure Metrics** | ❌ | ✅ CPU, RAM, disk | ❌ |
| **Application Logs** | ❌ | ✅ Systemd, app logs | ❌ |
| **LLM Calls** | ✅ Spans (generic) | ✅ Metrics | ✅ Full context |
| **Prompt/Completion Text** | ❌ | ❌ | ✅ Full text |
| **Token Costs** | ❌ | ✅ Counter | ✅ Per-call breakdown |
| **Model Performance** | ❌ | ✅ Latency | ✅ Quality scores |
| **Persona Switching** | ✅ Context tags | ✅ Labels | ✅ User metadata |
| **Workflow Composition** | ✅ Parent-child spans | ✅ Metrics | ❌ |
| **Error Tracing** | ✅ Exceptions | ✅ Error logs | ✅ Failed generations |

---

## 🚀 Setup Guide

### Step 1: Initialize OpenTelemetry (Built-in)

**All TTA.dev primitives automatically inherit from `InstrumentedPrimitive`** - no code changes needed!

```python
from tta_dev_primitives import SequentialPrimitive, RouterPrimitive
from tta_dev_primitives.recovery import RetryPrimitive
from observability_integration import initialize_observability

# Initialize once at application startup
initialize_observability(
    service_name="tta-dev-copilot",  # Your workspace name
    enable_prometheus=True,
    prometheus_port=9464,
)

# Your primitives are automatically instrumented!
workflow = (
    input_processor >>
    RouterPrimitive(routes={"fast": llm1, "quality": llm2}) >>
    RetryPrimitive(max_retries=3) >>
    output_formatter
)

# Traces automatically created with:
# - primitive.InputProcessor
# - primitive.RouterPrimitive
# - primitive.RetryPrimitive
# - primitive.OutputFormatter
```

**No decorators, no manual span creation - automatic!**

### Step 2: Install Grafana Alloy (Linux-Native)

**Grafana Alloy replaces Docker Compose** and sends metrics/traces/logs to Grafana Cloud:

```bash
# Get your Grafana Cloud token
TOKEN=$(grep GRAFANA_CLOUD_API_KEY ~/.env.tta-dev | cut -d= -f2)

# Run installation script
cd /home/thein/repos/TTA.dev
sudo GRAFANA_CLOUD_TOKEN="$TOKEN" ./scripts/setup-native-observability.sh
```

This installs:
- ✅ Grafana Alloy (systemd service)
- ✅ Prometheus metrics scraping (port 9464)
- ✅ OTLP trace collection (ports 4317/4318)
- ✅ Systemd log forwarding

**See:** [`docs/guides/LINUX_NATIVE_OBSERVABILITY.md`](LINUX_NATIVE_OBSERVABILITY.md)

### Step 3: Add Langfuse for LLM Observability

**Langfuse provides LLM-specific analytics** (prompts, completions, costs):

```python
from .hypertool.instrumentation.langfuse_integration import LangfuseIntegration

# Initialize Langfuse (uses env vars: LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY)
langfuse = LangfuseIntegration()

# Start trace with persona context
trace = langfuse.start_trace(
    name="feature-implementation",
    persona="backend-engineer",
    chatmode="feature-implementation",
)

# Wrap your LLM call
generation = langfuse.create_generation(
    trace=trace,
    name="api-design",
    model="gpt-4",
    prompt="Design REST API for user profiles",
    completion="Here's the API design...",
    usage={"prompt_tokens": 150, "completion_tokens": 800},
)
```

**See:** [`.hypertool/instrumentation/LANGFUSE_INTEGRATION.md`](../../.hypertool/instrumentation/LANGFUSE_INTEGRATION.md)

---

## 🔗 Integration Patterns

### Pattern 1: Primitive Workflow with LLM Calls

**Automatic OpenTelemetry + Manual Langfuse:**

```python
from tta_dev_primitives import SequentialPrimitive, WorkflowContext
from tta_dev_primitives.observability import InstrumentedPrimitive
from .hypertool.instrumentation.langfuse_integration import LangfuseIntegration

class LLMAnalyzerPrimitive(InstrumentedPrimitive[dict, dict]):
    """Primitive that calls LLM with Langfuse tracking."""

    def __init__(self):
        super().__init__(name="LLMAnalyzer")
        self.langfuse = LangfuseIntegration()

    async def _execute_impl(self, input_data: dict, context: WorkflowContext) -> dict:
        # OpenTelemetry span created automatically by InstrumentedPrimitive

        # Start Langfuse trace (for LLM-specific analytics)
        trace = self.langfuse.start_trace(
            name="document-analysis",
            persona=input_data.get("persona", "analyst"),
            chatmode="analysis",
        )

        # Call LLM
        prompt = f"Analyze: {input_data['text']}"
        response = await openai.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
        )

        # Track in Langfuse
        self.langfuse.create_generation(
            trace=trace,
            name="gpt4-analysis",
            model="gpt-4",
            prompt=prompt,
            completion=response.choices[0].message.content,
            usage={
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
            },
        )

        # End trace
        self.langfuse.end_trace(trace, output={"analysis": response.choices[0].message.content})

        return {"analysis": response.choices[0].message.content}


# Use in workflow
workflow = (
    input_processor >>
    LLMAnalyzerPrimitive() >>  # Automatic OpenTelemetry + Langfuse
    output_formatter
)

context = WorkflowContext(workflow_id="doc-analysis")
result = await workflow.execute({"text": "...", "persona": "analyst"}, context)
```

**Result:**
- ✅ OpenTelemetry span: `primitive.LLMAnalyzer` (timing, context)
- ✅ Langfuse trace: `document-analysis` (prompt, completion, tokens, cost)
- ✅ Grafana metrics: `primitive_execution_duration_seconds{primitive_name="LLMAnalyzer"}`

### Pattern 2: Integration Primitive

**For integrations (OpenAI, Anthropic, Supabase, E2B):**

```python
from tta_dev_integrations import OpenAIPrimitive
from observability_integration import initialize_observability

# Initialize observability
initialize_observability(service_name="tta-dev-main")

# Use integration primitive (automatically instrumented)
openai_primitive = OpenAIPrimitive(
    model="gpt-4",
    temperature=0.7,
)

# Automatic observability!
result = await openai_primitive.execute({"prompt": "Hello"}, context)
```

**See:** [`packages/tta-dev-integrations/`](../../packages/tta-dev-integrations/)

### Pattern 3: Persona Switching (Hypertool)

**Track persona changes with all three layers:**

```python
from .hypertool.instrumentation.langfuse_integration import LangfuseIntegration
from tta_dev_primitives import WorkflowContext

# Initialize Langfuse
langfuse = LangfuseIntegration()

def switch_persona(new_persona: str, chatmode: str, context: WorkflowContext):
    """Switch persona and update observability context."""

    # Update WorkflowContext (propagates to OpenTelemetry)
    context.metadata["persona"] = new_persona
    context.metadata["chatmode"] = chatmode
    context.tags["persona"] = new_persona  # For Grafana filtering

    # Start new Langfuse trace for persona
    trace = langfuse.start_trace(
        name=f"persona-{chatmode}",
        persona=new_persona,
        chatmode=chatmode,
    )

    return trace

# Usage
context = WorkflowContext(workflow_id="dev-session")
trace = switch_persona("backend-engineer", "feature-implementation", context)

# Now all primitives and LLM calls are tagged with persona
workflow = step1 >> llm_call >> step2
result = await workflow.execute(data, context)
```

**Query in Grafana:**
```promql
# Filter by persona
primitive_execution_duration_seconds{persona="backend-engineer"}

# Compare personas
sum by (persona) (rate(primitive_executions_total[5m]))
```

**Query in Langfuse:**
- Filter by user: `backend-engineer`
- View all traces for that persona
- See prompt/completion patterns

---

## 📈 Querying Observability Data

### Grafana Cloud (Metrics & Traces)

**Prometheus queries:**

```promql
# Primitive execution rate
rate(primitive_executions_total[5m])

# Primitive duration by type
histogram_quantile(0.95,
  rate(primitive_execution_duration_seconds_bucket[5m])
)

# LLM cost tracking (if instrumented)
sum by (model) (rate(llm_cost_usd_total[1h]))

# Filter by workspace
{service_name="tta-dev-copilot"}

# Filter by persona
{persona="backend-engineer"}
```

**Loki log queries:**

```logql
# All logs from TTA.dev
{job="systemd-journal", service_name=~"tta-dev-.*"}

# Errors only
{service_name="tta-dev-copilot"} |= "ERROR"

# LLM calls
{service_name="tta-dev-main"} |= "llm" |= "completion"
```

**Tempo trace queries:**

- Navigate to Explore → Tempo
- Query: `{service.name="tta-dev-copilot"}`
- View traces with primitive spans

### Langfuse Cloud (LLM Analytics)

**Dashboard views:**

1. **Traces** - View full workflow traces with LLM calls
2. **Generations** - See all LLM completions with prompts
3. **Users** - Persona-based analytics (backend-engineer, frontend-dev, etc.)
4. **Costs** - Token usage and cost breakdown
5. **Quality** - Score LLM outputs

**Example queries:**

- User: `backend-engineer` → See all LLM calls from backend persona
- Model: `gpt-4` → Compare with `gpt-4-mini` performance
- Trace name: `feature-implementation` → View specific workflow type

---

## 🔧 Configuration

### Environment Variables

```bash
# Grafana Cloud
GRAFANA_CLOUD_API_KEY=<your-token>
GRAFANA_CLOUD_STACK=<your-stack-id>
GRAFANA_CLOUD_REGION=prod-us-east-0  # or your region

# Langfuse
LANGFUSE_PUBLIC_KEY=<your-public-key>
LANGFUSE_SECRET_KEY=<your-secret-key>
LANGFUSE_HOST=https://cloud.langfuse.com  # or self-hosted URL
```

**Store in:** `~/.env.tta-dev`

### Application Configuration

```python
# At application startup
from observability_integration import initialize_observability
from .hypertool.instrumentation.langfuse_integration import LangfuseIntegration
import os
from dotenv import load_dotenv

load_dotenv("~/.env.tta-dev")

# Initialize OpenTelemetry + Prometheus
initialize_observability(
    service_name=os.getenv("SERVICE_NAME", "tta-dev-main"),
    enable_prometheus=True,
    prometheus_port=9464,
)

# Initialize Langfuse (for LLM calls)
langfuse = LangfuseIntegration()

# Your application code...
```

---

## 🎯 Multi-Workspace Setup

### Recommended: Same Port, Different Service Names

```python
# TTA.dev (main)
initialize_observability(service_name="tta-dev-main", prometheus_port=9464)

# TTA.dev-cline
initialize_observability(service_name="tta-dev-cline", prometheus_port=9464)

# TTA.dev-copilot
initialize_observability(service_name="tta-dev-copilot", prometheus_port=9464)
```

**Constraint:** Only run one workspace at a time (port 9464 conflict).

**Grafana Alloy config** (single scrape target):

```alloy
prometheus.scrape "tta_app" {
  targets = [{
    __address__ = "localhost:9464",
  }]
  forward_to = [prometheus.remote_write.grafana_cloud.receiver]
}
```

**Query by service name:**
```promql
{service_name="tta-dev-copilot"}
```

### Advanced: Multiple Ports

**If you need to run multiple workspaces simultaneously:**

```python
# TTA.dev (main) - port 9464
initialize_observability(service_name="tta-dev-main", prometheus_port=9464)

# TTA.dev-cline - port 9465
initialize_observability(service_name="tta-dev-cline", prometheus_port=9465)

# TTA.dev-copilot - port 9466
initialize_observability(service_name="tta-dev-copilot", prometheus_port=9466)
```

**Update Grafana Alloy config** to scrape all ports:

```alloy
prometheus.scrape "tta_main" {
  targets = [{__address__ = "localhost:9464", workspace = "main"}]
  forward_to = [prometheus.remote_write.grafana_cloud.receiver]
}

prometheus.scrape "tta_cline" {
  targets = [{__address__ = "localhost:9465", workspace = "cline"}]
  forward_to = [prometheus.remote_write.grafana_cloud.receiver]
}

prometheus.scrape "tta_copilot" {
  targets = [{__address__ = "localhost:9466", workspace = "copilot"}]
  forward_to = [prometheus.remote_write.grafana_cloud.receiver]
}
```

**See:** [`docs/guides/MULTI_WORKSPACE_OBSERVABILITY.md`](MULTI_WORKSPACE_OBSERVABILITY.md)

---

## 🆘 Troubleshooting

### Metrics Not Appearing in Grafana

**Check Prometheus endpoint:**
```bash
curl http://localhost:9464/metrics | grep tta_
```

**Check Alloy status:**
```bash
sudo systemctl status alloy
journalctl -u alloy -n 50
```

**Verify scrape config:**
```bash
sudo cat /etc/alloy/config.alloy | grep -A 10 "prometheus.scrape"
```

### Langfuse Traces Not Showing

**Check environment variables:**
```bash
echo $LANGFUSE_PUBLIC_KEY
echo $LANGFUSE_SECRET_KEY
```

**Check initialization:**
```python
from .hypertool.instrumentation.langfuse_integration import LangfuseIntegration

langfuse = LangfuseIntegration()
print(f"Langfuse enabled: {langfuse.enabled}")
```

**Flush traces:**
```python
langfuse.flush()  # Force send pending traces
```

### OpenTelemetry Spans Missing

**Check if OpenTelemetry is installed:**
```bash
uv run python -c "from opentelemetry import trace; print('OpenTelemetry OK')"
```

**Verify initialization:**
```python
from observability_integration import is_observability_enabled
print(f"Observability: {is_observability_enabled()}")
```

---

## 📚 Related Documentation

- **Linux-Native Observability:** [`LINUX_NATIVE_OBSERVABILITY.md`](LINUX_NATIVE_OBSERVABILITY.md)
- **Multi-Workspace Setup:** [`MULTI_WORKSPACE_OBSERVABILITY.md`](MULTI_WORKSPACE_OBSERVABILITY.md)
- **Langfuse Integration:** [`../../.hypertool/instrumentation/LANGFUSE_INTEGRATION.md`](../../.hypertool/instrumentation/LANGFUSE_INTEGRATION.md)
- **Primitives Catalog:** [`../../PRIMITIVES_CATALOG.md`](../../PRIMITIVES_CATALOG.md)
- **Integrations Package:** [`../../packages/tta-dev-integrations/README.md`](../../packages/tta-dev-integrations/README.md)

---

## ✅ Quick Start Checklist

- [ ] Install Grafana Alloy: `sudo ./scripts/setup-native-observability.sh`
- [ ] Initialize observability: `initialize_observability(service_name="tta-dev-copilot")`
- [ ] Set up Langfuse account and API keys
- [ ] Add Langfuse to your LLM calls
- [ ] Verify metrics: `curl http://localhost:9464/metrics`
- [ ] Check Grafana Cloud: https://theinterneti.grafana.net/
- [ ] Check Langfuse dashboard: https://cloud.langfuse.com/

---

**Last Updated:** November 15, 2025
**Status:** Production-Ready
**Maintained by:** TTA.dev Team


---
**Logseq:** [[TTA.dev/Docs/Guides/Unified_observability_architecture]]
