# Agentic Workflow: Bug Fix

**Purpose:** Systematic bug investigation and resolution for TTA components
**Persona:** TTA.dev Expert Agent (High Reliability, Security First)
**Observability:** Langfuse Tracing Enabled

**When to Use:**
- Bug reported by user or QA
- Test failure discovered
- Production issue detected
- Regression identified

---

## Workflow Description

This workflow guides systematic bug investigation, root cause analysis, fix implementation, and verification to ensure bugs are properly resolved without introducing regressions.

**Key Principles:**
- **Full Observability:** All actions traced via Langfuse
- Reproduce before fixing
- Fix root cause, not symptoms
- Test-driven resolution
- Verify no regressions

---

## Input Requirements

### Required Inputs
- **Bug Description:** Clear description of the bug
- **Reproduction Steps:** Steps to reproduce the bug
- **Expected Behavior:** What should happen
- **Actual Behavior:** What actually happens
- **Component:** Affected component name

### Optional Inputs
- **Environment:** Where bug occurs (dev/staging/production)
- **Severity:** Critical/High/Medium/Low
- **User Impact:** Number of users affected
- **Error Messages:** Any error messages or stack traces

---

## Step-by-Step Process

### Step 1: Reproduce the Bug

**Goal:** Reliably reproduce the bug locally

**Actions:**
1. Review bug description and reproduction steps
2. Set up test environment
3. Attempt to reproduce
4. Document reproduction

**Observability Integration (Langfuse):**
```python
# Start trace for bug fix
from .hypertool.instrumentation.langfuse_integration import LangfuseIntegration

langfuse = LangfuseIntegration()
trace = langfuse.start_trace(
    name="bug-fix",
    persona="backend-engineer",
    chatmode="bug-fix"
)

# Log reproduction attempt
langfuse.create_generation(
    trace=trace,
    name="reproduction",
    model="gemini-2.5-flash",
    prompt="Attempting to reproduce bug...",
    completion="Reproduction successful/failed."
)
```

**Commands:**
```bash
# Set up environment
export ENVIRONMENT=development
uv sync --all-groups

# Run specific test if available
uv run pytest tests/test_{component}.py::test_{bug_scenario} -v

# Or reproduce manually
python -m src.{component}.{module}
```

**Validation Criteria:**
- [ ] Bug reproduces consistently
- [ ] Reproduction steps documented
- [ ] Environment documented
- [ ] Error messages captured

**If Cannot Reproduce:**
- Request more information from reporter
- Check environment differences
- Review recent changes
- Check for intermittent issues

---

### Step 2: Isolate the Problem

**Goal:** Identify the root cause

**Actions:**
1. Review error messages and stack traces
2. Add logging/debugging
3. Use debugger to step through code
4. Check recent changes (git log)
5. Review related code

**Debugging Techniques:**
```python
# Add debugging breakpoint
import pdb; pdb.set_trace()

# Add logging
import logging
logger = logging.getLogger(__name__)
logger.debug(f"Variable state: {variable}")

# Check recent changes
git log --oneline --since="1 week ago" -- src/{component}/
```

**Root Cause Analysis:**
- **Logic Error:** Incorrect condition, off-by-one, missing edge case
- **Async Issue:** Missing await, race condition, blocking operation
- **Database Issue:** Connection leak, query error, transaction issue
- **Integration Issue:** API change, dependency update, configuration
- **Type Error:** Type mismatch, None handling, missing validation

**Validation Criteria:**
- [ ] Root cause identified
- [ ] Understand why bug occurs
- [ ] Know what needs to change
- [ ] Documented in AI context

---

### Step 3: Design the Fix

**Goal:** Plan the fix before implementing

**Actions:**
1. Determine minimal fix
2. Consider side effects
3. Plan test strategy
4. Review with team if needed

**Fix Design Template:**
```markdown
## Bug Fix Design

**Bug:** {brief description}
**Root Cause:** {root cause}

**Proposed Fix:**
{describe the fix}

**Files to Change:**
- src/{component}/{file}.py
- tests/test_{component}.py

**Side Effects:**
{any potential side effects}

**Test Strategy:**
- Add regression test
- Update existing tests
- Run integration tests

**Alternatives Considered:**
{any alternative approaches}
```

**Validation Criteria:**
- [ ] Fix is minimal and targeted
- [ ] Side effects considered
- [ ] Test strategy defined
- [ ] Documented in AI context

---

### Step 4: Implement the Fix

**Goal:** Implement the fix with tests

**Actions:**
1. Write regression test first (TDD)
2. Implement the fix
3. Verify test passes
4. Run all tests
5. Check quality gates

**Test-Driven Development:**
```python
# Step 1: Write failing test
@pytest.mark.asyncio
async def test_bug_fix_regression():
    """Test that bug is fixed."""
    # Arrange
    setup_bug_scenario()

    # Act
    result = await function_with_bug()

    # Assert
    assert result == expected_result  # Currently fails
```

**Implement Fix:**
```python
# Step 2: Implement fix
async def function_with_bug():
    # Before: Buggy implementation
    # if condition:  # ❌ Wrong condition

    # After: Fixed implementation
    if correct_condition:  # ✅ Correct condition
        return expected_result
```

**Verify Fix:**
```bash
# Step 3: Run regression test
uv run pytest tests/test_{component}.py::test_bug_fix_regression -v

# Step 4: Run all tests
uv run pytest tests/{component}/ -v

# Step 5: Check coverage
uv run pytest tests/{component}/ --cov=src/{component} --cov-report=term

# Step 6: Run quality gates
uvx ruff check src/{component}/
uvx pyright src/{component}/
```

**Validation Criteria:**
- [ ] Regression test passes
- [ ] All existing tests pass
- [ ] Coverage maintained or improved
- [ ] Linting clean
- [ ] Type checking clean

---

### Step 5: Verify No Regressions

**Goal:** Ensure fix doesn't break other functionality

**Actions:**
1. Run full test suite
2. Run integration tests
3. Test related functionality
4. Check for side effects

**Commands:**
```bash
# Run all unit tests
uv run pytest tests/ -v

# Run integration tests
uv run pytest tests/integration/ -v -m integration

# Run E2E tests (if applicable)
uv run pytest tests/e2e/ -v -m e2e

# Run full workflow
python scripts/workflow/spec_to_production.py \
    --spec specs/{component}.md \
    --component {component} \
    --target staging
```

**Validation Criteria:**
- [ ] All tests pass
- [ ] No new failures introduced
- [ ] Integration tests pass
- [ ] Quality gates pass
- [ ] No performance degradation

---

### Step 6: Document the Fix

**Goal:** Document bug and fix for future reference

**Actions:**
1. Update component failures memory
2. Add code comments
3. Update AI context
4. Create/update GitHub issue

**Update Memory:**
```bash
# Document in component failures
cat >> .augment/memory/component-failures.memory.md << EOF

## Bug: {brief description}

**Date:** {date}
**Component:** {component}
**Severity:** {severity}

**Root Cause:**
{root cause description}

**Fix:**
{fix description}

**Lesson Learned:**
{what we learned}

**Prevention:**
{how to prevent similar bugs}

EOF
```

**Add Code Comments:**
```python
# Add comment explaining the fix
async def fixed_function():
    # Fix for bug #{issue_number}: {brief description}
    # Previous implementation had {problem}
    # Now correctly handles {scenario}
    if correct_condition:  # Fixed: was using wrong_condition
        return expected_result
```

**Update AI Context:**
```bash
python .augment/context/cli.py add integrated-workflow-2025-10-20 \
    "Fixed bug in {component}: {brief description}. Root cause: {root_cause}. Added regression test." \
    --importance 0.9
```

**GitHub Issue:**
```markdown
## Bug Fix: {brief description}

**Component:** {component}
**Severity:** {severity}
**Status:** Fixed

### Description
{detailed description}

### Root Cause
{root cause}

### Fix
{fix description}

### Testing
- [x] Regression test added
- [x] All tests pass
- [x] Integration tests pass
- [x] Quality gates pass

### Files Changed
- src/{component}/{file}.py
- tests/test_{component}.py

Closes #{issue_number}
```

---

## Validation Criteria

### Overall Success Criteria
- [ ] Bug reproduces reliably
- [ ] Root cause identified
- [ ] Fix implemented with regression test
- [ ] All tests pass
- [ ] No regressions introduced
- [ ] Quality gates pass
- [ ] Bug documented
- [ ] AI context updated

### Failure Criteria (Need More Work)
- Cannot reproduce bug
- Root cause unclear
- Fix introduces regressions
- Tests fail
- Quality gates fail

---

## Output/Deliverables

### 1. Bug Fix Report
```json
{
  "bug": {
    "description": "{description}",
    "component": "{component}",
    "severity": "{severity}",
    "reported_date": "{date}"
  },
  "investigation": {
    "root_cause": "{root_cause}",
    "affected_code": ["{file1}", "{file2}"]
  },
  "fix": {
    "description": "{fix_description}",
    "files_changed": ["{file1}", "{file2}"],
    "regression_test": "tests/test_{component}.py::test_bug_fix"
  },
  "validation": {
    "all_tests_pass": true,
    "coverage": "{coverage}%",
    "quality_gates": "passed"
  }
}
```

### 2. Regression Test
- New test that catches the bug
- Prevents future regressions
- Documents expected behavior

### 3. Updated Documentation
- Component failures memory updated
- Code comments added
- AI context updated

### 4. GitHub Issue
- Bug documented
- Fix documented
- Issue closed

---

## Integration with Primitives

### AI Context Management
```python
# Track bug investigation
context_manager.add_message(
    session_id="integrated-workflow-2025-10-20",
## Integration with Phase 1 Primitives

### AI Context Management
```python
# Track fix completion in Langfuse
langfuse.create_generation(
    trace=trace,
    name="bug-fix-complete",
    model="gemini-2.5-flash",
    prompt="Summarizing bug fix...",
    completion="Bug fixed. Root cause identified and resolved. Regression tests added."
)
```

### Error Recovery
```python
# Use error recovery for flaky tests
@with_retry(RetryConfig(max_retries=3, base_delay=1.0))
async def run_regression_test():
    # Test with automatic retry for transient failures
    pass
```

### Development Observability
```python
# Track bug fix metrics
@track_execution("bug_fix")
async def fix_bug(component: str, bug_id: str):
    # Bug fix tracked automatically
    pass

# Metrics tracked:
# - Time to reproduce
# - Time to fix
# - Number of files changed
# - Test coverage impact
```

---

## Common Bug Patterns

### 1. Async/Await Issues
```python
# Bug: Missing await
async def get_data():
    result = fetch_data()  # ❌ Missing await
    return result

# Fix:
async def get_data():
    result = await fetch_data()  # ✅ Added await
    return result
```

### 2. Database Connection Leaks
```python
# Bug: Connection not closed
async def get_session(session_id):
    redis = await create_redis_connection()
    data = await redis.get(f"session:{session_id}")
    return data  # ❌ Connection not closed

# Fix:
async def get_session(session_id):
    redis = await create_redis_connection()
    try:
        data = await redis.get(f"session:{session_id}")
        return data
    finally:
        await redis.close()  # ✅ Connection closed
```

### 3. Missing Error Handling
```python
# Bug: No error handling
async def get_ai_response(prompt):
    response = await ai_provider.generate(prompt)  # ❌ No error handling
    return response

# Fix:
async def get_ai_response(prompt):
    try:
        response = await ai_provider.generate(prompt)
        return response
    except RateLimitError:  # ✅ Handle rate limits
        logger.warning("Rate limit hit, using fallback")
        return await fallback_provider.generate(prompt)
    except AIProviderError as e:  # ✅ Handle other errors
        logger.error(f"AI provider error: {e}")
        raise
```

---

## Resources

### TTA Documentation
- Debugging Context: `.augment/context/debugging.context.md`
- Component Failures: `.augment/memory/component-failures.memory.md`
- Testing Patterns: `.augment/memory/testing-patterns.memory.md`

### Tools
- pytest: `uv run pytest`
- Debugger: `pdb`, `ipdb`
- Linting: `uvx ruff check`
- Type checking: `uvx pyright`

---

**Note:** Always write a regression test before fixing the bug. This ensures the bug is caught if it reappears.



---
**Logseq:** [[TTA.dev/Platform/Agent-context/.augment/Workflows/Bug-fix.prompt]]
