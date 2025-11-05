# TTA.dev/Primitives

**Complete namespace for all TTA.dev workflow primitives.**

## Overview

This namespace contains documentation for all TTA.dev workflow primitives - the composable building blocks for AI workflows.

## Primitives by Category

### Core Workflow
- [[TTA.dev/Primitives/WorkflowPrimitive]] - Base class for all primitives
- [[TTA.dev/Primitives/SequentialPrimitive]] - Sequential composition (`>>` operator)
- [[TTA.dev/Primitives/ParallelPrimitive]] - Parallel execution (`|` operator)
- [[TTA.dev/Primitives/ConditionalPrimitive]] - Conditional branching
- [[TTA.dev/Primitives/RouterPrimitive]] - Dynamic routing

### Recovery & Resilience
- [[TTA.dev/Primitives/RetryPrimitive]] - Retry with exponential backoff
- [[TTA.dev/Primitives/FallbackPrimitive]] - Graceful degradation
- [[TTA.dev/Primitives/TimeoutPrimitive]] - Circuit breaker pattern
- [[TTA.dev/Primitives/CompensationPrimitive]] - Saga pattern for transactions

### Performance
- [[TTA.dev/Primitives/CachePrimitive]] - LRU cache with TTL
- [[TTA.dev/Primitives/MemoryPrimitive]] - Conversational memory

### Observability
- [[TTA.dev/Primitives/InstrumentedPrimitive]] - Base with automatic observability
- [[TTA.dev/Primitives/ObservablePrimitive]] - Wrapper for adding observability

### Testing
- [[TTA.dev/Primitives/MockPrimitive]] - Testing and mocking

### Orchestration
- [[TTA.dev/Orchestration/DelegationPrimitive]] - Orchestrator-executor pattern
- [[TTA.dev/Orchestration/MultiModelWorkflow]] - Multi-model coordination
- [[TTA.dev/Orchestration/TaskClassifierPrimitive]] - Task routing

## Reference Documentation

- [[PRIMITIVES_CATALOG]] - Complete catalog with examples
- [[Core Primitives]] - Core workflow patterns
- [[Recovery Patterns]] - Error handling strategies
- [[Performance Optimization]] - Performance patterns

## Package Location

**Source:** `packages/tta-dev-primitives/src/tta_dev_primitives/`

## Related Pages

- [[TTA.dev/Packages/tta-dev-primitives]] - Package documentation
- [[GETTING_STARTED]] - Getting started guide
- [[TTA.dev/Examples]] - Working examples

## Tags

namespace:: primitives
type:: reference
