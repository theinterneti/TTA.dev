# TTA.dev 3-Pillar Observability Strategy

**Staff-Level Observability Architecture for Agentic Workflows**

---

## Executive Summary

This document defines a comprehensive observability strategy for TTA.dev (The Thinking Agent), transforming raw trace data into actionable intelligence for "lazy vibe coders" who need at-a-glance insights into complex agentic systems.

**Current State:**
- ✅ Basic tracing functional (OTLP → Jaeger)
- ✅ Individual primitive traces (`primitive.SequentialPrimitive`, `sequential.step_0`)
- ⚠️ Span linking broken (traces not unified)
- ⚠️ Minimal metadata
- ⚠️ No aggregated metrics
- ⚠️ No pre-built dashboards

**Target State:**
- ✅ Unified, semantic traces across entire agent workflows
- ✅ Aggregated metrics showing system health and bottlenecks
- ✅ Intuitive dashboards requiring zero trace diving
- ✅ Answer key questions: What's running? How's it connected? Where are bottlenecks? Is it healthy?

---

## Pillar 1: Semantic Tracing Strategy

### Service Naming Convention

**Approach: Hierarchical Service Architecture**

TTA.dev should use a **multi-service model** where each logical component is a separate service. This provides:
- Better service maps showing component relationships
- Granular filtering and alerting per component
- Clear ownership boundaries

**Recommended Service Names:**

```yaml
# Core Agent Services
service.name: "tta-agent-orchestrator"    # Agent coordination layer
service.name: "tta-workflow-engine"       # Workflow primitive execution
service.name: "tta-llm-gateway"           # LLM abstraction layer
service.name: "tta-cache-layer"           # Caching primitive service

# Integration Services
service.name: "tta-external-llm"          # External LLM calls (OpenAI, Anthropic)
service.name: "tta-data-processing"       # Data transformation primitives
service.name: "tta-validation"            # Validation primitives

# Support Services
service.name: "tta-metrics-collector"     # Metrics aggregation
service.name: "tta-health-monitor"        # System health checks
```

**Implementation:**

```python
from opentelemetry.sdk.resources import Resource

# In each component's initialization
resource = Resource.create({
    "service.name": "tta-workflow-engine",
    "service.version": "0.1.0",
    "service.namespace": "tta-platform",
    "deployment.environment": "production",  # or staging, development
    "component.type": "workflow-primitive",   # or agent, llm-gateway, etc.
})
```

---

### Span Naming Convention

**Pattern: `{domain}.{component}.{action}`**

This 3-level hierarchy provides semantic clarity while maintaining trace readability.

**Level 1: Domain** - High-level system area
- `agent.*` - Agent orchestration and coordination
- `primitive.*` - Workflow primitive execution
- `llm.*` - Language model interactions
- `cache.*` - Caching operations
- `validation.*` - Validation steps
- `recovery.*` - Retry, fallback, circuit breaker operations

**Level 2: Component** - Specific component or primitive type
- `agent.orchestrator`, `agent.coordinator`
- `primitive.sequential`, `primitive.parallel`, `primitive.router`
- `llm.openai`, `llm.anthropic`, `llm.local`
- `cache.redis`, `cache.memory`

**Level 3: Action** - Specific operation
- `.execute`, `.validate`, `.retry`, `.fallback`, `.cache_lookup`

**Examples:**

```python
# Agent execution
span_name = "agent.orchestrator.execute"
span_name = "agent.coordinator.delegate_task"

# Primitive execution
span_name = "primitive.sequential.execute"
span_name = "primitive.parallel.execute"
span_name = "primitive.router.route_decision"
span_name = "primitive.validation.check"

# Individual primitive steps
span_name = "primitive.sequential.step_0"
span_name = "primitive.sequential.step_1"
span_name = "primitive.parallel.branch_0"

# LLM operations
span_name = "llm.openai.generate"
span_name = "llm.anthropic.stream"
span_name = "llm.router.select_model"

# Cache operations
span_name = "cache.redis.lookup"
span_name = "cache.memory.store"
span_name = "cache.primitive.execute"  # Wrapper primitive

# Recovery operations
span_name = "recovery.retry.attempt"
span_name = "recovery.fallback.execute_primary"
span_name = "recovery.circuit_breaker.check"
```

**Implementation in InstrumentedPrimitive:**

```python
# Current (needs update)
span_name = f"primitive.{self.name}"

# Recommended (semantic)
span_name = f"primitive.{self.primitive_type}.{self.action}"

# Example updates:
class SequentialPrimitive(InstrumentedPrimitive):
    def __init__(self):
        super().__init__(
            primitive_type="sequential",
            action="execute"
        )

    def _create_step_span(self, step_index: int):
        return f"primitive.sequential.step_{step_index}"

class RouterPrimitive(InstrumentedPrimitive):
    def _create_routing_span(self):
        return "primitive.router.route_decision"

    def _create_execution_span(self, route_name: str):
        return f"primitive.router.execute_{route_name}"
```

---

### Essential Span Attributes

**Standard Attributes (All Spans):**

```python
# Identity attributes
"agent.id": "agent_xyz_123",              # Unique agent instance ID
"agent.type": "narrative_generator",       # Type of agent
"workflow.id": "wf_456",                   # Workflow instance ID
"workflow.name": "content_generation",     # Human-readable workflow name
"session.id": "sess_789",                  # User/session identifier

# Primitive attributes
"primitive.name": "SequentialPrimitive",   # Primitive class name
"primitive.type": "sequential",            # Primitive category
"primitive.step_index": 0,                 # Step number in sequence
"primitive.total_steps": 3,                # Total steps in workflow

# Execution attributes
"execution.start_time": 1699123456.789,    # Timestamp (float)
"execution.duration_ms": 234.5,            # Duration in milliseconds
"execution.status": "success",             # success | error | timeout
"execution.retry_count": 0,                # Number of retries (if applicable)

# Error attributes (when applicable)
"error.type": "ValidationFailure",         # Exception type
"error.message": "Invalid input format",   # Exception message
"error.stack_trace": "...",                # Full stack trace
"error.recoverable": true,                 # Can be retried?
```

**LLM-Specific Attributes:**

```python
# Model information
"llm.provider": "openai",                  # openai | anthropic | google | local
"llm.model_name": "gpt-4o",                # Specific model
"llm.model_tier": "premium",               # fast | balanced | premium
"llm.temperature": 0.7,                    # Model temperature
"llm.max_tokens": 2000,                    # Max tokens

# Usage tracking
"llm.prompt_tokens": 150,                  # Input tokens
"llm.completion_tokens": 300,              # Output tokens
"llm.total_tokens": 450,                   # Total tokens
"llm.cost_usd": 0.0045,                    # Cost in USD

# Streaming
"llm.streaming": true,                     # Is streaming response?
"llm.chunks_received": 15,                 # Number of chunks (if streaming)
```

**Cache-Specific Attributes:**

```python
# Cache behavior
"cache.hit": true,                         # Cache hit or miss?
"cache.key": "hash_abc123",                # Cache key (hashed)
"cache.ttl_seconds": 3600,                 # TTL setting
"cache.age_seconds": 234,                  # Age of cached entry
"cache.eviction_policy": "lru",            # LRU | TTL | FIFO

# Cache performance
"cache.lookup_time_ms": 2.3,               # Cache lookup latency
"cache.size_bytes": 15000,                 # Size of cached value
"cache.savings_usd": 0.05,                 # Cost saved by cache hit
```

**Recovery-Specific Attributes:**

```python
# Retry attributes
"retry.attempt": 2,                        # Current attempt (1-indexed)
"retry.max_attempts": 3,                   # Max retry attempts
"retry.backoff_ms": 1000,                  # Backoff delay
"retry.strategy": "exponential",           # constant | linear | exponential

# Fallback attributes
"fallback.triggered": true,                # Fallback activated?
"fallback.primary_failed": true,           # Primary path failed?
"fallback.strategy_used": "cached_response", # Which fallback strategy

# Circuit breaker attributes
"circuit_breaker.state": "open",           # open | closed | half_open
"circuit_breaker.failure_rate": 0.45,      # Current failure rate
"circuit_breaker.threshold": 0.50,         # Failure threshold
"circuit_breaker.timeout_ms": 30000,       # Circuit open timeout
```

**Validation-Specific Attributes:**

```python
# Validation results
"validation.passed": true,                 # Validation result
"validation.rule": "schema_compliance",    # Validation rule name
"validation.schema": "narrative_v1",       # Schema identifier
"validation.errors": 0,                    # Number of validation errors
"validation.warnings": 2,                  # Number of warnings
```

**Implementation Example:**

```python
class InstrumentedPrimitive(WorkflowPrimitive[T, U]):
    async def execute(self, input_data: T, context: WorkflowContext) -> U:
        with create_linked_span(
            self._tracer,
            f"primitive.{self.primitive_type}.{self.action}",
            context
        ) as span:
            # Standard attributes
            span.set_attribute("agent.id", context.agent_id or "unknown")
            span.set_attribute("agent.type", context.agent_type or "unknown")
            span.set_attribute("workflow.id", context.workflow_id or "unknown")
            span.set_attribute("workflow.name", context.workflow_name or "unknown")
            span.set_attribute("session.id", context.session_id or "unknown")

            # Primitive attributes
            span.set_attribute("primitive.name", self.__class__.__name__)
            span.set_attribute("primitive.type", self.primitive_type)

            # Context metadata (dynamic)
            for key, value in context.metadata.items():
                if key.startswith("primitive."):
                    span.set_attribute(key, value)

            try:
                result = await self._execute_impl(input_data, context)
                span.set_attribute("execution.status", "success")
                return result
            except Exception as e:
                span.set_attribute("execution.status", "error")
                span.set_attribute("error.type", type(e).__name__)
                span.set_attribute("error.message", str(e))
                span.set_attribute("error.recoverable", self._is_recoverable(e))
                raise
```

---

## Pillar 2: Aggregated Metrics Strategy

### Top 7 Core Metrics

**1. Primitive Execution Counter**

```python
# Metric name
"primitive.execution.count"

# Type: Counter
# Description: Total number of primitive executions
# Attributes:
#   - primitive.name: SequentialPrimitive, RouterPrimitive, etc.
#   - primitive.type: sequential, parallel, router, cache, etc.
#   - execution.status: success | error | timeout
#   - agent.type: narrative_generator, content_analyzer, etc.

# Use cases:
# - Track which primitives are most/least used
# - Monitor error rates per primitive
# - Identify failing components

# PromQL queries:
# Total executions: sum(primitive_execution_count)
# Error rate: rate(primitive_execution_count{execution_status="error"}[5m])
# Top 5 primitives: topk(5, sum by (primitive_name) (primitive_execution_count))
```

**Implementation:**

```python
from opentelemetry import metrics

meter = metrics.get_meter(__name__)
execution_counter = meter.create_counter(
    name="primitive.execution.count",
    description="Total primitive executions",
    unit="1",
)

# Record execution
execution_counter.add(
    1,
    attributes={
        "primitive.name": "SequentialPrimitive",
        "primitive.type": "sequential",
        "execution.status": "success",
        "agent.type": "narrative_generator",
    }
)
```

---

**2. Primitive Execution Duration Histogram**

```python
# Metric name
"primitive.execution.duration"

# Type: Histogram
# Description: Execution duration distribution
# Unit: milliseconds
# Attributes:
#   - primitive.name: SequentialPrimitive, RouterPrimitive, etc.
#   - primitive.type: sequential, parallel, router, cache, etc.
#   - agent.type: narrative_generator, content_analyzer, etc.

# Buckets: [10, 50, 100, 250, 500, 1000, 2500, 5000, 10000]  # milliseconds

# Use cases:
# - Identify slow primitives (bottlenecks)
# - Track latency percentiles (p50, p90, p95, p99)
# - Monitor SLO compliance

# PromQL queries:
# P95 latency: histogram_quantile(0.95, primitive_execution_duration_bucket)
# P99 by primitive: histogram_quantile(0.99, sum by (primitive_name, le) (primitive_execution_duration_bucket))
# Slow primitives: topk(5, histogram_quantile(0.95, sum by (primitive_name, le) (primitive_execution_duration_bucket)))
```

**Implementation:**

```python
duration_histogram = meter.create_histogram(
    name="primitive.execution.duration",
    description="Primitive execution duration",
    unit="ms",
)

# Record duration
start_time = time.time()
# ... execute primitive ...
duration_ms = (time.time() - start_time) * 1000

duration_histogram.record(
    duration_ms,
    attributes={
        "primitive.name": "SequentialPrimitive",
        "primitive.type": "sequential",
        "agent.type": "narrative_generator",
    }
)
```

---

**3. Primitive Connection Counter**

```python
# Metric name
"primitive.connection.count"

# Type: Counter
# Description: Tracks how primitives call each other (edges in workflow graph)
# Attributes:
#   - source.primitive: Name of calling primitive
#   - source.type: Type of calling primitive
#   - target.primitive: Name of called primitive
#   - target.type: Type of called primitive
#   - connection.type: sequential | parallel | conditional

# Use cases:
# - Build service dependency graph
# - Understand workflow structure
# - Identify critical paths

# PromQL queries:
# All connections: sum by (source_primitive, target_primitive) (primitive_connection_count)
# Most connected primitive: topk(1, sum by (target_primitive) (primitive_connection_count))
# Connection frequency: rate(primitive_connection_count[5m])
```

**Implementation:**

```python
connection_counter = meter.create_counter(
    name="primitive.connection.count",
    description="Primitive-to-primitive connections",
    unit="1",
)

# Record connection (in SequentialPrimitive)
for i, primitive in enumerate(self.primitives):
    if i > 0:
        connection_counter.add(
            1,
            attributes={
                "source.primitive": self.primitives[i-1].__class__.__name__,
                "source.type": getattr(self.primitives[i-1], "primitive_type", "unknown"),
                "target.primitive": primitive.__class__.__name__,
                "target.type": getattr(primitive, "primitive_type", "unknown"),
                "connection.type": "sequential",
            }
        )
```

---

**4. LLM Token Usage Counter**

```python
# Metric name
"llm.tokens.total"

# Type: Counter
# Description: Total tokens consumed by LLM calls
# Attributes:
#   - llm.provider: openai, anthropic, google, local
#   - llm.model_name: gpt-4o, claude-sonnet-3.5, etc.
#   - llm.token_type: prompt | completion | total
#   - agent.type: narrative_generator, content_analyzer, etc.

# Use cases:
# - Track LLM usage and costs
# - Monitor token consumption trends
# - Budget enforcement

# PromQL queries:
# Total tokens: sum(llm_tokens_total)
# Tokens by model: sum by (llm_model_name) (llm_tokens_total)
# Token rate: rate(llm_tokens_total[5m])
# Cost estimate: sum(llm_tokens_total) * cost_per_token
```

**Implementation:**

```python
token_counter = meter.create_counter(
    name="llm.tokens.total",
    description="Total LLM tokens consumed",
    unit="1",
)

# Record token usage
token_counter.add(
    usage.prompt_tokens,
    attributes={
        "llm.provider": "openai",
        "llm.model_name": "gpt-4o",
        "llm.token_type": "prompt",
        "agent.type": "narrative_generator",
    }
)
token_counter.add(
    usage.completion_tokens,
    attributes={
        "llm.provider": "openai",
        "llm.model_name": "gpt-4o",
        "llm.token_type": "completion",
        "agent.type": "narrative_generator",
    }
)
```

---

**5. Cache Hit Rate Gauge**

```python
# Metric name
"cache.hit_rate"

# Type: Gauge (calculated from hits/total)
# Description: Cache hit rate percentage
# Attributes:
#   - cache.type: redis | memory | distributed
#   - primitive.name: CachePrimitive instance name
#   - cache.key_pattern: Pattern of cache keys

# Use cases:
# - Monitor cache effectiveness
# - Track cost savings from cache hits
# - Identify cache tuning opportunities

# PromQL queries:
# Hit rate: (sum(cache_hits) / sum(cache_total)) * 100
# Hit rate by cache: (sum by (cache_type) (cache_hits) / sum by (cache_type) (cache_total)) * 100
# Low hit rate: cache_hit_rate < 0.5
```

**Implementation:**

```python
cache_hit_counter = meter.create_counter(
    name="cache.hits",
    description="Cache hits",
    unit="1",
)
cache_total_counter = meter.create_counter(
    name="cache.total",
    description="Total cache lookups",
    unit="1",
)

# Record cache lookup
cache_total_counter.add(1, attributes={"cache.type": "redis", "primitive.name": "llm_cache"})
if cache_hit:
    cache_hit_counter.add(1, attributes={"cache.type": "redis", "primitive.name": "llm_cache"})
```

---

**6. Agent Active Workflows Gauge**

```python
# Metric name
"agent.workflows.active"

# Type: Gauge (up/down counter)
# Description: Number of currently active workflow executions
# Attributes:
#   - agent.type: narrative_generator, content_analyzer, etc.
#   - workflow.name: content_generation, data_processing, etc.

# Use cases:
# - Monitor system load and concurrency
# - Identify peak usage times
# - Capacity planning

# PromQL queries:
# Current active: agent_workflows_active
# Peak concurrent: max_over_time(agent_workflows_active[1h])
# Average concurrent: avg_over_time(agent_workflows_active[5m])
```

**Implementation:**

```python
active_workflows_gauge = meter.create_up_down_counter(
    name="agent.workflows.active",
    description="Active workflow executions",
    unit="1",
)

# Start workflow
active_workflows_gauge.add(
    1,
    attributes={
        "agent.type": "narrative_generator",
        "workflow.name": "content_generation",
    }
)

# End workflow
active_workflows_gauge.add(
    -1,
    attributes={
        "agent.type": "narrative_generator",
        "workflow.name": "content_generation",
    }
)
```

---

**7. SLO Compliance Gauge**

```python
# Metric name
"slo.compliance"

# Type: Gauge
# Description: SLO compliance percentage (0.0 to 1.0)
# Attributes:
#   - slo.name: latency_p95 | availability | error_budget
#   - slo.target: 0.99, 0.999, etc.
#   - primitive.name: SequentialPrimitive, RouterPrimitive, etc.

# Use cases:
# - Monitor SLO compliance in real-time
# - Alert on SLO violations
# - Track error budget burn rate

# PromQL queries:
# Current compliance: slo_compliance
# Violations: slo_compliance < slo_target
# Error budget remaining: 1 - ((1 - slo_compliance) / (1 - slo_target))
```

**Implementation:**

```python
slo_compliance_gauge = meter.create_gauge(
    name="slo.compliance",
    description="SLO compliance percentage",
    unit="1",  # 0.0 to 1.0
)

# Update SLO compliance
slo_compliance_gauge.set(
    0.995,  # 99.5% compliance
    attributes={
        "slo.name": "latency_p95",
        "slo.target": 0.99,
        "primitive.name": "SequentialPrimitive",
    }
)
```

---

### Connecting Primitives via Metrics

**Strategy: Parent-Child Span Context + Connection Metrics**

1. **Span Links**: Use OpenTelemetry span links to connect parent and child spans
2. **Context Propagation**: Pass `trace_id` and `span_id` through WorkflowContext
3. **Connection Metrics**: Explicit counter for primitive-to-primitive calls

**Implementation:**

```python
class SequentialPrimitive(InstrumentedPrimitive):
    async def _execute_impl(self, input_data, context):
        for i, primitive in enumerate(self.primitives):
            # Record connection metric
            if i > 0:
                connection_counter.add(
                    1,
                    attributes={
                        "source.primitive": self.primitives[i-1].__class__.__name__,
                        "target.primitive": primitive.__class__.__name__,
                        "connection.type": "sequential",
                        "workflow.id": context.workflow_id,
                    }
                )

            # Create child span with link to parent
            with tracer.start_as_current_span(
                f"primitive.sequential.step_{i}",
                attributes={
                    "primitive.step_index": i,
                    "primitive.total_steps": len(self.primitives),
                    "parent.primitive": self.__class__.__name__,
                }
            ) as span:
                # Inject trace context for child primitive
                context = inject_trace_context(context)

                # Execute child primitive
                result = await primitive.execute(result, context)
```

**Resulting Metrics:**

```promql
# Service map (connection graph)
sum by (source_primitive, target_primitive) (
    rate(primitive_connection_count[5m])
)

# Most connected primitives (hubs)
topk(5, sum by (target_primitive) (primitive_connection_count))

# Critical paths (high traffic connections)
topk(10, rate(primitive_connection_count[5m]))
```

---

## Pillar 3: Dashboard Design

### Ultimate Agent Observability Dashboard

**Dashboard Structure: 4 Tabs**

1. **Overview** - System health at a glance
2. **Workflows** - Workflow execution and performance
3. **Primitives** - Individual primitive deep-dive
4. **Resources** - LLM usage, cache, costs

---

### Tab 1: Overview (System Health)

**Panel 1: Service Map**
```
Type: Graph/Network Diagram
Data: primitive_connection_count
Question: How are my components connected?

Query:
sum by (source_primitive, target_primitive) (
    rate(primitive_connection_count[5m])
)

Visualization:
- Nodes: Primitives (sized by execution count)
- Edges: Connections (thickness = call frequency)
- Colors: Node health (green = healthy, yellow = degraded, red = errors)
```

**Panel 2: System Health Score**
```
Type: Gauge (0-100%)
Data: Weighted average of SLO compliance
Question: Is the system healthy overall?

Query:
(
  avg(slo_compliance{slo_name="availability"}) * 0.4 +
  avg(slo_compliance{slo_name="latency_p95"}) * 0.4 +
  avg(slo_compliance{slo_name="error_budget"}) * 0.2
) * 100

Thresholds:
- Green: > 95%
- Yellow: 90-95%
- Red: < 90%
```

**Panel 3: Throughput (Requests/sec)**
```
Type: Time series graph
Data: primitive_execution_count
Question: How much traffic is the system handling?

Query:
sum(rate(primitive_execution_count[5m]))

Additional series:
- Success rate: rate(primitive_execution_count{execution_status="success"}[5m])
- Error rate: rate(primitive_execution_count{execution_status="error"}[5m])
```

**Panel 4: Active Workflows**
```
Type: Time series graph
Data: agent_workflows_active
Question: How many workflows are running concurrently?

Query:
sum(agent_workflows_active)

By workflow:
sum by (workflow_name) (agent_workflows_active)
```

**Panel 5: Error Rate (Last Hour)**
```
Type: Single stat with sparkline
Data: primitive_execution_count
Question: Is the error rate increasing?

Query:
sum(rate(primitive_execution_count{execution_status="error"}[1h])) /
sum(rate(primitive_execution_count[1h])) * 100

Alert threshold: > 5%
```

---

### Tab 2: Workflows

**Panel 1: Workflow Execution Timeline**
```
Type: Gantt chart / Flame graph
Data: Traces from Jaeger
Question: What's the timeline of my workflow execution?

Visualization:
- X-axis: Time
- Y-axis: Span hierarchy
- Bars: Span duration (colored by primitive type)
- Annotations: Cache hits, retries, errors
```

**Panel 2: Workflow Performance (Top N)**
```
Type: Bar chart (horizontal)
Data: primitive_execution_duration
Question: Which workflows are slowest?

Query (P95):
topk(10, histogram_quantile(
    0.95,
    sum by (workflow_name, le) (
        primitive_execution_duration_bucket{primitive_type="sequential"}
    )
))

Alternative (P99):
histogram_quantile(0.99, ...)
```

**Panel 3: Workflow Success Rate**
```
Type: Table
Columns: Workflow Name | Executions | Success Rate | P95 Latency | Error Count
Data: primitive_execution_count, primitive_execution_duration

Query:
sum by (workflow_name) (primitive_execution_count) as executions,
(
    sum by (workflow_name) (primitive_execution_count{execution_status="success"}) /
    sum by (workflow_name) (primitive_execution_count)
) * 100 as success_rate,
histogram_quantile(0.95, sum by (workflow_name, le) (primitive_execution_duration_bucket)) as p95_latency,
sum by (workflow_name) (primitive_execution_count{execution_status="error"}) as errors
```

**Panel 4: Workflow Error Drill-Down**
```
Type: Pie chart + Table
Data: primitive_execution_count
Question: What types of errors are occurring?

Pie chart query:
sum by (error_type) (
    primitive_execution_count{execution_status="error"}
)

Table query:
sum by (workflow_name, error_type, error_message) (
    primitive_execution_count{execution_status="error"}
)
order by value desc
limit 20
```

---

### Tab 3: Primitives (Deep Dive)

**Panel 1: Primitive Performance Heatmap**
```
Type: Heatmap
X-axis: Time (5-minute buckets)
Y-axis: Primitive names
Color: P95 latency (green = fast, red = slow)
Question: Which primitives are bottlenecks over time?

Query:
histogram_quantile(
    0.95,
    sum by (primitive_name, le) (
        rate(primitive_execution_duration_bucket[5m])
    )
)
```

**Panel 2: Primitive Execution Count**
```
Type: Stacked area chart
Data: primitive_execution_count
Question: Which primitives are most/least used?

Query:
sum by (primitive_name) (
    rate(primitive_execution_count[5m])
)
```

**Panel 3: Cache Performance**
```
Type: Gauge + Time series
Data: cache_hits, cache_total
Question: Is caching effective?

Hit rate gauge:
(sum(rate(cache_hits[5m])) / sum(rate(cache_total[5m]))) * 100

Time series:
sum(rate(cache_hits[5m])) as "Cache Hits/sec",
sum(rate(cache_total[5m])) as "Total Lookups/sec"
```

**Panel 4: Retry and Fallback Activity**
```
Type: Time series
Data: primitive_execution_count with retry/fallback attributes
Question: How often are recovery mechanisms activating?

Query:
sum(rate(primitive_execution_count{retry_attempt!="0"}[5m])) as "Retry Rate",
sum(rate(primitive_execution_count{fallback_triggered="true"}[5m])) as "Fallback Rate"
```

**Panel 5: Top 5 Slowest Primitives**
```
Type: Bar chart (horizontal)
Data: primitive_execution_duration
Question: Where are my bottlenecks?

Query:
topk(5, histogram_quantile(
    0.95,
    sum by (primitive_name, le) (
        primitive_execution_duration_bucket
    )
))
```

---

### Tab 4: Resources (LLM, Cache, Costs)

**Panel 1: LLM Token Usage**
```
Type: Stacked area chart
Data: llm_tokens_total
Question: Which models are consuming the most tokens?

Query:
sum by (llm_model_name, llm_token_type) (
    rate(llm_tokens_total[5m])
)
```

**Panel 2: LLM Cost Estimate**
```
Type: Single stat with trend
Data: llm_tokens_total + cost mapping
Question: What's my current LLM spend?

Query (hourly):
sum(rate(llm_tokens_total{llm_model_name="gpt-4o"}[1h])) * 3600 * 0.00001 +
sum(rate(llm_tokens_total{llm_model_name="claude-sonnet-3.5"}[1h])) * 3600 * 0.000015

Note: Cost per token varies by model
```

**Panel 3: Cache Hit Rate by Cache Type**
```
Type: Gauge (multi-series)
Data: cache_hits, cache_total
Question: Are all caches performing well?

Query:
(
    sum by (cache_type) (rate(cache_hits[5m])) /
    sum by (cache_type) (rate(cache_total[5m]))
) * 100

Separate gauge for each cache_type (redis, memory, distributed)
```

**Panel 4: Cost Savings from Cache**
```
Type: Single stat
Data: cache_hits + estimated LLM cost
Question: How much am I saving with caching?

Query (estimated savings per hour):
sum(rate(cache_hits{primitive_name="llm_cache"}[1h])) * 3600 * 0.05

Where 0.05 = average cost per LLM call
```

**Panel 5: Top 5 LLM-Calling Primitives**
```
Type: Table
Columns: Primitive | LLM Calls | Tokens | Est. Cost
Data: llm_tokens_total

Query:
sum by (primitive_name) (llm_tokens_total) as tokens,
sum by (primitive_name) (primitive_execution_count{primitive_type="llm"}) as calls,
sum by (primitive_name) (llm_tokens_total) * avg_cost_per_token as est_cost

order by est_cost desc
limit 5
```

---

## Implementation Roadmap

### Phase 1: Semantic Tracing (Week 1-2)

**Tasks:**
1. Update `InstrumentedPrimitive` to use semantic span naming
2. Add all essential span attributes to WorkflowContext
3. Implement span linking via context propagation
4. Add LLM-specific attributes to LLM primitives
5. Add cache-specific attributes to CachePrimitive
6. Test trace continuity end-to-end

**Deliverables:**
- ✅ Unified traces across full workflow
- ✅ Rich span attributes for filtering
- ✅ Service map showing component relationships

**Validation:**
```bash
# Start demo workflow
uv run python examples/observability_demo.py

# Check Jaeger UI (http://localhost:16686)
# - Verify service.name = "tta-workflow-engine"
# - Verify span names follow pattern: primitive.{type}.{action}
# - Verify all attributes present in spans
```

---

### Phase 2: Aggregated Metrics (Week 3-4)

**Tasks:**
1. Implement 7 core metrics in `enhanced_metrics.py`
2. Add metric recording to `InstrumentedPrimitive.execute()`
3. Add connection counter to SequentialPrimitive and ParallelPrimitive
4. Add LLM token counter to LLM primitives
5. Add cache hit rate tracking to CachePrimitive
6. Expose Prometheus endpoint on port 9464

**Deliverables:**
- ✅ Prometheus metrics available at `/metrics`
- ✅ All 7 core metrics collecting data
- ✅ Connection graph data for service map

**Validation:**
```bash
# Start observability stack
./scripts/setup-observability.sh

# Run demo
uv run python examples/observability_demo.py

# Check Prometheus (http://localhost:9090)
# Run sample queries:
primitive_execution_count
histogram_quantile(0.95, primitive_execution_duration_bucket)
primitive_connection_count
```

---

### Phase 3: Dashboard Implementation (Week 5-6)

**Tasks:**
1. Create Grafana dashboard JSON from design specs
2. Import dashboard into Grafana
3. Configure data sources (Prometheus, Jaeger)
4. Set up alerting rules for SLO violations
5. Document dashboard usage
6. Create demo video

**Deliverables:**
- ✅ Complete Grafana dashboard (4 tabs)
- ✅ Alert rules configured
- ✅ User documentation

**Validation:**
```bash
# Access Grafana (http://localhost:3000)
# Username: admin
# Password: admin

# Navigate to "TTA Agent Observability" dashboard
# Verify all 4 tabs render correctly
# Run demo workflow and watch metrics update in real-time
```

---

## Success Metrics

**Technical Success:**
- ✅ 100% trace continuity across workflows
- ✅ <5ms observability overhead per primitive
- ✅ <1% memory overhead for metrics
- ✅ Zero trace data loss

**User Success (Lazy Vibe Coder):**
- ✅ Answer "What's running?" in <5 seconds
- ✅ Identify bottlenecks without trace diving
- ✅ Understand system health at a glance
- ✅ Detect errors before users report them

---

## Appendix: Quick Reference

### Span Naming Examples
```
agent.orchestrator.execute
primitive.sequential.execute
primitive.sequential.step_0
primitive.parallel.execute
primitive.router.route_decision
llm.openai.generate
cache.redis.lookup
recovery.retry.attempt_2
```

### Key Metrics
```
primitive.execution.count
primitive.execution.duration
primitive.connection.count
llm.tokens.total
cache.hit_rate
agent.workflows.active
slo.compliance
```

### Essential Attributes
```
agent.id, agent.type
workflow.id, workflow.name
primitive.name, primitive.type
llm.model_name, llm.cost_usd
cache.hit, cache.savings_usd
error.type, error.recoverable
```

---

**Document Version:** 1.0
**Author:** Staff Observability Architect (AI)
**Date:** November 11, 2025
**Next Review:** After Phase 1 Implementation
