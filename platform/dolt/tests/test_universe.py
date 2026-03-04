"""Tests for DoltUniversePrimitive."""

from __future__ import annotations

import pytest

from tta_dolt_primitives import BranchOperation, DoltUniversePrimitive, UniverseInput


@pytest.mark.asyncio
async def test_list_branches(dolt_config, workflow_context, mock_dolt_run):
    """List returns current branch and all branches."""
    mock_dolt_run.return_value = ("* main\n  player-42/brave-choice", "", 0)

    primitive = DoltUniversePrimitive(dolt_config)
    result = await primitive.execute(
        UniverseInput(operation=BranchOperation.LIST),
        workflow_context,
    )

    assert result.success
    assert result.current_branch == "main"
    assert len(result.branches) == 2
    assert result.branches[0].is_current is True
    assert result.branches[1].name == "player-42/brave-choice"


@pytest.mark.asyncio
async def test_current_branch(dolt_config, workflow_context, mock_dolt_run):
    """Current returns the active branch name."""
    mock_dolt_run.return_value = ("main", "", 0)

    primitive = DoltUniversePrimitive(dolt_config)
    result = await primitive.execute(
        UniverseInput(operation=BranchOperation.CURRENT),
        workflow_context,
    )

    assert result.success
    assert result.current_branch == "main"


@pytest.mark.asyncio
async def test_create_branch(dolt_config, workflow_context, mock_dolt_run):
    """Create forks a new universe branch."""
    # First call: branch create, second call: branch -a for list
    mock_dolt_run.side_effect = [
        ("", "", 0),  # dolt branch player-1/forest
        ("* main\n  player-1/forest", "", 0),  # dolt branch -a
    ]

    primitive = DoltUniversePrimitive(dolt_config)
    result = await primitive.execute(
        UniverseInput(operation=BranchOperation.CREATE, name="player-1/forest"),
        workflow_context,
    )

    assert result.success
    assert "player-1/forest" in [b.name for b in result.branches]


@pytest.mark.asyncio
async def test_create_requires_name(dolt_config, workflow_context):
    """Create raises ValueError when name is missing."""
    primitive = DoltUniversePrimitive(dolt_config)

    with pytest.raises(ValueError, match="Branch name required"):
        await primitive.execute(
            UniverseInput(operation=BranchOperation.CREATE),
            workflow_context,
        )


@pytest.mark.asyncio
async def test_delete_branch(dolt_config, workflow_context, mock_dolt_run):
    """Delete removes a universe branch."""
    mock_dolt_run.side_effect = [
        ("", "", 0),  # dolt branch -d
        ("* main", "", 0),  # dolt branch -a
    ]

    primitive = DoltUniversePrimitive(dolt_config)
    result = await primitive.execute(
        UniverseInput(operation=BranchOperation.DELETE, name="player-1/forest"),
        workflow_context,
    )

    assert result.success
    assert result.message == "Universe 'player-1/forest' deleted"


@pytest.mark.asyncio
async def test_checkout_failure(dolt_config, workflow_context, mock_dolt_run):
    """Checkout failure is reflected in result."""
    mock_dolt_run.side_effect = [
        ("", "branch 'nonexistent' not found", 1),  # checkout fails
        ("* main", "", 0),  # branch -a still works
    ]

    primitive = DoltUniversePrimitive(dolt_config)
    result = await primitive.execute(
        UniverseInput(operation=BranchOperation.CHECKOUT, name="nonexistent"),
        workflow_context,
    )

    assert not result.success
    assert "not found" in result.message
