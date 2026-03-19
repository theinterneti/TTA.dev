"""Tests for ttadev.agents.github.GitHubAgent — Task K5."""

import pytest

from ttadev.agents.github import GITHUB_SPEC, GitHubAgent
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
        return "## Summary\n- Adds retry logic to the HTTP client\n\n## Test Plan\n- [ ] Unit tests pass"


class TestGitHubSpec:
    def test_name(self):
        assert GITHUB_SPEC.name == "github"

    def test_capabilities_include_pull_request(self):
        assert any("pull request" in c for c in GITHUB_SPEC.capabilities)

    def test_gh_is_always_tool(self):
        tool = next((t for t in GITHUB_SPEC.tools if t.name == "gh"), None)
        assert tool is not None
        assert tool.rule == ToolRule.ALWAYS

    def test_git_is_always_tool(self):
        tool = next((t for t in GITHUB_SPEC.tools if t.name == "git"), None)
        assert tool is not None
        assert tool.rule == ToolRule.ALWAYS

    def test_system_prompt_not_empty(self):
        assert len(GITHUB_SPEC.system_prompt) > 100

    def test_system_prompt_mentions_pr_standards(self):
        assert (
            "PR" in GITHUB_SPEC.system_prompt or "pull request" in GITHUB_SPEC.system_prompt.lower()
        )

    def test_security_handoff_trigger_fires(self):
        trigger = next(
            (t for t in GITHUB_SPEC.handoff_triggers if t.target_agent == "security"), None
        )
        assert trigger is not None
        task = AgentTask(
            instruction="run a dependabot audit on this repository", context={}, constraints=[]
        )
        assert trigger.condition(task) is True

    def test_security_handoff_does_not_fire_on_normal_task(self):
        trigger = next(
            (t for t in GITHUB_SPEC.handoff_triggers if t.target_agent == "security"), None
        )
        assert trigger is not None
        task = AgentTask(
            instruction="write a PR description for this branch", context={}, constraints=[]
        )
        assert trigger.condition(task) is False

    def test_devops_handoff_trigger_fires(self):
        trigger = next(
            (t for t in GITHUB_SPEC.handoff_triggers if t.target_agent == "devops"), None
        )
        assert trigger is not None
        task = AgentTask(
            instruction="implement a GitHub Actions release pipeline", context={}, constraints=[]
        )
        assert trigger.condition(task) is True


class TestGitHubAgent:
    def test_construction(self):
        agent = GitHubAgent(model=_MockModel())
        assert agent.spec.name == "github"

    def test_registered_after_import(self):
        reg = get_registry()
        assert reg.get("github") is GitHubAgent

    def test_class_spec_accessible_without_instantiation(self):
        assert GitHubAgent._class_spec.name == "github"

    @pytest.mark.asyncio
    async def test_execute_returns_result(self):
        agent = GitHubAgent(model=_MockModel())
        task = AgentTask(
            instruction="Write a PR description for the retry primitive feature",
            context={},
            constraints=[],
        )
        result = await agent.execute(task, WorkflowContext())
        assert result.agent_name == "github"
        assert len(result.response) > 0
