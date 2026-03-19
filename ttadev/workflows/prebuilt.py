"""Prebuilt workflow definitions for common TTA.dev use cases."""

from ttadev.workflows.definition import MemoryConfig, WorkflowDefinition, WorkflowStep

feature_dev_workflow = WorkflowDefinition(
    name="feature_dev",
    description=(
        "Implement a feature end-to-end: code → tests → security review → commit → pull request"
    ),
    steps=[
        WorkflowStep(agent="developer", gate=True),
        WorkflowStep(agent="qa", gate=True),
        WorkflowStep(agent="security", gate=True),
        WorkflowStep(agent="git", gate=True),
        WorkflowStep(agent="github", gate=True),
    ],
    memory_config=MemoryConfig(flush_to_persistent=True),
)
