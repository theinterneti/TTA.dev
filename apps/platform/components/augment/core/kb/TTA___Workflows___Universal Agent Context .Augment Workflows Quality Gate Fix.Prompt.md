---
title: Agentic Workflow: Quality Gate Fix
tags: #TTA
status: Active
repo: theinterneti/TTA
path: packages/universal-agent-context/.augment/workflows/quality-gate-fix.prompt.md
created: 2025-11-01
updated: 2025-11-01
---
# [[TTA/Workflows/Agentic Workflow: Quality Gate Fix]]

**Purpose:** Systematically fix quality gate failures to enable component promotion

**Input Requirements:**
- Component name
- Failed quality gates (coverage, tests, linting, types, security)
- Target maturity stage (development/staging/production)
- Workflow report (optional, for detailed failure analysis)

---

## Workflow Description

This workflow guides the systematic resolution of quality gate failures, ensuring components meet TTA maturity criteria for promotion through development, staging, and production stages.

**Key Principles:**
- Fix root causes, not symptoms
- Maintain code quality while fixing
- Verify no regressions introduced
- Document fixes for future reference

---

## Step-by-Step Process

### Step 1: Identify Failed Quality Gates

**Goal:** Understand which quality gates failed and why

**Actions:**
1. Review workflow report or run quality gates
2. Identify failed gates
3. Categorize failures by type
4. Prioritize fixes

**Tools:**
```bash
# Run quality gates
python scripts/workflow/spec_to_production.py \
    --spec specs/component_name.md \
    --component component_name \
    --target staging

# View workflow report
cat workflow_report_component_name.json | jq '.stage_results.testing.quality_gates'

# Or run gates individually
uv run pytest tests/component_name/ --cov=src/component_name
uvx ruff check src/component_name/ tests/component_name/
uvx pyright src/component_name/
uvx detect-secrets scan src/component_name/
```

**Failure Categories:**
- **Coverage:** Test coverage below threshold
- **Tests:** Test failures
- **Linting:** Code style violations (ruff)
- **Types:** Type checking errors (pyright)
- **Security:** Secrets or vulnerabilities detected

**Example Output:**
```json
{
  "quality_gates": {
    "test_coverage": {
      "passed": false,
      "threshold": 70.0,
      "actual": 52.3,
      "message": "Coverage 52.3% below threshold 70.0%"
    },
    "test_pass_rate": {
      "passed": false,
      "total": 45,
      "passed_tests": 42,
      "failed_tests": 3,
      "message": "3 tests failed"
    },
    "linting": {
      "passed": false,
      "errors": 12,
      "message": "12 linting errors found"
    },
    "type_checking": {
      "passed": true
    },
    "security": {
      "passed": true
    }
  }
}
```

**AI Context Integration:**
```bash
# Create session for quality gate fixes
python .augment/context/cli.py new quality-gate-fix-component-2025-10-20

# Track failures
python .augment/context/cli.py add quality-gate-fix-component-2025-10-20 \
    "Quality gate failures: Coverage 52.3% (need 70%), 3 test failures, 12 linting errors" \
    --importance 1.0
```

---

### Step 2: Fix Test Failures

**Goal:** Resolve all failing tests

**Actions:**
1. Run failing tests locally
2. Analyze failure messages
3. Fix implementation or test
4. Verify tests pass
5. Ensure no regressions

**Common Test Failure Causes:**
- Missing pytest-asyncio decorator
- Incorrect assertions
- Mock configuration issues
- Race conditions in async tests
- Environment differences

**Example Fix:**
```python
# Failure: Missing async decorator
def test_async_function():  # ❌ Missing decorator
    result = await async_function()
    assert result is not None

# Fix:
@pytest.mark.asyncio  # ✅ Added decorator
async def test_async_function():
    result = await async_function()
    assert result is not None
```

**Tools:**
```bash
# Run specific failing test
uv run pytest tests/component_name/test_file.py::test_function -vv

# Run all tests
uv run pytest tests/component_name/ -v

# Run with debugging
uv run pytest tests/component_name/test_file.py::test_function --pdb
```

**Validation Criteria:**
- [ ] All tests pass
- [ ] No regressions introduced
- [ ] Test pass rate = 100%

**AI Context Integration:**
```bash
# Track test fixes
python .augment/context/cli.py add quality-gate-fix-component-2025-10-20 \
    "Fixed 3 test failures: Added pytest-asyncio decorators, fixed mock configuration" \
    --importance 0.9
```

---

### Step 3: Fix Coverage Issues

**Goal:** Increase test coverage to meet threshold

**Actions:**
1. Generate coverage report with missing lines
2. Identify critical uncovered code
3. Write tests for uncovered code
4. Verify coverage meets threshold

**Note:** For comprehensive coverage improvement, use `.augment/workflows/test-coverage-improvement.prompt.md`

**Quick Coverage Fix:**
```bash
# Generate coverage report
uv run pytest tests/component_name/ \
    --cov=src/component_name \
    --cov-report=html \
    --cov-report=term-missing

# Open HTML report to see uncovered lines
open htmlcov/index.html

# Write tests for critical uncovered code
# ... create test file ...

# Verify coverage
uv run pytest tests/component_name/ \
    --cov=src/component_name \
    --cov-report=term
```

**Validation Criteria:**
- [ ] Coverage ≥ threshold (60%/70%/80%)
- [ ] Critical code paths covered
- [ ] All new tests pass

**AI Context Integration:**
```bash
# Track coverage improvement
python .augment/context/cli.py add quality-gate-fix-component-2025-10-20 \
    "Coverage improved: 52.3% → 72.1% (added 8 tests)" \
    --importance 0.9
```

---

### Step 4: Fix Linting Errors

**Goal:** Resolve all code style violations

**Actions:**
1. Run ruff to identify errors
2. Use auto-fix for simple issues
3. Manually fix complex issues
4. Verify linting clean

**Common Linting Issues:**
- Unused imports
- Line too long
- Missing docstrings
- Unused variables
- Import order

**Tools:**
```bash
# Check linting errors
uvx ruff check src/component_name/ tests/component_name/

# Auto-fix simple issues
uvx ruff check --fix src/component_name/ tests/component_name/

# Format code
uvx ruff format src/component_name/ tests/component_name/

# Verify clean
uvx ruff check src/component_name/ tests/component_name/
```

**Example Fixes:**
```python
# Error: Unused import
import os  # ❌ Unused
from typing import Optional

# Fix: Remove unused import
from typing import Optional  # ✅ Only used imports

# Error: Line too long
def very_long_function_name_with_many_parameters(param1, param2, param3, param4, param5):  # ❌ Line too long
    pass

# Fix: Break into multiple lines
def very_long_function_name_with_many_parameters(  # ✅ Proper formatting
    param1,
    param2,
    param3,
    param4,
    param5,
):
    pass

# Error: Missing docstring
def process_data(data):  # ❌ Missing docstring
    return data.upper()

# Fix: Add docstring
def process_data(data: str) -> str:  # ✅ With docstring
    """Process data by converting to uppercase."""
    return data.upper()
```

**Validation Criteria:**
- [ ] No linting errors
- [ ] Code formatted consistently
- [ ] All functions have docstrings

**AI Context Integration:**
```bash
# Track linting fixes
python .augment/context/cli.py add quality-gate-fix-component-2025-10-20 \
    "Fixed 12 linting errors: Removed unused imports, added docstrings, formatted code" \
    --importance 0.7
```

---

### Step 5: Fix Type Checking Errors

**Goal:** Resolve all type checking errors

**Actions:**
1. Run pyright to identify errors
2. Add missing type hints
3. Fix type mismatches
4. Verify type checking clean

**Common Type Errors:**
- Missing type hints
- Type mismatches
- None handling
- Generic type issues

**Tools:**
```bash
# Check type errors
uvx pyright src/component_name/

# Check specific file
uvx pyright src/component_name/module.py
```

**Example Fixes:**
```python
# Error: Missing type hints
def process_items(items):  # ❌ No type hints
    return [item.upper() for item in items]

# Fix: Add type hints
def process_items(items: list[str]) -> list[str]:  # ✅ Type hints added
    return [item.upper() for item in items]

# Error: Type mismatch
def get_user_id(user: dict) -> int:  # ❌ Returns str, not int
    return user["id"]

# Fix: Correct return type
def get_user_id(user: dict) -> str:  # ✅ Correct type
    return user["id"]

# Error: None handling
def get_value(data: dict) -> str:  # ❌ Can return None
    return data.get("key")

# Fix: Handle None
def get_value(data: dict) -> Optional[str]:  # ✅ Correct type
    return data.get("key")
```

**Validation Criteria:**
- [ ] No type checking errors
- [ ] All functions have type hints
- [ ] Type hints are accurate

**AI Context Integration:**
```bash
# Track type fixes
python .augment/context/cli.py add quality-gate-fix-component-2025-10-20 \
    "Fixed type checking errors: Added type hints, fixed None handling" \
    --importance 0.7
```

---

### Step 6: Fix Security Issues

**Goal:** Resolve all security vulnerabilities

**Actions:**
1. Run security scan
2. Identify secrets or vulnerabilities
3. Remove hardcoded secrets
4. Use environment variables
5. Verify security scan clean

**Common Security Issues:**
- Hardcoded API keys
- Hardcoded passwords
- Exposed secrets in code
- Insecure configurations

**Tools:**
```bash
# Run security scan
uvx detect-secrets scan src/component_name/

# Scan specific file
uvx detect-secrets scan src/component_name/module.py
```

**Example Fixes:**
```python
# Error: Hardcoded API key
API_KEY = "sk-1234567890abcdef"  # ❌ Hardcoded secret

# Fix: Use environment variable
import os
API_KEY = os.getenv("OPENROUTER_API_KEY")  # ✅ From environment

# Error: Hardcoded password
def connect_db():
    return connect("postgresql://user:password123@localhost/db")  # ❌ Hardcoded

# Fix: Use environment variable
def connect_db():
    db_url = os.getenv("DATABASE_URL")  # ✅ From environment
    return connect(db_url)
```

**Validation Criteria:**
- [ ] No secrets in code
- [ ] All secrets in environment variables
- [ ] Security scan clean

**AI Context Integration:**
```bash
# Track security fixes
python .augment/context/cli.py add quality-gate-fix-component-2025-10-20 \
    "Fixed security issues: Removed hardcoded API keys, using environment variables" \
    --importance 0.9
```

---

### Step 7: Verify All Quality Gates Pass

**Goal:** Confirm all quality gates now pass

**Actions:**
1. Run full quality gate suite
2. Verify all gates pass
3. Generate quality report
4. Document fixes

**Tools:**
```bash
# Run full quality gates
python scripts/workflow/spec_to_production.py \
    --spec specs/component_name.md \
    --component component_name \
    --target staging

# View results
cat workflow_report_component_name.json | jq '.stage_results.testing.quality_gates'
```

**Expected Output:**
```json
{
  "quality_gates": {
    "test_coverage": {
      "passed": true,
      "threshold": 70.0,
      "actual": 72.1
    },
    "test_pass_rate": {
      "passed": true,
      "total": 53,
      "passed_tests": 53,
      "failed_tests": 0
    },
    "linting": {
      "passed": true,
      "errors": 0
    },
    "type_checking": {
      "passed": true
    },
    "security": {
      "passed": true
    }
  }
}
```

**Validation Criteria:**
- [ ] All quality gates pass
- [ ] No regressions introduced
- [ ] Component ready for promotion

**AI Context Integration:**
```bash
# Track completion
python .augment/context/cli.py add quality-gate-fix-component-2025-10-20 \
    "All quality gates pass: Coverage 72.1%, 53/53 tests pass, linting clean, types clean, security clean" \
    --importance 1.0
```

---

## Output/Deliverables

### Fixed Code
- [ ] All tests passing
- [ ] Coverage ≥ threshold
- [ ] Linting clean
- [ ] Type checking clean
- [ ] Security scan clean

### Quality Reports
- [ ] Quality gate report (all pass)
- [ ] Coverage report
- [ ] Test execution report

### Documentation
- [ ] Fixes documented in memory
- [ ] Lessons learned captured

---

## Integration with Phase 1 Primitives

### AI Context Management
```bash
# Track quality gate fix journey
python .augment/context/cli.py add quality-gate-fix-component-2025-10-20 \
    "Quality gate fixes complete: All gates pass, component ready for staging promotion" \
    --importance 1.0
```

### Error Recovery
- Automatic retry for transient test failures
- Circuit breaker for persistent failures

### Development Observability
- Quality gate metrics tracked
- Fix execution times recorded
- Dashboard shows quality trends

---

## Common Quality Gate Failure Patterns

### Pattern 1: Coverage Below Threshold
**Symptoms:** Coverage 52% but need 70%
**Solution:** Use `.augment/workflows/test-coverage-improvement.prompt.md`

### Pattern 2: Async Test Failures
**Symptoms:** Tests fail with "coroutine was never awaited"
**Solution:** Add `@pytest.mark.asyncio` decorator

### Pattern 3: Import Errors in Tests
**Symptoms:** `ModuleNotFoundError` when running tests
**Solution:** Use `uv run pytest` instead of `uvx pytest`

### Pattern 4: Linting Errors After Refactoring
**Symptoms:** Many linting errors after code changes
**Solution:** Run `uvx ruff check --fix` and `uvx ruff format`

---

## Resources

### TTA Documentation
- Quality Gates: `.augment/instructions/quality-gates.instructions.md`
- Testing Instructions: `.augment/instructions/testing.instructions.md`
- Quality Gates Memory: `.augment/memory/quality-gates.memory.md`
- Component Failures: `.augment/memory/component-failures.memory.md`

### Related Workflows
- Test Coverage Improvement: `.augment/workflows/test-coverage-improvement.prompt.md`
- Bug Fix: `.augment/workflows/bug-fix.prompt.md`
- Component Promotion: `.augment/workflows/component-promotion.prompt.md`

---

**Note:** Document all quality gate fixes in `.augment/memory/quality-gates.memory.md` for future reference.


---
**Logseq:** [[TTA.dev/Platform_tta_dev/Components/Augment/Core/Kb/Tta___workflows___universal agent context .augment workflows quality gate fix.prompt]]
