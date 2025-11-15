# GitHub Copilot Instructions for TTA.dev

This file provides workspace-level guidance for GitHub Copilot when working with TTA.dev.

---

## 📍 CRITICAL: Know Your Context

**This file is read by MULTIPLE Copilot contexts. Know which one YOU are:**

### 🖥️ **Are you the VS Code Extension? (LOCAL)**

- ✅ Running in developer's VS Code on local machine
- ✅ Have access to: MCP servers, Copilot toolsets, local filesystem
- ✅ Read sections marked: 🎯 (all), 🖥️ (local only)
- ❌ Ignore sections marked: ☁️ (cloud only - not for you)

### ☁️ **Are you the Coding Agent? (CLOUD/GitHub Actions)**

- ✅ Running in ephemeral GitHub Actions environment
- ✅ Have access to: GitHub Actions tools, installed packages
- ✅ Read sections marked: 🎯 (all), ☁️ (cloud only)
- ❌ Ignore sections marked: 🖥️ (local only - not available to you)
- ⚠️ **You do NOT have access to:** MCP servers, VS Code extensions, Copilot toolsets

### 💻 **Are you the GitHub CLI? (TERMINAL)**

- ✅ Running in terminal via `gh copilot`
- ✅ Have access to: Terminal environment, GitHub API
- ✅ Read sections marked: 🎯 (all)
- ❌ Ignore sections marked: 🖥️ (local) and ☁️ (cloud)

**Not sure which you are?**
- In VS Code with chat UI? → 🖥️ VS Code Extension
- In GitHub Actions workflow logs? → ☁️ Coding Agent
- In terminal with `gh copilot`? → 💻 GitHub CLI

---

## 🎯 FOR ALL CONTEXTS: Project Overview

**TTA.dev** is a production-ready AI development toolkit providing composable agentic primitives for building reliable AI workflows.

### Core Concepts

- **Agentic Primitives**: Reusable workflow components that compose via operators
- **Type-Safe Composition**: `>>` (sequential) and `|` (parallel) operators
- **Built-in Observability**: OpenTelemetry integration across all primitives
- **Recovery Patterns**: Retry, Fallback, Timeout, Compensation primitives
- **Monorepo Structure**: Multiple focused packages in `/packages`

### � Observability Persistence Check (Required for Local Sessions)

**🖥️ LOCAL ONLY:** If you're the VS Code Extension, verify observability infrastructure on session start:

```bash
./scripts/verify-and-setup-persistence.sh
```

**What this checks:**
- ✅ Agent activity tracker (systemd service)
- ✅ Docker containers (Jaeger, Prometheus, Grafana, OTLP, Pushgateway)
- ✅ Restart policies configured
- ✅ Git post-commit hook installed

**If not set up:** The script will offer to run `./scripts/setup-persistence.sh` automatically.

**Why this matters:** TTA.dev's observability infrastructure must be running to track agent activity, capture metrics, and provide distributed tracing. Without it, you're working blind.

**Documentation:** See `scripts/PERSISTENCE_SETUP.md` for details.

---

### �📋 TODO Management (Required for All Agents)

**ALL agents must use the Logseq TODO management system:**

- **System Documentation:** `logseq/pages/TODO Management System.md`
- **Daily Journals:** `logseq/journals/YYYY_MM_DD.md`
- **Tag Convention:**
  - `#dev-todo` - Development tasks (code, tests, CI/CD, infrastructure)
  - `#user-todo` - User/agent tasks (learning, onboarding, examples)

**Agent Requirements:**

1. **Add TODOs:** When creating work items, add to today's journal with proper tags/properties
2. **Update Status:** Mark tasks as DOING when starting, DONE when complete
3. **Link Context:** Use `related::` property to link Logseq pages
4. **Document Blockers:** Use `blocked::` and `blocker::` properties
5. **Daily Review:** Check TODO dashboards before/after work sessions

**Properties to Use:**

```markdown
- TODO [Task] #dev-todo
  type:: implementation | testing | documentation | infrastructure
  priority:: high | medium | low
  package:: [package-name]
  related:: [[Page Reference]]
  status:: not-started | in-progress | blocked | waiting
```

**See:** `logseq/ADVANCED_FEATURES.md` for complete Logseq usage guide.

---

## 🎯 FOR ALL CONTEXTS: Monorepo Structure

### Package Architecture

```text
TTA.dev/
├── packages/
│   ├── tta-dev-primitives/          # Core workflow primitives (START HERE)
│   ├── tta-observability-integration/  # OpenTelemetry + Prometheus
│   ├── universal-agent-context/      # Agent context management
│   ├── keploy-framework/             # API testing framework
│   └── python-pathway/               # Python analysis utilities
├── docs/                             # Documentation
├── scripts/                          # Automation scripts
└── tests/                            # Integration tests
```

### When to Use Which Package

| Task | Package | Files to Focus On |
|------|---------|------------------|
| Creating new workflow primitives | `tta-dev-primitives` | `src/tta_dev_primitives/core/`, `examples/` |
| Adding recovery patterns | `tta-dev-primitives` | `src/tta_dev_primitives/recovery/` |
| Adding observability | `tta-observability-integration` | `src/observability_integration/primitives/` |
| Agent coordination | `universal-agent-context` | `src/universal_agent_context/` |
| API testing | `keploy-framework` | `src/keploy_framework/` |
| Python code analysis | `python-pathway` | `src/python_pathway/` |

---

## Key Patterns & Best Practices

### 1. Workflow Primitive Composition

**Always use primitives** instead of manual async orchestration:

```python
# ✅ GOOD - Use primitive composition
from tta_dev_primitives import SequentialPrimitive, ParallelPrimitive

workflow = (
    input_processor >>
    (fast_llm | slow_llm | cached_llm) >>
    aggregator
)

# ❌ BAD - Manual async orchestration
async def workflow(input_data):
    processed = await input_processor(input_data)
    results = await asyncio.gather(
        fast_llm(processed),
        slow_llm(processed),
        cached_llm(processed)
    )
    return await aggregator(results)
```

### 2. WorkflowContext for State Management

**Always pass state via WorkflowContext**:

```python
# ✅ GOOD - Use WorkflowContext
from tta_dev_primitives import WorkflowContext

context = WorkflowContext(
    correlation_id="req-123",
    data={"user_id": "user-789"}
)
result = await workflow.execute(context, input_data)

# ❌ BAD - Global variables or function parameters
USER_ID = "user-789"  # Don't use globals
```

### 3. Type Safety

**Use Python 3.11+ type hints**:

```python
# ✅ GOOD - Modern type hints
def process(data: str | None) -> dict[str, Any]:
    ...

class MyPrimitive(WorkflowPrimitive[InputModel, OutputModel]):
    async def _execute_impl(
        self,
        context: WorkflowContext,
        input_data: InputModel
    ) -> OutputModel:
        ...

# ❌ BAD - Old type hints
from typing import Optional, Dict

def process(data: Optional[str]) -> Dict[str, Any]:
    ...
```

### 4. Recovery Patterns

**Use recovery primitives** instead of manual error handling:

```python
# ✅ GOOD - Use RetryPrimitive
from tta_dev_primitives.recovery import RetryPrimitive

workflow = RetryPrimitive(
    primitive=api_call,
    max_retries=3,
    backoff_strategy="exponential"
)

# ❌ BAD - Manual retry logic
async def api_call_with_retry():
    for i in range(3):
        try:
            return await api_call()
        except Exception:
            await asyncio.sleep(2 ** i)
    raise Exception("Failed after retries")
```

### 5. Testing

**Use MockPrimitive for testing**:

```python
# ✅ GOOD - Use MockPrimitive
from tta_dev_primitives.testing import MockPrimitive
import pytest

@pytest.mark.asyncio
async def test_workflow():
    mock_llm = MockPrimitive(return_value={"output": "test"})
    workflow = step1 >> mock_llm >> step3
    result = await workflow.execute(context, input_data)
    assert mock_llm.call_count == 1

# ❌ BAD - Complex mocking
@patch('module.llm_call')
async def test_workflow(mock_llm):
    mock_llm.return_value = {"output": "test"}
    ...
```

---

## 🖥️ FOR VS CODE EXTENSION ONLY: Copilot Toolsets

**⚠️ Coding Agent:** This section is NOT for you. Toolsets are a VS Code feature not available in GitHub Actions.

TTA.dev provides **focused toolsets** to optimize your workflow. Use the appropriate toolset hashtag in your Copilot chat:

### Core Development Toolsets

| Toolset | When to Use | Tools Included |
|---------|-------------|----------------|
| `#tta-minimal` | Quick edits, reading code | search, read_file, edit, problems |
| `#tta-package-dev` | Developing primitives | All dev tools + runTests, configurePythonEnvironment |
| `#tta-testing` | Writing/running tests | runTests, edit, search, terminal, get_errors |
| `#tta-observability` | Tracing/metrics work | Prometheus, Loki, observability tools + dev tools |

### Specialized Toolsets

| Toolset | When to Use | Tools Included |
|---------|-------------|----------------|
| `#tta-agent-dev` | Building AI agents | Context7, AI Toolkit, agent development tools |
| `#tta-mcp-integration` | MCP server work | MCP tools, semantic search, documentation |
| `#tta-validation` | Running quality checks | Linting, type checking, validation scripts |
| `#tta-pr-review` | Reviewing PRs | GitHub PR tools, diff analysis, changed files |

**Full toolset documentation:** [`.vscode/README.md`](.vscode/README.md)

---

## Common Workflows

### Adding a New Primitive

1. **Create primitive class** in `packages/tta-dev-primitives/src/tta_dev_primitives/`
   - Extend `WorkflowPrimitive[InputType, OutputType]`
   - Implement `_execute_impl()` method
   - Add type hints and docstrings

2. **Add tests** in `packages/tta-dev-primitives/tests/`
   - Test success case
   - Test error cases
   - Test edge cases
   - Aim for 100% coverage

3. **Create example** in `packages/tta-dev-primitives/examples/`
   - Show real-world usage
   - Include comments explaining pattern
   - Demonstrate composition

4. **Update documentation**
   - Add to package README
   - Update `PRIMITIVES_CATALOG.md`
   - Update relevant guides in `docs/`

**Use toolset:** `#tta-package-dev`

### Adding Observability

1. **Choose package:**
   - Core tracing → `tta-observability-integration`
   - Primitive-specific → `tta-dev-primitives/observability/`

2. **Follow OpenTelemetry standards:**
   - Use span names: `primitive_name.operation`
   - Add attributes for context
   - Record events for key milestones
   - Handle errors properly

3. **Test with Prometheus:**
   ```bash
   docker-compose -f docker-compose.test.yml up -d
   # Run your code
   # Check http://localhost:9090
   ```

**Use toolset:** `#tta-observability`

### Running Tests

```bash
# All tests
uv run pytest -v

# Specific package
uv run pytest packages/tta-dev-primitives/tests/ -v

# With coverage
uv run pytest --cov=packages --cov-report=html

# Integration tests
uv run pytest tests/integration/ -v
```

**Use toolset:** `#tta-testing`

---

## File-Type Specific Instructions

TTA.dev uses **path-based instruction files** in `.github/instructions/`:

| File Pattern | Instruction File | Key Rules |
|--------------|-----------------|-----------|
| `packages/**/src/**/*.py` | `package-source.instructions.md` | Production quality, full types, comprehensive tests |
| `**/tests/**/*.py` | `tests.instructions.md` | 100% coverage, pytest-asyncio, MockPrimitive usage |
| `scripts/**/*.py` | `scripts.instructions.md` | Use primitives for orchestration, clear documentation |
| `**/*.md`, `**/README.md` | `documentation.instructions.md` | Clear, actionable, with code examples |
| `**` (all files) | `logseq-knowledge-base.instructions.md` | Use Logseq for TODOs, journals, and knowledge management |

**Always check the relevant instruction file** before editing files of that type.

---

## Package Manager: uv (NOT pip)

TTA.dev uses **uv** for dependency management:

```bash
# ✅ CORRECT - Use uv
uv add package-name                  # Add dependency
uv sync --all-extras                 # Sync all dependencies
uv run pytest                        # Run command in venv
uv run python script.py              # Run Python script

# ❌ WRONG - Don't use pip
pip install package-name             # Don't do this
python -m pip install package-name   # Don't do this
```

---

## Code Quality Standards

### Required Checks Before Commit

1. **Format code:** `uv run ruff format .`
2. **Lint code:** `uv run ruff check . --fix`
3. **Type check:** `uvx pyright packages/`
4. **Run tests:** `uv run pytest -v`

**Shortcut:** Use VS Code task `✅ Quality Check (All)`

### Type Checking

- **100% type coverage required** for all public APIs
- Use `pyright` (built into Pylance)
- Configure in `pyproject.toml` per package

### Testing Standards

- **100% coverage required** for all new code
- Use `pytest` with `pytest-asyncio`
- Mock external services with `MockPrimitive`
- Test success, failure, and edge cases

---

## Anti-Patterns to Avoid

| ❌ Don't Do This | ✅ Do This Instead |
|-----------------|-------------------|
| Manual async orchestration | Use `SequentialPrimitive` or `ParallelPrimitive` |
| Try/except with retry loops | Use `RetryPrimitive` |
| `asyncio.wait_for()` for timeouts | Use `TimeoutPrimitive` |
| Manual caching with dicts | Use `CachePrimitive` |
| Global variables for state | Use `WorkflowContext` |
| `pip install` | Use `uv add` |
| `Optional[T]` type hints | Use `T \| None` |
| Modifying core primitives | Extend via composition |

---

## Observability Best Practices

### Structured Logging

```python
import structlog

logger = structlog.get_logger(__name__)

logger.info(
    "workflow_executed",
    workflow_name="my_workflow",
    duration_ms=123.45,
    status="success"
)
```

### Tracing

```python
from opentelemetry import trace

tracer = trace.get_tracer(__name__)

async def my_operation():
    with tracer.start_as_current_span("my_operation") as span:
        span.set_attribute("input_size", len(data))
        # ... do work ...
        span.add_event("processing_complete")
```

### Context Propagation

```python
# WorkflowContext automatically propagates:
# - correlation_id
# - user_id
# - request metadata
# - parent span context

context = WorkflowContext(
    correlation_id="req-123",
    data={"user_id": "user-789"}
)

# All primitives in workflow get this context
result = await workflow.execute(context, input_data)
```

---

## Example References

### Basic Workflow Composition

**File:** `packages/tta-dev-primitives/examples/basic_sequential.py`

Shows sequential composition with `>>` operator.

### Parallel Execution

**File:** `packages/tta-dev-primitives/examples/parallel_execution.py`

Shows parallel composition with `|` operator.

### LLM Router

**File:** `packages/tta-dev-primitives/examples/router_llm_selection.py`

Shows dynamic routing between different LLMs.

### Error Handling

**File:** `packages/tta-dev-primitives/examples/error_handling_patterns.py`

Shows retry, fallback, timeout patterns.

### Real-World Workflows

**File:** `packages/tta-dev-primitives/examples/real_world_workflows.py`

Shows complete production-ready workflows.

---

## Documentation Structure

### Main Documentation

| Document | Purpose |
|----------|---------|
| [`AGENTS.md`](AGENTS.md) | Primary agent instructions (START HERE) |
| [`README.md`](README.md) | Project overview |
| [`GETTING_STARTED.md`](GETTING_STARTED.md) | Setup guide |
| [`PRIMITIVES_CATALOG.md`](PRIMITIVES_CATALOG.md) | Complete primitive reference |
| [`MCP_SERVERS.md`](MCP_SERVERS.md) | MCP server integrations |

### Package Documentation

Each package in `/packages` has:

- `README.md` - API documentation
- `AGENTS.md` or `.github/copilot-instructions.md` - Agent guidance
- `examples/` - Working code examples
- `tests/` - Test suite

### Guides & Architecture

- `docs/guides/` - Usage guides and tutorials
- `docs/architecture/` - Architecture decisions
- `docs/integration/` - Integration patterns
- `docs/observability/` - Observability setup

---

## Quick Decision Guide

### "Should I create a new primitive?"

**YES if:**

- Pattern is reusable across workflows
- Has clear input/output types
- Can be composed with other primitives
- Adds observability value

**NO if:**

- One-off operation (just use a function)
- Tightly coupled to specific workflow
- Doesn't need observability

### "Should I modify an existing primitive?"

**YES if:**

- Fixing a bug
- Adding optional parameter (backward compatible)
- Improving performance without breaking API

**NO if:**

- Breaking change (create new primitive instead)
- Adding workflow-specific logic
- Changing core behavior

### "Which package does this belong in?"

- **Workflow patterns** → `tta-dev-primitives`
- **Tracing/metrics** → `tta-observability-integration`
- **Agent coordination** → `universal-agent-context`
- **API testing** → `keploy-framework`
- **Python analysis** → `python-pathway`

---

## Troubleshooting

### Import Errors

```bash
# Make sure dependencies are synced
uv sync --all-extras

# Check Python version
python --version  # Should be 3.11+

# Verify in virtual environment
which python  # Should point to .venv/bin/python
```

### Type Errors

```bash
# Run type checker
uvx pyright packages/

# Check specific file
uvx pyright packages/tta-dev-primitives/src/tta_dev_primitives/core/base.py
```

### Test Failures

```bash
# Run with verbose output
uv run pytest -v -s

# Run specific test
uv run pytest packages/tta-dev-primitives/tests/test_sequential.py -v

# Debug with pdb
uv run pytest --pdb
```

### Observability Issues

```bash
# Start test services
docker-compose -f docker-compose.test.yml up -d

# Check Prometheus
curl http://localhost:9090/api/v1/targets

# Check logs
docker-compose -f docker-compose.test.yml logs -f
```

---

## Git Workflow

### Branch Naming

- `feature/` - New features
- `fix/` - Bug fixes
- `docs/` - Documentation updates
- `refactor/` - Code refactoring
- `test/` - Test additions/fixes

### Commit Messages

Follow conventional commits:

```text
feat(primitives): add CachePrimitive with LRU and TTL support

- Implement LRU eviction policy
- Add TTL-based expiration
- Include comprehensive tests
- Add example usage

Closes #123
```

### Pull Request Checklist

- [ ] Tests added/updated
- [ ] Documentation updated
- [ ] Type hints complete
- [ ] Ruff formatting applied
- [ ] All quality checks pass
- [ ] Examples added (if new feature)

---

## ☁️ FOR CODING AGENT ONLY: Your GitHub Actions Environment

**⚠️ VS Code Extension:** This section is NOT for you. This describes the cloud environment where the Coding Agent runs.

**For Coding Agent:** This section describes your ephemeral development environment.

### ⚠️ IMPORTANT: You are NOT the VS Code Extension

You run in **GitHub Actions**, not in VS Code. You do NOT have access to:

- ❌ **MCP servers** (only available in VS Code locally)
- ❌ **Copilot toolsets** (VS Code-specific feature)
- ❌ **VS Code extensions** (you're in a terminal environment)
- ❌ **Local filesystem** (you have ephemeral Actions runner)
- ❌ **Persistent state** (environment resets each session)

### Your Environment Setup

When you (the Copilot coding agent) work on tasks, you run in an **ephemeral GitHub Actions environment** configured by:

**Setup Workflow:** `.github/workflows/copilot-setup-steps.yml`

**Your Environment Includes:**

- Ubuntu latest runner (2 CPU, 7GB RAM, 14GB disk)
- Python 3.11
- `uv` package manager (preferred over pip)
- Full dependency tree from `uv sync --all-extras`
- Cached dependencies (~9-11s startup with cache)
- All testing, linting, and type checking tools

**Available Commands:**

```bash
# Run tests
uv run pytest -v
uv run pytest --cov=packages --cov-report=html

# Check code quality
uv run ruff check . --fix
uv run ruff format .
uvx pyright packages/

# Verify environment
./scripts/check-environment.sh

# Use VS Code tasks
# See: .vscode/tasks.json for all available tasks
```

**Environment Variables:**

- `PYTHONPATH=$PWD/packages` - Package discovery
- `PYTHONUTF8=1` - UTF-8 encoding
- `PYTHONDONTWRITEBYTECODE=1` - No .pyc files
- `UV_CACHE_DIR=~/.cache/uv` - Dependency cache

**Performance:**

- **Setup time:** 9-11 seconds (with cache), 14 seconds (cold start)
- **Cache size:** ~43MB
- **Cache hit rate:** ~90%
- **Session timeout:** 60 minutes maximum

### How to Customize Your Environment

If you need additional tools or dependencies:

1. **Update** `.github/workflows/copilot-setup-steps.yml`
2. **Add steps** to the `copilot-setup-steps` job
3. **Test changes** - Workflow auto-runs on modifications
4. **Commit** to default branch for agent to use

**Example - Adding a new tool:**

```yaml
- name: Install custom tool
  run: uv pip install custom-package

- name: Verify installation
  run: custom-package --version
```

**Allowed Customizations:**

- `steps` - Add installation/setup steps
- `permissions` - Adjust permissions (minimize to necessary)
- `runs-on` - Change runner size (ubuntu-latest, ubuntu-4-core, etc.)
- `services` - Add service containers (databases, etc.)
- `timeout-minutes` - Max 59 minutes
- `snapshot` - Snapshot configuration

**Prohibited Customizations:**

- Cannot change job name (must be `copilot-setup-steps`)
- Cannot use non-Ubuntu runners (Windows/macOS not supported)
- Cannot use self-hosted runners (without ARC setup)

### Environment Variables and Secrets

**Current Approach:** Variables set directly in workflow

**GitHub Feature:** Can also use `copilot` environment in repository settings:

1. Go to Settings → Environments → `copilot`
2. Add variables or secrets
3. Access in workflow: `${{ vars.VARIABLE_NAME }}` or `${{ secrets.SECRET_NAME }}`

**When to Use:**

- Authentication tokens for external services
- Configuration values that change per branch
- Sensitive data (use secrets, not variables)

**Current TTA.dev Variables:** None configured (not needed yet)

### Performance Considerations

**Current Resources (Standard Runner):**

- **CPU:** 2 cores
- **RAM:** 7GB
- **Disk:** 14GB SSD
- **Network:** GitHub Actions network with firewall

**Larger Runners Available:**

- `ubuntu-4-core` (4 CPU, 16GB RAM, 14GB SSD)
- `ubuntu-8-core` (8 CPU, 32GB RAM, 14GB SSD)
- `ubuntu-16-core` (16 CPU, 64GB RAM, 14GB SSD)
- And larger sizes available

**When to Upgrade:**

- Test suite consistently takes >5 minutes
- Out of memory errors
- Heavy compilation or ML model work
- Large dependency graphs

**Current Performance:** ✅ Standard runner is adequate

### Limitations and Constraints

**Network:**

- ✅ Firewall enabled (protects repository)
- ✅ Can access public internet (PyPI, GitHub, etc.)
- ❌ Cannot access private networks without VPN setup

**File System:**

- ✅ Full read/write access to workspace
- ✅ Can create temporary files
- ❌ Changes don't persist (ephemeral environment)

**Time:**

- ✅ 60 minutes per session
- ✅ Multiple sessions allowed per task
- ❌ Long-running processes need checkpointing

**Resources:**

- ✅ Sufficient for most Python development
- ✅ Can cache dependencies effectively
- ❌ Limited for ML training or large compilations

### Requesting Environment Changes

If you encounter limitations:

1. **Document the issue** in session logs:
   - What you tried
   - Error messages
   - Resource constraints hit
2. **Suggest specific changes** to workflow
3. **Provide rationale** for the change
4. **Reference this documentation**

**Example Request:**

> "The test suite is timing out after 45 minutes. I recommend upgrading to `ubuntu-4-core` runner for faster parallel test execution. Update `.github/workflows/copilot-setup-steps.yml` line 29 to `runs-on: ubuntu-4-core`."

### Verification and Debugging

**Check your environment:**

```bash
# Run verification script
./scripts/check-environment.sh

# Manual checks
uv --version
python --version
uv run pytest --version
uv pip list

# Check what's cached
du -sh ~/.cache/uv
```

**If setup fails:**

1. Check workflow logs in GitHub Actions
2. Verify all dependencies are installable
3. Check for network issues (PyPI down, etc.)
4. Try without cache (workflow will auto-retry)

**Common Issues:**

- **Missing dependencies:** Add to `pyproject.toml` or `packages/*/pyproject.toml`
- **Import errors:** Check `PYTHONPATH` is set correctly
- **Tool not found:** Add installation step to workflow
- **Timeout:** Consider larger runner or optimization

### Self-Awareness Checklist

When working on tasks, remember:

- ✅ I run in GitHub Actions (not VS Code or local machine)
- ✅ My environment is configured by `.github/workflows/copilot-setup-steps.yml`
- ✅ I can suggest workflow changes if I need different tools
- ✅ My sessions are ephemeral (nothing persists except commits)
- ✅ I have access to all tools listed in verification output
- ✅ I should use `uv` not `pip` for Python packages
- ✅ I can reference this documentation to understand my limits

---

## Quick Links

- **Main Agent Instructions:** [`AGENTS.md`](../AGENTS.md)
- **Primitive Catalog:** [`PRIMITIVES_CATALOG.md`](../PRIMITIVES_CATALOG.md)
- **Phase 3 Examples Complete:** [`PHASE3_EXAMPLES_COMPLETE.md`](../PHASE3_EXAMPLES_COMPLETE.md) - InstrumentedPrimitive pattern guide
- **MCP Servers:** [`MCP_SERVERS.md`](../MCP_SERVERS.md)
- **Toolsets Guide:** [`docs/guides/copilot-toolsets-guide.md`](../docs/guides/copilot-toolsets-guide.md)
- **Getting Started:** [`GETTING_STARTED.md`](../GETTING_STARTED.md)
- **TODO Management:** [`logseq/pages/TODO Management System.md`](../logseq/pages/TODO Management System.md) - Required for all agents
- **Logseq Guide:** [`logseq/ADVANCED_FEATURES.md`](../logseq/ADVANCED_FEATURES.md) - Knowledge base features

---

**Last Updated:** October 31, 2025
**For:** GitHub Copilot in VS Code
**Maintained by:** TTA.dev Team
