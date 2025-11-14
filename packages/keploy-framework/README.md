# Keploy Framework

**Production-ready framework for zero-code API test automation using Keploy**

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Code style: Ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)
[![Type checked: Pyright](https://img.shields.io/badge/type%20checked-pyright-blue.svg)](https://github.com/microsoft/pyright)

---

## 🎯 What is Keploy Framework?

A **battle-tested, production-ready** framework that makes it trivial to add Keploy automated testing to any Python API project. Eliminates 90% of the setup complexity and provides reusable automation patterns.

**Key Features**:
- 🚀 **One-Command Setup**: `keploy-setup` gets you running in 60 seconds
- 🤖 **Intelligent Test Runner**: Validates results, generates reports, integrates with CI/CD
- 🎨 **Interactive Menu**: Master control panel for all operations
- 🔄 **Pre-Commit Integration**: Optional test validation before commits
- 📊 **GitHub Actions Templates**: Drop-in CI/CD workflows
- 🎯 **Zero Config**: Sensible defaults, customize only what you need

**Philosophy**: Make API testing so easy that developers actually do it.

---

## 📦 Installation

```bash
# Install from PyPI (when published)
pip install keploy-framework

# Or install from source
pip install git+https://github.com/theinterneti/TTA.dev.git#subdirectory=packages/keploy-framework
```

---

## 🚀 Quick Start (60 seconds)

### 1. Initialize in Your Project

```bash
cd your-python-project/
keploy-setup
```

This creates:
- `keploy.yml` - Keploy configuration
- `scripts/master-keploy.sh` - Interactive menu
- `scripts/keploy-workflow.sh` - Automation script
- `.github/workflows/keploy-tests.yml` - CI/CD workflow (optional)

### 2. Start Your API

```bash
# Your existing API (e.g., FastAPI, Flask, Django)
uvicorn your_app:app --port 8000
```

### 3. Record Tests

```bash
./scripts/master-keploy.sh
# Choose option 2: "Record New Tests"
# Then interact with your API (curl, Postman, browser)
```

### 4. Run Tests

```bash
./scripts/master-keploy.sh
# Choose option 3: "Run All Tests"
# Watch as Keploy replays and validates
```

That's it! You now have automated API tests with zero code written.

---

## 🎨 Interactive Menu

The framework includes a beautiful TUI for all operations:

```
╔════════════════════════════════════════════════════════════╗
║           🤖 KEPLOY TEST AUTOMATION MENU                   ║
╠════════════════════════════════════════════════════════════╣
║                                                            ║
║  1. 🔍 Status Check        - Verify Keploy + API          ║
║  2. 📹 Record New Tests    - Capture API interactions     ║
║  3. ▶️  Run All Tests       - Execute full test suite     ║
║  4. 🎯 Run Specific Test   - Test individual case         ║
║  5. 🔄 Full Workflow       - Record + Test + Report       ║
║  6. 🧹 Clean Test Data     - Remove old tests             ║
║  7. 📊 Test Report         - View detailed results        ║
║  8. ⚙️  Configuration       - Edit keploy.yml             ║
║  9. 📚 Documentation       - View guides                  ║
║  0. ❌ Exit                                                ║
║                                                            ║
╚════════════════════════════════════════════════════════════╝
```

---

## 🔧 Python API

Use the framework programmatically in your tests:

```python
from keploy_framework import KeployTestRunner, RecordingSession

# Run tests with validation
runner = KeployTestRunner(api_url="http://localhost:8000")
results = await runner.run_all_tests()

print(f"Pass rate: {results.pass_rate}%")
print(f"Tests: {results.passed}/{results.total}")

# Record new tests
async with RecordingSession(api_url="http://localhost:8000") as session:
    # Your API interactions here
    response = await session.client.get("/api/users")
    
# Tests are automatically saved
```

---

## 📚 Framework Components

### 1. Test Runner (`keploy_framework.test_runner`)

Intelligent test execution with validation and reporting:

```python
from keploy_framework.test_runner import KeployTestRunner

runner = KeployTestRunner(
    api_url="http://localhost:8000",
    keploy_dir="./keploy",
    timeout=30,
)

results = await runner.run_tests(
    test_set="test-set-1",  # Optional: specific test set
    validate=True,           # Validate responses
    generate_report=True,    # Create HTML report
)
```

### 2. Recording Utilities (`keploy_framework.recorder`)

Simplified test recording with context managers:

```python
from keploy_framework.recorder import RecordingSession

async with RecordingSession(api_url="http://localhost:8000") as session:
    # All requests are automatically recorded
    await session.client.post("/api/login", json={"user": "test"})
    await session.client.get("/api/profile")
```

### 3. Validation (`keploy_framework.validation`)

Test result validation and assertions:

```python
from keploy_framework.validation import ResultValidator

validator = ResultValidator()

# Validate test results
is_valid = validator.validate_test_run(
    results=results,
    expected_pass_rate=0.8,  # Minimum 80% pass rate
)

assert is_valid, f"Test pass rate {results.pass_rate}% below threshold"
```

---

## 🎯 Templates

### GitHub Actions Workflow

Drop-in CI/CD for automated testing:

```yaml
# .github/workflows/keploy-tests.yml
name: Keploy API Tests

on:
  push:
    branches: [main, develop]
  pull_request:
  schedule:
    - cron: '0 2 * * *'  # Nightly at 2am

jobs:
  keploy-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Run Keploy Tests
        uses: keploy-framework/github-action@v1
        with:
          api-url: http://localhost:8000
          min-pass-rate: 80
          
      - name: Upload Report
        uses: actions/upload-artifact@v4
        with:
          name: keploy-report
          path: keploy-report.html
```

### Pre-Commit Hook

Validate tests before commits:

```bash
#!/bin/bash
# .git/hooks/pre-commit

# Run Keploy tests
keploy-test --quiet

if [ $? -ne 0 ]; then
    echo "❌ Keploy tests failed - commit blocked"
    exit 1
fi

echo "✅ Keploy tests passed"
```

---

## 📖 Advanced Usage

### Custom Configuration

```yaml
# keploy.yml
version: api.keploy.io/v1beta2
name: my-api-tests
app:
  command: uvicorn app:app --host 0.0.0.0 --port 8000
  port: 8000
  host: 0.0.0.0
test:
  path: ./keploy/tests
  globalNoise:
    global:
      body:
        - timestamp
        - request_id
    test-sets:
      auth-tests:
        body:
          - session_token
```

### Filtering Recorded Data

```python
from keploy_framework import KeployConfig

config = KeployConfig.load("keploy.yml")

# Add global noise filters
config.add_noise_filter("timestamp", scope="global")
config.add_noise_filter("session_id", scope="auth-tests")

config.save()
```

### Integration with Pytest

```python
import pytest
from keploy_framework import KeployTestRunner

@pytest.fixture
async def keploy_runner():
    return KeployTestRunner(api_url="http://localhost:8000")

@pytest.mark.integration
async def test_api_with_keploy(keploy_runner):
    results = await keploy_runner.run_all_tests()
    assert results.pass_rate >= 80, f"Only {results.pass_rate}% passed"
```

---

## 🏗️ Real-World Example: TTA Implementation

See the [TTA repository](https://github.com/theinterneti/TTA) for a complete reference implementation:

- **Setup**: [keploy.yml](https://github.com/theinterneti/TTA/blob/main/keploy.yml)
- **Automation**: [master-tta-testing.sh](https://github.com/theinterneti/TTA/blob/main/scripts/master-tta-testing.sh)
- **CI/CD**: [.github/workflows/keploy-tests.yml](https://github.com/theinterneti/TTA/blob/main/.github/workflows/keploy-tests.yml)
- **Documentation**: [Keploy Testing Guide](https://github.com/theinterneti/TTA/blob/main/docs/development/keploy-automated-testing.md)

**Results**: 88.9% pass rate, 9 automated tests, zero maintenance

---

## 🤝 Contributing

We welcome contributions! See [CONTRIBUTING.md](../../CONTRIBUTING.md) for guidelines.

---

## 📄 License

MIT License - see [LICENSE](../../LICENSE) for details.

---

## 🙏 Acknowledgments

Built on top of [Keploy](https://keploy.io) - the amazing open-source API testing platform.

---

**Questions?** Open an [issue](https://github.com/theinterneti/TTA.dev/issues) or join our [discussions](https://github.com/theinterneti/TTA.dev/discussions)!
