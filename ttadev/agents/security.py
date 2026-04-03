"""SecurityAgent — Application Security Engineer specialist."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ttadev.agents._utils import _matches
from ttadev.agents.base import AgentPrimitive
from ttadev.agents.registry import _global_registry
from ttadev.agents.spec import AgentSpec, AgentTool, HandoffTrigger, QualityGate, ToolRule
from ttadev.primitives.llm import COMPLEXITY_COMPLEX, TASK_REASONING, TaskProfile

if TYPE_CHECKING:
    from ttadev.agents.protocol import ChatPrimitive

_DEVOPS_KEYWORDS = frozenset(
    ["deploy", "deployment", "infrastructure", "docker", "kubernetes", "pipeline", "helm"]
)
_DEVELOPER_KEYWORDS = frozenset(
    ["implement", "refactor", "add feature", "fix bug", "write code", "change the"]
)


SECURITY_SPEC = AgentSpec(
    name="security",
    role="Application Security Engineer",
    system_prompt=(
        "You are an application security engineer specialising in Python web applications "
        "and API security.\n\n"
        "## Core Responsibilities\n"
        "- Identify vulnerabilities using OWASP Top 10 as a baseline\n"
        "- Audit authentication, authorisation, and session management\n"
        "- Review dependency trees for known CVEs\n"
        "- Scan for secrets, credentials, and sensitive data in code\n"
        "- Assess input validation, output encoding, and injection risks\n\n"
        "## Vulnerability Assessment Approach\n"
        "1. **Injection** — SQL, command, LDAP, XPath injection risks\n"
        "2. **Broken auth** — weak tokens, session fixation, missing expiry\n"
        "3. **Sensitive data** — hardcoded secrets, unencrypted storage, logging PII\n"
        "4. **XSS / CSRF** — missing sanitisation, missing CSRF tokens\n"
        "5. **Dependency CVEs** — run pip-audit; flag high/critical findings\n"
        "6. **Supply chain** — unpinned deps, typosquatting risks\n\n"
        "## Tools\n"
        "- bandit: Python-specific security linter (always run first)\n"
        "- semgrep: Semantic code analysis with security rule sets\n"
        "- pip-audit: Dependency vulnerability scanner against PyPI Advisory DB\n\n"
        "## Output Format\n"
        "Structure findings as: [SEVERITY] Finding — Location — Remediation. "
        "Severity levels: CRITICAL, HIGH, MEDIUM, LOW, INFO. "
        "Always include a concrete remediation step, not just a description of the problem."
    ),
    capabilities=[
        "vulnerability assessment",
        "dependency audit",
        "secrets scanning",
        "OWASP review",
        "auth review",
        "SQL injection",
        "XSS",
        "security hardening",
        "CVE analysis",
        "penetration testing guidance",
    ],
    tools=[
        AgentTool(
            "bandit",
            "Python security linter — detects common security issues",
            ToolRule.ALWAYS,
        ),
        AgentTool(
            "semgrep",
            "Semantic code analysis with OWASP and secrets rule sets",
            ToolRule.WHEN_INSTRUCTED,
        ),
        AgentTool(
            "pip-audit",
            "Dependency vulnerability scanner against PyPI Advisory Database",
            ToolRule.WHEN_INSTRUCTED,
        ),
        AgentTool(
            "git", "Version control — inspect history for leaked secrets", ToolRule.WHEN_INSTRUCTED
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
            condition=lambda t: _matches(t, _DEVOPS_KEYWORDS),
            target_agent="devops",
            reason="Task involves infrastructure security — routing to DevOpsAgent.",
        ),
        HandoffTrigger(
            condition=lambda t: _matches(t, _DEVELOPER_KEYWORDS),
            target_agent="developer",
            reason="Task requires code changes — routing to DeveloperAgent.",
        ),
    ],
    default_task_profile=TaskProfile(task_type=TASK_REASONING, complexity=COMPLEXITY_COMPLEX),
)


class SecurityAgent(AgentPrimitive):
    """Application Security Engineer agent.

    Assesses vulnerabilities, audits dependencies, and reviews code for
    OWASP Top 10 risks. Uses bandit, semgrep, and pip-audit. Hands off to
    DevOpsAgent for infrastructure concerns or DeveloperAgent for code fixes.

    Example::

        from ttadev.agents import SecurityAgent
        from ttadev.primitives.integrations import AnthropicPrimitive

        agent = SecurityAgent(model=AnthropicPrimitive())
        result = await agent.execute(
            AgentTask(instruction="Check for SQL injection vulnerabilities", context={}),
            WorkflowContext(),
        )
    """

    _class_spec: AgentSpec = SECURITY_SPEC

    def __init__(self, model: ChatPrimitive) -> None:
        super().__init__(spec=SECURITY_SPEC, model=model)


# Auto-register in the global registry on import.
_global_registry.register("security", SecurityAgent)
