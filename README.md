# TTA.dev - Batteries-Included Workflow Primitives for AI Agents

**Clone, point your CLI agent, and start building reliable AI applications immediately.**

[![CI](https://github.com/theinterneti/TTA.dev/workflows/CI/badge.svg)](https://github.com/theinterneti/TTA.dev/actions)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Code style: Ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)
[![Type checked: Pyright](https://img.shields.io/badge/type%20checked-pyright-blue.svg)](https://github.com/microsoft/pyright)

---

## 🚀 Quick Start (30 seconds)

```bash
# 1. Clone
git clone https://github.com/theinterneti/TTA.dev
cd TTA.dev

# 2. Setup (one command)
./setup.sh

# 3. Point your CLI agent (Copilot/Claude/Cline) at this directory
# Your agent auto-detects AGENTS.md and starts using TTA.dev primitives!

# 4. (Optional) View observability dashboard
tta-dev-ui  # Opens at http://localhost:8501
```

**That's it!** TTA.dev is now powering your agent with production-ready primitives.

---

## 🎯 What is TTA.dev?

TTA.dev makes AI coding agents **reliable and production-ready** by providing:

✅ **Workflow Primitives** - Retry, timeout, circuit breaker, caching, parallelization  
✅ **Auto-Discovery** - CLI agents detect `AGENTS.md` and use primitives automatically  
✅ **Batteries-Included Observability** - Self-hosted dashboard that grows with your project  
✅ **Zero Config** - Works out of the box after `./setup.sh`

**The Vision:** Clone the repo → Agent detects it → Build reliable AI apps

---

## 📦 Repository Structure

```
TTA.dev/
├── setup.sh               # One-command setup
├── AGENTS.md              # Auto-detected by CLI agents
├── USER_JOURNEY.md        # End-to-end walkthrough
│
├── tta-dev/               # Unified Package (Batteries Included)
│   ├── primitives/        # Core workflow primitives
│   ├── observability/     # Built-in APM and tracing
│   ├── agents/            # Multi-agent coordination
│   ├── ui/                # Self-hosted observability dashboard
│   └── pyproject.toml     # Single source of truth
│
├── .github/               # 🤖 CI/CD & Agentic Workflows
│   ├── agents/            # Custom GitHub Copilot agents
│   ├── skills/            # Reusable agent skills
│   └── workflows/         # GitHub Actions (YAML + Markdown)
│
├── scripts/               # 🛠️ Automation Scripts
│   └── ci/                # CI helper scripts
│
├── logseq/                # 📚 Knowledge Base (Logseq)
│   ├── pages/             # Architecture docs & decisions
│   └── journals/          # Development journal
│
└── local/                 # 🏠 Local-Only (Not in Git)
    └── archive/           # Archived deprecated code
```

---

## 🏗️ Core Packages

### 1. `tta-primitives` (Production Ready)

Core workflow primitives for building reliable, observable AI agent workflows.

**Features:**
- 🔀 Composable primitives: Router, Cache, Timeout, Retry, Fallback
- 🔗 Composition operators (`>>`, `|`)
- ⚡ Parallel and sequential execution
- 📊 OpenTelemetry instrumentation built-in
- 💪 Circuit breakers and recovery patterns
- 📉 Cost reduction via intelligent caching and routing

**Installation:**
```bash
uv add tta-primitives
# or
pip install tta-primitives
```

**Quick Start:**
```python
from tta_dev_primitives import RetryPrimitive, CachePrimitive, WorkflowContext

# Build resilient workflows with composable primitives
workflow = CachePrimitive(ttl=3600) >> RetryPrimitive(max_attempts=3)
result = await workflow.execute(data, WorkflowContext())
```

[📚 Full Documentation](packages/tta-primitives/README.md)

---

### 2. `tta-observability` (Production Ready)

OpenTelemetry integration for distributed tracing, metrics, and logging.

**Features:**
- 📊 Automatic OpenTelemetry tracing and metrics
- 📝 Structured logging
- 📈 Prometheus-compatible metrics export
- 🛡️ Graceful degradation when observability backend is unavailable

**Installation:**
```bash
uv add tta-observability-integration
```

[📚 Full Documentation](platform/observability/README.md)

---

#### 3. `universal-agent-context` → `platform/agent-context/`

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

[📚 Full Documentation](platform/agent-context/README.md)

---

### Extended Platform (Active Development)

#### 4. `tta-agent-coordination` → `platform/agent-coordination/`

Atomic DevOps Architecture for multi-agent coordination.

[📚 Documentation](platform/agent-coordination/README.md)

#### 5. `tta-dev-integrations` → `platform/integrations/`

Pre-built integration primitives (Supabase, PostgreSQL, Clerk, JWT).

[📚 Documentation](platform/integrations/README.md)

#### 6. `tta-documentation-primitives` → `platform/documentation/`

Automated docs ↔ Logseq sync with AI metadata.

[📚 Documentation](platform/documentation/README.md)

#### 7. `tta-kb-automation` → `platform/kb-automation/`

Automated knowledge base maintenance (links, TODOs, flashcards).

[📚 Documentation](platform/kb-automation/README.md)

---

## 📱 Applications

### `tta-observability-ui` → `apps/observability-ui/`

LangSmith-inspired observability dashboard with VS Code webview integration.

**Features:**
- 📊 Real-time trace visualization
- 🔍 Primitive-aware debugging
- 🎯 VS Code integration (coming Phase 3)

[📚 Documentation](apps/observability-ui/README.md)

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
- **[Coding Standards](docs/guides/development/CodingStandards.md)** - Development best practices
- **[MCP Integration](MCP_SERVERS.md)** - Model Context Protocol guides
- **[Workspace Organization](docs/WORKSPACE_ORGANIZATION.md)** - Repository structure and navigation guide

### Additional Resources

- [PR Management Guide](docs/guides/pr-management-guide.md) - Intelligent PR oversight and automation
- [PR Management Quick Reference](docs/guides/pr-management-quickref.md) - Quick commands and best practices
- [LLM Cost Guide](docs/guides/llm-cost-guide.md) - Free vs paid model comparison, pricing analysis
- [Cost Optimization Patterns](docs/guides/cost-optimization-patterns.md) - Production patterns for 50-70% cost reduction
- [Cline Integration](docs/guides/CLINE_INTEGRATION_GUIDE.md) - Enhanced Cline development experience
- [AI Libraries Comparison](docs/guides/integration/AI_Libraries_Comparison.md)
- [Model Selection Guide](docs/reference/models/Model_Selection_Strategy.md)
- [LLM Selection Guide](docs/guides/llm-selection-guide.md)
- [Examples](platform/primitives/examples/)

---

## 🧪 Testing

All packages maintain **100% test coverage** with comprehensive test suites.

```bash
# Run all tests
uv run pytest -v

# Run with coverage
uv run pytest --cov=platform --cov=apps --cov-report=html

# Run specific package tests
uv run pytest platform/primitives/tests/ -v
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
uvx pyright platform/ apps/
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
   - 📊 PR Dashboard
   - 🔍 PR Analytics
   - 🏥 PR Triage
   - 🏥 PR Health Check
   - 💡 PR Recommendations

[See full task list](.vscode/tasks.json)

### PR Management

TTA.dev includes intelligent PR management tools:

```bash
# Dashboard - Visual overview of all open PRs
python scripts/pr_manager.py dashboard

# Analytics - Detailed metrics and insights
python scripts/pr_manager.py analyze

# Triage - Categorize and prioritize PRs
python scripts/pr_manager.py triage

# Health Check - Identify PRs needing attention
python scripts/pr_manager.py health-check

# Recommendations - Get actionable next steps
python scripts/pr_manager.py recommend
```

**Features:**
- 📊 Smart categorization (critical, ready-to-merge, stale, etc.)
- 🎯 Priority scoring (0-100) based on urgency and impact
- 🏥 Automated health monitoring
- 💡 Actionable recommendations
- 🔗 Integration with Logseq TODO system
- 🤖 Weekly automated monitoring via GitHub Actions

[See PR Management Guide](docs/guides/pr-management-guide.md) for details.

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
- **Phase 3 Examples:** See [`platform/primitives/examples/PHASE3_EXAMPLES_COMPLETE.md`](platform/primitives/examples/PHASE3_EXAMPLES_COMPLETE.md) for InstrumentedPrimitive pattern guide

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


---
**Logseq:** [[TTA.dev/Readme]]
