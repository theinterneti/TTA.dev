"""Structured logging for workflow primitives."""

from __future__ import annotations

import logging
import sys
from typing import Any

try:
    import structlog

    STRUCTLOG_AVAILABLE = True
except ImportError:
    STRUCTLOG_AVAILABLE = False


def setup_logging(level: str = "INFO") -> None:
    """
    Setup structured logging.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR)
    """
    if STRUCTLOG_AVAILABLE:
        structlog.configure(
            processors=[
                structlog.contextvars.merge_contextvars,
                structlog.processors.add_log_level,
                structlog.processors.StackInfoRenderer(),
                structlog.dev.set_exc_info,
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.dev.ConsoleRenderer(),
            ],
            wrapper_class=structlog.make_filtering_bound_logger(getattr(logging, level.upper())),
            context_class=dict,
            logger_factory=structlog.PrintLoggerFactory(),
            cache_logger_on_first_use=False,
        )
    else:
        # Fallback to standard logging
        logging.basicConfig(
            level=getattr(logging, level.upper()),
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            stream=sys.stdout,
        )


class _StdlibStructlogAdapter:
    """Accepts structlog-style keyword args on a stdlib logger.

    Converts ``logger.info("event", key=val)`` to a stdlib-compatible call so
    the same calling convention works whether or not structlog is installed.
    """

    def __init__(self, inner: logging.Logger) -> None:
        self._inner = inner

    # stdlib logging kwargs that must be forwarded rather than serialised
    _STDLIB_KW = frozenset({"exc_info", "stack_info", "stacklevel", "extra"})

    def _log(self, level: int, event: str, **kw: Any) -> None:
        stdlib_kw: dict[str, Any] = {k: kw.pop(k) for k in list(kw) if k in self._STDLIB_KW}
        msg = event
        if kw:
            kv = " ".join(f"{k}={v!r}" for k, v in kw.items())
            msg = f"{event} {kv}"
        self._inner.log(level, msg, **stdlib_kw)

    def debug(self, event: str, **kw: Any) -> None:
        self._log(logging.DEBUG, event, **kw)

    def info(self, event: str, **kw: Any) -> None:
        self._log(logging.INFO, event, **kw)

    def warning(self, event: str, **kw: Any) -> None:
        self._log(logging.WARNING, event, **kw)

    def error(self, event: str, **kw: Any) -> None:
        self._log(logging.ERROR, event, **kw)

    def exception(self, event: str, **kw: Any) -> None:
        self._log(logging.ERROR, event, exc_info=True, **kw)


def get_logger(name: str) -> Any:
    """
    Get a logger instance.

    Args:
        name: Logger name

    Returns:
        Logger instance (structlog or stdlib-compatible adapter)
    """
    if STRUCTLOG_AVAILABLE:
        return structlog.get_logger(name)
    else:
        return _StdlibStructlogAdapter(logging.getLogger(name))
