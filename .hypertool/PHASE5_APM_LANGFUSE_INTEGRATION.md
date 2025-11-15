# Phase 5: APM Integration & Langfuse Connection

**Comprehensive observability for Hypertool persona system with Langfuse LLM observability**

**Status:** 🚧 Planning  
**Created:** 2025-11-15  
**Phase:** 5 of 6 (Hypertool Roadmap)

---

## 📊 Overview

Integrate Application Performance Monitoring (APM) with the Hypertool persona system and connect to Langfuse for comprehensive LLM observability. This enables:

- **Persona Performance Tracking** - Monitor persona switching, token usage, workflow execution
- **LLM Observability** - Trace all LLM calls with Langfuse (costs, latency, quality)
- **Business Metrics** - Correlate technical metrics with business outcomes (MTTR, deployment frequency, error budgets)
- **Real-Time Dashboards** - Grafana dashboards for persona and workflow monitoring
- **Production Insights** - Understand workflow performance patterns for optimization

---

## 🎯 Goals

### Primary Goals

1. **Persona Metrics** - Track persona usage, switching frequency, token efficiency
2. **Workflow Observability** - Monitor multi-persona workflows end-to-end
3. **LLM Tracing** - Capture all LLM calls with Langfuse for cost and quality analysis
4. **Grafana Dashboards** - Visualize persona and workflow metrics
5. **Alerting** - Prometheus alerts for persona budget overruns, workflow failures

### Success Criteria

- ✅ All persona switches tracked in Prometheus
- ✅ Workflow execution time <1s overhead for observability
- ✅ 100% LLM call coverage in Langfuse traces
- ✅ Grafana dashboard showing persona distribution and token usage
- ✅ Alerts trigger on persona budget violations

---

## 🏗️ Architecture

### Component Overview

```text
┌─────────────────────────────────────────────────────────────┐
│  Hypertool Persona System                                   │
│  ├─ tta-persona CLI                                         │
│  ├─ Chatmodes (28 validated)                                │
│  └─ Multi-Persona Workflows (3 production examples)         │
└───────────────┬─────────────────────────────────────────────┘
                │
                ↓
┌─────────────────────────────────────────────────────────────┐
│  APM Integration Layer (NEW)                                │
│  ├─ PersonaMetricsCollector                                 │
│  ├─ WorkflowTracer                                          │
│  └─ LangfuseIntegration                                     │
└───────────────┬─────────────────────────────────────────────┘
                │
    ┌───────────┼───────────┐
    ↓           ↓           ↓
┌─────────┐ ┌──────────┐ ┌─────────────┐
│OpenTel- │ │Prometheus│ │  Langfuse   │
│emetry   │ │ Metrics  │ │  Platform   │
│ (Traces)│ │ (9464)   │ │  (Cloud)    │
└─────────┘ └──────────┘ └─────────────┘
    │           │           │
    └───────────┼───────────┘
                ↓
    ┌───────────────────────┐
    │  Grafana Dashboards   │
    │  ├─ Persona Overview  │
    │  ├─ Workflow Metrics  │
    │  └─ LLM Cost Analysis │
    └───────────────────────┘
```

### Integration Points

1. **tta-persona CLI** - Instrument persona switches with metrics
2. **Multi-Persona Workflows** - Add tracing spans for each stage
3. **TTA Primitives** - Existing observability (already instrumented)
4. **Langfuse SDK** - Wrap LLM calls for deep observability

---

## 📋 Implementation Plan

### Week 1: Core APM Integration (8-12 hours)

#### Day 1-2: Persona Metrics Collection

**Create PersonaMetricsCollector:**

```python
# File: .hypertool/instrumentation/persona_metrics.py

from prometheus_client import Counter, Histogram, Gauge
from opentelemetry import trace
from typing import Optional
import time

# Prometheus metrics
persona_switches = Counter(
    'hypertool_persona_switches_total',
    'Total persona switches',
    ['from_persona', 'to_persona', 'chatmode']
)

persona_duration = Histogram(
    'hypertool_persona_duration_seconds',
    'Time spent in each persona',
    ['persona', 'chatmode'],
    buckets=[10, 30, 60, 120, 300, 600, 1800, 3600]  # 10s to 1h
)

persona_token_usage = Counter(
    'hypertool_persona_tokens_used_total',
    'Tokens consumed per persona',
    ['persona', 'chatmode', 'model']
)

persona_token_budget = Gauge(
    'hypertool_persona_token_budget_remaining',
    'Remaining token budget for persona',
    ['persona']
)

workflow_stage_duration = Histogram(
    'hypertool_workflow_stage_duration_seconds',
    'Duration of workflow stages',
    ['workflow', 'stage', 'persona'],
    buckets=[1, 5, 10, 30, 60, 120, 300, 600]  # 1s to 10min
)

workflow_quality_gate_result = Counter(
    'hypertool_workflow_quality_gate_total',
    'Quality gate pass/fail results',
    ['workflow', 'stage', 'result']  # result: passed/failed
)

tracer = trace.get_tracer(__name__)


class PersonaMetricsCollector:
    """Collect metrics for Hypertool persona usage."""

    def __init__(self):
        self.current_persona: Optional[str] = None
        self.persona_start_time: Optional[float] = None

    def switch_persona(
        self,
        from_persona: Optional[str],
        to_persona: str,
        chatmode: str
    ) -> None:
        """Track persona switch."""
        # Record duration in previous persona
        if from_persona and self.persona_start_time:
            duration = time.time() - self.persona_start_time
            persona_duration.labels(
                persona=from_persona,
                chatmode=chatmode
            ).observe(duration)

        # Record switch
        persona_switches.labels(
            from_persona=from_persona or "none",
            to_persona=to_persona,
            chatmode=chatmode
        ).inc()

        # Create OpenTelemetry span
        with tracer.start_as_current_span("persona_switch") as span:
            span.set_attribute("from_persona", from_persona or "none")
            span.set_attribute("to_persona", to_persona)
            span.set_attribute("chatmode", chatmode)

        # Update state
        self.current_persona = to_persona
        self.persona_start_time = time.time()

    def record_token_usage(
        self,
        persona: str,
        chatmode: str,
        model: str,
        tokens: int
    ) -> None:
        """Track token consumption."""
        persona_token_usage.labels(
            persona=persona,
            chatmode=chatmode,
            model=model
        ).inc(tokens)

        # Update remaining budget (would need config integration)
        # persona_token_budget.labels(persona=persona).set(remaining)

    def record_workflow_stage(
        self,
        workflow: str,
        stage: str,
        persona: str,
        duration_seconds: float,
        quality_gate_passed: bool
    ) -> None:
        """Track workflow stage completion."""
        workflow_stage_duration.labels(
            workflow=workflow,
            stage=stage,
            persona=persona
        ).observe(duration_seconds)

        workflow_quality_gate_result.labels(
            workflow=workflow,
            stage=stage,
            result="passed" if quality_gate_passed else "failed"
        ).inc()


# Global collector instance
_metrics_collector = PersonaMetricsCollector()

def get_persona_metrics_collector() -> PersonaMetricsCollector:
    """Get global persona metrics collector."""
    return _metrics_collector
```

**Instrument tta-persona CLI:**

```python
# File: .hypertool/cli/persona.py (modifications)

from ..instrumentation.persona_metrics import get_persona_metrics_collector

def switch_persona(to_persona: str, chatmode: str = None):
    """Switch to a different persona."""
    collector = get_persona_metrics_collector()
    current = get_current_persona()
    
    # Record switch
    collector.switch_persona(
        from_persona=current,
        to_persona=to_persona,
        chatmode=chatmode or "default"
    )
    
    # ... existing switch logic
```

#### Day 3-4: Workflow Tracing

**Create WorkflowTracer:**

```python
# File: .hypertool/instrumentation/workflow_tracing.py

from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode
from typing import Any, Dict, Optional
import time

tracer = trace.get_tracer(__name__)


class WorkflowTracer:
    """OpenTelemetry tracing for multi-persona workflows."""

    def __init__(self, workflow_name: str):
        self.workflow_name = workflow_name
        self.current_span: Optional[trace.Span] = None

    async def __aenter__(self):
        """Start workflow span."""
        self.current_span = tracer.start_as_current_span(
            f"workflow.{self.workflow_name}",
            attributes={
                "workflow.name": self.workflow_name,
                "workflow.type": "multi_persona"
            }
        )
        self.current_span.__enter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """End workflow span."""
        if exc_type:
            self.current_span.set_status(
                Status(StatusCode.ERROR, str(exc_val))
            )
            self.current_span.record_exception(exc_val)
        else:
            self.current_span.set_status(Status(StatusCode.OK))

        self.current_span.__exit__(exc_type, exc_val, exc_tb)

    async def trace_stage(
        self,
        stage_name: str,
        persona: str,
        func,
        *args,
        **kwargs
    ) -> Any:
        """Trace a workflow stage execution."""
        start_time = time.time()
        
        with tracer.start_as_current_span(f"stage.{stage_name}") as span:
            span.set_attribute("stage.name", stage_name)
            span.set_attribute("stage.persona", persona)
            span.set_attribute("workflow.name", self.workflow_name)

            try:
                result = await func(*args, **kwargs)
                
                duration = time.time() - start_time
                span.set_attribute("stage.duration_seconds", duration)
                span.set_attribute("stage.success", True)
                span.set_status(Status(StatusCode.OK))
                
                # Record metrics
                from .persona_metrics import get_persona_metrics_collector
                collector = get_persona_metrics_collector()
                collector.record_workflow_stage(
                    workflow=self.workflow_name,
                    stage=stage_name,
                    persona=persona,
                    duration_seconds=duration,
                    quality_gate_passed=True  # Could check result
                )
                
                return result

            except Exception as e:
                duration = time.time() - start_time
                span.set_attribute("stage.duration_seconds", duration)
                span.set_attribute("stage.success", False)
                span.set_attribute("stage.error", str(e))
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.record_exception(e)
                
                # Record failure metrics
                from .persona_metrics import get_persona_metrics_collector
                collector = get_persona_metrics_collector()
                collector.record_workflow_stage(
                    workflow=self.workflow_name,
                    stage=stage_name,
                    persona=persona,
                    duration_seconds=duration,
                    quality_gate_passed=False
                )
                
                raise
```

**Update Multi-Persona Workflows:**

```python
# File: .hypertool/workflows/package_release_instrumented.py

from ..instrumentation.workflow_tracing import WorkflowTracer
from ..instrumentation.persona_metrics import get_persona_metrics_collector

async def package_release_workflow(version: str, changelog: str):
    """Package release workflow with full observability."""
    
    async with WorkflowTracer("package_release") as tracer:
        # Stage 1: Backend Engineer
        result1 = await tracer.trace_stage(
            stage_name="version_bump",
            persona="backend-engineer",
            func=backend_version_bump,
            version=version,
            changelog=changelog
        )
        
        # Stage 2: Testing Specialist
        result2 = await tracer.trace_stage(
            stage_name="quality_validation",
            persona="testing-specialist",
            func=testing_validation,
            release_data=result1
        )
        
        # Stage 3: DevOps Engineer
        result3 = await tracer.trace_stage(
            stage_name="publish_deploy",
            persona="devops-engineer",
            func=devops_publish,
            validated_release=result2
        )
        
        return result3
```

### Week 2: Langfuse Integration (8-12 hours)

#### Day 1-2: Langfuse SDK Setup

**Install and Configure:**

```bash
# Install Langfuse SDK
uv add langfuse

# Set environment variables
export LANGFUSE_PUBLIC_KEY="pk-lf-..."
export LANGFUSE_SECRET_KEY="sk-lf-..."
export LANGFUSE_HOST="https://cloud.langfuse.com"  # or self-hosted
```

**Create LangfuseIntegration:**

```python
# File: .hypertool/instrumentation/langfuse_integration.py

from langfuse import Langfuse
from langfuse.decorators import observe, langfuse_context
from typing import Any, Dict, Optional
import os

# Initialize Langfuse client
langfuse = Langfuse(
    public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
    secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
    host=os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")
)


class LangfuseIntegration:
    """Integrate Hypertool with Langfuse for LLM observability."""

    def __init__(self):
        self.langfuse = langfuse

    @observe()  # Langfuse decorator for automatic tracing
    async def trace_llm_call(
        self,
        persona: str,
        chatmode: str,
        model: str,
        prompt: str,
        response: str,
        tokens_used: int,
        cost_usd: float,
        latency_ms: float,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Trace LLM call with Langfuse.
        
        Captures:
        - Input/output
        - Model and persona
        - Token usage and cost
        - Latency
        - Custom metadata
        """
        # Langfuse automatically captures this via @observe decorator
        # We just need to pass metadata
        langfuse_context.update_current_trace(
            name=f"{persona}_{chatmode}_llm_call",
            user_id=persona,  # Treat persona as user for analytics
            session_id=chatmode,  # Session = chatmode
            metadata={
                "persona": persona,
                "chatmode": chatmode,
                "model": model,
                "tokens_used": tokens_used,
                "cost_usd": cost_usd,
                "latency_ms": latency_ms,
                **(metadata or {})
            }
        )

        # Also record tokens in Langfuse
        langfuse_context.update_current_observation(
            usage={
                "total": tokens_used,
                "unit": "TOKENS"
            },
            cost_details={
                "total": cost_usd,
                "currency": "USD"
            }
        )

    @observe(as_type="generation")  # Mark as LLM generation
    async def trace_persona_generation(
        self,
        persona: str,
        task_type: str,
        input_context: Dict[str, Any],
        output: Dict[str, Any],
        quality_score: Optional[float] = None
    ) -> None:
        """
        Trace persona-specific generation task.
        
        Examples:
        - Backend: Code generation
        - Frontend: Component generation
        - Testing: Test case generation
        """
        langfuse_context.update_current_observation(
            name=f"{persona}_{task_type}",
            metadata={
                "persona": persona,
                "task_type": task_type,
                "quality_score": quality_score
            },
            input=input_context,
            output=output
        )

        if quality_score:
            langfuse_context.score_current_observation(
                name="quality",
                value=quality_score,
                comment=f"Automated quality score for {task_type}"
            )

    def create_dataset(
        self,
        name: str,
        description: str,
        items: list[Dict[str, Any]]
    ) -> str:
        """
        Create Langfuse dataset for evaluation.
        
        Example: Test dataset for persona prompt engineering
        """
        dataset = self.langfuse.create_dataset(
            name=name,
            description=description
        )

        for item in items:
            self.langfuse.create_dataset_item(
                dataset_name=name,
                input=item["input"],
                expected_output=item["expected_output"],
                metadata=item.get("metadata", {})
            )

        return dataset.id

    def flush(self):
        """Flush Langfuse events (call at shutdown)."""
        self.langfuse.flush()


# Global instance
_langfuse_integration = LangfuseIntegration()

def get_langfuse() -> LangfuseIntegration:
    """Get global Langfuse integration."""
    return _langfuse_integration
```

#### Day 3-4: Wrap LLM Calls

**Create LLM Wrapper:**

```python
# File: .hypertool/instrumentation/llm_wrapper.py

from typing import Any, Dict, Optional
import time
from .langfuse_integration import get_langfuse
from .persona_metrics import get_persona_metrics_collector

class ObservableLLM:
    """
    Wrapper for LLM calls with Langfuse and Prometheus tracking.
    
    Usage:
        llm = ObservableLLM(persona="backend-engineer", chatmode="code-generation")
        response = await llm.generate(prompt="Generate FastAPI endpoint")
    """

    def __init__(
        self,
        persona: str,
        chatmode: str,
        model: str = "gpt-4",
        cost_per_1k_tokens: float = 0.03  # Default GPT-4 pricing
    ):
        self.persona = persona
        self.chatmode = chatmode
        self.model = model
        self.cost_per_1k_tokens = cost_per_1k_tokens
        
        self.langfuse = get_langfuse()
        self.metrics = get_persona_metrics_collector()

    async def generate(
        self,
        prompt: str,
        system_message: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate LLM response with full observability.
        
        Returns:
            {
                "response": str,
                "tokens_used": int,
                "cost_usd": float,
                "latency_ms": float
            }
        """
        start_time = time.time()

        # TODO: Replace with actual LLM call (OpenAI, Anthropic, etc.)
        # This is a placeholder
        response_text = f"[LLM Response to: {prompt[:50]}...]"
        tokens_used = 150  # Placeholder

        latency_ms = (time.time() - start_time) * 1000
        cost_usd = (tokens_used / 1000) * self.cost_per_1k_tokens

        # Record in Langfuse
        await self.langfuse.trace_llm_call(
            persona=self.persona,
            chatmode=self.chatmode,
            model=self.model,
            prompt=prompt,
            response=response_text,
            tokens_used=tokens_used,
            cost_usd=cost_usd,
            latency_ms=latency_ms,
            metadata=metadata
        )

        # Record in Prometheus
        self.metrics.record_token_usage(
            persona=self.persona,
            chatmode=self.chatmode,
            model=self.model,
            tokens=tokens_used
        )

        return {
            "response": response_text,
            "tokens_used": tokens_used,
            "cost_usd": cost_usd,
            "latency_ms": latency_ms
        }
```

### Week 3: Grafana Dashboards & Alerts (6-8 hours)

#### Day 1-2: Create Dashboards

**Persona Overview Dashboard:**

```json
// File: .hypertool/dashboards/persona_overview.json

{
  "dashboard": {
    "title": "Hypertool - Persona Overview",
    "panels": [
      {
        "title": "Persona Switches (Last 24h)",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(hypertool_persona_switches_total[5m])",
            "legendFormat": "{{from_persona}} → {{to_persona}}"
          }
        ]
      },
      {
        "title": "Token Usage by Persona",
        "type": "piechart",
        "targets": [
          {
            "expr": "sum by (persona) (hypertool_persona_tokens_used_total)"
          }
        ]
      },
      {
        "title": "Average Session Duration",
        "type": "stat",
        "targets": [
          {
            "expr": "avg(hypertool_persona_duration_seconds)"
          }
        ]
      },
      {
        "title": "Top Chatmodes",
        "type": "table",
        "targets": [
          {
            "expr": "topk(10, sum by (chatmode) (hypertool_persona_switches_total))"
          }
        ]
      }
    ]
  }
}
```

**Workflow Performance Dashboard:**

```json
// File: .hypertool/dashboards/workflow_performance.json

{
  "dashboard": {
    "title": "Hypertool - Workflow Performance",
    "panels": [
      {
        "title": "Workflow Execution Time",
        "type": "heatmap",
        "targets": [
          {
            "expr": "rate(hypertool_workflow_stage_duration_seconds_bucket[5m])",
            "legendFormat": "{{workflow}}"
          }
        ]
      },
      {
        "title": "Quality Gate Pass Rate",
        "type": "gauge",
        "targets": [
          {
            "expr": "sum(rate(hypertool_workflow_quality_gate_total{result='passed'}[5m])) / sum(rate(hypertool_workflow_quality_gate_total[5m]))"
          }
        ],
        "thresholds": {
          "mode": "absolute",
          "steps": [
            { "value": 0, "color": "red" },
            { "value": 0.8, "color": "yellow" },
            { "value": 0.95, "color": "green" }
          ]
        }
      },
      {
        "title": "Stage Duration by Persona",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(hypertool_workflow_stage_duration_seconds_bucket[5m]))",
            "legendFormat": "{{persona}} - {{stage}}"
          }
        ]
      }
    ]
  }
}
```

#### Day 3: Configure Alerts

**Prometheus Alert Rules:**

```yaml
# File: .hypertool/alerts/persona_alerts.yml

groups:
  - name: hypertool_persona
    interval: 30s
    rules:
      - alert: PersonaTokenBudgetExceeded
        expr: hypertool_persona_token_budget_remaining < 0
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Persona {{ $labels.persona }} exceeded token budget"
          description: "Token budget remaining is {{ $value }}"

      - alert: HighPersonaSwitchRate
        expr: rate(hypertool_persona_switches_total[5m]) > 10
        for: 10m
        labels:
          severity: info
        annotations:
          summary: "High persona switching rate detected"
          description: "{{ $value }} switches/sec in last 5 minutes"

      - alert: WorkflowQualityGateFailure
        expr: |
          sum by (workflow, stage) (rate(hypertool_workflow_quality_gate_total{result="failed"}[5m]))
          /
          sum by (workflow, stage) (rate(hypertool_workflow_quality_gate_total[5m]))
          > 0.2
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High quality gate failure rate for {{ $labels.workflow }}/{{ $labels.stage }}"
          description: "{{ $value | humanizePercentage }} of quality gates failing"

      - alert: WorkflowStageSlow
        expr: |
          histogram_quantile(0.95,
            rate(hypertool_workflow_stage_duration_seconds_bucket[10m])
          ) > 300
        for: 15m
        labels:
          severity: warning
        annotations:
          summary: "Workflow stage {{ $labels.stage }} is slow"
          description: "P95 latency is {{ $value }}s (threshold: 300s)"
```

---

## 🔗 Langfuse Integration Benefits

### 1. LLM Call Visibility

**Every LLM call captured:**
- Prompt and response (with PII masking if needed)
- Token usage and cost
- Latency
- Model and persona context

**Langfuse UI shows:**
- Timeline of LLM calls
- Cost breakdown by persona
- Token efficiency trends
- Slow queries

### 2. Persona-as-User Analytics

**Treat each persona as a "user" in Langfuse:**
- `user_id` = persona name (e.g., "backend-engineer")
- `session_id` = chatmode name (e.g., "code-generation")
- `tags` = workflow name, stage

**Benefits:**
- Compare persona efficiency
- Identify high-cost personas
- Optimize prompts per persona

### 3. Prompt Management

**Langfuse Prompt Management:**
- Version control prompts
- A/B test prompt variations
- Deploy prompts via API
- Track performance per version

**Example:**

```python
# Fetch prompt from Langfuse
from langfuse import Langfuse
langfuse = Langfuse()

# Get latest prompt for persona
prompt = langfuse.get_prompt("backend-code-generation", label="production")

# Use in LLM call
llm = ObservableLLM(persona="backend-engineer")
response = await llm.generate(prompt=prompt.compile(task="Create FastAPI endpoint"))
```

### 4. Evaluation & Datasets

**Create evaluation datasets:**
- Test persona prompts
- Validate quality scores
- Compare prompt versions

**Example:**

```python
# Create test dataset
langfuse = get_langfuse()
dataset_id = langfuse.create_dataset(
    name="backend_code_generation_tests",
    description="Test cases for backend engineer persona",
    items=[
        {
            "input": {"task": "Create CRUD endpoint"},
            "expected_output": {"quality_score": 0.9},
            "metadata": {"persona": "backend-engineer"}
        }
    ]
)

# Run evaluations
for item in dataset.items:
    result = await backend_persona.execute(item.input)
    score = evaluate_quality(result, item.expected_output)
    langfuse.score(item.id, score)
```

### 5. Cost Optimization

**Langfuse cost analytics:**
- Total spend per persona
- Cost per workflow
- Expensive prompts
- Token efficiency trends

**Grafana + Langfuse:**
- Prometheus tracks real-time tokens
- Langfuse stores historical data
- Export Langfuse data to Prometheus for unified dashboards

---

## 📈 Metrics Catalog

### Persona Metrics

| Metric | Type | Description | Labels |
|--------|------|-------------|--------|
| `hypertool_persona_switches_total` | Counter | Total persona switches | `from_persona`, `to_persona`, `chatmode` |
| `hypertool_persona_duration_seconds` | Histogram | Time spent in persona | `persona`, `chatmode` |
| `hypertool_persona_tokens_used_total` | Counter | Tokens consumed | `persona`, `chatmode`, `model` |
| `hypertool_persona_token_budget_remaining` | Gauge | Remaining token budget | `persona` |

### Workflow Metrics

| Metric | Type | Description | Labels |
|--------|------|-------------|--------|
| `hypertool_workflow_stage_duration_seconds` | Histogram | Stage execution time | `workflow`, `stage`, `persona` |
| `hypertool_workflow_quality_gate_total` | Counter | Quality gate results | `workflow`, `stage`, `result` |

### LLM Metrics (via Langfuse)

| Metric | Source | Description |
|--------|--------|-------------|
| Total cost | Langfuse | Aggregated LLM spend |
| Tokens per persona | Langfuse | Token usage by persona |
| P95 latency | Langfuse | 95th percentile response time |
| Quality scores | Langfuse | User feedback and evaluations |

---

## 🚀 Getting Started

### 1. Install Dependencies

```bash
# Install observability packages
uv add opentelemetry-api opentelemetry-sdk
uv add opentelemetry-exporter-prometheus
uv add prometheus-client
uv add langfuse

# Optional: Grafana setup
docker-compose -f docker-compose.observability.yml up -d
```

### 2. Initialize APM

```python
# File: .hypertool/init_apm.py

from observability_integration import initialize_observability
from .instrumentation.langfuse_integration import get_langfuse

def init_hypertool_apm():
    """Initialize APM for Hypertool."""
    # Start OpenTelemetry + Prometheus
    initialize_observability(
        service_name="hypertool-persona-system",
        enable_prometheus=True,
        prometheus_port=9464
    )

    # Verify Langfuse connection
    langfuse = get_langfuse()
    print("✅ Langfuse initialized")
    print(f"   Host: {langfuse.langfuse.base_url}")

if __name__ == "__main__":
    init_hypertool_apm()
```

### 3. Run Instrumented Workflow

```python
# Example: Package release with observability
from .hypertool.workflows.package_release_instrumented import package_release_workflow

async def main():
    result = await package_release_workflow(
        version="0.3.0",
        changelog="Added APM integration"
    )
    print(f"✅ Release complete: {result}")

# Metrics now available at http://localhost:9464/metrics
# Traces visible in Langfuse UI
```

---

## 📊 Success Metrics

### Technical Metrics

- ✅ **Persona switches tracked**: 100% coverage
- ✅ **Workflow tracing**: <1s overhead per workflow
- ✅ **LLM call coverage**: 100% (all calls in Langfuse)
- ✅ **Dashboard uptime**: 99.9%
- ✅ **Alert latency**: <1 minute

### Business Metrics

- 📈 **Time savings**: 10-20% reduction in debugging time
- 📉 **Cost reduction**: 15-25% via prompt optimization
- 🎯 **Quality improvement**: 90%+ quality gate pass rate
- ⚡ **MTTR**: <30 minutes for persona-related issues

---

## 🔮 Future Enhancements

### Phase 6: Adaptive Persona Switching

**Automatic persona selection based on:**
- Task analysis (code vs docs vs deploy)
- Historical performance (which persona works best)
- Token budget remaining
- Quality score trends

**Implementation:**
- Use Langfuse evaluation data
- Train lightweight classifier
- Integrate with AdaptivePrimitive pattern

### Advanced Analytics

- **Persona efficiency matrix** - Which persona excels at which tasks
- **Workflow optimization** - Identify bottleneck stages
- **Cost forecasting** - Predict token usage
- **Quality trends** - Track improvement over time

---

## 📝 Documentation Deliverables

1. ✅ **This implementation plan** - Complete technical design
2. ⬜ **Instrumentation code** - PersonaMetricsCollector, WorkflowTracer, LangfuseIntegration
3. ⬜ **Grafana dashboards** - Persona Overview, Workflow Performance
4. ⬜ **Alert rules** - Token budget, quality gates, slow workflows
5. ⬜ **User guide** - How to use Langfuse for prompt optimization
6. ⬜ **Runbook** - Troubleshooting common observability issues

---

## 🎯 Next Steps

### Immediate (This Week)

1. **Create instrumentation directory structure**
2. **Implement PersonaMetricsCollector**
3. **Add metrics to tta-persona CLI**
4. **Test metrics collection locally**

### Short-Term (2-3 Weeks)

1. **Implement WorkflowTracer**
2. **Integrate Langfuse SDK**
3. **Update 3 multi-persona workflows**
4. **Create Grafana dashboards**

### Long-Term (1-2 Months)

1. **Production deployment**
2. **Alert tuning based on real data**
3. **Prompt optimization with Langfuse**
4. **Adaptive persona switching (Phase 6)**

---

**Status:** 🚧 Planning Complete, Ready for Implementation  
**Next Phase:** Phase 6 - Adaptive System (auto persona switching)  
**Owner:** TTA.dev Team  
**Last Updated:** 2025-11-15
