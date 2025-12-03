# tta-dev-primitives

**Core workflow primitives and composition patterns for TTA.dev.**

## Overview

The tta-dev-primitives package is the foundation of TTA.dev, providing composable primitives for building reliable AI workflows.

**Package:** `platform/primitives/`

## Installation

```bash
# From source (current)
cd platform/primitives
uv sync

# From PyPI (when published)
pip install tta-dev-primitives
```

## Quick Start

```python
from tta_dev_primitives import SequentialPrimitive, WorkflowContext
from tta_dev_primitives.performance import CachePrimitive
from tta_dev_primitives.recovery import RetryPrimitive

# Compose workflow with operators
workflow = (
    CachePrimitive(ttl=3600) >>
    RetryPrimitive(your_llm_call, max_retries=3) >>
    format_response
)

# Execute
context = WorkflowContext(correlation_id="req-123")
result = await workflow.execute(input_data, context)
```

## Core Primitives

### Composition Primitives

- [[SequentialPrimitive]] - Sequential execution (`>>` operator)
- [[ParallelPrimitive]] - Parallel execution (`|` operator)
- [[ConditionalPrimitive]] - If/else branching
- [[RouterPrimitive]] - Dynamic routing to multiple destinations

### Recovery Primitives

- [[RetryPrimitive]] - Retry with exponential backoff
- [[FallbackPrimitive]] - Graceful degradation cascade
- [[TimeoutPrimitive]] - Circuit breaker with timeout
- [[CompensationPrimitive]] - Saga pattern for rollback
- [[CircuitBreakerPrimitive]] - Circuit breaker pattern

### Performance Primitives

- [[CachePrimitive]] - LRU cache with TTL (40-60% cost reduction)
- [[MemoryPrimitive]] - Conversational memory with search

### Testing Primitives

- [[MockPrimitive]] - Mock primitives for testing

### Base Classes

- [[WorkflowPrimitive]] - Base class for all primitives
- [[InstrumentedPrimitive]] - Automatic observability

## Key Features

### 1. Composability

Use operators for intuitive workflow composition:

```python
# Sequential: >>
workflow = step1 >> step2 >> step3

# Parallel: |
workflow = branch1 | branch2 | branch3

# Mixed
workflow = (
    input_processor >>
    (fast_path | slow_path | cached_path) >>
    aggregator
)
```

### 2. Type Safety

Full type hints with generics:

```python
from tta_dev_primitives import WorkflowPrimitive

class MyPrimitive(WorkflowPrimitive[InputType, OutputType]):
    async def _execute_impl(
        self,
        input_data: InputType,
        context: WorkflowContext
    ) -> OutputType:
        # Type-checked by pyright/mypy
        return process(input_data)
```

### 3. Automatic Observability

Every primitive has built-in:
- OpenTelemetry tracing
- Prometheus metrics
- Structured logging
- Context propagation

### 4. Recovery Patterns

Built-in primitives for resilience:

```python
from tta_dev_primitives.recovery import (
    RetryPrimitive,
    FallbackPrimitive,
    TimeoutPrimitive
)

# Layered recovery
reliable_workflow = (
    TimeoutPrimitive(timeout=30) >>
    RetryPrimitive(max_retries=3) >>
    FallbackPrimitive(primary=api, fallbacks=[backup, cache])
)
```

## Package Structure

```
platform/primitives/
├── src/tta_dev_primitives/
│   ├── core/              # Core composition primitives
│   │   ├── base.py       # WorkflowPrimitive
│   │   ├── sequential.py
│   │   ├── parallel.py
│   │   ├── conditional.py
│   │   └── routing.py
│   ├── recovery/          # Recovery primitives
│   │   ├── retry.py
│   │   ├── fallback.py
│   │   ├── timeout.py
│   │   ├── compensation.py
│   │   └── circuit_breaker.py
│   ├── performance/       # Performance primitives
│   │   ├── cache.py
│   │   └── memory.py
│   ├── observability/     # Observability base
│   │   └── instrumented_primitive.py
│   └── testing/           # Testing utilities
│       └── mock_primitive.py
├── tests/                 # Comprehensive test suite
├── examples/              # Working code examples
├── README.md
└── pyproject.toml
```

## Examples

### RAG Workflow

```python
from tta_dev_primitives import SequentialPrimitive
from tta_dev_primitives.performance import CachePrimitive
from tta_dev_primitives.recovery import RetryPrimitive

rag_workflow = (
    CachePrimitive(ttl=3600) >>
    retrieve_documents >>
    rerank_results >>
    RetryPrimitive(generate_response, max_retries=3) >>
    format_output
)
```

**Full example:** `examples/rag_workflow.py`

### Multi-Agent Coordination

```python
from tta_dev_primitives import ParallelPrimitive, RouterPrimitive

multi_agent = (
    classify_task >>
    RouterPrimitive(routes={
        "simple": fast_agent,
        "complex": expert_agent,
        "research": research_agent
    }) >>
    validate_output
)
```

**Full example:** `examples/multi_agent_workflow.py`

### Cost Optimization

```python
from tta_dev_primitives.performance import CachePrimitive
from tta_dev_primitives.core import RouterPrimitive

# 30-40% cache savings + 20-30% router savings = 60-80% total
cost_optimized = (
    CachePrimitive(ttl=3600) >>
    RouterPrimitive(tier="balanced") >>
    process_response
)
```

**Full example:** `examples/cost_tracking_workflow.py`

## Testing

### Unit Tests

```python
from tta_dev_primitives.testing import MockPrimitive
import pytest

@pytest.mark.asyncio
async def test_workflow():
    mock_llm = MockPrimitive(return_value={"output": "test"})
    workflow = step1 >> mock_llm >> step3

    result = await workflow.execute(input_data, context)
    assert mock_llm.call_count == 1
```

### Running Tests

```bash
# All tests
cd platform/primitives
uv run pytest -v

# With coverage
uv run pytest --cov=src --cov-report=html

# Specific test
uv run pytest tests/test_sequential.py -v
```

## Documentation

### Main Documentation
- [[PRIMITIVES CATALOG]] - Complete primitive reference
- [[GETTING STARTED]] - Quick start guide
- [[TTA.dev/Examples]] - Working examples

### Package Documentation
- Package README: `platform/primitives/README.md`
- Agent Instructions: `platform/primitives/AGENTS.md`
- API Docs: Generated from docstrings

## Development

### Adding New Primitives

1. **Create primitive class** extending `WorkflowPrimitive[TInput, TOutput]`
2. **Implement** `_execute_impl()` method
3. **Add tests** achieving 100% coverage
4. **Create examples** showing real usage
5. **Update documentation** in README and catalog

### Code Quality Standards

- ✅ 100% test coverage required
- ✅ Full type hints (pyright strict mode)
- ✅ Comprehensive docstrings
- ✅ Working examples for all features
- ✅ Ruff formatting and linting

## Related Packages

- [[tta-observability-integration]] - Enhanced observability
- [[universal-agent-context]] - Agent coordination
- [[Package]] - All packages overview

## External Resources

- Repository: <https://github.com/theinterneti/TTA.dev>
- Examples: `platform/primitives/examples/`
- Tests: `platform/primitives/tests/`

## Tags

package:: tta-dev-primitives
type:: core
feature:: composition
feature:: recovery
feature:: performance
