"""Unit tests for the ``tta control`` CLI surface."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def _run(
    args: list[str], tmp_path: Path, env: dict[str, str] | None = None
) -> subprocess.CompletedProcess:
    repo_root = Path(__file__).resolve().parents[2]
    merged_env = os.environ.copy()
    merged_env["PYTHONPATH"] = f"{repo_root}:{merged_env.get('PYTHONPATH', '')}".rstrip(":")
    if env:
        merged_env.update(env)
    return subprocess.run(
        [sys.executable, "-m", "ttadev.cli", "--data-dir", str(tmp_path), *args],
        capture_output=True,
        text=True,
        env=merged_env,
        cwd=repo_root,
    )


def _parse_prefixed_value(output: str, prefix: str) -> str:
    for line in output.splitlines():
        if line.startswith(prefix):
            return line.split(":", 1)[1].strip()
    raise AssertionError(f"Missing line with prefix {prefix!r} in output: {output}")


def test_control_help_lists_task_and_run(tmp_path: Path) -> None:
    result = _run(["control", "--help"], tmp_path)
    assert result.returncode == 0
    assert "task" in result.stdout
    assert "run" in result.stdout


def test_task_create_and_list(tmp_path: Path) -> None:
    created = _run(
        [
            "control",
            "task",
            "create",
            "Build L0 queue",
            "--description",
            "Create the first local queue",
            "--project",
            "alpha",
        ],
        tmp_path,
    )
    assert created.returncode == 0
    assert "Task:" in created.stdout

    listed = _run(["control", "task", "list"], tmp_path)
    assert listed.returncode == 0
    assert "Build L0 queue" in listed.stdout
    assert "alpha" in listed.stdout


def test_task_show_and_claim_then_complete(tmp_path: Path) -> None:
    created = _run(["control", "task", "create", "Claim me"], tmp_path)
    task_id = _parse_prefixed_value(created.stdout, "Task")

    shown = _run(["control", "task", "show", task_id], tmp_path)
    assert shown.returncode == 0
    assert task_id in shown.stdout

    claimed = _run(
        ["control", "task", "claim", task_id, "--role", "developer"],
        tmp_path,
        env={"TTA_AGENT_ID": "agent-123", "TTA_AGENT_TOOL": "copilot"},
    )
    assert claimed.returncode == 0
    run_id = _parse_prefixed_value(claimed.stdout, "Run")

    runs = _run(["control", "run", "list"], tmp_path)
    assert runs.returncode == 0
    assert run_id in runs.stdout

    completed = _run(
        ["control", "run", "complete", run_id, "--summary", "done"],
        tmp_path,
    )
    assert completed.returncode == 0

    shown_again = _run(["control", "task", "show", task_id], tmp_path)
    assert shown_again.returncode == 0
    assert "completed" in shown_again.stdout
