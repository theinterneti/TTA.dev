"""Tests for Keploy Framework."""

import tempfile
from pathlib import Path

import pytest

from keploy_framework import KeployConfig, ResultValidator
from keploy_framework.test_runner import KeployTestRunner, TestResults


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


def test_html_report_escapes_xss():
    """Test HTML report escapes user-controlled data to prevent XSS."""
    # Create a temporary directory for the report
    with tempfile.TemporaryDirectory() as tmpdir:
        keploy_dir = Path(tmpdir)

        # Create test results with potentially malicious input
        results = TestResults(
            total=2,
            passed=1,
            failed=1,
            pass_rate=50.0,
            test_cases=[
                {"name": "<script>alert('XSS')</script>", "status": "passed"},
                {"name": "normal_test", "status": "<img src=x onerror=alert('XSS')>"},
            ],
        )

        # Create runner and generate report
        runner = KeployTestRunner(
            api_url="http://localhost:8000",
            keploy_dir=keploy_dir,
        )
        runner._generate_report(results)

        # Read the generated HTML
        report_path = keploy_dir / "test-report.html"
        html_content = report_path.read_text()

        # Verify that malicious scripts are escaped
        assert "<script>alert('XSS')</script>" not in html_content
        assert "&lt;script&gt;alert(&#x27;XSS&#x27;)&lt;/script&gt;" in html_content

        assert "<img src=x onerror=alert('XSS')>" not in html_content
        assert "&lt;img src=x onerror=alert(&#x27;XSS&#x27;)&gt;" in html_content

        # Verify normal test name is still present (but escaped)
        assert "normal_test" in html_content
