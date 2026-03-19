"""Tests for ttadev.agents.base.AgentPrimitive — Task C2."""

import pytest

from ttadev.agents.base import AgentPrimitive, QualityGateError
from ttadev.agents.protocol import ChatMessage
from ttadev.agents.registry import AgentRegistry, override_registry
from ttadev.agents.spec import AgentSpec, HandoffTrigger, QualityGate
from ttadev.agents.task import AgentResult, AgentTask
from ttadev.primitives.core.base import WorkflowContext


def _make_spec(**kwargs) -> AgentSpec:
    defaults = dict(
        name="test",
        role="Test Agent",
        system_prompt="You are helpful.",
        capabilities=["testing"],
        tools=[],
        quality_gates=[],
        handoff_triggers=[],
    )
    defaults.update(kwargs)
    return AgentSpec(**defaults)


class _MockModel:
    def __init__(self, response: str = "looks good"):
        self._response = response

    async def chat(
        self,
        messages: list[ChatMessage],
        system: str | None,
        ctx: WorkflowContext,
    ) -> str:
        return self._response


class TestAgentPrimitive:
    @pytest.mark.asyncio
    async def test_execute_returns_agent_result(self):
        spec = _make_spec()
        agent = AgentPrimitive(spec=spec, model=_MockModel())
        task = AgentTask(instruction="do something", context={}, constraints=[])
        result = await agent.execute(task, WorkflowContext())
        assert isinstance(result, AgentResult)
        assert result.agent_name == "test"
        assert result.response == "looks good"

    @pytest.mark.asyncio
    async def test_quality_gate_pass(self):
        spec = _make_spec(
            quality_gates=[QualityGate("always_pass", lambda r: True, "should not fail")]
        )
        agent = AgentPrimitive(spec=spec, model=_MockModel())
        task = AgentTask(instruction="x", context={}, constraints=[])
        result = await agent.execute(task, WorkflowContext())
        assert result.quality_gates_passed is True

    @pytest.mark.asyncio
    async def test_quality_gate_fail_raises(self):
        spec = _make_spec(
            quality_gates=[QualityGate("always_fail", lambda r: False, "gate failed")]
        )
        agent = AgentPrimitive(spec=spec, model=_MockModel())
        task = AgentTask(instruction="x", context={}, constraints=[])
        with pytest.raises(QualityGateError, match="always_fail"):
            await agent.execute(task, WorkflowContext())

    @pytest.mark.asyncio
    async def test_handoff_trigger_calls_spawn_agent(self):
        spawned: list[str] = []

        class _CtxWithSpawn(WorkflowContext):
            async def spawn_agent(self, agent_name: str, task: AgentTask) -> AgentResult:
                spawned.append(agent_name)
                return AgentResult(
                    agent_name=agent_name,
                    response="sub done",
                    artifacts=[],
                    suggestions=[],
                    spawned_agents=[],
                    quality_gates_passed=True,
                    confidence=1.0,
                )

        spec = _make_spec(
            handoff_triggers=[
                HandoffTrigger(
                    condition=lambda t: "security" in t.instruction,
                    target_agent="security",
                    reason="security task",
                )
            ]
        )
        agent = AgentPrimitive(spec=spec, model=_MockModel())
        task = AgentTask(instruction="check security vulnerabilities", context={}, constraints=[])
        result = await agent.execute(task, _CtxWithSpawn())
        assert "security" in spawned
        assert "security" in result.spawned_agents

    def test_composable_with_rshift(self):
        from ttadev.primitives.core.base import LambdaPrimitive

        spec = _make_spec()
        agent = AgentPrimitive(spec=spec, model=_MockModel())
        passthrough = LambdaPrimitive(lambda x, ctx: x)
        workflow = agent >> passthrough
        assert workflow is not None

    def test_subclass_auto_registers(self):
        test_reg = AgentRegistry()

        with override_registry(test_reg):

            class _AutoAgent(AgentPrimitive):
                _spec_name = "auto"

                def __init__(self):
                    super().__init__(spec=_make_spec(name="auto"), model=_MockModel())

            test_reg.register("auto", _AutoAgent)
            assert test_reg.get("auto") is _AutoAgent
