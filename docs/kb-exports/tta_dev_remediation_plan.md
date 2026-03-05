# TTA.dev Remediation Plan

**Generated:** 2026-03-05
**Author:** Staff DevOps Engineer / Agentic Architect
**Objective:** Restore zero known bugs, 100% test coverage, and strict CI compliance.

---

## Assessment Summary

The following drift was captured by running the full local verification suite against
the current `main` branch before any code changes.

| Check | Tool | Status | Count |
|-------|------|--------|-------|
| Linting | `uv run ruff check .` | ⚠️ Errors | 91 errors (38 auto-fixable) after setting `line-length = 88` |
| Type Checking | `uvx pyright platform/` | ❌ Failing | 326 errors, 16 warnings |
| Tests | `uv run pytest` | ✅ Passing | 221 passed, 4 skipped |
| Coverage | `--cov=platform` | ⚠️ Below target | 47% (target: 80%/100%) |
| TODO Compliance | `scripts/validate-todos.py` | ❌ Failing | 78.9% (target: 100%) |

---

## Phase 1: Deterministic Fixes (Ruff + Pyright)

> **Goal:** Get `ruff check` and `pyright` to report zero errors before touching tests.
> These are mechanical, non-behavioral changes.

### 1.1 — Auto-fix Ruff Errors

**File:** `.github/scripts/workflow-migration.py`
**Command:** `uv run ruff check .github/scripts/workflow-migration.py --fix`

All 38 auto-fixable errors in this file can be resolved in one command.
The 4 remaining non-auto-fixable errors need manual attention.

- [x] Update `pyproject.toml`: change `line-length = 100` to `line-length = 88` to match
  the enforced standard in CLAUDE.md and `.github/copilot-instructions.md`
- [x] Run `uv run ruff check . --fix` to resolve 38 auto-fixable violations
- [x] Fix remaining 4 non-auto-fixable errors in `.github/scripts/workflow-migration.py`:
  - `E501` — shorten lines >88 chars (will become violations once `line-length = 88` is set)
  - `UP035`/`UP006` residuals — replace all `typing.Dict` / `typing.List` usages with built-in `dict` / `list`
- [x] Confirm zero errors: `uv run ruff check .`

**Error breakdown (`.github/scripts/workflow-migration.py`):**

| Code | Description | Count | Auto-fix |
|------|-------------|-------|---------|
| I001 | Import block unsorted | 1 | ✅ |
| UP035 | `typing.Dict`/`typing.List` deprecated | 2 | ✅ |
| UP006 | Use `dict`/`list` for type annotations | 2 | ✅ |
| W293 | Blank line contains whitespace | 33+ | ✅ |
| E501 | Line too long (>88 chars) | 4+ | ❌ manual |

### 1.2 — Fix Pyright Type Errors

**Total non-import errors:** 110 across 5 packages.

Run `uvx pyright platform/` to see the current full list. Fix in this order:

#### 1.2.1 — `platform/primitives` (93 errors)

The highest-impact package. Key error clusters:

- [x] `adaptive/logseq_integration.py` — `StrategyMetrics` has no `avg_latency_ms` attribute; constructor
  call mismatches (`success_rate`/`avg_latency_ms` not accepted). Align call sites with the
  actual `StrategyMetrics` dataclass fields.
- [x] `adaptive/cache.py:392` — `"parameters"` accessed on `None`. Add a `None` guard before access.
- [x] `ace/benchmarks.py:219,232,235` — Constructor `__init__` overload mismatch; `str | None`
  passed where `str` is required. Add `assert` / early return guards.
- [x] `analysis/transformer.py:367` — Return type mismatch: `Return` assigned to `Expr`. Fix the
  return type annotation or the return statement.
- [x] `apm/setup.py:78` — `add_span_processor` called on `None`. Guard the tracer provider
  dereference with an `if provider is not None` check.
- [x] `core/context_engineering.py:187–219` — Multiple `TypedDict` item access errors and
  `str | None` → `str` mismatches. Add `None` guards and narrow types before passing to
  functions that require `str`.

#### 1.2.2 — `platform/integrations` (5 errors)

- [x] `integrations/__init__.py:57–78` — `PostgreSQLPrimitive`, `SQLitePrimitive`,
  `ClerkAuthPrimitive`, `Auth0Primitive`, `JWTPrimitive` are listed as exports but the
  stub files only contain `# TODO: Implement`. Either remove them from `__init__.py`
  exports or implement stub classes that satisfy the import contract.

#### 1.2.3 — `platform/agent-coordination` (3 errors)

- [x] `wrappers/docker_wrapper.py:273–275` — `tags` and `id` accessed on `None`. Add a
  `None` guard around the Docker image attribute access block.

#### 1.2.4 — `platform/observability` (2 errors)

- [x] `observability/apm_setup.py:116` — `add_span_processor` called on `None`. Mirror
  the fix in `platform/primitives/apm/setup.py`.

#### 1.2.5 — `platform/agent-context` (7 errors in `.augment/` subdirectory)

- [x] `agent-context/.augment/context/conversation_manager.py:924–934` — `str | None`
  declared but `Path` assigned; `str` used where `Path` methods called. Fix type
  declaration to `Path | None` and add `None` guard.

**Note:** The 216 remaining Pyright errors are all `reportMissingImports` for packages
(e.g., `pytest`, `structlog`, `pydantic`) that are not installed in the Pyright environment
used by `uvx pyright`. These are environment-configuration false positives — not real code
bugs — and require adding the missing packages to Pyright's `extraPaths` or the workspace
venv path. They do **not** indicate broken code.

#### 1.2.6 — Pyright environment fix (216 false-positive import errors)

- [x] Update `pyrightconfig.json` to include `.venv/lib/python3.11/site-packages` in
  `extraPaths` so that installed dev dependencies (pytest, structlog, pydantic, etc.) are
  resolved during type checking without requiring them in every sub-package's `pyproject.toml`.

---

## Phase 2: TODO Compliance (Logseq Journal Fixes)

> **Goal:** Reach 100% TODO compliance so the `validate-todos` CI step passes.
> Current rate: **78.9%** (15/19). Target: **100%**.

### 2.1 — Fix malformed TODOs in `logseq/journals/2024_12_20.md`

Run `uv run python scripts/validate-todos.py` to confirm the exact line numbers before editing.
Current findings:

| Line | Issue | Required Fix |
|------|-------|-------------|
| 8 | Missing category tag — plain TODO with no `#dev-todo` or `#user-todo` | Add `#dev-todo` tag and required properties |
| 16 | Uses `#ops-todo` — not a recognized category for validation | Change to `#dev-todo` or `#user-todo`; add required properties |
| 17 | `#dev-todo` but missing `type::` and `priority::` properties | Add `  type:: documentation` and `  priority:: low` |
| 18 | `#dev-todo` but missing `type::` and `priority::` properties | Add `  type:: implementation` and `  priority:: medium` |

**Corrected entries for `2024_12_20.md`:**

```markdown
- TODO Set up Logseq dashboard page #dev-todo
  type:: documentation
  priority:: low
  package:: tta-kb-automation

- TODO Verify Logseq app can open the graph #dev-todo
  type:: implementation
  priority:: medium
  package:: tta-kb-automation

- TODO Gradually add more documentation pages #dev-todo
  type:: documentation
  priority:: low
  package:: tta-dev-primitives

- TODO Set up automated sync from code docs to KB #dev-todo
  type:: implementation
  priority:: medium
  package:: tta-kb-automation
```

- [x] Edit `logseq/journals/2024_12_20.md` — fix line 8 (add `#dev-todo` + properties)
- [x] Edit `logseq/journals/2024_12_20.md` — fix line 16 (`#ops-todo` → `#dev-todo` + properties)
- [x] Edit `logseq/journals/2024_12_20.md` — fix line 17 (add `type::` and `priority::`)
- [x] Edit `logseq/journals/2024_12_20.md` — fix line 18 (add `type::` and `priority::`)
- [x] Verify: `uv run python scripts/validate-todos.py` → `Compliance rate: 100.0%`

### 2.2 — Audit source-code `# TODO:` comments

The following `# TODO:` inline comments exist in platform source files. These are **code-level
placeholders** that are not tracked in the Logseq TODO Management System. They represent
unimplemented stubs and should either be:
(a) implemented before the next release, or
(b) moved to a Logseq journal entry following the `#dev-todo` format.

| File | Count | Notes |
|------|-------|-------|
| `platform/integrations/src/tta_dev_integrations/auth/clerk_primitive.py` | 1 | Entire file is a stub |
| `platform/integrations/src/tta_dev_integrations/auth/jwt_primitive.py` | 1 | Entire file is a stub |
| `platform/integrations/src/tta_dev_integrations/auth/auth0_primitive.py` | 1 | Entire file is a stub |
| `platform/integrations/src/tta_dev_integrations/database/postgresql_primitive.py` | 1 | Entire file is a stub |
| `platform/integrations/src/tta_dev_integrations/database/sqlite_primitive.py` | 1 | Entire file is a stub |
| `platform/integrations/src/tta_dev_integrations/database/supabase_primitive.py` | 3 | Partial stubs |
| `platform/primitives/src/tta_dev_primitives/knowledge/knowledge_base.py` | 5 | Awaiting MCP tool |
| `platform/primitives/src/tta_dev_primitives/cli/app.py` | 2 | Template generation helpers |

- [x] For each file above: either implement the stub or add a corresponding Logseq TODO entry
  with `#dev-todo`, `type::`, `priority::`, and `package::` properties.

---

## Phase 3: Test Coverage (Restore ≥80% / 100% for new code)

> **Goal:** Raise platform/ coverage from **47%** to **≥80%** (Codecov project target)
> and ensure all new code achieves **100%** coverage.
> Tests must follow the AAA (Arrange / Act / Assert) pattern and use `MockPrimitive`.

### 3.1 — Priority Coverage Gaps (0% coverage modules)

These modules have **zero test coverage** and are the highest priority for new tests:

| Module | Lines | Priority | Notes |
|--------|-------|----------|-------|
| `recovery/circuit_breaker.py` | 150 | 🔴 Critical | Core resilience primitive |
| `recovery/compensation.py` | 96 | 🔴 Critical | Saga / rollback logic |
| `recovery/timeout.py` | 33 | 🔴 Critical | Timeout primitive |
| `performance/memory.py` | 126 | 🔴 High | In-memory store |
| `package_managers/uv.py` | 101 | 🟠 High | uv wrapper |
| `speckit/` (5 files) | 878 | 🟠 High | SDD spec primitives |
| `research/free_tier_research.py` | 110 | 🟡 Medium | Research automation |
| `testing/mocks.py` | 51 | 🟡 Medium | MockPrimitive itself |

### 3.2 — Low Coverage Modules (<50%)

| Module | Coverage | Lines Missed | Action Needed |
|--------|----------|-------------|---------------|
| `recovery/circuit_breaker.py` | 27% | 109 | Full test suite for all states |
| `recovery/compensation.py` | 17% | 80 | Test saga execution + rollback |
| `recovery/timeout.py` | 36% | 21 | Test timeout expiry paths |
| `performance/cache.py` | 72% | 16 | Cover cache miss + expiry paths |
| `recovery/fallback.py` | 80% | 19 | Cover fallback chain exhaustion |
| `testing/mocks.py` | 31% | 35 | Cover `side_effect` callable path |

### 3.3 — Test Writing Guidelines

All new tests must follow the AAA pattern:

```python
import pytest
from tta_dev_primitives.core.base import WorkflowContext
from tta_dev_primitives.testing import MockPrimitive

@pytest.mark.asyncio
async def test_circuit_breaker_opens_after_threshold():
    """Test that CircuitBreaker opens after exceeding failure threshold."""
    # Arrange
    from tta_dev_primitives.recovery.circuit_breaker import CircuitBreaker
    breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=1.0)
    failing_primitive = MockPrimitive("fail", side_effect=ValueError("simulated failure"))
    context = WorkflowContext(workflow_id="test-cb")

    # Act
    for _ in range(3):
        with pytest.raises(ValueError):
            await breaker.execute(failing_primitive, context)

    # Assert
    assert breaker.state == "open"
```

- [ ] Write `tests/test_circuit_breaker.py` — full state-machine coverage (closed → open → half-open)
- [ ] Write `tests/test_compensation.py` — saga execution, partial rollback, full rollback
- [ ] Write `tests/test_timeout_primitive.py` — timeout expiry, cancellation, success path
- [ ] Write `tests/test_memory_primitive.py` — add, get, eviction, capacity limits
- [ ] Write `tests/test_mock_primitive.py` — `return_value`, `side_effect` callable, call tracking
- [ ] Write tests for `speckit/` primitives (specify, plan, tasks, implement phases)
- [ ] Write tests for `research/free_tier_research.py`
- [ ] Write tests for `package_managers/uv.py`
- [ ] Verify coverage: `uv run pytest --cov=platform --cov-report=term-missing` → ≥80%

---

## Execution Order

```
Phase 1 first → Phase 2 second → Phase 3 last
```

Rationale:
1. Phase 1 (ruff + pyright) changes are mechanical and non-behavioral — safe to batch.
2. Phase 2 (TODO compliance) is purely in Logseq markdown — no Python changes.
3. Phase 3 (test coverage) depends on Phase 1 being clean so new tests don't inherit lint debt.

---

## CI Gate Commands (Verify Before Each Commit)

```bash
uv run ruff format .                         # Auto-format
uv run ruff check . --fix                    # Lint + auto-fix
uvx pyright platform/                        # Type check
uv run python scripts/validate-todos.py      # TODO compliance
uv run pytest -v --tb=short \
  -m "not integration and not slow and not external" \
  --cov=platform --cov-report=term-missing   # Tests + coverage
```

All five commands must exit 0 before opening a PR.

---

**Logseq:** [[TTA.dev/Remediation Plan 2026-03-05]]
