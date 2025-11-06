# TTA.dev/Templates

**Reusable templates for TTA.dev development**

---

## Overview

This namespace contains templates for common TTA.dev development tasks. Templates provide starting points for creating primitives, workflows, tests, and documentation.

**Purpose:** Accelerate development with proven patterns
**Categories:** Primitives, Workflows, Tests, Documentation, Configuration

---

## Available Templates

### Primitive Templates

| Template | Purpose | Location |
|----------|---------|----------|
| [[Basic Primitive Template]] | Simple custom primitive | Creating new primitives |
| [[Instrumented Primitive Template]] | Primitive with observability | Adding metrics/tracing |
| [[Async Primitive Template]] | Asynchronous primitive | Async operations |
| [[Configurable Primitive Template]] | Primitive with config | Parameterized primitives |

### Workflow Templates

| Template | Purpose | Location |
|----------|---------|----------|
| [[Sequential Workflow Template]] | Linear workflow | Sequential processing |
| [[Parallel Workflow Template]] | Concurrent workflow | Parallel processing |
| [[RAG Workflow Template]] | RAG pipeline | Document retrieval |
| [[Multi-Agent Workflow Template]] | Agent coordination | Multi-agent systems |

### Testing Templates

| Template | Purpose | Location |
|----------|---------|----------|
| [[Unit Test Template]] | Unit test structure | Testing primitives |
| [[Integration Test Template]] | Integration testing | Testing workflows |
| [[Mock Test Template]] | Using mocks | Testing with mocks |
| [[Async Test Template]] | Async testing | Testing async code |

### Documentation Templates

| Template | Purpose | Location |
|----------|---------|----------|
| [[Primitive Documentation Template]] | Document primitive | API documentation |
| [[Workflow Documentation Template]] | Document workflow | Usage guides |
| [[README Template]] | Package README | Package documentation |
| [[Example Template]] | Code example | Example documentation |

---

## Quick Start Templates

### 1. Basic Custom Primitive

```python
"""
Template: Basic Custom Primitive
Purpose: Simple primitive with single responsibility
"""

from tta_dev_primitives import WorkflowPrimitive, WorkflowContext

class MyCustomPrimitive(WorkflowPrimitive[TInput, TOutput]):
    """
    [Description of what this primitive does]

    Args:
        config_param: [Description]

    Example:
        >>> primitive = MyCustomPrimitive(config_param="value")
        >>> result = await primitive.execute(input_data, context)
    """

    def __init__(self, config_param: str = "default"):
        super().__init__()
        self.config_param = config_param

    async def _execute_impl(
        self,
        data: TInput,
        context: WorkflowContext
    ) -> TOutput:
        """
        Execute the primitive logic.

        Args:
            data: Input data
            context: Workflow context

        Returns:
            Processed output
        """
        # TODO: Implement your logic here
        result = self._process(data)
        return result

    def _process(self, data: TInput) -> TOutput:
        """Helper method for processing."""
        # TODO: Implement processing
        pass
```

### 2. Sequential Workflow Template

```python
"""
Template: Sequential Workflow
Purpose: Chain operations in sequence
"""

from tta_dev_primitives import WorkflowContext

async def create_sequential_workflow():
    """
    Create a sequential workflow.

    Returns:
        Composed workflow
    """

    # Step 1: Input validation
    validate = ValidationPrimitive()

    # Step 2: Main processing
    process = ProcessingPrimitive()

    # Step 3: Output formatting
    format_output = FormattingPrimitive()

    # Compose sequentially
    workflow = validate >> process >> format_output

    return workflow

# Usage
workflow = await create_sequential_workflow()
result = await workflow.execute(input_data, WorkflowContext())
```

### 3. Parallel Workflow Template

```python
"""
Template: Parallel Workflow
Purpose: Execute operations concurrently
"""

from tta_dev_primitives import ParallelPrimitive, WorkflowContext

async def create_parallel_workflow():
    """
    Create a parallel workflow.

    Returns:
        Composed workflow
    """

    # Define parallel branches
    branch1 = Branch1Primitive()
    branch2 = Branch2Primitive()
    branch3 = Branch3Primitive()

    # Compose in parallel
    parallel = branch1 | branch2 | branch3

    # Optional: Add aggregation
    aggregate = AggregationPrimitive()
    workflow = parallel >> aggregate

    return workflow

# Usage
workflow = await create_parallel_workflow()
results = await workflow.execute(input_data, WorkflowContext())
```

### 4. Unit Test Template

```python
"""
Template: Unit Test
Purpose: Test primitive in isolation
"""

import pytest
from tta_dev_primitives import WorkflowContext

@pytest.mark.asyncio
async def test_primitive_success_case():
    """Test successful execution."""

    # Arrange
    primitive = MyCustomPrimitive()
    context = WorkflowContext(workflow_id="test")
    input_data = {"key": "value"}

    # Act
    result = await primitive.execute(input_data, context)

    # Assert
    assert result["status"] == "success"
    assert "data" in result

@pytest.mark.asyncio
async def test_primitive_error_case():
    """Test error handling."""

    primitive = MyCustomPrimitive()
    context = WorkflowContext(workflow_id="test")

    with pytest.raises(ValueError):
        await primitive.execute(None, context)

@pytest.mark.asyncio
async def test_primitive_with_mock():
    """Test with mocked dependencies."""

    from tta_dev_primitives.testing import MockPrimitive

    # Mock dependency
    mock_dep = MockPrimitive(return_value={"mocked": True})

    # Create primitive with mock
    primitive = MyCustomPrimitive(dependency=mock_dep)

    result = await primitive.execute({"test": "data"}, WorkflowContext())

    assert mock_dep.call_count == 1
    assert result["mocked"]
```

---

## Template Categories

### 1. Primitive Development

**Basic Primitive:**
- Single responsibility
- Clear input/output types
- Minimal configuration

**Instrumented Primitive:**
- Automatic tracing
- Metrics collection
- Structured logging

**Recovery Primitive:**
- Error handling
- Retry logic
- Fallback behavior

**Performance Primitive:**
- Caching
- Batching
- Optimization

### 2. Workflow Patterns

**Sequential Pattern:**
- Linear data flow
- Step-by-step processing
- Clear dependencies

**Parallel Pattern:**
- Concurrent execution
- Independent branches
- Result aggregation

**Conditional Pattern:**
- Dynamic branching
- Route selection
- Context-aware logic

**Hybrid Pattern:**
- Mixed sequential/parallel
- Complex workflows
- Multi-stage processing

### 3. Testing Patterns

**Unit Testing:**
- Isolated testing
- Mock dependencies
- Edge case coverage

**Integration Testing:**
- Component interaction
- Workflow validation
- End-to-end scenarios

**Performance Testing:**
- Latency measurement
- Throughput testing
- Resource usage

**Error Testing:**
- Failure scenarios
- Recovery validation
- Edge cases

### 4. Documentation Patterns

**API Documentation:**
- Class docstrings
- Method signatures
- Usage examples

**Usage Guides:**
- Step-by-step tutorials
- Code examples
- Best practices

**Architecture Docs:**
- Design decisions
- Component relationships
- Data flow diagrams

---

## Using Templates

### 1. Copy and Customize

```bash
# Copy template file
cp templates/basic_primitive_template.py my_primitive.py

# Customize for your use case
# - Replace MyCustomPrimitive with your class name
# - Implement _execute_impl logic
# - Add tests
```

### 2. Template Variables

Common variables to replace:

| Variable | Replace With | Example |
|----------|--------------|---------|
| `MyCustomPrimitive` | Your class name | `TextAnalysisPrimitive` |
| `TInput` | Input type | `str`, `dict` |
| `TOutput` | Output type | `dict`, `list` |
| `config_param` | Config name | `model_name`, `timeout` |
| `[Description]` | Your description | Actual documentation |

### 3. Template Checklist

After using a template, verify:

- [ ] Class name updated
- [ ] Type hints correct
- [ ] Docstrings complete
- [ ] Logic implemented
- [ ] Tests added
- [ ] Examples provided
- [ ] Documentation updated

---

## Template Best Practices

### 1. Start with Simple Template

```python
# ✅ Good: Start simple
class SimplePrimitive(WorkflowPrimitive[str, str]):
    async def _execute_impl(self, data: str, context: WorkflowContext) -> str:
        return data.upper()

# ❌ Bad: Over-engineered from start
class ComplexPrimitive(WorkflowPrimitive):
    # Lots of config, inheritance, abstractions...
    pass
```

### 2. Add Features Incrementally

```python
# Step 1: Basic functionality
class MyPrimitive(WorkflowPrimitive):
    async def _execute_impl(self, data, context):
        return self._process(data)

# Step 2: Add configuration
class MyPrimitive(WorkflowPrimitive):
    def __init__(self, mode: str = "fast"):
        self.mode = mode

    async def _execute_impl(self, data, context):
        return self._process(data)

# Step 3: Add metrics
class MyPrimitive(WorkflowPrimitive):
    execution_count = Counter(...)

    async def _execute_impl(self, data, context):
        self.execution_count.inc()
        return self._process(data)
```

### 3. Keep Templates Updated

```python
# Update template when patterns emerge

# v1: Basic template
class BasicTemplate:
    pass

# v2: Add common pattern
class BasicTemplate:
    # Common pattern observed across primitives
    def __init__(self, **kwargs):
        self.config = kwargs

# v3: Add best practice
class BasicTemplate:
    def __init__(self, **kwargs):
        self.config = kwargs
        self._validate_config()  # Now standard
```

---

## Template Library

### Primitive Templates

1. **[[Basic Primitive Template]]** - Minimal primitive
2. **[[Async Primitive Template]]** - Async operations
3. **[[Batch Primitive Template]]** - Batch processing
4. **[[Stream Primitive Template]]** - Streaming data
5. **[[Cached Primitive Template]]** - With caching
6. **[[Retry Primitive Template]]** - With retry logic

### Workflow Templates

1. **[[RAG Workflow Template]]** - Document retrieval
2. **[[Agentic RAG Template]]** - With agents
3. **[[Multi-Agent Template]]** - Agent coordination
4. **[[Streaming Workflow Template]]** - Streaming responses
5. **[[Cost-Aware Template]]** - Budget tracking

### Testing Templates

1. **[[Unit Test Template]]** - Basic unit tests
2. **[[Integration Test Template]]** - Integration tests
3. **[[Mock Test Template]]** - Using mocks
4. **[[Fixture Template]]** - Test fixtures
5. **[[Benchmark Template]]** - Performance tests

### Documentation Templates

1. **[[Primitive Docs Template]]** - API docs
2. **[[README Template]]** - Package README
3. **[[Example Template]]** - Code examples
4. **[[Tutorial Template]]** - Step-by-step guide
5. **[[Architecture Doc Template]]** - Design docs

---

## Related Pages

### Development Resources

- [[TTA.dev/Development/Getting Started]] - Setup guide
- [[TTA.dev/Development/Best Practices]] - Development standards
- [[TTA.dev/Development/Testing Strategy]] - Testing approach

### Pattern Documentation

- [[TTA.dev/Patterns]] - All patterns
- [[TTA.dev/Patterns/Sequential Workflow]] - Sequential patterns
- [[TTA.dev/Patterns/Parallel Execution]] - Parallel patterns

### Example Code

- [[TTA.dev/Examples]] - All examples
- [[TTA.dev/Examples/Basic Workflow]] - Simple examples
- [[TTA.dev/Examples/RAG Workflow]] - RAG examples

---

## Contributing Templates

Want to contribute a template?

1. **Identify pattern:** Common code you've written multiple times
2. **Create template:** Generalize and document
3. **Add examples:** Show usage
4. **Test template:** Verify it works
5. **Submit PR:** Add to template library

See [[Contributing Guide]] for details.

---

**Category:** Templates / Development Resources
**Complexity:** Beginner to Advanced
**Status:** Active - continuously updated
