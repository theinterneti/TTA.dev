"""Test validation utilities."""

from keploy_framework.test_runner import TestResults


class ResultValidator:
    """Validator for Keploy test results."""

    def __init__(self, min_pass_rate: float = 0.8) -> None:
        """Initialize validator.

        Args:
            min_pass_rate: Minimum pass rate (0.0-1.0)
        """
        self.min_pass_rate = min_pass_rate

    def validate_test_run(
        self,
        results: TestResults,
        expected_pass_rate: float | None = None,
    ) -> bool:
        """Validate test run results.

        Args:
            results: Test results to validate
            expected_pass_rate: Override minimum pass rate for this validation

        Returns:
            True if validation passed
        """
        threshold = expected_pass_rate if expected_pass_rate is not None else self.min_pass_rate
        return (results.pass_rate / 100.0) >= threshold

    def assert_pass_rate(
        self,
        results: TestResults,
        expected_pass_rate: float | None = None,
    ) -> None:
        """Assert that pass rate meets threshold.

        Args:
            results: Test results to validate
            expected_pass_rate: Override minimum pass rate for this validation

        Raises:
            AssertionError: If pass rate is below threshold
        """
        threshold = expected_pass_rate if expected_pass_rate is not None else self.min_pass_rate
        actual = results.pass_rate / 100.0

        if actual < threshold:
            msg = f"Pass rate {actual:.1%} below threshold {threshold:.1%}"
            raise AssertionError(msg)
