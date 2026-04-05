# TTA.dev — Cline Instructions

## Project Identity

TTA.dev is a **Python library of composable workflow primitives** for building reliable,
observable AI applications. It provides retry, timeout, cache, circuit-breaker, LLM routing,
and multi-agent coordination primitives — all composable via `>>` (sequential) and `|` (parallel).

Repository: https://github.com/theinterneti/TTA.dev

---

## 🚨 SDD Mandate — Spec Before Code

**No implementation code before a signed-off spec.**

Workflow: `/specify` → `/plan` → `/tasks` → `/implement`

Full constitution: [docs/agent-guides/sdd-constitution.md](docs/agent-guides/sdd-constitution.md)

---

## Session Start Protocol

Before any non-trivial task:
1. Call `tta_bootstrap` (MCP) — returns full project orientation in one call
2. Read `tta://catalog` MCP resource — live primitives catalog (always current)
3. Read `tta://patterns` MCP resource — detectable workflow patterns
4. Check `TEST_STATUS.md` for current test state
5. Run `mcp__codegraphcontext__get_repository_stats` to orient the code graph
6. Recall from `hindsight` — `adam-global` (cross-project) + `tta-dev` bank (repo-specific)

After completing significant tasks:
- Retain cross-project patterns → `adam-global` Hindsight bank
- Retain repo-specific decisions → `tta-dev` Hindsight bank

---

## MCP Resources — Read These First

The TTA.dev MCP server (`ttadev/primitives/mcp_server/server.py`) exposes two key resources
that give you the complete picture of available primitives and patterns:

| Resource | What it returns |
|----------|----------------|
| `tta://catalog` | Full primitives catalog — name, description, import path, use cases |
| `tta://patterns` | Detectable code patterns and inferred workflow requirements |

**To verify primitives available in this repo**, fetch `tta://catalog` via the MCP server.
It reads `PRIMITIVES_CATALOG.md` live and returns structured data.

**Quick verification (no MCP required):**
```bash
uv run python -c "
from ttadev.primitives.analysis.analyzer import PrimitiveAnalyzer
a = PrimitiveAnalyzer()
for p in a.list_primitives():
    print(p['name'], '-', p['category'])
"
```

---

## Package Manager — `uv` Only

```bash
uv sync --all-extras        # Install / refresh all dependencies
make watch                  # TDD loop — fast, fail-fast (use during development)
make watch-cov              # TDD loop with live coverage (use before committing)
make test                   # Full one-shot test run with coverage
uv run ruff format .        # Format
uv run ruff check . --fix   # Lint and auto-fix
uvx pyright ttadev/         # Type check (basic mode)
uv run python scripts/validate-todos.py  # Validate TODO format
```

**NEVER use `pip`, `pip3`, `poetry add`, or `conda`.** Only `uv`.

---

## Python Standards

- **Python 3.12+** (required — see `pyproject.toml: requires-python = ">=3.12"`)
- **Type hints — new union syntax only:**
  - ✅ `str | None`, `dict[str, Any]`, `list[str]`, `tuple[int, ...]`
  - ❌ `Optional[str]`, `Dict[str, Any]`, `List[str]`, `Tuple[int, ...]`
- **Ruff** — line length **100**, strict mode (`select = ["ALL"]`)
- **Google-style docstrings** on all public functions, classes, methods
- **Pyright basic mode** — `uvx pyright ttadev/`
- **Conventional Commits:** `feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`

### Naming Conventions

- **Classes:** `PascalCase` — always suffix primitives with `Primitive`
- **Functions/variables:** `snake_case`
- **Constants:** `UPPER_SNAKE_CASE`
- **Private members:** `_leading_underscore`

### Import Organization

```python
# Standard library
import asyncio
from typing import Any

# Third-party
from pydantic import BaseModel

# Local — absolute imports only
from ttadev.primitives import WorkflowContext
from ttadev.primitives.core.base import WorkflowPrimitive
```

---

## Primitives Pattern — Core Rule

> **Always use primitives. Never write manual retry/timeout/cache loops.**

### ✅ Correct

```python
from ttadev.primitives import LambdaPrimitive, WorkflowContext
from ttadev.primitives.recovery import RetryPrimitive
from ttadev.primitives.performance import CachePrimitive

base = LambdaPrimitive(my_function)
workflow = RetryPrimitive(
    CachePrimitive(base, cache_key_fn=lambda d, ctx: str(d), ttl_seconds=3600.0)
)
context = WorkflowContext(workflow_id="demo")
result = await workflow.execute(input_data, context)
```

### ❌ Wrong — Manual Loops

```python
for attempt in range(3):     # NEVER — use RetryPrimitive
    try:
        result = call_api()
    except Exception:
        time.sleep(2 ** attempt)
```

### Composition Operators

```python
workflow = step1 >> step2 >> step3                       # Sequential
workflow = branch1 | branch2 | branch3                   # Parallel
workflow = preprocessor >> (fast | slow) >> aggregator   # Mixed
```

### Primitive Catalog

| Category | Primitives |
|----------|-----------|
| **Core** | `WorkflowPrimitive`, `SequentialPrimitive`, `ParallelPrimitive`, `ConditionalPrimitive`, `RouterPrimitive`, `LambdaPrimitive` |
| **Recovery** | `RetryPrimitive`, `TimeoutPrimitive`, `CircuitBreakerPrimitive`, `FallbackPrimitive`, `CompensationPrimitive` |
| **Performance** | `CachePrimitive`, `MemoryPrimitive` |
| **LLM** | `ModelRouterPrimitive`, `ModelRouterChatAdapter`, `TaskProfile` |
| **Orchestration** | `SkillPrimitive`, workflow orchestration primitives |
| **Observability** | OTel span/metric primitives |
| **Testing** | `MockPrimitive` |

---

## State Management

- ✅ Pass all state via `WorkflowContext` (workflow_id, session_id, metadata, state)
- ❌ No module-level mutable globals for workflow data

```python
context = WorkflowContext(
    workflow_id="my-workflow",
    session_id="session-123",
    metadata={"user_id": "u42"},
)
```

---

## Error Handling

```python
if not input_data.get("required_field"):
    raise ValueError(
        f"Missing required_field in {self.__class__.__name__} "
        f"for workflow_id={context.workflow_id}"
    )
```

- Use specific exceptions, not generic `Exception`
- Always include context (workflow_id, primitive name) in error messages
- Use structured logging with correlation IDs from `WorkflowContext`

---

## Testing Standards

- **pytest** with AAA pattern (Arrange, Act, Assert)
- **`@pytest.mark.asyncio`** for all async tests
- **`MockPrimitive`** for mocking (`from ttadev.primitives.testing import MockPrimitive`)
- **Coverage:** 80%+ project-wide; **100% for all new code**
- **TDD loop:** `make watch` during development

```python
import pytest
from ttadev.primitives import WorkflowContext
from ttadev.primitives.testing import MockPrimitive

@pytest.mark.asyncio
async def test_sequential_workflow():
    # Arrange
    mock1 = MockPrimitive("step1", return_value="result1")
    mock2 = MockPrimitive("step2", return_value="result2")
    workflow = mock1 >> mock2
    context = WorkflowContext(workflow_id="test-001")

    # Act
    result = await workflow.execute("input", context)

    # Assert
    assert mock1.call_count == 1
    assert result == "result2"
```

---

## ⛔ TODO Format — CI-Blocking

**Malformed TODOs block CI.** Required format in code and markdown:

```markdown
- TODO <description> #dev-todo
  type:: <bug|implementation|refactor|documentation>
  priority:: <critical|high|medium|low>
  package:: <package-name>
```

- ❌ `# TODO: fix this` — BLOCKS CI
- ❌ `# FIXME: broken` — BLOCKS CI
- ✅ Complete example:

```markdown
- TODO add TTL validation for edge case at midnight boundary #dev-todo
  type:: bug
  priority:: high
  package:: ttadev-primitives
```

---

## Quality Gates

Run after every code change:

```bash
.github/copilot-hooks/post-generation.sh
```

| Gate | Command | Requirement |
|------|---------|-------------|
| **Lint** | `uv run ruff check .` | Zero violations |
| **Types** | `uvx pyright ttadev/` | ≤2 known OTel SDK errors |
| **Tests** | `uv run pytest -m "not integration"` | All pass |

**Self-correction protocol:**
1. Capture full error output
2. Identify root cause
3. Apply minimal fix
4. Re-run gates
5. Repeat until all green

Never present results until all quality gates pass.

---

## L0 Control Plane — Extend, Don't Duplicate

The L0 developer control-plane is live:
- `ttadev/control_plane/` — JSON-backed task/run/lease state
- `ttadev/cli/control.py` — `tta control task|run|workflow ...`
- `ttadev/primitives/mcp_server/server.py` — MCP tools for task/run lifecycle

**Rule:** For agent coordination, task ownership, approvals, or leases — **extend L0**.
Do not create parallel task/run systems anywhere else in the repo.

---

## MCP Servers Available

| Server | Purpose |
|--------|---------|
| `tta_bootstrap` | **Start here** — full project orientation in one call |
| **codegraphcontext** | Code graph: `find_code`, `analyze_code_relationships` |
| **hindsight** | Long-term memory: `recall` (start) + `retain` (after tasks) |
| **serena** | Symbol edits: `find_symbol`, `replace_symbol_body`, `get_symbols_overview` |
| **context7** | Library documentation lookup |
| **github** | Issues, PRs, releases, secrets |
| **playwright** | Browser automation and testing |
| **grafana** | Metrics and dashboard queries |
| **gitmcp** | Git operations |
| **sequential-thinking** | Complex problem decomposition |
| **e2b** | Sandboxed code execution |

**Orient before edit:** Use `codegraphcontext` (`find_code` + `analyze_code_relationships`)
before modifying any non-trivial target.

**Symbol-level work:** Prefer Serena over raw file reads:
- `find_symbol` > grep + read
- `replace_symbol_body` > edit with large context
- `find_referencing_symbols` > pattern search

---

## Adding a New Primitive (Checklist)

1. Create module in appropriate `ttadev/primitives/` subpackage
2. Extend `WorkflowPrimitive[TInput, TOutput]` with typed generics
3. Implement `async execute(self, input_data: TInput, context: WorkflowContext) -> TOutput`
4. Add Google-style docstring with `Args:`, `Returns:`, `Raises:`, `Example:`
5. Export in the subpackage `__init__.py`
6. Create `tests/test_my_primitive.py` with 100% coverage and AAA pattern
7. Update `PRIMITIVES_CATALOG.md` with the new primitive
8. Run `make test` and `.github/copilot-hooks/post-generation.sh`

---

## Directory Structure

```
ttadev/
├── primitives/         # All workflow primitives (MAIN SURFACE)
│   ├── core/           # Base classes, WorkflowContext, LambdaPrimitive
│   ├── recovery/       # Retry, Timeout, CircuitBreaker, Fallback, Compensation
│   ├── performance/    # Cache, Memory
│   ├── llm/            # ModelRouterPrimitive, TaskProfile, adapters
│   ├── coordination/   # Router, Sequential, Parallel
│   ├── observability/  # OTel span/metric primitives
│   ├── testing/        # MockPrimitive, test utilities
│   └── mcp_server/     # 43-tool MCP server for coding agents
├── control_plane/      # L0 task/run/lease state
├── agents/             # Role-based agent system
├── observability/      # OpenTelemetry + local dashboard server
├── cli/                # `tta` CLI subcommands
└── workflows/          # LLM provider chain, feature_dev workflow
tests/                  # Test suite (mirrors ttadev/ structure)
docs/agent-guides/      # Deep-reference guides per topic
.github/agents/         # Per-role agent definition files (.agent.md)
.github/workflows/      # CI/CD pipelines
.claude/skills/         # Single-agent Claude Code skills
```

---

## Skills (Load Dynamically)

| Skill | When to Use |
|-------|-------------|
| [build-test-verify](.claude/skills/build-test-verify/SKILL.md) | Build, test, lint, verify |
| [git-commit](.claude/skills/git-commit/SKILL.md) | Making commits |
| [create-pull-request](.claude/skills/create-pull-request/SKILL.md) | Creating PRs |
| [core-conventions](.claude/skills/core-conventions/SKILL.md) | Writing/reviewing Python code |
| [self-review-checklist](.claude/skills/self-review-checklist/SKILL.md) | Pre-merge review |
| [sdd-workflow](.claude/skills/sdd-workflow/SKILL.md) | New feature development |

---

## Integration Smoke Test

**To verify this config is working:** Ask the agent "what primitives does TTA.dev have?"
The agent should answer using one of these sources (in priority order):

1. `tta://catalog` MCP resource (live, always current)
2. `tta_bootstrap` MCP tool — `primitives` field in its response
3. `PRIMITIVES_CATALOG.md` — static reference

Expected answer includes: `RetryPrimitive`, `TimeoutPrimitive`, `CachePrimitive`,
`CircuitBreakerPrimitive`, `LambdaPrimitive`, `SequentialPrimitive`, `ParallelPrimitive`,
`ModelRouterPrimitive`, `MockPrimitive`.

---

## Key Reference Files

- [AGENTS.md](../AGENTS.md) — Universal agent hub for all roles
- [CLAUDE.md](../CLAUDE.md) — Primary agent (Claude Code) directives
- [PRIMITIVES_CATALOG.md](../PRIMITIVES_CATALOG.md) — Full primitive API reference
- [MCP_TOOL_REGISTRY.md](../MCP_TOOL_REGISTRY.md) — MCP tool catalog
- [docs/agent-guides/primitives-patterns.md](../docs/agent-guides/primitives-patterns.md)
- [docs/agent-guides/python-standards.md](../docs/agent-guides/python-standards.md)
- [docs/agent-guides/testing-architecture.md](../docs/agent-guides/testing-architecture.md)
- [docs/agent-guides/todo-management.md](../docs/agent-guides/todo-management.md)
- [docs/agent-guides/sdd-constitution.md](../docs/agent-guides/sdd-constitution.md)
