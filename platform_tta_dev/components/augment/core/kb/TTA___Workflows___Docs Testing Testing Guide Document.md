---
title: TTA Testing Guide
tags: #TTA
status: Active
repo: theinterneti/TTA
path: docs/testing/TESTING_GUIDE.md
created: 2025-11-01
updated: 2025-11-01
---
# [[TTA/Workflows/TTA Testing Guide]]

## Quick Reference

```bash
# Run automated tests (developers)
pytest tests/

# Run model evaluation (QA/research)
python testing/run_single_player_tests.py

# Run specific test file
pytest tests/test_api_integration.py -v

# Run tests with coverage
pytest tests/ --cov=src

# Run model evaluation (quick mode)
python testing/run_single_player_tests.py --mode quick
```

---

## Overview

The TTA project uses **two distinct testing approaches** to ensure quality:

1. **`tests/`** - Automated testing for code correctness
2. **`testing/`** - Quality assurance and model evaluation

Both are essential and serve complementary purposes.

---

## Directory Structure

```
TTA Project Root
├── tests/                    # Automated Testing (pytest)
│   ├── conftest.py          # pytest configuration
│   ├── test_*.py            # 952 automated tests
│   ├── agent_orchestration/ # Agent system tests
│   ├── integration/         # Integration tests
│   ├── e2e/                 # End-to-end tests
│   └── ...
│
└── testing/                  # QA & Evaluation (custom frameworks)
    ├── README.md            # Detailed documentation
    ├── single_player_test_framework.py
    ├── run_single_player_tests.py
    ├── extended_evaluation/ # Model evaluation tools
    ├── comprehensive_validation/
    └── results/             # Test results and reports
```

---

## 1. Automated Testing (`tests/`)

### Purpose

Verify code correctness through automated unit, integration, and end-to-end tests.

### When to Use

- ✅ Developing new features
- ✅ Fixing bugs
- ✅ Refactoring code
- ✅ Before committing changes
- ✅ In CI/CD pipelines

### How to Run

```bash
# Run all tests
pytest tests/

# Run specific test file
pytest tests/test_api_integration.py

# Run with verbose output
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html

# Run specific test function
pytest tests/test_api_integration.py::test_health_endpoint

# Run tests matching pattern
pytest tests/ -k "session"

# Run tests with specific marker
pytest tests/ -m "integration"
```

### Test Organization

```
tests/
├── test_*.py                 # Component-specific tests
├── agent_orchestration/      # Agent system tests
├── integration/              # Cross-component tests
├── e2e/                      # Full workflow tests
├── performance/              # Performance tests
└── helpers/                  # Test utilities
```

### Writing Tests

**Example test file:**

```python
# tests/test_my_feature.py
import pytest
from src.my_module import MyClass

def test_my_feature():
    """Test basic functionality."""
    obj = MyClass()
    result = obj.do_something()
    assert result == expected_value

@pytest.mark.asyncio
async def test_async_feature():
    """Test async functionality."""
    result = await async_function()
    assert result is not None
```

### VS Code Integration

Tests in `tests/` are automatically discovered by VS Code:

1. Open Testing panel (flask icon in sidebar)
2. Click "Refresh Tests"
3. Run tests directly from the panel

---

## 2. QA & Evaluation (`testing/`)

### Purpose

Evaluate AI models, validate user experience, and assess narrative quality.

### When to Use

- ✅ Comparing AI models
- ✅ Validating user experience
- ✅ Assessing narrative quality
- ✅ Performance/load testing
- ✅ Pre-release validation
- ✅ Research and analysis

### How to Run

```bash
# Quick test (one model, one scenario)
python testing/run_single_player_tests.py --mode quick

# Comprehensive test (all models, all scenarios)
python testing/run_single_player_tests.py --mode comprehensive

# Check configuration
python testing/run_single_player_tests.py --mode status

# Setup environment
python testing/setup_testing_environment.py

# Run extended evaluation
python testing/run_extended_evaluation.py

# Run model comparison
python testing/extended_evaluation/multi_model_comparison.py
```

### Evaluation Framework

**Focus Areas:**
1. **Narrative Quality (40%)** - Creativity, consistency, depth
2. **User Engagement (30%)** - Fun factor, immersion
3. **Therapeutic Integration (20%)** - Subtlety, effectiveness
4. **Technical Performance (10%)** - Response time, reliability

**Scoring Scale:** 1-10 points
- **Minimum Acceptable:** 6.0/10
- **Target Score:** 7.5/10
- **Excellence:** 8.5/10

### Test Scenarios

1. New Player Onboarding Journey
2. Multi-Session Story Continuity
3. Crisis Scenario Response
4. Character Development Journey
5. Choice Consequence Exploration

### Results

Results are saved in `testing/results/`:
```
testing/results/
├── raw_data/           # Raw test data
├── analysis/           # Analysis files
├── reports/            # Generated reports
└── logs/               # Execution logs
```

### Documentation

See `testing/README.md` for comprehensive documentation including:
- Detailed test scenarios
- Evaluation criteria
- Model configuration
- Prerequisites
- Troubleshooting

---

## 3. Comparison: `tests/` vs `testing/`

| Aspect | `tests/` | `testing/` |
|--------|----------|------------|
| **Purpose** | Code correctness | User experience & model evaluation |
| **Framework** | pytest | Custom frameworks |
| **Execution** | `pytest tests/` | `python testing/run_*.py` |
| **Frequency** | Every commit | Pre-release, research |
| **Duration** | Minutes | Hours |
| **Automation** | Fully automated | Semi-automated |
| **CI/CD** | Always runs | Manual trigger |
| **Audience** | Developers | QA, PM, researchers |
| **Output** | Pass/fail | Detailed reports & metrics |

---

## 4. Development Workflow

### Daily Development

```bash
# 1. Make code changes
vim src/my_module.py

# 2. Run relevant tests
pytest tests/test_my_module.py -v

# 3. Run all tests before commit
pytest tests/

# 4. Commit if tests pass
git add .
git commit -m "feat: add new feature"
```

### Pre-Release Validation

```bash
# 1. Run all automated tests
pytest tests/ --cov=src

# 2. Run model evaluation
python testing/run_single_player_tests.py --mode comprehensive

# 3. Review results
cat testing/results/reports/latest_report.md

# 4. Address any issues
# 5. Re-run tests
# 6. Proceed with release
```

---

## 5. CI/CD Integration

### Automated Tests (Always Run)

```yaml
# .github/workflows/tests.yml
name: Automated Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run tests
        run: pytest tests/ -v
```

### Evaluation (Manual Trigger)

```yaml
# .github/workflows/evaluation.yml
name: Model Evaluation
on: workflow_dispatch
jobs:
  evaluate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run evaluation
        run: python testing/run_single_player_tests.py --mode comprehensive
```

---

## 6. Prerequisites

### For `tests/` (Automated Testing)

**Required:**
- Python 3.10+
- pytest 8.4.2+
- Redis (localhost:6379)
- Neo4j (localhost:7687)

**Install:**
```bash
uv sync --all-extras
```

### For `testing/` (QA & Evaluation)

**Required:**
- All `tests/` prerequisites
- Local model server (LM Studio, Ollama, etc.)
- OpenRouter API key (for cloud models)

**Install:**
```bash
pip install -r testing/requirements-testing.txt
```

**Configure:**
```bash
export OPENROUTER_API_KEY=your_api_key_here
python testing/setup_testing_environment.py
```

---

## 7. Common Tasks

### Running Tests in VS Code

1. Open Testing panel (flask icon)
2. Click "Refresh Tests"
3. Click play button next to test
4. View results in panel

### Running Tests from Terminal

```bash
# All tests
pytest tests/

# Specific file
pytest tests/test_api_integration.py

# Specific test
pytest tests/test_api_integration.py::test_health_endpoint

# With markers
pytest tests/ -m "not integration"  # Skip integration tests
pytest tests/ -m "redis"            # Only Redis tests
```

### Debugging Failed Tests

```bash
# Run with verbose output
pytest tests/test_failing.py -v

# Run with print statements
pytest tests/test_failing.py -s

# Run with debugger
pytest tests/test_failing.py --pdb

# Run last failed tests
pytest tests/ --lf
```

### Generating Coverage Reports

```bash
# HTML report
pytest tests/ --cov=src --cov-report=html
open htmlcov/index.html

# Terminal report
pytest tests/ --cov=src --cov-report=term

# XML report (for CI)
pytest tests/ --cov=src --cov-report=xml
```

---

## 8. Best Practices

### For Automated Tests (`tests/`)

1. ✅ Write tests for all new features
2. ✅ Run tests before committing
3. ✅ Keep tests fast (< 1 second each)
4. ✅ Use fixtures for common setup
5. ✅ Use markers for test categories
6. ✅ Mock external dependencies
7. ✅ Test edge cases and error conditions

### For Evaluation (`testing/`)

1. ✅ Run comprehensive tests before releases
2. ✅ Document evaluation criteria
3. ✅ Save results for comparison
4. ✅ Review narrative quality manually
5. ✅ Test with diverse user profiles
6. ✅ Compare multiple models
7. ✅ Validate therapeutic effectiveness

---

## 9. Troubleshooting

### Tests Not Discovered

**Problem:** VS Code doesn't show tests

**Solution:**
```bash
# 1. Verify pytest works
pytest tests/ --collect-only

# 2. Clear cache
rm -rf .pytest_cache
rm -rf ~/.vscode-server/data/User/workspaceStorage/*/ms-python.python/

# 3. Restart VS Code
pkill -f 'vscode-server'
code .

# 4. Select interpreter
# Ctrl+Shift+P → "Python: Select Interpreter" → .venv/bin/python

# 5. Refresh tests
# Testing panel → Click "Refresh Tests"
```

### Evaluation Framework Issues

**Problem:** Model evaluation fails

**Solution:**
```bash
# 1. Check prerequisites
python testing/setup_testing_environment.py

# 2. Verify services
redis-cli ping  # Should return PONG
# Check Neo4j at http://localhost:7474

# 3. Check configuration
cat testing/model_testing_config.yaml

# 4. Test connection
python testing/extended_evaluation/test_openrouter_connection.py
```

---

## 10. Additional Resources

### Documentation

- **Automated Testing:** `pytest.ini`, VS Code Testing panel
- **QA & Evaluation:** `testing/README.md`
- **Directory Analysis:** `TESTING_DIRECTORIES_ANALYSIS.md`

### External Links

- **pytest Documentation:** https://docs.pytest.org/
- **VS Code Python Testing:** https://code.visualstudio.com/docs/python/testing

---

**Last Updated:** 2025-10-04
**Maintained By:** TTA Development Team


---
**Logseq:** [[TTA.dev/Platform_tta_dev/Components/Augment/Core/Kb/Tta___workflows___docs testing testing guide document]]
