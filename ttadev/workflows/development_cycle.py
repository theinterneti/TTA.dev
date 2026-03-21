"""DevelopmentCycle — Orient → Recall → Write → Validate → Retain as a single primitive.

Phase 3 of the DevelopmentCycle integration design. Composes CodeGraphPrimitive,
AgentMemory, and CodeExecutionPrimitive with a free-LLM Write step into one
observable, composable InstrumentedPrimitive.
"""

from __future__ import annotations

import logging
from contextlib import nullcontext  # noqa: F401
from typing import Any, TypedDict  # noqa: F401

import httpx

from ttadev.primitives.code_graph import (
    CGCOp,  # noqa: F401
    CodeGraphPrimitive,
    CodeGraphQuery,  # noqa: F401
    ImpactReport,
)
from ttadev.primitives.core.base import WorkflowContext
from ttadev.primitives.integrations.e2b_primitive import CodeExecutionPrimitive
from ttadev.primitives.memory import AgentMemory
from ttadev.primitives.observability import InstrumentedPrimitive
from ttadev.workflows.llm_provider import get_llm_client  # noqa: F401

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

    instruction: str  # Required: what to build/analyse/review
    target_files: list[str]  # Optional: file paths/names to orient CGC on (max 3)
    agent_hint: str  # Optional: role persona ("developer", "qa", "security")


class DevelopmentResult(TypedDict):
    """Output from a DevelopmentCycle execution."""

    response: str  # LLM-generated output
    validated: bool  # True if E2B ran related tests and they passed
    impact_report: ImpactReport  # From Orient step (empty if CGC unavailable)
    memories_retained: int  # 1 if Hindsight stored the memory; 0 if unavailable
    context_prefix: str  # Memory prefix injected into the LLM system prompt


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
        self._executor: CodeExecutionPrimitive | None = (
            _executor  # lazy: instantiated on first use if None
        )
        self._http = _http or httpx.AsyncClient(timeout=timeout)
        self._dc_tracer = self._tracer  # separate ref; tests set _tracer=None, _dc_tracer=mock

    async def _execute_impl(
        self, task: DevelopmentTask, context: WorkflowContext
    ) -> DevelopmentResult:
        instruction = task.get("instruction", "")
        if not instruction:
            raise ValueError("instruction must not be empty")

        target_files = list(task.get("target_files") or [])[:3]  # noqa: F841
        agent_hint = task.get("agent_hint") or self._agent_hint  # noqa: F841

        # Steps implemented in subsequent tasks
        raise NotImplementedError
