"""Tests for the circuit_breaker backward-compat shim.

Importing this module covers the re-export lines in circuit_breaker.py.
"""

from __future__ import annotations

from ttadev.primitives.recovery import circuit_breaker  # noqa: F401
from ttadev.primitives.recovery.circuit_breaker import (
    CircuitBreaker,
    ErrorCategory,
    ErrorSeverity,
    RetryConfig,
    calculate_delay,
    classify_error,
    should_retry,
    with_retry,
    with_retry_async,
)


def test_shim_exports_all_symbols():
    """All expected symbols are importable from the shim module."""
    assert CircuitBreaker is not None
    assert ErrorCategory is not None
    assert ErrorSeverity is not None
    assert RetryConfig is not None
    assert calculate_delay is not None
    assert classify_error is not None
    assert should_retry is not None
    assert with_retry is not None
    assert with_retry_async is not None
