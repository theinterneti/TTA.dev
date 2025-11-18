---
workflow: primitive-development-v2.0
title: TTA.dev Primitive Development Workflow
version: 2.0
author: TTA.dev Agent Framework
description: Complete workflow for developing new TTA.dev workflow primitives with validation gates and human checkpoints
tags: [primitive, development, validation, testing]
persona_recommendation: backend-developer
estimated_duration: "4-6 hours"
complexity: high
---

# TTA.dev Primitive Development Workflow

## Overview

This workflow implements the complete lifecycle for developing new TTA.dev workflow primitives, including design, implementation, validation, and integration.

## Workflow Stages

### Stage 1: Analysis & Specifications
**Duration:** 30-45 minutes
**Persona:** backend-developer
**Validation Gates:** ✓ Human Approval Required

1. **Requirement Analysis**
   ```
   Analyze: What workflow pattern does this primitive solve?
   Research: Existing primitives in same category
   Document: Clear specification with acceptance criteria
   ```

2. **API Design**
   ```
   Design: Type-safe interfaces following WorkflowPrimitive[T,U] pattern
   Document: Generic type parameters and their meanings
   Plan: Error handling and observable patterns
   ```

   **❓ HUMAN CHECKPOINT: API Design Review**
   ```
   Does the API follow TTA.dev conventions?
   Are type annotations complete and modern (T | None)?
   Is the abstraction level appropriate?
   Can it compose with existing primitives?
   ```

### Stage 2: Implementation with Quality Gates
**Duration:** 90-120 minutes
**Persona:** backend-developer
**Validation Gates:** ⚙️ Automated + ✓ Human Approval

1. **Core Implementation**
   ```python
   # Template for primitive implementation
   from dataclasses import dataclass
   from tta_dev_primitives import WorkflowPrimitive, WorkflowContext

   @dataclass
   class NewPrimitive(WorkflowPrimitive[T, U]):
       """[Brief description]"""

       parameter: str | None = None

       async def execute(self, context: WorkflowContext[T] | None, input_data: T) -> U:
           # Create span for observability
           with self._create_span(context, "NewPrimitive") as span:
               span.set_attribute("parameter", self.parameter)

               try:
                   result = await self._work(input_data)
                   self._record_success(span, result)
                   return result
               except Exception as e:
                   self._record_error(span, e)
                   raise
   ```

2. **Unit Tests with 100% Coverage**
   ```python
   # Automated validation requirements
   import pytest
   from tta_dev_primitives.testing import MockPrimitive

   @pytest.mark.asyncio
   async def test_new_primitive_success():
       primitive = NewPrimitive()
       result = await primitive.execute(None, test_input)
       assert result == expected_output

   @pytest.mark.asyncio
   async def test_new_primitive_error_handling():
       primitive = NewPrimitive()
       with pytest.raises(ValueError):
           await primitive.execute(None, invalid_input)
   ```

   **⚙️ AUTOMATED VALIDATION GATE: Quality Checks**
   ```bash
   # Must pass before proceeding
   uv run ruff check packages/tta-dev-primitives/src/
   uv run pyright packages/tta-dev-primitives/src/
   uv run pytest --cov=tta_dev_primitives --cov-fail-under=100
   ```

### Stage 3: Integration & Compatibility Testing
**Duration:** 60-90 minutes
**Persona:** testing-specialist
**Validation Gates:** ✓ Human Approval Required

1. **Composition Testing**
   ```python
   # Test composition with existing primitives
   workflow = NewPrimitive() >> RetryPrimitive() >> CachePrimitive()
   result = await workflow.execute(context, data)

   # Test parallel composition
   workflow = NewPrimitive() | AlternativePrimitive()
   results = await workflow.execute(context, data)
   ```

2. **Cross-Primitive Compatibility**
   ```python
   # Verify with RouterPrimitive routing
   router = RouterPrimitive(routes={
       "use_new": NewPrimitive(),
       "fallback": ExistingPrimitive()
   })
   result = await router.execute(context, data)
   ```

   **❓ HUMAN CHECKPOINT: Integration Review**
   ```
   Does it compose properly with existing primitives?
   Are there any breaking changes to the API contract?
   Does it fit well in the primitive ecosystem?
   Should it be in a new recovery/performance/core category?
   ```

### Stage 4: Documentation & Examples
**Duration:** 45-60 minutes
**Persona:** backend-developer
**Validation Gates:** ✓ Human Approval Required

1. **Comprehensive Documentation**
   ```python
   """
   NewPrimitive: [Clear description of what it does]

   Use when: [Specific use cases]
   Don't use when: [When alternatives are better]

   Example:
       primitive = NewPrimitive(param=value)
       workflow = primitive >> other_step
       result = await workflow.execute(context, data)
   """
   ```

2. **Working Examples**
   ```python
   # examples/new_primitive_usage.py
   from tta_dev_primitives import NewPrimitive, WorkflowContext

   async def main():
       primitive = NewPrimitive()
       context = WorkflowContext(correlation_id="example-123")
       result = await primitive.execute(context, input_data)
       return result
   ```

   **❓ HUMAN CHECKPOINT: Documentation Review**
   ```
   Is the purpose clear from the docstring?
   Are examples runnable and demonstrate real usage?
   Does it explain when to use (and when not to)?
   Is the API documentation complete?
   ```

### Stage 5: Final Integration & Release
**Duration:** 30-45 minutes
**Persona:** backend-developer
**Validation Gates:** ❓ HUMAN APPROVAL REQUIRED

1. **Package Updates**
   ```python
   # Update __init__.py
   from .new_primitive import NewPrimitive
   __all__ = [..., "NewPrimitive"]
   ```

2. **Version & Changelog**
   ```
   # Update version in pyproject.toml
   # Add entry to CHANGELOG.md
   # Update PRIMITIVES_CATALOG.md
   ```

   **❓ HUMAN CHECKPOINT: Release Readiness**
   ```
   All tests pass with 100% coverage?
   Documentation is complete and accurate?
   No breaking changes to existing APIs?
   Ready for production deployment?
   ```

## Quality Assurance Gates

### Pre-Commit Validation
```bash
#!/bin/bash
# .cline/hooks/PreToolUse

echo "🔍 Primitive Development Quality Gates..."

# Code quality
uv run ruff check packages/tta-dev-primitives/src/ || exit 1
uv run ruff format packages/tta-dev-primitives/src/ || exit 1

# Type safety
uv run pyright packages/tta-dev-primitives/src/ || exit 1

# Test coverage
uv run pytest packages/tta-dev-primitives/tests/ \
  --cov=tta_dev_primitives \
  --cov-fail-under=100 \
  --cov-report=term-missing || exit 1

# Integration tests
uv run pytest tests/ -k "integration" || exit 1

echo "✅ All quality gates passed!"
```

### CI/CD Pipeline Requirements
```yaml
# .github/workflows/primitive-ci.yml
name: Primitive CI
on: [push, pull_request]

jobs:
  validate-primitive:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run Quality Gates
        run: ./.cline/hooks/PreToolUse
      - name: Validate Composition
        run: python -m pytest tests/test_composition.py
```

## Success Criteria

- ✅ **Functional**: Primitive works correctly in isolation
- ✅ **Composable**: Integrates seamlessly with existing primitives
- ✅ **Observable**: Full OpenTelemetry integration
- ✅ **Tested**: 100% coverage with edge cases covered
- ✅ **Documented**: Clear examples and usage guidelines
- ✅ **Type Safe**: Full modern type annotations
- ✅ **Peer Reviewed**: Human checkpoints passed

## Related Resources

- [PRIMITIVES_CATALOG.md](../../PRIMITIVES_CATALOG.md) - Complete primitive reference
- [development-workflow.spec.md](../specs/development-workflow.spec.md) - Specification standards
- [primitive-development-examples/](../examples/primitives/) - Working primitive examples

## Emergency Rollback Plan

If issues discovered post-release:
1. Create immediate issue with `priority: critical` tag
2. Temporarily remove from `__init__.py` exports
3. Revert to previous version if needed
4. Schedule fix within 24 hours
