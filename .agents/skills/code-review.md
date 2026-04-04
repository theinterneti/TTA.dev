---
name: code-review
description: TTA.dev code review guidelines for OpenHands — covers primitives, typing, testing, TODOs, and security
triggers:
  - /codereview
---

# TTA.dev Code Review Guidelines

> **Scope:** Apply these rules to every Python file under `ttadev/` and every
> test file under `tests/`. Frontend (`apps/**/frontend/`), CI workflows
> (`.github/workflows/`), and `secrets/` are out of scope for this skill.

---

## 1. APPROVE vs COMMENT Decision

### APPROVE immediately (no blocking issues) when the PR is:

- **Docs-only** — changes limited to `*.md`, `docs/`, `CHANGELOG.md`, or docstring updates with no logic changes.
- **Test-only** — new or updated tests that follow all testing requirements (see §4) and have no production-code changes.
- **Config following existing patterns** — `pyproject.toml`, `pytest.ini`, or `ruff` config changes that clearly mirror the existing style (e.g. adding a rule to the `ignore` list already present, bumping a pinned version).

### Leave a COMMENT (do NOT approve) when the PR contains:

- Any 🔴 Critical anti-pattern from §2.
- A security concern from §7.
- Wrong or missing primitive composition (§6).
- Missing type hints or docstrings on **public** functions/classes (§3).
- Test suite gaps or broken test patterns (§4).
- Malformed TODO blocks (§5).

When leaving a COMMENT, always:

1. Quote the offending line(s) with a GitHub suggestion block where possible.
2. State which rule is violated (e.g. "§2 — Manual retry loop").
3. Provide a corrected code snippet.

---

## 2. Core Anti-patterns — 🔴 CRITICAL (always flag, block merge)

### 2.1 Manual retry or timeout loops

**Never** write retry or timeout logic by hand. Use `RetryPrimitive` and
`TimeoutPrimitive` from `ttadev.primitives.recovery`.

```python
# ❌ FORBIDDEN
for attempt in range(3):
    try:
        result = await call_api()
        break
    except Exception:
        await asyncio.sleep(2 ** attempt)

# ✅ CORRECT
from ttadev.primitives import RetryPrimitive, RetryStrategy, LambdaPrimitive

workflow = RetryPrimitive(
    LambdaPrimitive(call_api),
    strategy=RetryStrategy(max_retries=3, backoff_base=2.0),
)
result = await workflow.execute(input_data, ctx)
```

### 2.2 Global mutable state instead of `WorkflowContext`

State that must survive across primitive boundaries belongs in
`WorkflowContext.state` or `WorkflowContext.metadata`, not in module-level
globals or class variables shared across executions.

```python
# ❌ FORBIDDEN
_cache: dict = {}  # module-level mutable state

# ✅ CORRECT
# Read/write via context:
ctx.state["my_key"] = value
value = ctx.state.get("my_key")
```

### 2.3 Legacy type hint syntax

The project targets Python ≥ 3.12; use PEP 604/585 union and built-in
collection types everywhere.

```python
# ❌ FORBIDDEN
from typing import Optional, Dict, List, Tuple
def foo(x: Optional[str]) -> Dict[str, Any]: ...

# ✅ CORRECT
def foo(x: str | None) -> dict[str, Any]: ...
```

Specifically flag: `Optional[...]`, `Union[...]`, `Dict[...]`, `List[...]`,
`Tuple[...]`, `Set[...]` in any new code.

### 2.4 `import pip` / inline `pip install`

All dependency management uses `uv`. Never install packages at runtime.

```python
# ❌ FORBIDDEN
import subprocess
subprocess.run(["pip", "install", "requests"])

import pip
pip.main(["install", "requests"])

# ✅ CORRECT — add to pyproject.toml and run:
# uv add requests
```

### 2.5 Bare `except Exception` without re-raise or logging

Silent exception swallowing hides failures and breaks observability.

```python
# ❌ FORBIDDEN
try:
    result = await primitive.execute(data, ctx)
except Exception:
    pass  # silent swallow

# ✅ CORRECT — always log or re-raise
from ttadev.primitives.observability.logging import get_logger
logger = get_logger(__name__)

try:
    result = await primitive.execute(data, ctx)
except Exception as exc:
    logger.error("operation_failed", error=str(exc), workflow_id=ctx.workflow_id)
    raise
```

### 2.6 `print()` for logging

All structured logging must go through `structlog` via the project's logger
factory. `print()` is only acceptable in CLI entry-points and scripts.

```python
# ❌ FORBIDDEN (in ttadev/ library code)
print(f"Executing workflow {ctx.workflow_id}")

# ✅ CORRECT
from ttadev.primitives.observability.logging import get_logger
logger = get_logger(__name__)
logger.info("workflow_executing", workflow_id=ctx.workflow_id)
```

### 2.7 `time.sleep()` in async code

Blocking sleep in an async function stalls the event loop.

```python
# ❌ FORBIDDEN
import time
async def my_primitive(data, ctx):
    time.sleep(1)  # blocks the event loop

# ✅ CORRECT
import asyncio
async def my_primitive(data, ctx):
    await asyncio.sleep(1)
```

### 2.8 Hardcoded secrets or API keys

No credentials, tokens, API keys, or passwords may appear in source files —
not even partially, not even in comments.

```python
# ❌ FORBIDDEN
GROQ_API_KEY = "gsk_abc123..."
client = OpenAI(api_key="sk-proj-...")

# ✅ CORRECT
import os
api_key = os.environ["GROQ_API_KEY"]
```

If a secret is found, comment immediately with `🔴 Security — remove this
credential and rotate it. See §7.`

---

## 3. Code Style — 🟡 Suggestion (flag, but don't block)

### 3.1 Line length

`ruff` enforces 100-character lines. Watch for logical lines (multi-condition
`if`, chained method calls) that exceed 100 chars even after formatting — these
are style issues that ruff may not catch.

### 3.2 Type hints on all public functions

Every public function and method must have:
- Typed parameters (including `self` is optional, but all others required).
- An explicit return type annotation (`-> None` if nothing is returned).

```python
# ❌ Missing type hints
def process(data, context):
    return data

# ✅ Correct
async def process(data: str, context: WorkflowContext) -> dict[str, Any]:
    return {"result": data}
```

### 3.3 Google-style docstrings on public API

Every public class, method, and function must have a Google-style docstring
with `Args:`, `Returns:`, and `Raises:` sections (omit sections that don't
apply).

```python
def calculate_delay(self, attempt: int) -> float:
    """Calculate delay before the next retry attempt.

    Args:
        attempt: Zero-indexed retry attempt number.

    Returns:
        Delay in seconds, capped at ``max_backoff``.
    """
```

### 3.4 Import order

Imports must follow: **stdlib → third-party → local `ttadev.*`**, with a blank
line separating each group. Use `from __future__ import annotations` at the top
of every `ttadev/` module.

```python
from __future__ import annotations

import asyncio
import time
from abc import ABC, abstractmethod

import structlog
from pydantic import BaseModel

from ttadev.primitives.core.base import WorkflowContext, WorkflowPrimitive
from ttadev.primitives.observability.logging import get_logger
```

---

## 4. Testing Requirements

### 4.1 Coverage

- **New code** added by this PR must have **100% test coverage**.
- The project-wide floor is 80% (`fail_under = 80` in `pyproject.toml`); new
  code must never drag coverage below that floor.

### 4.2 Async test decoration

Every async test function must be decorated with `@pytest.mark.asyncio`.
(`asyncio_mode = "auto"` is set in `pytest.ini`, so the decorator is
technically optional, but keep it for explicitness and grep-ability.)

```python
@pytest.mark.asyncio
async def test_retry_succeeds_on_second_attempt(monkeypatch: pytest.MonkeyPatch) -> None:
    ...
```

### 4.3 Use `MockPrimitive` — never real primitives in unit tests

```python
# ❌ FORBIDDEN in unit tests
from ttadev.primitives import RetryPrimitive, LambdaPrimitive
real_call = LambdaPrimitive(lambda d, c: actual_api_call(d))

# ✅ CORRECT
from ttadev.primitives.testing.mocks import MockPrimitive

mock = MockPrimitive("api-call", return_value={"status": "ok"})
workflow = RetryPrimitive(mock, strategy=RetryStrategy(max_retries=2))
```

`MockPrimitive` constructor signature:

```python
MockPrimitive(
    name: str,
    return_value: Any | None = None,
    side_effect: Callable | None = None,
    raise_error: Exception | None = None,
)
```

After execution: `mock.call_count`, `mock.calls` (list of `(input, ctx)` tuples),
`mock.assert_called()`.

### 4.4 AAA pattern — mandatory

Every test function must have exactly three labelled sections:

```python
async def test_retry_exhausts_all_attempts(monkeypatch: pytest.MonkeyPatch) -> None:
    # Arrange
    error = ConnectionError("network down")
    mock = MockPrimitive("flaky", raise_error=error)
    strategy = RetryStrategy(max_retries=2, jitter=False)
    primitive = RetryPrimitive(mock, strategy=strategy)
    monkeypatch.setattr("asyncio.sleep", AsyncMock())
    ctx = WorkflowContext(workflow_id="test")

    # Act
    with pytest.raises(ConnectionError, match="network down"):
        await primitive.execute("data", ctx)

    # Assert
    assert mock.call_count == 3  # initial + 2 retries
```

### 4.5 No external dependencies in unit tests

- No real HTTP calls — patch with `unittest.mock.AsyncMock` or `respx`.
- No real database connections — use `FakeUnitOfWork` from
  `ttadev.primitives.persistence` or `fakeredis`.
- No real filesystem writes — use `tmp_path` pytest fixture.
- Tests tagged `@pytest.mark.integration` or `@pytest.mark.external` are exempt.

---

## 5. TODO Format — 🔴 CRITICAL (malformed TODOs block CI)

Every TODO comment in `ttadev/` source must follow the Logseq block format
exactly. The `scripts/issue_manager.py` parser enforces this, and CI will fail
on malformed blocks.

### Required format

```python
# - TODO <description of the work> #dev-todo
#   type:: <bug|implementation|refactor|documentation|observability>
#   priority:: <critical|high|medium|low>
#   package:: <package-name>
```

Rules:
- The `#dev-todo` tag **must** appear on the first line.
- `type::`, `priority::`, and `package::` properties must appear **within 5 lines** of the TODO.
- All three properties are mandatory — missing any one is a CI failure.

### Valid example

```python
# - TODO Add circuit-breaker half-open jitter to prevent thundering herd #dev-todo
#   type:: implementation
#   priority:: medium
#   package:: ttadev.primitives.recovery
```

### Invalid examples (flag as 🔴)

```python
# TODO: add retry logic here        ← missing #dev-todo, missing properties
# FIXME: this is broken             ← not in TODO block format
# TODO improve performance          ← missing #dev-todo tag
```

---

## 6. Primitives Composition

### 6.1 Standard composition pattern

External calls (API, DB, filesystem) must always be wrapped with error-recovery
primitives. The canonical composition order is:

```
RetryPrimitive(
    CachePrimitive(
        TimeoutPrimitive(
            LambdaPrimitive(fn)
        )
    )
)
```

```python
from ttadev.primitives import (
    CachePrimitive, LambdaPrimitive, RetryPrimitive,
    RetryStrategy, TimeoutPrimitive,
)
from ttadev.primitives.performance.cache import InMemoryBackend

workflow = RetryPrimitive(
    CachePrimitive(
        TimeoutPrimitive(
            LambdaPrimitive(fetch_user_profile),
            timeout_seconds=5.0,
        ),
        backend=InMemoryBackend(),
        ttl_seconds=300,
    ),
    strategy=RetryStrategy(max_retries=3, backoff_base=2.0),
)
result = await workflow.execute(user_id, ctx)
```

### 6.2 Never chain without error recovery on external calls

If a `LambdaPrimitive` or custom primitive makes a network call, a DB call, or
reads from the filesystem, it **must** be wrapped in at least `RetryPrimitive`
or `FallbackPrimitive`. Naked external calls are a 🔴 Critical flag.

### 6.3 `WorkflowContext` must be threaded through — never created fresh inside a primitive

```python
# ❌ FORBIDDEN — discards trace context, correlation ID, agent identity
async def execute(self, data: str, context: WorkflowContext) -> str:
    inner_ctx = WorkflowContext()  # creates orphaned root context
    return await self.inner.execute(data, inner_ctx)

# ✅ CORRECT — derive a child to preserve the trace chain
async def execute(self, data: str, context: WorkflowContext) -> str:
    child_ctx = WorkflowContext.child(context, step_name="inner-step")
    return await self.inner.execute(data, child_ctx)
```

### 6.4 Custom `WorkflowPrimitive` subclasses

Every subclass must:
1. Inherit from `WorkflowPrimitive[TInput, TOutput]` with concrete type parameters.
2. Implement `async def execute(self, input_data: TInput, context: WorkflowContext) -> TOutput`.
3. Log start/end via `get_logger(__name__)` with structlog kwargs (not f-strings).
4. Record checkpoints via `context.checkpoint("step.name")` for observability.

```python
from ttadev.primitives.core.base import WorkflowContext, WorkflowPrimitive
from ttadev.primitives.observability.logging import get_logger

logger = get_logger(__name__)

class MyPrimitive(WorkflowPrimitive[str, dict[str, str]]):
    """One-line summary.

    Args describe constructor params here if any.
    """

    async def execute(self, input_data: str, context: WorkflowContext) -> dict[str, str]:
        """Execute the primitive.

        Args:
            input_data: The string to process.
            context: Workflow context carrying trace and correlation IDs.

        Returns:
            Processed result dictionary.
        """
        context.checkpoint("my_primitive.start")
        logger.info("my_primitive_start", input=input_data, workflow_id=context.workflow_id)

        result = {"output": input_data.upper()}

        context.checkpoint("my_primitive.end")
        logger.info("my_primitive_end", workflow_id=context.workflow_id)
        return result
```

### 6.5 Operator chaining (`>>` and `|`)

Prefer the operator API over explicit `SequentialPrimitive`/`ParallelPrimitive`
construction — it reads like a pipeline and is easier to extend.

```python
# Sequential
pipeline = validate >> transform >> persist

# Parallel
results = fetch_users | fetch_products | fetch_inventory
```

---

## 7. Security

### 7.1 Never log secrets — even partially

`logger.info("auth_ok", api_key=key[:8] + "...")` is **still a violation**. Log
only opaque identifiers (e.g. a hash or the last 4 chars if strictly needed for
debugging, and only at `DEBUG` level gated by a feature flag).

### 7.2 URL validation

Use `urllib.parse.urlparse()`, not substring checks.

```python
# ❌ FORBIDDEN
if "http" in url and "://" in url:
    ...

# ✅ CORRECT
from urllib.parse import urlparse
parsed = urlparse(url)
if parsed.scheme not in ("http", "https") or not parsed.netloc:
    raise ValueError(f"Invalid URL: {url!r}")
```

### 7.3 Input validation for user-facing CLI commands

Any CLI command that accepts user input must validate it with Pydantic or
explicit checks before passing values to shell commands, file paths, or
primitives. Flag raw `subprocess.run(user_input)` as 🔴 Critical.

### 7.4 Dependency hygiene

New dependencies added to `pyproject.toml` must:
- Be well-maintained (last release < 12 months).
- Not duplicate functionality already provided by an existing dep.
- Be added to the correct section (`dependencies` vs `dependency-groups.dev`
  vs `project.optional-dependencies`).

---

## Quick Reference Checklist

Use this before posting a review:

```
□ No manual retry/timeout loops (§2.1)
□ No global mutable state (§2.2)
□ No legacy typing syntax Optional/Dict/List (§2.3)
□ No pip install at runtime (§2.4)
□ No silent except swallowing (§2.5)
□ No print() in library code (§2.6)
□ No time.sleep() in async functions (§2.7)
□ No hardcoded secrets (§2.8)
□ Type hints on all public functions (§3.2)
□ Google docstrings on all public functions (§3.3)
□ Tests use MockPrimitive, not real primitives (§4.3)
□ Tests follow AAA pattern (§4.4)
□ Tests have no external dependencies (§4.5)
□ TODOs have #dev-todo + type:: priority:: package:: (§5)
□ External calls wrapped in RetryPrimitive/FallbackPrimitive (§6.2)
□ WorkflowContext derived from parent, not created fresh (§6.3)
□ No secrets in logs (§7.1)
□ URL validation uses urlparse() (§7.2)
```
