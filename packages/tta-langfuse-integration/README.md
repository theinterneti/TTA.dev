# TTA Langfuse Integration

Langfuse integration for TTA.dev - dedicated LLM observability, analytics, and monitoring.

## Overview

Langfuse provides specialized observability for LLM applications that complements TTA.dev's existing OpenTelemetry-based monitoring. While OpenTelemetry provides general distributed tracing and metrics, Langfuse offers LLM-specific capabilities:

- **LLM Call Tracing** - Detailed traces of prompts, completions, tokens, and costs
- **Prompt Management** - Version control and testing for prompts
- **Evaluation** - Automated evaluation of LLM outputs
- **Cost Tracking** - Per-model cost analysis and optimization insights
- **Performance Analytics** - LLM-specific performance metrics and dashboards

## Features

- **Seamless Integration** - Works alongside existing OpenTelemetry tracing
- **LangfusePrimitive** - Wrapper primitive for automatic LLM call tracking
- **Context Propagation** - Integrates with TTA.dev's WorkflowContext
- **Cost Analytics** - Automatic cost calculation per provider and model
- **Evaluation Support** - Built-in support for LLM output evaluation

## Installation

```bash
uv add tta-langfuse-integration
```

## Quick Start

```python
from langfuse_integration import initialize_langfuse
from langfuse_integration.primitives import LangfusePrimitive

# Initialize Langfuse (call early in main.py)
initialize_langfuse(
    public_key="pk-lf-...",
    secret_key="sk-lf-...",
    host="https://cloud.langfuse.com"  # or self-hosted
)

# Wrap LLM calls with Langfuse tracing
llm_call = LangfusePrimitive(
    name="narrative_generation",
    metadata={"type": "story", "model": "gpt-4"}
)

# Use in workflow
workflow = input_processor >> llm_call >> output_formatter
result = await workflow.execute(context, input_data)
```

## Integration with Existing Observability

Langfuse works alongside TTA.dev's existing observability stack:

```python
from observability_integration import initialize_observability
from langfuse_integration import initialize_langfuse

# OpenTelemetry for general tracing/metrics
initialize_observability(
    service_name="tta-app",
    enable_prometheus=True
)

# Langfuse for LLM-specific analytics
initialize_langfuse(
    public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
    secret_key=os.getenv("LANGFUSE_SECRET_KEY")
)
```

**Result:**
- OpenTelemetry tracks overall workflow performance
- Langfuse tracks LLM-specific metrics (tokens, costs, quality)
- Both share correlation IDs for unified debugging

## Use Cases

### 1. Cost Optimization
```python
# Track costs per LLM provider
from langfuse_integration.primitives import LangfusePrimitive

fast_llm = LangfusePrimitive(
    name="fast_model",
    metadata={"provider": "openrouter", "model": "llama-3.1-8b"}
)

premium_llm = LangfusePrimitive(
    name="premium_model", 
    metadata={"provider": "openai", "model": "gpt-4"}
)

# Langfuse dashboard shows cost comparison
```

### 2. Prompt Engineering
```python
# Track prompt versions and performance
llm = LangfusePrimitive(
    name="narrative_gen",
    prompt_version="v2.1"  # Track which prompt version was used
)
```

### 3. Quality Monitoring
```python
# Evaluate LLM outputs
from langfuse_integration.evaluation import evaluate_output

result = await llm.execute(context, input_data)

# Automatic evaluation
score = await evaluate_output(
    result=result,
    criteria=["coherence", "relevance", "safety"]
)
```

## Architecture

```
┌─────────────────────────────────────────────────┐
│           TTA.dev Application                    │
├─────────────────────────────────────────────────┤
│                                                  │
│  ┌──────────────┐      ┌──────────────┐        │
│  │ OpenTelemetry│      │   Langfuse   │        │
│  │   (General)  │      │ (LLM-focused)│        │
│  └──────┬───────┘      └──────┬───────┘        │
│         │                      │                │
│         │  ┌───────────────────┤                │
│         │  │                   │                │
│         ▼  ▼                   ▼                │
│  ┌──────────────┐      ┌──────────────┐        │
│  │  Prometheus  │      │   Langfuse   │        │
│  │   Metrics    │      │   Dashboard  │        │
│  └──────────────┘      └──────────────┘        │
│                                                  │
└─────────────────────────────────────────────────┘
```

## Documentation

- [Integration Guide](docs/INTEGRATION_GUIDE.md) - Detailed integration patterns
- [Architecture](docs/ARCHITECTURE.md) - Technical architecture details
- [Examples](docs/EXAMPLES.md) - Common use cases and patterns

## License

MIT (or as per TTA.dev repository)
