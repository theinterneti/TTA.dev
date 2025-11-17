# Component Failures

**Purpose:** Document failed approaches, mistakes, and lessons learned to avoid repeating them.

**Last Updated:** 2025-10-20

---

## 2025-10-20: Orchestration Component - Low Test Coverage

**Component:** `orchestration`
**Stage:** Development → Staging
**Failure Type:** Quality Gate Failure (Test Coverage)

**Problem:**
- Attempted to promote orchestration component to staging
- Test coverage: 29.5% (threshold: 70%)
- 8 out of 10 tests failing

**Root Causes:**
1. **Incomplete Test Suite:**
   - Missing tests for error handling
   - Edge cases not covered
   - Integration tests incomplete

2. **Test Failures:**
   - Tests written but not maintained
   - Dependencies changed, tests not updated
   - Async fixtures not properly configured

**Lessons Learned:**
1. **Write tests alongside implementation** - Don't defer testing
2. **Maintain tests** - Update tests when code changes
3. **Test error paths** - Not just happy paths
4. **Use pytest-asyncio correctly** - Ensure async fixtures work

**Prevention:**
- Run tests frequently during development
- Aim for ≥60% coverage before considering component "done"
- Use pre-commit hooks to catch test failures early
- Review test coverage reports regularly

**Status:** In Progress (fixing tests and adding coverage)

---

## Anti-Patterns to Avoid

### Anti-Pattern 1: Deferring Testing

**Description:** Writing all code first, then adding tests later

**Why It Fails:**
- Hard to achieve good coverage retroactively
- Tests become an afterthought
- Miss edge cases discovered during implementation
- Quality gates fail at promotion time

**Correct Approach:**
- Write tests alongside implementation (TDD or test-after-feature)
- Aim for ≥60% coverage during development
- Test each feature as it's implemented
- Run tests frequently

**Example:**
```python
# ❌ Wrong: All implementation, no tests
def complex_function():
    # 100 lines of code
    pass

# Later: "I'll add tests when I have time"
# Result: Never happens, or incomplete coverage

# ✅ Correct: Test alongside implementation
def test_complex_function_happy_path():
    """Test main functionality."""
    result = complex_function(valid_input)
    assert result == expected

def test_complex_function_error_handling():
    """Test error cases."""
    with pytest.raises(ValueError):
        complex_function(invalid_input)

def complex_function():
    # Implementation with tests guiding design
    pass
```

---

### Anti-Pattern 2: Ignoring Test Failures

**Description:** Committing code with failing tests, planning to "fix later"

**Why It Fails:**
- Broken tests accumulate
- Hard to identify new failures
- Quality gates fail at promotion
- Technical debt grows

**Correct Approach:**
- Fix failing tests immediately
- Never commit with failing tests
- Use CI/CD to catch failures early
- Treat test failures as bugs

**Example:**
```bash
# ❌ Wrong: Commit with failing tests
git add .
git commit -m "Add feature (tests failing, will fix later)"
# Result: Tests never fixed, quality gates fail

# ✅ Correct: Fix tests before committing
uvx pytest tests/
# Fix any failures
git add .
git commit -m "Add feature with passing tests"
```

---

### Anti-Pattern 3: Lowering Quality Gates

**Description:** Reducing coverage thresholds to pass quality gates

**Why It Fails:**
- Masks underlying quality issues
- Sets bad precedent
- Reduces overall code quality
- Defeats purpose of quality gates

**Correct Approach:**
- Fix the code and add tests
- Maintain or increase thresholds
- Document any threshold changes with rationale
- Treat quality gates as hard requirements

**Example:**
```yaml
# ❌ Wrong: Lower threshold to pass
quality_gates:
  test_coverage:
    staging_threshold: 50.0  # Lowered from 70.0 to pass

# ✅ Correct: Fix code to meet threshold
quality_gates:
  test_coverage:
    staging_threshold: 70.0  # Maintained
# Then: Add tests to reach 70% coverage
```

---

### Anti-Pattern 4: Testing Implementation Details

**Description:** Testing private methods and internal state instead of public behavior

**Why It Fails:**
- Tests break when refactoring
- Doesn't validate actual behavior
- Couples tests to implementation
- Low value, high maintenance

**Correct Approach:**
- Test public APIs and contracts
- Test behavior, not implementation
- Allow internal refactoring without breaking tests
- Focus on what users/callers care about

**Example:**
```python
# ❌ Wrong: Test private method
def test_internal_calculation():
    """Test private calculation method."""
    obj = Calculator()
    assert obj._internal_calc(5, 3) == 8

# ✅ Correct: Test public behavior
def test_calculator_addition():
    """Test calculator addition."""
    calc = Calculator()
    result = calc.add(5, 3)
    assert result == 8
```

---

### Anti-Pattern 5: Flaky Tests

**Description:** Tests that pass/fail intermittently without code changes

**Why It Fails:**
- Erodes trust in test suite
- Wastes developer time
- Masks real failures
- Quality gates unreliable

**Common Causes:**
- Race conditions in async code
- Timing dependencies (sleep())
- Shared state between tests
- External dependencies

**Correct Approach:**
- Fix flaky tests immediately
- Use proper async/await instead of sleep()
- Isolate tests (no shared state)
- Mock external dependencies

**Example:**
```python
# ❌ Wrong: Flaky test with sleep
def test_async_operation():
    start_async_operation()
    time.sleep(1)  # Hope it's done
    assert operation_complete()

# ✅ Correct: Proper async test
@pytest.mark.asyncio
async def test_async_operation():
    await async_operation()
    assert operation_complete()
```

---

### Anti-Pattern 6: Missing Integration Tests

**Description:** Only unit tests, no integration tests

**Why It Fails:**
- Components work in isolation but fail together
- Integration issues discovered late
- Staging quality gates fail
- Production bugs

**Correct Approach:**
- Write integration tests for component interactions
- Test database integration
- Test API integration
- Test external service integration

**Example:**
```python
# ❌ Wrong: Only unit tests
def test_user_service():
    """Test user service in isolation."""
    service = UserService(mock_db)
    result = service.create_user(user_data)
    assert result.success

# ✅ Correct: Add integration tests
@pytest.mark.integration
def test_user_service_integration(redis_client, neo4j_session):
    """Test user service with real databases."""
    service = UserService(redis_client, neo4j_session)
    result = service.create_user(user_data)

    # Verify data in Redis
    assert redis_client.exists(f"user:{result.user_id}")

    # Verify data in Neo4j
    user_node = neo4j_session.run(
        "MATCH (u:User {id: $id}) RETURN u",
        id=result.user_id
    ).single()
    assert user_node is not None
```

---

### Anti-Pattern 7: Hardcoded Test Data

**Description:** Hardcoding test data in each test instead of using fixtures

**Why It Fails:**
- Duplicated test data
- Hard to maintain
- Inconsistent test data
- Difficult to update

**Correct Approach:**
- Use fixtures for reusable test data
- Centralize test data in conftest.py
- Make test data easy to update
- Use parametrized tests for variations

**Example:**
```python
# ❌ Wrong: Hardcoded in each test
def test_user_creation():
    user_data = {"username": "test", "email": "test@example.com"}
    result = create_user(user_data)
    assert result.success

def test_user_validation():
    user_data = {"username": "test", "email": "test@example.com"}
    result = validate_user(user_data)
    assert result.valid

# ✅ Correct: Use fixture
@pytest.fixture
def sample_user_data():
    return {"username": "test", "email": "test@example.com"}

def test_user_creation(sample_user_data):
    result = create_user(sample_user_data)
    assert result.success

def test_user_validation(sample_user_data):
    result = validate_user(sample_user_data)
    assert result.valid
```

---

### Anti-Pattern 8: Skipping Error Handling Tests

**Description:** Only testing happy paths, not error conditions

**Why It Fails:**
- Error handling bugs in production
- Poor user experience
- Difficult to debug issues
- Low confidence in error recovery

**Correct Approach:**
- Test all error conditions
- Test edge cases
- Test boundary conditions
- Test recovery mechanisms

**Example:**
```python
# ❌ Wrong: Only happy path
def test_divide():
    """Test division."""
    assert divide(10, 2) == 5

# ✅ Correct: Test error cases too
def test_divide_happy_path():
    """Test normal division."""
    assert divide(10, 2) == 5

def test_divide_by_zero():
    """Test division by zero."""
    with pytest.raises(ZeroDivisionError):
        divide(10, 0)

def test_divide_invalid_input():
    """Test invalid input."""
    with pytest.raises(TypeError):
        divide("10", 2)
```

---

## Component-Specific Failures

### Orchestration Component

**Failure Date:** 2025-10-20
**Stage:** Development → Staging
**Failure Type:** Quality Gate Failure

**Specific Issues:**
1. **Test Coverage:** 29.5% (need 70%)
   - Missing: Error handling tests
   - Missing: Edge case tests
   - Missing: Integration tests

2. **Test Failures:** 8/10 tests failing
   - Async fixture issues
   - Dependency changes not reflected in tests
   - Mock configurations outdated

**Action Items:**
- [ ] Fix async fixture configuration
- [ ] Update tests for dependency changes
- [ ] Add error handling tests
- [ ] Add edge case tests
- [ ] Add integration tests
- [ ] Achieve ≥70% coverage

**Estimated Effort:** 2-3 days

---

## Lessons Learned Summary

### Testing
1. **Write tests alongside implementation** - Don't defer
2. **Test error paths** - Not just happy paths
3. **Use fixtures** - Avoid hardcoded test data
4. **Fix flaky tests immediately** - Don't tolerate intermittent failures
5. **Add integration tests** - Unit tests aren't enough

### Quality Gates
1. **Never lower thresholds** - Fix the code instead
2. **Run gates frequently** - Don't wait until promotion
3. **Fix failures immediately** - Don't accumulate technical debt
4. **Understand gate failures** - Read error messages carefully

### Development Process
1. **Run tests frequently** - Catch issues early
2. **Use pre-commit hooks** - Prevent bad commits
3. **Review coverage reports** - Identify gaps
4. **Maintain tests** - Update when code changes

---

## Prevention Checklist

Before promoting a component, ensure:

- [ ] All tests pass locally
- [ ] Test coverage ≥60% (development), ≥70% (staging), ≥80% (production)
- [ ] Error handling tested
- [ ] Edge cases tested
- [ ] Integration tests written (for staging)
- [ ] No flaky tests
- [ ] Linting clean
- [ ] Type checking clean
- [ ] No security issues
- [ ] Documentation complete

---

## Resources

### Documentation
- Testing Instructions: `.augment/instructions/testing.instructions.md`
- Quality Gates Instructions: `.augment/instructions/quality-gates.instructions.md`
- Component Maturity Instructions: `.augment/instructions/component-maturity.instructions.md`

### Tools
- Run tests: `uvx pytest tests/`
- Check coverage: `uvx pytest tests/ --cov=src/ --cov-report=html`
- Run linting: `uvx ruff check src/`
- Run type checking: `uvx pyright src/`
- Run workflow: `python scripts/workflow/spec_to_production.py`

---

**Note:** This file should be updated whenever a component fails quality gates or when new anti-patterns are discovered.
