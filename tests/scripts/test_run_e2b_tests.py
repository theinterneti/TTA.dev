"""Unit tests for scripts/run_e2b_tests.py — all E2B interactions mocked."""

from __future__ import annotations

import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from scripts.run_e2b_tests import (
    _find_test_file,
    _load_changed_files,
    _map_to_test_files,
    _run_pytest_in_sandbox,
    main,
)


class TestFindTestFile:
    def test_returns_none_for_test_file(self) -> None:
        # A file starting with test_ is already a test — skip it
        result = _find_test_file(Path("tests/primitives/test_foo.py"))
        assert result is None

    def test_maps_non_ttadev_source(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        # A source file without the ttadev/ prefix should still map correctly
        monkeypatch.chdir(tmp_path)
        test_file = tmp_path / "tests" / "test_bar.py"
        test_file.parent.mkdir(parents=True)
        test_file.write_text("")
        result = _find_test_file(Path("bar.py"))
        assert result == Path("tests/test_bar.py")


class TestLoadChangedFiles:
    def test_reads_py_files(self, tmp_path: Path) -> None:
        f = tmp_path / "changed.txt"
        f.write_text("ttadev/foo/bar.py\nttadev/baz/qux.py\n")
        result = _load_changed_files(str(f))
        assert result == ["ttadev/foo/bar.py", "ttadev/baz/qux.py"]

    def test_filters_non_py(self, tmp_path: Path) -> None:
        f = tmp_path / "changed.txt"
        f.write_text("ttadev/foo/bar.py\nREADME.md\ndocs/guide.rst\n")
        result = _load_changed_files(str(f))
        assert result == ["ttadev/foo/bar.py"]

    def test_returns_empty_on_missing_file(self) -> None:
        result = _load_changed_files("/nonexistent/path/changed.txt")
        assert result == []

    def test_returns_empty_on_empty_file(self, tmp_path: Path) -> None:
        f = tmp_path / "changed.txt"
        f.write_text("")
        result = _load_changed_files(str(f))
        assert result == []

    def test_strips_whitespace(self, tmp_path: Path) -> None:
        f = tmp_path / "changed.txt"
        f.write_text("  ttadev/foo/bar.py  \n  \n  ttadev/baz/qux.py\n")
        result = _load_changed_files(str(f))
        assert result == ["ttadev/foo/bar.py", "ttadev/baz/qux.py"]


class TestMapToTestFiles:
    def test_maps_source_to_test(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.chdir(tmp_path)
        test_file = tmp_path / "tests" / "foo" / "test_bar.py"
        test_file.parent.mkdir(parents=True)
        test_file.write_text("")
        result = _map_to_test_files(["ttadev/foo/bar.py"])
        assert result == [str(test_file.relative_to(tmp_path))]

    def test_returns_empty_when_no_test_files(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.chdir(tmp_path)
        # No test file created on disk — candidate.exists() returns False
        result = _map_to_test_files(["ttadev/foo/bar.py"])
        assert result == []

    def test_deduplicates(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.chdir(tmp_path)
        test_file = tmp_path / "tests" / "foo" / "test_bar.py"
        test_file.parent.mkdir(parents=True)
        test_file.write_text("")
        # Same source path twice
        result = _map_to_test_files(["ttadev/foo/bar.py", "ttadev/foo/bar.py"])
        assert len(result) == 1
        assert result == [str(test_file.relative_to(tmp_path))]

    def test_skips_non_py(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.chdir(tmp_path)
        result = _map_to_test_files(["README.md", "docs/guide.rst", ".github/ci.yml"])
        assert result == []


def _make_sandbox_mock(
    bootstrap_exit_code: int = 0,
    bootstrap_stderr: str = "",
    pytest_exit_code: int = 0,
    pytest_stdout: str = "1 passed",
) -> MagicMock:
    """Build a sandbox mock that supports 'async with AsyncSandbox.create(...)'.

    AsyncSandbox.create() is used as an async context manager in production code,
    so the mock must: (a) be a regular callable (not AsyncMock), (b) return an
    object with __aenter__/__aexit__ set to AsyncMocks.
    """
    mock_bootstrap = MagicMock(exit_code=bootstrap_exit_code, stderr=bootstrap_stderr)
    mock_result = MagicMock(exit_code=pytest_exit_code, stdout=pytest_stdout)

    mock_commands = MagicMock()
    mock_commands.run = AsyncMock(side_effect=[mock_bootstrap, mock_result])

    mock_files = MagicMock()
    mock_files.write = AsyncMock()

    mock_sandbox = MagicMock()
    mock_sandbox.commands = mock_commands
    mock_sandbox.files = mock_files
    mock_sandbox.__aenter__ = AsyncMock(return_value=mock_sandbox)
    mock_sandbox.__aexit__ = AsyncMock(return_value=False)

    return mock_sandbox


class TestRunPytestInSandbox:
    async def test_creates_sandbox_and_runs_pytest(self) -> None:
        mock_sandbox = _make_sandbox_mock(pytest_exit_code=0, pytest_stdout="1 passed")

        with patch("e2b_code_interpreter.AsyncSandbox") as mock_cls:
            # create() is awaited in production code, so use AsyncMock
            mock_cls.create = AsyncMock(return_value=mock_sandbox)
            exit_code = await _run_pytest_in_sandbox(["tests/foo/test_bar.py"])

        assert exit_code == 0
        mock_sandbox.files.write.assert_called_once()

    async def test_raises_on_bootstrap_failure(self) -> None:
        mock_bootstrap = MagicMock(exit_code=1, stderr="uv not found")

        mock_commands = MagicMock()
        mock_commands.run = AsyncMock(return_value=mock_bootstrap)

        mock_files = MagicMock()
        mock_files.write = AsyncMock()

        mock_sandbox = MagicMock()
        mock_sandbox.commands = mock_commands
        mock_sandbox.files = mock_files
        mock_sandbox.__aenter__ = AsyncMock(return_value=mock_sandbox)
        mock_sandbox.__aexit__ = AsyncMock(return_value=False)

        with (
            patch("e2b_code_interpreter.AsyncSandbox") as mock_cls,
            pytest.raises(RuntimeError, match="Bootstrap failed"),
        ):
            mock_cls.create = AsyncMock(return_value=mock_sandbox)
            await _run_pytest_in_sandbox(["tests/foo/test_bar.py"])

    async def test_returns_pytest_exit_code(self) -> None:
        mock_sandbox = _make_sandbox_mock(pytest_exit_code=1, pytest_stdout="1 failed")

        with patch("e2b_code_interpreter.AsyncSandbox") as mock_cls:
            mock_cls.create = AsyncMock(return_value=mock_sandbox)
            exit_code = await _run_pytest_in_sandbox(["tests/foo/test_bar.py"])

        assert exit_code == 1


class TestMain:
    def test_exits_zero_no_argv(self) -> None:
        result = main([])
        assert result == 0

    def test_exits_zero_no_py_files(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        f = tmp_path / "changed.txt"
        f.write_text("README.md\ndocs/guide.rst\n")
        monkeypatch.setenv("E2B_API_KEY", "fake-key")
        result = main([str(f)])
        assert result == 0

    def test_exits_zero_no_test_counterparts(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.chdir(tmp_path)
        f = tmp_path / "changed.txt"
        f.write_text("ttadev/foo/bar.py\n")
        # No test file on disk — _map_to_test_files returns []
        monkeypatch.setenv("E2B_API_KEY", "fake-key")
        result = main([str(f)])
        assert result == 0

    def test_exits_zero_missing_api_key(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.chdir(tmp_path)
        test_file = tmp_path / "tests" / "foo" / "test_bar.py"
        test_file.parent.mkdir(parents=True)
        test_file.write_text("")
        f = tmp_path / "changed.txt"
        f.write_text("ttadev/foo/bar.py\n")
        monkeypatch.delenv("E2B_API_KEY", raising=False)
        result = main([str(f)])
        assert result == 0

    def test_exits_zero_on_e2b_infra_error(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.chdir(tmp_path)
        test_file = tmp_path / "tests" / "foo" / "test_bar.py"
        test_file.parent.mkdir(parents=True)
        test_file.write_text("")
        f = tmp_path / "changed.txt"
        f.write_text("ttadev/foo/bar.py\n")
        monkeypatch.setenv("E2B_API_KEY", "fake-key")
        with patch(
            "scripts.run_e2b_tests._run_pytest_in_sandbox",
            new_callable=AsyncMock,
            side_effect=RuntimeError("E2B connection refused"),
        ):
            result = main([str(f)])
        assert result == 0

    def test_exits_zero_on_e2b_timeout(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.chdir(tmp_path)
        test_file = tmp_path / "tests" / "foo" / "test_bar.py"
        test_file.parent.mkdir(parents=True)
        test_file.write_text("")
        f = tmp_path / "changed.txt"
        f.write_text("ttadev/foo/bar.py\n")
        monkeypatch.setenv("E2B_API_KEY", "fake-key")
        with patch(
            "scripts.run_e2b_tests._run_pytest_in_sandbox",
            new_callable=AsyncMock,
            side_effect=TimeoutError("sandbox timed out"),
        ):
            result = main([str(f)])
        assert result == 0

    def test_exits_zero_on_asyncio_timeout(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.chdir(tmp_path)
        test_file = tmp_path / "tests" / "foo" / "test_bar.py"
        test_file.parent.mkdir(parents=True)
        test_file.write_text("")
        f = tmp_path / "changed.txt"
        f.write_text("ttadev/foo/bar.py\n")
        monkeypatch.setenv("E2B_API_KEY", "fake-key")
        with patch(
            "scripts.run_e2b_tests._run_pytest_in_sandbox",
            new_callable=AsyncMock,
            side_effect=asyncio.TimeoutError("sandbox timed out"),
        ):
            result = main([str(f)])
        assert result == 0

    def test_exits_one_on_test_failure(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.chdir(tmp_path)
        test_file = tmp_path / "tests" / "foo" / "test_bar.py"
        test_file.parent.mkdir(parents=True)
        test_file.write_text("")
        f = tmp_path / "changed.txt"
        f.write_text("ttadev/foo/bar.py\n")
        monkeypatch.setenv("E2B_API_KEY", "fake-key")
        with patch(
            "scripts.run_e2b_tests._run_pytest_in_sandbox",
            new_callable=AsyncMock,
            return_value=1,
        ):
            result = main([str(f)])
        assert result == 1

    def test_exits_zero_on_test_pass(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.chdir(tmp_path)
        test_file = tmp_path / "tests" / "foo" / "test_bar.py"
        test_file.parent.mkdir(parents=True)
        test_file.write_text("")
        f = tmp_path / "changed.txt"
        f.write_text("ttadev/foo/bar.py\n")
        monkeypatch.setenv("E2B_API_KEY", "fake-key")
        with patch(
            "scripts.run_e2b_tests._run_pytest_in_sandbox",
            new_callable=AsyncMock,
            return_value=0,
        ):
            result = main([str(f)])
        assert result == 0
