# TTA Workflow Primitives

Production-ready composable workflow primitives for building reliable, observable, and maintainable agent workflows.

## Features

### Core Primitives
- **Composable Workflows**: Build complex workflows from simple primitives
- **Type-Safe Composition**: Generics-based type safety
- **Operator Overloading**: Ergonomic `>>` and `|` operators for chaining

### Observability
- **Distributed Tracing**: OpenTelemetry integration
- **Structured Logging**: Correlation IDs and context
- **Execution Traces**: Complete workflow execution history
- **Metrics Collection**: Performance and success rate tracking

### Error Recovery
- **Retry Strategies**: Exponential backoff with jitter
- **Fallback Mechanisms**: Graceful degradation
- **Compensation Patterns**: Saga pattern support
- **Circuit Breakers**: Prevent cascading failures

### Testing
- **Mock Primitives**: Easy workflow testing
- **Test Fixtures**: Pre-built test utilities
- **Assertion Framework**: Workflow-specific assertions

## Installation

```bash
uv pip install -e packages/tta-workflow-primitives
```

For tracing support:
```bash
uv pip install -e "packages/tta-workflow-primitives[tracing]"
```

## Quick Start

### Basic Composition

```python
from tta_workflow_primitives import WorkflowPrimitive, SequentialPrimitive

# Define primitives
safety_check = SafetyValidationPrimitive()
input_proc = InputProcessingPrimitive()
narrative_gen = NarrativeGenerationPrimitive()

# Compose with >> operator
workflow = safety_check >> input_proc >> narrative_gen

# Execute
result = await workflow.execute(user_input, context)
```

### With Error Recovery

```python
from tta_workflow_primitives.recovery import RetryPrimitive, FallbackStrategy

# Retry with fallback
workflow = (
    safety_check >>
    input_proc >>
    RetryPrimitive(
        narrative_gen,
        max_retries=3,
        strategies=[FallbackStrategy(safe_narrative_gen)]
    )
)
```

### With Observability

```python
from tta_workflow_primitives.observability import ObservablePrimitive

# Wrap primitives for tracing
workflow = (
    ObservablePrimitive(safety_check, "safety") >>
    ObservablePrimitive(input_proc, "input") >>
    ObservablePrimitive(narrative_gen, "narrative")
)

# Automatic tracing, logging, and metrics
result = await workflow.execute(user_input, context)
```

### Parallel Execution

```python
from tta_workflow_primitives import ParallelPrimitive

# Execute in parallel with | operator
parallel = world_build | character_analysis | theme_analysis

# Or explicit
parallel = ParallelPrimitive([world_build, character_analysis, theme_analysis])

workflow = input_proc >> parallel >> narrative_gen
```

### Conditional Branching

```python
from tta_workflow_primitives import ConditionalPrimitive

# Branch based on safety level
workflow = (
    safety_check >>
    ConditionalPrimitive(
        condition=lambda result, ctx: result.safety_level != "blocked",
        then_primitive=standard_narrative,
        else_primitive=safe_narrative
    )
)
```

## Architecture

```
tta_workflow_primitives/
├── core/              # Core primitive abstractions
│   ├── base.py        # WorkflowPrimitive base class
│   ├── sequential.py  # Sequential composition
│   ├── parallel.py    # Parallel composition
│   └── conditional.py # Conditional branching
├── observability/     # Observability features
│   ├── tracing.py     # OpenTelemetry integration
│   ├── logging.py     # Structured logging
│   └── metrics.py     # Metrics collection
├── recovery/          # Error recovery patterns
│   ├── retry.py       # Retry strategies
│   ├── fallback.py    # Fallback mechanisms
│   └── compensation.py # Saga pattern
└── testing/           # Testing utilities
    ├── mocks.py       # Mock primitives
    └── assertions.py  # Test assertions
```

## Testing

```python
from tta_workflow_primitives.testing import MockPrimitive, WorkflowTestCase

async def test_workflow():
    # Create mocks
    mock_safety = MockPrimitive("safety", return_value={"level": "safe"})
    mock_input = MockPrimitive("input", return_value={"intent": "explore"})

    # Build test case
    test = WorkflowTestCase(workflow)
    test.with_mock("safety", mock_safety)
    test.with_mock("input", mock_input)

    # Execute and assert
    result = await test.execute({"user_input": "test"})
    test.assert_primitive_called("safety", times=1)
    test.assert_primitive_called("input", times=1)
```

## Examples

See the [examples](./examples) directory for complete workflow examples:

- `basic_composition.py` - Simple workflow composition
- `error_recovery.py` - Error handling and recovery
- `observability.py` - Tracing and monitoring
- `therapeutic_workflow.py` - Complete therapeutic narrative workflow

## Migration Guide

See [MIGRATION.md](./MIGRATION.md) for migrating existing TTA workflows to use primitives.

## License

Proprietary - TTA Storytelling Platform
