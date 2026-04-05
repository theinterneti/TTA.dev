# Agent-First Guide — TTA.dev

> **This file is written for coding agents** (Claude Code, GitHub Copilot, OpenCode,
> Cline, etc.). Humans are welcome too, but structure and phrasing prioritise
> machine-readable clarity over narrative flow.

---

## 1. Orientation — what to read first

Start with this file, then follow the chain below. Do **not** start editing until
you have at least read steps 1–3.

| Priority | File | What it tells you |
|----------|------|------------------|
| **1** | `AGENTS.md` | Universal rules, commands, routing table |
| **2** | `CLAUDE.md` | Claude Code specifics, SDD mandate, skills table |
| **3** | `PRIMITIVES_CATALOG.md` | Full primitive API surface |
| **4** | `docs/agent-guides/primitives-patterns.md` | Composition patterns, operators |
| **5** | `docs/agent-guides/testing-architecture.md` | Test standards, `MockPrimitive` API |
| **6** | `docs/agent-guides/python-standards.md` | Types, naming, imports |

If you are working inside an MCP-enabled IDE, call `tta_bootstrap` first —
it returns a compressed orientation package in a single round-trip:

```python
# MCP tool call (Claude Desktop / VS Code / Cline)
result = tta_bootstrap(agent_id="my-agent", task_hint="add retry to LLM calls")
# result contains: version, top_primitives, quick_start, key_files, rules
```

---

## 2. Repository layout (machine-readable)

```
TTA.dev/
├── ttadev/                     # Main importable package
│   ├── primitives/             # ← Start here for workflow logic
│   │   ├── core/               # Base classes, sequential, parallel, routing
│   │   ├── recovery/           # RetryPrimitive, FallbackPrimitive, TimeoutPrimitive, CircuitBreakerPrimitive
│   │   ├── performance/        # CachePrimitive
│   │   ├── testing/            # MockPrimitive
│   │   ├── llm/                # UniversalLLMPrimitive, LLMProvider
│   │   └── __init__.py         # All public exports (check here for import paths)
│   ├── agents/                 # DeveloperAgent, QAAgent, SecurityAgent, registry, router
│   ├── workflows/              # WorkflowDefinition, WorkflowOrchestrator
│   ├── control_plane/          # L0 task/step tracking, leases
│   ├── cli/                    # `tta` CLI subcommands
│   └── observability/          # OTel tracing setup
├── tests/
│   ├── integration/            # test_multi_agent_proof.py — canonical CI proof
│   └── fakes.py                # MockChatPrimitive and test fakes
├── examples/
│   ├── showcase/               # Smart Code Reviewer — realistic multi-primitive demo
│   └── resilient_llm_pipeline.py  # Retry + CircuitBreaker + OTel example
├── docs/
│   ├── agent-first.md          # ← this file
│   ├── agent-guides/           # Deep reference docs (primitives, testing, python standards)
│   └── observability-quickstart.md
├── .github/skills/             # Copilot skills (build-test-verify, git-commit, etc.)
├── .claude/skills/             # Claude Code skills (session-start, sdd-workflow, etc.)
├── AGENTS.md                   # Universal agent entry point
├── CLAUDE.md                   # Claude Code configuration
├── QUICKSTART.md               # Shortest verified proof path
└── PRIMITIVES_CATALOG.md       # Full primitive reference
```

---

## 3. The one rule you must follow first

> **Never write manual retry loops, manual timeout logic, or manual circuit
> breakers.** Use the primitives. The linter enforces this; the reviewer will
> reject it.

```python
# ❌ WRONG — never do this
for attempt in range(3):
    try:
        result = await call_api()
        break
    except Exception:
        await asyncio.sleep(2 ** attempt)

# ✅ CORRECT — use RetryPrimitive
from ttadev.primitives import RetryPrimitive, WorkflowContext
from ttadev.primitives.core.base import LambdaPrimitive

api_call = LambdaPrimitive(call_api)
workflow = RetryPrimitive(api_call, max_retries=3, backoff_factor=2.0)
result = await workflow.execute(input_data, ctx)
```

---

## 4. Primitive composition pattern

All primitives share the same interface:

```python
async def execute(self, input_data: TInput, context: WorkflowContext) -> TOutput:
    ...
```

### 4.1 Import paths

```python
# Preferred — import from the package root
from ttadev.primitives import (
    WorkflowPrimitive,
    WorkflowContext,
    LambdaPrimitive,
    SequentialPrimitive,
    ParallelPrimitive,
    RouterPrimitive,
    RetryPrimitive,
    FallbackPrimitive,
    TimeoutPrimitive,
    CompensationPrimitive,
    CachePrimitive,
    MockPrimitive,
)

# For CircuitBreakerPrimitive (not yet on package root):
from ttadev.primitives.recovery.circuit_breaker_primitive import (
    CircuitBreakerPrimitive,
    CircuitBreakerConfig,
)

# For UniversalLLMPrimitive:
from ttadev.primitives import UniversalLLMPrimitive, LLMProvider, LLMRequest, LLMResponse
```

### 4.2 Composition operators

```python
# >> chains primitives sequentially (output of left → input of right)
pipeline = step_a >> step_b >> step_c

# | runs primitives in parallel (same input to all, returns list of results)
fan_out = branch_a | branch_b | branch_c

# Combined
workflow = preprocess >> (fast_path | slow_path) >> aggregate
```

### 4.3 Wrapping pattern

Recovery and performance primitives wrap an inner primitive:

```python
workflow = TimeoutPrimitive(
    CachePrimitive(
        RetryPrimitive(base_call, max_retries=3),
        cache_key_fn=lambda data, ctx: f"cache:{data}",
        ttl_seconds=300.0,
    ),
    timeout_seconds=10.0,
)
```

### 4.4 Full working example — resilient LLM call

```python
import asyncio
from ttadev.primitives import RetryPrimitive, WorkflowContext
from ttadev.primitives.core.base import LambdaPrimitive
from ttadev.primitives.recovery.circuit_breaker_primitive import (
    CircuitBreakerConfig,
    CircuitBreakerPrimitive,
)


async def call_llm(prompt: str, ctx: WorkflowContext) -> str:
    """Replace with a real LLM call in production."""
    return f"response to: {prompt}"


async def main() -> None:
    ctx = WorkflowContext(workflow_id="demo")

    pipeline = CircuitBreakerPrimitive(
        primitive=RetryPrimitive(
            LambdaPrimitive(call_llm),
            max_retries=3,
        ),
        config=CircuitBreakerConfig(failure_threshold=5),
    )

    result = await pipeline.execute("What is 2+2?", ctx)
    print(result)


asyncio.run(main())
```

See [`examples/resilient_llm_pipeline.py`](../examples/resilient_llm_pipeline.py) for
the full runnable version (mock mode + live Groq mode).

---

## 5. State — always use WorkflowContext

```python
from ttadev.primitives import WorkflowContext

# Create a context per workflow run
ctx = WorkflowContext(workflow_id="my-workflow-123")

# Read/write shared state
ctx.set("key", value)
value = ctx.get("key")

# Metadata
ctx.workflow_id   # str
ctx.metadata      # dict[str, Any]
```

**Never use globals** to share state between primitives. Pass `ctx` through.

---

## 6. Writing tests

### 6.1 Test file layout

```python
# tests/test_my_feature.py
import pytest
from ttadev.primitives import MockPrimitive, WorkflowContext


@pytest.mark.asyncio
async def test_my_workflow_succeeds() -> None:
    # Arrange
    mock = MockPrimitive("step1", return_value={"status": "ok"})
    ctx = WorkflowContext(workflow_id="test-run")

    # Act
    result = await mock.execute("input", ctx)

    # Assert
    assert result == {"status": "ok"}
    assert mock.call_count == 1
```

### 6.2 MockPrimitive API

```python
from ttadev.primitives import MockPrimitive

# Return a static value
mock = MockPrimitive("name", return_value={"key": "value"})

# Raise an exception
mock = MockPrimitive("name", raise_error=ValueError("boom"))

# Custom behaviour
async def custom(data: str, ctx: WorkflowContext) -> str:
    return data.upper()
mock = MockPrimitive("name", side_effect=custom)

# Inspect after execution
assert mock.call_count == 1
assert mock.calls[0][0] == "input"   # mock.calls is list[tuple[input, context]]
```

### 6.3 Run the test suite

```bash
make watch          # TDD loop — re-runs on every file change, fail-fast
make test           # Full run with coverage (required before committing)
uv run pytest -v    # Single run
uv run pytest tests/integration/test_multi_agent_proof.py -v  # Canonical proof
```

### 6.4 Coverage requirements

- New code: **100%** coverage required
- Overall project: 80%+ enforced by Codecov
- Use `make test` (not just `uv run pytest`) to generate coverage reports

---

## 7. Code quality gates

Run these before every commit:

```bash
uv run ruff format .                    # Format
uv run ruff check . --fix               # Lint + auto-fix
uvx pyright ttadev/                     # Type check
uv run pytest -v                        # Tests
```

Or run all at once:

```bash
.github/copilot-hooks/post-generation.sh
```

### Standards checklist

- [ ] `uv` only — never `pip` or `poetry`
- [ ] Python 3.11+ syntax: `str | None` not `Optional[str]`, `dict[str, Any]` not `Dict`
- [ ] Type hints on all function signatures
- [ ] Google-style docstrings
- [ ] `WorkflowContext` passed explicitly — no globals
- [ ] Primitives for retry/timeout/circuit-breaker — no manual loops
- [ ] AAA pattern in tests
- [ ] Conventional Commits: `feat:`, `fix:`, `docs:`, `test:`, `refactor:`

---

## 8. Routing — what to read before touching specific code

| Area | Read first |
|------|-----------|
| Primitive internals | `docs/agents/dev/architecture.md` |
| Retry / timeout / circuit breaker | `docs/agents/dev/reliability.md` |
| OTel / Langfuse tracing | `docs/agents/dev/observability.md` |
| Tests / coverage | `docs/agent-guides/testing-architecture.md` |
| L0 control plane / leases | `docs/agents/dev/l0-coordination.md` |
| Agent roles | `docs/agents/runtime/l0-roster.md` |

---

## 9. Skills — on-demand HOW-TO workflows

Skills are step-by-step workflows for common tasks. They live in two places:

| Location | Used by |
|----------|---------|
| `.github/skills/` | GitHub Copilot |
| `.claude/skills/` | Claude Code |

Available skills:

| Skill | When |
|-------|------|
| `session-start` | Start of every session — orient, load context |
| `build-test-verify` | Build → test → lint cycle |
| `core-conventions` | Writing / reviewing Python code |
| `git-commit` | Making commits (Conventional Commits format) |
| `create-pull-request` | Opening PRs |
| `self-review-checklist` | Pre-merge checklist |
| `sdd-workflow` | New feature development (spec → plan → tasks → implement) |

---

## 10. MCP tools — structured access to TTA.dev

When running inside an MCP-enabled IDE, these tools are available:

```python
# First call of every session — returns orientation package
tta_bootstrap(agent_id="<your-id>", task_hint="<what you're building>")

# Query available primitives
get_primitive_catalog()

# Check workflow status
get_workflow_status(workflow_id="<id>")

# Search primitives by capability
search_primitives(query="retry exponential backoff")

# Get test patterns
get_test_patterns(pattern_type="async_workflow")
```

Tools tagged `allowed_callers` support programmatic tool calling (PTC) — they
return structured JSON that can be parsed and acted on directly in code.

See [`MCP_TOOL_REGISTRY.md`](../MCP_TOOL_REGISTRY.md) for the full tool catalog.

---

## 11. Common patterns — quick reference

### Retry with exponential backoff

```python
from ttadev.primitives import RetryPrimitive
workflow = RetryPrimitive(base, max_retries=3, backoff_factor=2.0)
```

### Fallback chain

```python
from ttadev.primitives import FallbackPrimitive
workflow = FallbackPrimitive(primary=fast_service, fallback=slow_service)
```

### Timeout protection

```python
from ttadev.primitives import TimeoutPrimitive
workflow = TimeoutPrimitive(long_task, timeout_seconds=30.0)
```

### Circuit breaker

```python
from ttadev.primitives.recovery.circuit_breaker_primitive import (
    CircuitBreakerConfig, CircuitBreakerPrimitive,
)
workflow = CircuitBreakerPrimitive(
    primitive=api_call,
    config=CircuitBreakerConfig(failure_threshold=5, recovery_timeout=60.0),
)
```

### Cache with custom key

```python
from ttadev.primitives import CachePrimitive
workflow = CachePrimitive(
    base,
    cache_key_fn=lambda data, ctx: f"{ctx.workflow_id}:{data}",
    ttl_seconds=300.0,
)
```

### Parallel fan-out

```python
from ttadev.primitives import ParallelPrimitive
# Operator form:
workflow = branch_a | branch_b | branch_c
# Explicit form:
workflow = ParallelPrimitive([branch_a, branch_b, branch_c])
results: list = await workflow.execute(input_data, ctx)
```

### Sequential pipeline

```python
from ttadev.primitives import SequentialPrimitive
# Operator form:
workflow = step_a >> step_b >> step_c
# Explicit form:
workflow = SequentialPrimitive([step_a, step_b, step_c])
```

---

## 12. Where to find more

| Resource | URL / Path |
|----------|-----------|
| Full primitive API | [`PRIMITIVES_CATALOG.md`](../PRIMITIVES_CATALOG.md) |
| Observability setup | [`docs/observability-quickstart.md`](observability-quickstart.md) |
| L0 workflow walkthrough | [`docs/l0-workflow-walkthrough.md`](l0-workflow-walkthrough.md) |
| Python standards | [`docs/agent-guides/python-standards.md`](agent-guides/python-standards.md) |
| Composition deep-dive | [`docs/agent-guides/primitives-patterns.md`](agent-guides/primitives-patterns.md) |
| Testing deep-dive | [`docs/agent-guides/testing-architecture.md`](agent-guides/testing-architecture.md) |
| LLM provider strategy | [`docs/agent-guides/llm-provider-strategy.md`](agent-guides/llm-provider-strategy.md) |
| Secrets / API keys | [`docs/agent-guides/secrets-guide.md`](agent-guides/secrets-guide.md) |
| SDD constitution | [`docs/agent-guides/sdd-constitution.md`](agent-guides/sdd-constitution.md) |
| Canonical integration test | [`tests/integration/test_multi_agent_proof.py`](../tests/integration/test_multi_agent_proof.py) |
| Showcase example | [`examples/showcase/`](../examples/showcase/) |
| Resilient LLM pipeline | [`examples/resilient_llm_pipeline.py`](../examples/resilient_llm_pipeline.py) |
