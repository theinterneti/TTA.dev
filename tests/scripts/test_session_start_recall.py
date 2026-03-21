"""Unit tests for scripts/session_start_recall.py — all HTTP calls mocked."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from scripts.session_start_recall import _get_directives, main


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
        with patch("scripts.session_start_recall._get_directives", return_value=["Use uv."]):
            main()
        out = capsys.readouterr().out
        assert "## Hindsight Directives" in out
        assert "Use uv." in out

    def test_prints_nothing_when_empty(self, capsys: pytest.CaptureFixture[str]) -> None:
        with patch("scripts.session_start_recall._get_directives", return_value=[]):
            main()
        out = capsys.readouterr().out
        assert out == ""
