"""Unit tests for scripts/session_start_recall.py — all HTTP calls mocked."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from scripts.session_start_recall import _ensure_hindsight, _get_directives, _is_healthy, main


class TestIsHealthy:
    def test_returns_true_when_health_ok(self) -> None:
        mock_resp = MagicMock()
        mock_resp.raise_for_status = MagicMock()
        with patch("httpx.get", return_value=mock_resp):
            assert _is_healthy("http://localhost:8888") is True

    def test_returns_false_on_failure(self) -> None:
        with patch("httpx.get", side_effect=Exception("refused")):
            assert _is_healthy("http://localhost:8888") is False


class TestEnsureHindsight:
    def test_returns_true_when_already_healthy(self) -> None:
        with patch("scripts.session_start_recall._is_healthy", return_value=True):
            result = _ensure_hindsight("http://localhost:8888")
        assert result is True

    def test_starts_container_when_down_and_returns_true(self) -> None:
        healthy_sequence = [False, True]  # down then up after docker start
        with (
            patch("scripts.session_start_recall._is_healthy", side_effect=healthy_sequence),
            patch("subprocess.run", return_value=MagicMock(returncode=0)) as mock_run,
            patch("time.sleep"),
        ):
            result = _ensure_hindsight("http://localhost:8888")
        assert result is True
        mock_run.assert_called_once()
        assert mock_run.call_args.args[0] == ["docker", "start", "hindsight"]

    def test_returns_false_when_docker_start_fails(self) -> None:
        with (
            patch("scripts.session_start_recall._is_healthy", return_value=False),
            patch("subprocess.run", return_value=MagicMock(returncode=1)),
            patch("time.sleep"),
        ):
            result = _ensure_hindsight("http://localhost:8888")
        assert result is False

    def test_returns_false_when_still_unhealthy_after_start(self) -> None:
        with (
            patch("scripts.session_start_recall._is_healthy", return_value=False),
            patch("subprocess.run", return_value=MagicMock(returncode=0)),
            patch("time.sleep"),
        ):
            result = _ensure_hindsight("http://localhost:8888")
        assert result is False


class TestGetDirectives:
    def test_returns_directive_texts(self) -> None:
        mock_resp = MagicMock()
        mock_resp.raise_for_status = MagicMock()
        mock_resp.json.return_value = {"directives": [{"content": "Always orient first."}]}
        with patch("httpx.get", return_value=mock_resp):
            result = _get_directives("http://localhost:8888", "tta-dev")
        assert result == ["Always orient first."]

    def test_returns_directives_from_text_field(self) -> None:
        mock_resp = MagicMock()
        mock_resp.raise_for_status = MagicMock()
        mock_resp.json.return_value = {"directives": [{"text": "Use uv always."}]}
        with patch("httpx.get", return_value=mock_resp):
            result = _get_directives("http://localhost:8888", "tta-dev")
        assert result == ["Use uv always."]

    def test_returns_empty_on_failure(self) -> None:
        with patch("httpx.get", side_effect=Exception("timeout")):
            result = _get_directives("http://localhost:8888", "tta-dev")
        assert result == []


class TestMain:
    def test_prints_directives_as_markdown(self, capsys: pytest.CaptureFixture[str]) -> None:
        with (
            patch("scripts.session_start_recall._ensure_hindsight", return_value=True),
            patch("scripts.session_start_recall._get_directives", return_value=["Use uv."]),
        ):
            main()
        out = capsys.readouterr().out
        assert "## Hindsight Directives" in out
        assert "Use uv." in out

    def test_prints_nothing_when_empty_bank(self, capsys: pytest.CaptureFixture[str]) -> None:
        with (
            patch("scripts.session_start_recall._ensure_hindsight", return_value=True),
            patch("scripts.session_start_recall._get_directives", return_value=[]),
        ):
            main()
        out = capsys.readouterr().out
        assert out == ""

    def test_prints_unavailable_message_when_hindsight_down(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        with patch("scripts.session_start_recall._ensure_hindsight", return_value=False):
            main()
        out = capsys.readouterr().out
        assert "unavailable" in out
