# TTA.dev/Common

type:: [[Reusable Content]]
category:: [[Documentation]]
purpose:: Reusable content blocks for embedding across documentation

This page contains frequently used content that should be embedded (not copied) to maintain a single source of truth.

---

## Installation & Setup

### Prerequisites
- id:: prerequisites-full
  **Prerequisites for TTA.dev Development:**
  - **Python 3.11+** - Required for modern type hints (`str | None` syntax)
  - **uv package manager** - We use `uv`, NOT `pip`
  - **VS Code** (recommended) - With Pylance for type checking
  - **Git** - For version control

### UV Installation
- id:: uv-installation
  ```bash
  # Install uv
  curl -LsSf https://astral.sh/uv/install.sh | sh

  # Verify installation
  uv --version
  ```

### Project Setup
- id:: project-setup
  ```bash
  # Clone repository
  git clone https://github.com/theinterneti/TTA.dev.git
  cd TTA.dev

  # Sync all dependencies
  uv sync --all-extras

  # Verify setup
  uv run pytest -v
  ```

### Python Environment Check
- id:: python-environment-check
  ```bash
  # Check Python version (should be 3.11+)
  python --version

  # Verify in virtual environment
  which python  # Should point to .venv/bin/python
  ```

---

## Code Style & Conventions

### Type Hints (Python 3.11+)
- id:: type-hints-modern
  ```python
  # ✅ Modern Python 3.11+ style (USE THIS)
  def process(data: str | None) -> dict[str, Any]:
      ...

  # ❌ Old style (DON'T USE)
  from typing import Optional, Dict
  def process(data: Optional[str]) -> Dict[str, Any]:
      ...
  ```

### Package Manager - uv NOT pip
- id:: package-manager-uv
  ```bash
  # ✅ CORRECT - Use uv
  uv add package-name
  uv sync --all-extras
  uv run pytest

  # ❌ WRONG - Don't use pip
  pip install package-name  # DON'T DO THIS
  python -m pip install package-name  # DON'T DO THIS
  ```

### Async Best Practices
- id:: async-best-practices
  ```python
  # ✅ Use primitives for orchestration
  workflow = step1 >> step2 >> step3

  # ❌ Manual async orchestration
  async def workflow():
      result1 = await step1()
      result2 = await step2(result1)
      return await step3(result2)
  ```

---

## Workflow Patterns

### WorkflowContext Pattern
- id:: workflow-context-pattern
  ```python
  from tta_dev_primitives import WorkflowContext

  # Create context with correlation ID and metadata
  context = WorkflowContext(
      correlation_id="req-12345",
      data={
          "user_id": "user-789",
          "request_type": "analysis"
      }
  )

  # Context is passed through entire workflow automatically
  result = await workflow.execute(context, input_data)
  ```

### Sequential Composition
- id:: sequential-composition-pattern
  ```python
  from tta_dev_primitives import SequentialPrimitive

  # Using the >> operator (recommended)
  workflow = (
      input_processor >>
      data_transformer >>
      output_formatter
  )

  # Or using SequentialPrimitive directly
  workflow = SequentialPrimitive([
      input_processor,
      data_transformer,
      output_formatter
  ])
  ```

### Parallel Composition
- id:: parallel-composition-pattern
  ```python
  from tta_dev_primitives import ParallelPrimitive

  # Using the | operator (recommended)
  workflow = (
      input_step >>
      (fast_path | slow_path | cached_path) >>
      aggregator
  )

  # Or using ParallelPrimitive directly
  workflow = ParallelPrimitive([
      fast_path,
      slow_path,
      cached_path
  ])
  ```

### Error Recovery Pattern
- id:: error-recovery-pattern
  ```python
  from tta_dev_primitives.recovery import RetryPrimitive, FallbackPrimitive

  # Retry with exponential backoff
  retry_step = RetryPrimitive(
      primitive=api_call,
      max_retries=3,
      backoff_strategy="exponential"
  )

  # Fallback to alternative on failure
  resilient_step = FallbackPrimitive(
      primary=expensive_service,
      fallbacks=[cheaper_service, cached_result]
  )
  ```

---

## Testing Patterns

### Basic Test Structure
- id:: basic-test-structure
  ```python
  import pytest
  from tta_dev_primitives import WorkflowContext

  @pytest.mark.asyncio
  async def test_workflow():
      # Arrange
      context = WorkflowContext(correlation_id="test-123")
      input_data = {"test": "data"}

      # Act
      result = await workflow.execute(context, input_data)

      # Assert
      assert result["status"] == "success"
  ```

### MockPrimitive Usage
- id:: mock-primitive-usage
  ```python
  from tta_dev_primitives.testing import MockPrimitive

  @pytest.mark.asyncio
  async def test_with_mock():
      # Create mock primitive
      mock_llm = MockPrimitive(
          return_value={"response": "mocked output"}
      )

      # Use in workflow
      workflow = step1 >> mock_llm >> step3
      result = await workflow.execute(context, input_data)

      # Verify mock was called
      assert mock_llm.call_count == 1
  ```

---

## Quality Checks

### Running All Quality Checks
- id:: quality-checks-all
  ```bash
  # Format code
  uv run ruff format .

  # Lint code
  uv run ruff check . --fix

  # Type check
  uvx pyright packages/

  # Run tests
  uv run pytest -v

  # Or use the combined task
  # (requires VS Code tasks setup)
  ```

### Test Coverage
- id:: test-coverage
  ```bash
  # Run tests with coverage
  uv run pytest --cov=packages --cov-report=html --cov-report=term-missing

  # View HTML report
  open htmlcov/index.html
  ```

---

## Import Patterns

### Standard Imports
- id:: standard-imports
  ```python
  # Core primitives
  from tta_dev_primitives import (
      WorkflowPrimitive,
      WorkflowContext,
      SequentialPrimitive,
      ParallelPrimitive,
      ConditionalPrimitive,
      RouterPrimitive,
  )

  # Recovery primitives
  from tta_dev_primitives.recovery import (
      RetryPrimitive,
      FallbackPrimitive,
      TimeoutPrimitive,
      CompensationPrimitive,
  )

  # Performance primitives
  from tta_dev_primitives.performance import CachePrimitive

  # Testing primitives
  from tta_dev_primitives.testing import MockPrimitive
  ```

---

## Observability

### Basic Instrumentation
- id:: basic-instrumentation
  ```python
  from tta_dev_primitives import WorkflowContext
  from tta_dev_primitives.observability import get_logger

  logger = get_logger(__name__)

  # Structured logging
  logger.info(
      "workflow_executed",
      workflow_name="my_workflow",
      duration_ms=123.45,
      status="success"
  )
  ```

### Enhanced Observability
- id:: enhanced-observability
  ```python
  from observability_integration import initialize_observability
  from observability_integration.primitives import (
      RouterPrimitive,
      CachePrimitive,
  )

  # Initialize once at app startup
  initialize_observability(
      service_name="my-app",
      enable_prometheus=True
  )

  # Use enhanced primitives (automatic metrics)
  workflow = (
      input_step >>
      RouterPrimitive(routes={"fast": llm1, "quality": llm2}) >>
      CachePrimitive(expensive_op, ttl_seconds=3600)
  )
  ```

---

## Anti-Patterns to Avoid

### ❌ Manual Async Orchestration
- id:: antipattern-manual-async
  ```python
  # ❌ DON'T DO THIS
  async def manual_workflow(input_data):
      result1 = await step1(input_data)
      result2 = await step2(result1)
      return await step3(result2)

  # ✅ DO THIS INSTEAD
  workflow = step1 >> step2 >> step3
  result = await workflow.execute(context, input_data)
  ```

### ❌ Manual Retry Logic
- id:: antipattern-manual-retry
  ```python
  # ❌ DON'T DO THIS
  async def api_call_with_retry():
      for i in range(3):
          try:
              return await api_call()
          except Exception:
              await asyncio.sleep(2 ** i)
      raise Exception("Failed after retries")

  # ✅ DO THIS INSTEAD
  from tta_dev_primitives.recovery import RetryPrimitive

  workflow = RetryPrimitive(
      primitive=api_call,
      max_retries=3,
      backoff_strategy="exponential"
  )
  ```

### ❌ Global State
- id:: antipattern-global-state
  ```python
  # ❌ DON'T DO THIS
  USER_ID = "user-789"  # Global variable

  async def process():
      return await do_something(USER_ID)

  # ✅ DO THIS INSTEAD
  context = WorkflowContext(
      data={"user_id": "user-789"}
  )
  result = await workflow.execute(context, input_data)
  ```

---

## Quick Links

### Documentation
- [[TTA.dev]] - Main hub
- [[TTA.dev/Guides/Getting Started]] - Setup guide
- [[TTA.dev/Primitives]] - All primitives catalog

### Development
- [[TTA.dev/Development/Setup]] - Dev environment
- [[TTA.dev/Development/Testing]] - Testing guide
- [[TTA.dev/Development/Quality]] - Quality standards

### Packages
- [[TTA.dev/Packages/tta-dev-primitives]] - Core primitives
- [[TTA.dev/Packages/tta-observability-integration]] - Observability
- [[TTA.dev/Packages/universal-agent-context]] - Agent context

---

## Usage

To embed any of these blocks in your documentation:

```markdown
# In any page, reference by block ID:
{{embed ((prerequisites-full))}}
{{embed ((type-hints-modern))}}
{{embed ((workflow-context-pattern))}}
```

**Remember:** Edit once here, updates everywhere automatically!

---

**Last Updated:** 2025-10-30
**Maintained by:** [[TTA Team]]

- [[Project Hub]]