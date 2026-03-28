"""Tests for ApprovalGate — Task T6."""

import pytest

from ttadev.agents.task import AgentResult
from ttadev.workflows.definition import StepResult
from ttadev.workflows.gate import ApprovalGate, GateDecision


def _step_result(index: int = 0, agent: str = "developer") -> StepResult:
    result = AgentResult(
        agent_name=agent,
        response="All done.",
        artifacts=[],
        suggestions=[],
        spawned_agents=[],
        quality_gates_passed=True,
        confidence=0.9,
    )
    return StepResult(step_index=index, agent_name=agent, result=result)


class TestAutoApprove:
    @pytest.mark.asyncio
    async def test_auto_approve_returns_continue(self):
        gate = ApprovalGate(auto_approve=True)
        decision, edit, _policy = await gate.check(_step_result(), total_steps=3, next_agent="qa")
        assert decision == GateDecision.CONTINUE
        assert edit is None

    @pytest.mark.asyncio
    async def test_auto_approve_no_io(self, monkeypatch):
        """auto_approve must not touch stdin."""
        monkeypatch.delattr("builtins.input", raising=False)
        gate = ApprovalGate(auto_approve=True)
        decision, _, _policy = await gate.check(_step_result(), total_steps=1, next_agent=None)
        assert decision == GateDecision.CONTINUE


class TestNonTTY:
    @pytest.mark.asyncio
    async def test_non_tty_auto_approves(self, monkeypatch):
        monkeypatch.setattr("sys.stdin.isatty", lambda: False)
        gate = ApprovalGate(auto_approve=False)
        decision, edit, _policy = await gate.check(_step_result(), total_steps=2, next_agent="qa")
        assert decision == GateDecision.CONTINUE
        assert edit is None


class TestSubclassOverride:
    """Subclass _prompt_user to inject inputs without touching stdin."""

    def _make_gate(self, response: str) -> ApprovalGate:
        class _FakeGate(ApprovalGate):
            async def _prompt_user(self, step_result, total_steps, next_agent):  # type: ignore[override]
                return response

        return _FakeGate(auto_approve=False)

    @pytest.mark.asyncio
    async def test_enter_returns_continue(self):
        gate = self._make_gate("")
        decision, edit, _policy = await gate.check(_step_result(), total_steps=3, next_agent="qa")
        assert decision == GateDecision.CONTINUE

    @pytest.mark.asyncio
    async def test_s_returns_skip(self):
        gate = self._make_gate("s")
        decision, edit, _policy = await gate.check(_step_result(), total_steps=3, next_agent="qa")
        assert decision == GateDecision.SKIP
        assert edit is None

    @pytest.mark.asyncio
    async def test_q_returns_quit(self):
        gate = self._make_gate("q")
        decision, edit, _policy = await gate.check(_step_result(), total_steps=3, next_agent="qa")
        assert decision == GateDecision.QUIT

    @pytest.mark.asyncio
    async def test_e_with_instruction_returns_edit(self):
        class _EditGate(ApprovalGate):
            async def _prompt_user(self, step_result, total_steps, next_agent):  # type: ignore[override]
                return "e"

            async def _prompt_edit(self, original: str) -> str:  # type: ignore[override]
                return "revised instruction"

        gate = _EditGate(auto_approve=False)
        decision, edit, _policy = await gate.check(_step_result(), total_steps=3, next_agent="qa")
        assert decision == GateDecision.EDIT
        assert edit == "revised instruction"
