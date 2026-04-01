"""Tests for ttadev.primitives.observability.logging."""

import logging
from unittest.mock import patch

import pytest

from ttadev.primitives.observability.logging import (
    _StdlibStructlogAdapter,
    get_logger,
    setup_logging,
)


class TestSetupLogging:
    def test_setup_logging_runs_without_error(self) -> None:
        # Should not raise regardless of structlog availability
        setup_logging("INFO")

    def test_setup_logging_debug_level(self) -> None:
        setup_logging("DEBUG")

    def test_setup_logging_fallback_path(self, monkeypatch: pytest.MonkeyPatch) -> None:
        # Force the fallback (stdlib) branch by hiding structlog
        monkeypatch.setattr(
            "ttadev.primitives.observability.logging.STRUCTLOG_AVAILABLE", False, raising=False
        )
        with patch("logging.basicConfig") as mock_basic:
            setup_logging("WARNING")
            mock_basic.assert_called_once()


class TestGetLogger:
    def test_returns_something(self) -> None:
        logger = get_logger("test.module")
        assert logger is not None

    def test_fallback_returns_adapter(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(
            "ttadev.primitives.observability.logging.STRUCTLOG_AVAILABLE", False, raising=False
        )
        logger = get_logger("fallback.module")
        assert isinstance(logger, _StdlibStructlogAdapter)


class TestStdlibStructlogAdapter:
    @pytest.fixture
    def adapter(self) -> _StdlibStructlogAdapter:
        inner = logging.getLogger("test.adapter")
        return _StdlibStructlogAdapter(inner)

    def test_debug(
        self, adapter: _StdlibStructlogAdapter, caplog: pytest.LogCaptureFixture
    ) -> None:
        with caplog.at_level(logging.DEBUG, logger="test.adapter"):
            adapter.debug("debug event", key="val")
        assert any("debug event" in r.message for r in caplog.records)

    def test_info(self, adapter: _StdlibStructlogAdapter, caplog: pytest.LogCaptureFixture) -> None:
        with caplog.at_level(logging.INFO, logger="test.adapter"):
            adapter.info("info event", x=1)
        assert any("info event" in r.message for r in caplog.records)

    def test_warning(
        self, adapter: _StdlibStructlogAdapter, caplog: pytest.LogCaptureFixture
    ) -> None:
        with caplog.at_level(logging.WARNING, logger="test.adapter"):
            adapter.warning("warn event")
        assert any("warn event" in r.message for r in caplog.records)

    def test_error(
        self, adapter: _StdlibStructlogAdapter, caplog: pytest.LogCaptureFixture
    ) -> None:
        with caplog.at_level(logging.ERROR, logger="test.adapter"):
            adapter.error("error event")
        assert any("error event" in r.message for r in caplog.records)

    def test_exception(
        self, adapter: _StdlibStructlogAdapter, caplog: pytest.LogCaptureFixture
    ) -> None:
        with caplog.at_level(logging.ERROR, logger="test.adapter"):
            adapter.exception("exc event")
        assert any("exc event" in r.message for r in caplog.records)

    def test_kv_pairs_serialised_into_message(
        self, adapter: _StdlibStructlogAdapter, caplog: pytest.LogCaptureFixture
    ) -> None:
        with caplog.at_level(logging.INFO, logger="test.adapter"):
            adapter.info("event", foo="bar", baz=42)
        msg = caplog.records[-1].message
        assert "foo=" in msg
        assert "baz=" in msg

    def test_stdlib_kwargs_forwarded_not_serialised(
        self, adapter: _StdlibStructlogAdapter, caplog: pytest.LogCaptureFixture
    ) -> None:
        with caplog.at_level(logging.INFO, logger="test.adapter"):
            adapter.info("event", extra={"request_id": "abc"})
        msg = caplog.records[-1].message
        # extra should not appear as a serialised key=value pair
        assert "extra=" not in msg
