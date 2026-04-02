# TTA.dev Audit Remediation Plan
**Date:** 2026-04-01
**Source:** Full-spectrum repo audit (CGC dead code, complexity, grep stubs, architecture + code quality agents)

## Background

A Copilot fleet mode session had been run prior to this audit. The audit revealed:
- A `.cline/` directory with ~5,000+ lines of unintegrated Copilot-generated code polluting CGC
- 4 critical runtime bugs (router TypeError, OTel hard imports, store race condition, Gemini thread safety)
- 5 significant defects (tool handler stubs, ToolCallLoop incompatibility, fake streaming, unsafe deserialization, unguarded import)
- Structural/quality debt in docs, tests, and complexity

---

## Tasks

### Task 1 — Remove `.cline/` directory [P0 · structural]

**Scope:** Delete the entire `.cline/` tree from the repo. It contains Copilot IDE config artifacts and generated (non-integrated) code that has no place in the production codebase.

**Files:**
- `.cline/advanced/analytics_system.py` (~1,194 lines)
- `.cline/advanced/multi_agent_optimizer.py` (~1,125 lines)
- `.cline/advanced/tool_aware_engine.py` (~1,186 lines)
- `.cline/advanced/dynamic_context_loader.py` (~963 lines)
- `.cline/mcp-server/tta_recommendations.py` (~875 lines)
- `.cline/tests/` (phase2 and phase3 test files)
- Any other `.cline/` content

**Acceptance criteria:**
- `.cline/` directory no longer exists in repo
- No references to `.cline/` remain in pyproject.toml, .gitignore (unless already gitignored), or any import
- Committed with `chore:` prefix

---

### Task 2 — Add OTel `try/except` guards to 5 core primitives [P1 · critical · mechanical]

**Scope:** Five files do bare `from opentelemetry import trace` at module level with no guard. Every other file in the codebase wraps this. Fix all five to match the established pattern.

**Pattern to apply (established in codebase):**
```python
try:
    from opentelemetry import trace
    _TRACING_AVAILABLE = True
except ImportError:
    trace = None  # type: ignore[assignment]
    _TRACING_AVAILABLE = False
```

Then guard all `trace.*` calls with `if _TRACING_AVAILABLE and trace is not None:`.

**Files to fix:**
- `ttadev/primitives/recovery/retry.py:14`
- `ttadev/primitives/recovery/fallback.py:11`
- `ttadev/primitives/recovery/compensation.py:12`
- `ttadev/primitives/safety/safety_gate_primitive.py:29`
- `ttadev/primitives/core/conditional.py:12`

**Acceptance criteria:**
- All 5 files import OTel with try/except guard
- All uses of `trace` in those files are gated on `_TRACING_AVAILABLE`
- `uv run pytest tests/` passes (especially recovery and safety tests)
- `uvx pyright ttadev/` no new errors

---

### Task 3 — Add file locking to `ControlPlaneStore` [P1 · critical]

**Scope:** `ControlPlaneStore` in `ttadev/control_plane/store.py` has a read-modify-write race condition in all mutating operations. Two concurrent agents can silently overwrite each other's task mutations.

**Current pattern (all `put_*` methods):**
```python
data = self._read_map(path)   # step 1: read
data[key] = value              # step 2: modify
self._write_map(path, data)    # step 3: write (atomic rename, but no lock on RMW cycle)
```

**Fix:** Add advisory file locking around every read-modify-write cycle. Use `filelock.FileLock` (already a dependency or add `filelock` to deps). Each JSON file (tasks, leases, steps) gets its own lock file (e.g., `tasks.json.lock`).

```python
from filelock import FileLock

def _tasks_lock(self) -> FileLock:
    return FileLock(str(self._tasks_path) + ".lock")
```

Wrap every `put_task`, `put_lease`, `put_step`, `get_lease_for_run` and any other RMW cycle in `with self._tasks_lock():`.

**Acceptance criteria:**
- All mutating operations on `tasks.json`, `leases.json`, `steps.json` hold a file lock for the duration of the RMW
- `filelock` added to `pyproject.toml` dependencies if not already present
- Existing control plane tests pass
- New test: concurrent writes from two threads do not lose data

---

### Task 4 — Fix `AgentRouterPrimitive` constructor injection [P1 · critical]

**Scope:** `AgentRouterPrimitive` instantiates every registered agent class with `agent_class()` but all concrete agents require `model: ChatPrimitive` as a mandatory constructor arg. This raises `TypeError` on every routing call.

**File:** `ttadev/agents/router.py`

**Fix approach:**
- `AgentRouterPrimitive` should accept `model: ChatPrimitive` at construction time
- All `agent_class()` calls should become `agent_class(model=self._model)`
- The scoring loop (line 87–91) instantiates ALL agents for scoring; this should be refactored to use `agent_class.spec` (class-level attribute) for scoring without instantiation — lazy init only for the chosen agent

**Also fix in `ttadev/agents/base.py:77`:**
The placeholder tool handlers `lambda args, t=tool: f"[{t.name} executed]"` should raise `NotImplementedError` with a clear message rather than silently returning fake strings. This makes incomplete wiring visible rather than hiding it.

**Acceptance criteria:**
- `AgentRouterPrimitive` accepts and stores `model: ChatPrimitive`
- Routing calls no longer raise `TypeError`
- Scoring does not instantiate all agents; only the selected agent is instantiated
- Tool handler stubs raise `NotImplementedError` with actionable message
- Tests updated/added to cover the routing path

---

### Task 5 — Fix Gemini thread safety and `_call_gemini` temperature [P1 · critical]

**Scope:** `genai.configure(api_key=...)` mutates a module-level singleton. Race condition in concurrent workflows. Also `_call_gemini` ignores `request.temperature`.

**Files:**
- `ttadev/primitives/llm/universal_llm_primitive.py:336,384`
- `ttadev/primitives/integrations/google_ai_studio_primitive.py:88`

**Fix:** Remove `genai.configure()` calls entirely. Instead, pass the API key via environment variable `GOOGLE_API_KEY` (which the SDK reads automatically), or use the newer `google.generativeai.Client(api_key=...)` per-call constructor if available. If neither works, use a module-level lock around the configure+call sequence as a minimum viable fix.

Also fix `_call_gemini` to pass `generation_config={"temperature": request.temperature}` when `request.temperature` is not None.

**Acceptance criteria:**
- No `genai.configure()` calls remain in either file
- `_call_gemini` passes temperature to the SDK
- `uvx pyright ttadev/` no new errors
- Existing LLM tests pass

---

### Task 6 — Fix unguarded OTel import in `control_plane/service.py` [P2 · warning]

**Scope:** `_get_active_otel_context()` in `ttadev/control_plane/service.py:49` does a bare `from opentelemetry import trace as _otel_trace` inside the function body with no try/except. Called on every `claim_task()`.

**Fix:** Wrap in `try/except ImportError`, return a no-op context object if OTel not available.

**Acceptance criteria:**
- `claim_task()` works in environments without `opentelemetry` installed
- Existing control plane tests pass

---

### Task 7 — Fix Gemini streaming and mark `ToolCallLoop` as experimental [P2 · warning]

**Scope:**
1. `_stream_gemini` buffers full response and yields once — not real streaming
2. `ToolCallLoop` uses `__tool_call__:` prefix incompatible with all LLM provider APIs

**For `_stream_gemini`** (`universal_llm_primitive.py:358-390`):
Use the SDK's streaming API (`model.generate_content(..., stream=True)`) and yield chunks as they arrive. If the SDK version doesn't support async streaming, add a docstring note and a `# TODO #dev-todo` tag marking it for proper async streaming.

**For `ToolCallLoop`** (`ttadev/agents/tool_call_loop.py`):
- Add a prominent module-level docstring explaining the `__tool_call__:` prefix is a custom convention requiring a system prompt that instructs the model to use it
- Mark the class with a `#dev-todo` noting incompatibility with native tool-calling APIs
- Do NOT rewrite the tool-calling protocol in this task — that is a separate architectural decision

**Acceptance criteria:**
- Gemini streaming yields tokens progressively (or has a clear TODO with #dev-todo tag)
- ToolCallLoop has explanatory docstring about its custom protocol
- Tests pass

---

### Task 8 — Fix `SequentialPrimitive` failure metrics + add `__all__` to benchmarking/extensions [P3 · quality]

**Scope:** Two separate mechanical fixes:

**A. SequentialPrimitive failure metrics** (`ttadev/primitives/core/sequential.py:127-129`):
Add a `finally` block (or `except` + re-raise) that calls `metrics_collector.record_execution(..., success=False)` when a step raises. Currently failures bypass metric recording entirely.

**B. Add `__all__` to benchmarking and extensions:**
- `ttadev/primitives/benchmarking/__init__.py` (950 lines) — no `__all__`; add one listing all public classes/functions
- `ttadev/primitives/extensions/__init__.py` — no `__all__`; add one

**Acceptance criteria:**
- Sequential step failures show in metrics as `success=False`
- `ttadev.primitives.benchmarking.__all__` is defined
- `ttadev.primitives.extensions.__all__` is defined
- Tests pass, no regressions

---

### Task 9 — Mark all stubs with CI-blocking `#dev-todo` tags [P3 · hygiene]

**Scope:** Several modules have stubs (returning `[]`, raising `NotImplementedError`) that are silently wrong. Mark all with proper `#dev-todo` tags per CLAUDE.md standard.

**Targets:**
- `ttadev/primitives/knowledge/knowledge_base.py:164,185,200,215,228` — 5x `# TODO: Call configured backend`
- `ttadev/integrations/src/tta_dev_integrations/auth/clerk_primitive.py:3`
- `ttadev/integrations/src/tta_dev_integrations/auth/jwt_primitive.py:3`
- `ttadev/integrations/src/tta_dev_integrations/auth/auth0_primitive.py:3`
- `ttadev/integrations/src/tta_dev_integrations/database/postgresql_primitive.py:3`
- `ttadev/integrations/src/tta_dev_integrations/database/sqlite_primitive.py:3`

**Format per CLAUDE.md:**
```markdown
- TODO <description> #dev-todo
  type:: implementation
  priority:: high
  package:: <package-name>
```

In Python files, as comments:
```python
# TODO: Implement ClerkAuthPrimitive #dev-todo
# type:: implementation
# priority:: high
# package:: tta-dev-integrations
```

**Acceptance criteria:**
- All listed stubs have properly formatted `#dev-todo` tags
- `uv run ruff check .` passes (no new lint issues)

---

## Deferred (requires architectural decisions)

- **Task D1** — Decompose `create_server` (CC=50) and `_handle_task_command` (CC=54) — significant refactor, own session
- **Task D2** — Resolve dual integration package structure (`primitives/integrations/` vs `integrations/src/`) — architectural decision needed first
- **Task D3** — Fix Redis `pickle.loads` unsafe deserialization — requires deciding on serialization format
- **Task D4** — Fix `ToolCallLoop` to use native provider tool-calling APIs — significant redesign

---

## Execution Notes

- Work on a feature branch: `fix/audit-remediation-2026-04-01`
- Tasks 1–3 are independent and can go first (cleanup + mechanical OTel fix)
- Tasks 4, 5, 6 are P1/P2 bug fixes
- Tasks 7–9 are quality/hygiene
- Each task gets its own commit with conventional commit prefix
