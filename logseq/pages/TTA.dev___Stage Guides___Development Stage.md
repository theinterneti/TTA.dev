# TTA.dev Development Stage Guide

stage:: development
complexity:: intermediate
prerequisites:: [[TTA.dev/Stage Guides/Experimentation Stage]]
next-stage:: [[TTA.dev/Stage Guides/Testing Stage]]
related:: [[TTA.dev/DevOps Studio Architecture]], [[TTA.dev/CI-CD Pipeline]]

Complete guide for feature implementation and development workflows

---

## 🎯 Stage Overview

The **Development Stage** is where validated prototypes from experimentation become production-ready features. This stage focuses on clean implementation, type safety, and architectural consistency.

### Stage Goals

- **Feature Implementation** - Build working, tested features
- **Code Quality** - Maintain high standards and consistency
- **Type Safety** - Ensure 100% type coverage
- **Documentation** - Create comprehensive user and developer docs
- **Integration** - Seamlessly integrate with existing codebase

### Success Criteria

- [ ] All tests passing with 100% coverage
- [ ] Full type annotations and pyright compliance
- [ ] Code formatted with ruff and passes all linting
- [ ] Documentation updated (README, examples, docstrings)
- [ ] Integration tests validate end-to-end workflows

---

## 🛠️ Development Workflow

### 1. Implementation Planning

**Before Starting Development:**

```markdown
## Development Plan Template

### Feature: [Feature Name]
**Package:** tta-dev-primitives | tta-observability-integration | etc.
**Complexity:** simple | moderate | complex
**Estimated Duration:** X days
**Dependencies:** List any blocking dependencies

### Implementation Approach
- [ ] Core implementation strategy
- [ ] Integration points with existing code
- [ ] Testing strategy
- [ ] Documentation plan

### Acceptance Criteria
- [ ] Functional requirements met
- [ ] Performance requirements met
- [ ] Type safety requirements met
- [ ] Documentation complete
```

### 2. Code Implementation

**TTA.dev Development Standards:**

```python
# Example: Implementing a new primitive
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from tta_dev_primitives import WorkflowPrimitive, WorkflowContext

class NewPrimitive(WorkflowPrimitive[InputType, OutputType]):
    """
    Brief description of what this primitive does.

    This primitive implements [specific pattern/behavior].

    Args:
        param1: Description of parameter
        param2: Description of parameter

    Example:
        ```python
        primitive = NewPrimitive(param1="value")
        result = await primitive.execute(data, context)
        ```
    """

    def __init__(
        self,
        param1: str,
        param2: Optional[int] = None,
        **kwargs: Any
    ) -> None:
        super().__init__(**kwargs)
        self.param1 = param1
        self.param2 = param2

    async def _execute_impl(
        self,
        input_data: InputType,
        context: WorkflowContext
    ) -> OutputType:
        """Core implementation with full type safety."""
        # Implementation here
        return output_data
```

### 3. Testing Implementation

**Comprehensive Testing Strategy:**

```python
# Example: Test implementation
import pytest
from tta_dev_primitives.testing import MockPrimitive, create_test_context

class TestNewPrimitive:
    """Comprehensive test suite for NewPrimitive."""

    @pytest.mark.asyncio
    async def test_basic_functionality(self):
        """Test basic primitive execution."""
        primitive = NewPrimitive(param1="test")
        context = create_test_context()

        result = await primitive.execute(test_data, context)

        assert result.property == expected_value

    @pytest.mark.asyncio
    async def test_error_handling(self):
        """Test error scenarios."""
        primitive = NewPrimitive(param1="invalid")
        context = create_test_context()

        with pytest.raises(ExpectedError):
            await primitive.execute(bad_data, context)

    @pytest.mark.asyncio
    async def test_composition(self):
        """Test primitive composition."""
        workflow = primitive1 >> NewPrimitive(param1="test") >> primitive3
        result = await workflow.execute(data, context)

        assert workflow_validates_correctly(result)
```

### 4. Documentation Creation

**Documentation Requirements:**

- **Code Documentation** - Comprehensive docstrings
- **User Documentation** - README updates and examples
- **Developer Documentation** - Architecture and integration notes
- **API Documentation** - Type hints and parameter descriptions

---

## 🏗️ Architecture Integration

### Package Structure

```text
packages/package-name/
├── src/package_name/
│   ├── __init__.py           # Public exports
│   ├── core/                 # Core implementations
│   │   ├── __init__.py
│   │   └── new_primitive.py  # Your implementation
│   ├── types.py              # Type definitions
│   └── exceptions.py         # Custom exceptions
├── tests/
│   ├── conftest.py           # Test configuration
│   ├── test_new_primitive.py # Unit tests
│   └── integration/          # Integration tests
├── examples/
│   └── new_primitive_usage.py # Working examples
├── README.md                 # Package documentation
└── pyproject.toml           # Package configuration
```

### Integration Points

**With TTA.dev Primitives:**

- **Composability** - Must work with >> and | operators
- **Type Safety** - Full generic type support
- **Observability** - Automatic tracing and metrics
- **Testing** - Compatible with MockPrimitive

**With Other Packages:**

- **tta-observability-integration** - Enhanced observability
- **universal-agent-context** - Agent coordination
- **tta-documentation-primitives** - Documentation generation

---

## 🔍 Quality Assurance

### Automated Quality Checks

**Pre-commit Requirements:**

```bash
# Format code
uv run ruff format .

# Fix linting issues
uv run ruff check . --fix

# Type checking
uvx pyright packages/

# Run tests
uv run pytest -v

# Coverage check
uv run pytest --cov=packages --cov-report=term-missing
```

**VS Code Task Integration:**

Use the "✅ Quality Check (All)" task to run all checks:

```json
{
    "label": "✅ Quality Check (All)",
    "type": "shell",
    "command": "echo '=== Formatting ===' && uv run ruff format . && echo '' && echo '=== Linting ===' && uv run ruff check . --fix && echo '' && echo '=== Type Checking ===' && uvx pyright packages/ && echo '' && echo '=== Tests ===' && uv run pytest -v"
}
```

### Code Review Checklist

**Implementation Review:**

- [ ] **Correctness** - Logic is sound and handles edge cases
- [ ] **Performance** - No obvious performance bottlenecks
- [ ] **Security** - No security vulnerabilities introduced
- [ ] **Maintainability** - Code is readable and well-structured

**Architecture Review:**

- [ ] **Consistency** - Follows established patterns
- [ ] **Integration** - Properly integrates with existing components
- [ ] **Extensibility** - Design allows for future enhancements
- [ ] **Documentation** - Architecture decisions are documented

**Quality Review:**

- [ ] **Type Safety** - 100% type coverage
- [ ] **Test Coverage** - 100% line and branch coverage
- [ ] **Documentation** - All public APIs documented
- [ ] **Examples** - Working examples provided

---

## 🧪 Development Tools

### Local Development Environment

**Required Tools:**

- **Python 3.11+** - Modern Python with latest type hints
- **uv** - Package management and virtual environments
- **VS Code** - Primary IDE with extensions
- **Git** - Version control

**VS Code Extensions:**

- **Python + Pylance** - Python language support and type checking
- **Ruff** - Linting and formatting
- **GitHub Copilot** - AI assistance with proper toolsets
- **GitLens** - Git integration and history

### Development Workflow Tools

**Package Development:**

```bash
# Create new feature branch
git checkout -b feature/new-primitive

# Install dependencies
uv sync --all-extras

# Start development
code .

# Use Copilot toolset for development
# @workspace #tta-package-dev
```

**Testing and Validation:**

```bash
# Run fast tests during development
./scripts/test_fast.sh

# Run comprehensive tests before commit
uv run pytest -v

# Check coverage
uv run pytest --cov=packages --cov-report=html
```

---

## 🎭 Development Patterns

### Primitive Development Pattern

**1. Define Types:**

```python
from typing import TypeVar, Generic
from pydantic import BaseModel

class InputModel(BaseModel):
    """Input data model with validation."""
    field1: str
    field2: int

class OutputModel(BaseModel):
    """Output data model with validation."""
    result: str
    metadata: dict[str, Any]
```

**2. Implement Core Logic:**

```python
class BusinessLogicPrimitive(WorkflowPrimitive[InputModel, OutputModel]):
    """Implements specific business logic pattern."""

    async def _execute_impl(
        self,
        input_data: InputModel,
        context: WorkflowContext
    ) -> OutputModel:
        # Core business logic
        processed_data = self._process_data(input_data)

        # Return structured output
        return OutputModel(
            result=processed_data,
            metadata={"processed_at": datetime.utcnow()}
        )
```

**3. Add Observability:**

```python
from tta_dev_primitives.observability import InstrumentedPrimitive

class ObservablePrimitive(InstrumentedPrimitive[InputModel, OutputModel]):
    """Primitive with enhanced observability."""

    async def _execute_impl(
        self,
        input_data: InputModel,
        context: WorkflowContext
    ) -> OutputModel:
        # Automatic span creation and metrics
        with self._tracer.start_as_current_span("business_logic") as span:
            span.set_attribute("input_size", len(input_data.field1))

            result = await self._core_logic(input_data)

            span.set_attribute("output_size", len(result.result))
            return result
```

### Integration Pattern

**Composing with Existing Primitives:**

```python
# Build complex workflows from simple primitives
workflow = (
    InputValidationPrimitive() >>
    NewBusinessLogicPrimitive() >>
    OutputFormattingPrimitive()
)

# With error handling
resilient_workflow = (
    TimeoutPrimitive(workflow, timeout=30) >>
    RetryPrimitive(max_retries=3) >>
    FallbackPrimitive(fallback=default_handler)
)
```

---

## 📊 Performance Considerations

### Optimization Guidelines

**Memory Efficiency:**

- Use generators for large data processing
- Implement proper cleanup in async contexts
- Avoid holding references to large objects
- Use appropriate data structures

**Async Performance:**

- Minimize blocking operations
- Use asyncio.gather() for parallel operations
- Implement proper connection pooling
- Handle async context managers correctly

**Caching Strategy:**

```python
# Use CachePrimitive for expensive operations
cached_operation = CachePrimitive(
    primitive=expensive_llm_call,
    ttl_seconds=3600,
    max_size=1000,
    key_fn=lambda data, ctx: f"{data.user_id}:{hash(data.query)}"
)
```

### Performance Testing

**Benchmark Implementation:**

```python
import time
import asyncio
from statistics import mean, stdev

async def benchmark_primitive():
    """Benchmark primitive performance."""
    primitive = NewPrimitive()
    times = []

    for _ in range(100):
        start = time.perf_counter()
        await primitive.execute(test_data, context)
        times.append(time.perf_counter() - start)

    print(f"Mean: {mean(times):.4f}s")
    print(f"StdDev: {stdev(times):.4f}s")
    print(f"95th percentile: {sorted(times)[95]:.4f}s")
```

---

## 🚀 Deployment Preparation

### Pre-deployment Checklist

**Code Quality:**

- [ ] All quality checks pass
- [ ] Code review completed
- [ ] Documentation updated
- [ ] Examples tested

**Integration Validation:**

- [ ] Integration tests pass
- [ ] Backward compatibility maintained
- [ ] Performance benchmarks meet requirements
- [ ] Security review completed

**Release Preparation:**

- [ ] Version number updated
- [ ] Changelog updated
- [ ] Migration guide created (if needed)
- [ ] Rollback plan documented

### Deployment Strategy

**Staged Rollout:**

1. **Testing Stage** - Deploy to testing environment
2. **Staging Stage** - Deploy to staging with production-like data
3. **Production Stage** - Gradual rollout with monitoring

**Monitoring Setup:**

```python
# Ensure observability is configured
from observability_integration import initialize_observability

initialize_observability(
    service_name="new-feature",
    environment="production",
    enable_prometheus=True
)
```

---

## 🎓 Learning Resources

### Development Best Practices

- **TTA.dev Coding Standards** - [[TTA.dev/Best Practices/Coding Standards]]
- **Type Safety Guide** - [[TTA.dev/Best Practices/Type Safety]]
- **Testing Strategies** - [[TTA.dev/Best Practices/Testing]]
- **Documentation Guidelines** - [[TTA.dev/Best Practices/Documentation]]

### Advanced Patterns

- **Primitive Composition Patterns** - [[TTA Primitives/Composition Patterns]]
- **Error Handling Strategies** - [[TTA Primitives/Error Handling]]
- **Performance Optimization** - [[TTA.dev/Best Practices/Performance]]
- **Observability Integration** - [[TTA.dev/Observability/Integration]]

### Package-Specific Guides

- **tta-dev-primitives** - [[TTA.dev/Packages/tta-dev-primitives]]
- **tta-observability-integration** - [[TTA.dev/Packages/tta-observability-integration]]
- **universal-agent-context** - [[TTA.dev/Packages/universal-agent-context]]

---

## 🔄 Stage Transitions

### From Experimentation

**Transition Criteria:**

- [ ] Prototype validates core assumptions
- [ ] Technical approach is sound
- [ ] Performance requirements can be met
- [ ] Integration strategy is clear

**Handoff Artifacts:**

- Prototype code and experiments
- Research findings and decisions
- Performance benchmarks
- Integration analysis

### To Testing

**Completion Criteria:**

- [ ] Feature implementation complete
- [ ] Unit tests written and passing
- [ ] Code review completed and approved
- [ ] Documentation updated

**Deliverables:**

- Production-ready code
- Comprehensive test suite
- Updated documentation
- Integration examples

---

## 📚 Related Resources

### Stage Guides

- **Previous:** [[TTA.dev/Stage Guides/Experimentation Stage]] - Research and prototyping
- **Next:** [[TTA.dev/Stage Guides/Testing Stage]] - Quality validation
- **Related:** [[TTA.dev/Stage Guides/Staging Stage]], [[TTA.dev/Stage Guides/Production Stage]]

### Architecture Documentation

- [[TTA.dev/DevOps Studio Architecture]] - Complete studio architecture
- [[TTA.dev/Architecture]] - System architecture overview
- [[TTA.dev/CI-CD Pipeline]] - Pipeline configuration

### Development Resources

- [[TTA.dev/Best Practices]] - Development best practices
- [[TTA Primitives]] - Primitive library reference
- [[TTA.dev/Learning Paths]] - Structured learning progression

---

**Last Updated:** November 7, 2025
**Stage Status:** Active
**Next Review:** Monthly

