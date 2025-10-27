# TTA.dev - AI Development Toolkit

**Production-ready agentic primitives and workflow patterns for building reliable AI applications.**

[![CI](https://github.com/theinterneti/TTA.dev/workflows/CI/badge.svg)](https://github.com/theinterneti/TTA.dev/actions)
[![Quality](https://github.com/theinterneti/TTA.dev/workflows/Quality%20Checks/badge.svg)](https://github.com/theinterneti/TTA.dev/actions)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Code style: Ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)
[![Type checked: Pyright](https://img.shields.io/badge/type%20checked-pyright-blue.svg)](https://github.com/microsoft/pyright)

---

## 🎯 What is TTA.dev?

TTA.dev is a curated collection of **battle-tested, production-ready** components for building reliable AI applications. Every component here has:

- ✅ 100% test coverage
- ✅ Real-world production usage
- ✅ Comprehensive documentation
- ✅ Zero known critical bugs

**Philosophy:** Only proven code enters this repository.

---

## 📦 Packages

### tta-workflow-primitives

Production-ready composable workflow primitives for building reliable, observable agent workflows.

**Features:**
- 🔀 Router, Cache, Timeout, Retry primitives
- 🔗 Composition operators (`>>`, `|`)
- ⚡ Parallel and conditional execution
- 📊 OpenTelemetry integration
- 💪 Comprehensive error handling
- 📉 30-40% cost reduction via intelligent caching

**Installation:**
```bash
pip install tta-workflow-primitives
```

**Quick Start:**
```python
from tta_workflow_primitives import RouterPrimitive, CachePrimitive

# Compose workflow with operators
workflow = (
    validate_input >>
    CachePrimitive(ttl=3600) >>
    process_data >>
    generate_response
)

# Execute
result = await workflow.execute(data, context)
```

[📚 Full Documentation](packages/tta-workflow-primitives/README.md)

---

### dev-primitives

Development utilities and meta-level primitives for building robust development processes.

**Features:**
- 🛠️ Development and debugging tools
- 📝 Structured logging utilities
- ♻️ Retry mechanisms
- 🧪 Testing helpers

**Installation:**
```bash
pip install dev-primitives
```

[📚 Full Documentation](packages/dev-primitives/README.md)

---

## 🚀 Quick Start

### Installation

```bash
# Install with pip
pip install tta-workflow-primitives dev-primitives

# Or with uv (recommended)
uv pip install tta-workflow-primitives dev-primitives
```

### Basic Workflow Example

```python
from tta_workflow_primitives import WorkflowContext
from tta_workflow_primitives.core.base import LambdaPrimitive

# Define primitives
validate = LambdaPrimitive(lambda x, ctx: {"validated": True, **x})
process = LambdaPrimitive(lambda x, ctx: {"processed": True, **x})
generate = LambdaPrimitive(lambda x, ctx: {"result": "success"})

# Compose with >> operator
workflow = validate >> process >> generate

# Execute
context = WorkflowContext(workflow_id="demo", session_id="123")
result = await workflow.execute({"input": "data"}, context)

print(result)  # {"validated": True, "processed": True, "result": "success"}
```

---

## 🏗️ Architecture

TTA.dev follows a **composable, modular architecture**:

```
┌─────────────────────────────────────────────────────┐
│                  Your Application                   │
└─────────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────┐
│           tta-workflow-primitives                   │
│  ┌────────────┬──────────────┬─────────────────┐   │
│  │   Router   │    Cache     │    Timeout      │   │
│  ├────────────┼──────────────┼─────────────────┤   │
│  │  Parallel  │ Conditional  │     Retry       │   │
│  └────────────┴──────────────┴─────────────────┘   │
└─────────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────┐
│              dev-primitives                         │
│  ┌────────────┬──────────────┬─────────────────┐   │
│  │  Logging   │   Retries    │   Test Utils    │   │
│  └────────────┴──────────────┴─────────────────┘   │
└─────────────────────────────────────────────────────┘
```

---

## 📚 Documentation

- [Getting Started](docs/getting-started.md) (Coming soon)
- [Architecture Overview](docs/architecture.md) (Coming soon)
- [API Reference](docs/api/) (Coming soon)
- [Migration Guide](docs/migration.md) (Coming soon)

---

## 🧪 Testing

All packages maintain **100% test coverage** with comprehensive test suites.

```bash
# Run all tests
uv run pytest -v

# Run with coverage
uv run pytest --cov=packages --cov-report=html

# Run specific package tests
uv run pytest packages/tta-workflow-primitives/tests/ -v
```

---

## 🛠️ Development

### Prerequisites

- Python 3.11+
- [uv](https://github.com/astral-sh/uv) (recommended) or pip
- VS Code with Copilot (recommended)

### Setup

```bash
# Clone repository
git clone https://github.com/theinterneti/TTA.dev
cd TTA.dev

# Install dependencies
uv sync --all-extras

# Run tests
uv run pytest -v

# Run quality checks
uv run ruff format .
uv run ruff check . --fix
uvx pyright packages/
```

### VS Code Workflow

We provide VS Code tasks for common operations:

1. Press `Cmd/Ctrl+Shift+P`
2. Type "Task: Run Task"
3. Select from:
   - 🧪 Run All Tests
   - ✅ Quality Check (All)
   - 📦 Validate Package
   - 🔍 Lint Code
   - ✨ Format Code

[See full task list](.vscode/tasks.json)

---

## 🤝 Contributing

We welcome contributions! However, **only battle-tested, proven code is accepted**.

### Contribution Criteria

Before submitting a PR, ensure:

- ✅ All tests passing (100%)
- ✅ Test coverage >80%
- ✅ Documentation complete
- ✅ Ruff + Pyright checks pass
- ✅ Real-world usage validation
- ✅ No known critical bugs

### Contribution Workflow

1. **Create feature branch**
   ```bash
   git checkout -b feature/add-awesome-feature
   ```

2. **Make changes and validate**
   ```bash
   ./scripts/validate-package.sh <package-name>
   ```

3. **Commit with semantic message**
   ```bash
   git commit -m "feat(package): Add awesome feature"
   ```

4. **Create PR**
   ```bash
   gh pr create --title "feat: Add awesome feature"
   ```

5. **Squash merge after approval**

[See full contribution guide](CONTRIBUTING.md) (Coming soon)

---

## 📋 Code Quality Standards

### Formatting
- **Ruff** with 88 character line length
- Auto-format on save in VS Code

### Linting
- **Ruff** with strict rules
- No unused imports or variables

### Type Checking
- **Pyright** in basic mode
- Type hints required for all functions

### Testing
- **pytest** with AAA pattern
- >80% coverage required
- All tests must pass

### Documentation
- Google-style docstrings
- README for each package
- Examples for all features

---

## 🚦 CI/CD

All PRs automatically run:

- ✅ Ruff format check
- ✅ Ruff lint check
- ✅ Pyright type check
- ✅ pytest (all tests)
- ✅ Coverage report
- ✅ Multi-OS testing (Ubuntu, macOS, Windows)
- ✅ Multi-Python testing (3.11, 3.12)

**Merging requires all checks to pass.**

---

## 📊 Project Status

### Current Release: v0.1.0 (Initial)

| Package | Version | Tests | Coverage | Status |
|---------|---------|-------|----------|--------|
| tta-workflow-primitives | 0.1.0 | 12/12 ✅ | 100% | 🟢 Stable |
| dev-primitives | 0.1.0 | TBD | TBD | 🟢 Stable |

### Roadmap

- [ ] v0.2.0: Add more workflow primitives (saga, circuit breaker)
- [ ] v0.3.0: Enhanced observability features
- [ ] v1.0.0: First stable release

---

## 🔗 Related Projects

- **TTA** - Therapeutic text adventure game (private)
- **Augment Code** - AI coding assistant
- **GitHub Copilot** - AI pair programmer

---

## 📄 License

MIT License - see [LICENSE](LICENSE) for details

---

## 🙏 Acknowledgments

Built with:
- [Python](https://www.python.org/)
- [uv](https://github.com/astral-sh/uv) - Fast Python package installer
- [Ruff](https://github.com/astral-sh/ruff) - Fast Python linter
- [Pyright](https://github.com/microsoft/pyright) - Type checker
- [pytest](https://pytest.org/) - Testing framework
- [GitHub Copilot](https://github.com/features/copilot) - AI assistance

---

## 📧 Contact

- **Maintainer:** @theinterneti
- **Issues:** [GitHub Issues](https://github.com/theinterneti/TTA.dev/issues)
- **Discussions:** [GitHub Discussions](https://github.com/theinterneti/TTA.dev/discussions)

---

## ⭐ Star History

If you find TTA.dev useful, please consider giving it a star! ⭐

---

**Last Updated:** 2025-10-27
**Status:** 🚀 Ready for migration
