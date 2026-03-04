"""Tests for DoltCommitPrimitive."""

from __future__ import annotations

import pytest

from tta_dolt_primitives import CommitInput, DoltCommitPrimitive


@pytest.mark.asyncio
async def test_commit_success(dolt_config, workflow_context, mock_dolt_run):
    """Successful commit returns commit hash."""
    mock_dolt_run.side_effect = [
        ("", "", 0),  # dolt add -A
        ("", "", 0),  # dolt commit -m ...
        ("abc1234 Player chose the forest path", "", 0),  # dolt log --oneline -1
    ]

    primitive = DoltCommitPrimitive(dolt_config)
    result = await primitive.execute(
        CommitInput(message="Player chose the forest path", author="player-42"),
        workflow_context,
    )

    assert result.success
    assert result.commit is not None
    assert result.commit.hash == "abc1234"
    assert result.commit.message == "Player chose the forest path"


@pytest.mark.asyncio
async def test_commit_nothing_to_commit(dolt_config, workflow_context, mock_dolt_run):
    """Nothing to commit is treated as success with no commit object."""
    mock_dolt_run.side_effect = [
        ("", "", 0),  # dolt add -A
        ("", "nothing to commit", 1),  # dolt commit fails gracefully
    ]

    primitive = DoltCommitPrimitive(dolt_config)
    result = await primitive.execute(
        CommitInput(message="Empty state"),
        workflow_context,
    )

    assert result.success
    assert result.commit is None
    assert "Nothing to commit" in result.message


@pytest.mark.asyncio
async def test_commit_specific_tables(dolt_config, workflow_context, mock_dolt_run):
    """Commit with specific tables stages only those tables."""
    mock_dolt_run.side_effect = [
        ("", "", 0),  # dolt add character_state
        ("", "", 0),  # dolt add choices
        ("", "", 0),  # dolt commit -m ...
        ("def5678 Updated character state", "", 0),  # dolt log
    ]

    primitive = DoltCommitPrimitive(dolt_config)
    result = await primitive.execute(
        CommitInput(
            message="Updated character state",
            tables=["character_state", "choices"],
        ),
        workflow_context,
    )

    assert result.success
    assert result.commit is not None
    assert result.commit.hash == "def5678"


@pytest.mark.asyncio
async def test_commit_stage_failure(dolt_config, workflow_context, mock_dolt_run):
    """Stage failure returns failed result immediately."""
    mock_dolt_run.return_value = ("", "table not found: bad_table", 1)

    primitive = DoltCommitPrimitive(dolt_config)
    result = await primitive.execute(
        CommitInput(message="Should fail", tables=["bad_table"]),
        workflow_context,
    )

    assert not result.success
    assert result.commit is None
