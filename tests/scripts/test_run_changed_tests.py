"""Unit tests for scripts/run_changed_tests.py — filesystem interactions use tmp_path."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from scripts.run_changed_tests import _find_test_file, main


class TestFindTestFile:
    def test_maps_source_to_test_file(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.chdir(tmp_path)
        test_file = tmp_path / "tests" / "primitives" / "memory" / "test_agent_memory.py"
        test_file.parent.mkdir(parents=True)
        test_file.touch()
        result = _find_test_file(Path("ttadev/primitives/memory/agent_memory.py"))
        assert result == Path("tests/primitives/memory/test_agent_memory.py")

    def test_returns_none_when_no_test_file(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.chdir(tmp_path)
        result = _find_test_file(Path("ttadev/workflows/llm_provider.py"))
        assert result is None

    def test_skips_test_files(self) -> None:
        result = _find_test_file(Path("tests/workflows/test_development_cycle.py"))
        assert result is None


class TestMain:
    def test_returns_zero_when_no_tests_found(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.chdir(tmp_path)
        rc = main(["ttadev/workflows/llm_provider.py"])
        assert rc == 0

    def test_mirrors_pytest_exit_code(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.chdir(tmp_path)
        # Create a test file at the mapped path so _find_test_file finds it
        test_file = tmp_path / "tests" / "primitives" / "test_foo.py"
        test_file.parent.mkdir(parents=True)
        test_file.touch()
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=1)
            rc = main(["ttadev/primitives/foo.py"])
        assert rc == 1

    def test_skips_non_python_files(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.chdir(tmp_path)
        rc = main(["README.md", "Makefile", "ttadev/foo.txt"])
        assert rc == 0
