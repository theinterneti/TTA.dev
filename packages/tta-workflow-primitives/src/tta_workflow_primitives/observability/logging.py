"""Structured logging for workflow primitives."""

from __future__ import annotations

import logging
import sys

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


def get_logger(name: str) -> Any:
    """
    Get a logger instance.

    Args:
        name: Logger name

    Returns:
        Logger instance (structlog or standard logging)
    """
    if STRUCTLOG_AVAILABLE:
        return structlog.get_logger(name)
    else:
        return logging.getLogger(name)
