# TTA.dev System Design

**Repository:** TTA.dev
**Purpose:** High-level system architecture and design overview
**Last Updated:** October 30, 2025

---

## System Overview

TTA.dev is a production-ready AI development toolkit providing **composable agentic primitives** for building reliable AI workflows. The system is designed around core principles of composability, observability, and reliability.

### Core Vision

**Enable developers to build AI workflows like Unix pipes:**
- Small, focused components (`primitives`)
- Composable with intuitive operators (`>>`, `|`)
- Type-safe composition
- Built-in observability
- Production-ready patterns

---

## System Architecture

### High-Level View

```text
┌────────────────────────────────────────────────────────────┐
│                   Application Layer                         │
│  (User workflows, AI agents, API services)                  │
└────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌────────────────────────────────────────────────────────────┐
│              TTA.dev Primitive Layer                        │
│                                                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │  Core    │  │ Recovery │  │ Perf     │  │ Testing  │  │
│  │          │  │          │  │          │  │          │  │
│  │Sequential│  │  Retry   │  │  Cache   │  │   Mock   │  │
│  │ Parallel │  │ Fallback │  │          │  │          │  │
│  │  Router  │  │ Timeout  │  │          │  │          │  │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘  │
└────────────────────────────────────────────────────────────┘
                           │
           ┌───────────────┼───────────────┐
           │               │               │
           ▼               ▼               ▼
    ┌───────────┐   ┌───────────┐   ┌───────────┐
    │Observabil │   │  Agent    │   │  Testing  │
    │ity        │   │ Context   │   │ Framework │
    │           │   │           │   │           │
    │OpenTelem  │   │Coordinat  │   │  Keploy   │
    │Prometheus │   │   ion     │   │  Mocks    │
    └───────────┘   └───────────┘   └───────────┘
```

### Component Layers

**1. Core Primitives Layer**
- Base abstractions (`WorkflowPrimitive`, `WorkflowContext`)
- Composition primitives (Sequential, Parallel, Conditional, Router)
- Recovery primitives (Retry, Fallback, Timeout, Compensation)
- Performance primitives (Cache)
- Testing primitives (Mock)

**2. Integration Layer**
- Observability integration (OpenTelemetry, Prometheus)
- Agent context management
- API testing framework (Keploy)
- Python utilities (Pathway)

**3. Application Layer**
- User workflows
- AI agents
- API services
- Custom primitives

---

## Design Principles

### 1. Composability

**Principle:** Small, focused components that compose intuitively.

**Implementation:**
- Base `WorkflowPrimitive` class
- Operator overloading (`>>`, `|`)
- Type-safe composition with generics
- Mix sequential and parallel patterns

**Example:**
```python
workflow = (
    input_processor >>
    (fast_llm | slow_llm | cached_llm) >>
    aggregator >>
    output_formatter
)
```

### 2. Type Safety

**Principle:** Catch errors at development time, not runtime.

**Implementation:**
- Generic types: `WorkflowPrimitive[TInput, TOutput]`
- Type checking at composition time
- IDE autocomplete and type hints
- Pyright for strict type checking

**Example:**
```python
# Type-safe composition
step1: WorkflowPrimitive[str, dict]
step2: WorkflowPrimitive[dict, list]

workflow = step1 >> step2  # ✅ Types match
workflow = step1 >> step3  # ❌ Editor shows type error
```

### 3. Observability by Default

**Principle:** All operations traced, measured, and logged automatically.

**Implementation:**
- `InstrumentedPrimitive` base class
- Automatic span creation
- Built-in metrics collection
- Structured logging
- Context propagation

**Example:**
```python
# Observability is automatic
result = await workflow.execute(context, input_data)

# Automatically:
# - Creates spans for each primitive
# - Records execution metrics
# - Logs with correlation IDs
# - Exports to Prometheus/Jaeger
```

### 4. Graceful Degradation

**Principle:** System works even when optional components fail.

**Implementation:**
- Optional OpenTelemetry dependency
- Try/except with fallbacks
- Return boolean from initialization
- Continue without observability if unavailable

**Example:**
```python
# Observability fails gracefully
success = initialize_observability()
if not success:
    logger.info("Running without observability")
# Application continues working
```

### 5. Production-Ready Patterns

**Principle:** Built-in patterns for reliability and performance.

**Implementation:**
- Retry with exponential backoff
- Fallback for degradation
- Timeout for circuit breaking
- Cache for performance
- Compensation for distributed transactions

**Example:**
```python
# Production-ready with one line
llm = TimeoutPrimitive(
    RetryPrimitive(
        FallbackPrimitive(
            CachePrimitive(gpt4),
            fallbacks=[gpt35, local_llm]
        )
    ),
    timeout_seconds=30.0
)
```

---

## Data Flow

### Typical Workflow Execution

```text
1. Application creates WorkflowContext
   └─> correlation_id: "req-123"
   └─> data: {"user_id": "user-789"}

2. Execute workflow.execute(context, input_data)
   │
   ├─> Step 1: input_processor
   │   ├─> Create span "input_processor.execute"
   │   ├─> Execute business logic
   │   ├─> Record metrics
   │   └─> Return result
   │
   ├─> Step 2: Parallel execution
   │   ├─> Branch A: fast_llm
   │   │   └─> (same observability)
   │   ├─> Branch B: slow_llm
   │   │   └─> (same observability)
   │   └─> Branch C: cached_llm
   │       ├─> Check cache (hit!)
   │       └─> Return cached result
   │
   ├─> Step 3: aggregator
   │   ├─> Receives [result_A, result_B, result_C]
   │   └─> Combines into single result
   │
   └─> Step 4: output_formatter
       └─> Formats final output

3. Return final result to application

4. Export observability data
   ├─> Spans to Jaeger
   ├─> Metrics to Prometheus
   └─> Logs to stdout (JSON)
```

---

## Key Components

### WorkflowPrimitive

**Purpose:** Base abstraction for all primitives

**Key Methods:**
- `execute(context, input_data)` - Public interface with observability
- `_execute_impl(context, input_data)` - Subclass implementation
- `__rshift__(other)` - Sequential composition (`>>`)
- `__or__(other)` - Parallel composition (`|`)

**Subclassing:**
```python
class CustomPrimitive(WorkflowPrimitive[str, dict]):
    async def _execute_impl(self, context, input_data):
        # Your logic here
        return {"result": "processed"}
```

### WorkflowContext

**Purpose:** Carry state and correlation through workflows

**Key Fields:**
- `correlation_id` - Unique ID for request tracking
- `data` - User-defined context data
- `parent_span_context` - OpenTelemetry span context

**Usage:**
```python
context = WorkflowContext(
    correlation_id="req-abc-123",
    data={"user_id": "user-789", "priority": "high"}
)

result = await workflow.execute(context, input_data)

# correlation_id appears in all logs and traces
```

### Composition Primitives

**SequentialPrimitive** - Execute in order
```python
workflow = step1 >> step2 >> step3
```

**ParallelPrimitive** - Execute concurrently
```python
workflow = branch1 | branch2 | branch3
```

**ConditionalPrimitive** - Branch based on condition
```python
workflow = ConditionalPrimitive(
    condition=lambda ctx, data: len(data) < 1000,
    true_primitive=fast_path,
    false_primitive=slow_path
)
```

**RouterPrimitive** - Dynamic routing
```python
router = RouterPrimitive(
    routes={"fast": llm1, "quality": llm2},
    selector=select_route,
    default_route="fast"
)
```

### Recovery Primitives

**RetryPrimitive** - Automatic retry with backoff
**FallbackPrimitive** - Graceful degradation
**TimeoutPrimitive** - Circuit breaker
**CompensationPrimitive** - Saga pattern for rollback

### Performance Primitives

**CachePrimitive** - LRU cache with TTL

---

## Integration Architecture

### Observability Integration

**Two-Package Design:**

1. **Core Observability** (tta-dev-primitives)
   - Lightweight, no external dependencies
   - `InstrumentedPrimitive`, `PrimitiveMetrics`
   - Always available

2. **Enhanced Observability** (tta-observability-integration)
   - OpenTelemetry SDK
   - Prometheus metrics server
   - Optional, fails gracefully

**Benefits:**
- Core stays lightweight
- Enhanced features optional
- Production-ready patterns available
- Vendor-neutral (works with any backend)

### Agent Context Integration

**Purpose:** Multi-agent coordination and state management

**Key Components:**
- Agent context management
- Shared state across agents
- Coordination primitives

**Integration:** Builds on WorkflowContext for agent coordination

### Testing Integration

**Keploy Framework:**
- Record API interactions
- Replay for testing
- Generate mocks

**MockPrimitive:**
- Built-in mock for testing workflows
- Track calls, return values, side effects

---

## Deployment Models

### Model 1: Standalone Application

```text
┌─────────────────────────┐
│   Python Application    │
│                         │
│  ├─ tta-dev-primitives │
│  └─ Custom workflows    │
└─────────────────────────┘
```

**Use Case:** Simple AI workflows, scripts, notebooks

**Installation:**
```bash
uv add tta-dev-primitives
```

### Model 2: Observability-Enabled Service

```text
┌──────────────────────────────┐
│   Python Service             │
│                              │
│  ├─ tta-dev-primitives      │
│  └─ tta-observability-int   │
└──────────────────────────────┘
         │
         ├──> Prometheus (metrics)
         └──> Jaeger (traces)
```

**Use Case:** Production services needing monitoring

**Installation:**
```bash
uv add tta-dev-primitives tta-observability-integration
```

### Model 3: Full Stack with Agent Coordination

```text
┌──────────────────────────────────┐
│   Multi-Agent System             │
│                                  │
│  ├─ tta-dev-primitives          │
│  ├─ tta-observability-int       │
│  ├─ universal-agent-context     │
│  └─ keploy-framework (testing)  │
└──────────────────────────────────┘
         │
         ├──> Monitoring Stack
         └──> Agent Coordination
```

**Use Case:** Complex multi-agent systems

**Installation:**
```bash
uv add tta-dev-primitives tta-observability-integration \
  universal-agent-context keploy-framework
```

---

## Performance Characteristics

### Overhead

**Core Primitives:**
- Span creation: ~0.5ms
- Metrics recording: ~0.2ms
- **Total overhead per primitive: ~1-2ms**

**Enhanced Observability:**
- Prometheus metrics: ~0.5ms
- OTLP export (async): ~0ms
- **Total overhead: ~2-3ms**

**Optimization:**
- Batch span export (reduces overhead)
- Sampling (for high-volume services)
- Selective instrumentation (critical paths only)

### Throughput

**Sequential Workflow:**
- 5 primitives: ~10ms overhead
- 10 primitives: ~20ms overhead
- Scales linearly with primitive count

**Parallel Workflow:**
- Overhead only on coordinator primitive
- Individual branches run concurrently
- Scales with number of branches (asyncio)

---

## Scalability

### Horizontal Scaling

**Stateless Design:**
- Primitives are stateless (except Cache)
- WorkflowContext carries all state
- Easy to scale across multiple instances

**Load Balancing:**
- Standard load balancers work
- No session affinity needed
- Observability context propagates via headers

### Vertical Scaling

**Async/Await:**
- All primitives use async/await
- Efficient use of single thread
- Handles 1000s of concurrent workflows

**Resource Management:**
- Cache primitives have size limits
- Timeout primitives prevent resource leaks
- Graceful degradation under load

---

## Security Considerations

### Input Validation

**Pattern:** Validate at workflow entry
```python
workflow = input_validator >> process >> output
```

### Sensitive Data

**Pattern:** Filter from logs/traces
```python
# Don't log sensitive fields
context = WorkflowContext(
    correlation_id="req-123",
    data={"user_id": "user-789"}  # Don't include passwords!
)
```

### API Keys

**Pattern:** Environment variables, not code
```python
# ✅ Good
api_key = os.getenv("API_KEY")

# ❌ Bad
api_key = "sk-hardcoded-key"  # Never do this!
```

---

## Future Directions

### Planned Enhancements

1. **More Primitives**
   - `BatchPrimitive` - Batch processing
   - `StreamPrimitive` - Streaming data
   - `FilterPrimitive` - Conditional filtering

2. **Advanced Observability**
   - Cost tracking dashboard
   - Performance recommendations
   - Anomaly detection

3. **Agent Orchestration**
   - Multi-agent workflows
   - Agent communication primitives
   - Shared state management

4. **Cloud Integrations**
   - AWS Lambda deployment
   - GCP Cloud Run support
   - Azure Functions integration

---

## Related Documentation

- **Getting Started:** [`GETTING_STARTED.md`](../../GETTING_STARTED.md)
- **Primitives Catalog:** [`PRIMITIVES_CATALOG.md`](../../PRIMITIVES_CATALOG.md)
- **Decision Records:** [`DECISION_RECORDS.md`](DECISION_RECORDS.md)
- **Primitive Patterns:** [`PRIMITIVE_PATTERNS.md`](PRIMITIVE_PATTERNS.md)
- **Observability Architecture:** [`OBSERVABILITY_ARCHITECTURE.md`](OBSERVABILITY_ARCHITECTURE.md)
- **Monorepo Structure:** [`MONOREPO_STRUCTURE.md`](MONOREPO_STRUCTURE.md)

---

**Last Updated:** October 30, 2025
**Maintainer:** TTA.dev Core Team
