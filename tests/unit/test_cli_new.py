"""Unit tests for `tta new <app-name>` CLI command.

Pattern: AAA (Arrange / Act / Assert).
Isolation: all filesystem I/O uses the ``tmp_path`` pytest fixture.
No real ``git init`` is ever executed — mocked via ``unittest.mock``.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from ttadev.cli.new import (
    _git_init,
    _render,
    _write_scaffold,
    cmd_new,
    validate_app_name,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _args(
    name: str = "my-app",
    output_dir: str | None = None,
    no_git: bool = True,
) -> argparse.Namespace:
    """Build a minimal Namespace that mimics parsed CLI args for `tta new`."""
    return argparse.Namespace(name=name, output_dir=output_dir, no_git=no_git)


# ---------------------------------------------------------------------------
# validate_app_name
# ---------------------------------------------------------------------------


class TestValidateAppName:
    """Tests for :func:`validate_app_name`."""

    def test_valid_simple(self) -> None:
        """Plain alphanumeric name is accepted."""
        assert validate_app_name("myapp") is None

    def test_valid_with_hyphens(self) -> None:
        """Hyphens are permitted."""
        assert validate_app_name("my-app") is None

    def test_valid_with_underscores(self) -> None:
        """Underscores are permitted."""
        assert validate_app_name("my_app") is None

    def test_valid_mixed(self) -> None:
        """Mixed alphanumeric, hyphens, and underscores."""
        assert validate_app_name("My-App_123") is None

    def test_valid_starts_with_digit(self) -> None:
        """Names that start with a digit are valid."""
        assert validate_app_name("1app") is None

    def test_invalid_empty(self) -> None:
        """Empty string is rejected."""
        error = validate_app_name("")
        assert error is not None
        assert "empty" in error.lower()

    def test_invalid_space(self) -> None:
        """Names containing spaces are rejected."""
        error = validate_app_name("my app")
        assert error is not None
        assert "Invalid app name" in error

    def test_invalid_dot(self) -> None:
        """Names containing dots are rejected."""
        error = validate_app_name("my.app")
        assert error is not None

    def test_invalid_slash(self) -> None:
        """Names containing slashes are rejected."""
        error = validate_app_name("my/app")
        assert error is not None

    def test_invalid_at_symbol(self) -> None:
        """Names containing @ are rejected."""
        error = validate_app_name("@scope/pkg")
        assert error is not None

    def test_invalid_starts_with_hyphen(self) -> None:
        """Names starting with a hyphen are rejected."""
        error = validate_app_name("-myapp")
        assert error is not None

    def test_error_message_contains_name(self) -> None:
        """Error message includes the offending name for clarity."""
        error = validate_app_name("bad name!")
        assert error is not None
        assert "bad name!" in error


# ---------------------------------------------------------------------------
# _render
# ---------------------------------------------------------------------------


class TestRender:
    """Tests for the :func:`_render` template helper."""

    def test_substitutes_app_name(self) -> None:
        """All occurrences of ``{app_name}`` are replaced."""
        result = _render("Hello {app_name}, welcome to {app_name}!", "cool-app")
        assert result == "Hello cool-app, welcome to cool-app!"

    def test_no_placeholder(self) -> None:
        """Templates without ``{app_name}`` are returned unchanged."""
        result = _render("No placeholder here.", "irrelevant")
        assert result == "No placeholder here."


# ---------------------------------------------------------------------------
# _write_scaffold
# ---------------------------------------------------------------------------


class TestWriteScaffold:
    """Tests for :func:`_write_scaffold` — file creation."""

    def test_creates_expected_files(self, tmp_path: Path) -> None:
        """All four scaffold files are created."""
        app_dir = tmp_path / "my-app"
        _write_scaffold(app_dir, "my-app")

        expected = [
            app_dir / "pyproject.toml",
            app_dir / "README.md",
            app_dir / "main.py",
            app_dir / "tests" / "test_main.py",
        ]
        for f in expected:
            assert f.exists(), f"{f} was not created"

    def test_returns_written_paths(self, tmp_path: Path) -> None:
        """Return value lists every file that was written."""
        app_dir = tmp_path / "my-app"
        written = _write_scaffold(app_dir, "my-app")
        assert len(written) == 4
        for path in written:
            assert path.is_file()

    def test_pyproject_contains_app_name(self, tmp_path: Path) -> None:
        """pyproject.toml has the app name substituted."""
        app_dir = tmp_path / "cool-project"
        _write_scaffold(app_dir, "cool-project")
        content = (app_dir / "pyproject.toml").read_text()
        assert 'name = "cool-project"' in content

    def test_pyproject_contains_ttadev_dependency(self, tmp_path: Path) -> None:
        """pyproject.toml declares ttadev as a dependency."""
        app_dir = tmp_path / "my-app"
        _write_scaffold(app_dir, "my-app")
        content = (app_dir / "pyproject.toml").read_text()
        assert "ttadev" in content

    def test_pyproject_requires_python_312(self, tmp_path: Path) -> None:
        """pyproject.toml pins requires-python to >=3.12."""
        app_dir = tmp_path / "my-app"
        _write_scaffold(app_dir, "my-app")
        content = (app_dir / "pyproject.toml").read_text()
        assert ">=3.12" in content

    def test_readme_contains_app_name(self, tmp_path: Path) -> None:
        """README.md has the app name in the heading."""
        app_dir = tmp_path / "my-app"
        _write_scaffold(app_dir, "my-app")
        content = (app_dir / "README.md").read_text()
        assert "# my-app" in content

    def test_main_py_contains_app_name(self, tmp_path: Path) -> None:
        """main.py references the app name in the docstring and WorkflowContext."""
        app_dir = tmp_path / "my-app"
        _write_scaffold(app_dir, "my-app")
        content = (app_dir / "main.py").read_text()
        assert "my-app" in content

    def test_main_py_imports_lambda_primitive(self, tmp_path: Path) -> None:
        """main.py imports LambdaPrimitive and WorkflowContext."""
        app_dir = tmp_path / "my-app"
        _write_scaffold(app_dir, "my-app")
        content = (app_dir / "main.py").read_text()
        assert "LambdaPrimitive" in content
        assert "WorkflowContext" in content

    def test_main_py_has_async_main(self, tmp_path: Path) -> None:
        """main.py defines an async main() function."""
        app_dir = tmp_path / "my-app"
        _write_scaffold(app_dir, "my-app")
        content = (app_dir / "main.py").read_text()
        assert "async def main()" in content
        assert "asyncio.run(main())" in content

    def test_test_main_py_imports_process(self, tmp_path: Path) -> None:
        """tests/test_main.py imports the process function."""
        app_dir = tmp_path / "my-app"
        _write_scaffold(app_dir, "my-app")
        content = (app_dir / "tests" / "test_main.py").read_text()
        assert "from main import process" in content

    def test_test_main_py_has_asyncio_mark(self, tmp_path: Path) -> None:
        """tests/test_main.py uses @pytest.mark.asyncio."""
        app_dir = tmp_path / "my-app"
        _write_scaffold(app_dir, "my-app")
        content = (app_dir / "tests" / "test_main.py").read_text()
        assert "pytest.mark.asyncio" in content

    def test_tests_directory_created(self, tmp_path: Path) -> None:
        """The tests/ subdirectory is created automatically."""
        app_dir = tmp_path / "my-app"
        _write_scaffold(app_dir, "my-app")
        assert (app_dir / "tests").is_dir()


# ---------------------------------------------------------------------------
# _git_init
# ---------------------------------------------------------------------------


class TestGitInit:
    """Tests for :func:`_git_init`."""

    def test_returns_true_on_success(self, tmp_path: Path) -> None:
        """Returns True when git init exits with code 0."""
        app_dir = tmp_path / "repo"
        app_dir.mkdir()
        mock_result = MagicMock()
        mock_result.returncode = 0
        with patch("ttadev.cli.new.subprocess.run", return_value=mock_result) as mock_run:
            ok = _git_init(app_dir)
        assert ok is True
        mock_run.assert_called_once_with(["git", "init"], cwd=app_dir, capture_output=True)

    def test_returns_false_on_failure(self, tmp_path: Path) -> None:
        """Returns False when git init exits with a non-zero code."""
        app_dir = tmp_path / "repo"
        app_dir.mkdir()
        mock_result = MagicMock()
        mock_result.returncode = 128
        with patch("ttadev.cli.new.subprocess.run", return_value=mock_result):
            ok = _git_init(app_dir)
        assert ok is False


# ---------------------------------------------------------------------------
# cmd_new — happy path
# ---------------------------------------------------------------------------


class TestCmdNewHappyPath:
    """End-to-end tests for :func:`cmd_new` success scenarios."""

    def test_returns_zero_on_success(self, tmp_path: Path) -> None:
        """Exit code is 0 when everything succeeds."""
        args = _args(name="my-app", output_dir=str(tmp_path), no_git=True)
        rc = cmd_new(args)
        assert rc == 0

    def test_creates_app_directory(self, tmp_path: Path) -> None:
        """The app directory is created under output_dir."""
        args = _args(name="hello-world", output_dir=str(tmp_path), no_git=True)
        cmd_new(args)
        assert (tmp_path / "hello-world").is_dir()

    def test_creates_all_expected_files(self, tmp_path: Path) -> None:
        """All four scaffold files are present after cmd_new."""
        args = _args(name="my-app", output_dir=str(tmp_path), no_git=True)
        cmd_new(args)
        app_dir = tmp_path / "my-app"
        for rel in ["pyproject.toml", "README.md", "main.py", "tests/test_main.py"]:
            assert (app_dir / rel).exists(), f"Missing: {rel}"

    def test_output_dir_flag(self, tmp_path: Path) -> None:
        """--output-dir places the app in the specified parent directory."""
        custom_parent = tmp_path / "workspace"
        custom_parent.mkdir()
        args = _args(name="sub-app", output_dir=str(custom_parent), no_git=True)
        cmd_new(args)
        assert (custom_parent / "sub-app").is_dir()

    def test_no_git_skips_git_init(self, tmp_path: Path) -> None:
        """--no-git ensures git init is never called."""
        args = _args(name="my-app", output_dir=str(tmp_path), no_git=True)
        with patch("ttadev.cli.new._git_init") as mock_git:
            cmd_new(args)
        mock_git.assert_not_called()

    def test_git_init_called_by_default(self, tmp_path: Path) -> None:
        """git init is called when --no-git is not set."""
        args = _args(name="my-app", output_dir=str(tmp_path), no_git=False)
        with patch("ttadev.cli.new._git_init", return_value=True) as mock_git:
            rc = cmd_new(args)
        assert rc == 0
        mock_git.assert_called_once()

    def test_prints_success_message(self, tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
        """A success message with the app name is printed to stdout."""
        args = _args(name="my-app", output_dir=str(tmp_path), no_git=True)
        cmd_new(args)
        captured = capsys.readouterr()
        assert "my-app" in captured.out
        assert "✅" in captured.out

    def test_prints_next_steps(self, tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
        """Next steps instructions (cd, uv run) are printed to stdout."""
        args = _args(name="my-app", output_dir=str(tmp_path), no_git=True)
        cmd_new(args)
        captured = capsys.readouterr()
        assert "cd my-app" in captured.out
        assert "uv run python main.py" in captured.out


# ---------------------------------------------------------------------------
# cmd_new — invalid name
# ---------------------------------------------------------------------------


class TestCmdNewInvalidName:
    """Tests for name validation in :func:`cmd_new`."""

    @pytest.mark.parametrize(
        "bad_name",
        [
            "",
            "my app",
            "my.app",
            "my/app",
            "@scope/pkg",
            "-myapp",
            "app name!",
        ],
    )
    def test_invalid_names_return_one(self, bad_name: str, tmp_path: Path) -> None:
        """Invalid app names cause cmd_new to return exit code 1."""
        args = _args(name=bad_name, output_dir=str(tmp_path), no_git=True)
        rc = cmd_new(args)
        assert rc == 1

    def test_invalid_name_prints_to_stderr(
        self, tmp_path: Path, capsys: pytest.CaptureFixture
    ) -> None:
        """An error message is written to stderr for invalid names."""
        args = _args(name="bad name!", output_dir=str(tmp_path), no_git=True)
        cmd_new(args)
        captured = capsys.readouterr()
        assert "error:" in captured.err

    def test_invalid_name_creates_no_directory(self, tmp_path: Path) -> None:
        """No directory is created when the name is invalid."""
        args = _args(name="bad name!", output_dir=str(tmp_path), no_git=True)
        cmd_new(args)
        # No new directories should appear in tmp_path
        assert list(tmp_path.iterdir()) == []


# ---------------------------------------------------------------------------
# cmd_new — existing directory
# ---------------------------------------------------------------------------


class TestCmdNewExistingDirectory:
    """Tests that cmd_new refuses to clobber existing directories."""

    def test_existing_dir_returns_one(self, tmp_path: Path) -> None:
        """Exit code is 1 when the target directory already exists."""
        existing = tmp_path / "my-app"
        existing.mkdir()
        args = _args(name="my-app", output_dir=str(tmp_path), no_git=True)
        rc = cmd_new(args)
        assert rc == 1

    def test_existing_dir_prints_to_stderr(
        self, tmp_path: Path, capsys: pytest.CaptureFixture
    ) -> None:
        """An error message mentioning the directory is written to stderr."""
        existing = tmp_path / "my-app"
        existing.mkdir()
        args = _args(name="my-app", output_dir=str(tmp_path), no_git=True)
        cmd_new(args)
        captured = capsys.readouterr()
        assert "error:" in captured.err
        assert "my-app" in captured.err

    def test_existing_dir_not_modified(self, tmp_path: Path) -> None:
        """Files inside the existing directory are not touched."""
        existing = tmp_path / "my-app"
        existing.mkdir()
        sentinel = existing / "sentinel.txt"
        sentinel.write_text("do not touch", encoding="utf-8")

        args = _args(name="my-app", output_dir=str(tmp_path), no_git=True)
        cmd_new(args)

        assert sentinel.read_text(encoding="utf-8") == "do not touch"


# ---------------------------------------------------------------------------
# cmd_new — file content spot-checks
# ---------------------------------------------------------------------------


class TestCmdNewFileContents:
    """Spot-check the content of every scaffold file written by cmd_new."""

    @pytest.fixture
    def app_dir(self, tmp_path: Path) -> Path:
        """Run cmd_new and return the created app directory."""
        args = _args(name="my-app", output_dir=str(tmp_path), no_git=True)
        cmd_new(args)
        return tmp_path / "my-app"

    def test_pyproject_name(self, app_dir: Path) -> None:
        content = (app_dir / "pyproject.toml").read_text()
        assert 'name = "my-app"' in content

    def test_pyproject_ttadev_dep(self, app_dir: Path) -> None:
        content = (app_dir / "pyproject.toml").read_text()
        assert '"ttadev"' in content

    def test_pyproject_build_system(self, app_dir: Path) -> None:
        content = (app_dir / "pyproject.toml").read_text()
        assert "hatchling" in content

    def test_readme_heading(self, app_dir: Path) -> None:
        content = (app_dir / "README.md").read_text()
        assert "# my-app" in content

    def test_readme_has_quick_start(self, app_dir: Path) -> None:
        content = (app_dir / "README.md").read_text()
        assert "Quick start" in content

    def test_main_py_module_docstring(self, app_dir: Path) -> None:
        content = (app_dir / "main.py").read_text()
        assert "my-app" in content

    def test_main_py_process_function(self, app_dir: Path) -> None:
        content = (app_dir / "main.py").read_text()
        assert "async def process" in content

    def test_main_py_workflow_context_id(self, app_dir: Path) -> None:
        content = (app_dir / "main.py").read_text()
        assert "my-app-run" in content

    def test_test_main_py_assertion(self, app_dir: Path) -> None:
        content = (app_dir / "tests" / "test_main.py").read_text()
        assert "assert isinstance(result, str)" in content
        assert '"input" in result' in content


# ---------------------------------------------------------------------------
# CLI integration — parser registration
# ---------------------------------------------------------------------------


class TestCliParserRegistration:
    """Verify that 'tta new' is properly wired into the CLI parser."""

    def test_new_subcommand_registered(self) -> None:
        """The 'new' subcommand appears in the top-level CLI parser."""
        from ttadev.cli import _build_parser

        parser = _build_parser()
        # Argparse does not expose subparser names easily; we probe by parsing.
        args = parser.parse_args(["new", "test-app", "--no-git"])
        assert args.command == "new"
        assert args.name == "test-app"
        assert args.no_git is True

    def test_new_output_dir_flag(self) -> None:
        """--output-dir is parsed into args.output_dir."""
        from ttadev.cli import _build_parser

        parser = _build_parser()
        args = parser.parse_args(["new", "test-app", "--output-dir", "/tmp", "--no-git"])
        assert args.output_dir == "/tmp"

    def test_new_no_git_default_false(self) -> None:
        """--no-git defaults to False when not supplied."""
        from ttadev.cli import _build_parser

        parser = _build_parser()
        args = parser.parse_args(["new", "test-app"])
        assert args.no_git is False
