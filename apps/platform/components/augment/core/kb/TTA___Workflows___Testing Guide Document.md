---
title: 🧪 Efficient Testing Guide for TTA Codebase
tags: #TTA
status: Active
repo: theinterneti/TTA
path: TESTING_GUIDE.md
created: 2025-10-28
updated: 2025-10-28
---
# [[TTA/Workflows/🧪 Efficient Testing Guide for TTA Codebase]]

## 🎯 Testing Strategy Overview

Your TTA project has a **comprehensive testing infrastructure** with multiple layers and approaches. Here's how to test efficiently:

```
┌─────────────────────────────────────────────────────────────┐
│                    TTA Testing Pyramid                      │
├─────────────────────────────────────────────────────────────┤
│  E2E Tests (10%)        │ Full user workflows              │
│  Integration (20%)      │ Component interactions           │
│  Unit Tests (70%)       │ Individual functions/classes     │
└─────────────────────────────────────────────────────────────┘
       + Keploy (API Recording) + Comprehensive Battery
```

## 🚀 Quick Start: Run Tests NOW

### 1. **Unit Tests** (Fastest - Run First!)

```bash
# All unit tests
uv run pytest tests/unit/ -v

# Specific component
uv run pytest tests/unit/agent_orchestration/ -v

# With coverage
uv run pytest tests/unit/ --cov=src/agent_orchestration --cov-report=html

# Parallel execution (faster!)
uv run pytest tests/unit/ -n auto
```

### 2. **Integration Tests** (Require Services)

```bash
# Start services first
bash docker/scripts/tta-docker.sh dev up -d

# Run integration tests
uv run pytest tests/integration/ -v --neo4j --redis

# Specific integration
uv run pytest tests/integration/test_redis_integration.py -v
```

### 3. **API Tests with Keploy** (New!)

```bash
# Record real API interactions
./demo-api.sh  # Makes real API calls

# Then use Keploy for regression testing
# (Install Keploy first: curl -O https://keploy.io/install.sh && source install.sh)
keploy record -c "uv run python simple_test_api.py"
# Make some API calls, then:
keploy test -c "uv run python simple_test_api.py"
```

### 4. **Comprehensive Battery** (Full System)

```bash
# All test categories
cd tests/comprehensive_battery
python run_comprehensive_tests.py --all

# Specific categories
python run_comprehensive_tests.py --categories standard adversarial

# With detailed metrics
python run_comprehensive_tests.py --all --detailed-report --metrics
```

## 📊 Test Organization

### By Test Type

| Type | Location | When to Run | Speed |
|------|----------|-------------|-------|
| **Unit** | `tests/unit/` | Always (pre-commit) | ⚡ Fast |
| **Integration** | `tests/integration/` | Before PR | 🐢 Slower |
| **E2E** | `tests/e2e/` | Before merge | 🐌 Slowest |
| **API Recording** | Keploy | Continuous | ⚡ Fast |
| **Comprehensive** | `tests/comprehensive_battery/` | Nightly/Release | 🐌 Slowest |

### By Component

```bash
# Agent Orchestration
uv run pytest tests/unit/agent_orchestration/ -v

# Player Experience
uv run pytest tests/player_experience/ -v

# Common/Shared Utils
uv run pytest tests/common/ -v

# Monitoring
uv run pytest tests/monitoring/ -v
```

## 🎯 Efficient Testing Workflow

### **Daily Development** (Fast Feedback Loop)

```bash
# 1. Run unit tests for what you're changing
uv run pytest tests/unit/my_component/ -v

# 2. Check coverage
uv run pytest tests/unit/my_component/ --cov=src/my_component --cov-report=term

# 3. Run related integration tests
uv run pytest tests/integration/test_my_component_integration.py -v
```

### **Before Committing** (Quality Gate)

```bash
# 1. Format and lint
uv run ruff format src/ tests/
uv run ruff check src/ tests/ --fix

# 2. Type check
uv run pyright src/

# 3. Run all unit tests
uv run pytest tests/unit/ -v

# 4. Check coverage threshold (≥70% for dev)
uv run pytest tests/unit/ --cov=src --cov-report=term --cov-fail-under=70
```

### **Before Pull Request** (Full Validation)

```bash
# 1. All quality checks
uv run ruff format . && uv run ruff check . --fix && uv run pyright src/

# 2. All unit tests with coverage
uv run pytest tests/unit/ --cov=src --cov-report=html

# 3. Integration tests (services required)
bash docker/scripts/tta-docker.sh dev up -d
uv run pytest tests/integration/ -v --neo4j --redis

# 4. E2E tests
uv run pytest tests/e2e/ -v

# 5. API tests with Keploy (if applicable)
keploy test -c "uv run python simple_test_api.py"
```

### **Before Release** (Complete Battery)

```bash
# 1. Comprehensive test battery
cd tests/comprehensive_battery
python run_comprehensive_tests.py --all --detailed-report --metrics

# 2. Mutation testing (critical components)
uv run pytest tests/mutation/ -v

# 3. Performance tests
uv run pytest tests/performance/ -v

# 4. Security tests
uv run pytest tests/security/ -v
```

## 🔥 Speed Optimization Tips

### 1. **Parallel Execution**

```bash
# Run tests in parallel (auto-detect CPU cores)
uv run pytest tests/unit/ -n auto

# Or specify number of workers
uv run pytest tests/unit/ -n 4
```

### 2. **Run Only Changed Tests**

```bash
# Run tests that failed last time
uv run pytest --lf

# Run tests affected by changes
uv run pytest --testmon
```

### 3. **Skip Slow Tests During Dev**

```bash
# Skip slow tests
uv run pytest -m "not slow"

# Skip integration tests
uv run pytest -m "not integration"
```

### 4. **Use Test Markers**

```bash
# Only Redis tests
uv run pytest -m redis

# Only Neo4j tests
uv run pytest -m neo4j

# Fast tests only
uv run pytest -m "not slow and not integration"
```

## 📈 Coverage Tracking

### Check Coverage

```bash
# Generate HTML report
uv run pytest tests/unit/ --cov=src --cov-report=html

# View in browser
xdg-open htmlcov/index.html

# Terminal summary
uv run pytest tests/unit/ --cov=src --cov-report=term-missing
```

### Coverage Thresholds

**Component Maturity Levels**:
- **Development**: ≥70% coverage, ≥75% mutation score
- **Staging**: ≥80% coverage, ≥80% mutation score
- **Production**: ≥85% coverage, ≥85% mutation score

```bash
# Enforce coverage threshold
uv run pytest --cov=src --cov-fail-under=70
```

## 🤖 Automated Testing with Keploy

### Why Keploy?

- ✅ **Record real API interactions** as tests
- ✅ **No manual test writing** for regression
- ✅ **Automatic mocking** of dependencies
- ✅ **Fast execution** - replays in milliseconds

### Keploy Workflow

```bash
# 1. Start your API
uv run python simple_test_api.py &

# 2. Record interactions
keploy record -c "uv run python simple_test_api.py"

# 3. Use your API normally (or run demo)
./demo-api.sh

# 4. Stop recording (Ctrl+C)

# 5. Replay as tests (anytime)
keploy test -c "uv run python simple_test_api.py"
```

### Integrate Keploy into CI/CD

```yaml
# .github/workflows/test.yml
- name: Run Keploy Tests
  run: |
    ./keploy.sh test
```

## 🧩 Test Categories Explained

### **Standard Tests** (`tests/comprehensive_battery/test_suites/standard_test_suite.py`)
- User registration & authentication
- Character creation
- Story generation pipeline
- Session management

### **Adversarial Tests** (`tests/comprehensive_battery/test_suites/adversarial_test_suite.py`)
- Edge cases (malformed input)
- Security vulnerabilities
- Rate limiting
- Concurrent access conflicts

### **Load/Stress Tests** (`tests/comprehensive_battery/test_suites/load_stress_test_suite.py`)
- Concurrent user sessions
- High-frequency requests
- Resource exhaustion scenarios

### **Data Pipeline Tests** (`tests/comprehensive_battery/validators/data_pipeline_validator.py`)
- End-to-end data flow
- Data consistency
- Database integrity

### **Mutation Tests** (`tests/mutation/`)
- Code resilience to changes
- Test suite effectiveness

## 📋 Testing Checklist

### ✅ Pre-Commit Checklist
- [ ] Unit tests pass (`uv run pytest tests/unit/`)
- [ ] Code formatted (`uv run ruff format .`)
- [ ] Linting clean (`uv run ruff check . --fix`)
- [ ] Type checking passes (`uv run pyright src/`)
- [ ] Coverage ≥70% for changed files

### ✅ Pre-PR Checklist
- [ ] All unit tests pass
- [ ] Integration tests pass (with services running)
- [ ] E2E tests pass for affected workflows
- [ ] Coverage ≥80% for staging components
- [ ] No security vulnerabilities
- [ ] API tests recorded with Keploy (if applicable)

### ✅ Pre-Release Checklist
- [ ] Comprehensive test battery passes
- [ ] Mutation score ≥80%
- [ ] Performance benchmarks met
- [ ] Security audit clean
- [ ] Coverage ≥85% for production components

## 🛠️ Useful Commands Reference

### Quick Testing

```bash
# Fastest: Unit tests only
uv run pytest tests/unit/ -v

# Medium: With integration
uv run pytest tests/unit/ tests/integration/ -v

# Full: Everything
uv run pytest

# Watch mode (re-run on changes)
uv run pytest-watch tests/unit/
```

### Coverage

```bash
# Coverage report
uv run pytest --cov=src --cov-report=html

# Coverage with missing lines
uv run pytest --cov=src --cov-report=term-missing

# Coverage for specific module
uv run pytest tests/unit/agent_orchestration/ --cov=src/agent_orchestration
```

### Debugging

```bash
# Stop on first failure
uv run pytest -x

# Show print statements
uv run pytest -s

# More verbose output
uv run pytest -vv

# Run specific test
uv run pytest tests/unit/test_file.py::test_function_name
```

### Performance

```bash
# Show slowest tests
uv run pytest --durations=10

# Parallel execution
uv run pytest -n auto

# Skip slow tests
uv run pytest -m "not slow"
```

## 🎓 Next Steps

1. **Start with unit tests**: `uv run pytest tests/unit/ -v`
2. **Check coverage**: `uv run pytest tests/unit/ --cov=src --cov-report=html`
3. **Record API tests**: `keploy record -c "uv run python simple_test_api.py"`
4. **Set up pre-commit hooks**: Test automatically before commits
5. **Integrate into CI/CD**: Automated testing on every push

## 📚 Further Reading

- [[TTA/Workflows/testing-requirements.instructions|Testing Requirements]]
- [[TTA/Workflows/README|Testing Battery Guide]]
- [Component Maturity Workflow](AGENTS.md#component-maturity-workflow)
- [Keploy Documentation](https://keploy.io/docs/)

---

**🎉 You now have everything to test TTA efficiently!**

**Quick start**: `uv run pytest tests/unit/ -v --cov=src --cov-report=html`


---
**Logseq:** [[TTA.dev/Platform_tta_dev/Components/Augment/Core/Kb/Tta___workflows___testing guide document]]
