type:: [[Learning]]
description:: Structured learning sequences for TTA.dev

# Learning Paths

## Beginner Path

### 1. Getting Started
- [ ] Read [[TTA.dev]] overview
- [ ] Understand what primitives are
- [ ] Run first workflow example

### 2. Core Concepts
- [ ] Learn about [[WorkflowContext]]
- [ ] Understand sequential composition (`>>`)
- [ ] Understand parallel composition (`|`)

### 3. First Workflow
```python
from tta_dev_primitives import WorkflowContext
from tta_dev_primitives.performance import CachePrimitive

workflow = CachePrimitive(ttl=3600) >> process_data
result = await workflow.execute(data, WorkflowContext())
```

## Intermediate Path

### 1. Recovery Patterns
- [ ] Implement [[RetryPrimitive]] for API calls
- [ ] Add [[FallbackPrimitive]] for provider failover
- [ ] Use [[TimeoutPrimitive]] for slow operations

### 2. Performance Optimization
- [ ] Add caching to reduce API costs
- [ ] Implement [[MemoryPrimitive]] for conversations
- [ ] Profile and optimize workflows

### 3. Testing
- [ ] Use [[MockPrimitive]] in tests
- [ ] Write async tests with pytest-asyncio
- [ ] Achieve 80%+ coverage

## Advanced Path

### 1. Custom Primitives
- [ ] Create custom primitive class
- [ ] Implement `_execute` method
- [ ] Add observability hooks

### 2. Orchestration
- [ ] Build multi-model workflows
- [ ] Implement task routing
- [ ] Add delegation patterns

### 3. Production Deployment
- [ ] Configure OpenTelemetry
- [ ] Set up Prometheus metrics
- [ ] Deploy with health checks

## Resources

- [[TTA.dev/Primitives]] - Complete primitives reference
- [[TTA.dev/Architecture]] - System design
- [GETTING_STARTED.md](../GETTING_STARTED.md)
- [PRIMITIVES_CATALOG.md](../PRIMITIVES_CATALOG.md)
