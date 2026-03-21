"""Unit tests for scripts/auto_retain.py — all HTTP and subprocess calls mocked."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from scripts.auto_retain import _git_log, _retain, main


class TestGitLog:
    def test_returns_commit_subjects(self) -> None:
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(stdout="abc123 feat: add thing\n", returncode=0)
            result = _git_log()
        assert "feat: add thing" in result

    def test_returns_empty_on_failure(self) -> None:
        with patch("subprocess.run", side_effect=Exception("no git")):
            result = _git_log()
        assert result == ""


class TestRetain:
    def test_posts_to_hindsight(self) -> None:
        mock_resp = MagicMock()
        mock_resp.raise_for_status = MagicMock()
        with patch("httpx.post", return_value=mock_resp) as mock_post:
            result = _retain("http://localhost:8888", "tta-dev", "test content")
        assert result is True
        mock_post.assert_called_once()

    def test_returns_false_on_network_error(self) -> None:
        with patch("httpx.post", side_effect=Exception("connection refused")):
            result = _retain("http://localhost:8888", "tta-dev", "test content")
        assert result is False


class TestMain:
    def test_exits_zero_always(self) -> None:
        with (
            patch("scripts.auto_retain._git_log", return_value=""),
            patch("scripts.auto_retain._retain", return_value=False),
        ):
            # Should not raise
            main()
