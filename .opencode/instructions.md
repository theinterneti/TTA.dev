# TTA.dev — OpenCode Instructions

## Project Identity

TTA.dev is a **Python library of composable workflow primitives** for building reliable,
observable AI applications. It provides retry, timeout, cache, circuit-breaker, LLM routing,
and multi-agent coordination primitives — composable via `>>` (sequential) and `|` (parallel).

Repository: https://github.com/theinterneti/TTA.dev

---

## Session Start

Before any non-trivial task:
1. Call `tta_bootstrap` (MCP) — full project orientation in one call
2. Check `TEST_STATUS.md` for current test state
3. Run `mcp__codegraphcontext__get_repository_stats` to orient the code graph

---

## Package Manager — `uv` Only

```bash
uv sync --all-extras        # Install / refresh dependencies
make watch                  # TDD loop (fast, fail-fast — use during development)
make watch-cov              # TDD loop with live coverage (use before committing)
make test                   # Full test run with coverage
uv run ruff format .        # Format
uv run ruff check . --fix   # Lint
uvx pyright ttadev/         # Type check
uv run python scripts/validate-todos.py  # Validate TODO format
```

**Never use `pip`, `pip3`, `poetry`, or `conda`.**

---

## Python Standards

- **Python 3.11+** (3.12 preferred)
- **Type hints — new union syntax:**
  - ✅ `str | None`, `dict[str, Any]`, `list[str]`
  - ❌ `Optional[str]`, `Dict[str, Any]`, `List[str]`
- **Ruff** — line length **100**, strict mode
- **Google-style docstrings** on all public APIs
- **Pyright basic mode** (`uvx pyright ttadev/`)
- **Conventional Commits** (`feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`)

---

## Primitives Pattern — Core Rule

> Always use primitives for workflows. Never write manual retry/timeout/cache loops.

### ✅ Correct

```python
from ttadev.primitives import LambdaPrimitive, WorkflowContext
from ttadev.primitives.recovery import RetryPrimitive
from ttadev.primitives.performance import CachePrimitive

base = LambdaPrimitive(my_function)
workflow = RetryPrimitive(
    CachePrimitive(base, cache_key_fn=lambda d, ctx: str(d), ttl_seconds=3600.0)
)
result = await workflow.execute(input_data, WorkflowContext(workflow_id="demo"))
```

### ❌ Wrong

```python
for attempt in range(3):      # NEVER — use RetryPrimitive
    try:
        result = my_function(data)
    except Exception:
        time.sleep(2 ** attempt)
```

### Composition

```python
workflow = step1 >> step2 >> step3                    # Sequential
workflow = branch1 | branch2 | branch3                # Parallel
workflow = preprocessor >> (fast | slow) >> aggregator  # Mixed
```

### Available Primitives

| Category | Primitives |
|----------|-----------|
| **Core** | `WorkflowPrimitive`, `SequentialPrimitive`, `ParallelPrimitive`, `ConditionalPrimitive`, `RouterPrimitive`, `LambdaPrimitive` |
| **Recovery** | `RetryPrimitive`, `TimeoutPrimitive`, `CircuitBreakerPrimitive`, `FallbackPrimitive`, `CompensationPrimitive` |
| **Performance** | `CachePrimitive`, `MemoryPrimitive` |
| **LLM** | `ModelRouterPrimitive`, `ModelRouterChatAdapter`, `TaskProfile` |
| **Testing** | `MockPrimitive` |

---

## State Management

- ✅ Pass state via `WorkflowContext` (workflow_id, session_id, metadata, state)
- ❌ Never use module-level globals for workflow data

---

## Testing Standards

- **pytest** with AAA pattern (Arrange, Act, Assert)
- **`@pytest.mark.asyncio`** for all async tests
- **`MockPrimitive`** for mocking (`from ttadev.primitives.testing import MockPrimitive`)
- **Coverage:** 80% minimum project-wide; **100% for all new code**

```python
@pytest.mark.asyncio
async def test_my_workflow():
    # Arrange
    mock = MockPrimitive("step", return_value="ok")
    context = WorkflowContext(workflow_id="test")
    # Act
    result = await mock.execute("input", context)
    # Assert
    assert result == "ok"
    assert mock.call_count == 1
```

---

## ⛔ TODO Format — CI-Blocking

```markdown
- TODO <description> #dev-todo
  type:: <bug|implementation|refactor|documentation>
  priority:: <critical|high|medium|low>
  package:: <package-name>
```

Malformed TODOs (plain `# TODO:` comments) **block CI**.

---

## Quality Gates

Run after every code change:

```bash
.github/copilot-hooks/post-generation.sh
```

Gates: Ruff (lint) → Pyright (types, ≤2 known errors) → Pytest (all non-integration tests).

Do not present results until all gates pass.

---

## L0 Control Plane — Extend, Don't Duplicate

- `ttadev/control_plane/` — task/run/lease state
- `ttadev/cli/control.py` — `tta control ...` CLI
- `ttadev/primitives/mcp_server/server.py` — MCP access

For agent coordination, task ownership, approvals: **extend L0, don't create parallel systems**.

---

## MCP Servers

| Server | Purpose |
|--------|---------|
| `tta_bootstrap` | Start every session — full project orientation |
| **codegraphcontext** | Code graph: `find_code`, `analyze_code_relationships` |
| **hindsight** | Long-term memory: `recall` (session start) + `retain` (after tasks) |
| **serena** | Symbol edits: `find_symbol`, `replace_symbol_body` |
| **context7** | Library documentation |
| **github** | Issues, PRs, repository operations |
| **playwright** | Browser automation |
| **grafana** | Monitoring and metrics |
| **gitmcp** | Git operations |
| **sequential-thinking** | Complex problem decomposition |
| **e2b** | Sandboxed code execution |

---

## Directory Structure

```
ttadev/primitives/      # All workflow primitives (main surface)
ttadev/control_plane/   # L0 task/run/lease state
ttadev/agents/          # Role-based agent system
ttadev/observability/   # OpenTelemetry integration
ttadev/cli/             # `tta` CLI subcommands
tests/                  # Test suite
docs/agent-guides/      # Deep-reference guides
```

---

## Key References

- [AGENTS.md](../AGENTS.md) — Universal agent guidance
- [PRIMITIVES_CATALOG.md](../PRIMITIVES_CATALOG.md) — Full primitive API
- [MCP_TOOL_REGISTRY.md](../MCP_TOOL_REGISTRY.md) — MCP tool catalog
- [docs/agent-guides/primitives-patterns.md](../docs/agent-guides/primitives-patterns.md)
- [docs/agent-guides/python-standards.md](../docs/agent-guides/python-standards.md)
- [docs/agent-guides/testing-architecture.md](../docs/agent-guides/testing-architecture.md)
- [docs/agent-guides/todo-management.md](../docs/agent-guides/todo-management.md)
