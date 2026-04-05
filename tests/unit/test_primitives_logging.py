"""Tests for ttadev.primitives.observability.logging."""

from __future__ import annotations

import logging
from unittest.mock import MagicMock, patch

import pytest


class TestSetupLogging:
    def test_setup_logging_stdlib_fallback(self):
        """setup_logging falls back to stdlib when structlog is unavailable."""
        from ttadev.primitives.observability import logging as prim_log

        with patch.object(prim_log, "STRUCTLOG_AVAILABLE", False):
            # Should not raise
            prim_log.setup_logging("DEBUG")

    def test_setup_logging_with_structlog(self):
        """setup_logging configures structlog when available."""
        from ttadev.primitives.observability import logging as prim_log

        if not prim_log.STRUCTLOG_AVAILABLE:
            pytest.skip("structlog not installed")

        prim_log.setup_logging("INFO")


class TestStdlibStructlogAdapter:
    def _make_adapter(self) -> tuple:
        from ttadev.primitives.observability.logging import _StdlibStructlogAdapter

        inner = MagicMock(spec=logging.Logger)
        adapter = _StdlibStructlogAdapter(inner)
        return adapter, inner

    def test_info(self):
        adapter, inner = self._make_adapter()
        adapter.info("hello", key="val")
        inner.log.assert_called_once()
        args, kwargs = inner.log.call_args
        assert "hello" in args[1]
        assert "key='val'" in args[1]

    def test_debug(self):
        adapter, inner = self._make_adapter()
        adapter.debug("dbg msg")
        inner.log.assert_called_once()
        assert inner.log.call_args[0][0] == logging.DEBUG

    def test_warning(self):
        adapter, inner = self._make_adapter()
        adapter.warning("warn msg")
        inner.log.assert_called_once()
        assert inner.log.call_args[0][0] == logging.WARNING

    def test_error(self):
        adapter, inner = self._make_adapter()
        adapter.error("err msg")
        inner.log.assert_called_once()
        assert inner.log.call_args[0][0] == logging.ERROR

    def test_exception(self):
        adapter, inner = self._make_adapter()
        adapter.exception("exc msg")
        inner.log.assert_called_once()
        _, kwargs = inner.log.call_args
        assert kwargs.get("exc_info") is True

    def test_stdlib_kwargs_forwarded(self):
        """Keys like exc_info, stack_info are forwarded, not serialised."""
        adapter, inner = self._make_adapter()
        adapter.info("event", exc_info=True, custom="x")
        _, kwargs = inner.log.call_args
        assert kwargs.get("exc_info") is True
        # custom="x" should be serialised into the message string
        assert "custom='x'" in inner.log.call_args[0][1]


class TestGetLogger:
    def test_get_logger_stdlib_fallback(self):
        from ttadev.primitives.observability import logging as prim_log
        from ttadev.primitives.observability.logging import _StdlibStructlogAdapter

        with patch.object(prim_log, "STRUCTLOG_AVAILABLE", False):
            lg = prim_log.get_logger("mymod")
            assert isinstance(lg, _StdlibStructlogAdapter)

    def test_get_logger_structlog(self):
        from ttadev.primitives.observability import logging as prim_log

        if not prim_log.STRUCTLOG_AVAILABLE:
            pytest.skip("structlog not installed")

        lg = prim_log.get_logger("mymod")
        assert lg is not None
