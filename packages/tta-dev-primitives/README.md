# TTA Development Primitives

Production-ready development primitives for building TTA agents and workflows. This package provides composable patterns, recovery strategies, performance utilities, and observability tools for development automation.

**Note**: These are development tools for building TTA, not player-facing game components.

## Features

### 🔧 Core Workflow Primitives
- **Sequential**: Execute operations in sequence with context passing
- **Parallel**: Execute operations concurrently with result aggregation
- **Conditional**: Branch execution based on runtime conditions
- **Router**: Dynamic routing with cost optimization and tier-based selection

### 🔄 Recovery & Resilience
- **Retry**: Exponential backoff with jitter and configurable policies
- **Fallback**: Graceful degradation with fallback strategies
- **Timeout**: Circuit breaker pattern with timeout enforcement
- **Compensation**: Saga pattern for distributed transaction rollback

### ⚡ Performance
- **LRU Cache**: Least-recently-used cache with TTL and eviction policies
- **Context-aware caching**: Intelligent caching for LLM responses

### 📊 Observability
- **Structured Logging**: Context-aware logging with correlation IDs
- **Metrics**: Performance tracking and monitoring
- **Tracing**: OpenTelemetry integration for distributed tracing

### 🧪 Testing Utilities
- **Mock Primitives**: Test doubles for workflow testing
- **Async Testing**: Full async/await support

### 📦 APM Integration
- **Agent Package Manager**: MCP-compatible package metadata
- **Instrumentation**: Automatic performance monitoring

## Installation

```bash
# Install from local package
uv pip install -e packages/tta-dev-primitives

# Install with all extras
uv pip install -e "packages/tta-dev-primitives[dev,tracing,apm]"
```

## Quick Start

### Workflow Composition

```python
from tta_dev_primitives import Sequential, Parallel, Router, WorkflowPrimitive

# Sequential workflow
workflow = Sequential([
    load_data,
    process_data,
    save_results
])
result = await workflow.execute({"input": "data"})

# Parallel execution
parallel = Parallel([
    fetch_user_data,
    fetch_analytics,
    fetch_recommendations
])
results = await parallel.execute({"user_id": 123})

# Dynamic routing with cost optimization
router = Router({
    "fast": gpt4_mini,
    "balanced": gpt4,
    "quality": gpt4_turbo
})
response = await router.execute({"tier": "balanced", "prompt": "..."})
```

### Recovery Patterns

```python
from tta_dev_primitives import Retry, Fallback, Timeout, Saga

# Retry with exponential backoff
@Retry(max_attempts=3, backoff_factor=2.0)
async def flaky_api_call():
    return await external_api.fetch()

# Fallback strategy
workflow = Fallback(
    primary=expensive_model,
    fallback=cheap_model
)

# Timeout enforcement
@Timeout(seconds=5.0)
async def long_running_task():
    return await process_data()

# Saga compensation pattern
saga = Saga()
saga.add_step(create_user, rollback=delete_user)
saga.add_step(send_email, rollback=send_cancellation)
await saga.execute({"user_data": {...}})
```

### Performance Optimization

```python
from tta_dev_primitives import cached

# LRU cache with TTL
@cached(max_size=1000, ttl=3600)
async def expensive_computation(input_data: str) -> dict:
    # Expensive operation here
    return result

# Check cache stats
stats = expensive_computation.cache_stats()
print(f"Hit rate: {stats.hit_rate:.2%}")
```

### Observability

```python
from tta_dev_primitives import get_logger, track_metrics, trace_operation

# Structured logging
logger = get_logger(__name__)
logger.info("Processing request", user_id=123, request_id="abc")

# Metrics tracking
@track_metrics(name="api_latency")
async def api_call():
    return await external_service.call()

# Distributed tracing
@trace_operation(span_name="data_processing")
async def process_pipeline(data):
    # Automatic span creation and context propagation
    return await transform(data)
```

## Package Structure

```
tta-dev-primitives/
├── src/tta_dev_primitives/
│   ├── core/              # Workflow primitives
│   │   ├── base.py        # Base classes and context
│   │   ├── sequential.py  # Sequential execution
│   │   ├── parallel.py    # Parallel execution
│   │   ├── conditional.py # Conditional branching
│   │   └── routing.py     # Dynamic routing
│   ├── recovery/          # Recovery patterns
│   │   ├── retry.py       # Retry logic
│   │   ├── fallback.py    # Fallback strategies
│   │   ├── timeout.py     # Timeout enforcement
│   │   └── compensation.py # Saga pattern
│   ├── performance/       # Performance utilities
│   │   └── cache.py       # LRU cache with TTL
│   ├── observability/     # Observability tools
│   │   ├── logging.py     # Structured logging
│   │   ├── metrics.py     # Metrics tracking
│   │   └── tracing.py     # Distributed tracing
│   ├── testing/           # Testing utilities
│   │   └── mocks.py       # Mock primitives
│   └── apm/               # APM integration
│       ├── decorators.py  # APM decorators
│       ├── instrumented.py # Instrumented primitives
│       └── setup.py       # APM setup
├── tests/                 # 35 comprehensive tests
├── examples/              # Usage examples
├── pyproject.toml         # Package configuration
└── apm.yml                # APM metadata
```

## Testing

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=src --cov-report=html

# Run specific test module
uv run pytest tests/test_cache.py -v
```

## Quality Metrics

- ✅ 35/35 tests passing (100%)
- ✅ Core primitives: 88-100% coverage
- ✅ Type-safe with Pydantic v2
- ✅ Full async/await support
- ✅ Production-tested in TTA

## Development

```bash
# Install development dependencies
uv sync --all-extras

# Format code
uv run ruff format .

# Lint code
uv run ruff check . --fix

# Type check
uv run mypy src/
```

## APM Integration

This package includes Agent Package Manager (APM) metadata for MCP compatibility:

```yaml
# apm.yml
name: tta-dev-primitives
version: 0.1.0
type: library
category: development-tools
```

## License

Proprietary - TTA Storytelling Platform

## Related Packages

- `tta-ai-framework`: AI components for TTA (separate - for game components)
- `tta-narrative-engine`: Narrative generation (separate - for game components)

This package is specifically for **development automation**, not player-facing features.
