"""Tests for ttadev/primitives/lifecycle/stage_criteria.py.

Covers:
- StageCriteria: creation, defaults, get_all_checks(), factory isolation
- StageReadiness: creation, get_summary() — every branch (blockers, critical,
  warnings, info, next_steps, recommended_actions)
- TransitionResult: creation, __post_init__ timestamp logic, get_summary()
"""

from __future__ import annotations

from dataclasses import is_dataclass
from pathlib import Path

from ttadev.primitives.core.base import WorkflowContext
from ttadev.primitives.lifecycle.stage import Stage
from ttadev.primitives.lifecycle.stage_criteria import (
    StageCriteria,
    StageReadiness,
    TransitionResult,
)
from ttadev.primitives.lifecycle.validation import (
    Severity,
    ValidationCheck,
    ValidationResult,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _always_true(path: Path, ctx: WorkflowContext) -> bool:
    return True


def _check(severity: Severity = Severity.INFO) -> ValidationCheck:
    return ValidationCheck(
        name="test_check",
        description="A test check",
        severity=severity,
        check_function=_always_true,
        failure_message="Failed",
        success_message="Passed",
    )


def _vresult(
    *,
    passed: bool = True,
    severity: Severity = Severity.INFO,
    message: str = "ok",
    fix_command: str | None = None,
) -> ValidationResult:
    return ValidationResult(
        check_name="check",
        passed=passed,
        severity=severity,
        message=message,
        fix_command=fix_command,
    )


def _bare_readiness(*, ready: bool = True) -> StageReadiness:
    return StageReadiness(
        current_stage=Stage.EXPERIMENTATION,
        target_stage=Stage.TESTING,
        ready=ready,
    )


# ===========================================================================
# TestStageCriteria
# ===========================================================================


class TestStageCriteria:
    def test_is_dataclass(self) -> None:
        assert is_dataclass(StageCriteria)

    def test_creation_minimal_stores_stage(self) -> None:
        # Arrange & Act
        criteria = StageCriteria(stage=Stage.TESTING)

        # Assert
        assert criteria.stage == Stage.TESTING

    def test_defaults_are_empty_collections_and_string(self) -> None:
        # Arrange & Act
        criteria = StageCriteria(stage=Stage.TESTING)

        # Assert
        assert criteria.entry_criteria == []
        assert criteria.exit_criteria == []
        assert criteria.recommended_actions == []
        assert criteria.description == ""

    def test_creation_with_all_fields(self) -> None:
        # Arrange
        entry = _check(Severity.BLOCKER)
        exit_ = _check(Severity.WARNING)

        # Act
        criteria = StageCriteria(
            stage=Stage.STAGING,
            entry_criteria=[entry],
            exit_criteria=[exit_],
            recommended_actions=["run tests", "update docs"],
            description="Staging phase description",
        )

        # Assert
        assert criteria.stage == Stage.STAGING
        assert len(criteria.entry_criteria) == 1
        assert len(criteria.exit_criteria) == 1
        assert criteria.recommended_actions == ["run tests", "update docs"]
        assert criteria.description == "Staging phase description"

    def test_get_all_checks_empty_returns_empty(self) -> None:
        # Arrange
        criteria = StageCriteria(stage=Stage.EXPERIMENTATION)

        # Act
        result = criteria.get_all_checks()

        # Assert
        assert result == []

    def test_get_all_checks_combines_entry_and_exit(self) -> None:
        # Arrange
        entry = _check(Severity.BLOCKER)
        exit_ = _check(Severity.WARNING)
        criteria = StageCriteria(
            stage=Stage.DEPLOYMENT,
            entry_criteria=[entry],
            exit_criteria=[exit_],
        )

        # Act
        result = criteria.get_all_checks()

        # Assert
        assert len(result) == 2
        assert entry in result
        assert exit_ in result

    def test_get_all_checks_entry_only(self) -> None:
        entry = _check()
        criteria = StageCriteria(stage=Stage.PRODUCTION, entry_criteria=[entry])
        assert len(criteria.get_all_checks()) == 1
        assert criteria.get_all_checks()[0] is entry

    def test_get_all_checks_exit_only(self) -> None:
        exit_ = _check()
        criteria = StageCriteria(stage=Stage.PRODUCTION, exit_criteria=[exit_])
        assert len(criteria.get_all_checks()) == 1

    def test_get_all_checks_multiple_in_each_group(self) -> None:
        # Arrange
        c1, c2, c3 = _check(), _check(), _check()
        criteria = StageCriteria(
            stage=Stage.TESTING,
            entry_criteria=[c1, c2],
            exit_criteria=[c3],
        )

        # Act
        result = criteria.get_all_checks()

        # Assert
        assert len(result) == 3
        assert all(c in result for c in (c1, c2, c3))

    def test_default_factory_entry_criteria_isolated(self) -> None:
        # Arrange
        c1 = StageCriteria(stage=Stage.TESTING)
        c2 = StageCriteria(stage=Stage.STAGING)

        # Act — mutate c1 only
        c1.entry_criteria.append(_check())

        # Assert — c2 unaffected
        assert c2.entry_criteria == []

    def test_default_factory_recommended_actions_isolated(self) -> None:
        c1 = StageCriteria(stage=Stage.TESTING)
        c2 = StageCriteria(stage=Stage.STAGING)
        c1.recommended_actions.append("do something")
        assert c2.recommended_actions == []

    def test_all_stages_accepted(self) -> None:
        for stage in Stage:
            criteria = StageCriteria(stage=stage)
            assert criteria.stage == stage


# ===========================================================================
# TestStageReadiness
# ===========================================================================


class TestStageReadiness:
    def test_is_dataclass(self) -> None:
        assert is_dataclass(StageReadiness)

    def test_creation_stores_required_fields(self) -> None:
        # Act
        r = _bare_readiness()

        # Assert
        assert r.current_stage == Stage.EXPERIMENTATION
        assert r.target_stage == Stage.TESTING
        assert r.ready is True

    def test_creation_defaults_are_empty(self) -> None:
        r = _bare_readiness()
        assert r.blockers == []
        assert r.critical == []
        assert r.warnings == []
        assert r.info == []
        assert r.all_results == []
        assert r.recommended_actions == []
        assert r.next_steps == []

    def test_get_summary_returns_string(self) -> None:
        assert isinstance(_bare_readiness().get_summary(), str)

    def test_get_summary_ready_shows_checkmark_status(self) -> None:
        summary = _bare_readiness(ready=True).get_summary()
        assert "✅" in summary
        assert "READY" in summary

    def test_get_summary_not_ready_shows_cross_status(self) -> None:
        summary = _bare_readiness(ready=False).get_summary()
        assert "❌" in summary
        assert "NOT READY" in summary

    def test_get_summary_shows_stage_transition_names(self) -> None:
        summary = StageReadiness(
            current_stage=Stage.TESTING,
            target_stage=Stage.STAGING,
            ready=True,
        ).get_summary()
        assert "Testing" in summary
        assert "Staging" in summary

    def test_get_summary_shows_blocker_message(self) -> None:
        # Arrange
        r = StageReadiness(
            current_stage=Stage.TESTING,
            target_stage=Stage.STAGING,
            ready=False,
            blockers=[_vresult(passed=False, severity=Severity.BLOCKER, message="Must fix X")],
        )

        # Act
        summary = r.get_summary()

        # Assert
        assert "BLOCKERS" in summary
        assert "Must fix X" in summary

    def test_get_summary_shows_blocker_fix_command(self) -> None:
        r = StageReadiness(
            current_stage=Stage.TESTING,
            target_stage=Stage.STAGING,
            ready=False,
            blockers=[
                _vresult(
                    passed=False,
                    severity=Severity.BLOCKER,
                    message="Blocker",
                    fix_command="tta fix-blocker",
                )
            ],
        )
        assert "Fix: tta fix-blocker" in r.get_summary()

    def test_get_summary_blocker_without_fix_command_omits_fix_line(self) -> None:
        # Arrange — blocker with no fix command
        r = StageReadiness(
            current_stage=Stage.TESTING,
            target_stage=Stage.STAGING,
            ready=False,
            blockers=[
                _vresult(
                    passed=False,
                    severity=Severity.BLOCKER,
                    message="Blocker without fix",
                    fix_command=None,
                )
            ],
        )

        # Act
        summary = r.get_summary()

        # Assert — message present but no "Fix:" line
        assert "Blocker without fix" in summary
        assert "Fix:" not in summary

    def test_get_summary_shows_critical_with_fix_command(self) -> None:
        r = StageReadiness(
            current_stage=Stage.TESTING,
            target_stage=Stage.STAGING,
            ready=True,
            critical=[
                _vresult(
                    passed=False,
                    severity=Severity.CRITICAL,
                    message="Critical issue",
                    fix_command="tta fix-critical",
                )
            ],
        )
        summary = r.get_summary()
        assert "CRITICAL" in summary
        assert "Critical issue" in summary
        assert "Fix: tta fix-critical" in summary

    def test_get_summary_shows_warnings(self) -> None:
        r = StageReadiness(
            current_stage=Stage.TESTING,
            target_stage=Stage.STAGING,
            ready=True,
            warnings=[_vresult(passed=False, severity=Severity.WARNING, message="Warning msg")],
        )
        summary = r.get_summary()
        assert "WARNINGS" in summary
        assert "Warning msg" in summary

    def test_get_summary_shows_info(self) -> None:
        r = StageReadiness(
            current_stage=Stage.TESTING,
            target_stage=Stage.STAGING,
            ready=True,
            info=[_vresult(passed=False, severity=Severity.INFO, message="Info msg")],
        )
        summary = r.get_summary()
        assert "INFO" in summary
        assert "Info msg" in summary

    def test_get_summary_shows_next_steps_numbered(self) -> None:
        r = StageReadiness(
            current_stage=Stage.TESTING,
            target_stage=Stage.STAGING,
            ready=True,
            next_steps=["Do step one", "Do step two"],
        )
        summary = r.get_summary()
        assert "NEXT STEPS" in summary
        assert "Do step one" in summary
        assert "1." in summary and "2." in summary

    def test_get_summary_shows_recommended_actions(self) -> None:
        r = StageReadiness(
            current_stage=Stage.TESTING,
            target_stage=Stage.STAGING,
            ready=True,
            recommended_actions=["Action alpha", "Action beta"],
        )
        summary = r.get_summary()
        assert "RECOMMENDED ACTIONS" in summary
        assert "Action alpha" in summary

    def test_get_summary_contains_separator_lines(self) -> None:
        summary = _bare_readiness().get_summary()
        assert "=" * 10 in summary

    def test_get_summary_empty_sections_omitted_when_no_data(self) -> None:
        summary = _bare_readiness().get_summary()
        assert "BLOCKERS" not in summary
        assert "CRITICAL" not in summary
        assert "WARNINGS" not in summary
        assert "NEXT STEPS" not in summary
        assert "RECOMMENDED ACTIONS" not in summary
        assert "KNOWLEDGE BASE" not in summary


# ===========================================================================
# TestTransitionResult
# ===========================================================================


class TestTransitionResult:
    def test_is_dataclass(self) -> None:
        assert is_dataclass(TransitionResult)

    def test_creation_with_explicit_timestamp(self) -> None:
        # Arrange & Act
        result = TransitionResult(
            success=True,
            from_stage=Stage.EXPERIMENTATION,
            to_stage=Stage.TESTING,
            message="Transition successful",
            readiness=_bare_readiness(),
            timestamp="2024-01-01T00:00:00+00:00",
        )

        # Assert
        assert result.success is True
        assert result.from_stage == Stage.EXPERIMENTATION
        assert result.to_stage == Stage.TESTING
        assert result.message == "Transition successful"
        assert result.timestamp == "2024-01-01T00:00:00+00:00"

    def test_post_init_sets_timestamp_when_not_provided(self) -> None:
        # Arrange & Act
        result = TransitionResult(
            success=True,
            from_stage=Stage.EXPERIMENTATION,
            to_stage=Stage.TESTING,
            message="Done",
            readiness=_bare_readiness(),
        )

        # Assert — auto-generated ISO 8601 timestamp
        assert result.timestamp != ""
        assert "T" in result.timestamp

    def test_post_init_preserves_explicit_timestamp(self) -> None:
        # Arrange
        ts = "2024-06-15T12:30:00+00:00"

        # Act
        result = TransitionResult(
            success=True,
            from_stage=Stage.EXPERIMENTATION,
            to_stage=Stage.TESTING,
            message="Done",
            readiness=_bare_readiness(),
            timestamp=ts,
        )

        # Assert
        assert result.timestamp == ts

    def test_get_summary_success_shows_checkmark_and_label(self) -> None:
        result = TransitionResult(
            success=True,
            from_stage=Stage.EXPERIMENTATION,
            to_stage=Stage.TESTING,
            message="All checks passed",
            readiness=_bare_readiness(),
        )
        summary = result.get_summary()
        assert "✅" in summary
        assert "SUCCESS" in summary

    def test_get_summary_failure_shows_cross_and_label(self) -> None:
        result = TransitionResult(
            success=False,
            from_stage=Stage.EXPERIMENTATION,
            to_stage=Stage.TESTING,
            message="Blocked",
            readiness=_bare_readiness(),
        )
        summary = result.get_summary()
        assert "❌" in summary
        assert "FAILED" in summary

    def test_get_summary_shows_message(self) -> None:
        result = TransitionResult(
            success=True,
            from_stage=Stage.EXPERIMENTATION,
            to_stage=Stage.TESTING,
            message="Custom transition message",
            readiness=_bare_readiness(),
        )
        assert "Custom transition message" in result.get_summary()

    def test_get_summary_failure_mentions_readiness_assessment(self) -> None:
        result = TransitionResult(
            success=False,
            from_stage=Stage.EXPERIMENTATION,
            to_stage=Stage.TESTING,
            message="Failed",
            readiness=_bare_readiness(),
        )
        assert "readiness" in result.get_summary().lower()

    def test_get_summary_success_has_no_readiness_hint(self) -> None:
        result = TransitionResult(
            success=True,
            from_stage=Stage.EXPERIMENTATION,
            to_stage=Stage.TESTING,
            message="Done",
            readiness=_bare_readiness(),
        )
        assert "readiness" not in result.get_summary().lower()

    def test_get_summary_shows_from_and_to_stage_names(self) -> None:
        result = TransitionResult(
            success=True,
            from_stage=Stage.TESTING,
            to_stage=Stage.STAGING,
            message="Ok",
            readiness=_bare_readiness(),
        )
        summary = result.get_summary()
        assert "Testing" in summary
        assert "Staging" in summary

    def test_get_summary_shows_timestamp(self) -> None:
        ts = "2024-03-01T10:00:00+00:00"
        result = TransitionResult(
            success=True,
            from_stage=Stage.EXPERIMENTATION,
            to_stage=Stage.TESTING,
            message="Done",
            readiness=_bare_readiness(),
            timestamp=ts,
        )
        assert ts in result.get_summary()

    def test_get_summary_returns_string(self) -> None:
        result = TransitionResult(
            success=True,
            from_stage=Stage.EXPERIMENTATION,
            to_stage=Stage.TESTING,
            message="Ok",
            readiness=_bare_readiness(),
        )
        assert isinstance(result.get_summary(), str)

    def test_get_summary_contains_separator_lines(self) -> None:
        result = TransitionResult(
            success=True,
            from_stage=Stage.EXPERIMENTATION,
            to_stage=Stage.TESTING,
            message="Ok",
            readiness=_bare_readiness(),
        )
        assert "=" * 10 in result.get_summary()
