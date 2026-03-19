"""Tests for ttadev.agents.spec — Task A2."""

import dataclasses

import pytest

from ttadev.agents.spec import (
    AgentSpec,
    AgentTool,
    HandoffTrigger,
    QualityGate,
    ToolRule,
)
from ttadev.agents.task import AgentResult, AgentTask


def _make_result(passed: bool = True) -> AgentResult:
    return AgentResult(
        agent_name="test",
        response="ok",
        artifacts=[],
        suggestions=[],
        spawned_agents=[],
        quality_gates_passed=passed,
        confidence=1.0,
    )


def _make_task(instruction: str = "do something") -> AgentTask:
    return AgentTask(instruction=instruction, context={}, constraints=[])


class TestToolRule:
    def test_values(self):
        assert ToolRule.ALWAYS.value == "always"
        assert ToolRule.WHEN_INSTRUCTED.value == "when_instructed"
        assert ToolRule.NEVER.value == "never"


class TestAgentTool:
    def test_construction(self):
        t = AgentTool(name="ruff", description="linter", rule=ToolRule.ALWAYS)
        assert t.name == "ruff"
        assert t.rule == ToolRule.ALWAYS

    def test_is_frozen(self):
        t = AgentTool(name="ruff", description="linter", rule=ToolRule.ALWAYS)
        with pytest.raises((dataclasses.FrozenInstanceError, AttributeError)):
            t.name = "other"  # type: ignore[misc]


class TestQualityGate:
    def test_construction(self):
        gate = QualityGate(
            name="lint",
            check=lambda r: True,
            error_message="lint failed",
        )
        assert gate.name == "lint"
        assert gate.check(_make_result()) is True

    def test_failing_gate(self):
        gate = QualityGate(name="fail", check=lambda r: False, error_message="oops")
        assert gate.check(_make_result()) is False

    def test_is_frozen(self):
        gate = QualityGate(name="g", check=lambda r: True, error_message="x")
        with pytest.raises((dataclasses.FrozenInstanceError, AttributeError)):
            gate.name = "other"  # type: ignore[misc]


class TestHandoffTrigger:
    def test_construction(self):
        trigger = HandoffTrigger(
            condition=lambda t: "security" in t.instruction,
            target_agent="security",
            reason="Security review needed",
        )
        assert trigger.target_agent == "security"
        assert trigger.condition(_make_task("check security")) is True
        assert trigger.condition(_make_task("add feature")) is False

    def test_is_frozen(self):
        trigger = HandoffTrigger(condition=lambda t: True, target_agent="x", reason="y")
        with pytest.raises((dataclasses.FrozenInstanceError, AttributeError)):
            trigger.target_agent = "z"  # type: ignore[misc]


class TestAgentSpec:
    def _make_spec(self, name: str = "test-agent") -> AgentSpec:
        return AgentSpec(
            name=name,
            role="Test Agent",
            system_prompt="You are a test agent.",
            capabilities=["testing"],
            tools=[AgentTool("ruff", "linter", ToolRule.ALWAYS)],
            quality_gates=[QualityGate("ok", lambda r: True, "failed")],
            handoff_triggers=[],
        )

    def test_construction(self):
        spec = self._make_spec()
        assert spec.name == "test-agent"
        assert spec.role == "Test Agent"
        assert len(spec.tools) == 1
        assert len(spec.capabilities) == 1

    def test_is_frozen(self):
        spec = self._make_spec()
        with pytest.raises((dataclasses.FrozenInstanceError, AttributeError)):
            spec.name = "other"  # type: ignore[misc]

    def test_tools_by_rule(self):
        spec = AgentSpec(
            name="x",
            role="X",
            system_prompt="x",
            capabilities=[],
            tools=[
                AgentTool("ruff", "linter", ToolRule.ALWAYS),
                AgentTool("git", "vcs", ToolRule.WHEN_INSTRUCTED),
                AgentTool("deploy", "deploy", ToolRule.NEVER),
            ],
            quality_gates=[],
            handoff_triggers=[],
        )
        always = [t for t in spec.tools if t.rule == ToolRule.ALWAYS]
        never = [t for t in spec.tools if t.rule == ToolRule.NEVER]
        assert len(always) == 1
        assert always[0].name == "ruff"
        assert len(never) == 1
