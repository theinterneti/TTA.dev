"""GitAgent — Git Operations Specialist."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ttadev.agents.base import AgentPrimitive
from ttadev.agents.registry import _global_registry
from ttadev.agents.spec import AgentSpec, AgentTool, HandoffTrigger, QualityGate, ToolRule
from ttadev.agents.task import AgentTask

if TYPE_CHECKING:
    from ttadev.agents.protocol import ChatPrimitive

_GITHUB_KEYWORDS = frozenset(
    ["pull request", "pr", "github", "merge request", "code review", "codeowners", "release notes"]
)
_DEVOPS_KEYWORDS = frozenset(
    ["ci/cd", "deploy", "pipeline", "github actions", "hook", "webhook", "automation"]
)


def _matches(task: AgentTask, keywords: frozenset[str]) -> bool:
    text = task.instruction.lower()
    return any(kw in text for kw in keywords)


GIT_SPEC = AgentSpec(
    name="git",
    role="Git Operations Specialist",
    system_prompt=(
        "You are a git operations specialist. You help developers manage their git "
        "repositories safely and efficiently.\n\n"
        "## Core Responsibilities\n"
        "- Advise on branch strategy and commit conventions\n"
        "- Resolve merge conflicts and rebase safely\n"
        "- Reconstruct or repair history (cherry-pick, revert, reset)\n"
        "- Manage stashes, tags, and submodules\n"
        "- Diagnose and recover from common git mistakes\n\n"
        "## Commit Standards (TTA.dev)\n"
        "- Use Conventional Commits: `<type>: <description>`\n"
        "- Types: feat, fix, docs, refactor, test, chore, perf, ci\n"
        "- Keep commits atomic — one logical change per commit\n"
        '- Write descriptions in imperative mood ("add" not "added")\n\n'
        "## Safety Rules\n"
        "- Never suggest force-pushing to main/master without explicit user confirmation\n"
        "- Always prefer `git revert` over `git reset --hard` for shared branches\n"
        "- Before any destructive operation, show the user what it will do\n"
        "- When in doubt, recommend creating a backup branch first\n\n"
        "## Output Format\n"
        "Always provide the exact git command(s) to run, in order. "
        "For multi-step operations, number each step. "
        "Flag any step that is destructive or irreversible."
    ),
    capabilities=[
        "git commit",
        "git branch",
        "git merge",
        "git rebase",
        "git history",
        "conflict resolution",
        "cherry-pick",
        "stash management",
        "git tag",
        "commit conventions",
    ],
    tools=[
        AgentTool("git", "Version control — all git operations", ToolRule.ALWAYS),
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
            condition=lambda t: _matches(t, _GITHUB_KEYWORDS),
            target_agent="github",
            reason="Task involves GitHub platform — routing to GitHubAgent.",
        ),
        HandoffTrigger(
            condition=lambda t: _matches(t, _DEVOPS_KEYWORDS),
            target_agent="devops",
            reason="Task involves CI/CD automation — routing to DevOpsAgent.",
        ),
    ],
)


class GitAgent(AgentPrimitive):
    """Git Operations Specialist agent.

    Advises on branching, rebasing, conflict resolution, and history management.
    Provides exact git commands for every operation. Hands off to GitHubAgent
    for GitHub platform tasks or DevOpsAgent for CI/CD automation.

    Example::

        from ttadev.agents import GitAgent
        from ttadev.primitives.integrations import AnthropicPrimitive

        agent = GitAgent(model=AnthropicPrimitive())
        result = await agent.execute(
            AgentTask(instruction="How do I squash the last 3 commits?", context={}),
            WorkflowContext(),
        )
    """

    _class_spec: AgentSpec = GIT_SPEC

    def __init__(self, model: ChatPrimitive) -> None:
        super().__init__(spec=GIT_SPEC, model=model)


# Auto-register in the global registry on import.
_global_registry.register("git", GitAgent)
