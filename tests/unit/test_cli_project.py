"""Unit tests for T1–T5: tta project CLI subcommands."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def _run(args: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "ttadev.cli", *args],
        capture_output=True,
        text=True,
        cwd=str(cwd) if cwd else None,
    )


# ---------------------------------------------------------------------------
# T1 — dispatcher
# ---------------------------------------------------------------------------


class TestDispatcher:
    def test_help_exits_zero(self):
        r = _run(["--help"])
        assert r.returncode == 0

    def test_help_lists_project_subcommand(self):
        r = _run(["--help"])
        assert "project" in r.stdout

    def test_project_help_lists_join_list_show(self):
        r = _run(["project", "--help"])
        assert r.returncode == 0
        assert "join" in r.stdout
        assert "list" in r.stdout
        assert "show" in r.stdout


# ---------------------------------------------------------------------------
# T2 — tta project join
# ---------------------------------------------------------------------------


class TestProjectJoin:
    def test_creates_project_file(self, tmp_path):
        r = _run(["--data-dir", str(tmp_path), "project", "join", "alpha"])
        assert r.returncode == 0
        assert (tmp_path / "projects" / "alpha.json").exists()

    def test_prints_joined_message(self, tmp_path):
        r = _run(["--data-dir", str(tmp_path), "project", "join", "beta"])
        assert "beta" in r.stdout

    def test_prints_export_line(self, tmp_path):
        r = _run(["--data-dir", str(tmp_path), "project", "join", "gamma"])
        assert "TTA_PROJECT_ID" in r.stdout

    def test_writes_current_project_file(self, tmp_path):
        _run(["--data-dir", str(tmp_path), "project", "join", "delta"])
        current = tmp_path / "current_project"
        assert current.exists()
        assert current.read_text().strip() != ""

    def test_idempotent_join(self, tmp_path):
        _run(["--data-dir", str(tmp_path), "project", "join", "epsilon"])
        r = _run(["--data-dir", str(tmp_path), "project", "join", "epsilon"])
        assert r.returncode == 0


# ---------------------------------------------------------------------------
# T3 — tta project list
# ---------------------------------------------------------------------------


class TestProjectList:
    def test_empty_state_message(self, tmp_path):
        r = _run(["--data-dir", str(tmp_path), "project", "list"])
        assert r.returncode == 0
        assert "No projects" in r.stdout

    def test_shows_created_projects(self, tmp_path):
        _run(["--data-dir", str(tmp_path), "project", "join", "zeta"])
        _run(["--data-dir", str(tmp_path), "project", "join", "eta"])
        r = _run(["--data-dir", str(tmp_path), "project", "list"])
        assert "zeta" in r.stdout
        assert "eta" in r.stdout


# ---------------------------------------------------------------------------
# T4 — tta project show
# ---------------------------------------------------------------------------


class TestProjectShow:
    def test_shows_project_details(self, tmp_path):
        _run(["--data-dir", str(tmp_path), "project", "join", "theta"])
        r = _run(["--data-dir", str(tmp_path), "project", "show", "theta"])
        assert r.returncode == 0
        assert "theta" in r.stdout

    def test_unknown_project_exits_1(self, tmp_path):
        r = _run(["--data-dir", str(tmp_path), "project", "show", "nonexistent"])
        assert r.returncode == 1
        assert "nonexistent" in r.stderr or "nonexistent" in r.stdout
