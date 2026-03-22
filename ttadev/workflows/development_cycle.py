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
from ttadev.workflows.llm_provider import LLMClientConfig, get_llm_provider_chain
from ttadev.workflows.quality_gate import _DEFAULT_THRESHOLD, quality_gate_passed, score_response

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
    provider_chain: list[LLMClientConfig]  # Optional: per-call provider override
    quality_threshold: float  # Optional: per-call threshold override


class DevelopmentResult(TypedDict):
    """Output from a DevelopmentCycle execution."""

    response: str  # LLM-generated output
    validated: bool  # True if E2B ran related tests and they passed
    impact_report: ImpactReport  # From Orient step (empty if CGC unavailable)
    memories_retained: int  # 1 if Hindsight stored the memory; 0 if unavailable
    context_prefix: str  # Memory prefix injected into the LLM system prompt
    confidence: float  # quality gate score of accepted response (0.0–1.0)
    provider: str  # provider that produced accepted response
    retry_count: int  # number of retries attempted (0 = no retry attempted yet)


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


_REFRAME_TEMPLATE = (
    "Task: {instruction}\n\n"
    "Instructions:\n"
    "- Respond with a concrete, actionable answer\n"
    "- Be specific and direct\n"
    "- Do not refuse or hedge\n"
    "- Format: start with the implementation, then explain briefly"
)


def _reframe_instruction(instruction: str) -> str:
    """Wrap instruction in explicit structure to improve weak-model compliance."""
    return _REFRAME_TEMPLATE.format(instruction=instruction)


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

        raw_chain = task.get("provider_chain")
        if raw_chain is not None and len(raw_chain) == 0:
            raise ValueError("provider_chain must not be empty")
        raw_threshold = task.get("quality_threshold")
        if raw_threshold is not None and not (0.0 <= raw_threshold <= 1.0):
            raise ValueError("quality_threshold must be in [0.0, 1.0]")

        # Step 1 — Orient
        impact_report = await self._orient(target_files, context)

        # Step 2 — Recall
        context_prefix = await self._recall(instruction)

        # Step 3 — Write
        response, confidence, provider, retry_count = await self._write(
            instruction,
            agent_hint,
            context_prefix,
            chain=raw_chain,
            threshold=raw_threshold,
        )

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
            confidence=confidence,
            provider=provider,
            retry_count=retry_count,
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

    async def _call_llm(self, cfg: LLMClientConfig, system: str, instruction: str) -> str:
        """Make one LLM API call. Returns content string. Raises on HTTP error."""
        resp = await self._http.post(
            f"{cfg.base_url}/chat/completions",
            headers={"Authorization": f"Bearer {cfg.api_key}"},
            json={
                "model": cfg.model,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": instruction},
                ],
            },
        )
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"] or ""

    async def _run_chain_pass(
        self,
        chain: list[LLMClientConfig],
        system: str,
        instruction: str,
        threshold: float,
    ) -> tuple[str, float, str, Exception | None, int]:
        """Run one full pass through the provider chain.

        Returns (best_response, best_score, best_provider, last_exc, attempts).
        best_response is "" if all providers raised.
        """
        best_response: str = ""
        best_score: float = 0.0
        best_provider: str = chain[0].provider
        last_exc: Exception | None = None
        attempts: int = 0

        for cfg in chain:
            attempts += 1
            try:
                content = await self._call_llm(cfg, system, instruction)
            except Exception as exc:
                logger.warning("DevelopmentCycle write: %s failed: %s", cfg.provider, exc)
                last_exc = exc
                continue
            score = score_response(content)
            if score > best_score or not best_response:
                best_response, best_score, best_provider = content, score, cfg.provider
            if quality_gate_passed(content, threshold):
                break
            logger.warning(
                "DevelopmentCycle write: %s quality gate failed (score=%.2f), trying fallback",
                cfg.provider,
                score,
            )

        return best_response, best_score, best_provider, last_exc, attempts

    async def _write(
        self,
        instruction: str,
        agent_hint: str,
        context_prefix: str,
        *,
        chain: list[LLMClientConfig] | None = None,
        threshold: float | None = None,
    ) -> tuple[str, float, str, int]:
        """Step 3 — Write: try each provider in chain, return (response, confidence, provider, retry_count).

        Iterates provider chain (per-call override or default from get_llm_provider_chain()).
        Accepts first response passing quality gate.
        If pass 1 fails the gate: reframes instruction and retries (pass 2).
        If all fail the gate: returns best available (highest score).
        If all providers raise: re-raises last exception.
        """
        span_cm: Any = (
            self._dc_tracer.start_as_current_span("development_cycle.write")
            if self._dc_tracer
            else nullcontext()
        )
        with span_cm as span:
            system = _build_system_prompt(agent_hint, context_prefix)
            effective_chain = chain if chain is not None else get_llm_provider_chain()
            effective_threshold = threshold if threshold is not None else _DEFAULT_THRESHOLD

            # Pass 1 — original instruction
            (
                best_response,
                best_score,
                best_provider,
                last_exc,
                attempts,
            ) = await self._run_chain_pass(
                effective_chain, system, instruction, effective_threshold
            )

            retry_count: int = 0

            # Reframe if pass 1 failed quality gate
            if best_response and not quality_gate_passed(best_response, effective_threshold):
                logger.info("DevelopmentCycle write: reframing instruction for retry")
                reframed = _reframe_instruction(instruction)
                (
                    retry_response,
                    retry_score,
                    retry_provider,
                    retry_exc,
                    _,
                ) = await self._run_chain_pass(
                    effective_chain, system, reframed, effective_threshold
                )
                retry_count = 1
                # Keep best across both passes
                if retry_score > best_score:
                    best_response, best_score, best_provider = (
                        retry_response,
                        retry_score,
                        retry_provider,
                    )
                elif not best_response and retry_response:
                    best_response, best_score, best_provider = (
                        retry_response,
                        retry_score,
                        retry_provider,
                    )
                # Also propagate last_exc from reframe for error path
                if not best_response and retry_exc is not None:
                    last_exc = retry_exc

            if not best_response:
                # All providers raised exceptions across all passes
                if last_exc is not None:
                    raise last_exc
                raise RuntimeError("LLM provider chain returned no response")

            if not quality_gate_passed(best_response, effective_threshold):
                logger.warning(
                    "DevelopmentCycle write: all providers below threshold (best=%.2f)", best_score
                )

            if span is not None:
                span.set_attribute("model", "unknown")  # model is on cfg, not tracked here
                span.set_attribute("response_chars", len(best_response))
                span.set_attribute("write.confidence", best_score)
                span.set_attribute("write.provider", best_provider)
                span.set_attribute("write.fallback_attempts", attempts)
                span.set_attribute("write.retry_count", retry_count)
                span.set_attribute("write.reframe_triggered", retry_count > 0)
                span.set_attribute("write.final_confidence", best_score)

            return best_response, best_score, best_provider, retry_count

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
