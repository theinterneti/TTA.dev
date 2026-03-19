"""GitHubAgent — GitHub Workflow Specialist."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ttadev.agents.base import AgentPrimitive
from ttadev.agents.registry import _global_registry
from ttadev.agents.spec import AgentSpec, AgentTool, HandoffTrigger, QualityGate, ToolRule
from ttadev.agents.task import AgentTask

if TYPE_CHECKING:
    from ttadev.agents.protocol import ChatPrimitive

_SECURITY_KEYWORDS = frozenset(
    ["security", "vulnerability", "secret", "credential", "dependabot", "cve", "audit"]
)
_DEVOPS_KEYWORDS = frozenset(
    ["github actions", "workflow file", "ci/cd", "runner", "deploy", "release pipeline"]
)
_DEVELOPER_KEYWORDS = frozenset(["implement", "fix the bug", "write code", "refactor", "unit test"])


def _matches(task: AgentTask, keywords: frozenset[str]) -> bool:
    text = task.instruction.lower()
    return any(kw in text for kw in keywords)


GITHUB_SPEC = AgentSpec(
    name="github",
    role="GitHub Workflow Specialist",
    system_prompt=(
        "You are a GitHub workflow specialist. You help teams use GitHub effectively "
        "for code review, release management, and repository governance.\n\n"
        "## Core Responsibilities\n"
        "- Write clear, actionable pull request descriptions\n"
        "- Conduct and structure code reviews with inline feedback\n"
        "- Triage and organise GitHub issues\n"
        "- Configure branch protection rules and CODEOWNERS\n"
        "- Draft release notes from commit history\n"
        "- Advise on GitHub Actions workflow structure (leave implementation to DevOpsAgent)\n\n"
        "## PR Standards\n"
        "- Title: Conventional Commits format, max 72 characters\n"
        "- Body: Summary (what + why), Test Plan, Breaking Changes (if any)\n"
        "- Link to relevant issues with `Closes #N` or `Relates to #N`\n"
        "- Keep PRs focused — one logical change per PR\n\n"
        "## Code Review Guidelines\n"
        "1. Read the PR description before the diff\n"
        "2. Understand intent before critiquing implementation\n"
        "3. Distinguish blocking (must fix) from non-blocking (suggestion) comments\n"
        "4. Praise good patterns — reviews should be constructive, not just critical\n"
        "5. Approve only when all blocking comments are resolved\n\n"
        "## Output Format\n"
        "For PR descriptions: use the standard template (Summary / Test Plan / Notes). "
        "For code review comments: cite file and line number. "
        "For issue triage: suggest labels, milestone, and assignee."
    ),
    capabilities=[
        "pull request",
        "code review",
        "GitHub Actions",
        "issue triage",
        "branch protection",
        "CODEOWNERS",
        "release notes",
        "PR description",
        "repository governance",
    ],
    tools=[
        AgentTool("gh", "GitHub CLI — PRs, issues, releases, repo settings", ToolRule.ALWAYS),
        AgentTool("git", "Version control — log, diff for release notes", ToolRule.ALWAYS),
    ],
    quality_gates=[
        QualityGate(
            name="response_not_empty",
            check=lambda r: len(r.response.strip()) > 0,
            error_message="Agent returned an empty response.",
        ),
    ],
    handoff_triggers=[
        HandoffTrigger(
            condition=lambda t: _matches(t, _SECURITY_KEYWORDS),
            target_agent="security",
            reason="Task involves security scanning — routing to SecurityAgent.",
        ),
        HandoffTrigger(
            condition=lambda t: _matches(t, _DEVOPS_KEYWORDS),
            target_agent="devops",
            reason="Task involves CI/CD pipeline implementation — routing to DevOpsAgent.",
        ),
        HandoffTrigger(
            condition=lambda t: _matches(t, _DEVELOPER_KEYWORDS),
            target_agent="developer",
            reason="Task requires code changes — routing to DeveloperAgent.",
        ),
    ],
)


class GitHubAgent(AgentPrimitive):
    """GitHub Workflow Specialist agent.

    Writes PR descriptions, structures code reviews, triages issues, and
    advises on repository governance. Hands off to SecurityAgent,
    DevOpsAgent, or DeveloperAgent when the task requires it.

    Example::

        from ttadev.agents import GitHubAgent
        from ttadev.primitives.integrations import AnthropicPrimitive

        agent = GitHubAgent(model=AnthropicPrimitive())
        result = await agent.execute(
            AgentTask(instruction="Write a PR description for this change", context={}),
            WorkflowContext(),
        )
    """

    _class_spec: AgentSpec = GITHUB_SPEC

    def __init__(self, model: ChatPrimitive) -> None:
        super().__init__(spec=GITHUB_SPEC, model=model)


# Auto-register in the global registry on import.
_global_registry.register("github", GitHubAgent)
