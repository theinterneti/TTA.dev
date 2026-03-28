"""ApprovalGate — human-in-the-loop checkpoint after each workflow step."""

from __future__ import annotations

import asyncio
import sys
from dataclasses import dataclass
from enum import StrEnum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ttadev.workflows.definition import StepResult

_HELP_TEXT = """
  [Enter] continue to next step
  [s]     skip next step
  [e]     edit the next step's instruction
  [q]     quit the workflow
  [?]     show full step output
"""

# Sentinel confidence above any real score — used by auto_approve=True mapping.
_ALWAYS_AUTO_CONFIDENCE: float = 2.0


@dataclass
class GatePolicy:
    """Policy rules controlling when an ApprovalGate auto-approves a step.

    Attributes:
        min_confidence: Auto-approve when step confidence >= this value.
                        0.0 means never auto-approve (always prompt).
                        Values > 1.0 always auto-approve (use auto_approve=True instead).
        require_quality_gates: When True, block auto-approval if
                               quality_gates_passed is False, even when confidence
                               meets the threshold.
        always_manual: Hard override — always prompt the user regardless of
                       confidence or quality gates.
    """

    min_confidence: float = 0.0
    require_quality_gates: bool = True
    always_manual: bool = False


class GateDecision(StrEnum):
    CONTINUE = "continue"
    SKIP = "skip"
    EDIT = "edit"
    QUIT = "quit"


class ApprovalGate:
    """Pause between workflow steps for human review.

    Args:
        auto_approve: If True, always return CONTINUE without prompting.
                      Equivalent to GatePolicy(min_confidence=2.0,
                      require_quality_gates=False).
        policy: Default GatePolicy for this gate instance.  Overridden
                per-call by the ``policy`` argument to ``check()``.
    """

    def __init__(
        self,
        auto_approve: bool = False,
        policy: GatePolicy | None = None,
    ) -> None:
        if policy is not None:
            self._policy = policy
        elif auto_approve:
            self._policy = GatePolicy(
                min_confidence=_ALWAYS_AUTO_CONFIDENCE,
                require_quality_gates=False,
            )
        else:
            self._policy = GatePolicy()

    async def check(
        self,
        step_result: StepResult,
        total_steps: int,
        *,
        next_agent: str | None,
        policy: GatePolicy | None = None,
    ) -> tuple[GateDecision, str | None, str | None]:
        """Evaluate a completed step and return the gate decision.

        Args:
            step_result:  The completed step's result.
            total_steps:  Total number of steps in the workflow.
            next_agent:   Name of the next agent (for display).
            policy:       Per-call policy override.  Falls back to the
                          instance-level policy when None.

        Returns:
            Tuple of (GateDecision, edited_instruction | None, policy_name | None).
            ``policy_name`` is a non-None string when the decision was made
            automatically by policy (e.g. ``"auto:confidence≥0.85"``), and
            ``None`` when a human made the decision.
        """
        effective = policy if policy is not None else self._policy

        # --- policy-driven auto-approval path ---
        if not effective.always_manual:
            # Sentinel: min_confidence >= _ALWAYS_AUTO_CONFIDENCE means unconditional auto.
            if effective.min_confidence >= _ALWAYS_AUTO_CONFIDENCE:
                return GateDecision.CONTINUE, None, "auto:always"

            if effective.min_confidence > 0.0:
                qg_ok = (
                    not effective.require_quality_gates
                ) or step_result.result.quality_gates_passed
                if step_result.result.confidence >= effective.min_confidence and qg_ok:
                    policy_name = f"auto:confidence≥{effective.min_confidence}"
                    return GateDecision.CONTINUE, None, policy_name

        # --- human prompt path ---
        self._render(step_result, total_steps, next_agent, effective)
        raw = await self._prompt_user(step_result, total_steps, next_agent)
        decision, edited = await self._resolve(raw, step_result)
        return decision, edited, None

    async def _resolve(self, raw: str, step_result: StepResult) -> tuple[GateDecision, str | None]:
        choice = raw.strip().lower()

        if choice in ("", "c"):
            return GateDecision.CONTINUE, None
        if choice == "s":
            return GateDecision.SKIP, None
        if choice == "q":
            return GateDecision.QUIT, None
        if choice == "e":
            edited = await self._prompt_edit(step_result.result.response)
            return GateDecision.EDIT, edited
        if choice == "?":
            print(step_result.result.response)
            raw2 = await self._prompt_user(step_result, 0, None)
            return await self._resolve(raw2, step_result)

        return GateDecision.CONTINUE, None

    def _render(
        self,
        step_result: StepResult,
        total_steps: int,
        next_agent: str | None,
        policy: GatePolicy,
    ) -> None:
        i = step_result.step_index + 1
        confidence_pct = int(step_result.result.confidence * 100)
        gate_status = "✓" if step_result.result.quality_gates_passed else "✗"
        preview = step_result.result.response[:500]
        if len(step_result.result.response) > 500:
            preview += "\n  ..."

        sep = "─" * 54
        print(f"\n{sep}")
        print(f"  Step {i}/{total_steps} complete: {step_result.agent_name}")
        print(f"  Confidence: {confidence_pct}%  |  Quality gates: {gate_status}")
        if policy.min_confidence > 0.0 and not step_result.result.quality_gates_passed:
            print(
                f"  ⚠  Quality gates failed — auto-approve blocked (policy threshold {policy.min_confidence})"
            )
        print(sep)
        print(f"  {preview}")
        print(sep)
        if next_agent:
            print(f"  Next step: {next_agent}")
        print("  [Enter] continue   [s] skip   [e] edit   [q] quit   [?] full output")

    async def _prompt_user(
        self,
        step_result: StepResult,
        total_steps: int,
        next_agent: str | None,
    ) -> str:
        if not sys.stdin.isatty():
            import logging

            logging.getLogger(__name__).warning(
                "ApprovalGate: non-TTY stdin — auto-approving step %d",
                step_result.step_index,
            )
            return ""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, lambda: input("> ").strip())

    async def _prompt_edit(self, original: str) -> str:
        print(f"  Current instruction preview: {original[:200]}")
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, lambda: input("  New instruction> ").strip())
