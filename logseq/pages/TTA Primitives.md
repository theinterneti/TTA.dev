# TTA Primitives

type:: [[Package]]
category:: [[Core Library]]
package-name:: tta-dev-primitives
status:: [[Active]]

---

## 🎯 Purpose

Core workflow primitives providing composable, type-safe building blocks for AI workflows with built-in observability.

**Key Innovation:** Operator overloading (`>>`, `|`) for intuitive workflow composition.

---

## 📂 Package Structure

```text
packages/tta-dev-primitives/
├── src/tta_dev_primitives/
│   ├── core/              # Base primitives
│   ├── recovery/          # Error handling patterns
│   ├── performance/       # Optimization primitives
│   ├── testing/           # Testing utilities
│   └── observability/     # Tracing and metrics
├── tests/                 # Comprehensive test suite
├── examples/              # Working code examples
└── AGENTS.md              # AI agent instructions
```

---

## 🧱 Core Primitives

### Execution Patterns

#### [[SequentialPrimitive]]

Sequential composition with `>>` operator

```python
workflow = step1 >> step2 >> step3
```

**Use cases:**

- Data transformation pipelines
- Multi-stage processing
- Sequential API calls

#### [[ParallelPrimitive]]

Parallel composition with `|` operator

```python
workflow = branch1 | branch2 | branch3
```

**Use cases:**

- Concurrent LLM calls
- Parallel data processing
- Fan-out/fan-in patterns

#### [[RouterPrimitive]]

Dynamic routing based on input

```python
router = RouterPrimitive(
    routes={"fast": gpt4_mini, "quality": gpt4},
    default_route="fast"
)
```

**Use cases:**

- LLM selection (cost/quality tradeoff)
- Load balancing
- A/B testing

#### [[ConditionalPrimitive]]

Conditional branching

```python
workflow = ConditionalPrimitive(
    condition=lambda ctx, data: data["complexity"] > 0.7,
    true_branch=complex_handler,
    false_branch=simple_handler
)
```

**Use cases:**

- Input validation
- Feature flags
- Adaptive workflows

---

## 🔄 Recovery Primitives

### [[RetryPrimitive]]

Automatic retry with backoff strategies

```python
workflow = RetryPrimitive(
    primitive=api_call,
    max_retries=3,
    backoff_strategy="exponential"
)
```

**Strategies:**

- `constant` - Fixed delay
- `exponential` - Exponential backoff
- `fibonacci` - Fibonacci sequence

### [[FallbackPrimitive]]

Graceful degradation

```python
workflow = FallbackPrimitive(
    primary=expensive_llm,
    fallbacks=[cheaper_llm, cached_response]
)
```

**Use cases:**

- LLM fallback chains
- Service degradation
- Cost optimization

### [[TimeoutPrimitive]]

Circuit breaker pattern

```python
workflow = TimeoutPrimitive(
    primitive=slow_operation,
    timeout_seconds=30.0
)
```

**Use cases:**

- Preventing hanging requests
- Resource protection
- SLA enforcement

### [[CompensationPrimitive]]

Saga pattern for rollback

```python
workflow = CompensationPrimitive(
    forward_primitive=create_order,
    compensation_primitive=cancel_order
)
```

**Use cases:**

- Distributed transactions
- Multi-step workflows with rollback
- State consistency

---

## ⚡ Performance Primitives

### [[CachePrimitive]]

LRU + TTL caching

```python
workflow = CachePrimitive(
    primitive=expensive_operation,
    ttl_seconds=3600,
    max_size=1000
)
```

**Benefits:**

- 30-40% cost reduction for LLM calls
- Sub-millisecond cache hits
- Automatic eviction

**Use cases:**

- Expensive LLM calls
- API responses
- Computed results

---

## 🧪 Testing Primitives

### [[MockPrimitive]]

Testing and mocking

```python
mock_llm = MockPrimitive(
    return_value={"response": "mocked output"}
)

workflow = step1 >> mock_llm >> step3
```

**Features:**

- Call count tracking
- Custom return values
- Exception simulation

---

## 🔍 Observability

All primitives include:

- **Structured logging** via `structlog`
- **Distributed tracing** via OpenTelemetry
- **Metrics** via Prometheus
- **Context propagation** via `WorkflowContext`

### [[WorkflowContext]]

State and correlation tracking

```python
context = WorkflowContext(
    correlation_id="req-123",
    data={"user_id": "user-789"}
)

result = await workflow.execute(context, input_data)
```

**Propagates:**

- Correlation IDs
- User metadata
- Span contexts
- Custom attributes

---

## 🎨 Composition Patterns

### Sequential Pipeline

```python
workflow = (
    input_validator >>
    data_transformer >>
    llm_processor >>
    output_formatter
)
```

### Parallel Fan-Out

```python
workflow = (
    input_processor >>
    (fast_path | quality_path | cached_path) >>
    result_aggregator
)
```

### Router with Fallback

```python
workflow = FallbackPrimitive(
    primary=RouterPrimitive(routes={...}),
    fallbacks=[backup_llm, cached_response]
)
```

### Retry with Timeout

```python
workflow = TimeoutPrimitive(
    primitive=RetryPrimitive(
        primitive=api_call,
        max_retries=3
    ),
    timeout_seconds=60.0
)
```

---

## 🚀 Development Tasks

### Current Sprint

- TODO Add [[BatchPrimitive]] for bulk operations
- TODO Implement [[StreamingPrimitive]] for real-time data
- TODO Create [[TransformPrimitive]] helper
- DOING Add more examples to [[examples/]]

### Backlog

- LATER [[DistributedPrimitive]] for multi-node execution
- LATER [[SchedulerPrimitive]] for cron-like workflows
- LATER [[RateLimitPrimitive]] for API throttling

---

## 📖 Examples

All examples are in `packages/tta-dev-primitives/examples/`:

- `basic_sequential.py` - Sequential composition
- `parallel_execution.py` - Parallel patterns
- `router_llm_selection.py` - LLM routing
- `error_handling_patterns.py` - Recovery primitives
- `real_world_workflows.py` - Production examples

---

## 🧪 Testing Strategy

### Coverage Requirements

- **100% coverage** for all primitives
- **Edge case testing** (empty inputs, errors, timeouts)
- **Async testing** with `pytest-asyncio`
- **Mock integration** with `MockPrimitive`

### Running Tests

```bash
# All tests
uv run pytest packages/tta-dev-primitives/tests/ -v

# Specific primitive
uv run pytest packages/tta-dev-primitives/tests/core/test_sequential.py

# With coverage
uv run pytest --cov=packages/tta-dev-primitives --cov-report=html
```

---

## 🔗 Integration Points

### Used By

- [[Universal Agent Context]] - Agent coordination
- [[Observability Integration]] - Enhanced observability
- All TTA.dev workflows

### Dependencies

- Python 3.11+
- `asyncio` - Async runtime
- `structlog` - Structured logging
- `opentelemetry-api` - Tracing (optional)

---

## 📊 Metrics

### Performance

- Primitive overhead: < 1ms
- Memory footprint: < 1MB per workflow
- Cache hit rate: 80-95% (production)

### Code Quality

- Test coverage: 100%
- Type coverage: 100%
- Lint score: 10.0/10.0

---

## 🎯 Design Principles

1. **Composability** - Primitives compose via operators
2. **Type Safety** - Full generic type support
3. **Observability** - Built-in tracing and logging
4. **Testability** - Easy mocking and testing
5. **Performance** - Minimal overhead
6. **Extensibility** - Subclass for custom behavior

---

## 🔗 Resources

- **Package README:** `packages/tta-dev-primitives/README.md`
- **Agent Instructions:** `packages/tta-dev-primitives/AGENTS.md`
- **Catalog:** [[PRIMITIVES_CATALOG]]
- **Architecture:** `docs/architecture/primitives-design.md`

---

**Last Updated:** 2025-10-30
**Maintainer:** @theinterneti
**Status:** Production-ready
