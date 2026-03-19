"""Tests for ttadev.agents.security.SecurityAgent — Task K2."""

import pytest

from ttadev.agents.protocol import ChatMessage
from ttadev.agents.registry import get_registry
from ttadev.agents.security import SECURITY_SPEC, SecurityAgent
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
        return "[HIGH] SQL injection risk — line 42 — use parameterised queries."


class TestSecuritySpec:
    def test_name(self):
        assert SECURITY_SPEC.name == "security"

    def test_capabilities_include_vulnerability(self):
        assert any("vulnerab" in c for c in SECURITY_SPEC.capabilities)

    def test_bandit_is_always_tool(self):
        tool = next((t for t in SECURITY_SPEC.tools if t.name == "bandit"), None)
        assert tool is not None
        assert tool.rule == ToolRule.ALWAYS

    def test_semgrep_is_when_instructed(self):
        tool = next((t for t in SECURITY_SPEC.tools if t.name == "semgrep"), None)
        assert tool is not None
        assert tool.rule == ToolRule.WHEN_INSTRUCTED

    def test_pip_audit_is_when_instructed(self):
        tool = next((t for t in SECURITY_SPEC.tools if t.name == "pip-audit"), None)
        assert tool is not None
        assert tool.rule == ToolRule.WHEN_INSTRUCTED

    def test_system_prompt_not_empty(self):
        assert len(SECURITY_SPEC.system_prompt) > 100

    def test_system_prompt_mentions_owasp(self):
        assert "OWASP" in SECURITY_SPEC.system_prompt

    def test_devops_handoff_trigger_fires(self):
        trigger = next(
            (t for t in SECURITY_SPEC.handoff_triggers if t.target_agent == "devops"), None
        )
        assert trigger is not None
        task = AgentTask(
            instruction="harden the docker deployment configuration", context={}, constraints=[]
        )
        assert trigger.condition(task) is True

    def test_devops_handoff_does_not_fire_on_normal_task(self):
        trigger = next(
            (t for t in SECURITY_SPEC.handoff_triggers if t.target_agent == "devops"), None
        )
        assert trigger is not None
        task = AgentTask(
            instruction="check for XSS vulnerabilities in the API", context={}, constraints=[]
        )
        assert trigger.condition(task) is False


class TestSecurityAgent:
    def test_construction(self):
        agent = SecurityAgent(model=_MockModel())
        assert agent.spec.name == "security"

    def test_registered_after_import(self):
        reg = get_registry()
        assert reg.get("security") is SecurityAgent

    def test_class_spec_accessible_without_instantiation(self):
        assert SecurityAgent._class_spec.name == "security"

    @pytest.mark.asyncio
    async def test_execute_returns_result(self):
        agent = SecurityAgent(model=_MockModel())
        task = AgentTask(
            instruction="Assess this module for injection vulnerabilities",
            context={},
            constraints=[],
        )
        result = await agent.execute(task, WorkflowContext())
        assert result.agent_name == "security"
        assert len(result.response) > 0
