"""Tests for prebuilt workflows — Task T8."""

from ttadev.workflows.definition import WorkflowDefinition
from ttadev.workflows.prebuilt import feature_dev_workflow


class TestFeatureDevWorkflow:
    def test_is_workflow_definition(self):
        assert isinstance(feature_dev_workflow, WorkflowDefinition)

    def test_name(self):
        assert feature_dev_workflow.name == "feature_dev"

    def test_has_five_steps(self):
        assert len(feature_dev_workflow.steps) == 5

    def test_step_agents(self):
        agents = [s.agent for s in feature_dev_workflow.steps]
        assert agents == ["developer", "qa", "security", "git", "github"]

    def test_all_gates_enabled(self):
        assert all(s.gate for s in feature_dev_workflow.steps)

    def test_flush_to_persistent_true(self):
        assert feature_dev_workflow.memory_config.flush_to_persistent is True

    def test_all_agents_registered(self):
        import ttadev.agents  # noqa: F401 — triggers agent registration
        from ttadev.agents.registry import get_registry

        registry = get_registry()
        for step in feature_dev_workflow.steps:
            assert registry.get(step.agent) is not None, f"Agent '{step.agent}' not in registry"
