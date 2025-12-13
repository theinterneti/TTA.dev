# TTA.dev Monorepo Structure

**Repository:** TTA.dev
**Purpose:** Comprehensive guide to monorepo organization and conventions
**Last Updated:** October 30, 2025

---

## Overview

TTA.dev uses a **monorepo structure** with multiple focused packages managed by `uv` workspace. This document explains the organization, conventions, and best practices for working in this monorepo.

### Key Principles

1. **Focused Packages** - Each package has a single, clear responsibility
2. **Independent Versioning** - Packages can be versioned and released independently
3. **Shared Tooling** - Common development tools (Ruff, Pyright, Pytest) configured at root
4. **Unified Documentation** - Central docs/ folder with cross-package guides

---

## Repository Structure

```text
TTA.dev/
├── packages/                        # All Python packages
│   ├── tta-dev-primitives/         # Core workflow primitives
│   ├── tta-observability-integration/ # Enhanced observability
│   ├── universal-agent-context/     # Agent coordination
│   ├── keploy-framework/            # API testing framework
│   └── python-pathway/              # Python analysis utilities
│
├── docs/                            # Centralized documentation
│   ├── architecture/                # System design docs
│   ├── guides/                      # How-to guides
│   ├── integration/                 # Integration docs
│   ├── examples/                    # Code examples
│   └── knowledge/                   # Conceptual guides
│
├── scripts/                         # Automation scripts
│   ├── validate-package.sh          # Package validation
│   ├── sync-deps.sh                 # Dependency sync
│   └── run-quality-checks.sh        # Quality checks
│
├── tests/                           # Integration tests
│   ├── integration/                 # Cross-package tests
│   └── e2e/                         # End-to-end tests
│
├── .github/                         # GitHub configuration
│   ├── workflows/                   # CI/CD workflows
│   ├── instructions/                # Copilot instructions
│   └── copilot-instructions.md      # Workspace Copilot guidance
│
├── .vscode/                         # VS Code configuration
│   ├── copilot-toolsets.jsonc      # Copilot toolsets
│   ├── tasks.json                   # VS Code tasks
│   └── settings.json                # Workspace settings
│
├── pyproject.toml                   # Root workspace configuration
├── uv.lock                          # Dependency lockfile
├── AGENTS.md                        # Primary agent instructions
├── README.md                        # Project overview
├── GETTING_STARTED.md               # Setup guide
└── PRIMITIVES_CATALOG.md            # Primitive reference
```

---

## Package Organization

### Standard Package Structure

Each package follows this structure:

```text
packages/<package-name>/
├── src/
│   └── <package_module>/
│       ├── __init__.py
│       ├── core/                    # Core functionality
│       ├── utils/                   # Utility functions
│       └── <feature_folders>/       # Feature-specific code
│
├── tests/
│   ├── unit/                        # Unit tests
│   ├── integration/                 # Integration tests
│   └── fixtures/                    # Test fixtures
│
├── examples/                        # Example usage
│   ├── basic_usage.py
│   └── advanced_patterns.py
│
├── pyproject.toml                   # Package configuration
├── README.md                        # Package documentation
├── AGENTS.md                        # Agent-specific guidance
└── CHANGELOG.md                     # Version history
```

### Package Details

#### 1. tta-dev-primitives

**Purpose:** Core workflow primitives and composition patterns

**Key Modules:**
- `core/` - Base abstractions (`WorkflowPrimitive`, `WorkflowContext`)
- `recovery/` - Recovery primitives (Retry, Fallback, Timeout, Compensation)
- `performance/` - Performance primitives (Cache)
- `testing/` - Testing utilities (`MockPrimitive`)
- `observability/` - Core observability (`InstrumentedPrimitive`)

**Dependencies:** Minimal (asyncio, dataclasses, abc)

**Used By:** All other packages

**Path:** `packages/tta-dev-primitives/`

#### 2. tta-observability-integration

**Purpose:** Enhanced observability with OpenTelemetry + Prometheus

**Key Modules:**
- `primitives/` - Enhanced primitives (Router, Cache, Timeout with metrics)
- `exporters/` - Prometheus/OTLP exporters
- `utils/` - Observability helpers

**Dependencies:** OpenTelemetry SDK, Prometheus client

**Depends On:** tta-dev-primitives

**Path:** `packages/tta-observability-integration/`

#### 3. universal-agent-context

**Purpose:** Agent coordination and context management

**Key Modules:**
- `context/` - Agent context management
- `coordination/` - Multi-agent coordination
- `state/` - State management

**Dependencies:** tta-dev-primitives

**Path:** `packages/universal-agent-context/`

#### 4. keploy-framework

**Purpose:** API test recording and replay

**Key Modules:**
- `recorder/` - Test recording
- `replayer/` - Test replay
- `mock/` - Mock generation

**Dependencies:** httpx, pytest

**Path:** `packages/keploy-framework/`

#### 5. python-pathway

**Purpose:** Python code analysis and utilities

**Key Modules:**
- `analysis/` - Code analysis
- `pathlib/` - Path management
- `utils/` - Utility functions

**Dependencies:** ast, pathlib

**Path:** `packages/python-pathway/`

---

## Dependency Management

### Workspace Configuration

Root `pyproject.toml` defines workspace:

```toml
[tool.uv.workspace]
members = [
    "packages/tta-dev-primitives",
    "packages/tta-observability-integration",
    "packages/universal-agent-context",
    "packages/keploy-framework",
    "packages/python-pathway",
]
```

### Package Dependencies

Each package has its own `pyproject.toml`:

```toml
[project]
name = "tta-observability-integration"
version = "2.0.0"
dependencies = [
    "tta-dev-primitives>=1.0.0",  # Workspace dependency
    "opentelemetry-api>=1.20.0",
    "opentelemetry-sdk>=1.20.0",
    "prometheus-client>=0.19.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "pytest-asyncio>=0.21.0",
    "pytest-cov>=4.1.0",
]
```

### Dependency Graph

```text
┌─────────────────────────────┐
│    tta-dev-primitives       │  (Core - no dependencies)
│    (Workflow Primitives)    │
└──────────────┬──────────────┘
               │
       ┌───────┴────────┬──────────────────┐
       │                │                  │
       ▼                ▼                  ▼
┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│Observability│  │   Agent     │  │   Keploy    │
│ Integration │  │   Context   │  │  Framework  │
└─────────────┘  └─────────────┘  └─────────────┘
       │
       ▼
┌─────────────┐
│   Python    │
│   Pathway   │
└─────────────┘
```

### Managing Dependencies

```bash
# Sync all workspace dependencies
uv sync --all-extras

# Add dependency to specific package
cd packages/tta-dev-primitives
uv add httpx

# Add dev dependency
uv add --dev pytest-asyncio

# Update dependencies
uv lock --upgrade
```

---

## Development Workflow

### Setting Up Workspace

```bash
# Clone repository
git clone https://github.com/theinterneti/TTA.dev.git
cd TTA.dev

# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Sync dependencies
uv sync --all-extras

# Verify setup
uv run pytest -v
```

### Working on a Package

```bash
# Navigate to package
cd packages/tta-dev-primitives

# Run package tests
uv run pytest tests/ -v

# Run specific test
uv run pytest tests/test_sequential.py -v

# With coverage
uv run pytest tests/ --cov=src --cov-report=html
```

### Cross-Package Development

```bash
# Make changes in tta-dev-primitives
cd packages/tta-dev-primitives
# ... edit code ...

# Test in dependent package
cd packages/tta-observability-integration
uv run pytest tests/  # Uses local tta-dev-primitives

# Run integration tests
cd ../..
uv run pytest tests/integration/
```

---

## Code Quality Tools

### Ruff (Formatting + Linting)

**Configuration:** Root `pyproject.toml`

```bash
# Format all code
uv run ruff format .

# Lint all code
uv run ruff check .

# Lint with auto-fix
uv run ruff check . --fix

# Check specific package
uv run ruff check packages/tta-dev-primitives/
```

### Pyright (Type Checking)

**Configuration:** Per-package `pyproject.toml`

```bash
# Type check all packages
uvx pyright packages/

# Type check specific package
uvx pyright packages/tta-dev-primitives/

# Type check with watch mode
uvx pyright --watch packages/
```

### Pytest (Testing)

**Configuration:** Root `pyproject.toml`

```bash
# Run all tests
uv run pytest -v

# Run package tests
uv run pytest packages/tta-dev-primitives/tests/ -v

# Run integration tests
uv run pytest tests/integration/ -v

# With coverage
uv run pytest --cov=packages --cov-report=html
```

### Quality Check Task

```bash
# Run all quality checks
uv run python scripts/quality-check.sh

# Or use VS Code task
# Tasks: Run Task > ✅ Quality Check (All)
```

---

## Documentation Standards

### Package Documentation

Each package must have:

1. **README.md**
   - Package overview
   - Installation instructions
   - API documentation
   - Usage examples
   - Contributing guidelines

2. **AGENTS.md** or `.github/copilot-instructions.md`
   - AI agent-specific guidance
   - Package architecture
   - Key patterns and conventions
   - Testing guidelines

3. **CHANGELOG.md**
   - Version history
   - Breaking changes
   - New features
   - Bug fixes

4. **examples/**
   - Working code examples
   - Common use cases
   - Advanced patterns

### Central Documentation

Located in `docs/`:

- **architecture/** - System design, ADRs, component analysis
- **guides/** - How-to guides, tutorials
- **integration/** - Integration documentation
- **examples/** - Cross-package examples
- **knowledge/** - Conceptual guides

### Documentation Updates

When making changes:

1. Update package README.md
2. Update relevant docs/ files
3. Add/update examples
4. Update CHANGELOG.md
5. Update AGENTS.md if architecture changes

---

## Testing Strategy

### Test Organization

```text
tests/
├── unit/                  # Per-package unit tests
│   └── packages/
│       └── tta-dev-primitives/
│           └── test_sequential.py
│
├── integration/           # Cross-package integration tests
│   ├── test_observability_integration.py
│   └── test_workflow_patterns.py
│
└── e2e/                   # End-to-end tests
    └── test_complete_workflows.py
```

### Test Levels

**Unit Tests** (per package)
- Fast, isolated
- Mock external dependencies
- 100% coverage goal
- Located in `packages/<name>/tests/`

**Integration Tests** (cross-package)
- Test package interactions
- Use real dependencies
- Located in `tests/integration/`

**End-to-End Tests**
- Test complete workflows
- May use Docker containers
- Located in `tests/e2e/`

### Running Tests

```bash
# All tests
uv run pytest -v

# Package unit tests only
uv run pytest packages/tta-dev-primitives/tests/ -v

# Integration tests only
uv run pytest tests/integration/ -v

# Specific test file
uv run pytest packages/tta-dev-primitives/tests/test_sequential.py -v

# With coverage
uv run pytest --cov=packages --cov-report=html --cov-report=term-missing
```

---

## CI/CD Pipeline

### GitHub Actions Workflows

Located in `.github/workflows/`:

**1. ci.yml** - Continuous Integration
- Runs on every push/PR
- Format check (Ruff)
- Lint check (Ruff)
- Type check (Pyright)
- Unit tests (Pytest)
- Coverage report (Codecov)

**2. integration-tests.yml** - Integration Tests
- Runs on PRs to main
- Cross-package integration tests
- Docker-based tests

**3. release.yml** - Release Automation
- Triggered by version tags
- Build packages
- Publish to PyPI (future)
- Create GitHub releases

### Running CI Locally

```bash
# Format check
uv run ruff format --check .

# Lint check
uv run ruff check .

# Type check
uvx pyright packages/

# Tests
uv run pytest -v

# Coverage
uv run pytest --cov=packages --cov-report=term-missing

# All checks (VS Code task)
# Tasks: Run Task > ✅ Quality Check (All)
```

---

## VS Code Integration

### Workspace Settings

`.vscode/settings.json` configures:
- Python interpreter (uv-managed venv)
- Ruff formatting on save
- Pyright type checking
- Pytest integration

### Tasks

`.vscode/tasks.json` defines:
- 🧪 Run All Tests
- 🧪 Run Tests with Coverage
- ✨ Format Code
- 🔍 Lint Code
- 🔬 Type Check
- ✅ Quality Check (All)
- 📦 Sync Dependencies

**Usage:** `Cmd+Shift+P` → "Tasks: Run Task"

### Copilot Toolsets

`.vscode/copilot-toolsets.jsonc` defines:
- `#tta-minimal` - Quick edits
- `#tta-package-dev` - Full development
- `#tta-testing` - Test development
- `#tta-observability` - Observability work

**Usage:** Type `#tta-package-dev` in Copilot chat

---

## Conventions

### Naming Conventions

**Packages:**
- Lowercase with hyphens: `tta-dev-primitives`
- Python module: `tta_dev_primitives`

**Files:**
- Lowercase with underscores: `base.py`, `sequential_primitive.py`
- Test files: `test_<module>.py`

**Classes:**
- PascalCase: `WorkflowPrimitive`, `SequentialPrimitive`

**Functions/Variables:**
- snake_case: `execute_workflow`, `input_data`

**Constants:**
- UPPER_SNAKE_CASE: `DEFAULT_TIMEOUT`, `MAX_RETRIES`

### Code Style

- **Line length:** 100 characters (Ruff configured)
- **Imports:** Sorted by Ruff (isort rules)
- **Docstrings:** Google style
- **Type hints:** Python 3.11+ syntax (`str | None` not `Optional[str]`)

### Git Conventions

**Branch naming:**
- `feature/` - New features
- `fix/` - Bug fixes
- `docs/` - Documentation
- `refactor/` - Refactoring
- `test/` - Test additions

**Commit messages:**
- Follow Conventional Commits
- Format: `type(scope): description`
- Examples:
  - `feat(primitives): add CachePrimitive`
  - `fix(observability): handle missing OTLP endpoint`
  - `docs(architecture): add ADR for operator overloading`

---

## Adding a New Package

### Step 1: Create Package Structure

```bash
# Create package directory
mkdir -p packages/new-package/src/new_package
mkdir -p packages/new-package/tests
mkdir -p packages/new-package/examples

# Create basic files
touch packages/new-package/src/new_package/__init__.py
touch packages/new-package/README.md
touch packages/new-package/AGENTS.md
touch packages/new-package/pyproject.toml
```

### Step 2: Configure pyproject.toml

```toml
[project]
name = "new-package"
version = "0.1.0"
description = "Description of package"
requires-python = ">=3.11"
dependencies = [
    "tta-dev-primitives>=1.0.0",  # If depends on primitives
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "pytest-asyncio>=0.21.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.ruff]
line-length = 100
```

### Step 3: Add to Workspace

Update root `pyproject.toml`:

```toml
[tool.uv.workspace]
members = [
    "packages/tta-dev-primitives",
    "packages/tta-observability-integration",
    # ... existing packages ...
    "packages/new-package",  # Add here
]
```

### Step 4: Write Documentation

Create comprehensive:
- README.md - Package overview and API
- AGENTS.md - Agent-specific guidance
- examples/ - Working code examples

### Step 5: Add Tests

```bash
# Create test structure
mkdir -p packages/new-package/tests/unit
mkdir -p packages/new-package/tests/integration

# Write tests
touch packages/new-package/tests/test_core.py
```

### Step 6: Sync and Test

```bash
# Sync workspace
uv sync --all-extras

# Run tests
uv run pytest packages/new-package/tests/ -v

# Run quality checks
uv run ruff format packages/new-package/
uv run ruff check packages/new-package/
uvx pyright packages/new-package/
```

---

## Troubleshooting

### Issue: Package Not Found

**Symptoms:**
```text
ModuleNotFoundError: No module named 'tta_dev_primitives'
```

**Solution:**
```bash
# Sync workspace dependencies
uv sync --all-extras

# Verify installation
uv run python -c "import tta_dev_primitives; print(tta_dev_primitives.__version__)"
```

### Issue: Version Conflicts

**Symptoms:**
```text
Unable to resolve dependencies
```

**Solution:**
```bash
# Clear lock file and re-resolve
rm uv.lock
uv sync --all-extras

# Or update specific package
uv add package-name --upgrade
```

### Issue: Type Check Failures

**Symptoms:**
```text
Pyright reports errors not shown in VS Code
```

**Solution:**
```bash
# Ensure using workspace Python
which python  # Should point to .venv

# Restart VS Code Python server
# Cmd+Shift+P → "Python: Restart Language Server"

# Run Pyright manually
uvx pyright packages/
```

---

## Best Practices

### Package Design

1. **Single Responsibility** - Each package does one thing well
2. **Minimal Dependencies** - Keep core packages lightweight
3. **Clear Boundaries** - Well-defined interfaces between packages
4. **Independent Testing** - Packages can be tested in isolation

### Dependency Management

1. **Pin Major Versions** - `package>=1.0.0,<2.0.0`
2. **Use Lockfile** - Commit `uv.lock` for reproducibility
3. **Regular Updates** - Run `uv lock --upgrade` monthly
4. **Audit Dependencies** - Review new dependencies carefully

### Testing

1. **100% Coverage Goal** - Especially for core primitives
2. **Fast Unit Tests** - Mock external dependencies
3. **Integration Tests** - Test real package interactions
4. **CI Coverage** - Enforce coverage thresholds

### Documentation

1. **Keep README Updated** - Document all public APIs
2. **Example-Driven** - Show real usage patterns
3. **Agent-Friendly** - Clear guidance in AGENTS.md
4. **Version Changelog** - Document all changes

---

## Related Documentation

- **Getting Started:** [`GETTING_STARTED.md`](../../GETTING_STARTED.md)
- **Agent Instructions:** [`AGENTS.md`](../../AGENTS.md)
- **Decision Records:** [`DECISION_RECORDS.md`](DECISION_RECORDS.md)
- **Component Integration:** [`COMPONENT_INTEGRATION_ANALYSIS.md`](COMPONENT_INTEGRATION_ANALYSIS.md)

---

**Last Updated:** October 30, 2025
**Maintainer:** TTA.dev Core Team


---
**Logseq:** [[TTA.dev/_archive/Nested_copies/Framework/Docs/Architecture/Monorepo_structure]]
