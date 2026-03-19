"""Tests for WorkflowDefinition dataclasses — Task T2."""

import dataclasses

import pytest

from ttadev.agents.task import AgentResult, Artifact
from ttadev.workflows.definition import (
    MemoryConfig,
    StepResult,
    WorkflowDefinition,
    WorkflowResult,
    WorkflowStep,
)


class TestWorkflowStep:
    def test_minimal_construction(self):
        step = WorkflowStep(agent="developer")
        assert step.agent == "developer"
        assert step.gate is True
        assert step.input_transform is None

    def test_frozen(self):
        step = WorkflowStep(agent="qa")
        with pytest.raises((dataclasses.FrozenInstanceError, TypeError)):
            step.agent = "security"  # type: ignore[misc]

    def test_gate_false(self):
        step = WorkflowStep(agent="git", gate=False)
        assert step.gate is False

    def test_input_transform_callable(self):
        fn = lambda state: None  # noqa: E731
        step = WorkflowStep(agent="developer", input_transform=fn)
        assert step.input_transform is fn


class TestMemoryConfig:
    def test_defaults(self):
        cfg = MemoryConfig()
        assert cfg.flush_to_persistent is True
        assert cfg.bank_id is None

    def test_custom_bank_id(self):
        cfg = MemoryConfig(bank_id="tta.workflow.my_flow")
        assert cfg.bank_id == "tta.workflow.my_flow"

    def test_frozen(self):
        cfg = MemoryConfig()
        with pytest.raises((dataclasses.FrozenInstanceError, TypeError)):
            cfg.flush_to_persistent = False  # type: ignore[misc]


class TestWorkflowDefinition:
    def test_minimal_construction(self):
        defn = WorkflowDefinition(
            name="test",
            description="A test workflow",
            steps=[WorkflowStep(agent="developer")],
        )
        assert defn.name == "test"
        assert defn.auto_approve is False
        assert isinstance(defn.memory_config, MemoryConfig)

    def test_frozen(self):
        defn = WorkflowDefinition(
            name="test", description="d", steps=[WorkflowStep(agent="developer")]
        )
        with pytest.raises((dataclasses.FrozenInstanceError, TypeError)):
            defn.name = "other"  # type: ignore[misc]

    def test_steps_order_preserved(self):
        agents = ["developer", "qa", "security", "git", "github"]
        steps = [WorkflowStep(agent=a) for a in agents]
        defn = WorkflowDefinition(name="f", description="d", steps=steps)
        assert [s.agent for s in defn.steps] == agents


class TestStepResult:
    def _make_result(self) -> AgentResult:
        return AgentResult(
            agent_name="developer",
            response="done",
            artifacts=[],
            suggestions=[],
            spawned_agents=[],
            quality_gates_passed=True,
            confidence=0.9,
        )

    def test_construction(self):
        sr = StepResult(step_index=0, agent_name="developer", result=self._make_result())
        assert sr.step_index == 0
        assert sr.skipped is False
        assert sr.gate_decision == "continue"

    def test_skipped_defaults(self):
        sr = StepResult(step_index=1, agent_name="qa", result=self._make_result(), skipped=True)
        assert sr.skipped is True


class TestWorkflowResult:
    def test_construction(self):
        wr = WorkflowResult(
            workflow_name="feature_dev",
            goal="add login",
            steps=[],
            artifacts=[],
            memory_snapshot={},
            completed=True,
            total_confidence=0.85,
        )
        assert wr.completed is True
        assert wr.total_confidence == 0.85

    def test_artifacts_aggregation(self):
        art = Artifact(name="foo.py", content="x = 1", artifact_type="code")
        wr = WorkflowResult(
            workflow_name="f",
            goal="g",
            steps=[],
            artifacts=[art],
            memory_snapshot={},
            completed=True,
            total_confidence=1.0,
        )
        assert len(wr.artifacts) == 1
