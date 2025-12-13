# TTA-Dev-Primitives Examples

This directory contains practical examples demonstrating how to use the tta-dev-primitives package to build robust AI application workflows.

## 🆕 New Examples (Phase 3)

Phase 3 examples have been updated to align with the current `InstrumentedPrimitive` patterns and observability changes. The following examples are functional and tested in this branch:

- `rag_workflow.py` — Basic RAG example (retrieval + LLM generation)
- `agentic_rag_workflow.py` — Production-grade agentic RAG (routing, grading, hallucination checks)
- `cost_tracking_workflow.py` — Cost tracking and budget enforcement
- `streaming_workflow.py` — Token-by-token streaming with metrics and aggregation

`multi_agent_workflow.py` is being recreated to follow the same pattern and will be available shortly.

### RAG (Retrieval-Augmented Generation) - `rag_workflow.py` ✅
Demonstrates a working RAG workflow: vector retrieval (simulated), context augmentation, and LLM generation with caching and fallback.

Features:
- Vector DB retrieval (simulated)
- Context augmentation with relevance scoring
- LLM generation with fallback
- Cost optimization through caching
- Source attribution

**Run it:**
```bash
cd packages/tta-dev-primitives
uv run python examples/rag_workflow.py
```

### Agentic RAG (Production) - `agentic_rag_workflow.py` ✅
Production-grade agentic RAG implementation based on the NVIDIA agentic pattern. This example demonstrates a 6-stage pipeline with routing, retrieval, document grading, answer generation, answer grading, and hallucination checking.

Features:
- Dynamic routing (vectorstore vs web search)
- Cached vectorstore retrieval with fallback to web search
- Document and answer grading for quality control
- Hallucination detection (source grounding)
- Retry and iterative refinement

**Run it:**
```bash
cd packages/tta-dev-primitives
uv run python examples/agentic_rag_workflow.py
```

### Multi-Agent Coordination - `multi_agent_workflow.py`
**Multi-agent coordination pattern** with task decomposition and parallel execution.

Features:
- Coordinator agent decomposes tasks
- Specialist agents execute in parallel
- Result aggregation and synthesis
- Timeout protection per agent
- Type-safe agent composition

**Run it:**
```bash
cd packages/tta-dev-primitives
uv run python examples/multi_agent_workflow.py
```

### Cost Tracking - `cost_tracking_workflow.py`
**Cost tracking and budget enforcement** with detailed metrics and attribution.

Features:
- Token usage tracking per model
- Cost calculation based on pricing
- Budget enforcement (per-request and daily)
- Cost attribution by user and workflow
- Real-time cost reporting

**Run it:**
```bash
cd packages/tta-dev-primitives
uv run python examples/cost_tracking_workflow.py
```

### Streaming LLM - `streaming_workflow.py`
**Streaming LLM responses** with token-by-token delivery and performance metrics.

Features:
- Token-by-token streaming (SSE pattern)
- Stream buffering for smooth delivery
- Performance metrics tracking
- Stream aggregation
- Cancellation support

**Run it:**
```bash
cd packages/tta-dev-primitives
uv run python examples/streaming_workflow.py
```

---

## Core Examples

### 1. `quick_wins_demo.py`
**Quick start demonstration** showing basic primitive usage and composition.

Topics covered:
- Basic primitive creation
- Sequential composition
- Parallel execution
- Simple caching

**Run it:**
```bash
cd packages/tta-dev-primitives
uv run python examples/quick_wins_demo.py
```

### 2. `real_world_workflows.py`
**Production-ready workflow patterns** for common AI application scenarios.

Examples included:
- **Customer Support Chatbot**: Multi-tier routing with caching and fallback
- **Content Generation Pipeline**: Parallel analysis and sequential processing
- **Data Processing Pipeline**: Conditional branching based on data type
- **LLM Chain**: Complete LLM workflow with caching and tier-based routing

**Run it:**
```bash
cd packages/tta-dev-primitives
uv run python examples/real_world_workflows.py
```

### 3. `error_handling_patterns.py`
**Robust error handling strategies** using recovery primitives.

Examples included:
- **Retry with Exponential Backoff**: Handle transient failures
- **Fallback Chain**: Multiple levels of fallback
- **Timeout Protection**: Prevent hanging operations
- **Combined Strategies**: Retry + timeout + fallback
- **API Integration**: Real-world external API integration pattern

**Run it:**
```bash
cd packages/tta-dev-primitives
uv run python examples/error_handling_patterns.py
```

### 4. `apm_example.py`
**Agent Package Manager (APM) integration** showing how to use MCP-compatible package metadata.

Topics covered:
- APM configuration
- Instrumentation
- Performance monitoring

**Run it:**
```bash
cd packages/tta-dev-primitives
uv run python examples/apm_example.py
```

### 5. `observability_demo.py` ⭐ NEW
**Comprehensive observability platform demonstration** showcasing production-ready monitoring and metrics.

This demo proves that the TTA.dev observability platform (Phases 1-3) is production-ready and provides real value for monitoring AI workflows.

Topics covered:
- **Automatic Metrics Collection**: Via `InstrumentedPrimitive` - no manual instrumentation needed
- **Percentile Latency Tracking**: p50, p90, p95, p99 for performance analysis
- **SLO Compliance Monitoring**: Real-time SLO tracking with error budget calculation
- **Throughput Tracking**: Requests per second and concurrent request monitoring
- **Cost Tracking**: Cost monitoring and savings from cache hits (30-40% typical savings)
- **Prometheus Integration**: Metrics export for Grafana dashboards and AlertManager

**What the demo does:**
1. Creates a realistic multi-step AI workflow with:
   - Fast validation (1-10ms)
   - LLM calls with retry (50-500ms, 5% failure rate)
   - Data processing (10-50ms)
   - Parallel execution
   - Cache wrapper for cost savings
2. Runs 20 initial executions (cache misses)
3. Runs 10 repeated executions (cache hits - demonstrates 33% cache hit rate)
4. Displays comprehensive metrics for each primitive
5. Shows Prometheus integration (if prometheus-client installed)

**Run it:**
```bash
cd packages/tta-dev-primitives
uv run python examples/observability_demo.py
```

**Sample output:**
```
📊 Metrics for: llm_generation
------------------------------------------------------------
  Latency Percentiles:
    p50: 227.90ms
    p90: 463.71ms
    p95: 466.12ms
    p99: 472.14ms

  SLO Status: ✅
    Target: 95.0%
    Availability: 95.24%
    Latency Compliance: 100.00%
    Error Budget Remaining: 100.0%

  Throughput:
    Total Requests: 21
    RPS: 2.27
```

**Next steps after running the demo:**
- View Grafana dashboards: `dashboards/grafana/`
- Configure AlertManager: `dashboards/alertmanager/`
- Install Prometheus client: `uv pip install prometheus-client`
- Integrate with your monitoring stack

## Key Concepts Demonstrated

### Composition Patterns

**Sequential**:
```python
workflow = step1 >> step2 >> step3
```

**Parallel**:
```python
results = ParallelPrimitive([task1, task2, task3])
```

**Conditional**:
```python
conditional = ConditionalPrimitive(
    condition=lambda x, ctx: x["type"] == "important",
    if_true=priority_handler,
    if_false=normal_handler
)
```

### Error Handling

**Retry**:
```python
RetryPrimitive(
    primitive=api_call,
    max_attempts=3,
    backoff_factor=2.0
)
```

**Fallback**:
```python
FallbackPrimitive(
    primary=expensive_service,
    fallback=cheap_service
)
```

**Timeout**:
```python
TimeoutPrimitive(
    primitive=slow_operation,
    timeout_seconds=5.0
)
```

### Performance Optimization

**Caching**:
```python
CachePrimitive(
    ttl=3600,  # 1 hour
    max_size=1000
)
```

**Routing**:
```python
RouterPrimitive(
    routes={
        "fast": fast_model,
        "balanced": balanced_model,
        "quality": quality_model
    }
)
```

## Creating Your Own Workflows

1. **Start Simple**: Begin with `LambdaPrimitive` for quick prototyping
2. **Compose**: Use `>>` operator or `SequentialPrimitive` to chain steps
3. **Add Resilience**: Wrap with `RetryPrimitive`, `TimeoutPrimitive`, `FallbackPrimitive`
4. **Optimize**: Add `CachePrimitive` and `RouterPrimitive` for cost/performance
5. **Monitor**: Use `WorkflowContext` for tracking and observability

## Common Patterns

### LLM Application Workflow
```python
workflow = (
    validate_input >>
    CachePrimitive(ttl=1800) >>
    RouterPrimitive(tier="balanced") >>
    process_response >>
    format_output
)
```

### Resilient API Integration
```python
api_workflow = FallbackPrimitive(
    primary=TimeoutPrimitive(
        primitive=RetryPrimitive(
            primitive=api_call,
            max_attempts=3
        ),
        timeout_seconds=5.0
    ),
    fallback=cached_response
)
```

### Multi-Stage Processing
```python
pipeline = SequentialPrimitive([
    load_data,
    ParallelPrimitive([clean, validate, enrich]),
    transform,
    save_results
])
```

## Testing Your Workflows

All examples include inline assertions and output for verification. To run with pytest:

```bash
cd packages/tta-dev-primitives
uv run pytest examples/ -v
```

## Next Steps

- Review the [main package README](../README.md) for detailed API documentation
- Check the [tests directory](../tests/) for more usage patterns
- Read the [architecture documentation](../../../docs/architecture/Overview.md)
- Explore [coding standards](../../../docs/development/CodingStandards.md)

## Contributing Examples

Have a useful pattern to share? We welcome contributions!

1. Create a new example file following the existing structure
2. Include docstrings explaining the pattern
3. Add inline comments for clarity
4. Update this README with your example
5. Submit a PR

See [CONTRIBUTING.md](../../../CONTRIBUTING.md) for details.


---
**Logseq:** [[TTA.dev/Platform/Primitives/Examples/Readme]]
