"""Keploy Framework - Production-ready API test automation.

This package provides reusable utilities and automation patterns for Keploy-based
API testing, making it trivial to add zero-code test automation to any Python project.
"""

from keploy_framework.config import KeployConfig
from keploy_framework.recorder import RecordingSession
from keploy_framework.test_runner import KeployTestRunner, TestResults
from keploy_framework.validation import ResultValidator

__version__ = "0.1.0"
__all__ = [
    "KeployConfig",
    "KeployTestRunner",
    "RecordingSession",
    "ResultValidator",
    "TestResults",
]
