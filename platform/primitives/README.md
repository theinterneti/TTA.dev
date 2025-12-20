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

### Memory Primitives

```python
from tta_dev_primitives.performance import MemoryPrimitive

# Zero-setup mode (works immediately, no Docker/Redis required)
memory = MemoryPrimitive(max_size=100)

# Multi-turn conversation with memory
await memory.add("What is a primitive?", {"role": "user", "timestamp": "..."})
await memory.add("A primitive is a composable workflow component", {"role": "assistant"})

# Retrieve conversation history
response = await memory.get("What is a primitive?")
print(response)  # {"role": "assistant", ...}

# Search across conversation
results = await memory.search("primitive")  # Find all mentions

# Optional: Enable Redis for persistence and scaling
memory_redis = MemoryPrimitive(
    redis_url="redis://localhost:6379",
    max_size=1000,
    enable_redis=True
)

# Same API, enhanced backend - automatic fallback if Redis unavailable
await memory_redis.add(key, value)  # Uses Redis if available, in-memory otherwise
```

**Benefits:**

- ✅ **Zero Setup**: Works immediately without Docker or Redis
- ✅ **Hybrid Architecture**: In-memory fallback + optional Redis enhancement
- ✅ **Graceful Degradation**: Automatic fallback if Redis fails
- ✅ **Same API**: No code changes when upgrading backends
- ✅ **LRU Eviction**: Built-in memory management
- ✅ **Keyword Search**: Find conversation history by content

**Use Cases:**

- Multi-turn conversational agents
- Task context spanning multiple operations
- Agent memory and recall
- Personalization based on interaction history

**Documentation:** See [docs/memory/README.md](docs/memory/README.md) for complete guide.

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

## Production Examples

The `examples/` directory contains **5 validated, production-ready workflows** demonstrating key patterns:

### Quick Links

| Example | Pattern | Features | Use When |
|---------|---------|----------|----------|
| [**rag_workflow.py**](examples/rag_workflow.py) | RAG Pipeline | Caching, Fallback, Retry, Sequential | Building document retrieval systems |
| [**agentic_rag_workflow.py**](examples/agentic_rag_workflow.py) | Agentic RAG | Router, Grading, Validation, Hallucination Detection | Production RAG with quality control |
| [**cost_tracking_workflow.py**](examples/cost_tracking_workflow.py) | Cost Management | Budget Enforcement, Per-Model Tracking | Managing LLM API costs |
| [**streaming_workflow.py**](examples/streaming_workflow.py) | Token Streaming | AsyncIterator, Buffering, Metrics | Real-time response streaming |
| [**multi_agent_workflow.py**](examples/multi_agent_workflow.py) | Multi-Agent | Coordinator, Parallel Specialists, Aggregation | Complex agent orchestration |

### Example Highlights

**Agentic RAG (Production Pattern):**
```python
# Complete RAG pipeline with quality controls
workflow = (
    QueryRouterPrimitive() >>                    # Route simple vs complex
    VectorstoreRetrieverPrimitive() >>           # Cached retrieval
    DocumentGraderPrimitive() >>                 # Filter irrelevant docs
    AnswerGeneratorPrimitive() >>                # Generate response
    AnswerGraderPrimitive() >>                   # Validate quality
    HallucinationGraderPrimitive()               # Detect hallucinations
)
```

**Multi-Agent Coordination:**
```python
# Decompose task and execute with specialist agents
workflow = (
    CoordinatorAgentPrimitive() >>               # Analyze and plan
    ParallelPrimitive([                          # Execute in parallel
        DataAnalystAgentPrimitive(),
        ResearcherAgentPrimitive(),
        FactCheckerAgentPrimitive(),
        SummarizerAgentPrimitive()
    ]) >>
    AggregatorAgentPrimitive()                   # Combine results
)
```

**Cost Tracking:**
```python
# Track and enforce budget across LLM calls
cost_tracker = CostTrackingPrimitive(llm_primitive)
enforcer = BudgetEnforcementPrimitive(
    cost_tracker,
    budget_usd=10.0
)

# Automatic cost reporting
report = await enforcer.get_cost_report()
```

### Implementation Guide

All examples follow the **InstrumentedPrimitive pattern** with:
- ✅ Automatic OpenTelemetry tracing
- ✅ Structured logging with correlation IDs
- ✅ Prometheus metrics
- ✅ Type-safe composition

**Detailed Guide:** See [PHASE3_EXAMPLES_COMPLETE.md](../../PHASE3_EXAMPLES_COMPLETE.md) for complete implementation details, test results, and pattern documentation.

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
├── tests/                 # 95 comprehensive tests
│   ├── unit/              # 77 unit tests for all primitives
│   ├── observability/     # Observability instrumentation tests
│   └── integration/       # 18 integration tests with real backends
├── examples/              # Usage examples
├── scripts/               # Helper scripts (integration-test-env.sh)
├── docker-compose.integration.yml  # Integration test environment
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

## Integration Testing

The package includes comprehensive integration tests that verify observability instrumentation works correctly with real OpenTelemetry backends (Jaeger, Prometheus, Grafana, OpenTelemetry Collector).

### Prerequisites

- **Docker** and **Docker Compose** installed
- Ports available: 4317, 4318, 8888, 8889, 9090, 3000, 16686, 14268, 14250

### Quick Start

```bash
# Start integration test environment
cd packages/tta-dev-primitives
./scripts/integration-test-env.sh start

# Run integration tests
uv run pytest tests/integration/ -v

# Stop services when done
./scripts/integration-test-env.sh stop
```

### Available Services

Once started, the following services are available:

| Service | URL | Purpose |
|---------|-----|---------|
| **Jaeger UI** | http://localhost:16686 | Distributed tracing visualization |
| **Prometheus** | http://localhost:9090 | Metrics collection and querying |
| **Grafana** | http://localhost:3000 | Dashboards and visualization (admin/admin) |
| **OTLP Collector** | http://localhost:4317 (gRPC)<br>http://localhost:4318 (HTTP) | OpenTelemetry data collection |

### Integration Test Suites

#### 1. OpenTelemetry Backend Integration (8 tests)

Tests in `tests/integration/test_otel_backend_integration.py` verify that all workflow primitives create proper spans with correlation IDs:

```bash
# Run OpenTelemetry integration tests
uv run pytest tests/integration/test_otel_backend_integration.py -v
```

**Coverage:**
- ✅ SequentialPrimitive - Sequential execution tracing
- ✅ ParallelPrimitive - Concurrent execution tracing
- ✅ ConditionalPrimitive - Branch execution tracing
- ✅ SwitchPrimitive - Case-based routing tracing
- ✅ RetryPrimitive - Retry attempt tracing
- ✅ FallbackPrimitive - Fallback execution tracing
- ✅ SagaPrimitive - Compensation tracing
- ✅ Composed Workflows - End-to-end trace propagation

#### 2. Prometheus Metrics Infrastructure (10 tests)

Tests in `tests/integration/test_prometheus_metrics.py` verify the metrics collection pipeline:

```bash
# Run Prometheus integration tests
uv run pytest tests/integration/test_prometheus_metrics.py -v
```

**Coverage:**
- ✅ Prometheus health and readiness
- ✅ Prometheus API accessibility
- ✅ Scrape job configuration (prometheus, otel-collector, tta-primitives)
- ✅ Active scrape targets
- ✅ OpenTelemetry Collector metrics export
- ✅ Span and metric processing metrics
- ✅ Prometheus self-monitoring

### Example Queries

#### Jaeger Queries

1. **Find traces by correlation ID:**
   - Service: `tta-dev-primitives`
   - Tags: `workflow.correlation_id=<your-correlation-id>`

2. **Find all Sequential primitive executions:**
   - Service: `tta-dev-primitives`
   - Operation: `primitive.SequentialPrimitive`

3. **Find failed executions:**
   - Service: `tta-dev-primitives`
   - Tags: `error=true`

#### Prometheus Queries (PromQL)

1. **Check OTEL Collector uptime:**
   ```promql
   otelcol_process_uptime{job="otel-collector"}
   ```

2. **Count spans exported:**
   ```promql
   otelcol_exporter_sent_spans{job="otel-collector"}
   ```

3. **Check Prometheus scrape targets:**
   ```promql
   up{job=~"prometheus|otel-collector|tta-primitives"}
   ```

### Troubleshooting

#### Services won't start

```bash
# Check if ports are already in use
lsof -i :9090  # Prometheus
lsof -i :16686 # Jaeger
lsof -i :3000  # Grafana

# Stop any conflicting services
docker ps | grep -E "prometheus|jaeger|grafana|otel"
docker stop <container-id>
```

#### Tests fail with "backend not available"

```bash
# Verify services are running
docker ps | grep tta-

# Check service health
curl http://localhost:9090/-/healthy  # Prometheus
curl http://localhost:16686/          # Jaeger

# Restart services
./scripts/integration-test-env.sh stop
./scripts/integration-test-env.sh start
```

#### No spans appearing in Jaeger

1. **Check OTLP Collector logs:**
   ```bash
   docker logs tta-otel-collector
   ```

2. **Verify correlation ID in test:**
   - Tests use `workflow.correlation_id` tag
   - Search Jaeger with exact correlation ID from test output

3. **Wait for flush:**
   - Tests include 5-second wait for span export
   - Increase wait time if needed in test code

#### No metrics in Prometheus

1. **Check scrape targets:**
   - Visit http://localhost:9090/targets
   - Verify all targets are "UP"

2. **Check OTEL Collector metrics endpoint:**
   ```bash
   curl http://localhost:8889/metrics
   ```

3. **Verify Prometheus configuration:**
   ```bash
   curl http://localhost:9090/api/v1/status/config
   ```

### Future Work

The following integration testing tasks are planned for future implementation:

1. **Performance Overhead Measurement** (Issue TBD)
   - Benchmark tests to measure instrumentation overhead
   - Compare execution time with and without observability enabled
   - Target: <5% latency increase with instrumentation
   - Test with Sequential, Parallel, and composed workflows

2. **Graceful Degradation Tests** (Issue TBD)
   - Test behavior when OpenTelemetry backends are unavailable
   - Verify primitives continue to execute correctly without tracing
   - Test with missing Jaeger, Prometheus, and OTLP Collector
   - Ensure no exceptions are raised when backends are down

3. **Primitive-Level Metrics Integration** (Issue TBD)
   - Export execution time, success/failure rates to Prometheus
   - Add OpenTelemetry metrics instrumentation to InstrumentedPrimitive
   - Bridge EnhancedMetricsCollector with OpenTelemetry metrics
   - Verify metrics have correct labels (primitive_type, workflow_id, correlation_id)

## Quality Metrics

- ✅ **95 tests passing** (100% pass rate)
  - 77 unit tests (core primitives, recovery, performance, observability)
  - 18 integration tests (OpenTelemetry backends, Prometheus metrics)
- ✅ **Core primitives**: 88-100% coverage
- ✅ **Type-safe** with Pydantic v2 and full type annotations
- ✅ **Full async/await** support with proper context propagation
- ✅ **Production-tested** in TTA with real OpenTelemetry backends
- ✅ **Integration-ready** with Docker Compose test environment

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
