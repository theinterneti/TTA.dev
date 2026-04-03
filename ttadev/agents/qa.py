"""QAAgent — Senior QA / Test Engineer specialist."""

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
        "injection",
        "xss",
        "csrf",
        "exploit",
        "attack",
        "auth",
        "authentication",
        "authorization",
    ]
)
_DEVOPS_KEYWORDS = frozenset(
    ["ci/cd", "pipeline", "github actions", "jenkins", "infrastructure", "deploy"]
)
_PERFORMANCE_KEYWORDS = frozenset(
    [
        "slow",
        "slowly",
        "performance",
        "latency",
        "benchmark",
        "profile",
        "profiling",
        "memory leak",
        "bottleneck",
    ]
)


QA_SPEC = AgentSpec(
    name="qa",
    role="Senior QA / Test Engineer",
    system_prompt=(
        "You are a senior QA and test engineer specialising in Python applications.\n\n"
        "## Core Responsibilities\n"
        "- Write comprehensive pytest test suites (unit, integration, E2E)\n"
        "- Diagnose flaky tests and CI pipeline failures\n"
        "- Analyse test coverage and identify untested paths\n"
        "- Define and enforce test strategy for new features\n"
        "- Review test code for correctness, isolation, and reliability\n\n"
        "## Testing Standards\n"
        "- Use pytest with AAA pattern (Arrange / Act / Assert)\n"
        "- Tests must be deterministic — no time-dependent or order-dependent behaviour\n"
        "- Mock external dependencies; never hit real APIs in unit tests\n"
        "- Use `@pytest.mark.asyncio` for async tests\n"
        "- Use `@pytest.mark.integration` for tests that need real infrastructure\n"
        "- Target 100% branch coverage for new code\n\n"
        "## Flaky Test Diagnosis\n"
        "When diagnosing flaky tests, check for:\n"
        "1. Shared mutable state between tests\n"
        "2. Time-dependent assertions (use freezegun or mock time)\n"
        "3. File system or network I/O without proper mocking\n"
        "4. Race conditions in async code\n"
        "5. Order-dependent test data\n\n"
        "## Output Format\n"
        "Be specific about test names, line numbers, and failure modes. "
        "Provide working pytest code for any new or fixed tests."
    ),
    capabilities=[
        "test writing",
        "test review",
        "flaky test diagnosis",
        "coverage analysis",
        "test strategy",
        "CI pipeline debugging",
        "regression testing",
        "pytest",
    ],
    tools=[
        AgentTool("pytest", "Test runner — executes the full test suite", ToolRule.ALWAYS),
        AgentTool(
            "coverage",
            "Coverage analysis — identifies untested code paths",
            ToolRule.ALWAYS,
        ),
        AgentTool("ruff", "Python linter — validates test code style", ToolRule.WHEN_INSTRUCTED),
        AgentTool(
            "git", "Version control — inspect history for regressions", ToolRule.WHEN_INSTRUCTED
        ),
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
            reason="Task involves security testing — routing to SecurityAgent.",
        ),
        HandoffTrigger(
            condition=lambda t: _matches(t, _DEVOPS_KEYWORDS),
            target_agent="devops",
            reason="Task involves CI/CD infrastructure — routing to DevOpsAgent.",
        ),
        HandoffTrigger(
            condition=lambda t: _matches(t, _PERFORMANCE_KEYWORDS),
            target_agent="performance",
            reason="Task involves performance analysis — routing to PerformanceAgent.",
        ),
    ],
    default_task_profile=TaskProfile(task_type=TASK_GENERAL, complexity=COMPLEXITY_MODERATE),
)


class QAAgent(AgentPrimitive):
    """Senior QA / Test Engineer agent.

    Writes, reviews, and debugs pytest test suites. Diagnoses flaky tests
    and coverage gaps. Hands off to SecurityAgent, DevOpsAgent, or
    PerformanceAgent when the task requires it.

    Example::

        from ttadev.agents import QAAgent
        from ttadev.primitives.integrations import AnthropicPrimitive

        agent = QAAgent(model=AnthropicPrimitive())
        result = await agent.execute(
            AgentTask(instruction="Our test suite is flaky on CI", context={}),
            WorkflowContext(),
        )
    """

    _class_spec: AgentSpec = QA_SPEC

    def __init__(self, model: ChatPrimitive) -> None:
        super().__init__(spec=QA_SPEC, model=model)


# Auto-register in the global registry on import.
_global_registry.register("qa", QAAgent)
