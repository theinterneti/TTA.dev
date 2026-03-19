"""Tests for ttadev.agents.git.GitAgent — Task K4."""

import pytest

from ttadev.agents.git import GIT_SPEC, GitAgent
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
        return "Run: git rebase -i HEAD~3, then mark the last two commits as 'squash'."


class TestGitSpec:
    def test_name(self):
        assert GIT_SPEC.name == "git"

    def test_capabilities_include_commit(self):
        assert any("commit" in c for c in GIT_SPEC.capabilities)

    def test_git_is_always_tool(self):
        tool = next((t for t in GIT_SPEC.tools if t.name == "git"), None)
        assert tool is not None
        assert tool.rule == ToolRule.ALWAYS

    def test_system_prompt_not_empty(self):
        assert len(GIT_SPEC.system_prompt) > 100

    def test_system_prompt_mentions_conventional_commits(self):
        assert "Conventional Commits" in GIT_SPEC.system_prompt

    def test_github_handoff_trigger_fires(self):
        trigger = next((t for t in GIT_SPEC.handoff_triggers if t.target_agent == "github"), None)
        assert trigger is not None
        task = AgentTask(
            instruction="create a pull request for this branch", context={}, constraints=[]
        )
        assert trigger.condition(task) is True

    def test_github_handoff_does_not_fire_on_normal_task(self):
        trigger = next((t for t in GIT_SPEC.handoff_triggers if t.target_agent == "github"), None)
        assert trigger is not None
        task = AgentTask(
            instruction="squash my last 3 commits into one", context={}, constraints=[]
        )
        assert trigger.condition(task) is False

    def test_devops_handoff_trigger_fires(self):
        trigger = next((t for t in GIT_SPEC.handoff_triggers if t.target_agent == "devops"), None)
        assert trigger is not None
        task = AgentTask(
            instruction="set up a git webhook for the CI/CD pipeline", context={}, constraints=[]
        )
        assert trigger.condition(task) is True


class TestGitAgent:
    def test_construction(self):
        agent = GitAgent(model=_MockModel())
        assert agent.spec.name == "git"

    def test_registered_after_import(self):
        reg = get_registry()
        assert reg.get("git") is GitAgent

    def test_class_spec_accessible_without_instantiation(self):
        assert GitAgent._class_spec.name == "git"

    @pytest.mark.asyncio
    async def test_execute_returns_result(self):
        agent = GitAgent(model=_MockModel())
        task = AgentTask(
            instruction="How do I squash the last 3 commits into one?",
            context={},
            constraints=[],
        )
        result = await agent.execute(task, WorkflowContext())
        assert result.agent_name == "git"
        assert len(result.response) > 0
