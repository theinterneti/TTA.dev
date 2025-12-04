type:: index
status:: active
generated:: 2025-12-04

# TTA.dev Primitives

**Composable workflow building blocks for AI-powered applications.**

## Overview

Primitives are the fundamental units of the TTA.dev workflow system. They can be combined, nested, and orchestrated to build complex AI workflows.

**Source:** `platform/primitives/src/tta_dev_primitives/`

---

## Core Primitives

Foundation primitives for workflow composition:

- [[TTA.dev/Primitives/WorkflowPrimitive]] - Base class for all primitives
- [[TTA.dev/Primitives/SequentialPrimitive]] - Execute primitives in sequence
- [[TTA.dev/Primitives/ParallelPrimitive]] - Execute primitives concurrently
- [[TTA.dev/Primitives/ConditionalPrimitive]] - Conditional branching
- [[TTA.dev/Primitives/RouterPrimitive]] - Dynamic routing based on input
- [[TTA.dev/Primitives/LambdaPrimitive]] - Wrap functions as primitives

---

## Recovery Primitives

Error handling and resilience patterns:

- [[TTA.dev/Primitives/RetryPrimitive]] - Retry with exponential backoff
- [[TTA.dev/Primitives/FallbackPrimitive]] - Graceful degradation
- [[TTA.dev/Primitives/TimeoutPrimitive]] - Timeout enforcement
- [[TTA.dev/Primitives/CircuitBreaker]] - Prevent cascade failures
- [[TTA.dev/Primitives/SagaPrimitive]] - Distributed transactions
- [[TTA.dev/Primitives/CompensationPrimitive]] - Rollback operations

---

## Adaptive Primitives

Self-tuning primitives that learn from runtime behavior:

- [[TTA.dev/Primitives/AdaptivePrimitive]] - Base adaptive class
- [[TTA.dev/Primitives/AdaptiveRetryPrimitive]] - Auto-tuning retry
- [[TTA.dev/Primitives/AdaptiveTimeoutPrimitive]] - Dynamic timeouts
- [[TTA.dev/Primitives/AdaptiveCachePrimitive]] - Smart caching
- [[TTA.dev/Primitives/AdaptiveFallbackPrimitive]] - Adaptive fallbacks

---

## Performance Primitives

Optimization and resource management:

- [[TTA.dev/Primitives/CachePrimitive]] - Result caching
- [[TTA.dev/Primitives/MemoryPrimitive]] - Memory management

---

## Observability Primitives

Monitoring and tracing:

- [[TTA.dev/Primitives/InstrumentedPrimitive]] - OpenTelemetry integration
- [[TTA.dev/Primitives/ObservablePrimitive]] - Metrics collection

---

## Testing Primitives

Development and testing utilities:

- [[TTA.dev/Primitives/MockPrimitive]] - Mock primitives for testing

---

## Orchestration Primitives

Multi-agent coordination:

- [[TTA.dev/Primitives/TaskClassifierPrimitive]] - Route tasks by type
- [[TTA.dev/Primitives/DelegationPrimitive]] - Delegate to sub-agents
- [[TTA.dev/Primitives/KnowledgeBasePrimitive]] - KB-backed decisions

---

## Quick Start

```python
from tta_dev_primitives import (
    SequentialPrimitive,
    RetryPrimitive,
    RetryStrategy,
)

# Compose a resilient workflow
workflow = RetryPrimitive(
    SequentialPrimitive([
        step1,
        step2,
        step3,
    ]),
    strategy=RetryStrategy(max_retries=3)
)

# Execute
result = await workflow.execute(context)
```

---

## Related

- [[TTA.dev/KB Structure]] - How the KB is organized
- [[TTA.dev/Architecture]] - System architecture
