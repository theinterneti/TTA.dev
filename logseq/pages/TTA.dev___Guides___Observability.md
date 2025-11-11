# Observability

type:: [[Guide]]
category:: [[Production]]
difficulty:: [[Intermediate]]
estimated-time:: 35 minutes
target-audience:: [[Developers]], [[DevOps]], [[AI Engineers]]

---

## Overview

- id:: observability-overview
  **Observability** in TTA.dev provides built-in monitoring, tracing, and metrics for all workflow primitives. Every primitive automatically logs execution, creates distributed traces, records metrics, and propagates context - giving you deep visibility into AI workflow behavior without manual instrumentation.

---

## Prerequisites

{{embed ((prerequisites-full))}}

**Should have read:**
- [[TTA.dev/Guides/Agentic Primitives]] - Core concepts
- [[TTA.dev/Guides/Getting Started]] - Basic workflows

**Should understand:**
- WorkflowContext basics
- Async execution
- Why monitoring matters

---

## Three Pillars of Observability

### 1. Logs (What Happened)

- id:: observability-logs

**Structured logging** captures events during execution:

```python
from tta_dev_primitives.observability.logging import get_logger

logger = get_logger(__name__)

logger.info("workflow_started", workflow_id="wf-123", user_id="user-789")
logger.warning("retry_attempted", attempt=2, max_retries=3)
logger.error("operation_failed", error="Connection timeout")
```

**Built into primitives** - every primitive logs automatically:
- Workflow start/end
- Branch selection (ConditionalPrimitive)
- Retry attempts (RetryPrimitive)
- Fallback usage (FallbackPrimitive)
- Cache hits/misses (CachePrimitive)

### 2. Traces (How It Flowed)

- id:: observability-traces

**Distributed tracing** shows execution flow:

- Parent-child span relationships
- Duration of each operation
- Which primitives executed
- Where time was spent

**OpenTelemetry integration** - works with Jaeger, Zipkin, Datadog:

```python
from opentelemetry import trace

tracer = trace.get_tracer(__name__)

with tracer.start_as_current_span("llm_call") as span:
    span.set_attribute("model", "gpt-4")
    span.set_attribute("tokens", 150)
    result = await llm.execute(prompt, context)
```

### 3. Metrics (How Many, How Fast)

- id:: observability-metrics

**Prometheus-compatible metrics**:

- **Counters** - How many times executed
- **Gauges** - Current values
- **Histograms** - Distribution of durations
- **Summaries** - Percentiles (P50, P95, P99)

**Automatic metrics** for all primitives:
- Execution count
- Success/failure rate
- Duration (P50, P95, P99)
- Cache hit rate
- Retry count
- Timeout rate

---

## WorkflowContext: The Observability Carrier

### Creating Context

```python
from tta_dev_primitives import WorkflowContext
import uuid

context = WorkflowContext(
    workflow_id="user-signup-flow",
    session_id="session-abc123",
    correlation_id=str(uuid.uuid4()),
    metadata={
        "user_id": "user-789",
        "request_type": "signup",
        "environment": "production"
    },
    tags={
        "version": "2.1.0",
        "region": "us-west-2"
    }
)

result = await workflow.execute(input_data, context)
```

### Key Context Fields

**Core Identifiers:**
- `workflow_id` - Identifies the workflow type
- `session_id` - Groups related workflows (user session)
- `correlation_id` - Unique ID for this execution (auto-generated)

**Tracing (W3C Trace Context):**
- `trace_id` - OpenTelemetry trace ID
- `span_id` - Current span ID
- `parent_span_id` - Parent span ID
- `trace_flags` - Sampled flag

**Observability Metadata:**
- `metadata` - Custom key-value data
- `tags` - Labels for filtering/grouping
- `baggage` - W3C Baggage for cross-service propagation

**Timing:**
- `start_time` - When workflow started
- `checkpoints` - List of timing checkpoints

---

## Using Checkpoints

### Recording Checkpoints

```python
from tta_dev_primitives import WorkflowPrimitive, WorkflowContext

class DataProcessor(WorkflowPrimitive[dict, dict]):
    async def execute(self, input_data: dict, context: WorkflowContext) -> dict:
        context.checkpoint("processing.start")

        # Step 1: Validate
        context.checkpoint("validation.start")
        validated = validate_data(input_data)
        context.checkpoint("validation.complete")

        # Step 2: Transform
        context.checkpoint("transform.start")
        transformed = transform_data(validated)
        context.checkpoint("transform.complete")

        # Step 3: Enrich
        context.checkpoint("enrichment.start")
        enriched = enrich_data(transformed)
        context.checkpoint("enrichment.complete")

        context.checkpoint("processing.complete")

        return enriched
```

### Analyzing Checkpoints

```python
# Execute workflow
result = await workflow.execute(input_data, context)

# Analyze timing
print(f"Total time: {context.elapsed_ms():.2f}ms")

for name, timestamp in context.checkpoints:
    print(f"Checkpoint: {name} at {timestamp}")

# Calculate stage durations
checkpoints = dict(context.checkpoints)
validation_duration = (checkpoints["validation.complete"] - checkpoints["validation.start"]) * 1000
transform_duration = (checkpoints["transform.complete"] - checkpoints["transform.start"]) * 1000
enrichment_duration = (checkpoints["enrichment.complete"] - checkpoints["enrichment.start"]) * 1000

print(f"Validation: {validation_duration:.2f}ms")
print(f"Transform: {transform_duration:.2f}ms")
print(f"Enrichment: {enrichment_duration:.2f}ms")
```

---

## OpenTelemetry Integration

### Setup

```python
from observability_integration import initialize_observability

# Initialize OpenTelemetry + Prometheus
success = initialize_observability(
    service_name="my-ai-app",
    enable_prometheus=True,
    prometheus_port=9464
)

if success:
    print("✅ Observability initialized")
    print("📊 Metrics available at http://localhost:9464/metrics")
else:
    print("⚠️ OpenTelemetry not available, using fallback logging")
```

### Span Attributes from Context

```python
from opentelemetry import trace

class TracedPrimitive(WorkflowPrimitive[str, str]):
    async def execute(self, input_data: str, context: WorkflowContext) -> str:
        tracer = trace.get_tracer(__name__)

        with tracer.start_as_current_span("custom_operation") as span:
            # Add workflow context as span attributes
            for key, value in context.to_otel_context().items():
                span.set_attribute(key, value)

            # Add custom attributes
            span.set_attribute("input_length", len(input_data))
            span.set_attribute("operation_type", "text_processing")

            # Do work
            result = process_text(input_data)

            # Record events
            span.add_event("processing_complete", {
                "output_length": len(result)
            })

            return result
```

### Child Context for Nested Workflows

```python
# Parent workflow
parent_context = WorkflowContext(
    workflow_id="main-workflow",
    correlation_id="req-12345"
)

# Execute parent workflow
result = await parent_workflow.execute(data, parent_context)

# Create child context for sub-workflow
child_context = parent_context.create_child_context()

# Child inherits trace context
assert child_context.trace_id == parent_context.trace_id
assert child_context.correlation_id == parent_context.correlation_id
assert child_context.parent_span_id == parent_context.span_id

# Execute sub-workflow with child context
sub_result = await sub_workflow.execute(data, child_context)
```

---

## Monitoring Metrics

### Key Metrics to Track

**Execution Metrics:**
- `workflow_executions_total` - Total execution count
- `workflow_execution_duration_seconds` - Execution time histogram
- `workflow_execution_success_total` - Success count
- `workflow_execution_failure_total` - Failure count

**Primitive-Specific Metrics:**
- `cache_hits_total` - Cache hit count
- `cache_misses_total` - Cache miss count
- `retry_attempts_total` - Retry attempt count
- `fallback_used_total` - Fallback usage count
- `timeout_exceeded_total` - Timeout count

### Accessing Metrics

```python
from observability_integration.primitives import RouterPrimitive

# Router with automatic metrics
router = RouterPrimitive(
    routes={"fast": llm1, "quality": llm2},
    route_selector=select_model
)

# Metrics automatically recorded:
# - router_executions_total{route="fast"}
# - router_executions_total{route="quality"}
# - router_execution_duration_seconds
```

### Prometheus Queries

```promql
# Average execution time (last 5 minutes)
rate(workflow_execution_duration_seconds_sum[5m]) /
rate(workflow_execution_duration_seconds_count[5m])

# Success rate
sum(rate(workflow_execution_success_total[5m])) /
sum(rate(workflow_executions_total[5m])) * 100

# Cache hit rate
sum(rate(cache_hits_total[5m])) /
(sum(rate(cache_hits_total[5m])) + sum(rate(cache_misses_total[5m]))) * 100

# P95 latency
histogram_quantile(0.95, rate(workflow_execution_duration_seconds_bucket[5m]))
```

---

## Real-World Example: Production Monitoring

```python
from tta_dev_primitives import SequentialPrimitive
from tta_dev_primitives.recovery import RetryPrimitive, FallbackPrimitive, TimeoutPrimitive
from tta_dev_primitives.performance import CachePrimitive
from observability_integration import initialize_observability
import uuid

# Initialize observability
initialize_observability(
    service_name="content-generation-api",
    enable_prometheus=True
)

# Build workflow with observability
class ContentGenerator(WorkflowPrimitive[dict, dict]):
    async def execute(self, input_data: dict, context: WorkflowContext) -> dict:
        # Checkpoint: Start
        context.checkpoint("content_generation.start")

        # Step 1: Safety check
        context.checkpoint("safety_check.start")
        safety_result = await self.check_safety(input_data, context)
        context.checkpoint("safety_check.complete")

        if not safety_result["is_safe"]:
            logger.warning(
                "content_blocked",
                reason=safety_result["reason"],
                workflow_id=context.workflow_id
            )
            return {"blocked": True, "reason": safety_result["reason"]}

        # Step 2: Generate content
        context.checkpoint("llm_generation.start")
        content = await self.generate_content(input_data, context)
        context.checkpoint("llm_generation.complete")

        # Step 3: Post-process
        context.checkpoint("post_process.start")
        formatted = await self.format_content(content, context)
        context.checkpoint("post_process.complete")

        context.checkpoint("content_generation.complete")

        # Log success
        logger.info(
            "content_generated",
            workflow_id=context.workflow_id,
            content_length=len(formatted["text"]),
            duration_ms=context.elapsed_ms()
        )

        return formatted

# Wrap with resilience primitives
generator = ContentGenerator()

# Layer 1: Cache (1 hour)
cached_generator = CachePrimitive(generator, ttl_seconds=3600)

# Layer 2: Timeout (30 seconds)
timeout_generator = TimeoutPrimitive(cached_generator, timeout_seconds=30.0)

# Layer 3: Retry (3 attempts)
retry_generator = RetryPrimitive(timeout_generator, max_retries=3)

# Layer 4: Fallback (simple response)
simple_generator = LambdaPrimitive(lambda data, ctx: {
    "text": "Content unavailable at this time.",
    "fallback": True
})

resilient_generator = FallbackPrimitive(
    primary=retry_generator,
    fallbacks=[simple_generator]
)

# Execute with full observability
async def handle_request(user_input: dict) -> dict:
    # Create context with rich metadata
    context = WorkflowContext(
        workflow_id="content-generation",
        session_id=user_input.get("session_id"),
        correlation_id=str(uuid.uuid4()),
        metadata={
            "user_id": user_input.get("user_id"),
            "request_type": "content_generation",
            "prompt_length": len(user_input.get("prompt", ""))
        },
        tags={
            "environment": "production",
            "version": "2.1.0",
            "region": "us-west-2"
        }
    )

    # Execute
    result = await resilient_generator.execute(user_input, context)

    # Log metrics
    print(f"✅ Request completed in {context.elapsed_ms():.2f}ms")
    print(f"📊 Checkpoints: {len(context.checkpoints)}")
    print(f"🔍 Correlation ID: {context.correlation_id}")

    return result
```

---

## Dashboards and Alerting

### Grafana Dashboard Queries

**Request Rate:**
```promql
sum(rate(workflow_executions_total{workflow_id="content-generation"}[5m]))
```

**Error Rate:**
```promql
sum(rate(workflow_execution_failure_total[5m])) /
sum(rate(workflow_executions_total[5m])) * 100
```

**Latency Percentiles:**
```promql
histogram_quantile(0.50, rate(workflow_execution_duration_seconds_bucket[5m]))  # P50
histogram_quantile(0.95, rate(workflow_execution_duration_seconds_bucket[5m]))  # P95
histogram_quantile(0.99, rate(workflow_execution_duration_seconds_bucket[5m]))  # P99
```

**Cache Effectiveness:**
```promql
sum(rate(cache_hits_total[5m])) /
(sum(rate(cache_hits_total[5m])) + sum(rate(cache_misses_total[5m]))) * 100
```

### Alert Rules

```yaml
# Alert if error rate > 5%
- alert: HighErrorRate
  expr: |
    sum(rate(workflow_execution_failure_total[5m])) /
    sum(rate(workflow_executions_total[5m])) * 100 > 5
  for: 5m
  annotations:
    summary: "High error rate in workflows"

# Alert if P95 latency > 2 seconds
- alert: HighLatency
  expr: |
    histogram_quantile(0.95, rate(workflow_execution_duration_seconds_bucket[5m])) > 2
  for: 5m
  annotations:
    summary: "P95 latency above 2 seconds"

# Alert if cache hit rate < 30%
- alert: LowCacheHitRate
  expr: |
    sum(rate(cache_hits_total[5m])) /
    (sum(rate(cache_hits_total[5m])) + sum(rate(cache_misses_total[5m]))) * 100 < 30
  for: 10m
  annotations:
    summary: "Cache hit rate below 30%"
```

---

## Best Practices

### Context Creation

✅ **Always create context** for workflow execution
✅ **Use unique correlation IDs** for request tracking
✅ **Add relevant metadata** (user_id, request_type, etc.)
✅ **Use tags for filtering** (environment, version, region)
✅ **Set workflow_id** for grouping similar workflows

### Logging

✅ **Use structured logging** (key-value pairs, not strings)
✅ **Log at appropriate levels** (info, warning, error)
✅ **Include correlation_id** in all logs
✅ **Log business events** (not just technical events)
✅ **Avoid logging sensitive data** (PII, secrets)

### Tracing

✅ **Create spans for key operations** (LLM calls, DB queries)
✅ **Add relevant attributes** (model name, query type)
✅ **Record events for milestones** (cache hit, retry attempt)
✅ **Use child contexts** for nested workflows
✅ **Sample appropriately** (100% in dev, 10% in prod)

### Metrics

✅ **Monitor Golden Signals** (latency, errors, traffic, saturation)
✅ **Track business metrics** (cost per request, tokens used)
✅ **Set SLOs** (99.9% uptime, P95 < 2s)
✅ **Alert on anomalies** (sudden spike in errors)
✅ **Use dashboards** (Grafana for visualization)

---

## Troubleshooting with Observability

### Scenario 1: Slow Requests

**Symptoms:** P95 latency increased from 500ms to 2s

**Investigation:**
1. Check checkpoint timing in logs
2. Identify slowest stage
3. Look at span durations in traces
4. Check for cache misses (cache hit rate dropped?)

**Resolution:** Increase cache TTL or optimize slow operation

### Scenario 2: High Error Rate

**Symptoms:** Error rate jumped from 1% to 15%

**Investigation:**
1. Check error logs for common patterns
2. Filter by correlation_id to see full request flow
3. Check retry metrics (retries exhausted?)
4. Check timeout metrics (operations timing out?)

**Resolution:** Adjust timeout, add fallback, or fix underlying service

### Scenario 3: Cost Spike

**Symptoms:** LLM costs doubled overnight

**Investigation:**
1. Check cache hit rate (cache expired or misconfigured?)
2. Check router metrics (routing to expensive model?)
3. Check request volume (sudden traffic increase?)
4. Look at token usage per request

**Resolution:** Fix cache configuration or adjust router logic

---

## Next Steps

- **Optimize costs:** [[TTA.dev/Guides/Cost Optimization]]
- **Test workflows:** [[TTA.dev/Guides/Testing Workflows]]
- **Handle errors:** [[TTA.dev/Guides/Error Handling Patterns]]

---

## Related Content

### Observability Primitives

{{query (page-property package [[tta-observability-integration]])}}

### Essential Guides

- [[TTA.dev/Guides/Agentic Primitives]] - Core concepts
- [[TTA.dev/Guides/Workflow Composition]] - Building workflows
- [[TTA.dev/Guides/Error Handling Patterns]] - Recovery strategies

---

## Key Takeaways

1. **Three pillars:** Logs (what), Traces (how), Metrics (how many/fast)
2. **WorkflowContext:** Carrier for observability data
3. **Checkpoints:** Fine-grained timing analysis
4. **OpenTelemetry:** Industry-standard distributed tracing
5. **Prometheus:** Metrics for monitoring and alerting
6. **Built-in:** Primitives automatically instrumented

---

**Created:** [[2025-10-30]]
**Last Updated:** [[2025-10-30]]
**Estimated Time:** 35 minutes
**Difficulty:** [[Intermediate]]

- [[Project Hub]]