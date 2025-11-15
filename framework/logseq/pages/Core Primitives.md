# Core Primitives

**Fundamental workflow primitives for composing TTA.dev workflows.**

## Overview

Core Primitives are the foundational building blocks of TTA.dev workflows. They provide essential control flow patterns like sequential execution, parallel execution, and conditional branching.

## Primary Core Primitives

### Composition Primitives
- [[TTA.dev/Primitives/SequentialPrimitive]] - Execute steps in sequence (`>>` operator)
- [[TTA.dev/Primitives/ParallelPrimitive]] - Execute steps concurrently (`|` operator)
- [[TTA.dev/Primitives/ConditionalPrimitive]] - Branch based on conditions

### Base Classes
- [[TTA.dev/Primitives/WorkflowPrimitive]] - Base class for all primitives
- [[TTA.dev/Primitives/InstrumentedPrimitive]] - Base with observability

### Routing
- [[TTA.dev/Primitives/RouterPrimitive]] - Dynamic routing to multiple destinations

## Usage Patterns

### Sequential Workflow
```python
workflow = step1 >> step2 >> step3
result = await workflow.execute(data, context)
```

### Parallel Execution
```python
workflow = task1 | task2 | task3
results = await workflow.execute(data, context)
```

### Mixed Composition
```python
workflow = input >> (fast | slow | cached) >> aggregator
```

## Related Categories

- [[Recovery Patterns]] - Error handling primitives
- [[Performance Primitives]] - Optimization primitives
- [[Orchestration Primitives]] - Multi-agent coordination

## Documentation

- [[PRIMITIVES CATALOG]] - Complete primitive reference
- [[TTA.dev/Guides/Workflow Composition]] - Composition guide
- `packages/tta-dev-primitives/examples/` - Code examples

## Tags

category:: core
type:: primitives

- [[Project Hub]]