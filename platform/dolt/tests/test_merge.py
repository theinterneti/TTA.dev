"""Tests for DoltMergePrimitive."""

from __future__ import annotations

import pytest

from tta_dolt_primitives import DoltMergePrimitive, MergeInput


@pytest.mark.asyncio
async def test_merge_success(dolt_config, workflow_context, mock_dolt_run):
    """Successful merge returns commit hash."""
    mock_dolt_run.side_effect = [
        ("", "", 0),  # dolt checkout main
        ("", "", 0),  # dolt merge player-42/brave-choice
        ("abc1234 Merge brave-choice into main", "", 0),  # dolt log
    ]

    primitive = DoltMergePrimitive(dolt_config)
    result = await primitive.execute(
        MergeInput(
            source_branch="player-42/brave-choice",
            target_branch="main",
            message="The brave path becomes canon",
        ),
        workflow_context,
    )

    assert result.success
    assert result.commit_hash == "abc1234"
    assert result.source_branch == "player-42/brave-choice"
    assert result.target_branch == "main"


@pytest.mark.asyncio
async def test_merge_squash(dolt_config, workflow_context, mock_dolt_run):
    """Squash merge passes --squash to dolt."""
    mock_dolt_run.side_effect = [
        ("", "", 0),  # checkout
        ("", "", 0),  # merge --squash
        ("bcd2345 squash", "", 0),  # log
    ]

    primitive = DoltMergePrimitive(dolt_config)
    result = await primitive.execute(
        MergeInput(source_branch="player-1/forest", squash=True),
        workflow_context,
    )

    # Verify --squash was in the merge call
    merge_call_args = mock_dolt_run.call_args_list[1][0]
    assert "--squash" in merge_call_args
    assert result.success


@pytest.mark.asyncio
async def test_merge_conflict(dolt_config, workflow_context, mock_dolt_run):
    """Merge conflict returns failure with conflict details."""
    mock_dolt_run.side_effect = [
        ("", "", 0),  # checkout
        ("", "conflict: character_state has 2 conflicts", 1),  # merge fails
    ]

    primitive = DoltMergePrimitive(dolt_config)
    result = await primitive.execute(
        MergeInput(source_branch="player-1/alt-path"),
        workflow_context,
    )

    assert not result.success
    assert len(result.conflicts) > 0


@pytest.mark.asyncio
async def test_merge_checkout_failure(dolt_config, workflow_context, mock_dolt_run):
    """Checkout failure aborts merge before attempting it."""
    mock_dolt_run.return_value = ("", "branch 'nonexistent' not found", 1)

    primitive = DoltMergePrimitive(dolt_config)
    result = await primitive.execute(
        MergeInput(source_branch="player-1/alt", target_branch="nonexistent"),
        workflow_context,
    )

    assert not result.success
    assert "Failed to checkout" in result.message
