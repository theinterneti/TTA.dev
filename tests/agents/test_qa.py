"""Tests for ttadev.agents.qa.QAAgent — Task K1."""

import pytest

from ttadev.agents.protocol import ChatMessage
from ttadev.agents.qa import QA_SPEC, QAAgent
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
        return "The test suite has a race condition in the fixture teardown."


class TestQASpec:
    def test_name(self):
        assert QA_SPEC.name == "qa"

    def test_capabilities_include_test_writing(self):
        assert any("test" in c for c in QA_SPEC.capabilities)

    def test_pytest_is_always_tool(self):
        tool = next((t for t in QA_SPEC.tools if t.name == "pytest"), None)
        assert tool is not None
        assert tool.rule == ToolRule.ALWAYS

    def test_coverage_is_always_tool(self):
        tool = next((t for t in QA_SPEC.tools if t.name == "coverage"), None)
        assert tool is not None
        assert tool.rule == ToolRule.ALWAYS

    def test_git_is_when_instructed(self):
        tool = next((t for t in QA_SPEC.tools if t.name == "git"), None)
        assert tool is not None
        assert tool.rule == ToolRule.WHEN_INSTRUCTED

    def test_system_prompt_not_empty(self):
        assert len(QA_SPEC.system_prompt) > 100

    def test_system_prompt_mentions_pytest(self):
        assert "pytest" in QA_SPEC.system_prompt

    def test_security_handoff_trigger_fires(self):
        trigger = next((t for t in QA_SPEC.handoff_triggers if t.target_agent == "security"), None)
        assert trigger is not None
        task = AgentTask(
            instruction="check for SQL injection in the test fixtures", context={}, constraints=[]
        )
        assert trigger.condition(task) is True

    def test_security_handoff_does_not_fire_on_normal_task(self):
        trigger = next((t for t in QA_SPEC.handoff_triggers if t.target_agent == "security"), None)
        assert trigger is not None
        task = AgentTask(instruction="our test suite is flaky on CI", context={}, constraints=[])
        assert trigger.condition(task) is False

    def test_performance_handoff_trigger_fires(self):
        trigger = next(
            (t for t in QA_SPEC.handoff_triggers if t.target_agent == "performance"), None
        )
        assert trigger is not None
        task = AgentTask(instruction="the benchmark tests are too slow", context={}, constraints=[])
        assert trigger.condition(task) is True


class TestQAAgent:
    def test_construction(self):
        agent = QAAgent(model=_MockModel())
        assert agent.spec.name == "qa"

    def test_registered_after_import(self):
        reg = get_registry()
        assert reg.get("qa") is QAAgent

    def test_class_spec_accessible_without_instantiation(self):
        assert QAAgent._class_spec.name == "qa"

    @pytest.mark.asyncio
    async def test_execute_returns_result(self):
        agent = QAAgent(model=_MockModel())
        task = AgentTask(
            instruction="Diagnose flaky tests in the test suite",
            context={},
            constraints=[],
        )
        result = await agent.execute(task, WorkflowContext())
        assert result.agent_name == "qa"
        assert len(result.response) > 0
