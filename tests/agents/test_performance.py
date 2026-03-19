"""Tests for ttadev.agents.performance.PerformanceAgent — Task K6."""

import pytest

from ttadev.agents.performance import PERFORMANCE_SPEC, PerformanceAgent
from ttadev.agents.protocol import ChatMessage
from ttadev.agents.registry import get_registry
from ttadev.agents.spec import ToolRule
from ttadev.agents.task import AgentTask
from ttadev.primitives.core.base import WorkflowContext


class _MockModel:
    async def chat(
        self,
        messages: list[ChatMessage],
        system: str | None,
        ctx: WorkflowContext,
    ) -> str:
        return "Observation: p99 latency is 2s. Root Cause: N+1 query in user loader. Recommendation: add select_related()."


class TestPerformanceSpec:
    def test_name(self):
        assert PERFORMANCE_SPEC.name == "performance"

    def test_capabilities_include_profiling(self):
        assert any("profil" in c for c in PERFORMANCE_SPEC.capabilities)

    def test_py_spy_is_when_instructed(self):
        tool = next((t for t in PERFORMANCE_SPEC.tools if t.name == "py-spy"), None)
        assert tool is not None
        assert tool.rule == ToolRule.WHEN_INSTRUCTED

    def test_pytest_benchmark_is_when_instructed(self):
        tool = next((t for t in PERFORMANCE_SPEC.tools if t.name == "pytest-benchmark"), None)
        assert tool is not None
        assert tool.rule == ToolRule.WHEN_INSTRUCTED

    def test_memory_profiler_is_when_instructed(self):
        tool = next((t for t in PERFORMANCE_SPEC.tools if t.name == "memory-profiler"), None)
        assert tool is not None
        assert tool.rule == ToolRule.WHEN_INSTRUCTED

    def test_system_prompt_not_empty(self):
        assert len(PERFORMANCE_SPEC.system_prompt) > 100

    def test_system_prompt_mentions_profiling(self):
        assert "profil" in PERFORMANCE_SPEC.system_prompt.lower()

    def test_developer_handoff_trigger_fires(self):
        trigger = next(
            (t for t in PERFORMANCE_SPEC.handoff_triggers if t.target_agent == "developer"), None
        )
        assert trigger is not None
        task = AgentTask(
            instruction="refactor the hot path to reduce allocations", context={}, constraints=[]
        )
        assert trigger.condition(task) is True

    def test_developer_handoff_does_not_fire_on_normal_task(self):
        trigger = next(
            (t for t in PERFORMANCE_SPEC.handoff_triggers if t.target_agent == "developer"), None
        )
        assert trigger is not None
        task = AgentTask(
            instruction="our API p99 latency spiked to 2 seconds", context={}, constraints=[]
        )
        assert trigger.condition(task) is False

    def test_devops_handoff_trigger_fires(self):
        trigger = next(
            (t for t in PERFORMANCE_SPEC.handoff_triggers if t.target_agent == "devops"), None
        )
        assert trigger is not None
        task = AgentTask(
            instruction="we need to autoscale the kubernetes cluster", context={}, constraints=[]
        )
        assert trigger.condition(task) is True


class TestPerformanceAgent:
    def test_construction(self):
        agent = PerformanceAgent(model=_MockModel())
        assert agent.spec.name == "performance"

    def test_registered_after_import(self):
        reg = get_registry()
        assert reg.get("performance") is PerformanceAgent

    def test_class_spec_accessible_without_instantiation(self):
        assert PerformanceAgent._class_spec.name == "performance"

    @pytest.mark.asyncio
    async def test_execute_returns_result(self):
        agent = PerformanceAgent(model=_MockModel())
        task = AgentTask(
            instruction="Analyse why our API p99 latency spiked to 2 seconds",
            context={},
            constraints=[],
        )
        result = await agent.execute(task, WorkflowContext())
        assert result.agent_name == "performance"
        assert len(result.response) > 0
