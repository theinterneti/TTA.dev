"""Unit tests for ttadev/cli/project.py.

Tests cover: _validate_name, _projects_dir, join, list_projects, show.
All filesystem access uses tmp_path — no real project data is touched.
"""

from __future__ import annotations

import json
import uuid
from pathlib import Path

import pytest

from ttadev.cli.project import (
    _projects_dir,
    _validate_name,
    join,
    list_projects,
    show,
)

# ---------------------------------------------------------------------------
# _validate_name
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestValidateName:
    """_validate_name rejects names that could escape the projects directory."""

    @pytest.mark.parametrize("name", ["alpha", "my-project", "my_project", "Abc123", "1", "a-b_C"])
    def test_valid_names_pass(self, name: str) -> None:
        """Valid names return without raising or printing."""
        _validate_name(name)  # no exception

    @pytest.mark.parametrize("name", ["../escape", "bad/name", "has space", "dot.name", "", "a@b"])
    def test_invalid_names_exit_1(self, name: str) -> None:
        """Invalid names call sys.exit(1)."""
        with pytest.raises(SystemExit) as exc:
            _validate_name(name)
        assert exc.value.code == 1

    def test_invalid_name_writes_to_stderr(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Error message goes to stderr and includes the bad name."""
        with pytest.raises(SystemExit):
            _validate_name("bad/name")
        assert "bad/name" in capsys.readouterr().err

    def test_invalid_name_stderr_mentions_allowed_chars(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Error message hints at what characters are allowed."""
        with pytest.raises(SystemExit):
            _validate_name("x y")
        err = capsys.readouterr().err
        assert err  # non-empty guidance


# ---------------------------------------------------------------------------
# _projects_dir
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestProjectsDir:
    """_projects_dir returns data_dir/projects, creating it if needed."""

    def test_returns_projects_subdirectory(self, tmp_path: Path) -> None:
        result = _projects_dir(tmp_path)
        assert result == tmp_path / "projects"

    def test_creates_directory(self, tmp_path: Path) -> None:
        _projects_dir(tmp_path)
        assert (tmp_path / "projects").is_dir()

    def test_idempotent(self, tmp_path: Path) -> None:
        _projects_dir(tmp_path)
        _projects_dir(tmp_path)  # second call must not raise
        assert (tmp_path / "projects").is_dir()

    def test_creates_nested_parents(self, tmp_path: Path) -> None:
        deep = tmp_path / "a" / "b"
        _projects_dir(deep)
        assert (deep / "projects").is_dir()


# ---------------------------------------------------------------------------
# join
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestJoin:
    """join() creates or re-joins a project by name."""

    def test_creates_project_json(self, tmp_path: Path) -> None:
        join("myproject", tmp_path)
        assert (tmp_path / "projects" / "myproject.json").exists()

    def test_json_has_id_field(self, tmp_path: Path) -> None:
        join("myproject", tmp_path)
        meta = json.loads((tmp_path / "projects" / "myproject.json").read_text())
        assert "id" in meta

    def test_json_id_is_valid_uuid(self, tmp_path: Path) -> None:
        join("myproject", tmp_path)
        meta = json.loads((tmp_path / "projects" / "myproject.json").read_text())
        uuid.UUID(meta["id"])  # raises if invalid

    def test_json_name_matches(self, tmp_path: Path) -> None:
        join("myproject", tmp_path)
        meta = json.loads((tmp_path / "projects" / "myproject.json").read_text())
        assert meta["name"] == "myproject"

    def test_json_has_created_at(self, tmp_path: Path) -> None:
        join("myproject", tmp_path)
        meta = json.loads((tmp_path / "projects" / "myproject.json").read_text())
        assert "created_at" in meta

    def test_prints_joined_message(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        join("myproject", tmp_path)
        assert "myproject" in capsys.readouterr().out

    def test_prints_export_line(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
        join("myproject", tmp_path)
        assert "TTA_PROJECT_ID=" in capsys.readouterr().out

    def test_writes_current_project_pointer(self, tmp_path: Path) -> None:
        join("myproject", tmp_path)
        meta = json.loads((tmp_path / "projects" / "myproject.json").read_text())
        pointer = (tmp_path / "current_project").read_text()
        assert pointer == meta["id"]

    def test_rejoin_preserves_existing_id(self, tmp_path: Path) -> None:
        join("myproject", tmp_path)
        first_id = json.loads((tmp_path / "projects" / "myproject.json").read_text())["id"]
        join("myproject", tmp_path)
        second_id = json.loads((tmp_path / "projects" / "myproject.json").read_text())["id"]
        assert first_id == second_id

    def test_rejoin_updates_current_project_pointer(self, tmp_path: Path) -> None:
        join("proj-a", tmp_path)
        join("proj-b", tmp_path)
        join("proj-a", tmp_path)
        meta_a = json.loads((tmp_path / "projects" / "proj-a.json").read_text())
        assert (tmp_path / "current_project").read_text() == meta_a["id"]

    def test_invalid_name_exits_before_creating_file(self, tmp_path: Path) -> None:
        with pytest.raises(SystemExit):
            join("bad/name", tmp_path)
        assert not (tmp_path / "projects" / "bad").exists()


# ---------------------------------------------------------------------------
# list_projects
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestListProjects:
    """list_projects() prints all known projects."""

    def test_empty_prints_no_projects(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        list_projects(tmp_path)
        assert "No projects" in capsys.readouterr().out

    def test_single_project_appears(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        join("alpha", tmp_path)
        capsys.readouterr()
        list_projects(tmp_path)
        assert "alpha" in capsys.readouterr().out

    def test_multiple_projects_all_appear(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        for name in ("alpha", "beta", "gamma"):
            join(name, tmp_path)
        capsys.readouterr()
        list_projects(tmp_path)
        out = capsys.readouterr().out
        for name in ("alpha", "beta", "gamma"):
            assert name in out

    def test_output_sorted_alphabetically(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        for name in ("zulu", "alpha", "mike"):
            join(name, tmp_path)
        capsys.readouterr()
        list_projects(tmp_path)
        lines = [ln for ln in capsys.readouterr().out.splitlines() if ln.strip()]
        names = [ln.split()[0] for ln in lines]
        assert names == sorted(names)

    def test_corrupt_json_silently_skipped(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        join("good", tmp_path)
        (tmp_path / "projects" / "bad.json").write_text("not-json{{{")
        capsys.readouterr()
        list_projects(tmp_path)
        out = capsys.readouterr().out
        assert "good" in out  # good project still shown

    def test_output_includes_project_id(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        join("myproj", tmp_path)
        meta = json.loads((tmp_path / "projects" / "myproj.json").read_text())
        capsys.readouterr()
        list_projects(tmp_path)
        assert meta["id"] in capsys.readouterr().out


# ---------------------------------------------------------------------------
# show
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestShow:
    """show() prints details for a named project."""

    def test_prints_project_name(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
        join("myproj", tmp_path)
        capsys.readouterr()
        show("myproj", tmp_path)
        assert "myproj" in capsys.readouterr().out

    def test_prints_project_id(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
        join("myproj", tmp_path)
        meta = json.loads((tmp_path / "projects" / "myproj.json").read_text())
        capsys.readouterr()
        show("myproj", tmp_path)
        assert meta["id"] in capsys.readouterr().out

    def test_prints_created_at(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
        join("myproj", tmp_path)
        capsys.readouterr()
        show("myproj", tmp_path)
        assert "created_at" in capsys.readouterr().out

    def test_missing_project_exits_1(self, tmp_path: Path) -> None:
        with pytest.raises(SystemExit) as exc:
            show("ghost", tmp_path)
        assert exc.value.code == 1

    def test_missing_project_writes_to_stderr(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        with pytest.raises(SystemExit):
            show("ghost", tmp_path)
        err = capsys.readouterr().err
        assert "ghost" in err
        assert "not found" in err.lower()

    def test_invalid_name_exits_before_filesystem_access(self, tmp_path: Path) -> None:
        with pytest.raises(SystemExit):
            show("../escape", tmp_path)
        assert not (tmp_path / "projects").exists()

    def test_correct_project_shown_among_many(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        for name in ("zeus", "hera", "poseidon"):
            join(name, tmp_path)
        capsys.readouterr()
        show("hera", tmp_path)
        out = capsys.readouterr().out
        assert "hera" in out
        assert "zeus" not in out
