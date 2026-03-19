"""DeveloperAgent — Senior Python Developer specialist."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ttadev.agents.base import AgentPrimitive
from ttadev.agents.registry import _global_registry
from ttadev.agents.spec import AgentSpec, AgentTool, HandoffTrigger, QualityGate, ToolRule
from ttadev.agents.task import AgentTask

if TYPE_CHECKING:
    from ttadev.agents.protocol import ChatPrimitive

_SECURITY_KEYWORDS = frozenset(
    ["security", "vulnerability", "injection", "xss", "csrf", "exploit", "attack", "sanitize"]
)
_DEVOPS_KEYWORDS = frozenset(
    ["deploy", "deployment", "infrastructure", "docker", "kubernetes", "ci/cd", "pipeline", "helm"]
)
_GITHUB_KEYWORDS = frozenset(
    ["pull request", "pr", "merge", "branch", "release", "github", "review request"]
)


def _matches(task: AgentTask, keywords: frozenset[str]) -> bool:
    text = task.instruction.lower()
    return any(kw in text for kw in keywords)


DEVELOPER_SPEC = AgentSpec(
    name="developer",
    role="Senior Python Developer",
    system_prompt=(
        "You are a senior Python developer specialising in TTA.dev workflows and primitives.\n\n"
        "## Standards\n"
        "- Python 3.11+ with full type annotations (use `str | None`, never `Optional[str]`)\n"
        "- Follow PEP 8; line length 88 (ruff enforced)\n"
        "- Use `uv` for package management — never `pip` or `poetry`\n"
        "- Write pytest tests in AAA pattern (Arrange / Act / Assert)\n"
        "- Target 100% coverage for any new code you write\n"
        "- Use `WorkflowContext` to pass state — never globals\n"
        "- Prefer `InstrumentedPrimitive` as base for observable primitives\n\n"
        "## Review Criteria\n"
        "When reviewing code, check for:\n"
        "1. Correctness — does it do what is claimed?\n"
        "2. Type safety — are all types annotated and correct?\n"
        "3. Edge cases — division by zero, empty inputs, None values\n"
        "4. Security — no hardcoded secrets, no command injection, safe subprocess usage\n"
        "5. Readability — clear names, no unnecessary complexity\n"
        "6. Test coverage — are the happy path and error paths tested?\n\n"
        "## Output Format\n"
        "Be direct and specific. Cite line numbers when reviewing code. "
        "Provide working code examples for any suggested changes. "
        "If a task requires security review, explicitly say so."
    ),
    capabilities=[
        "code implementation",
        "code review",
        "debugging",
        "refactoring",
        "test writing",
        "type annotations",
        "primitive development",
    ],
    tools=[
        AgentTool("ruff", "Python linter — runs on all produced code", ToolRule.ALWAYS),
        AgentTool("pyright", "Type checker — runs on all produced code", ToolRule.ALWAYS),
        AgentTool("pytest", "Test runner", ToolRule.ALWAYS),
        AgentTool("git", "Version control", ToolRule.WHEN_INSTRUCTED),
    ],
    quality_gates=[
        # Gates are intentionally lightweight here — integration layer wires real checks.
        # The spec declares intent; ToolCallLoop executes the tools.
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
            reason="Task involves security analysis — routing to SecurityAgent.",
        ),
        HandoffTrigger(
            condition=lambda t: _matches(t, _DEVOPS_KEYWORDS),
            target_agent="devops",
            reason="Task involves deployment or infrastructure — routing to DevOpsAgent.",
        ),
        HandoffTrigger(
            condition=lambda t: _matches(t, _GITHUB_KEYWORDS),
            target_agent="github",
            reason="Task involves GitHub workflow — routing to GitHubAgent.",
        ),
    ],
)


class DeveloperAgent(AgentPrimitive):
    """Senior Python Developer agent.

    Class attribute ``_class_spec`` exposes the spec without requiring instantiation,
    allowing CLI introspection (``tta agent list/show``) without a model.

    Reviews, implements, debugs, and tests Python code to TTA.dev standards.
    Automatically hands off to SecurityAgent, DevOpsAgent, or GitHubAgent
    when the task requires it.

    Example::

        from ttadev.agents import DeveloperAgent
        from ttadev.primitives.integrations import AnthropicPrimitive

        agent = DeveloperAgent(model=AnthropicPrimitive())
        result = await agent.execute(
            AgentTask(instruction="Review this function", context={"code": "..."}),
            WorkflowContext(),
        )
    """

    _class_spec: AgentSpec = DEVELOPER_SPEC  # accessible without instantiation

    def __init__(self, model: ChatPrimitive) -> None:
        super().__init__(spec=DEVELOPER_SPEC, model=model)


# Auto-register in the global registry on import.
_global_registry.register("developer", DeveloperAgent)
