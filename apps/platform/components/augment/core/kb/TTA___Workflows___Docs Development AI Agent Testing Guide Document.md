---
title: AI Agent Testing Guide
tags: #TTA
status: Active
repo: theinterneti/TTA
path: docs/development/AI_AGENT_TESTING_GUIDE.md
created: 2025-11-01
updated: 2025-11-01
---
# [[TTA/Workflows/AI Agent Testing Guide]]

**Quick reference for AI agents to execute tests correctly and troubleshoot common issues.**

---

## Critical Rules

### Rule #1: ALWAYS Use `uv run pytest`

```bash
# ✅ CORRECT
uv run pytest

# ❌ WRONG - Causes 0% coverage
uvx pytest
```

**Why**: `uvx pytest` runs in an isolated environment without access to project dependencies, resulting in 0% coverage and false test results.

### Rule #2: Coverage Runs Automatically

```bash
# ✅ CORRECT - Coverage runs by default
uv run pytest

# ❌ UNNECESSARY - Coverage already configured
uv run pytest --cov=src --cov-report=html
```

**Why**: Coverage is configured in `pyproject.toml` to run automatically with every test execution.

### Rule #3: Verify Services for Integration Tests

```bash
# Check services are running
docker-compose ps

# Start services if needed
docker-compose up -d redis neo4j

# Then run integration tests
uv run pytest tests/integration/ --neo4j --redis
```

**Why**: Integration tests require Redis and Neo4j services to be running.

---

## Standard Commands

### Basic Test Execution

```bash
# Run all tests (most common)
uv run pytest

# Run with verbose output
uv run pytest -v

# Run with extra verbose output
uv run pytest -vv
```

### Test Selection

```bash
# Run specific test types
uv run pytest tests/unit/              # Unit tests only
uv run pytest tests/integration/       # Integration tests only
uv run pytest tests/e2e/              # End-to-end tests only

# Run specific file
uv run pytest tests/unit/test_example.py

# Run specific test function
uv run pytest tests/unit/test_example.py::test_function_name

# Run specific test class
uv run pytest tests/unit/test_example.py::TestClassName

# Run specific test method
uv run pytest tests/unit/test_example.py::TestClassName::test_method_name
```

### Test Filtering

```bash
# Skip slow tests
uv run pytest -m "not slow"

# Run only database tests
uv run pytest -m "redis or neo4j"

# Run failed tests only
uv run pytest --lf

# Run failed tests first, then all others
uv run pytest --ff
```

### Integration Tests

```bash
# Start services
docker-compose up -d redis neo4j

# Run integration tests
uv run pytest tests/integration/ --neo4j --redis

# Stop services
docker-compose down
```

---

## Expected Outputs

### Successful Test Run

```
============================= test session starts ==============================
platform linux -- Python 3.12.0, pytest-8.0.0, pluggy-1.4.0
rootdir: /path/to/project
configfile: pyproject.toml
plugins: asyncio-0.23.0, cov-4.1.0
collected 150 items

tests/unit/test_example.py ......................                        [ 15%]
tests/integration/test_redis.py ..........                               [ 21%]
...

---------- coverage: platform linux, python 3.12.0-final-0 -----------
Name                     Stmts   Miss  Cover   Missing
------------------------------------------------------
src/module.py              100     10    90%   45-50, 78
src/service.py             200     20    90%   120-125, 180-185
------------------------------------------------------
TOTAL                      300     30    90%

Required test coverage of 70.0% reached. Total coverage: 90.00%
========================== 150 passed in 5.23s ==============================
```

**Key Indicators:**
- ✅ All tests passed
- ✅ Coverage ≥ 70%
- ✅ No errors or warnings

### Failed Test Run

```
============================= test session starts ==============================
...
FAILED tests/unit/test_example.py::test_function - AssertionError: expected 5, got 3
========================== 1 failed, 149 passed in 5.45s ====================
```

**Key Indicators:**
- ❌ One or more tests failed
- 📝 Error message shows what failed and why

### Coverage Below Threshold

```
FAILED: Required test coverage of 70.0% not reached. Total coverage: 65.00%
```

**Key Indicators:**
- ❌ Coverage below 70% threshold
- 🔧 Need to add more tests or remove dead code

---

## Common Failures and Solutions

### Failure #1: Coverage Shows 0%

**Symptom:**
```
---------- coverage: platform linux, python 3.12.0-final-0 -----------
Name                     Stmts   Miss  Cover
--------------------------------------------
TOTAL                        0      0     0%
```

**Cause:** Using `uvx pytest` instead of `uv run pytest`

**Solution:**
```bash
# ❌ Wrong
uvx pytest

# ✅ Correct
uv run pytest
```

### Failure #2: Import Errors

**Symptom:**
```
ModuleNotFoundError: No module named 'src'
ImportError: cannot import name 'MyClass' from 'src.module'
```

**Cause:** Virtual environment not activated or dependencies not installed

**Solution:**
```bash
# Sync dependencies
uv sync --all-extras

# Verify virtual environment
which python  # Should show .venv/bin/python

# Run tests
uv run pytest
```

### Failure #3: Database Connection Errors

**Symptom:**
```
redis.exceptions.ConnectionError: Error connecting to Redis
neo4j.exceptions.ServiceUnavailable: Unable to connect to Neo4j
```

**Cause:** Services not running

**Solution:**
```bash
# Check services
docker-compose ps

# Start services
docker-compose up -d redis neo4j

# Verify services are healthy
docker-compose ps  # Should show "Up" status

# Run integration tests
uv run pytest tests/integration/ --neo4j --redis
```

### Failure #4: Tests Hang or Timeout

**Symptom:**
```
tests/integration/test_async.py::test_async_function ... (hangs indefinitely)
```

**Cause:** Async configuration issue or deadlock

**Solution:**
```bash
# Run with timeout
uv run pytest --timeout=60

# Check asyncio configuration in pyproject.toml
# [tool.pytest.ini_options]
# asyncio_mode = "auto"

# Run with verbose output to see where it hangs
uv run pytest -vv -s
```

### Failure #5: Tests Pass Locally but Fail in CI

**Symptom:**
```
Local: ✅ All tests passed
CI/CD: ❌ Tests failed
```

**Cause:** Environment differences, missing dependencies, or timing issues

**Solution:**
```bash
# Run tests in clean environment
uv venv --force  # Recreate virtual environment
uv sync --all-extras  # Reinstall dependencies
uv run pytest  # Run tests

# Check CI logs for specific errors
# - Review GitHub Actions logs
# - Look for environment-specific issues
# - Check service startup logs
```

---

## Troubleshooting Decision Tree

```
Test execution failed?
│
├─ Coverage shows 0%?
│  └─ YES → Check command
│     ├─ Using 'uvx pytest'? → Use 'uv run pytest' instead
│     └─ Using 'uv run pytest'? → Check pyproject.toml coverage config
│
├─ Import errors (ModuleNotFoundError)?
│  └─ YES → Run 'uv sync --all-extras' → Retry
│
├─ Database connection errors?
│  └─ YES → Check services
│     ├─ Run 'docker-compose ps'
│     ├─ Start services: 'docker-compose up -d redis neo4j'
│     └─ Retry tests
│
├─ Tests hang or timeout?
│  └─ YES → Add timeout flag
│     ├─ Run 'uv run pytest --timeout=60'
│     └─ Check async configuration in pyproject.toml
│
├─ Tests pass locally but fail in CI?
│  └─ YES → Check environment
│     ├─ Review GitHub Actions logs
│     ├─ Check for hardcoded paths
│     ├─ Verify service availability
│     └─ Check for timing issues
│
└─ Other errors?
   └─ Read error message carefully
      ├─ Check stack trace
      ├─ Review test code
      └─ Consult TESTING_INFRASTRUCTURE.md
```

---

## Best Practices

### 1. Always Verify Command

Before executing tests, verify you're using the correct command:

```bash
# ✅ Correct command
uv run pytest

# ❌ Common mistakes
uvx pytest           # Isolated environment, 0% coverage
pytest               # May use wrong Python version
python -m pytest     # May use wrong Python version
```

### 2. Read Output Carefully

Pay attention to:
- **Pass/Fail Status**: How many tests passed/failed?
- **Coverage Percentage**: Is it ≥ 70%?
- **Error Messages**: What specifically failed?
- **Missing Lines**: Which lines need test coverage?

### 3. Follow Decision Tree

Don't retry the same command repeatedly. Instead:
1. Identify the error type
2. Follow the troubleshooting decision tree
3. Apply the appropriate fix
4. Verify the fix worked
5. Retry the test

### 4. Report Results Clearly

When reporting test results, include:
- **Status**: Pass/Fail
- **Coverage**: Percentage and threshold
- **Failed Tests**: List of failed tests (if any)
- **Error Messages**: Specific errors encountered
- **Next Steps**: What needs to be done

**Example Report:**
```
Test Results:
✅ Status: PASSED
✅ Coverage: 85.23% (threshold: 70%)
✅ Tests: 150 passed, 0 failed
✅ Duration: 5.23s

Next Steps: None - all tests passing with good coverage
```

---

## Quick Reference

### Most Common Commands

```bash
# Run all tests
uv run pytest

# Run with verbose output
uv run pytest -v

# Run unit tests only
uv run pytest tests/unit/

# Run integration tests (requires services)
docker-compose up -d redis neo4j
uv run pytest tests/integration/ --neo4j --redis

# Run failed tests only
uv run pytest --lf

# View coverage report
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

### Coverage Thresholds

- **Development**: No minimum (aim for 70%+)
- **Staging**: 70% minimum (enforced)
- **Production**: 80% minimum (enforced)

### Coverage Reports

- **Terminal**: Shown after test execution
- **HTML**: `htmlcov/index.html` (interactive)
- **XML**: `coverage.xml` (machine-readable)

---

## Additional Resources

- **[[TTA/Workflows/TESTING_INFRASTRUCTURE|Testing Infrastructure Guide]]**: Comprehensive testing documentation
- **[[TTA/Workflows/COMPONENT_MATURITY_WORKFLOW|Component Maturity Workflow]]**: Quality gates and promotion criteria
- **[pytest Documentation](https://docs.pytest.org/)**: Official pytest documentation
- **[Coverage.py Documentation](https://coverage.readthedocs.io/)**: Coverage measurement documentation

---

**Last Updated**: 2025-10-23
**For**: AI Agents and Automated Systems
**Maintained By**: TTA Development Team


---
**Logseq:** [[TTA.dev/Platform_tta_dev/Components/Augment/Core/Kb/Tta___workflows___docs development ai agent testing guide document]]
