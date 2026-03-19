"""Tests for ttadev.agents.developer.DeveloperAgent — Task D1."""

import pytest

from ttadev.agents.developer import DEVELOPER_SPEC, DeveloperAgent
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
        return "Code looks good. No issues found."


class TestDeveloperSpec:
    def test_name(self):
        assert DEVELOPER_SPEC.name == "developer"

    def test_capabilities_include_review(self):
        assert any("review" in c for c in DEVELOPER_SPEC.capabilities)

    def test_ruff_is_always_tool(self):
        ruff = next((t for t in DEVELOPER_SPEC.tools if t.name == "ruff"), None)
        assert ruff is not None
        assert ruff.rule == ToolRule.ALWAYS

    def test_pyright_is_always_tool(self):
        pyright = next((t for t in DEVELOPER_SPEC.tools if t.name == "pyright"), None)
        assert pyright is not None
        assert pyright.rule == ToolRule.ALWAYS

    def test_git_is_when_instructed(self):
        git = next((t for t in DEVELOPER_SPEC.tools if t.name == "git"), None)
        assert git is not None
        assert git.rule == ToolRule.WHEN_INSTRUCTED

    def test_system_prompt_not_empty(self):
        assert len(DEVELOPER_SPEC.system_prompt) > 100

    def test_system_prompt_mentions_python(self):
        assert "Python" in DEVELOPER_SPEC.system_prompt

    def test_security_handoff_trigger_fires(self):
        trigger = next(
            (t for t in DEVELOPER_SPEC.handoff_triggers if t.target_agent == "security"),
            None,
        )
        assert trigger is not None
        task = AgentTask(
            instruction="check for SQL injection vulnerabilities", context={}, constraints=[]
        )
        assert trigger.condition(task) is True

    def test_security_handoff_does_not_fire_on_normal_task(self):
        trigger = next(
            (t for t in DEVELOPER_SPEC.handoff_triggers if t.target_agent == "security"),
            None,
        )
        assert trigger is not None
        task = AgentTask(instruction="add type hints to this function", context={}, constraints=[])
        assert trigger.condition(task) is False


class TestDeveloperAgent:
    def test_construction(self):
        agent = DeveloperAgent(model=_MockModel())
        assert agent.spec.name == "developer"

    def test_registered_after_import(self):
        # DeveloperAgent auto-registers on import
        reg = get_registry()
        assert reg.get("developer") is DeveloperAgent

    @pytest.mark.asyncio
    async def test_execute_returns_result(self):
        agent = DeveloperAgent(model=_MockModel())
        task = AgentTask(
            instruction="Review this function",
            context={"code": "def add(a, b): return a + b"},
            constraints=[],
        )
        result = await agent.execute(task, WorkflowContext())
        assert result.agent_name == "developer"
        assert len(result.response) > 0
