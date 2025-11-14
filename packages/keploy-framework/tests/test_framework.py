"""Tests for Keploy Framework."""

import pytest

from keploy_framework import KeployConfig, ResultValidator
from keploy_framework.test_runner import TestResults


def test_config_creation():
    """Test configuration creation."""
    config = KeployConfig(
        name="test-project",
        app={"command": "uvicorn app:app", "port": 8000, "host": "0.0.0.0"},
        test={"path": "./keploy/tests", "globalNoise": {}},
    )

    assert config.name == "test-project"
    assert config.app.port == 8000


def test_noise_filter_addition():
    """Test adding noise filters."""
    config = KeployConfig(
        name="test-project",
        app={"command": "uvicorn app:app", "port": 8000, "host": "0.0.0.0"},
        test={"path": "./keploy/tests", "globalNoise": {}},
    )

    config.add_noise_filter("timestamp")
    assert "timestamp" in config.test.global_noise["global"]["body"]


def test_validation_pass():
    """Test validation with passing tests."""
    results = TestResults(
        total=10,
        passed=9,
        failed=1,
        pass_rate=90.0,
        test_cases=[],
    )

    validator = ResultValidator(min_pass_rate=0.8)
    assert validator.validate_test_run(results)


def test_validation_fail():
    """Test validation with failing tests."""
    results = TestResults(
        total=10,
        passed=5,
        failed=5,
        pass_rate=50.0,
        test_cases=[],
    )

    validator = ResultValidator(min_pass_rate=0.8)
    assert not validator.validate_test_run(results)


def test_validation_assertion():
    """Test validation assertion."""
    results = TestResults(
        total=10,
        passed=5,
        failed=5,
        pass_rate=50.0,
        test_cases=[],
    )

    validator = ResultValidator(min_pass_rate=0.8)

    with pytest.raises(AssertionError, match="below threshold"):
        validator.assert_pass_rate(results)
