"""Tests for WorkflowContext.spawn_agent() — Task F1."""

import pytest

from ttadev.agents.base import AgentPrimitive
from ttadev.agents.protocol import ChatMessage
from ttadev.agents.registry import AgentRegistry, override_registry
from ttadev.agents.spec import AgentSpec
from ttadev.agents.task import AgentResult, AgentTask
from ttadev.primitives.core.base import WorkflowContext


def _make_spec(name: str) -> AgentSpec:
    return AgentSpec(
        name=name,
        role=name.title(),
        system_prompt=f"You are {name}.",
        capabilities=[name],
        tools=[],
        quality_gates=[],
        handoff_triggers=[],
    )


class _MockModel:
    async def chat(
        self,
        messages: list[ChatMessage],
        system: str | None,
        ctx: WorkflowContext,
    ) -> str:
        return f"response from {system}"


def _make_agent_class(name: str) -> type[AgentPrimitive]:
    spec = _make_spec(name)

    class _Agent(AgentPrimitive):
        def __init__(self):
            super().__init__(spec=spec, model=_MockModel())

    _Agent.__name__ = name
    return _Agent


class TestSpawnAgent:
    @pytest.mark.asyncio
    async def test_spawn_agent_returns_result(self):
        reg = AgentRegistry()
        reg.register("helper", _make_agent_class("helper"))

        ctx = WorkflowContext(workflow_id="test-workflow")
        task = AgentTask(instruction="help me", context={}, constraints=[])

        with override_registry(reg):
            result = await ctx.spawn_agent("helper", task)

        assert isinstance(result, AgentResult)
        assert result.agent_name == "helper"

    @pytest.mark.asyncio
    async def test_spawn_agent_unknown_name_raises(self):
        reg = AgentRegistry()
        ctx = WorkflowContext()
        task = AgentTask(instruction="x", context={}, constraints=[])

        with override_registry(reg), pytest.raises(KeyError, match="nonexistent"):
            await ctx.spawn_agent("nonexistent", task)

    @pytest.mark.asyncio
    async def test_spawn_agent_without_workflow_context(self):
        """spawn_agent works on a bare WorkflowContext — no workflow setup needed."""
        reg = AgentRegistry()
        reg.register("helper", _make_agent_class("helper"))

        ctx = WorkflowContext()  # no workflow_id
        task = AgentTask(instruction="help", context={}, constraints=[])

        with override_registry(reg):
            result = await ctx.spawn_agent("helper", task)

        assert result.agent_name == "helper"
