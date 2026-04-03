"""DevOpsAgent — DevOps / Platform Engineer specialist."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ttadev.agents._utils import _matches
from ttadev.agents.base import AgentPrimitive
from ttadev.agents.registry import _global_registry
from ttadev.agents.spec import AgentSpec, AgentTool, HandoffTrigger, QualityGate, ToolRule
from ttadev.primitives.llm import COMPLEXITY_MODERATE, TASK_GENERAL, TaskProfile

if TYPE_CHECKING:
    from ttadev.agents.protocol import ChatPrimitive

_SECURITY_KEYWORDS = frozenset(
    [
        "security",
        "vulnerability",
        "secret",
        "credential",
        "tls",
        "certificate",
        "firewall",
        "auth",
        "authentication",
        "authorization",
    ]
)
_DEVELOPER_KEYWORDS = frozenset(
    ["implement", "refactor", "add feature", "fix bug", "write code", "unit test"]
)
_GITHUB_KEYWORDS = frozenset(
    ["pull request", "pr", "merge", "branch protection", "codeowners", "release"]
)


DEVOPS_SPEC = AgentSpec(
    name="devops",
    role="DevOps / Platform Engineer",
    system_prompt=(
        "You are a DevOps and platform engineer specialising in Python project "
        "infrastructure, CI/CD pipelines, and container orchestration.\n\n"
        "## Core Responsibilities\n"
        "- Design and maintain CI/CD pipelines (GitHub Actions preferred)\n"
        "- Manage Docker images and container configurations\n"
        "- Handle environment setup, secrets injection, and configuration management\n"
        "- Plan and execute deployments with rollback strategies\n"
        "- Set up monitoring, alerting, and observability infrastructure\n"
        "- Manage dependency updates and release processes\n\n"
        "## Standards\n"
        "- Use `uv` for Python package management in all CI steps\n"
        "- Pin Docker base image digests for reproducibility\n"
        "- Never hardcode secrets — use environment variables or secret managers\n"
        "- All YAML (GitHub Actions, Docker Compose) must pass yamllint\n"
        "- Prefer declarative configuration over imperative scripts\n"
        "- Document every environment variable with its purpose and example value\n\n"
        "## CI/CD Principles\n"
        "1. Fast feedback: lint and type-check before running tests\n"
        "2. Fail fast: unit tests before integration tests\n"
        "3. Reproducible: pin all tool versions; use lockfiles\n"
        "4. Observable: emit structured logs and metrics from every pipeline step\n\n"
        "## Output Format\n"
        "Provide complete, runnable YAML or shell commands. "
        "Annotate every non-obvious configuration choice. "
        "Flag any step that requires manual intervention."
    ),
    capabilities=[
        "CI/CD pipeline",
        "Docker",
        "infrastructure",
        "deployment",
        "environment setup",
        "GitHub Actions",
        "monitoring setup",
        "release management",
        "container orchestration",
        "secrets management",
    ],
    tools=[
        AgentTool("git", "Version control — tagging releases, branch management", ToolRule.ALWAYS),
        AgentTool("docker", "Container build and run", ToolRule.WHEN_INSTRUCTED),
        AgentTool("gh", "GitHub CLI — releases, Actions, repo settings", ToolRule.WHEN_INSTRUCTED),
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
            reason="Task involves security or secrets — routing to SecurityAgent.",
        ),
        HandoffTrigger(
            condition=lambda t: _matches(t, _DEVELOPER_KEYWORDS),
            target_agent="developer",
            reason="Task requires application code changes — routing to DeveloperAgent.",
        ),
        HandoffTrigger(
            condition=lambda t: _matches(t, _GITHUB_KEYWORDS),
            target_agent="github",
            reason="Task involves GitHub workflow — routing to GitHubAgent.",
        ),
    ],
    default_task_profile=TaskProfile(task_type=TASK_GENERAL, complexity=COMPLEXITY_MODERATE),
)


class DevOpsAgent(AgentPrimitive):
    """DevOps / Platform Engineer agent.

    Designs CI/CD pipelines, manages Docker infrastructure, handles deployments,
    and sets up monitoring. Hands off to SecurityAgent, DeveloperAgent, or
    GitHubAgent when the task requires it.

    Example::

        from ttadev.agents import DevOpsAgent
        from ttadev.primitives.integrations import AnthropicPrimitive

        agent = DevOpsAgent(model=AnthropicPrimitive())
        result = await agent.execute(
            AgentTask(instruction="Set up a GitHub Actions CI pipeline", context={}),
            WorkflowContext(),
        )
    """

    _class_spec: AgentSpec = DEVOPS_SPEC

    def __init__(self, model: ChatPrimitive) -> None:
        super().__init__(spec=DEVOPS_SPEC, model=model)


# Auto-register in the global registry on import.
_global_registry.register("devops", DevOpsAgent)
