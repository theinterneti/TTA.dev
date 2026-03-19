"""Tests for ttadev.agents.router.AgentRouterPrimitive — Task E1."""

import pytest

from ttadev.agents.base import AgentPrimitive
from ttadev.agents.protocol import ChatMessage
from ttadev.agents.registry import AgentRegistry, override_registry
from ttadev.agents.router import AgentRouterPrimitive
from ttadev.agents.spec import AgentSpec
from ttadev.agents.task import AgentTask
from ttadev.primitives.core.base import WorkflowContext


def _make_spec(name: str, capabilities: list[str]) -> AgentSpec:
    return AgentSpec(
        name=name,
        role=name.title(),
        system_prompt=f"You are a {name}.",
        capabilities=capabilities,
        tools=[],
        quality_gates=[],
        handoff_triggers=[],
    )


class _MockOrchestrator:
    """Always picks the first agent — used for LLM fallback tests."""

    def __init__(self, pick: str):
        self._pick = pick
        self.call_count = 0

    async def chat(
        self,
        messages: list[ChatMessage],
        system: str | None,
        ctx: WorkflowContext,
    ) -> str:
        self.call_count += 1
        return self._pick


class _MockModel:
    async def chat(
        self,
        messages: list[ChatMessage],
        system: str | None,
        ctx: WorkflowContext,
    ) -> str:
        return f"done by {system or 'unknown'}"


def _make_agent_class(spec: AgentSpec) -> type[AgentPrimitive]:
    class _Agent(AgentPrimitive):
        def __init__(self):
            super().__init__(spec=spec, model=_MockModel())

    _Agent.__name__ = spec.name
    return _Agent


class TestAgentRouterPrimitive:
    def _make_registry(self) -> AgentRegistry:
        reg = AgentRegistry()
        reg.register(
            "developer",
            _make_agent_class(
                _make_spec("developer", ["code review", "debugging", "implementation"])
            ),
        )
        reg.register(
            "qa",
            _make_agent_class(_make_spec("qa", ["testing", "test coverage", "flaky tests"])),
        )
        return reg

    @pytest.mark.asyncio
    async def test_agent_hint_bypasses_scoring(self):
        reg = self._make_registry()
        orchestrator = _MockOrchestrator("qa")
        router = AgentRouterPrimitive(orchestrator=orchestrator)

        task = AgentTask(
            instruction="do something",
            context={},
            constraints=[],
            agent_hint="developer",
        )
        with override_registry(reg):
            result = await router.execute(task, WorkflowContext())

        assert result.agent_name == "developer"
        assert orchestrator.call_count == 0  # no LLM call needed

    @pytest.mark.asyncio
    async def test_keyword_routing_no_llm_call(self):
        reg = self._make_registry()
        orchestrator = _MockOrchestrator("qa")
        router = AgentRouterPrimitive(orchestrator=orchestrator)

        task = AgentTask(
            instruction="our test coverage is too low",
            context={},
            constraints=[],
        )
        with override_registry(reg):
            result = await router.execute(task, WorkflowContext())

        assert result.agent_name == "qa"
        assert orchestrator.call_count == 0

    @pytest.mark.asyncio
    async def test_ambiguous_task_calls_orchestrator(self):
        reg = self._make_registry()
        orchestrator = _MockOrchestrator("developer")
        router = AgentRouterPrimitive(orchestrator=orchestrator)

        task = AgentTask(
            instruction="help me with my project",  # no clear keywords
            context={},
            constraints=[],
        )
        with override_registry(reg):
            result = await router.execute(task, WorkflowContext())

        assert orchestrator.call_count == 1
        assert result.agent_name == "developer"

    @pytest.mark.asyncio
    async def test_unknown_hint_falls_back_to_routing(self):
        reg = self._make_registry()
        orchestrator = _MockOrchestrator("qa")
        router = AgentRouterPrimitive(orchestrator=orchestrator)

        task = AgentTask(
            instruction="fix flaky tests",
            context={},
            constraints=[],
            agent_hint="nonexistent",  # unknown agent
        )
        with override_registry(reg):
            result = await router.execute(task, WorkflowContext())

        # Falls back to keyword routing — "flaky tests" matches qa
        assert result.agent_name == "qa"
