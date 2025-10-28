# TTA-Dev-Primitives Examples

This directory contains practical examples demonstrating how to use the tta-dev-primitives package to build robust AI application workflows.

## Examples Overview

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
