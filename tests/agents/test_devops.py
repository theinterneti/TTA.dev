"""Tests for ttadev.agents.devops.DevOpsAgent — Task K3."""

import pytest

from ttadev.agents.devops import DEVOPS_SPEC, DevOpsAgent
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
        return "Here is a GitHub Actions workflow that runs tests on every push."


class TestDevOpsSpec:
    def test_name(self):
        assert DEVOPS_SPEC.name == "devops"

    def test_capabilities_include_cicd(self):
        assert any("CI/CD" in c or "pipeline" in c for c in DEVOPS_SPEC.capabilities)

    def test_git_is_always_tool(self):
        tool = next((t for t in DEVOPS_SPEC.tools if t.name == "git"), None)
        assert tool is not None
        assert tool.rule == ToolRule.ALWAYS

    def test_docker_is_when_instructed(self):
        tool = next((t for t in DEVOPS_SPEC.tools if t.name == "docker"), None)
        assert tool is not None
        assert tool.rule == ToolRule.WHEN_INSTRUCTED

    def test_gh_is_when_instructed(self):
        tool = next((t for t in DEVOPS_SPEC.tools if t.name == "gh"), None)
        assert tool is not None
        assert tool.rule == ToolRule.WHEN_INSTRUCTED

    def test_system_prompt_not_empty(self):
        assert len(DEVOPS_SPEC.system_prompt) > 100

    def test_system_prompt_mentions_uv(self):
        assert "uv" in DEVOPS_SPEC.system_prompt

    def test_security_handoff_trigger_fires(self):
        trigger = next(
            (t for t in DEVOPS_SPEC.handoff_triggers if t.target_agent == "security"), None
        )
        assert trigger is not None
        task = AgentTask(
            instruction="rotate the TLS certificate for our API", context={}, constraints=[]
        )
        assert trigger.condition(task) is True

    def test_security_handoff_does_not_fire_on_normal_task(self):
        trigger = next(
            (t for t in DEVOPS_SPEC.handoff_triggers if t.target_agent == "security"), None
        )
        assert trigger is not None
        task = AgentTask(
            instruction="set up a GitHub Actions CI pipeline", context={}, constraints=[]
        )
        assert trigger.condition(task) is False

    def test_github_handoff_trigger_fires(self):
        trigger = next(
            (t for t in DEVOPS_SPEC.handoff_triggers if t.target_agent == "github"), None
        )
        assert trigger is not None
        task = AgentTask(
            instruction="create a release for the new version", context={}, constraints=[]
        )
        assert trigger.condition(task) is True


class TestDevOpsAgent:
    def test_construction(self):
        agent = DevOpsAgent(model=_MockModel())
        assert agent.spec.name == "devops"

    def test_registered_after_import(self):
        reg = get_registry()
        assert reg.get("devops") is DevOpsAgent

    def test_class_spec_accessible_without_instantiation(self):
        assert DevOpsAgent._class_spec.name == "devops"

    @pytest.mark.asyncio
    async def test_execute_returns_result(self):
        agent = DevOpsAgent(model=_MockModel())
        task = AgentTask(
            instruction="Set up a GitHub Actions CI workflow for this repo",
            context={},
            constraints=[],
        )
        result = await agent.execute(task, WorkflowContext())
        assert result.agent_name == "devops"
        assert len(result.response) > 0
