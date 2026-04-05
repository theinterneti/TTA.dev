"""Unit tests for pre-built workflow definitions — GitHub issue #300.

Covers workflow registration, step structure, and discoverability via the
``tta workflow list`` CLI command.

Pattern: AAA (Arrange / Act / Assert) throughout.
"""

from __future__ import annotations

import pytest

from ttadev.workflows.prebuilt import (
    ALL_WORKFLOWS,
    bugfix_workflow,
    code_review_workflow,
    deploy_workflow,
    refactor_workflow,
)

# ---------------------------------------------------------------------------
# ALL_WORKFLOWS registry
# ---------------------------------------------------------------------------


def test_all_workflows_contains_five_entries() -> None:
    """ALL_WORKFLOWS should have exactly 5 entries (feature_dev + 4 new).

    Arrange: import ALL_WORKFLOWS from prebuilt module
    Act:     check its length
    Assert:  len == 5
    """
    assert len(ALL_WORKFLOWS) == 5


def test_all_workflows_have_unique_names() -> None:
    """Every workflow in ALL_WORKFLOWS must have a distinct name.

    Arrange: collect workflow names
    Act:     compare count of names to count of unique names
    Assert:  no duplicates
    """
    names = [wf.name for wf in ALL_WORKFLOWS]
    assert len(names) == len(set(names)), f"Duplicate workflow names found: {names}"


def test_workflow_list_includes_new_workflows() -> None:
    """ALL_WORKFLOWS must include bugfix, code_review, refactor, and deploy.

    Arrange: collect workflow names from ALL_WORKFLOWS
    Act:     check presence of each new workflow name
    Assert:  all four names present
    """
    names = [wf.name for wf in ALL_WORKFLOWS]
    assert "bugfix" in names
    assert "code_review" in names
    assert "refactor" in names
    assert "deploy" in names


def test_workflow_list_includes_feature_dev() -> None:
    """The original feature_dev workflow must still be in ALL_WORKFLOWS.

    Arrange: collect names
    Act:     membership check
    Assert:  feature_dev present
    """
    names = [wf.name for wf in ALL_WORKFLOWS]
    assert "feature_dev" in names


# ---------------------------------------------------------------------------
# Individual workflow: bugfix
# ---------------------------------------------------------------------------


def test_bugfix_workflow_name() -> None:
    assert bugfix_workflow.name == "bugfix"


def test_bugfix_workflow_has_correct_step_count() -> None:
    """bugfix must have at least 3 steps.

    Arrange: bugfix_workflow fixture
    Act:     measure step count
    Assert:  >= 3
    """
    assert len(bugfix_workflow.steps) >= 3


def test_bugfix_workflow_first_step_is_developer() -> None:
    """bugfix step 0 must use the developer agent.

    Arrange: bugfix_workflow
    Act:     inspect steps[0].agent
    Assert:  == "developer"
    """
    assert bugfix_workflow.steps[0].agent == "developer"


def test_bugfix_workflow_has_qa_step() -> None:
    agents = [s.agent for s in bugfix_workflow.steps]
    assert "qa" in agents


def test_bugfix_workflow_has_git_step() -> None:
    agents = [s.agent for s in bugfix_workflow.steps]
    assert "git" in agents


def test_bugfix_workflow_description_is_non_empty() -> None:
    assert bugfix_workflow.description.strip() != ""


def test_bugfix_workflow_flushes_to_persistent() -> None:
    assert bugfix_workflow.memory_config.flush_to_persistent is True


# ---------------------------------------------------------------------------
# Individual workflow: code_review
# ---------------------------------------------------------------------------


def test_code_review_workflow_name() -> None:
    assert code_review_workflow.name == "code_review"


def test_code_review_workflow_has_at_least_three_steps() -> None:
    assert len(code_review_workflow.steps) >= 3


def test_code_review_workflow_first_step_is_developer() -> None:
    assert code_review_workflow.steps[0].agent == "developer"


def test_code_review_workflow_has_security_step() -> None:
    agents = [s.agent for s in code_review_workflow.steps]
    assert "security" in agents


def test_code_review_workflow_is_ephemeral() -> None:
    """code_review is designed for single-session use; memory should NOT be flushed."""
    assert code_review_workflow.memory_config.flush_to_persistent is False


def test_code_review_workflow_description_is_non_empty() -> None:
    assert code_review_workflow.description.strip() != ""


# ---------------------------------------------------------------------------
# Individual workflow: refactor
# ---------------------------------------------------------------------------


def test_refactor_workflow_name() -> None:
    assert refactor_workflow.name == "refactor"


def test_refactor_workflow_has_at_least_three_steps() -> None:
    assert len(refactor_workflow.steps) >= 3


def test_refactor_workflow_first_step_is_developer() -> None:
    assert refactor_workflow.steps[0].agent == "developer"


def test_refactor_workflow_has_qa_step() -> None:
    agents = [s.agent for s in refactor_workflow.steps]
    assert "qa" in agents


def test_refactor_workflow_has_git_step() -> None:
    agents = [s.agent for s in refactor_workflow.steps]
    assert "git" in agents


def test_refactor_workflow_flushes_to_persistent() -> None:
    assert refactor_workflow.memory_config.flush_to_persistent is True


def test_refactor_workflow_description_is_non_empty() -> None:
    assert refactor_workflow.description.strip() != ""


# ---------------------------------------------------------------------------
# Individual workflow: deploy
# ---------------------------------------------------------------------------


def test_deploy_workflow_name() -> None:
    assert deploy_workflow.name == "deploy"


def test_deploy_workflow_has_at_least_four_steps() -> None:
    assert len(deploy_workflow.steps) >= 4


def test_deploy_workflow_first_step_is_developer() -> None:
    assert deploy_workflow.steps[0].agent == "developer"


def test_deploy_workflow_has_security_step() -> None:
    agents = [s.agent for s in deploy_workflow.steps]
    assert "security" in agents


def test_deploy_workflow_has_qa_step() -> None:
    agents = [s.agent for s in deploy_workflow.steps]
    assert "qa" in agents


def test_deploy_workflow_flushes_to_persistent() -> None:
    assert deploy_workflow.memory_config.flush_to_persistent is True


def test_deploy_workflow_description_is_non_empty() -> None:
    assert deploy_workflow.description.strip() != ""


# ---------------------------------------------------------------------------
# Structural invariants across ALL_WORKFLOWS
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("wf", ALL_WORKFLOWS)
def test_every_workflow_has_a_name(wf) -> None:  # type: ignore[no-untyped-def]
    """Every workflow must have a non-empty name."""
    assert wf.name.strip() != ""


@pytest.mark.parametrize("wf", ALL_WORKFLOWS)
def test_every_workflow_has_a_description(wf) -> None:  # type: ignore[no-untyped-def]
    """Every workflow must have a non-empty description."""
    assert wf.description.strip() != ""


@pytest.mark.parametrize("wf", ALL_WORKFLOWS)
def test_every_workflow_has_at_least_one_step(wf) -> None:  # type: ignore[no-untyped-def]
    """Every workflow must define at least one step."""
    assert len(wf.steps) >= 1


@pytest.mark.parametrize("wf", ALL_WORKFLOWS)
def test_every_step_has_a_non_empty_agent(wf) -> None:  # type: ignore[no-untyped-def]
    """Every WorkflowStep within every workflow must reference a non-empty agent name."""
    for step in wf.steps:
        assert step.agent.strip() != "", f"Empty agent name in workflow '{wf.name}'"


# ---------------------------------------------------------------------------
# CLI discoverability — _get_workflows() must surface new workflows
# ---------------------------------------------------------------------------


def test_cli_get_workflows_includes_all_prebuilt() -> None:
    """_get_workflows() must expose all workflows from ALL_WORKFLOWS.

    Arrange: import the CLI helper; reset the module-level cache first so the
             lazy initialiser runs fresh.
    Act:     call _get_workflows()
    Assert:  all five workflow names are present
    """
    import ttadev.cli.workflow as wf_module

    # Reset the module-level cache so lazy init re-runs cleanly.
    wf_module._WORKFLOWS.clear()

    workflows = wf_module._get_workflows()

    expected_names = {"feature_dev", "bugfix", "code_review", "refactor", "deploy"}
    assert expected_names <= set(workflows.keys()), (
        f"Missing workflows: {expected_names - set(workflows.keys())}"
    )


def test_cli_list_output_includes_new_workflows(capsys: pytest.CaptureFixture[str]) -> None:
    """``tta workflow list`` output must contain all new workflow names.

    Arrange: build args namespace for the list subcommand
    Act:     call handle_workflow_command
    Assert:  each new workflow name appears in stdout
    """
    import argparse

    import ttadev.cli.workflow as wf_module
    from ttadev.cli.workflow import handle_workflow_command

    # Reset cache so lazy init fires.
    wf_module._WORKFLOWS.clear()

    args = argparse.Namespace(workflow_command="list")
    rc = handle_workflow_command(args, data_dir=None)  # type: ignore[arg-type]

    assert rc == 0
    out = capsys.readouterr().out
    for name in ("bugfix", "code_review", "refactor", "deploy"):
        assert name in out, f"Expected '{name}' in `tta workflow list` output"


def test_cli_show_bugfix_lists_agents(capsys: pytest.CaptureFixture[str]) -> None:
    """``tta workflow show bugfix`` must list all agent names for that workflow.

    Arrange: build show args for bugfix
    Act:     call handle_workflow_command
    Assert:  exit 0, expected agent names in stdout
    """
    import argparse

    import ttadev.cli.workflow as wf_module
    from ttadev.cli.workflow import handle_workflow_command

    wf_module._WORKFLOWS.clear()

    args = argparse.Namespace(workflow_command="show", name="bugfix")
    rc = handle_workflow_command(args, data_dir=None)  # type: ignore[arg-type]

    assert rc == 0
    out = capsys.readouterr().out
    for agent in ("developer", "qa", "security", "git"):
        assert agent in out, f"Expected agent '{agent}' in `tta workflow show bugfix` output"
