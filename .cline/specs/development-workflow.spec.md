---
spec: development-workflow-v2.0
title: TTA.dev Development Workflow Specification
version: 2.0
author: TTA.dev Agent Framework
date: 2025-11-17
status: active
---

# TTA.dev Development Workflow Specification (.spec.md)

## Overview

This specification defines the standardized development workflow for TTA.dev primitives and applications. It establishes acceptance criteria, implementation blueprints, and quality gates that ensure consistency and reliability across all development activities.

## Acceptance Criteria (AC)

### AC-1: Primitive Compliance
All code MUST use TTA.dev primitives for workflow patterns:

**✅ REQUIRED PATTERNS:**

```python
# Sequential operations
workflow = step1 >> step2 >> step3

# Parallel operations
workflow = ParallelPrimitive([branch1, branch2, branch3])

# Conditional routing
router = RouterPrimitive(routes={"path_a": workflow_a, "path_b": workflow_b})

# Error recovery
robust_workflow = RetryPrimitive(unreliable_step, max_retries=3) >> fallback
```

**❌ FORBIDDEN PATTERNS:**

```python
# Manual async orchestration (ILLEGAL)
async def manual_workflow():
    result1 = await step1()
    result2 = await step2(result1)
    return await step3(result2)

# Manual retry loops (ILLEGAL)
async def manual_retry():
    for i in range(3):
        try:
            return await api_call()
        except Exception:
            await asyncio.sleep(2 ** i)
```

### AC-2: Type Safety
All code MUST follow modern Python 3.11+ type annotations:

```python
# ✅ CORRECT
def process_data(data: dict[str, Any] | None) -> dict[str, Any]:
    pass

# ❌ WRONG
from typing import Optional, Dict, Any  # ILLEGAL imports
def process_data(data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    pass
```

### AC-3: Observable by Default
All workflows MUST include automatic observability:

```python
from tta_dev_primitives import WorkflowContext

# Every workflow execution needs context
context = WorkflowContext(
    correlation_id="req-123",
    data={"user_id": "user-789", "operation": "process_data"}
)
result = await workflow.execute(context, input_data)
```

### AC-4: Test Coverage 100%
All new code MUST have comprehensive tests:

```python
import pytest
from tta_dev_primitives.testing import MockPrimitive

@pytest.mark.asyncio
async def test_workflow_with_failure_modes():
    # Test success path
    mock_success = MockPrimitive(return_value={"status": "success"})
    workflow = step1 >> mock_success >> step2
    result = await workflow.execute(context, input_data)
    assert mock_success.call_count == 1
    assert result["status"] == "success"

    # Test failure recovery
    mock_failure = MockPrimitive(side_effect=ValueError("test error"))
    retry_workflow = RetryPrimitive(mock_failure, max_retries=2)
    try:
        await retry_workflow.execute(context, input_data)
    except ValueError:
        assert mock_failure.call_count == 2  # Retried once
```

## Implementation Blueprints (IB)

### IB-1: New Workflow Primitive
**Template for creating new TTA.dev workflow primitives:**

```python
from dataclasses import dataclass
from typing import TypeVar, Generic
from tta_dev_primitives import WorkflowPrimitive, WorkflowContext

T = TypeVar('T')
U = TypeVar('U')

@dataclass
class NewWorkflowPrimitive(WorkflowPrimitive[T, U]):
    """[Brief description of what this primitive does]"""

    # Configuration parameters
    parameter1: str | None = None
    max_attempts: int = 3

    async def execute(self, context: WorkflowContext[T] | None, input_data: T) -> U:
        """Execute the primitive logic with observability."""
        # Create span for tracing
        with self._create_span(context, "NewWorkflowPrimitive") as span:
            span.set_attribute("parameter1", self.parameter1)
            span.set_attribute("max_attempts", self.max_attempts)

            # Implementation logic here
            try:
                result = await self._do_work(input_data)
                self._record_success(span, result)
                return result
            except Exception as e:
                self._record_error(span, e)
                raise
```

### IB-2: Service Integration Pattern
**Standard pattern for integrating external services:**

```python
from tta_dev_primitives.recovery import RetryPrimitive, TimeoutPrimitive, FallbackPrimitive
from tta_dev_primitives.performance import CachePrimitive

class ExternalServiceClient:
    """Example service client with primitive-based reliability."""

    def __init__(self):
        # Wrap unreliable operations with primitives
        self.api_call = TimeoutPrimitive(
            primitive=self._raw_api_call,
            timeout_seconds=30.0
        )

        self.reliable_call = RetryPrimitive(
            primitive=self.api_call,
            max_retries=3,
            backoff_strategy="exponential"
        )

        self.cached_call = CachePrimitive(
            primitive=self.reliable_call,
            ttl_seconds=300,  # 5 minutes
            max_size=1000
        )

    async def reliable_operation(self, request_data: dict) -> dict:
        """Reliable operation with automatic recovery."""
        return await self.cached_call.execute(None, request_data)

    async def _raw_api_call(self, request_data: dict) -> dict:
        """Raw API call - should NOT be called directly."""
        # Implementation here
        pass
```

### IB-3: Agentic Workflow Build
**Standard workflow for building agentic systems:**

```python
from tta_dev_primitives import SequentialPrimitive, ParallelPrimitive
from tta_dev_primitives.integrations import CodeExecutionPrimitive, LLMIntegration

class AgenticWorkflowBuilder:
    """Builds complex agentic workflows using primitives."""

    def __init__(self):
        self.code_executor = CodeExecutionPrimitive()
        self.llm = LLMIntegration()

    def create_code_generation_workflow(self) -> WorkflowPrimitive:
        """Create workflow that generates and validates code."""
        return SequentialPrimitive([
            # Step 1: Analyze requirements
            self._analyze_requirements,

            # Step 2: Generate multiple code options in parallel
            ParallelPrimitive([
                self._generate_code_variant_1,
                self._generate_code_variant_2,
                self._generate_code_variant_3
            ]),

            # Step 3: Validate all variants
            self._validate_code_variants,

            # Step 4: Select best variant and refine
            self._select_and_refine_best
        ])

    async def _analyze_requirements(self, data: dict) -> dict:
        """Step 1: Analyze requirements."""
        prompt = f"Analyze these requirements: {data['requirements']}"
        analysis = await self.llm.generate(prompt)
        return {**data, "analysis": analysis}

    async def _generate_code_variant_1(self, data: dict) -> dict:
        """Generate code variant 1."""
        prompt = f"Generate code for: {data['analysis']} (Variante supérieur)"
        code = await self.llm.generate_code(prompt)
        return {"variant": 1, "code": code, "quality": "high"}

    async def _generate_code_variant_2(self, data: dict) -> dict:
        """Generate code variant 2."""
        prompt = f"Generate code for: {data['analysis']} (Balanced approach)"
        code = await self.llm.generate_code(prompt)
        return {"variant": 2, "code": code, "quality": "balanced"}

    async def _generate_code_variant_3(self, data: dict) -> dict:
        """Generate code variant 3."""
        prompt = f"Generate code for: {data['analysis']} (Fast implementation)"
        code = await self.llm.generate_code(prompt)
        return {"variant": 3, "code": code, "quality": "fast"}

    async def _validate_code_variants(self, data: dict) -> dict:
        """Step 3: Validate all code variants."""
        validated_variants = []
        for variant in data["variants"]:
            # Execute code in sandbox to validate
            result = await self.code_executor.execute(
                {"code": variant["code"], "timeout": 10},
                data
            )
            validated_variants.append({
                **variant,
                "executes": result.get("success", False),
                "output": result.get("logs", ""),
                "error": result.get("error")
            })
        return {**data, "validated_variants": validated_variants}

    async def _select_and_refine_best(self, data: dict) -> dict:
        """Step 4: Select best variant and refine."""
        variants = data["validated_variants"]

        # Score variants (executes successfully + quality)
        scored = []
        for v in variants:
            score = 10 if v["executes"] else 0
            if v["quality"] == "high":
                score += 3
            elif v["quality"] == "balanced":
                score += 2
            elif v["quality"] == "fast":
                score += 1
            scored.append((score, v))

        # Pick best
        best_score, best_variant = max(scored, key=lambda x: x[0])

        # Refine if needed
        if not best_variant["executes"]:
            refinement_prompt = f"Fix this code that doesn't execute: {best_variant['error']}"
            fixed_code = await self.llm.generate_code(refinement_prompt)
            best_variant["code"] = fixed_code

        return {
            "final_code": best_variant["code"],
            "selected_variant": best_variant["variant"],
            "executes": best_variant["executes"],
            "quality": best_variant["quality"]
        }
```

## Quality Gates (QG)

### QG-Pre-Commit
**Automated checks that MUST pass before commit:**

```bash
# Quality gate script
#!/bin/bash

echo "🚀 Running Pre-Commit Quality Gates..."

# QG-1: Primitive Usage Verification
echo "Checking for forbidden manual patterns..."
if grep -r "async def.*for.*range" packages/tta-dev-primitives/src/; then
    echo "❌ Found manual retry loops! Use RetryPrimitive instead."
    exit 1
fi

if grep -r "asyncio.wait_for" packages/tta-dev-primitives/src/; then
    echo "❌ Found manual timeout! Use TimeoutPrimitive instead."
    exit 1
fi

# QG-2: Type Annotation Enforcement
echo "Checking type annotations..."
if grep -r "from typing import" packages/tta-dev-primitives/src/tta_dev_primitives/; then
    echo "❌ Found old typing imports! Use modern syntax (str | None)."
    exit 1
fi

if grep -r "Optional\[" packages/tta-dev-primitives/src/tta_dev_primitives/; then
    echo "❌ Found Optional[]! Use | None instead."
    exit 1
fi

# QG-3: Test Coverage
echo "Checking test coverage..."
if ! python3 -m pytest --cov=tta_dev_primitives --cov-fail-under=100 tests/; then
    echo "❌ Insufficient test coverage! Must be 100%."
    exit 1
fi

# QG-4: Linting
echo "Running ruff checks..."
if ! uv run ruff check packages/; then
    echo "❌ Linting failed!"
    exit 1
fi

echo "✅ All quality gates passed!"
```

### QG-CI/CD
**Continuous Integration checks:**

```yaml
# .github/workflows/ci.yml
name: CI

on: [push, pull_request]

jobs:
  quality-checks:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install uv
        run: curl -LsSf https://astral.sh/uv/install.sh | sh

      - name: Sync dependencies
        run: uv sync --all-extras

      - name: Run Quality Gates
        run: ./scripts/quality-gates.sh

      - name: Type Check
        run: uv run pyright packages/

      - name: Test
        run: uv run pytest -v --cov=tta_dev_primitives --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml
```

## Validation Examples (VE)

### VE-1: Primitive Usage Verification

**Input:** Code with manual patterns
```python
# Input code (should fail)
async def manual_workflow():
    for i in range(3):
        try:
            result = await api_call()
            return result
        except Exception:
            await asyncio.sleep(2 ** i)
```

**Expected Result:** `❌ FORBIDDEN: Manual retry pattern detected. Use RetryPrimitive.`

### VE-2: Type Annotation Validation

**Input:** Old typing style
```python
# Input (should fail)
from typing import Optional
def process(data: Optional[str]) -> str:
    pass
```

**Expected Result:** `❌ VIOLATION: Old typing syntax detected. Use 'str | None' instead.`

### VE-3: Test Coverage Validation

**Input:** New code without tests
```python
# New primitive
class NewPrimitive(WorkflowPrimitive):
    async def execute(self, context, data):
        return await self._work(data)
```

**Expected Result:** `❌ MISSING: No test file found for NewPrimitive. 0% coverage.`

## Change Log

- **v2.0** (2025-11-17): Enhanced with agentic workflow blueprints and automated quality gates
- **v1.0** (2025-10-01): Initial specification with basic acceptance criteria

## Related Specifications

- [PRIMITIVES_CATALOG.md](../../PRIMITIVES_CATALOG.md) - Complete primitive reference
- [.clinerules](../.clinerules) - Code style and package manager rules
- [AGENTS.md](../../AGENTS.md) - Agent development guidelines
