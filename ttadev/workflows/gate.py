"""ApprovalGate — human-in-the-loop checkpoint after each workflow step."""

from __future__ import annotations

import asyncio
import sys
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


class GateDecision(StrEnum):
    CONTINUE = "continue"
    SKIP = "skip"
    EDIT = "edit"
    QUIT = "quit"


class ApprovalGate:
    """Pause between workflow steps for human review.

    Args:
        auto_approve: If True, always return CONTINUE without prompting.
    """

    def __init__(self, auto_approve: bool = False) -> None:
        self.auto_approve = auto_approve

    async def check(
        self,
        step_result: StepResult,
        total_steps: int,
        *,
        next_agent: str | None,
    ) -> tuple[GateDecision, str | None]:
        """Evaluate a completed step and return the gate decision.

        Returns:
            Tuple of (GateDecision, edited_instruction | None).
        """
        if self.auto_approve:
            return GateDecision.CONTINUE, None

        self._render(step_result, total_steps, next_agent)
        raw = await self._prompt_user(step_result, total_steps, next_agent)
        return await self._resolve(raw, step_result)

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
