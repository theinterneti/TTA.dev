# GitHub Copilot Instructions for TTA.dev

This document provides specific guidance for GitHub Copilot users working on the TTA.dev repository.

## 🎯 Know Your Copilot Context

**CRITICAL:** If you're GitHub Copilot, understand which context you're in:

- **🖥️ VS Code Extension (LOCAL):** You have MCP servers, toolsets, local filesystem
- **☁️ Coding Agent (CLOUD):** You run in GitHub Actions, NO MCP/toolsets
- **💻 GitHub CLI (TERMINAL):** You run in terminal via `gh copilot`

**Why this matters:** Configuration, tools, and capabilities differ by context. Don't assume LOCAL features are available in CLOUD environment or vice versa.

---

## 🤖 Agent Persona & Behavior

**You are an expert AI developer working on TTA.dev.**

- **Think Step-by-Step:** Always break down complex problems into smaller, manageable steps before writing code.
- **Ask Clarifying Questions:** If a request is ambiguous, ask for clarification instead of making assumptions.
- **Proactive Improvement:** Suggest improvements to code or workflows when you see them, aligning with the "Inner Loop" philosophy of high reliability.
- **Tone:** Be professional, concise, and helpful. Focus on delivering value efficiently.
- **Safety First:** Always prioritize security and reliability. Do not execute destructive commands without confirmation.

---

## 📦 Package Manager (CRITICAL)

**ALWAYS use `uv`, NEVER `pip` or `poetry`**

```bash
# Install packages
uv add package-name

# Sync dependencies
uv sync --all-extras

# Run commands
uv run pytest -v
uv run ruff format .
uv run python script.py

# Install local package for development
uv pip install -e platform/primitives
```

❌ **NEVER use:** `pip install`, `poetry add`, `python -m pip`

---

## 🐍 Python Version & Type Hints

- **Python:** 3.11+ required
- **Type hints:** Use `str | None` NOT `Optional[str]`
- **Dicts:** Use `dict[str, Any]` NOT `Dict[str, Any]`
- **Type checking:** Run `uvx pyright platform/ apps/` before committing

**Example:**
```python
# ✅ GOOD: Python 3.11+ style
def process(data: dict[str, Any]) -> str | None:
    ...

# ❌ BAD: Old style
from typing import Optional, Dict, Any
def process(data: Dict[str, Any]) -> Optional[str]:
    ...
```

---

## 🧪 Testing Requirements

- **Framework:** pytest with AAA pattern (Arrange, Act, Assert)
- **Coverage:** Aim for 100% coverage on new code, minimum 80%
- **Async tests:** Use `@pytest.mark.asyncio` decorator
- **Mocking:** Use `MockPrimitive` from `tta_dev_primitives.testing`

**Run tests:**
```bash
# All tests
uv run pytest -v

# With coverage
uv run pytest --cov=packages --cov-report=html

# Specific package
uv run pytest platform/primitives/tests/ -v
```

**Test structure:**
```python
import pytest
from tta_dev_primitives.core.base import WorkflowContext
from tta_dev_primitives.testing import MockPrimitive

@pytest.mark.asyncio
async def test_workflow_success():
    """Test successful workflow execution."""
    # Arrange
    mock1 = MockPrimitive("step1", return_value="result1")
    context = WorkflowContext(workflow_id="test")
    
    # Act
    result = await mock1.execute("input", context)
    
    # Assert
    assert mock1.call_count == 1
    assert result == "result1"
```

---

## 🎨 Code Style & Formatting

- **Formatter:** Ruff with 100 character line length
- **Linter:** Ruff with strict rules
- **Auto-format:** Enabled on save in VS Code

**Run quality checks:**
```bash
# Format code
uv run ruff format .

# Check code
uv run ruff check . --fix

# Type check
uvx pyright platform/ apps/

# All checks (before commit)
uv run ruff format . && uv run ruff check . --fix && uvx pyright platform/ apps/
```

---

## 🔒 Security Practices

- **Never commit secrets** - Use environment variables or `.env` files (add to `.gitignore`)
- **Validate inputs** - Always validate external data
- **Use type hints** - Catches many security issues at type-check time
- **Follow OWASP** - Be aware of common vulnerabilities
- **Dependencies** - Keep dependencies updated, avoid known vulnerabilities

**Secrets handling:**
```python
import os
from dotenv import load_dotenv

# ✅ GOOD: Use environment variables
load_dotenv()
api_key = os.getenv("API_KEY")

# ❌ BAD: Hard-coded secrets
api_key = "sk-1234567890abcdef"  # NEVER DO THIS
```

---

## 📚 Documentation Standards

- **Style:** Google-style docstrings
- **Required:** All public classes and methods must have docstrings
- **Examples:** Include usage examples in docstrings
- **README:** Each package must have a comprehensive README

**Docstring format:**
```python
async def execute(self, input_data: dict, context: WorkflowContext) -> dict:
    """
    Process input with intelligent caching.

    Args:
        input_data: Request data with 'query' key
        context: Workflow context with session info

    Returns:
        Processed result with 'response' key

    Raises:
        ValueError: If input_data missing required keys

    Example:
        ```python
        cache = CachePrimitive(ttl=3600)
        result = await cache.execute({"query": "..."}, context)
        ```
    """
```

---

## 🔗 TTA.dev Primitives (Core Pattern)

**ALWAYS use primitives** for workflow composition. Never write raw async/await orchestration.

**Composition operators:**
```python
# Sequential (>>): Output of each step becomes input to next
workflow = step1 >> step2 >> step3

# Parallel (|): All branches receive same input
workflow = branch1 | branch2 | branch3

# Mixed: Combine patterns
workflow = input_processor >> (fast_path | slow_path) >> aggregator
```

**Common primitives:**
- `SequentialPrimitive` - Execute steps in order
- `ParallelPrimitive` - Execute steps concurrently
- `RouterPrimitive` - Route based on conditions
- `CachePrimitive` - Cache results with TTL
- `RetryPrimitive` - Retry on failure with backoff
- `TimeoutPrimitive` - Enforce time limits
- `FallbackPrimitive` - Fallback on failure

**See:** [`PRIMITIVES_CATALOG.md`](../PRIMITIVES_CATALOG.md) for complete reference

---

## 📋 TODO Management (Logseq)

**ALL agents must use Logseq for TODO tracking**

**Location:** `logseq/journals/YYYY_MM_DD.md`

**Tags:**
- `#dev-todo` - Development work (building TTA.dev)
- `#user-todo` - User education (tutorials, flashcards)

**Required properties:**
```markdown
- TODO Implement CachePrimitive metrics #dev-todo
  type:: implementation
  priority:: high
  package:: tta-dev-primitives
  related:: [[TTA Primitives/CachePrimitive]]

- TODO Create flashcards for retry patterns #user-todo
  type:: learning
  audience:: intermediate-users
  time-estimate:: 20 minutes
```

**See:** [`.github/instructions/logseq-knowledge-base.instructions.md`](instructions/logseq-knowledge-base.instructions.md)

---

## 🏗️ Repository Structure

```text
TTA.dev/
├── platform/              # Infrastructure packages
│   ├── tta-dev-primitives/           # Core workflow primitives ✅
│   ├── tta-observability-integration/ # OpenTelemetry integration ✅
│   └── universal-agent-context/      # Agent context management ✅
├── .github/
│   ├── copilot-instructions.md       # This file
│   ├── instructions/                 # Modular instructions
│   └── workflows/                    # CI/CD workflows
├── docs/                             # Comprehensive documentation
├── logseq/                           # Knowledge base & TODO system
└── scripts/                          # Automation scripts
```

---

## Copilot Toolsets (VS Code Extension)

TTA.dev leverages Copilot toolsets for specialized development tasks.

**Available toolsets:**
- Use `#tta-package-dev` for primitive development
- Use `#tta-testing` for test development
- Use `#tta-observability` for tracing/metrics work
- Use `#tta-agent-dev` for general agent development (includes Context7, AI Toolkit)
- Use `#tta-mcp-integration` for all available MCP tools
- Use `#tta-docs` for documentation-related tasks (includes Context7)
- Use `#tta-pr-review` for GitHub PR reviews (includes GitHub PR tools)
- Use `#tta-troubleshoot` for investigation and analysis (includes Sift, Grafana)
- Use `#tta-full-stack` for database operations (includes Database, Grafana, Context7)

**Using MCP Tools in Copilot Chat:**
```
# Specify toolset with hashtag
@workspace #tta-observability

# Ask natural language question
Show me CPU usage for the last 30 minutes

# Copilot automatically invokes appropriate MCP tools
```

**See:** [`docs/guides/copilot-toolsets-guide.md`](../docs/guides/copilot-toolsets-guide.md) for detailed usage

---

## 📝 Modular Instructions

TTA.dev uses modular instruction files for context-specific guidance:

- **Tests:** `.github/instructions/tests.instructions.instructions.md`
- **Scripts:** `.github/instructions/scripts.instructions.instructions.md`
- **Package Source:** `.github/instructions/package-source.instructions.instructions.md`
- **Documentation:** `.github/instructions/documentation.instructions.instructions.md`
- **Logseq/TODO:** `.github/instructions/logseq-knowledge-base.instructions.md`

These files use YAML frontmatter to target specific file patterns and provide detailed, context-aware guidance.

---

## 🚀 Development Workflow

1. **Setup environment:**
   ```bash
   uv sync --all-extras
   ```

2. **Make changes:**
   - Follow type hints and primitives patterns
   - Write tests for new code
   - Update documentation

3. **Run quality checks:**
   ```bash
   uv run ruff format .
   uv run ruff check . --fix
   uvx pyright platform/ apps/
   uv run pytest -v
   ```

4. **Commit:**
   ```bash
   git add .
   git commit -m "feat: Add awesome feature"
   ```

5. **Create PR:**
   ```bash
   gh pr create --title "feat: Add awesome feature"
   ```

**VS Code tasks available:**
- Press `Cmd/Ctrl+Shift+P`
- Type "Task: Run Task"
- Select from quality check, test, format tasks

---

## 📖 Related Documentation

- **Agent Instructions:** [`AGENTS.md`](../AGENTS.md) - Main agent hub
- **Getting Started:** [`GETTING_STARTED.md`](../GETTING_STARTED.md) - Quick start guide
- **Primitives Catalog:** [`PRIMITIVES_CATALOG.md`](../PRIMITIVES_CATALOG.md) - Complete primitive reference
- **MCP Servers:** [`MCP_SERVERS.md`](../MCP_SERVERS.md) - MCP integration guide
- **Contributing:** [`CONTRIBUTING.md`](../CONTRIBUTING.md) - Contribution guidelines
- **Toolset Guide:** [`docs/guides/copilot-toolsets-guide.md`](../docs/guides/copilot-toolsets-guide.md) - Detailed toolset usage

---

## ✅ Pre-Commit Checklist

Before committing code, ensure:

- [ ] Code formatted with `uv run ruff format .`
- [ ] Linter passes with `uv run ruff check . --fix`
- [ ] Type checks pass with `uvx pyright platform/ apps/`
- [ ] Tests pass with `uv run pytest -v`
- [ ] Test coverage >80% for new code
- [ ] Documentation updated (docstrings, README)
- [ ] TODOs added to Logseq (if applicable)
- [ ] No secrets committed
- [ ] Using `uv` (not pip/poetry)
- [ ] Using primitives for workflows
- [ ] Python 3.11+ type hints (no `Optional`, `Dict`)

---

**Last Updated:** 2025-11-13
**Maintained by:** TTA.dev Team
