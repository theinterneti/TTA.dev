# Testing Stage Guide

Tags: #stage-testing, #stage-guides, #tta-dev

## Overview

Complete guide to the TESTING stage in TTA.dev's lifecycle.

## Stage Definition

**Testing Stage (Stage.TESTING):**

- Unit tests completed
- Integration tests in progress
- Coverage targets met
- Ready for staging validation

## When to Enter

Transition from EXPERIMENTATION → TESTING when:

- ✅ Core functionality implemented
- ✅ Code compiles/runs without errors
- ✅ API stable (no breaking changes expected)
- ✅ Basic manual testing complete

## Entry Criteria

```python
from tta_dev_primitives.lifecycle import StageCriteria, ValidationCheck

testing_criteria = StageCriteria(
    stage=Stage.TESTING,
    entry_checks=[
        ValidationCheck(
            name="code_quality",
            check_fn=lambda: ruff_passes() and pyright_passes(),
            required=True
        ),
        ValidationCheck(
            name="basic_functionality",
            check_fn=lambda: smoke_tests_pass(),
            required=True
        ),
    ]
)
```

## Goals in This Stage

### 1. Achieve 100% Test Coverage

```bash
# Run tests with coverage
uv run pytest --cov=packages --cov-report=html

# Check coverage threshold
uv run pytest --cov=packages --cov-report=term-missing --cov-fail-under=100
```

### 2. Write Comprehensive Tests

Test types required:

- **Unit tests** - Individual primitive functionality
- **Integration tests** - Primitive composition and workflows
- **Error tests** - Exception handling
- **Edge case tests** - Boundary conditions

### 3. Mock External Dependencies

```python
from tta_dev_primitives.testing import MockPrimitive

# Mock LLM calls
mock_llm = MockPrimitive(return_value={"output": "test"})

# Mock API calls
@patch('requests.post')
def test_api_integration(mock_post):
    mock_post.return_value.json.return_value = {"status": "ok"}
    # Test implementation
```

### 4. Verify Observability

```python
@pytest.mark.asyncio
async def test_observability():
    """Test spans and metrics are created."""
    context = WorkflowContext(correlation_id="test-123")
    result = await primitive.execute(input_data, context)

    # Verify span created
    # Verify metrics recorded
```

## Exit Criteria

Transition TESTING → STAGING when:

- ✅ All tests pass
- ✅ 100% test coverage achieved
- ✅ No critical linting errors
- ✅ Type checking passes
- ✅ Documentation updated

```python
staging_transition = StageTransition(
    from_stage=Stage.TESTING,
    to_stage=Stage.STAGING,
    exit_checks=[
        ValidationCheck(
            name="test_coverage",
            check_fn=lambda: coverage >= 100,
            required=True
        ),
        ValidationCheck(
            name="all_tests_pass",
            check_fn=lambda: pytest_exit_code == 0,
            required=True
        ),
    ]
)
```

## Common Tasks

**Daily workflow in TESTING stage:**

```bash
# 1. Run tests
uv run pytest -v

# 2. Check coverage
uv run pytest --cov=packages --cov-report=term-missing

# 3. Fix linting issues
uv run ruff check . --fix

# 4. Type check
uvx pyright packages/

# 5. Commit passing tests
git add tests/
git commit -m "test: Add comprehensive tests for MyPrimitive"
```

## Best Practices

- [[TTA.dev/Best Practices/Testing]]
- Write tests DURING development, not after
- Test one concept per test function
- Use descriptive test names
- Add docstrings to complex tests

## Anti-Patterns

- [[TTA.dev/Common Mistakes/Testing Antipatterns]]
- Don't skip error case testing
- Don't use time.sleep() in async tests
- Don't test implementation details

## Examples

- [[TTA.dev/Examples/Unit Test Example]]
- [[TTA.dev/Examples/Integration Test Example]]
- See: `platform/primitives/tests/` for real examples

## Checklist

Before moving to STAGING:

- [ ] All unit tests written and passing
- [ ] All integration tests written and passing
- [ ] Error cases covered
- [ ] Edge cases covered
- [ ] 100% test coverage
- [ ] External dependencies mocked
- [ ] Observability verified
- [ ] Type hints complete
- [ ] Linting passes
- [ ] Documentation updated

## Related Pages

- [[TTA.dev/Stage Guides/Experimentation Stage]]
- [[TTA.dev/Stage Guides/Staging Stage]]
- [[TTA Primitives/StageManager]]
- [[Testing TTA Primitives]]

## Tools

- pytest: <https://docs.pytest.org/>
- pytest-asyncio: <https://pytest-asyncio.readthedocs.io/>
- pytest-cov: <https://pytest-cov.readthedocs.io/>
- MockPrimitive: `tta_dev_primitives.testing.MockPrimitive`
