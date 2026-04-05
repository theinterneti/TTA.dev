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

bugfix_workflow = WorkflowDefinition(
    name="bugfix",
    description="Reproduce → diagnose → fix → test → commit",
    steps=[
        WorkflowStep(agent="developer", gate=True),  # reproduce + fix
        WorkflowStep(agent="qa", gate=True),  # verify fix with tests
        WorkflowStep(agent="security", gate=False),  # optional security check
        WorkflowStep(agent="git", gate=True),  # commit
    ],
    memory_config=MemoryConfig(flush_to_persistent=True),
)

code_review_workflow = WorkflowDefinition(
    name="code_review",
    description="Analyze PR diff → security → style → generate review comments",
    steps=[
        WorkflowStep(agent="developer", gate=False),  # understand the diff
        WorkflowStep(agent="security", gate=True),  # security review
        WorkflowStep(agent="qa", gate=False),  # quality/style review
    ],
    memory_config=MemoryConfig(flush_to_persistent=False),  # ephemeral
)

refactor_workflow = WorkflowDefinition(
    name="refactor",
    description="Identify code smells → refactor → verify behavior unchanged → test",
    steps=[
        WorkflowStep(agent="developer", gate=True),  # plan + execute refactor
        WorkflowStep(agent="qa", gate=True),  # run tests, verify no regression
        WorkflowStep(agent="git", gate=True),  # commit
    ],
    memory_config=MemoryConfig(flush_to_persistent=True),
)

deploy_workflow = WorkflowDefinition(
    name="deploy",
    description="Build → test → security scan → deploy to staging → verify",
    steps=[
        WorkflowStep(agent="developer", gate=True),  # build
        WorkflowStep(agent="qa", gate=True),  # full test run
        WorkflowStep(agent="security", gate=True),  # security scan before deploy
        WorkflowStep(agent="git", gate=True),  # tag release
    ],
    memory_config=MemoryConfig(flush_to_persistent=True),
)

ALL_WORKFLOWS: list[WorkflowDefinition] = [
    feature_dev_workflow,
    bugfix_workflow,
    code_review_workflow,
    refactor_workflow,
    deploy_workflow,
]
