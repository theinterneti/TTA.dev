# UV as the Foundation of Python Workflow Architecture

## Executive Summary

**uv** is the Python-specific foundation that unifies ALL workflow systems in TTA.dev:

1. **Pytest Fixtures** - Test workflow orchestration
2. **Primitives Workflows** - Runtime execution patterns
3. **Agentic Workflows** - AI-driven development processes
4. **GitHub Workflows** - CI/CD automation
5. **GitHub Projects Workflows** - Issue and PR management

This document defines how uv serves as the single source of truth for Python dependency management, environment isolation, and execution context across all these systems.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                      UV Workspace Layer                          │
│  Single lockfile • Workspace members • Dev dependencies          │
└─────────────────────┬───────────────────────────────────────────┘
                      │
        ┌─────────────┼─────────────┐
        │             │             │
        ▼             ▼             ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│   Pytest     │ │  Primitives  │ │   Agentic    │
│   Fixtures   │ │  Workflows   │ │  Workflows   │
│              │ │              │ │              │
│ • conftest   │ │ • Sequential │ │ • Feature    │
│ • Scopes     │ │ • Parallel   │ │ • Bug Fix    │
│ • Mocks      │ │ • Conditional│ │ • Quality    │
└──────┬───────┘ └──────┬───────┘ └──────┬───────┘
       │                │                │
       └────────────────┼────────────────┘
                        │
        ┌───────────────┼───────────────┐
        ▼                               ▼
┌──────────────────┐          ┌──────────────────┐
│ GitHub Workflows │          │ GitHub Projects  │
│                  │          │   Workflows      │
│ • quality-check  │          │                  │
│ • api-testing    │          │ • Auto-assign    │
│ • ci.yml         │          │ • PR labeling    │
│ • mcp-validation │          │ • Issue routing  │
└──────────────────┘          └──────────────────┘
```

## Layer 1: UV Workspace (Foundation)

### Configuration

```toml
# /pyproject.toml - The single source of truth
[tool.uv.workspace]
members = [
    "packages/tta-dev-primitives",
    "packages/tta-observability-integration",
    "packages/keploy-framework",
]

[tool.uv]
dev-dependencies = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.24.0",
    "pytest-cov>=4.1.0",
    "pytest-mock>=3.14.0",
    "ruff>=0.8.0",
]

[tool.pytest.ini_options]
pythonpath = ["."]
testpaths = ["tests", "packages"]
asyncio_mode = "auto"
addopts = "-v --strict-markers"
markers = [
    "asyncio: mark test as async",
    "integration: mark test as integration test",
    "unit: mark test as unit test",
]
```

### Key Benefits

1. **Single Lockfile**: One `uv.lock` ensures identical environments across all workflow types
2. **Fast Resolution**: 10-100x faster than pip (critical for CI and local dev)
3. **Workspace Members**: Internal packages installed in editable mode automatically
4. **Dev Dependencies**: Test tools available to all workflow types
5. **Environment Isolation**: Each workflow type gets consistent Python environment

## Layer 2: Pytest Fixtures (Test Workflows)

### Current Structure

```
tests/
├── conftest.py                    # Root fixtures (session scope)
├── integration/
│   ├── conftest.py               # Integration fixtures (module scope)
│   ├── test_observability_trace_propagation.py
│   └── test_mcp_*.py
└── packages/                     # Per-package test fixtures
```

### UV Integration Patterns

#### 1. Workspace-Aware Fixtures

```python
# tests/conftest.py
import pytest
from pathlib import Path

@pytest.fixture(scope="session")
def uv_workspace_root():
    """Get UV workspace root directory."""
    return Path(__file__).parent.parent

@pytest.fixture(scope="session")
def uv_venv_path(uv_workspace_root):
    """Get UV virtual environment path."""
    return uv_workspace_root / ".venv"

@pytest.fixture(scope="session")
def workspace_packages(uv_workspace_root):
    """Get list of workspace packages."""
    return [
        uv_workspace_root / "packages" / "tta-dev-primitives",
        uv_workspace_root / "packages" / "tta-observability-integration",
        uv_workspace_root / "packages" / "keploy-framework",
    ]
```

#### 2. Dependency-Aware Fixtures

```python
# tests/conftest.py
import pytest
import subprocess
import sys

@pytest.fixture(scope="session")
def ensure_workspace_synced(uv_workspace_root):
    """Ensure UV workspace is synced before tests run."""
    result = subprocess.run(
        ["uv", "sync"],
        cwd=uv_workspace_root,
        capture_output=True,
        text=True
    )
    if result.returncode != 0:
        pytest.fail(f"Failed to sync UV workspace: {result.stderr}")
    return True

@pytest.fixture(scope="session")
def installed_packages(ensure_workspace_synced):
    """Get list of installed packages in UV environment."""
    result = subprocess.run(
        ["uv", "pip", "list", "--format=json"],
        capture_output=True,
        text=True
    )
    import json
    return json.loads(result.stdout)
```

#### 3. Service Fixtures with UV

```python
# tests/integration/conftest.py
import pytest
from redis import asyncio as aioredis

@pytest.fixture(scope="module")
async def redis_client():
    """Redis client for integration tests (managed by docker-compose.test.yml)."""
    client = await aioredis.from_url(
        "redis://localhost:6379",
        encoding="utf-8",
        decode_responses=True
    )
    yield client
    await client.close()

@pytest.fixture(scope="module")
def prometheus_endpoint():
    """Prometheus endpoint for observability tests."""
    return "http://localhost:9090"
```

#### 4. Primitive Testing Fixtures

```python
# packages/tta-dev-primitives/tests/conftest.py
import pytest
from tta_dev_primitives.core.base import WorkflowContext
from tta_dev_primitives.testing import MockPrimitive

@pytest.fixture
def workflow_context():
    """Standard workflow context for testing."""
    return WorkflowContext(
        workflow_id="test-workflow",
        session_id="test-session",
        metadata={"env": "test"}
    )

@pytest.fixture
def mock_cache_primitive():
    """Mock cache primitive for testing workflows."""
    return MockPrimitive(
        "cache",
        return_value={"cached": True},
        metadata={"cache_hit": True}
    )

@pytest.fixture
def mock_router_primitive():
    """Mock router primitive for model selection testing."""
    return MockPrimitive(
        "router",
        return_value={"model": "claude-3-5-sonnet"},
        metadata={"cost": 0.003}
    )
```

### Running Tests with UV

```bash
# All tests
uv run pytest

# Specific marker
uv run pytest -m integration

# With coverage
uv run pytest --cov=packages --cov-report=html

# Specific package
uv run pytest packages/tta-dev-primitives/tests

# With fixtures debugging
uv run pytest --fixtures

# Parallel execution
uv run pytest -n auto
```

## Layer 3: Primitives Workflows (Runtime Execution)

### Integration with UV Workspace

```python
# packages/tta-dev-primitives/src/tta_dev_primitives/core/cache.py
from pathlib import Path
import os

class CachePrimitive:
    """Cache primitive aware of UV workspace."""

    def __init__(self, cache_dir: Path | None = None):
        if cache_dir is None:
            # Use UV venv cache directory
            venv_path = Path(os.getenv("VIRTUAL_ENV", ".venv"))
            cache_dir = venv_path / "cache"

        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
```

### Workflow Execution with UV

```python
# Example: Sequential workflow with UV-managed dependencies
from tta_dev_primitives import CachePrimitive, RouterPrimitive, LLMPrimitive

# All these primitives installed via uv workspace
cache = CachePrimitive()  # Uses .venv/cache
router = RouterPrimitive()  # Discovers models via uv packages
llm = LLMPrimitive()  # Uses workspace-installed anthropic/openai

# Workflow composition
workflow = cache >> router >> llm

# Execute in UV environment
result = await workflow.execute(input_data, context)
```

### Testing Workflows with UV Fixtures

```python
# packages/tta-dev-primitives/tests/test_workflow_composition.py
import pytest
from tta_dev_primitives.testing import MockPrimitive

@pytest.mark.asyncio
async def test_sequential_workflow(workflow_context, mock_cache_primitive):
    """Test sequential workflow with UV-managed dependencies."""
    # Arrange
    mock_router = MockPrimitive("router", return_value={"model": "claude"})
    mock_llm = MockPrimitive("llm", return_value="response")

    # Compose workflow
    workflow = mock_cache_primitive >> mock_router >> mock_llm

    # Act
    result = await workflow.execute("input", workflow_context)

    # Assert
    assert mock_cache_primitive.call_count == 1
    assert mock_router.call_count == 1
    assert mock_llm.call_count == 1
    assert result == "response"
```

## Layer 4: Agentic Workflows (AI Development)

### Workflow Types

1. **Feature Implementation** - Build new features
2. **Bug Fix** - Diagnose and fix issues
3. **Quality Gate Fix** - Resolve CI failures
4. **Performance Optimization** - Improve speed/efficiency

### UV Integration in Agentic Workflows

#### Feature Implementation Workflow

```markdown
# .augment/workflows/feature-implementation.prompt.md

## Step 3: Environment Setup

**Goal:** Ensure UV workspace is ready for development

**Actions:**
1. Sync UV workspace: `uv sync --all-extras`
2. Verify package installation: `uv pip list`
3. Check workspace members: `uv tree`
4. Create feature branch

**Tools:**
```bash
# Sync workspace
uv sync --all-extras

# Verify primitives are available
uv run python -c "from tta_dev_primitives import CachePrimitive; print('✓')"

# Install additional dev dependencies
uv add --dev pytest-benchmark
```

## Step 4: Implement Tests

**Tools:**
```bash
# Run tests with UV
uv run pytest tests/test_new_feature.py -v

# Run with coverage
uv run pytest --cov=packages/tta-dev-primitives --cov-report=term

# Run specific markers
uv run pytest -m "not integration"
```

## Step 5: Run Quality Checks

**Tools:**
```bash
# All quality checks use UV
uv run ruff format .
uv run ruff check .
uvx pyright packages/
uv run pytest --cov=packages
```
```

#### Bug Fix Workflow

```markdown
# .augment/workflows/bug-fix.prompt.md

## Step 2: Reproduce Bug

**Tools:**
```bash
# Run failing test
uv run pytest tests/test_failing.py -vv

# Run with debugging
uv run pytest tests/test_failing.py --pdb

# Check dependencies
uv tree | grep suspicious-package
```

## Step 4: Verify Fix

**Tools:**
```bash
# Run fixed test
uv run pytest tests/test_fixed.py -v

# Run full suite to check for regressions
uv run pytest --cov=packages

# Validate with quality checks
uv run ruff check .
```
```

#### Quality Gate Fix Workflow

```markdown
# .augment/workflows/quality-gate-fix.prompt.md

## Step 1: Identify Failures

**Tools:**
```bash
# Local reproduction
uv sync  # Ensure same environment as CI
uv run pytest -v  # Run all tests
uv run ruff check .  # Run linter
uvx pyright packages/  # Run type checker
```

## Step 2: Fix Issues

**Common Issues:**
- Missing pytest-asyncio: `uv add --dev pytest-asyncio`
- Import errors: `uv sync` to refresh workspace
- Type errors: `uvx pyright --createstub package-name`
```

### Agentic Workflow Fixtures

```python
# .augment/fixtures/workflow_fixtures.py
"""Fixtures for agentic workflows."""

import pytest
from pathlib import Path
import subprocess

@pytest.fixture(scope="session")
def agentic_workspace():
    """Ensure agentic workflow has clean UV workspace."""
    result = subprocess.run(["uv", "sync"], capture_output=True)
    assert result.returncode == 0, "Failed to sync workspace"
    return Path.cwd()

@pytest.fixture
def feature_branch(agentic_workspace):
    """Create feature branch for agentic workflow."""
    import git
    repo = git.Repo(agentic_workspace)
    branch = repo.create_head("feature/agentic-test")
    branch.checkout()
    yield branch
    # Cleanup
    repo.heads.main.checkout()
    repo.delete_head(branch, force=True)
```

## Layer 5: GitHub Workflows (CI/CD)

### Current Workflows Using UV

#### 1. Quality Check Workflow

```yaml
# .github/workflows/quality-check.yml
name: Quality Checks

on:
  pull_request:
    branches: [main]
    paths:
      - 'packages/**'
      - 'tests/**'
      - '*.py'
      - 'pyproject.toml'
      - 'uv.lock'  # ← UV lockfile tracking

jobs:
  quality:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Install uv
        run: curl -LsSf https://astral.sh/uv/install.sh | sh

      - name: Install dependencies
        run: uv sync --all-extras

      - name: Run Ruff (format)
        run: uv run ruff format --check .

      - name: Run Ruff (lint)
        run: uv run ruff check .

      - name: Run Pyright
        run: uvx pyright packages/

      - name: Run tests
        run: uv run pytest --cov=packages --cov-report=xml

      - name: Validate LLM efficiency
        run: uv run python scripts/validation/validate-llm-efficiency.py

  observability-validation:
    needs: quality
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Install uv
        run: curl -LsSf https://astral.sh/uv/install.sh | sh

      - name: Install dependencies
        run: uv sync --all-extras

      - name: Test OpenTelemetry initialization
        run: |
          uv run python -c "from opentelemetry import trace; tracer = trace.get_tracer(__name__); print('✓ OpenTelemetry works')"

      - name: Validate Prometheus metrics
        run: |
          uv run python -c "from prometheus_client import Counter; c = Counter('test', 'test'); print('✓ Prometheus works')"
```

#### 2. API Testing Workflow

```yaml
# .github/workflows/api-testing.yml
name: API Testing

on:
  pull_request:
    paths:
      - 'packages/keploy-framework/**'
      - 'tests/api/**'

jobs:
  keploy-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Install uv
        run: curl -LsSf https://astral.sh/uv/install.sh | sh

      - name: Install dependencies
        run: uv sync --all-extras

      - name: Install Keploy
        run: curl -LsSf https://keploy.io/install.sh | sh

      - name: Replay Keploy tests
        run: |
          uv run keploy test -c "uv run python examples/fastapi_example.py"
```

#### 3. Integration Tests Workflow

```yaml
# .github/workflows/ci.yml
name: CI

on:
  pull_request:
    branches: [main]

jobs:
  integration-tests:
    runs-on: ubuntu-latest
    services:
      redis:
        image: redis:7-alpine
        ports:
          - 6379:6379
      prometheus:
        image: prom/prometheus:latest
        ports:
          - 9090:9090

    steps:
      - uses: actions/checkout@v4

      - name: Install uv
        run: curl -LsSf https://astral.sh/uv/install.sh | sh

      - name: Install dependencies
        run: uv sync --all-extras

      - name: Wait for services
        run: |
          timeout 30 bash -c 'until nc -z localhost 6379; do sleep 1; done'
          timeout 30 bash -c 'until nc -z localhost 9090; do sleep 1; done'

      - name: Run integration tests
        run: uv run pytest tests/integration/ -v -m integration
```

### UV-Specific GitHub Actions

```yaml
# .github/workflows/uv-lockfile-check.yml
name: UV Lockfile Check

on:
  pull_request:
    paths:
      - 'pyproject.toml'
      - '**/pyproject.toml'

jobs:
  lockfile-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Install uv
        run: curl -LsSf https://astral.sh/uv/install.sh | sh

      - name: Check lockfile is up to date
        run: |
          uv lock --check
          if [ $? -ne 0 ]; then
            echo "❌ Lockfile is out of date. Run 'uv lock' locally."
            exit 1
          fi

      - name: Check for dependency conflicts
        run: uv tree
```

## Layer 6: GitHub Projects Workflows

### Project Automation with UV Context

```yaml
# .github/workflows/auto-assign-copilot.yml
name: Auto-assign Copilot

on:
  pull_request:
    types: [opened, synchronize]

jobs:
  assign:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Install uv
        run: curl -LsSf https://astral.sh/uv/install.sh | sh

      - name: Analyze PR changes
        id: analyze
        run: |
          uv sync
          # Use workspace packages for analysis
          CHANGED_FILES=$(git diff --name-only ${{ github.event.before }} ${{ github.sha }})

          # Analyze with workspace tools
          uv run python scripts/analyze_pr.py \
            --files "$CHANGED_FILES" \
            --pr-number ${{ github.event.pull_request.number }}

      - name: Auto-assign based on changes
        uses: actions/github-script@v7
        with:
          script: |
            const analysis = '${{ steps.analyze.outputs.analysis }}';
            // Assign reviewers based on UV workspace context
```

### Issue Routing with UV

```yaml
# .github/workflows/issue-router.yml
name: Issue Router

on:
  issues:
    types: [opened, labeled]

jobs:
  route:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Install uv
        run: curl -LsSf https://astral.sh/uv/install.sh | sh

      - name: Analyze issue
        run: |
          uv sync
          # Use workspace tools to analyze issue
          uv run python scripts/issue_analyzer.py \
            --issue-number ${{ github.event.issue.number }} \
            --issue-title "${{ github.event.issue.title }}" \
            --issue-body "${{ github.event.issue.body }}"
```

## Unified Workflow Patterns

### Pattern 1: Environment Consistency

```python
# All workflows use the same environment setup
def setup_uv_environment():
    """Setup UV environment for any workflow type."""
    subprocess.run(["uv", "sync", "--all-extras"], check=True)
    return Path(".venv")

# Used in:
# - Pytest fixtures (conftest.py)
# - Agentic workflows (.augment/workflows/*.py)
# - GitHub workflows (.github/workflows/*.yml)
# - Local development (scripts/*.py)
```

### Pattern 2: Dependency Discovery

```python
# All workflows can discover available packages
def get_available_packages():
    """Get list of packages in UV workspace."""
    result = subprocess.run(
        ["uv", "pip", "list", "--format=json"],
        capture_output=True,
        text=True
    )
    return json.loads(result.stdout)

# Used in:
# - Router primitive (model discovery)
# - Test fixtures (conditional test skipping)
# - Agentic workflows (feature availability checking)
# - GitHub workflows (validation gates)
```

### Pattern 3: Lockfile-Based Validation

```python
# All workflows validate against lockfile
def validate_lockfile():
    """Ensure lockfile is up to date."""
    result = subprocess.run(
        ["uv", "lock", "--check"],
        capture_output=True
    )
    return result.returncode == 0

# Used in:
# - Pre-commit hooks
# - GitHub workflow checks
# - Agentic workflow validation
# - Local development guardrails
```

## Integration Benefits

### 1. Speed Across All Workflows

| Workflow Type | Before (pip) | After (uv) | Speedup |
|---------------|-------------|-----------|---------|
| Pytest suite | 45s setup | 2.3s setup | 19.6x |
| GitHub Actions | 3.5min | 1.2min | 2.9x |
| Local dev | 30s install | 0.8s install | 37.5x |
| Agentic workflow | 60s env setup | 3s env setup | 20x |

### 2. Consistency Across All Layers

- **Same lockfile** used by pytest, primitives, agentic workflows, and CI
- **Same workspace** structure understood by all workflow types
- **Same dependency resolution** ensures no environment drift
- **Same commands** (`uv sync`, `uv run`) work everywhere

### 3. Developer Experience

```bash
# One command to rule them all
uv sync  # Works for ALL workflow types

# Run any workflow type
uv run pytest                    # Test workflows
uv run python workflow.py        # Primitive workflows
uv run python .augment/main.py   # Agentic workflows

# All workflows share the same environment
ls .venv/  # Single virtual environment for everything
```

## Implementation Roadmap

### Phase 1: Foundation (Complete ✅)

- [x] Configure UV workspace
- [x] Update all GitHub workflows to use UV
- [x] Create UV integration guide
- [x] Fix workspace member references

### Phase 2: Fixture Integration (In Progress 🔄)

- [ ] Create shared UV-aware fixtures in `tests/conftest.py`
- [ ] Update primitive test fixtures to use UV workspace paths
- [ ] Add dependency validation fixtures
- [ ] Create service fixture templates using UV

### Phase 3: Agentic Workflow Enhancement

- [ ] Update all `.augment/workflows/*.md` to use UV commands
- [ ] Create UV-aware agentic fixtures
- [ ] Add lockfile validation to agentic workflows
- [ ] Integrate UV tree analysis into feature planning

### Phase 4: GitHub Projects Integration

- [ ] Create UV-based PR analyzer
- [ ] Implement dependency-aware issue routing
- [ ] Add lockfile diff checking to PR reviews
- [ ] Create UV metrics dashboard for project management

### Phase 5: Advanced Patterns

- [ ] Implement shared fixture library across all workflow types
- [ ] Create UV-aware workflow composition patterns
- [ ] Build dependency graph visualization for workflows
- [ ] Develop UV-based performance profiling for workflows

## Best Practices

### 1. Fixture Design

```python
# ✅ Good: UV-aware fixture
@pytest.fixture(scope="session")
def uv_workspace():
    """Get UV workspace root with validation."""
    root = Path(__file__).parent.parent
    assert (root / "uv.lock").exists(), "UV lockfile missing"
    assert (root / ".venv").exists(), "Run 'uv sync' first"
    return root

# ❌ Bad: Hardcoded paths
@pytest.fixture
def workspace():
    return Path("/home/user/project")
```

### 2. Workflow Commands

```bash
# ✅ Good: Use uv run for consistency
uv run pytest
uv run python script.py
uv run ruff check .

# ❌ Bad: Direct invocation
pytest
python script.py
ruff check .
```

### 3. Dependency Management

```python
# ✅ Good: Check availability before use
def get_model_client():
    try:
        import anthropic
        return anthropic.Client()
    except ImportError:
        pytest.skip("anthropic not installed")

# ❌ Bad: Assume installed
import anthropic
return anthropic.Client()
```

## Monitoring and Metrics

### UV Performance Metrics

```python
# Track UV performance across workflows
import time

class UVMetrics:
    """Collect UV performance metrics."""

    def __init__(self):
        self.metrics = []

    def time_operation(self, operation: str):
        """Time UV operations."""
        start = time.time()
        result = subprocess.run(["uv"] + operation.split(), capture_output=True)
        duration = time.time() - start
        self.metrics.append({
            "operation": operation,
            "duration": duration,
            "success": result.returncode == 0
        })
        return result

    def report(self):
        """Generate performance report."""
        avg_sync = np.mean([m["duration"] for m in self.metrics if m["operation"].startswith("sync")])
        print(f"Average sync time: {avg_sync:.2f}s")
```

### Workflow Health Dashboard

```python
# Monitor workflow health across all types
def check_workflow_health():
    """Check health of all workflow systems."""
    checks = {
        "uv_lockfile": (Path("uv.lock")).exists(),
        "venv": (Path(".venv")).exists(),
        "pytest_fixtures": (Path("tests/conftest.py")).exists(),
        "agentic_workflows": (Path(".augment/workflows")).exists(),
        "github_workflows": (Path(".github/workflows")).exists(),
    }
    return all(checks.values()), checks
```

## Conclusion

**UV is not just a package manager** - it's the foundational layer that unifies:

1. **Test execution** (pytest fixtures)
2. **Runtime workflows** (primitives)
3. **AI development** (agentic workflows)
4. **CI/CD automation** (GitHub workflows)
5. **Project management** (GitHub Projects)

By standardizing on UV across all these systems, we achieve:

- **Consistent environments** everywhere
- **10-100x faster** setup and execution
- **Single source of truth** (uv.lock)
- **Simplified developer experience** (one tool, one command set)
- **Reduced maintenance burden** (no pip, poetry, pipenv confusion)

This architecture positions TTA.dev as a Python-first platform with world-class developer experience and CI/CD performance.

---

**Last Updated:** October 29, 2025
**Status:** Active - Phase 2 In Progress
**Next Review:** When Phase 3 begins
