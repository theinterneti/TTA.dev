"""Smoke tests for public demo scripts."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize(
    ("script_path", "success_marker"),
    [
        ("examples/demo_workflow.py", "🎉 Demo Complete!"),
        ("ttadev/hello_world.py", "✅ Workflow complete!"),
    ],
)
def test_public_demo_script_runs_successfully(script_path: str, success_marker: str) -> None:
    """Ensure each supported public demo script still runs successfully."""
    # Arrange
    env = os.environ.copy()
    existing_pythonpath = env.get("PYTHONPATH")
    env["PYTHONPATH"] = (
        str(REPO_ROOT)
        if not existing_pythonpath
        else f"{REPO_ROOT}{os.pathsep}{existing_pythonpath}"
    )

    # Act
    completed = subprocess.run(
        [sys.executable, script_path],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=20,
        check=False,
        env=env,
    )

    # Assert
    assert completed.returncode == 0, completed.stderr
    assert success_marker in completed.stdout
