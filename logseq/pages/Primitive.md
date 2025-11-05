# Primitive

**Tag page for all TTA.dev primitives and primitive-related content**

---

## Overview

A **primitive** in TTA.dev is a composable building block for AI workflows. Primitives:
- Have a single, well-defined responsibility
- Can be composed using operators (`>>`, `|`)
- Include built-in observability (tracing, metrics, logging)
- Follow type-safe patterns with generics
- Are production-ready with comprehensive tests

**See:** [[TTA Primitives]], [[WorkflowPrimitive]], [[TTA.dev/Concepts/Composition]]

---

## All Primitives by Category

### Core Workflow Primitives

**Sequential Execution:**
- [[TTA Primitives/SequentialPrimitive]] - Execute steps in sequence
- [[TTA.dev/Patterns/Sequential Workflow]] - Linear data flow patterns

**Parallel Execution:**
- [[TTA Primitives/ParallelPrimitive]] - Execute steps concurrently
- [[TTA.dev/Patterns/Parallel Execution]] - Concurrent processing patterns

**Conditional & Routing:**
- [[TTA Primitives/ConditionalPrimitive]] - Branch based on conditions
- [[TTA Primitives/RouterPrimitive]] - Dynamic routing (LLM selection, etc.)

**Base Classes:**
- [[WorkflowPrimitive]] - Base class for all primitives
- [[InstrumentedPrimitive]] - Base with automatic observability

---

### Recovery Primitives

**Error Handling:**
- [[TTA Primitives/RetryPrimitive]] - Retry with backoff strategies
- [[TTA Primitives/FallbackPrimitive]] - Graceful degradation cascade
- [[TTA Primitives/TimeoutPrimitive]] - Circuit breaker pattern
- [[TTA Primitives/CompensationPrimitive]] - Saga pattern for distributed transactions
- [[TTA Primitives/CircuitBreakerPrimitive]] - Prevent cascade failures

**See:** [[Recovery]], [[TTA.dev/Patterns/Error Handling]]

---

### Performance Primitives

**Optimization:**
- [[TTA Primitives/CachePrimitive]] - LRU cache with TTL
- [[TTA Primitives/MemoryPrimitive]] - Conversational memory with search

**See:** [[Performance]], [[TTA.dev/Patterns/Caching]]

---

### Orchestration Primitives

**Multi-Agent:**
- [[TTA Primitives/DelegationPrimitive]] - Orchestrator → Executor pattern
- [[TTA Primitives/MultiModelWorkflow]] - Multi-model coordination
- [[TTA Primitives/TaskClassifierPrimitive]] - Task classification and routing

**See:** [[TTA.dev/Multi-Agent Patterns]]

---

### Testing Primitives

**Development Tools:**
- [[TTA Primitives/MockPrimitive]] - Testing and mocking workflows

**See:** [[Testing]]

---

### Integration Primitives

**Planned Features:**
- [[SupabasePrimitive]] - Supabase database integration (planned)
- [[SQLitePrimitive]] - SQLite database integration (planned)
- [[PostgreSQLPrimitive]] - PostgreSQL integration (planned)

---

## Pages Tagged with #Primitive

{{query (page-tags [[Primitive]])}}

---

## Primitive Development

### Creating Custom Primitives

**Basic Pattern:**
```python
from tta_dev_primitives import WorkflowPrimitive, WorkflowContext

class CustomPrimitive(WorkflowPrimitive[InputType, OutputType]):
    """Your custom primitive."""

    async def _execute_impl(
        self,
        context: WorkflowContext,
        input_data: InputType
    ) -> OutputType:
        # Your implementation
        return result
```

**With Observability:**
```python
from tta_dev_primitives.observability import InstrumentedPrimitive

class CustomPrimitive(InstrumentedPrimitive[InputType, OutputType]):
    """Primitive with automatic tracing."""

    async def _execute_impl(
        self,
        context: WorkflowContext,
        input_data: InputType
    ) -> OutputType:
        # Automatic spans, metrics, logging
        return result
```

**Resources:**
- [[TTA.dev/How-To/Custom Primitive Development]]
- [[TTA.dev/Templates]] - Primitive templates
- [[Primitive1]], [[Primitive2]] - Generic primitive guides

---

## Composition Patterns

### Sequential Composition (`>>`)
```python
workflow = primitive1 >> primitive2 >> primitive3
```

### Parallel Composition (`|`)
```python
workflow = primitive1 | primitive2 | primitive3
```

### Mixed Composition
```python
workflow = (
    input_processor >>
    (fast_path | quality_path | cached_path) >>
    aggregator
)
```

**See:** [[TTA.dev/Concepts/Composition]]

---

## Primitive Design Principles

### Single Responsibility
- Each primitive does **one thing well**
- Clear input and output types
- No hidden side effects

### Composability
- Combine primitives using operators
- Type-safe composition with generics
- Context propagation through workflow

### Observability
- Automatic tracing with OpenTelemetry
- Prometheus metrics built-in
- Structured logging with correlation IDs

### Testability
- Easy to mock with `MockPrimitive`
- Unit testable in isolation
- Integration testable in workflows

**See:** [[TTA.dev/Architecture/Design Principles]]

---

## Best Practices

### ✅ DO
- Keep primitives small and focused
- Use descriptive names (e.g., `RetryPrimitive`, not `Primitive1`)
- Add type hints for inputs and outputs
- Include docstrings with examples
- Test with both success and error cases
- Use composition over inheritance

### ❌ DON'T
- Create "god" primitives with multiple responsibilities
- Break composition chain with side effects
- Skip error handling
- Modify global state
- Return inconsistent types

**See:** [[TTA.dev/Best Practices]]

---

## Primitive Catalog

**Complete Reference:** [[PRIMITIVES_CATALOG]]

**Quick Links:**
- [[TTA Primitives]] - Main primitives namespace
- [[TTA.dev/Patterns]] - Pattern documentation
- [[TTA.dev/Examples]] - Working examples
- [[Production]] - Production usage patterns

---

## Related Concepts

- [[Workflow]] - Complete workflow patterns
- [[Recovery]] - Error handling strategies
- [[Performance]] - Optimization techniques
- [[Testing]] - Testing strategies
- [[TTA.dev/Concepts/Composition]] - Composition patterns
- [[TTA.dev/Patterns/Error Handling]] - Error handling patterns

---

## Documentation

- [[PRIMITIVES_CATALOG]] - Complete primitive reference
- [[AGENTS]] - Agent instructions for primitives
- [[GETTING_STARTED]] - Getting started guide
- [[README]] - Project overview

---

**Tags:** #primitive #workflow #composability #core-concept #index-page

**Last Updated:** 2025-11-05
**Maintained by:** TTA.dev Team
