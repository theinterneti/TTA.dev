"""Unit tests for `tta new <app-name>` CLI command — issue #333.

Pattern: AAA (Arrange / Act / Assert).
Isolation: all filesystem I/O uses the ``tmp_path`` pytest fixture.
No real ``git init`` is ever executed — mocked via ``unittest.mock``.

Scaffold structure produced by `tta new`:

    <project-name>/
    ├── pyproject.toml          # uv-ready, ttadev>=0.1.0 as dependency
    ├── .env.example            # Placeholder keys for supported providers
    ├── .gitignore              # Python + .env
    ├── README.md               # Getting-started instructions
    └── workflows/
        └── hello.py            # Minimal working workflow using make_resilient_llm
"""

from __future__ import annotations

import argparse
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from ttadev.cli.new import (
    _PROVIDER_MODELS,
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
    name: str = "my-project",
    output_dir: str | None = None,
    no_git: bool = True,
    provider: str = "groq",
) -> argparse.Namespace:
    """Build a minimal Namespace that mimics parsed CLI args for `tta new`."""
    return argparse.Namespace(name=name, output_dir=output_dir, no_git=no_git, provider=provider)


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

    def test_substitutes_provider_model(self) -> None:
        """``{provider_model}`` placeholder is replaced."""
        result = _render('model="{provider_model}"', "app", "groq/llama-3.1-8b-instant")
        assert result == 'model="groq/llama-3.1-8b-instant"'

    def test_both_placeholders(self) -> None:
        """Both ``{app_name}`` and ``{provider_model}`` can be substituted together."""
        tmpl = "name={app_name} model={provider_model}"
        result = _render(tmpl, "my-app", "ollama/llama3.2")
        assert result == "name=my-app model=ollama/llama3.2"


# ---------------------------------------------------------------------------
# _write_scaffold — issue #333 five-file structure
# ---------------------------------------------------------------------------


class TestWriteScaffold:
    """Tests for :func:`_write_scaffold` — file creation (issue #333 structure)."""

    def test_creates_expected_files(self, tmp_path: Path) -> None:
        """All five scaffold files from issue #333 are created."""
        app_dir = tmp_path / "my-project"
        _write_scaffold(app_dir, "my-project")

        expected = [
            app_dir / "pyproject.toml",
            app_dir / ".env.example",
            app_dir / ".gitignore",
            app_dir / "README.md",
            app_dir / "workflows" / "hello.py",
        ]
        for f in expected:
            assert f.exists(), f"{f} was not created"

    def test_returns_five_written_paths(self, tmp_path: Path) -> None:
        """Return value lists exactly five files."""
        app_dir = tmp_path / "my-project"
        written = _write_scaffold(app_dir, "my-project")
        assert len(written) == 5
        for path in written:
            assert path.is_file()

    def test_workflows_directory_created(self, tmp_path: Path) -> None:
        """The workflows/ subdirectory is created automatically."""
        app_dir = tmp_path / "my-project"
        _write_scaffold(app_dir, "my-project")
        assert (app_dir / "workflows").is_dir()

    # pyproject.toml ------------------------------------------------------- #

    def test_pyproject_contains_app_name(self, tmp_path: Path) -> None:
        """pyproject.toml has the app name substituted."""
        app_dir = tmp_path / "cool-project"
        _write_scaffold(app_dir, "cool-project")
        content = (app_dir / "pyproject.toml").read_text()
        assert 'name = "cool-project"' in content

    def test_pyproject_contains_ttadev_dependency(self, tmp_path: Path) -> None:
        """pyproject.toml declares ttadev>=0.1.0 as a dependency."""
        app_dir = tmp_path / "my-project"
        _write_scaffold(app_dir, "my-project")
        content = (app_dir / "pyproject.toml").read_text()
        assert "ttadev" in content

    def test_pyproject_requires_python_312(self, tmp_path: Path) -> None:
        """pyproject.toml pins requires-python to >=3.12."""
        app_dir = tmp_path / "my-project"
        _write_scaffold(app_dir, "my-project")
        content = (app_dir / "pyproject.toml").read_text()
        assert ">=3.12" in content

    def test_pyproject_build_system_hatchling(self, tmp_path: Path) -> None:
        """pyproject.toml uses hatchling as build backend."""
        app_dir = tmp_path / "my-project"
        _write_scaffold(app_dir, "my-project")
        content = (app_dir / "pyproject.toml").read_text()
        assert "hatchling" in content

    # .env.example --------------------------------------------------------- #

    def test_env_example_has_groq_key(self, tmp_path: Path) -> None:
        """.env.example contains a GROQ_API_KEY placeholder."""
        app_dir = tmp_path / "my-project"
        _write_scaffold(app_dir, "my-project")
        content = (app_dir / ".env.example").read_text()
        assert "GROQ_API_KEY=" in content

    def test_env_example_has_anthropic_key(self, tmp_path: Path) -> None:
        """.env.example contains an ANTHROPIC_API_KEY placeholder."""
        app_dir = tmp_path / "my-project"
        _write_scaffold(app_dir, "my-project")
        content = (app_dir / ".env.example").read_text()
        assert "ANTHROPIC_API_KEY=" in content

    def test_env_example_has_openrouter_key(self, tmp_path: Path) -> None:
        """.env.example contains an OPENROUTER_API_KEY placeholder."""
        app_dir = tmp_path / "my-project"
        _write_scaffold(app_dir, "my-project")
        content = (app_dir / ".env.example").read_text()
        assert "OPENROUTER_API_KEY=" in content

    # .gitignore ----------------------------------------------------------- #

    def test_gitignore_ignores_dotenv(self, tmp_path: Path) -> None:
        """.gitignore includes .env so secrets are not committed."""
        app_dir = tmp_path / "my-project"
        _write_scaffold(app_dir, "my-project")
        content = (app_dir / ".gitignore").read_text()
        assert ".env" in content

    def test_gitignore_ignores_pycache(self, tmp_path: Path) -> None:
        """.gitignore includes __pycache__/."""
        app_dir = tmp_path / "my-project"
        _write_scaffold(app_dir, "my-project")
        content = (app_dir / ".gitignore").read_text()
        assert "__pycache__/" in content

    def test_gitignore_ignores_venv(self, tmp_path: Path) -> None:
        """.gitignore includes .venv/."""
        app_dir = tmp_path / "my-project"
        _write_scaffold(app_dir, "my-project")
        content = (app_dir / ".gitignore").read_text()
        assert ".venv/" in content

    # README.md ------------------------------------------------------------ #

    def test_readme_contains_app_name(self, tmp_path: Path) -> None:
        """README.md has the app name in the heading."""
        app_dir = tmp_path / "my-project"
        _write_scaffold(app_dir, "my-project")
        content = (app_dir / "README.md").read_text()
        assert "# my-project" in content

    def test_readme_has_uv_sync_instruction(self, tmp_path: Path) -> None:
        """README.md instructs the user to run `uv sync`."""
        app_dir = tmp_path / "my-project"
        _write_scaffold(app_dir, "my-project")
        content = (app_dir / "README.md").read_text()
        assert "uv sync" in content

    def test_readme_has_env_example_copy(self, tmp_path: Path) -> None:
        """README.md instructs the user to copy .env.example."""
        app_dir = tmp_path / "my-project"
        _write_scaffold(app_dir, "my-project")
        content = (app_dir / "README.md").read_text()
        assert ".env.example" in content

    def test_readme_has_hello_py_run(self, tmp_path: Path) -> None:
        """README.md shows how to run workflows/hello.py."""
        app_dir = tmp_path / "my-project"
        _write_scaffold(app_dir, "my-project")
        content = (app_dir / "README.md").read_text()
        assert "workflows/hello.py" in content

    # workflows/hello.py --------------------------------------------------- #

    def test_hello_py_is_valid_python(self, tmp_path: Path) -> None:
        """workflows/hello.py compiles without syntax errors."""
        app_dir = tmp_path / "my-project"
        _write_scaffold(app_dir, "my-project")
        source = (app_dir / "workflows" / "hello.py").read_text()
        compile(source, "hello.py", "exec")  # raises SyntaxError on failure

    def test_hello_py_imports_make_resilient_llm(self, tmp_path: Path) -> None:
        """workflows/hello.py imports make_resilient_llm."""
        app_dir = tmp_path / "my-project"
        _write_scaffold(app_dir, "my-project")
        content = (app_dir / "workflows" / "hello.py").read_text()
        assert "make_resilient_llm" in content

    def test_hello_py_imports_workflow_context(self, tmp_path: Path) -> None:
        """workflows/hello.py imports WorkflowContext."""
        app_dir = tmp_path / "my-project"
        _write_scaffold(app_dir, "my-project")
        content = (app_dir / "workflows" / "hello.py").read_text()
        assert "WorkflowContext" in content

    def test_hello_py_imports_llm_request(self, tmp_path: Path) -> None:
        """workflows/hello.py imports LLMRequest."""
        app_dir = tmp_path / "my-project"
        _write_scaffold(app_dir, "my-project")
        content = (app_dir / "workflows" / "hello.py").read_text()
        assert "LLMRequest" in content

    def test_hello_py_has_async_main(self, tmp_path: Path) -> None:
        """workflows/hello.py defines an async main() entry point."""
        app_dir = tmp_path / "my-project"
        _write_scaffold(app_dir, "my-project")
        content = (app_dir / "workflows" / "hello.py").read_text()
        assert "async def main" in content
        assert "asyncio.run(main())" in content

    def test_hello_py_default_provider_groq(self, tmp_path: Path) -> None:
        """workflows/hello.py uses the groq provider model by default."""
        app_dir = tmp_path / "my-project"
        _write_scaffold(app_dir, "my-project", provider="groq")
        content = (app_dir / "workflows" / "hello.py").read_text()
        assert "groq/" in content

    def test_hello_py_provider_ollama(self, tmp_path: Path) -> None:
        """--provider ollama sets an ollama model in hello.py."""
        app_dir = tmp_path / "my-project"
        _write_scaffold(app_dir, "my-project", provider="ollama")
        content = (app_dir / "workflows" / "hello.py").read_text()
        assert "ollama/" in content

    def test_hello_py_provider_openrouter(self, tmp_path: Path) -> None:
        """--provider openrouter sets an openrouter model in hello.py."""
        app_dir = tmp_path / "my-project"
        _write_scaffold(app_dir, "my-project", provider="openrouter")
        content = (app_dir / "workflows" / "hello.py").read_text()
        assert "openrouter/" in content

    def test_hello_py_valid_python_all_providers(self, tmp_path: Path) -> None:
        """workflows/hello.py compiles cleanly for every supported provider."""
        for provider in _PROVIDER_MODELS:
            app_dir = tmp_path / f"proj-{provider}"
            _write_scaffold(app_dir, f"proj-{provider}", provider=provider)
            source = (app_dir / "workflows" / "hello.py").read_text()
            compile(source, f"hello-{provider}.py", "exec")


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

    def test_returns_false_when_git_not_found(self, tmp_path: Path) -> None:
        """Returns False gracefully when the git binary is missing."""
        app_dir = tmp_path / "repo"
        app_dir.mkdir()
        with patch("ttadev.cli.new.subprocess.run", side_effect=FileNotFoundError):
            ok = _git_init(app_dir)
        assert ok is False


# ---------------------------------------------------------------------------
# cmd_new — happy path
# ---------------------------------------------------------------------------


class TestCmdNewHappyPath:
    """End-to-end tests for :func:`cmd_new` success scenarios."""

    def test_returns_zero_on_success(self, tmp_path: Path) -> None:
        """Exit code is 0 when everything succeeds."""
        args = _args(name="my-project", output_dir=str(tmp_path), no_git=True)
        rc = cmd_new(args)
        assert rc == 0

    def test_creates_app_directory(self, tmp_path: Path) -> None:
        """The app directory is created under output_dir."""
        args = _args(name="hello-world", output_dir=str(tmp_path), no_git=True)
        cmd_new(args)
        assert (tmp_path / "hello-world").is_dir()

    def test_creates_all_five_expected_files(self, tmp_path: Path) -> None:
        """All five scaffold files from issue #333 are present after cmd_new."""
        args = _args(name="my-project", output_dir=str(tmp_path), no_git=True)
        cmd_new(args)
        app_dir = tmp_path / "my-project"
        for rel in [
            "pyproject.toml",
            ".env.example",
            ".gitignore",
            "README.md",
            "workflows/hello.py",
        ]:
            assert (app_dir / rel).exists(), f"Missing: {rel}"

    def test_output_dir_flag(self, tmp_path: Path) -> None:
        """--output-dir places the app in the specified parent directory."""
        custom_parent = tmp_path / "workspace"
        custom_parent.mkdir()
        args = _args(name="sub-app", output_dir=str(custom_parent), no_git=True)
        cmd_new(args)
        assert (custom_parent / "sub-app").is_dir()

    def test_path_flag_creates_at_right_path(self, tmp_path: Path) -> None:
        """--path (alias for --output-dir) creates the project at the specified path."""
        target_parent = tmp_path / "some" / "dir"
        target_parent.mkdir(parents=True)
        args = _args(name="my-project", output_dir=str(target_parent), no_git=True)
        cmd_new(args)
        assert (target_parent / "my-project").is_dir()

    def test_no_git_skips_git_init(self, tmp_path: Path) -> None:
        """--no-git ensures git init is never called."""
        args = _args(name="my-project", output_dir=str(tmp_path), no_git=True)
        with patch("ttadev.cli.new._git_init") as mock_git:
            cmd_new(args)
        mock_git.assert_not_called()

    def test_git_init_called_by_default(self, tmp_path: Path) -> None:
        """git init is called when --no-git is not set."""
        args = _args(name="my-project", output_dir=str(tmp_path), no_git=False)
        with patch("ttadev.cli.new._git_init", return_value=True) as mock_git:
            rc = cmd_new(args)
        assert rc == 0
        mock_git.assert_called_once()

    def test_prints_success_message(self, tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
        """A success message with the app name is printed to stdout."""
        args = _args(name="my-project", output_dir=str(tmp_path), no_git=True)
        cmd_new(args)
        captured = capsys.readouterr()
        assert "my-project" in captured.out
        assert "✅" in captured.out

    def test_prints_next_steps(self, tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
        """Next steps instructions (cd, uv sync, hello.py) are printed to stdout."""
        args = _args(name="my-project", output_dir=str(tmp_path), no_git=True)
        cmd_new(args)
        captured = capsys.readouterr()
        assert "cd " in captured.out
        assert "my-project" in captured.out
        assert "uv sync" in captured.out
        assert "workflows/hello.py" in captured.out

    def test_name_with_hyphens_works(self, tmp_path: Path) -> None:
        """Project names with hyphens are created successfully."""
        args = _args(name="my-cool-project", output_dir=str(tmp_path), no_git=True)
        rc = cmd_new(args)
        assert rc == 0
        assert (tmp_path / "my-cool-project").is_dir()

    def test_name_with_underscores_works(self, tmp_path: Path) -> None:
        """Project names with underscores are created successfully."""
        args = _args(name="my_cool_project", output_dir=str(tmp_path), no_git=True)
        rc = cmd_new(args)
        assert rc == 0
        assert (tmp_path / "my_cool_project").is_dir()

    def test_provider_groq_default(self, tmp_path: Path) -> None:
        """The default provider is groq."""
        args = _args(name="my-project", output_dir=str(tmp_path), no_git=True, provider="groq")
        cmd_new(args)
        content = (tmp_path / "my-project" / "workflows" / "hello.py").read_text()
        assert "groq/" in content

    def test_provider_ollama(self, tmp_path: Path) -> None:
        """--provider ollama sets an ollama model in hello.py."""
        args = _args(name="my-project", output_dir=str(tmp_path), no_git=True, provider="ollama")
        rc = cmd_new(args)
        assert rc == 0
        content = (tmp_path / "my-project" / "workflows" / "hello.py").read_text()
        assert "ollama/" in content

    def test_provider_openrouter(self, tmp_path: Path) -> None:
        """--provider openrouter sets an openrouter model in hello.py."""
        args = _args(
            name="my-project", output_dir=str(tmp_path), no_git=True, provider="openrouter"
        )
        rc = cmd_new(args)
        assert rc == 0
        content = (tmp_path / "my-project" / "workflows" / "hello.py").read_text()
        assert "openrouter/" in content

    def test_workflows_hello_py_is_valid_python(self, tmp_path: Path) -> None:
        """workflows/hello.py in the generated project compiles without errors."""
        args = _args(name="my-project", output_dir=str(tmp_path), no_git=True)
        cmd_new(args)
        source = (tmp_path / "my-project" / "workflows" / "hello.py").read_text()
        compile(source, "hello.py", "exec")


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
        assert list(tmp_path.iterdir()) == []

    def test_invalid_provider_returns_one(self, tmp_path: Path) -> None:
        """An unrecognised provider causes cmd_new to return exit code 1."""
        args = _args(name="my-project", output_dir=str(tmp_path), no_git=True, provider="azure")
        rc = cmd_new(args)
        assert rc == 1

    def test_invalid_provider_prints_to_stderr(
        self, tmp_path: Path, capsys: pytest.CaptureFixture
    ) -> None:
        """An error about the bad provider is written to stderr."""
        args = _args(name="my-project", output_dir=str(tmp_path), no_git=True, provider="azure")
        cmd_new(args)
        captured = capsys.readouterr()
        assert "error:" in captured.err
        assert "azure" in captured.err


# ---------------------------------------------------------------------------
# cmd_new — existing directory
# ---------------------------------------------------------------------------


class TestCmdNewExistingDirectory:
    """Tests that cmd_new refuses to clobber existing directories."""

    def test_existing_dir_returns_one(self, tmp_path: Path) -> None:
        """Exit code is 1 when the target directory already exists."""
        existing = tmp_path / "my-project"
        existing.mkdir()
        args = _args(name="my-project", output_dir=str(tmp_path), no_git=True)
        rc = cmd_new(args)
        assert rc == 1

    def test_existing_dir_prints_to_stderr(
        self, tmp_path: Path, capsys: pytest.CaptureFixture
    ) -> None:
        """An error message mentioning the directory is written to stderr."""
        existing = tmp_path / "my-project"
        existing.mkdir()
        args = _args(name="my-project", output_dir=str(tmp_path), no_git=True)
        cmd_new(args)
        captured = capsys.readouterr()
        assert "error:" in captured.err
        assert "my-project" in captured.err

    def test_existing_dir_not_modified(self, tmp_path: Path) -> None:
        """Files inside the existing directory are not touched."""
        existing = tmp_path / "my-project"
        existing.mkdir()
        sentinel = existing / "sentinel.txt"
        sentinel.write_text("do not touch", encoding="utf-8")

        args = _args(name="my-project", output_dir=str(tmp_path), no_git=True)
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
        args = _args(name="my-project", output_dir=str(tmp_path), no_git=True)
        cmd_new(args)
        return tmp_path / "my-project"

    def test_pyproject_name(self, app_dir: Path) -> None:
        content = (app_dir / "pyproject.toml").read_text()
        assert 'name = "my-project"' in content

    def test_pyproject_ttadev_dep(self, app_dir: Path) -> None:
        content = (app_dir / "pyproject.toml").read_text()
        assert "ttadev" in content

    def test_pyproject_ttadev_version_pinned(self, app_dir: Path) -> None:
        """ttadev dependency should carry a minimum version pin."""
        content = (app_dir / "pyproject.toml").read_text()
        assert "ttadev>=0.1.0" in content

    def test_pyproject_build_system(self, app_dir: Path) -> None:
        content = (app_dir / "pyproject.toml").read_text()
        assert "hatchling" in content

    def test_env_example_keys_present(self, app_dir: Path) -> None:
        content = (app_dir / ".env.example").read_text()
        for key in ("GROQ_API_KEY", "ANTHROPIC_API_KEY", "OPENROUTER_API_KEY"):
            assert key in content

    def test_gitignore_dotenv_entry(self, app_dir: Path) -> None:
        content = (app_dir / ".gitignore").read_text()
        assert ".env" in content

    def test_readme_heading(self, app_dir: Path) -> None:
        content = (app_dir / "README.md").read_text()
        assert "# my-project" in content

    def test_readme_has_quick_start(self, app_dir: Path) -> None:
        content = (app_dir / "README.md").read_text()
        assert "Quick start" in content

    def test_readme_uv_sync(self, app_dir: Path) -> None:
        content = (app_dir / "README.md").read_text()
        assert "uv sync" in content

    def test_hello_py_make_resilient_llm(self, app_dir: Path) -> None:
        content = (app_dir / "workflows" / "hello.py").read_text()
        assert "make_resilient_llm" in content

    def test_hello_py_workflow_context(self, app_dir: Path) -> None:
        content = (app_dir / "workflows" / "hello.py").read_text()
        assert 'workflow_id="hello"' in content

    def test_hello_py_compiles(self, app_dir: Path) -> None:
        source = (app_dir / "workflows" / "hello.py").read_text()
        compile(source, "hello.py", "exec")


# ---------------------------------------------------------------------------
# CLI integration — parser registration
# ---------------------------------------------------------------------------


class TestCliParserRegistration:
    """Verify that 'tta new' is properly wired into the CLI parser."""

    def test_new_subcommand_registered(self) -> None:
        """The 'new' subcommand appears in the top-level CLI parser."""
        from ttadev.cli import _build_parser

        parser = _build_parser()
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

    def test_new_path_flag_alias(self) -> None:
        """--path is an alias for --output-dir and parses into args.output_dir."""
        from ttadev.cli import _build_parser

        parser = _build_parser()
        args = parser.parse_args(["new", "test-app", "--path", "/tmp/projects", "--no-git"])
        assert args.output_dir == "/tmp/projects"

    def test_new_no_git_default_false(self) -> None:
        """--no-git defaults to False when not supplied."""
        from ttadev.cli import _build_parser

        parser = _build_parser()
        args = parser.parse_args(["new", "test-app"])
        assert args.no_git is False

    def test_new_provider_default_groq(self) -> None:
        """--provider defaults to 'groq'."""
        from ttadev.cli import _build_parser

        parser = _build_parser()
        args = parser.parse_args(["new", "test-app", "--no-git"])
        assert args.provider == "groq"

    def test_new_provider_ollama(self) -> None:
        """--provider ollama is accepted."""
        from ttadev.cli import _build_parser

        parser = _build_parser()
        args = parser.parse_args(["new", "test-app", "--provider", "ollama", "--no-git"])
        assert args.provider == "ollama"

    def test_new_provider_openrouter(self) -> None:
        """--provider openrouter is accepted."""
        from ttadev.cli import _build_parser

        parser = _build_parser()
        args = parser.parse_args(["new", "test-app", "--provider", "openrouter", "--no-git"])
        assert args.provider == "openrouter"
