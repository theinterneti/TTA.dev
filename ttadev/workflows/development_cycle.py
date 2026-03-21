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

from ttadev.primitives.code_graph import (
    CGCOp,
    CodeGraphPrimitive,
    CodeGraphQuery,
    ImpactReport,
)
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

        target_files = list(task.get("target_files") or [])[:3]
        agent_hint = task.get("agent_hint") or self._agent_hint

        # Step 1 — Orient
        impact_report = await self._orient(target_files, context)

        # Step 2 — Recall
        context_prefix = await self._recall(instruction)

        # Step 3 — Write
        response = await self._write(instruction, agent_hint, context_prefix)

        # Step 4 — Validate
        validated = await self._validate(impact_report, context)

        # Step 5 — Retain
        memories_retained = await self._retain(instruction, response)

        return DevelopmentResult(
            response=response,
            validated=validated,
            impact_report=impact_report,
            memories_retained=memories_retained,
            context_prefix=context_prefix,
        )

    async def _orient(self, target_files: list[str], context: WorkflowContext) -> ImpactReport:
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

    async def _write(self, instruction: str, agent_hint: str, context_prefix: str) -> str:
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

    async def _validate(self, impact_report: ImpactReport, context: WorkflowContext) -> bool:
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
            if self._executor is None:
                if span is not None:
                    span.set_attribute("validated", False)
                    span.set_attribute("n_tests", len(tests))
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
                output = await self._executor.execute({"code": code, "language": "python"}, context)
                validated = bool(output.get("success", False))
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
            content = f"[type: decision] {instruction[:80]} → {response[:120]}"
            result = await self._memory.retain(content, async_=True)
            retained = 1 if result.get("success", False) else 0
            if span is not None:
                span.set_attribute("memories_retained", retained)
                span.set_attribute("hindsight_available", bool(retained))
            return retained
