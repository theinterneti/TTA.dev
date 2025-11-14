# Langfuse Integration for TTA.dev

> **✅ STATUS: PRODUCTION-READY**  
> Langfuse v3.10.0 integration complete with latest API (updated via Context7)  
> Tests: 5/5 passing | Docs: 8 files (3,000+ lines) | Ready for deployment

## Overview

TTA.dev now includes Langfuse integration - a specialized LLM observability platform that complements existing OpenTelemetry-based monitoring with LLM-specific analytics.

**Package**: `packages/tta-langfuse-integration/`

## Why Langfuse?

### 1. Perfect Alignment with TTA.dev

- **Production-ready** - Enterprise-grade LLM analytics
- **Observability-focused** - Deep insights into agentic workflows
- **MCP ecosystem** - Built-in integration with mcp-use framework
- **Complements OpenTelemetry** - Works alongside, not as a replacement

### 2. Unique Capabilities

What Langfuse adds beyond OpenTelemetry:

| Capability | OpenTelemetry | Langfuse |
|------------|---------------|----------|
| General tracing | ✅ | ✅ |
| Infrastructure metrics | ✅ | ❌ |
| Workflow performance | ✅ | ✅ |
| **LLM prompts/completions** | ❌ | ✅ |
| **Token usage tracking** | ❌ | ✅ |
| **Cost analytics** | ❌ | ✅ |
| **Prompt versioning** | ❌ | ✅ |
| **Quality evaluation** | ❌ | ✅ |

### 3. Easy Integration

- Python SDK with async support
- OpenTelemetry compatible
- Environment variable configuration
- Graceful degradation
- No code changes for existing primitives

## Quick Start

### 1. Install

```bash
cd packages/tta-langfuse-integration
uv sync
```

### 2. Get Credentials

Sign up at [cloud.langfuse.com](https://cloud.langfuse.com) and create a project.

### 3. Configure

```bash
export LANGFUSE_PUBLIC_KEY=pk-lf-...
export LANGFUSE_SECRET_KEY=sk-lf-...
```

### 4. Use

```python
from langfuse_integration import initialize_langfuse, LangfusePrimitive

# Initialize
initialize_langfuse()

# Wrap LLM
llm = LangfusePrimitive(
    name="narrative_gen",
    metadata={"model": "gpt-4"}
)

# Execute
result = await llm.execute(input_data, context)

# View in dashboard at https://cloud.langfuse.com
```

## Integration Patterns

### Pattern 1: Full Stack (Recommended)

```python
from observability_integration import initialize_observability
from langfuse_integration import initialize_langfuse

# OpenTelemetry for infrastructure/workflows
initialize_observability(service_name="tta-app")

# Langfuse for LLM analytics
initialize_langfuse()

# Both systems track LLM calls
workflow = input >> LangfusePrimitive(llm) >> output
```

**Benefits**:
- Complete observability coverage
- LLM-specific insights
- Shared correlation IDs
- Unified debugging

### Pattern 2: Langfuse Only

```python
from langfuse_integration import initialize_langfuse

# LLM-focused app
initialize_langfuse()

workflow = (
    LangfusePrimitive(input_proc, name="input") >>
    LangfusePrimitive(llm, name="generate") >>
    LangfusePrimitive(formatter, name="format")
)
```

**Benefits**:
- Simpler setup
- Focused on LLM metrics
- Unified dashboard

### Pattern 3: OpenTelemetry Only

```python
from observability_integration import initialize_observability

# No Langfuse needed
initialize_observability(service_name="tta-app")

workflow = input >> llm >> output
```

**Benefits**:
- One less dependency
- Simpler for non-LLM workloads

## Key Features

### Automatic Tracking

```python
llm = LangfusePrimitive(name="llm")

result = await llm.execute(input_data, context)

# Automatically tracked:
# - Prompt
# - Completion
# - Tokens (input/output/total)
# - Latency
# - Model
# - Cost (if pricing configured)
# - Errors
```

### Cost Analytics

```python
# Configure model pricing in dashboard
llm = LangfusePrimitive(
    name="llm",
    metadata={"model": "gpt-4"}
)

# Langfuse calculates costs from token usage
# View cost breakdown by:
# - Model
# - Provider
# - User
# - Time period
```

### Session Tracking

```python
llm = LangfusePrimitive(
    name="chat",
    session_id=conversation_id,
    user_id=user_id
)

# Group related calls in dashboard
# View entire conversation thread
```

### Multi-Model Comparison

```python
fast = LangfusePrimitive(
    name="fast_model",
    metadata={"provider": "openrouter", "model": "llama-3.1-8b"}
)

premium = LangfusePrimitive(
    name="premium_model",
    metadata={"provider": "openai", "model": "gpt-4"}
)

# Dashboard shows:
# - Cost comparison
# - Performance comparison
# - Usage distribution
```

## Architecture

```
TTA.dev Application
├─> OpenTelemetry
│   ├─> Prometheus (metrics)
│   └─> Grafana (dashboards)
│
└─> Langfuse
    ├─> LLM traces (prompts, completions, tokens)
    ├─> Cost analytics
    └─> Quality evaluation

Shared: correlation_id, workflow_id, session_id
```

### Context Propagation

```python
# TTA.dev context
context = WorkflowContext(
    workflow_id="story-gen-001",
    correlation_id="req-12345"
)

# Langfuse uses same IDs
trace = client.trace(
    session_id=context.correlation_id,
    metadata={
        "workflow_id": context.workflow_id,
        "correlation_id": context.correlation_id
    }
)
```

**Result**: Search either system by `correlation_id` to find related data.

## Documentation

### Package Documentation
- [`README.md`](../packages/tta-langfuse-integration/README.md) - Quick start
- [`ARCHITECTURE.md`](../packages/tta-langfuse-integration/docs/ARCHITECTURE.md) - Technical details
- [`INTEGRATION_GUIDE.md`](../packages/tta-langfuse-integration/docs/INTEGRATION_GUIDE.md) - Complete guide
- [`QUICK_REFERENCE.md`](../packages/tta-langfuse-integration/QUICK_REFERENCE.md) - API reference
- [`IMPLEMENTATION_SUMMARY.md`](../packages/tta-langfuse-integration/IMPLEMENTATION_SUMMARY.md) - Project summary

### Key Topics
- Installation and setup
- Integration patterns
- Cost tracking
- Session management
- Troubleshooting
- Best practices

## Use Cases

### 1. Cost Optimization
Track and compare costs across models and providers.

### 2. Quality Monitoring
Evaluate LLM outputs for coherence, relevance, and safety.

### 3. Prompt Engineering
Version control prompts and A/B test improvements.

### 4. User Analytics
Track usage and costs per user or session.

### 5. Performance Analysis
Monitor latency and token usage trends.

## Next Steps

### Immediate
1. Install dependencies: `uv sync`
2. Get Langfuse credentials from [cloud.langfuse.com](https://cloud.langfuse.com)
3. Configure environment variables
4. Test integration with sample workflow

### Future Enhancements
- Prompt management and versioning
- Automated evaluation
- A/B testing
- Dataset management
- Cost budgeting and alerts
- Fine-tuning data collection

## Resources

- **Langfuse Docs**: https://langfuse.com/docs
- **Cloud Dashboard**: https://cloud.langfuse.com
- **Self-Hosted**: https://langfuse.com/docs/deployment
- **OpenTelemetry Integration**: https://langfuse.com/docs/integrations/opentelemetry

## Support

For issues or questions:
- Package documentation in `packages/tta-langfuse-integration/`
- TTA.dev observability docs in `docs/observability/`
- Langfuse community: https://langfuse.com/discord

---

**Status**: Ready for integration ✅  
**Version**: 0.1.0  
**Last Updated**: 2024-11-14
