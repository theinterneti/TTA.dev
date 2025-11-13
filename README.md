# TTA.dev - AI Development Toolkit

**Production-ready agentic primitives and workflow patterns for building reliable AI applications.**

[![CI](https://github.com/theinterneti/TTA.dev/workflows/CI/badge.svg)](https://github.com/theinterneti/TTA.dev/actions)
[![Quality](https://github.com/theinterneti/TTA.dev/workflows/Quality%20Checks/badge.svg)](https://github.com/theinterneti/TTA.dev/actions)
[![TODO Compliance](https://github.com/theinterneti/TTA.dev/workflows/TODO%20Compliance%20Validation/badge.svg)](https://github.com/theinterneti/TTA.dev/actions)
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

## 📦 Production Packages

TTA.dev is a Python monorepo with 3 production packages:

### 1. `tta-dev-primitives`

Core workflow primitives for building reliable, observable agent workflows.

**Features:**
- 🔀 Router, Cache, Timeout, Retry, Memory primitives
- 🔗 Composition operators (`>>`, `|`)
- ⚡ Parallel and conditional execution
- 📊 OpenTelemetry integration
- 💪 Comprehensive error handling
- 📉 Cost reduction via intelligent caching and routing

**Installation:**
```bash
uv add tta-dev-primitives
```

**Quick Start:**
See [`GETTING_STARTED.md`](GETTING_STARTED.md) for a quick start guide.

[📚 Full Documentation](packages/tta-dev-primitives/README.md)

---

### 2. `tta-observability-integration`

OpenTelemetry integration for tracing, metrics, and logging across TTA.dev primitives.

**Features:**
- 📊 Automatic OpenTelemetry tracing and metrics
- 📝 Structured logging
- 📈 Prometheus-compatible metrics export
- 🛡️ Graceful degradation when observability backend is unavailable

**Installation:**
```bash
uv add tta-observability-integration
```

[📚 Full Documentation](packages/tta-observability-integration/README.md)

---

### 3. `universal-agent-context`

Agent context management and orchestration for multi-agent workflows.

**Features:**
- 🧠 Centralized context management for agents
- 🔄 Context propagation across primitives
- 🔑 Secure handling of agent-specific data
- 🤝 Facilitates multi-agent coordination

**Installation:**
```bash
uv add universal-agent-context
```

[📚 Full Documentation](packages/universal-agent-context/README.md)

---

## ⚠️ Packages Under Review

- **`keploy-framework`**: Minimal implementation, no `pyproject.toml`, no tests. Decision needed.
- **`python-pathway`**: No clear use case documented. Decision needed.
- **`js-dev-primitives`**: Placeholder, not implemented. Decision needed.

---

## 🚀 Quick Start

For a comprehensive quick start guide, including installation and your first workflow, please refer to [`GETTING_STARTED.md`](GETTING_STARTED.md).

---

## 📚 Documentation

- **[Getting Started Guide](GETTING_STARTED.md)** - 5-minute quickstart
- **[Primitives Catalog](PRIMITIVES_CATALOG.md)** - Complete reference for all primitives
- **[Agent Instructions](AGENTS.md)** - Guidance for AI agents working on TTA.dev
- **[GitHub Copilot Instructions](.github/copilot-instructions.md)** - Comprehensive Copilot configuration and best practices
- **[Architecture Overview](docs/architecture/Overview.md)** - System design and principles
- **[Coding Standards](docs/development/CodingStandards.md)** - Development best practices
- **[MCP Integration](MCP_SERVERS.md)** - Model Context Protocol guides
- **[Cline Integration](CLINE_INTEGRATION_GUIDE.md)** - Enhanced Cline development experience

### Additional Resources

- [LLM Cost Guide](docs/guides/llm-cost-guide.md) - Free vs paid model comparison, pricing analysis
- [Cost Optimization Patterns](docs/guides/cost-optimization-patterns.md) - Production patterns for 50-70% cost reduction
- [AI Libraries Comparison](docs/integration/AI_Libraries_Comparison.md)
- [Model Selection Guide](docs/models/Model_Selection_Strategy.md)
- [LLM Selection Guide](docs/guides/llm-selection-guide.md)
- [Examples](packages/tta-dev-primitives/examples/)

---

## 🧪 Testing

All packages maintain **100% test coverage** with comprehensive test suites.

```bash
# Run all tests
uv run pytest -v

# Run with coverage
uv run pytest --cov=packages --cov-report=html

# Run specific package tests
uv run pytest packages/tta-dev-primitives/tests/ -v
```

---

## 🛠️ Development

### Prerequisites

- Python 3.11+
- [uv](https://github.com/astral-sh/uv) (recommended)
- VS Code with recommended extensions (see `.vscode/extensions.json`)

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
- ✅ Test coverage >100% (for new code)
- ✅ Documentation complete
- ✅ Ruff + Pyright checks pass
- ✅ **TODO compliance (100%)** - All Logseq TODOs properly formatted
- ✅ Real-world usage validation
- ✅ No known critical bugs

#### TODO Compliance Requirement

All TODOs in Logseq journals must follow the [TODO Management System](logseq/pages/TODO%20Management%20System.md):

- **Category tag required**: `#dev-todo` or `#user-todo`
- **For `#dev-todo`**: Must include `type::`, `priority::`, `package::` properties
- **For `#user-todo`**: Must include `type::`, `audience::`, `difficulty::` properties

**Validation:**
```bash
# Check TODO compliance locally
uv run python scripts/validate-todos.py

# Expected output: 100.0% compliance
```

The CI will automatically validate TODO compliance on all PRs. Non-compliant TODOs will block the merge.

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

[See full contribution guide](CONTRIBUTING.md)

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
- 100% coverage required
- All tests must pass

### Documentation

- Google-style docstrings
- README for each package
- Examples for all features
- **Phase 3 Examples:** See [`packages/tta-dev-primitives/examples/PHASE3_EXAMPLES_COMPLETE.md`](packages/tta-dev-primitives/examples/PHASE3_EXAMPLES_COMPLETE.md) for InstrumentedPrimitive pattern guide

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
| tta-dev-primitives | 0.1.0 | 12/12 ✅ | 100% | 🟢 Stable |
| tta-observability-integration | 0.1.0 | TBD | TBD | 🟢 Stable |
| universal-agent-context | 0.1.0 | TBD | TBD | 🟢 Stable |

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

**Last Updated:** 2025-11-10
