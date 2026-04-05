"""Tests for ttadev/primitives/lifecycle/validation.py.

Covers:
- Severity: all members, __str__, __lt__ ordering, sorting
- ValidationResult: creation, __str__ variants, field defaults, factory isolation
- ValidationCheck: creation, execute() — pass / fail / exception branches,
  fix_command propagation, documentation_link, custom success message
- ValidationPrimitive: check wrapping and delegation
- ReadinessCheckResult: creation, from_results() — all severity categories,
  ready / not-ready determination, passing results excluded from failure lists
- ReadinessCheckPrimitive: wrapping, parallel execution, error handling
"""

from __future__ import annotations

from dataclasses import is_dataclass
from pathlib import Path

from ttadev.primitives.core.base import WorkflowContext
from ttadev.primitives.lifecycle.validation import (
    ReadinessCheckPrimitive,
    ReadinessCheckResult,
    Severity,
    ValidationCheck,
    ValidationPrimitive,
    ValidationResult,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _ctx() -> WorkflowContext:
    return WorkflowContext(workflow_id="test-val")


async def _true(path: Path, ctx: WorkflowContext) -> bool:
    return True


async def _false(path: Path, ctx: WorkflowContext) -> bool:
    return False


async def _raise_runtime(path: Path, ctx: WorkflowContext) -> bool:
    raise RuntimeError("Simulated check error")


def _check(
    name: str = "my_check",
    severity: Severity = Severity.WARNING,
    check_fn=None,
    fix_command: str | None = None,
    documentation_link: str | None = None,
    success_message: str = "It passed",
) -> ValidationCheck:
    return ValidationCheck(
        name=name,
        description="Test check description",
        severity=severity,
        check_function=check_fn if check_fn is not None else _true,
        failure_message="It failed",
        success_message=success_message,
        fix_command=fix_command,
        documentation_link=documentation_link,
    )


def _vresult(
    *,
    passed: bool = True,
    severity: Severity = Severity.WARNING,
    check_name: str = "check",
) -> ValidationResult:
    return ValidationResult(
        check_name=check_name,
        passed=passed,
        severity=severity,
        message="passed" if passed else "failed",
    )


# ===========================================================================
# TestSeverity
# ===========================================================================


class TestSeverity:
    def test_all_four_members_exist(self) -> None:
        assert Severity.BLOCKER.value == "blocker"
        assert Severity.CRITICAL.value == "critical"
        assert Severity.WARNING.value == "warning"
        assert Severity.INFO.value == "info"

    def test_str_blocker(self) -> None:
        assert str(Severity.BLOCKER) == "Blocker"

    def test_str_critical(self) -> None:
        assert str(Severity.CRITICAL) == "Critical"

    def test_str_warning(self) -> None:
        assert str(Severity.WARNING) == "Warning"

    def test_str_info(self) -> None:
        assert str(Severity.INFO) == "Info"

    def test_info_lt_warning(self) -> None:
        # INFO is less severe than WARNING  (higher index in ordering list)
        assert Severity.INFO < Severity.WARNING

    def test_warning_lt_critical(self) -> None:
        assert Severity.WARNING < Severity.CRITICAL

    def test_critical_lt_blocker(self) -> None:
        assert Severity.CRITICAL < Severity.BLOCKER

    def test_blocker_not_lt_info(self) -> None:
        assert not (Severity.BLOCKER < Severity.INFO)

    def test_equal_severity_not_lt(self) -> None:
        assert not (Severity.WARNING < Severity.WARNING)
        assert not (Severity.BLOCKER < Severity.BLOCKER)
        assert not (Severity.INFO < Severity.INFO)

    def test_lt_non_severity_returns_not_implemented(self) -> None:
        result = Severity.BLOCKER.__lt__("not a severity")  # type: ignore[arg-type]
        assert result is NotImplemented

    def test_sorted_ascending_puts_info_first_blocker_last(self) -> None:
        severities = [Severity.BLOCKER, Severity.INFO, Severity.CRITICAL, Severity.WARNING]
        s = sorted(severities)
        # Ascending: INFO < WARNING < CRITICAL < BLOCKER
        assert s[0] == Severity.INFO
        assert s[-1] == Severity.BLOCKER


# ===========================================================================
# TestValidationResult
# ===========================================================================


class TestValidationResult:
    def test_is_dataclass(self) -> None:
        assert is_dataclass(ValidationResult)

    def test_required_fields_stored(self) -> None:
        # Arrange & Act
        result = ValidationResult(
            check_name="test_check",
            passed=True,
            severity=Severity.INFO,
            message="All good",
        )

        # Assert
        assert result.check_name == "test_check"
        assert result.passed is True
        assert result.severity == Severity.INFO
        assert result.message == "All good"

    def test_optional_fields_default_to_none_and_empty(self) -> None:
        result = ValidationResult(check_name="c", passed=True, severity=Severity.INFO, message="ok")
        assert result.fix_command is None
        assert result.documentation_link is None
        assert result.details == {}

    def test_all_optional_fields_accepted(self) -> None:
        result = ValidationResult(
            check_name="c",
            passed=False,
            severity=Severity.BLOCKER,
            message="blocked",
            fix_command="tta fix",
            documentation_link="https://docs.example.com",
            details={"key": "value"},
        )
        assert result.fix_command == "tta fix"
        assert result.documentation_link == "https://docs.example.com"
        assert result.details == {"key": "value"}

    def test_str_passed_shows_pass_and_check_name(self) -> None:
        result = ValidationResult(
            check_name="my_check", passed=True, severity=Severity.INFO, message="All good"
        )
        s = str(result)
        assert "PASS" in s
        assert "my_check" in s
        assert "All good" in s

    def test_str_failed_shows_fail_severity_and_name(self) -> None:
        result = ValidationResult(
            check_name="blocker_check",
            passed=False,
            severity=Severity.BLOCKER,
            message="Blocked by issue",
        )
        s = str(result)
        assert "FAIL" in s
        assert "Blocker" in s
        assert "blocker_check" in s

    def test_details_default_factory_isolated(self) -> None:
        r1 = ValidationResult(check_name="a", passed=True, severity=Severity.INFO, message="ok")
        r2 = ValidationResult(check_name="b", passed=True, severity=Severity.INFO, message="ok")
        r1.details["key"] = "val"
        assert "key" not in r2.details

    def test_all_severity_levels_accepted(self) -> None:
        for sev in Severity:
            r = ValidationResult(check_name="c", passed=False, severity=sev, message="msg")
            assert r.severity == sev


# ===========================================================================
# TestValidationCheck
# ===========================================================================


class TestValidationCheck:
    def test_is_dataclass(self) -> None:
        assert is_dataclass(ValidationCheck)

    def test_fields_stored_correctly(self) -> None:
        check = _check("my_check", Severity.BLOCKER, fix_command="fix it")
        assert check.name == "my_check"
        assert check.description == "Test check description"
        assert check.severity == Severity.BLOCKER
        assert check.failure_message == "It failed"
        assert check.success_message == "It passed"
        assert check.fix_command == "fix it"

    async def test_execute_passing_returns_passed_result(self) -> None:
        # Arrange
        check = _check(check_fn=_true)
        ctx = _ctx()

        # Act
        result = await check.execute(Path("/tmp"), ctx)

        # Assert
        assert result.passed is True
        assert result.check_name == "my_check"
        assert result.message == "It passed"

    async def test_execute_failing_returns_failed_result(self) -> None:
        # Arrange
        check = _check(check_fn=_false, severity=Severity.BLOCKER)
        ctx = _ctx()

        # Act
        result = await check.execute(Path("/tmp"), ctx)

        # Assert
        assert result.passed is False
        assert result.message == "It failed"
        assert result.severity == Severity.BLOCKER

    async def test_execute_passing_fix_command_is_none(self) -> None:
        # fix_command should not appear in passing results
        check = _check(check_fn=_true, fix_command="tta fix")
        result = await check.execute(Path("/tmp"), _ctx())
        assert result.fix_command is None

    async def test_execute_failing_propagates_fix_command(self) -> None:
        check = _check(check_fn=_false, fix_command="tta fix-thing")
        result = await check.execute(Path("/tmp"), _ctx())
        assert result.fix_command == "tta fix-thing"

    async def test_execute_failing_without_fix_command_is_none(self) -> None:
        check = _check(check_fn=_false, fix_command=None)
        result = await check.execute(Path("/tmp"), _ctx())
        assert result.fix_command is None

    async def test_execute_exception_returns_critical_failure(self) -> None:
        # Arrange
        check = _check(check_fn=_raise_runtime)
        ctx = _ctx()

        # Act
        result = await check.execute(Path("/tmp"), ctx)

        # Assert
        assert result.passed is False
        assert result.severity == Severity.CRITICAL
        assert "error" in result.message.lower()

    async def test_execute_exception_message_contains_original_error(self) -> None:
        check = _check(check_fn=_raise_runtime)
        result = await check.execute(Path("/tmp"), _ctx())
        assert "Simulated check error" in result.message

    async def test_execute_exception_details_has_error_and_type(self) -> None:
        check = _check(check_fn=_raise_runtime)
        result = await check.execute(Path("/tmp"), _ctx())
        assert result.details.get("error_type") == "RuntimeError"
        assert "error" in result.details

    async def test_execute_documentation_link_preserved_on_failure(self) -> None:
        check = _check(check_fn=_false, documentation_link="https://docs.example.com/check")
        result = await check.execute(Path("/tmp"), _ctx())
        assert result.documentation_link == "https://docs.example.com/check"

    async def test_execute_custom_success_message_used_on_pass(self) -> None:
        check = _check(check_fn=_true, success_message="Custom success!")
        result = await check.execute(Path("/tmp"), _ctx())
        assert result.message == "Custom success!"

    async def test_execute_check_name_propagated(self) -> None:
        check = _check(name="unique_name", check_fn=_true)
        result = await check.execute(Path("/tmp"), _ctx())
        assert result.check_name == "unique_name"

    async def test_execute_failing_severity_propagated_for_all_levels(self) -> None:
        for sev in Severity:
            check = _check(check_fn=_false, severity=sev)
            result = await check.execute(Path("/tmp"), _ctx())
            assert result.severity == sev


# ===========================================================================
# TestValidationPrimitive
# ===========================================================================


class TestValidationPrimitive:
    def test_stores_check_reference(self) -> None:
        check = _check()
        prim = ValidationPrimitive(check)
        assert prim.check is check

    async def test_execute_passing_returns_passed_result(self) -> None:
        # Arrange
        check = _check(check_fn=_true)
        prim = ValidationPrimitive(check)
        ctx = _ctx()

        # Act
        result = await prim.execute(ctx, Path("/tmp"))

        # Assert
        assert isinstance(result, ValidationResult)
        assert result.passed is True

    async def test_execute_failing_returns_failed_result(self) -> None:
        # Arrange
        check = _check(check_fn=_false, severity=Severity.CRITICAL)
        prim = ValidationPrimitive(check)

        # Act
        result = await prim.execute(_ctx(), Path("/tmp"))

        # Assert
        assert result.passed is False
        assert result.severity == Severity.CRITICAL

    async def test_execute_exception_propagates_as_critical(self) -> None:
        check = _check(check_fn=_raise_runtime)
        prim = ValidationPrimitive(check)
        result = await prim.execute(_ctx(), Path("/tmp"))
        assert result.passed is False
        assert result.severity == Severity.CRITICAL


# ===========================================================================
# TestReadinessCheckResult
# ===========================================================================


class TestReadinessCheckResult:
    def test_is_dataclass(self) -> None:
        assert is_dataclass(ReadinessCheckResult)

    def test_creation_defaults(self) -> None:
        r = ReadinessCheckResult(ready=True)
        assert r.ready is True
        assert r.blockers == r.critical == r.warnings == r.info == r.all_results == []

    def test_from_results_empty_list_is_ready(self) -> None:
        # Arrange & Act
        result = ReadinessCheckResult.from_results([])

        # Assert
        assert result.ready is True
        assert result.all_results == []

    def test_from_results_all_passing_is_ready(self) -> None:
        results = [
            _vresult(passed=True, severity=Severity.BLOCKER),
            _vresult(passed=True, severity=Severity.WARNING),
        ]
        r = ReadinessCheckResult.from_results(results)
        assert r.ready is True
        assert r.blockers == []

    def test_from_results_failed_blocker_not_ready(self) -> None:
        # Arrange
        results = [_vresult(passed=False, severity=Severity.BLOCKER)]

        # Act
        r = ReadinessCheckResult.from_results(results)

        # Assert
        assert r.ready is False
        assert len(r.blockers) == 1

    def test_from_results_failed_critical_does_not_block(self) -> None:
        results = [_vresult(passed=False, severity=Severity.CRITICAL)]
        r = ReadinessCheckResult.from_results(results)
        assert r.ready is True
        assert len(r.critical) == 1

    def test_from_results_failed_warning_does_not_block(self) -> None:
        results = [_vresult(passed=False, severity=Severity.WARNING)]
        r = ReadinessCheckResult.from_results(results)
        assert r.ready is True
        assert len(r.warnings) == 1

    def test_from_results_failed_info_does_not_block(self) -> None:
        results = [_vresult(passed=False, severity=Severity.INFO)]
        r = ReadinessCheckResult.from_results(results)
        assert r.ready is True
        assert len(r.info) == 1

    def test_from_results_categorises_all_severity_levels(self) -> None:
        # Arrange — one failing per category
        results = [
            _vresult(passed=False, severity=Severity.BLOCKER),
            _vresult(passed=False, severity=Severity.CRITICAL),
            _vresult(passed=False, severity=Severity.WARNING),
            _vresult(passed=False, severity=Severity.INFO),
        ]

        # Act
        r = ReadinessCheckResult.from_results(results)

        # Assert
        assert len(r.blockers) == 1
        assert len(r.critical) == 1
        assert len(r.warnings) == 1
        assert len(r.info) == 1
        assert len(r.all_results) == 4
        assert r.ready is False

    def test_from_results_passing_excluded_from_failure_lists(self) -> None:
        results = [
            _vresult(passed=True, severity=Severity.BLOCKER),
            _vresult(passed=True, severity=Severity.CRITICAL),
        ]
        r = ReadinessCheckResult.from_results(results)
        assert r.blockers == []
        assert r.critical == []
        assert r.ready is True

    def test_from_results_all_results_contains_every_input(self) -> None:
        results = [_vresult(passed=True), _vresult(passed=False, severity=Severity.WARNING)]
        r = ReadinessCheckResult.from_results(results)
        assert len(r.all_results) == 2

    def test_default_factory_lists_isolated(self) -> None:
        r1 = ReadinessCheckResult(ready=True)
        r2 = ReadinessCheckResult(ready=True)
        r1.blockers.append(_vresult(passed=False, severity=Severity.BLOCKER))
        assert r2.blockers == []


# ===========================================================================
# TestReadinessCheckPrimitive
# ===========================================================================


class TestReadinessCheckPrimitive:
    def test_stores_checks_and_creates_primitives(self) -> None:
        checks = [_check("c1"), _check("c2")]
        prim = ReadinessCheckPrimitive(checks)
        assert len(prim.checks) == 2
        assert len(prim.validation_primitives) == 2

    async def test_execute_no_checks_returns_ready(self) -> None:
        # Arrange
        prim = ReadinessCheckPrimitive([])

        # Act
        result = await prim.execute(_ctx(), Path("/tmp"))

        # Assert
        assert result.ready is True
        assert result.all_results == []

    async def test_execute_returns_readiness_check_result(self) -> None:
        prim = ReadinessCheckPrimitive([])
        result = await prim.execute(_ctx(), Path("/tmp"))
        assert isinstance(result, ReadinessCheckResult)

    async def test_execute_all_passing_ready(self) -> None:
        # Arrange
        checks = [_check("c1", check_fn=_true), _check("c2", check_fn=_true)]
        prim = ReadinessCheckPrimitive(checks)

        # Act
        result = await prim.execute(_ctx(), Path("/tmp"))

        # Assert
        assert result.ready is True
        assert len(result.all_results) == 2

    async def test_execute_blocker_failure_not_ready(self) -> None:
        # Arrange
        checks = [_check("blocker", severity=Severity.BLOCKER, check_fn=_false)]
        prim = ReadinessCheckPrimitive(checks)

        # Act
        result = await prim.execute(_ctx(), Path("/tmp"))

        # Assert
        assert result.ready is False
        assert len(result.blockers) == 1

    async def test_execute_warning_only_still_ready(self) -> None:
        checks = [_check("warn", severity=Severity.WARNING, check_fn=_false)]
        prim = ReadinessCheckPrimitive(checks)
        result = await prim.execute(_ctx(), Path("/tmp"))
        assert result.ready is True
        assert len(result.warnings) == 1

    async def test_execute_mixed_checks_categorised_correctly(self) -> None:
        # Arrange
        checks = [
            _check("pass_it", check_fn=_true),
            _check("block_it", severity=Severity.BLOCKER, check_fn=_false),
            _check("warn_it", severity=Severity.WARNING, check_fn=_false),
        ]
        prim = ReadinessCheckPrimitive(checks)

        # Act
        result = await prim.execute(_ctx(), Path("/tmp"))

        # Assert
        assert result.ready is False
        assert len(result.blockers) == 1
        assert len(result.warnings) == 1
        assert len(result.all_results) == 3

    async def test_execute_exception_in_check_produces_critical_not_crash(self) -> None:
        # Exception in a check → CRITICAL result; doesn't prevent other checks or crash
        checks = [
            _check("ok", check_fn=_true),
            _check("broken", check_fn=_raise_runtime),
        ]
        prim = ReadinessCheckPrimitive(checks)

        result = await prim.execute(_ctx(), Path("/tmp"))

        # Both results collected
        assert len(result.all_results) == 2
        # CRITICAL but no blocker → still ready
        assert result.ready is True
        assert len(result.critical) == 1
