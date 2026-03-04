"""Tests for DoltDiffPrimitive."""

from __future__ import annotations

import pytest

from tta_dolt_primitives import DiffInput, DoltDiffPrimitive


@pytest.mark.asyncio
async def test_diff_two_universes(dolt_config, workflow_context, mock_dolt_run):
    """Diff returns rows that differ between branches."""
    csv_output = "diff_type,player_id,emotional_intelligence\nmodified,player-42,0.8\n"
    mock_dolt_run.side_effect = [
        ("character_state\nchoices", "", 0),  # dolt ls
        (csv_output, "", 0),  # dolt diff character_state
        ("", "", 0),  # dolt diff choices (no changes)
    ]

    primitive = DoltDiffPrimitive(dolt_config)
    result = await primitive.execute(
        DiffInput(from_branch="main", to_branch="player-42/brave-choice"),
        workflow_context,
    )

    assert result.from_branch == "main"
    assert result.to_branch == "player-42/brave-choice"
    assert len(result.rows) == 1
    assert result.rows[0].table == "character_state"
    assert result.rows[0].diff_type == "modified"
    assert result.summary["character_state"] == 1


@pytest.mark.asyncio
async def test_diff_specific_tables(dolt_config, workflow_context, mock_dolt_run):
    """Diff with table filter only diffs specified tables."""
    mock_dolt_run.return_value = ("", "", 0)  # no changes

    primitive = DoltDiffPrimitive(dolt_config)
    result = await primitive.execute(
        DiffInput(
            from_branch="main",
            to_branch="player-42/brave-choice",
            tables=["emotional_history"],
        ),
        workflow_context,
    )

    assert result.tables == ["emotional_history"]
    assert result.rows == []
    assert result.summary == {}


@pytest.mark.asyncio
async def test_diff_no_divergence(dolt_config, workflow_context, mock_dolt_run):
    """Diff of identical branches returns empty result."""
    mock_dolt_run.side_effect = [
        ("scenes", "", 0),  # dolt ls
        ("", "", 0),  # dolt diff scenes — no output
    ]

    primitive = DoltDiffPrimitive(dolt_config)
    result = await primitive.execute(
        DiffInput(from_branch="main", to_branch="main"),
        workflow_context,
    )

    assert result.rows == []
    assert result.summary == {}
