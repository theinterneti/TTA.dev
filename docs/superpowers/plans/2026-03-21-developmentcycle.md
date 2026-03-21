# DevelopmentCycle Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build `DevelopmentCycle` — the five-step Orient → Recall → Write → Validate → Retain loop as a single composable `InstrumentedPrimitive`. Phase 3 of the DevelopmentCycle integration design.

**Architecture:** `DevelopmentCycle(InstrumentedPrimitive[DevelopmentTask, DevelopmentResult])` in `ttadev/workflows/development_cycle.py`. Composes `CodeGraphPrimitive`, `AgentMemory`, and `CodeExecutionPrimitive` with an `httpx.AsyncClient` LLM call (via `get_llm_client()`). All three dependencies are injected for testing.

**Tech stack:** `httpx==0.28.1` (already in venv, same pattern as `HindsightClient`), `asyncio` for async LLM call, all primitives already built.

---

## Key Context

**Existing patterns to follow:**
- `ttadev/primitives/code_graph/primitive.py` — `_cgc_tracer` pattern for OTel span injection in tests; `nullcontext()` for optional tracer; span set_attribute pattern
- `ttadev/primitives/memory/client.py` — `httpx.AsyncClient` injection via constructor
- `ttadev/primitives/memory/agent_memory.py` — `_client: HindsightClient | None` injection pattern

**Imports for the implementation:**
```python
from ttadev.primitives.code_graph import CGCOp, CodeGraphPrimitive, CodeGraphQuery, ImpactReport
from ttadev.primitives.memory import AgentMemory
from ttadev.primitives.core.base import WorkflowContext
from ttadev.primitives.observability import InstrumentedPrimitive
from ttadev.primitives.integrations.e2b_primitive import CodeExecutionPrimitive
from ttadev.workflows.llm_provider import get_llm_client
```

**`CodeGraphPrimitive` input/output:**
```python
# Input: CodeGraphQuery TypedDict — target (str) + operations (list[CGCOp])
# Output: ImpactReport TypedDict — callers, dependencies, related_tests, complexity, risk, summary, cgc_available
query = CodeGraphQuery(target="retry.py", operations=[CGCOp.find_code, CGCOp.get_relationships, CGCOp.find_tests])
report: ImpactReport = await self._graph.execute(query, context)
# Always returns ImpactReport — degrades gracefully, never raises
```

**`AgentMemory` interface:**
```python
prefix: str = await self._memory.build_context_prefix(query)  # "" if unavailable
result: RetainResult = await self._memory.retain(content)      # success=False if unavailable
```

**`CodeExecutionPrimitive` interface:**
```python
# CodeInput(code: str, language: str, timeout: int)
# CodeOutput(output: str, error: str|None, success: bool, sandbox_id: str, ...)
output: CodeOutput = await self._executor.execute({"code": code, "language": "python"}, context)
```

**LLM call pattern (OpenAI-compatible):**
```python
cfg = get_llm_client()  # LLMClientConfig(base_url, model, api_key, provider)
resp = await self._http.post(
    f"{cfg.base_url}/chat/completions",
    headers={"Authorization": f"Bearer {cfg.api_key}"},
    json={"model": cfg.model, "messages": [{"role": "system", "content": sys}, {"role": "user", "content": user}]},
)
data = resp.json()
content = data["choices"][0]["message"]["content"]
```

**OTel pattern (from `CodeGraphPrimitive`):**
```python
# In __init__:
self._dc_tracer = self._tracer  # separate ref; tests set _tracer=None, _dc_tracer=mock

# In _execute_impl:
span_cm = self._dc_tracer.start_as_current_span("development_cycle.step") if self._dc_tracer else nullcontext()
with span_cm as span:
    ...
    if span is not None:
        span.set_attribute("key", value)
```

**`_empty_impact_report()` pattern:**
```python
def _empty_impact_report() -> ImpactReport:
    return ImpactReport(
        target="", callers=[], dependencies=[], related_tests=[],
        complexity=0.0, risk="low", summary="No orient data.", cgc_available=False
    )
```

**Agent hint → system prompt persona:**
```python
_PERSONAS: dict[str, str] = {
    "developer": "You are an expert Python developer. Write clean, testable code.",
    "qa": "You are a QA engineer. Review code for correctness, edge cases, and test coverage.",
    "security": "You are a security engineer. Review code for vulnerabilities and unsafe patterns.",
}

def _build_system_prompt(agent_hint: str, context_prefix: str) -> str:
    persona = _PERSONAS.get(agent_hint, f"You are a {agent_hint}.")
    if context_prefix:
        return f"{persona}\n\n{context_prefix}"
    return persona
```

---

## File Map

| Action | Path | Purpose |
|---|---|---|
| Create | `ttadev/workflows/development_cycle.py` | `DevelopmentCycle`, `DevelopmentTask`, `DevelopmentResult` |
| Modify | `ttadev/workflows/__init__.py` | Export the three new names |
| Create | `tests/workflows/test_development_cycle.py` | Unit tests (all dependencies mocked) |

---

## Task 1: Retain design decision to Hindsight (pre-implementation)

**Files:** None (MCP API call only)

- [ ] **Step 1: Retain design decision**

POST to `http://localhost:8888/v1/default/banks/tta-dev/memories`:
```json
{
  "items": [{
    "content": "[type: decision] DevelopmentCycle is InstrumentedPrimitive[DevelopmentTask, DevelopmentResult] in ttadev/workflows/development_cycle.py. Five steps: Orient (CodeGraphPrimitive), Recall (AgentMemory.build_context_prefix), Write (get_llm_client()+httpx), Validate (CodeExecutionPrimitive/E2B), Retain (AgentMemory.retain). Write failure re-raises; all other steps degrade gracefully. _dc_tracer pattern for OTel span injection in tests. agent_hint maps to persona string (not AgentRegistry). DevelopmentTask: instruction (required), target_files (optional, max 3), agent_hint (optional). DevelopmentResult: response, validated, impact_report, memories_retained, context_prefix."
  }],
  "async": true
}
```

- [ ] **Step 2: Commit**
```bash
git commit --allow-empty -m "docs(hindsight): retain DevelopmentCycle design decision"
```

---

## Task 2: Types and skeleton

**Files:**
- Create: `ttadev/workflows/development_cycle.py` (types + class skeleton, no step logic)
- Create: `tests/workflows/test_development_cycle.py` (construction + ValueError tests)

- [ ] **Step 1: Write the failing tests**

Create `tests/workflows/test_development_cycle.py`:

```python
"""Unit tests for DevelopmentCycle — all dependencies mocked."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from ttadev.primitives.code_graph import ImpactReport
from ttadev.primitives.memory.types import RetainResult


def _empty_report() -> ImpactReport:
    return ImpactReport(
        target="",
        callers=[],
        dependencies=[],
        related_tests=[],
        complexity=0.0,
        risk="low",
        summary="No orient data.",
        cgc_available=False,
    )


def _make_mocks(
    context_prefix: str = "",
    impact_report: ImpactReport | None = None,
    validate_success: bool = False,
    retain_success: bool = True,
    llm_response: str = "Here is the implementation.",
) -> tuple:
    """Return (mock_memory, mock_graph, mock_executor, mock_http)."""
    mock_memory = MagicMock()
    mock_memory.build_context_prefix = AsyncMock(return_value=context_prefix)
    mock_memory.retain = AsyncMock(
        return_value=RetainResult(success=retain_success, operation_id="op-1" if retain_success else None)
    )

    mock_graph = MagicMock()
    mock_graph.execute = AsyncMock(return_value=impact_report or _empty_report())

    mock_executor = MagicMock()
    mock_executor.execute = AsyncMock(
        return_value={
            "output": "1 passed",
            "error": None,
            "success": validate_success,
            "sandbox_id": "sb-test",
            "execution_time": 1.2,
            "logs": [],
        }
    )

    mock_resp = MagicMock()
    mock_resp.raise_for_status = MagicMock()
    mock_resp.json.return_value = {
        "choices": [{"message": {"content": llm_response}}]
    }
    mock_http = MagicMock()
    mock_http.post = AsyncMock(return_value=mock_resp)

    return mock_memory, mock_graph, mock_executor, mock_http


class TestDevelopmentCycleConstruction:
    def test_constructs_with_defaults(self) -> None:
        from ttadev.workflows.development_cycle import DevelopmentCycle

        cycle = DevelopmentCycle(bank_id="tta-dev")
        assert cycle is not None

    def test_constructs_with_injected_dependencies(self) -> None:
        from ttadev.workflows.development_cycle import DevelopmentCycle

        mock_memory, mock_graph, mock_executor, mock_http = _make_mocks()
        cycle = DevelopmentCycle(
            bank_id="tta-dev",
            _memory=mock_memory,
            _graph=mock_graph,
            _executor=mock_executor,
            _http=mock_http,
        )
        assert cycle is not None


class TestDevelopmentCycleValidation:
    @pytest.mark.asyncio
    async def test_raises_on_empty_instruction(self) -> None:
        from ttadev.primitives.core.base import WorkflowContext
        from ttadev.workflows.development_cycle import DevelopmentCycle, DevelopmentTask

        mock_memory, mock_graph, mock_executor, mock_http = _make_mocks()
        cycle = DevelopmentCycle(
            bank_id="tta-dev",
            _memory=mock_memory,
            _graph=mock_graph,
            _executor=mock_executor,
            _http=mock_http,
        )
        with pytest.raises(ValueError, match="instruction must not be empty"):
            await cycle.execute(DevelopmentTask(instruction=""), WorkflowContext())

    @pytest.mark.asyncio
    async def test_raises_on_missing_instruction(self) -> None:
        from ttadev.primitives.core.base import WorkflowContext
        from ttadev.workflows.development_cycle import DevelopmentCycle, DevelopmentTask

        mock_memory, mock_graph, mock_executor, mock_http = _make_mocks()
        cycle = DevelopmentCycle(
            bank_id="tta-dev",
            _memory=mock_memory,
            _graph=mock_graph,
            _executor=mock_executor,
            _http=mock_http,
        )
        with pytest.raises(ValueError, match="instruction must not be empty"):
            await cycle.execute(DevelopmentTask(), WorkflowContext())
```

- [ ] **Step 2: Run to confirm they fail**
```bash
uv run python -m pytest tests/workflows/test_development_cycle.py -v
```
Expected: `ModuleNotFoundError`

- [ ] **Step 3: Create `ttadev/workflows/development_cycle.py` (types + skeleton)**

```python
"""DevelopmentCycle — Orient → Recall → Write → Validate → Retain as a single primitive.

Phase 3 of the DevelopmentCycle integration design. Composes CodeGraphPrimitive,
AgentMemory, and CodeExecutionPrimitive with a free-LLM Write step into one
observable, composable InstrumentedPrimitive.
"""

from __future__ import annotations

import logging
from contextlib import nullcontext
from typing import Any, TypedDict

import httpx

from ttadev.primitives.code_graph import CGCOp, CodeGraphPrimitive, CodeGraphQuery, ImpactReport
from ttadev.primitives.core.base import WorkflowContext
from ttadev.primitives.integrations.e2b_primitive import CodeExecutionPrimitive
from ttadev.primitives.memory import AgentMemory
from ttadev.primitives.observability import InstrumentedPrimitive
from ttadev.workflows.llm_provider import get_llm_client

logger = logging.getLogger(__name__)

_PERSONAS: dict[str, str] = {
    "developer": "You are an expert Python developer. Write clean, testable code.",
    "qa": "You are a QA engineer. Review code for correctness, edge cases, and test coverage.",
    "security": "You are a security engineer. Review code for vulnerabilities and unsafe patterns.",
}


# ── Types ─────────────────────────────────────────────────────────────────────


class DevelopmentTask(TypedDict, total=False):
    """Input task for DevelopmentCycle.

    Only ``instruction`` is required. All other fields are optional.
    """

    instruction: str        # Required: what to build/analyse/review
    target_files: list[str] # Optional: file paths/names to orient CGC on (max 3)
    agent_hint: str         # Optional: role persona ("developer", "qa", "security")


class DevelopmentResult(TypedDict):
    """Output from a DevelopmentCycle execution."""

    response: str             # LLM-generated output
    validated: bool           # True if E2B ran related tests and they passed
    impact_report: ImpactReport   # From Orient step (empty if CGC unavailable)
    memories_retained: int    # 1 if Hindsight stored the memory; 0 if unavailable
    context_prefix: str       # Memory prefix injected into the LLM system prompt


# ── Helpers ───────────────────────────────────────────────────────────────────


def _empty_impact_report(target: str = "") -> ImpactReport:
    return ImpactReport(
        target=target,
        callers=[],
        dependencies=[],
        related_tests=[],
        complexity=0.0,
        risk="low",
        summary="No orient data.",
        cgc_available=False,
    )


def _build_system_prompt(agent_hint: str, context_prefix: str) -> str:
    persona = _PERSONAS.get(agent_hint, f"You are a {agent_hint}.")
    if context_prefix:
        return f"{persona}\n\n{context_prefix}"
    return persona


# ── Primitive ─────────────────────────────────────────────────────────────────


class DevelopmentCycle(InstrumentedPrimitive[DevelopmentTask, DevelopmentResult]):
    """Five-step Orient → Recall → Write → Validate → Retain loop.

    Composes CodeGraphPrimitive (orient), AgentMemory (recall/retain),
    an LLM call (write), and CodeExecutionPrimitive (validate) into one
    observable, composable primitive.

    All steps except Write degrade gracefully — the cycle never aborts
    due to CGC, Hindsight, or E2B being unavailable.

    Args:
        bank_id: Hindsight bank identifier (default ``"tta-dev"``).
        base_url: Hindsight base URL (default: ``HINDSIGHT_URL`` or localhost:8888).
        agent_hint: Default role persona for Write step (default ``"developer"``).
        timeout: Timeout for Hindsight and network calls in seconds.
        _memory: Injected AgentMemory for testing.
        _graph: Injected CodeGraphPrimitive for testing.
        _executor: Injected CodeExecutionPrimitive for testing.
        _http: Injected httpx.AsyncClient for LLM call testing.
    """

    def __init__(
        self,
        bank_id: str = "tta-dev",
        base_url: str | None = None,
        agent_hint: str = "developer",
        timeout: float = 10.0,
        _memory: AgentMemory | None = None,
        _graph: CodeGraphPrimitive | None = None,
        _executor: CodeExecutionPrimitive | None = None,
        _http: httpx.AsyncClient | None = None,
    ) -> None:
        super().__init__(name="DevelopmentCycle")
        self._bank_id = bank_id
        self._agent_hint = agent_hint
        self._memory = _memory or AgentMemory(bank_id=bank_id, base_url=base_url, timeout=timeout)
        self._graph = _graph or CodeGraphPrimitive()
        self._executor = _executor or CodeExecutionPrimitive()
        self._http = _http or httpx.AsyncClient(timeout=timeout)
        self._dc_tracer = self._tracer  # separate ref; tests set _tracer=None, _dc_tracer=mock

    async def _execute_impl(
        self, task: DevelopmentTask, context: WorkflowContext
    ) -> DevelopmentResult:
        instruction = task.get("instruction", "")
        if not instruction:
            raise ValueError("instruction must not be empty")

        target_files = task.get("target_files", [])[:3]
        agent_hint = task.get("agent_hint", self._agent_hint)

        # Steps implemented in subsequent tasks
        raise NotImplementedError
```

- [ ] **Step 4: Run to confirm construction + ValueError tests pass**
```bash
uv run python -m pytest tests/workflows/test_development_cycle.py::TestDevelopmentCycleConstruction tests/workflows/test_development_cycle.py::TestDevelopmentCycleValidation -v
```
Expected: construction tests `PASSED`, ValueError tests `PASSED` (ValueError is raised before `NotImplementedError`)

- [ ] **Step 5: Commit**
```bash
git add ttadev/workflows/development_cycle.py tests/workflows/test_development_cycle.py
git commit -m "feat(dev-cycle): add DevelopmentTask, DevelopmentResult types and class skeleton"
```

---

## Task 3: Orient + Recall steps

**Files:**
- Modify: `ttadev/workflows/development_cycle.py` (implement `_orient`, `_recall`, begin `_execute_impl`)
- Modify: `tests/workflows/test_development_cycle.py` (add orient + recall tests)

- [ ] **Step 1: Add failing tests**

Add to `tests/workflows/test_development_cycle.py`:

```python
class TestDevelopmentCycleOrient:
    @pytest.mark.asyncio
    async def test_orient_runs_code_graph_when_target_files_given(self) -> None:
        from ttadev.primitives.core.base import WorkflowContext
        from ttadev.workflows.development_cycle import DevelopmentCycle, DevelopmentTask

        report = ImpactReport(
            target="retry.py",
            callers=["test_retry.py"],
            dependencies=[],
            related_tests=["tests/test_retry.py"],
            complexity=3.0,
            risk="low",
            summary="retry.py: risk=low",
            cgc_available=True,
        )
        mock_memory, mock_graph, mock_executor, mock_http = _make_mocks(
            impact_report=report, llm_response="Here is the plan."
        )
        cycle = DevelopmentCycle(
            bank_id="tta-dev",
            _memory=mock_memory,
            _graph=mock_graph,
            _executor=mock_executor,
            _http=mock_http,
        )
        result = await cycle.execute(
            DevelopmentTask(instruction="Add timeout to retry", target_files=["retry.py"]),
            WorkflowContext(),
        )
        mock_graph.execute.assert_called_once()
        assert result["impact_report"]["target"] == "retry.py"
        assert result["impact_report"]["cgc_available"] is True

    @pytest.mark.asyncio
    async def test_orient_skips_code_graph_when_no_target_files(self) -> None:
        from ttadev.primitives.core.base import WorkflowContext
        from ttadev.workflows.development_cycle import DevelopmentCycle, DevelopmentTask

        mock_memory, mock_graph, mock_executor, mock_http = _make_mocks(
            llm_response="Here is the plan."
        )
        cycle = DevelopmentCycle(
            bank_id="tta-dev",
            _memory=mock_memory,
            _graph=mock_graph,
            _executor=mock_executor,
            _http=mock_http,
        )
        result = await cycle.execute(
            DevelopmentTask(instruction="Refactor cache"),
            WorkflowContext(),
        )
        mock_graph.execute.assert_not_called()
        assert result["impact_report"]["cgc_available"] is False

    @pytest.mark.asyncio
    async def test_orient_caps_target_files_at_three(self) -> None:
        from ttadev.primitives.core.base import WorkflowContext
        from ttadev.workflows.development_cycle import DevelopmentCycle, DevelopmentTask

        mock_memory, mock_graph, mock_executor, mock_http = _make_mocks(
            llm_response="Done."
        )
        cycle = DevelopmentCycle(
            bank_id="tta-dev",
            _memory=mock_memory,
            _graph=mock_graph,
            _executor=mock_executor,
            _http=mock_http,
        )
        await cycle.execute(
            DevelopmentTask(
                instruction="Big refactor",
                target_files=["a.py", "b.py", "c.py", "d.py", "e.py"],
            ),
            WorkflowContext(),
        )
        # Only first target used in CGC query (first of capped 3)
        call_args = mock_graph.execute.call_args
        query = call_args.args[0]
        assert query["target"] == "a.py"


class TestDevelopmentCycleRecall:
    @pytest.mark.asyncio
    async def test_recall_injects_context_prefix(self) -> None:
        from ttadev.primitives.core.base import WorkflowContext
        from ttadev.workflows.development_cycle import DevelopmentCycle, DevelopmentTask

        mock_memory, mock_graph, mock_executor, mock_http = _make_mocks(
            context_prefix="## Directives\n- Always orient first",
            llm_response="Implementation here.",
        )
        cycle = DevelopmentCycle(
            bank_id="tta-dev",
            _memory=mock_memory,
            _graph=mock_graph,
            _executor=mock_executor,
            _http=mock_http,
        )
        result = await cycle.execute(
            DevelopmentTask(instruction="Add timeout parameter"),
            WorkflowContext(),
        )
        mock_memory.build_context_prefix.assert_called_once_with("Add timeout parameter")
        assert result["context_prefix"] == "## Directives\n- Always orient first"

    @pytest.mark.asyncio
    async def test_recall_returns_empty_when_hindsight_unavailable(self) -> None:
        from ttadev.primitives.core.base import WorkflowContext
        from ttadev.workflows.development_cycle import DevelopmentCycle, DevelopmentTask

        mock_memory, mock_graph, mock_executor, mock_http = _make_mocks(
            context_prefix="", llm_response="Implementation."
        )
        cycle = DevelopmentCycle(
            bank_id="tta-dev",
            _memory=mock_memory,
            _graph=mock_graph,
            _executor=mock_executor,
            _http=mock_http,
        )
        result = await cycle.execute(
            DevelopmentTask(instruction="Fix cache bug"),
            WorkflowContext(),
        )
        assert result["context_prefix"] == ""
```

- [ ] **Step 2: Run to confirm they fail**
```bash
uv run python -m pytest tests/workflows/test_development_cycle.py -k "Orient or Recall" -v
```
Expected: `NotImplementedError` (from skeleton)

- [ ] **Step 3: Implement `_orient`, `_recall`, and begin `_execute_impl`**

Replace `_execute_impl` and add private methods in `development_cycle.py`:

```python
    async def _execute_impl(
        self, task: DevelopmentTask, context: WorkflowContext
    ) -> DevelopmentResult:
        instruction = task.get("instruction", "")
        if not instruction:
            raise ValueError("instruction must not be empty")

        target_files = list(task.get("target_files") or [])[:3]
        agent_hint = task.get("agent_hint") or self._agent_hint

        # Step 1 — Orient
        impact_report = await self._orient(target_files, context)

        # Step 2 — Recall
        context_prefix = await self._recall(instruction)

        # Step 3 — Write (implemented in Task 4)
        response = await self._write(instruction, agent_hint, context_prefix)

        # Step 4 — Validate (implemented in Task 4)
        validated = await self._validate(impact_report, context)

        # Step 5 — Retain (implemented in Task 4)
        memories_retained = await self._retain(instruction, response)

        return DevelopmentResult(
            response=response,
            validated=validated,
            impact_report=impact_report,
            memories_retained=memories_retained,
            context_prefix=context_prefix,
        )

    async def _orient(
        self, target_files: list[str], context: WorkflowContext
    ) -> ImpactReport:
        """Step 1 — Orient: query CGC for impact analysis."""
        span_cm: Any = (
            self._dc_tracer.start_as_current_span("development_cycle.orient")
            if self._dc_tracer
            else nullcontext()
        )
        with span_cm as span:
            if not target_files:
                report = _empty_impact_report()
                if span is not None:
                    span.set_attribute("cgc_available", False)
                    span.set_attribute("target_files", [])
                return report

            query = CodeGraphQuery(
                target=target_files[0],
                operations=[CGCOp.find_code, CGCOp.get_relationships, CGCOp.find_tests],
            )
            # CodeGraphPrimitive degrades gracefully — never raises
            report = await self._graph.execute(query, context)

            if span is not None:
                span.set_attribute("cgc_available", report.get("cgc_available", False))
                span.set_attribute("target_files", target_files)
                span.set_attribute("risk", report.get("risk", "low"))
            return report

    async def _recall(self, instruction: str) -> str:
        """Step 2 — Recall: build context prefix from Hindsight."""
        span_cm: Any = (
            self._dc_tracer.start_as_current_span("development_cycle.recall")
            if self._dc_tracer
            else nullcontext()
        )
        with span_cm as span:
            prefix = await self._memory.build_context_prefix(instruction)
            if span is not None:
                span.set_attribute("context_chars", len(prefix))
                span.set_attribute("hindsight_available", bool(prefix))
            return prefix

    async def _write(
        self, instruction: str, agent_hint: str, context_prefix: str
    ) -> str:
        """Step 3 — Write: LLM call with system prompt + instruction."""
        raise NotImplementedError  # implemented in Task 4

    async def _validate(
        self, impact_report: ImpactReport, context: WorkflowContext
    ) -> bool:
        """Step 4 — Validate: run related tests in E2B."""
        raise NotImplementedError  # implemented in Task 4

    async def _retain(self, instruction: str, response: str) -> int:
        """Step 5 — Retain: store memory in Hindsight."""
        raise NotImplementedError  # implemented in Task 4
```

- [ ] **Step 4: Run to confirm orient + recall tests pass**
```bash
uv run python -m pytest tests/workflows/test_development_cycle.py -k "Orient or Recall or Construction or Validation" -v
```
Expected: all `PASSED`

- [ ] **Step 5: Commit**
```bash
git add ttadev/workflows/development_cycle.py tests/workflows/test_development_cycle.py
git commit -m "feat(dev-cycle): implement Orient and Recall steps"
```

---

## Task 4: Write + Validate + Retain steps

**Files:**
- Modify: `ttadev/workflows/development_cycle.py` (implement `_write`, `_validate`, `_retain`)
- Modify: `tests/workflows/test_development_cycle.py` (add write/validate/retain/integration tests)

- [ ] **Step 1: Add failing tests**

Add to `tests/workflows/test_development_cycle.py`:

```python
class TestDevelopmentCycleWrite:
    @pytest.mark.asyncio
    async def test_write_calls_llm_with_instruction(self) -> None:
        from ttadev.primitives.core.base import WorkflowContext
        from ttadev.workflows.development_cycle import DevelopmentCycle, DevelopmentTask

        mock_memory, mock_graph, mock_executor, mock_http = _make_mocks(
            llm_response="Here is the implementation."
        )
        cycle = DevelopmentCycle(
            bank_id="tta-dev",
            _memory=mock_memory,
            _graph=mock_graph,
            _executor=mock_executor,
            _http=mock_http,
        )
        result = await cycle.execute(
            DevelopmentTask(instruction="Add timeout parameter"),
            WorkflowContext(),
        )
        mock_http.post.assert_called_once()
        call_kwargs = mock_http.post.call_args
        body = call_kwargs.kwargs.get("json", {})
        messages = body.get("messages", [])
        assert any(m["role"] == "user" and "Add timeout parameter" in m["content"] for m in messages)
        assert result["response"] == "Here is the implementation."

    @pytest.mark.asyncio
    async def test_write_includes_persona_in_system_prompt(self) -> None:
        from ttadev.primitives.core.base import WorkflowContext
        from ttadev.workflows.development_cycle import DevelopmentCycle, DevelopmentTask

        mock_memory, mock_graph, mock_executor, mock_http = _make_mocks(
            llm_response="Security review done."
        )
        cycle = DevelopmentCycle(
            bank_id="tta-dev",
            _memory=mock_memory,
            _graph=mock_graph,
            _executor=mock_executor,
            _http=mock_http,
        )
        await cycle.execute(
            DevelopmentTask(instruction="Review for vulns", agent_hint="security"),
            WorkflowContext(),
        )
        body = mock_http.post.call_args.kwargs.get("json", {})
        messages = body.get("messages", [])
        sys_msg = next(m["content"] for m in messages if m["role"] == "system")
        assert "security" in sys_msg.lower()

    @pytest.mark.asyncio
    async def test_write_raises_on_empty_llm_response(self) -> None:
        from ttadev.primitives.core.base import WorkflowContext
        from ttadev.workflows.development_cycle import DevelopmentCycle, DevelopmentTask

        mock_memory, mock_graph, mock_executor, mock_http = _make_mocks(llm_response="")
        cycle = DevelopmentCycle(
            bank_id="tta-dev",
            _memory=mock_memory,
            _graph=mock_graph,
            _executor=mock_executor,
            _http=mock_http,
        )
        with pytest.raises(ValueError, match="LLM returned empty response"):
            await cycle.execute(
                DevelopmentTask(instruction="Explain the cache primitive"),
                WorkflowContext(),
            )

    @pytest.mark.asyncio
    async def test_write_context_prefix_in_system_prompt(self) -> None:
        from ttadev.primitives.core.base import WorkflowContext
        from ttadev.workflows.development_cycle import DevelopmentCycle, DevelopmentTask

        mock_memory, mock_graph, mock_executor, mock_http = _make_mocks(
            context_prefix="## Directives\n- Use uv",
            llm_response="Done.",
        )
        cycle = DevelopmentCycle(
            bank_id="tta-dev",
            _memory=mock_memory,
            _graph=mock_graph,
            _executor=mock_executor,
            _http=mock_http,
        )
        await cycle.execute(
            DevelopmentTask(instruction="Add feature"),
            WorkflowContext(),
        )
        body = mock_http.post.call_args.kwargs.get("json", {})
        messages = body.get("messages", [])
        sys_msg = next(m["content"] for m in messages if m["role"] == "system")
        assert "Use uv" in sys_msg


class TestDevelopmentCycleValidate:
    @pytest.mark.asyncio
    async def test_validate_returns_true_when_tests_pass(self) -> None:
        from ttadev.primitives.core.base import WorkflowContext
        from ttadev.workflows.development_cycle import DevelopmentCycle, DevelopmentTask

        report = ImpactReport(
            target="retry.py", callers=[], dependencies=[],
            related_tests=["tests/test_retry.py"],
            complexity=2.0, risk="low", summary="", cgc_available=True,
        )
        mock_memory, mock_graph, mock_executor, mock_http = _make_mocks(
            impact_report=report, validate_success=True, llm_response="Done."
        )
        cycle = DevelopmentCycle(
            bank_id="tta-dev",
            _memory=mock_memory,
            _graph=mock_graph,
            _executor=mock_executor,
            _http=mock_http,
        )
        result = await cycle.execute(
            DevelopmentTask(instruction="Add timeout", target_files=["retry.py"]),
            WorkflowContext(),
        )
        assert result["validated"] is True
        mock_executor.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_validate_returns_false_when_no_related_tests(self) -> None:
        from ttadev.primitives.core.base import WorkflowContext
        from ttadev.workflows.development_cycle import DevelopmentCycle, DevelopmentTask

        mock_memory, mock_graph, mock_executor, mock_http = _make_mocks(
            llm_response="Done."
        )
        cycle = DevelopmentCycle(
            bank_id="tta-dev",
            _memory=mock_memory,
            _graph=mock_graph,
            _executor=mock_executor,
            _http=mock_http,
        )
        result = await cycle.execute(
            DevelopmentTask(instruction="Update README"),
            WorkflowContext(),
        )
        assert result["validated"] is False
        mock_executor.execute.assert_not_called()

    @pytest.mark.asyncio
    async def test_validate_returns_false_when_e2b_errors(self) -> None:
        from ttadev.primitives.core.base import WorkflowContext
        from ttadev.workflows.development_cycle import DevelopmentCycle, DevelopmentTask

        report = ImpactReport(
            target="retry.py", callers=[], dependencies=[],
            related_tests=["tests/test_retry.py"],
            complexity=2.0, risk="low", summary="", cgc_available=True,
        )
        mock_memory, mock_graph, mock_executor, mock_http = _make_mocks(
            impact_report=report, llm_response="Done."
        )
        mock_executor.execute = AsyncMock(side_effect=Exception("E2B unavailable"))
        cycle = DevelopmentCycle(
            bank_id="tta-dev",
            _memory=mock_memory,
            _graph=mock_graph,
            _executor=mock_executor,
            _http=mock_http,
        )
        result = await cycle.execute(
            DevelopmentTask(instruction="Add timeout", target_files=["retry.py"]),
            WorkflowContext(),
        )
        assert result["validated"] is False


class TestDevelopmentCycleRetain:
    @pytest.mark.asyncio
    async def test_retain_stores_memory_and_returns_one(self) -> None:
        from ttadev.primitives.core.base import WorkflowContext
        from ttadev.workflows.development_cycle import DevelopmentCycle, DevelopmentTask

        mock_memory, mock_graph, mock_executor, mock_http = _make_mocks(
            retain_success=True, llm_response="Here is the output."
        )
        cycle = DevelopmentCycle(
            bank_id="tta-dev",
            _memory=mock_memory,
            _graph=mock_graph,
            _executor=mock_executor,
            _http=mock_http,
        )
        result = await cycle.execute(
            DevelopmentTask(instruction="Add timeout parameter"),
            WorkflowContext(),
        )
        mock_memory.retain.assert_called_once()
        assert result["memories_retained"] == 1

    @pytest.mark.asyncio
    async def test_retain_returns_zero_when_hindsight_unavailable(self) -> None:
        from ttadev.primitives.core.base import WorkflowContext
        from ttadev.workflows.development_cycle import DevelopmentCycle, DevelopmentTask

        mock_memory, mock_graph, mock_executor, mock_http = _make_mocks(
            retain_success=False, llm_response="Output."
        )
        cycle = DevelopmentCycle(
            bank_id="tta-dev",
            _memory=mock_memory,
            _graph=mock_graph,
            _executor=mock_executor,
            _http=mock_http,
        )
        result = await cycle.execute(
            DevelopmentTask(instruction="Fix bug"),
            WorkflowContext(),
        )
        assert result["memories_retained"] == 0


class TestDevelopmentCycleIntegration:
    @pytest.mark.asyncio
    async def test_full_cycle_returns_complete_result(self) -> None:
        from ttadev.primitives.core.base import WorkflowContext
        from ttadev.workflows.development_cycle import DevelopmentCycle, DevelopmentTask

        mock_memory, mock_graph, mock_executor, mock_http = _make_mocks(
            context_prefix="## Directives\n- Use uv",
            llm_response="Here is the implementation plan.",
        )
        cycle = DevelopmentCycle(
            bank_id="tta-dev",
            _memory=mock_memory,
            _graph=mock_graph,
            _executor=mock_executor,
            _http=mock_http,
        )
        result = await cycle.execute(
            DevelopmentTask(instruction="Add timeout parameter"),
            WorkflowContext(),
        )
        assert result["response"] == "Here is the implementation plan."
        assert result["context_prefix"] == "## Directives\n- Use uv"
        assert isinstance(result["validated"], bool)
        assert isinstance(result["memories_retained"], int)

    @pytest.mark.asyncio
    async def test_agent_hint_override_per_call(self) -> None:
        from ttadev.primitives.core.base import WorkflowContext
        from ttadev.workflows.development_cycle import DevelopmentCycle, DevelopmentTask

        mock_memory, mock_graph, mock_executor, mock_http = _make_mocks(
            llm_response="QA review done."
        )
        cycle = DevelopmentCycle(
            bank_id="tta-dev",
            agent_hint="developer",  # default
            _memory=mock_memory,
            _graph=mock_graph,
            _executor=mock_executor,
            _http=mock_http,
        )
        await cycle.execute(
            DevelopmentTask(instruction="Review tests", agent_hint="qa"),  # override
            WorkflowContext(),
        )
        body = mock_http.post.call_args.kwargs.get("json", {})
        messages = body.get("messages", [])
        sys_msg = next(m["content"] for m in messages if m["role"] == "system")
        assert "QA engineer" in sys_msg


def test_exported_from_workflows_package() -> None:
    from ttadev.workflows import DevelopmentCycle, DevelopmentResult, DevelopmentTask

    assert DevelopmentCycle is not None
    assert DevelopmentTask is not None
    assert DevelopmentResult is not None
```

- [ ] **Step 2: Run to confirm they fail**
```bash
uv run python -m pytest tests/workflows/test_development_cycle.py -k "Write or Validate or Retain or Integration or exported" -v
```
Expected: `NotImplementedError` for step tests, `ImportError` for export test

- [ ] **Step 3: Implement `_write`, `_validate`, `_retain` in `development_cycle.py`**

Replace the three stub methods:

```python
    async def _write(
        self, instruction: str, agent_hint: str, context_prefix: str
    ) -> str:
        """Step 3 — Write: LLM call with system prompt + instruction."""
        span_cm: Any = (
            self._dc_tracer.start_as_current_span("development_cycle.write")
            if self._dc_tracer
            else nullcontext()
        )
        with span_cm as span:
            cfg = get_llm_client()
            system = _build_system_prompt(agent_hint, context_prefix)
            messages = [
                {"role": "system", "content": system},
                {"role": "user", "content": instruction},
            ]
            resp = await self._http.post(
                f"{cfg.base_url}/chat/completions",
                headers={"Authorization": f"Bearer {cfg.api_key}"},
                json={"model": cfg.model, "messages": messages},
            )
            resp.raise_for_status()
            data = resp.json()
            content: str = data["choices"][0]["message"]["content"] or ""
            if not content:
                raise ValueError("LLM returned empty response")
            if span is not None:
                span.set_attribute("provider", cfg.provider)
                span.set_attribute("model", cfg.model)
                span.set_attribute("response_chars", len(content))
            return content

    async def _validate(
        self, impact_report: ImpactReport, context: WorkflowContext
    ) -> bool:
        """Step 4 — Validate: run related tests in E2B sandbox."""
        span_cm: Any = (
            self._dc_tracer.start_as_current_span("development_cycle.validate")
            if self._dc_tracer
            else nullcontext()
        )
        with span_cm as span:
            tests = impact_report.get("related_tests", [])
            if not tests:
                if span is not None:
                    span.set_attribute("validated", False)
                    span.set_attribute("n_tests", 0)
                return False

            try:
                tests_repr = repr(tests)
                code = (
                    "import subprocess\n"
                    f"result = subprocess.run(\n"
                    f"    ['python', '-m', 'pytest'] + {tests_repr} + ['-x', '--tb=short'],\n"
                    f"    capture_output=True, text=True\n"
                    f")\n"
                    f"print(result.stdout)\n"
                    f"if result.returncode != 0:\n"
                    f"    print(result.stderr)\n"
                    f"    raise SystemExit(result.returncode)\n"
                )
                output = await self._executor.execute(
                    {"code": code, "language": "python"}, context
                )
                validated = output.get("success", False)
            except Exception as exc:
                logger.warning("DevelopmentCycle validate step failed: %s", exc)
                validated = False

            if span is not None:
                span.set_attribute("validated", validated)
                span.set_attribute("n_tests", len(tests))
            return validated

    async def _retain(self, instruction: str, response: str) -> int:
        """Step 5 — Retain: store a structured memory in Hindsight."""
        span_cm: Any = (
            self._dc_tracer.start_as_current_span("development_cycle.retain")
            if self._dc_tracer
            else nullcontext()
        )
        with span_cm as span:
            content = (
                f"[type: decision] {instruction[:80]} → {response[:120]}"
            )
            result = await self._memory.retain(content, async_=True)
            retained = 1 if result.get("success", False) else 0
            if span is not None:
                span.set_attribute("memories_retained", retained)
                span.set_attribute("hindsight_available", bool(retained))
            return retained
```

- [ ] **Step 4: Run all tests**
```bash
uv run python -m pytest tests/workflows/test_development_cycle.py -v -k "not exported"
```
Expected: all `PASSED`

- [ ] **Step 5: Commit**
```bash
git add ttadev/workflows/development_cycle.py tests/workflows/test_development_cycle.py
git commit -m "feat(dev-cycle): implement Write, Validate, and Retain steps"
```

---

## Task 5: Package exports and final verification

**Files:**
- Modify: `ttadev/workflows/__init__.py`

- [ ] **Step 1: Update `ttadev/workflows/__init__.py`**

Add imports and `__all__` entries:

```python
from ttadev.workflows.development_cycle import DevelopmentCycle, DevelopmentResult, DevelopmentTask
```

Add to `__all__`:
```python
    # development cycle
    "DevelopmentCycle",
    "DevelopmentTask",
    "DevelopmentResult",
```

- [ ] **Step 2: Run export test**
```bash
uv run python -m pytest tests/workflows/test_development_cycle.py::test_exported_from_workflows_package -v
```
Expected: `PASSED`

- [ ] **Step 3: Run full suite**
```bash
uv run python -m pytest tests/workflows/test_development_cycle.py -v
```
Expected: all `PASSED`

- [ ] **Step 4: Quality gate**
```bash
uv run ruff check ttadev/workflows/development_cycle.py tests/workflows/test_development_cycle.py --fix
uvx pyright ttadev/workflows/development_cycle.py
```

- [ ] **Step 5: Retain to Hindsight** (if Hindsight is running)

POST to `http://localhost:8888/v1/default/banks/tta-dev/memories`:
```json
{
  "items": [{
    "content": "[type: pattern] DevelopmentCycle Phase 3 complete. InstrumentedPrimitive in ttadev/workflows/development_cycle.py. _dc_tracer pattern for OTel in tests. Write step re-raises on failure; all others degrade. Validate uses CodeExecutionPrimitive with subprocess pytest. Retain stores '[type: decision] instruction[:80] → response[:120]'. Exported from ttadev.workflows."
  }],
  "async": true
}
```

- [ ] **Step 6: Commit and push**
```bash
git add ttadev/workflows/__init__.py
git commit -m "feat(dev-cycle): export DevelopmentCycle from ttadev.workflows"
git push origin main
```
