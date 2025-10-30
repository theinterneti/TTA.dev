"""Stage criteria and readiness assessment for lifecycle management.

This module defines the criteria for entering and exiting lifecycle stages,
as well as data structures for assessing project readiness.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from tta_dev_primitives.lifecycle.stage import Stage
from tta_dev_primitives.lifecycle.validation import ValidationCheck, ValidationResult


@dataclass
class StageCriteria:
    """Entry and exit criteria for a lifecycle stage.

    Attributes:
        stage: The target stage
        entry_criteria: Checks that must pass to enter this stage
        exit_criteria: Checks that must pass to exit this stage
        recommended_actions: List of recommended actions for this stage
        description: Human-readable description of this stage
    """

    stage: Stage
    entry_criteria: list[ValidationCheck] = field(default_factory=list)
    exit_criteria: list[ValidationCheck] = field(default_factory=list)
    recommended_actions: list[str] = field(default_factory=list)
    description: str = ""

    def get_all_checks(self) -> list[ValidationCheck]:
        """Get all validation checks (entry + exit criteria).

        Returns:
            Combined list of entry and exit criteria checks
        """
        return self.entry_criteria + self.exit_criteria


@dataclass
class StageReadiness:
    """Assessment of project readiness for a target stage.

    Attributes:
        current_stage: The current stage
        target_stage: The target stage
        ready: Whether the project is ready to transition
        blockers: Blocking validation failures that must be fixed
        critical: Critical validation failures (strong recommendation to fix)
        warnings: Warning validation failures (should be addressed)
        info: Informational messages
        all_results: All validation results
        recommended_actions: List of recommended actions to reach target stage
        next_steps: Specific next steps to take
    """

    current_stage: Stage
    target_stage: Stage
    ready: bool
    blockers: list[ValidationResult] = field(default_factory=list)
    critical: list[ValidationResult] = field(default_factory=list)
    warnings: list[ValidationResult] = field(default_factory=list)
    info: list[ValidationResult] = field(default_factory=list)
    all_results: list[ValidationResult] = field(default_factory=list)
    recommended_actions: list[str] = field(default_factory=list)
    next_steps: list[str] = field(default_factory=list)

    def get_summary(self) -> str:
        """Get human-readable summary of readiness assessment.

        Returns:
            Formatted summary string
        """
        status = "✅ READY" if self.ready else "❌ NOT READY"
        summary_lines = [
            f"\n{'=' * 60}",
            f"Stage Transition: {self.current_stage} → {self.target_stage}",
            f"Status: {status}",
            f"{'=' * 60}",
        ]

        if self.blockers:
            summary_lines.append(f"\n🚫 BLOCKERS ({len(self.blockers)}):")
            for blocker in self.blockers:
                summary_lines.append(f"  • {blocker.message}")
                if blocker.fix_command:
                    summary_lines.append(f"    Fix: {blocker.fix_command}")

        if self.critical:
            summary_lines.append(f"\n⚠️  CRITICAL ({len(self.critical)}):")
            for issue in self.critical:
                summary_lines.append(f"  • {issue.message}")
                if issue.fix_command:
                    summary_lines.append(f"    Fix: {issue.fix_command}")

        if self.warnings:
            summary_lines.append(f"\n⚡ WARNINGS ({len(self.warnings)}):")
            for warning in self.warnings:
                summary_lines.append(f"  • {warning.message}")

        if self.info:
            summary_lines.append(f"\nℹ️  INFO ({len(self.info)}):")
            for info_item in self.info:
                summary_lines.append(f"  • {info_item.message}")

        if self.next_steps:
            summary_lines.append("\n📋 NEXT STEPS:")
            for i, step in enumerate(self.next_steps, 1):
                summary_lines.append(f"  {i}. {step}")

        if self.recommended_actions:
            summary_lines.append("\n💡 RECOMMENDED ACTIONS:")
            for action in self.recommended_actions:
                summary_lines.append(f"  • {action}")

        summary_lines.append(f"\n{'=' * 60}\n")
        return "\n".join(summary_lines)


@dataclass
class TransitionResult:
    """Result of a stage transition attempt.

    Attributes:
        success: Whether the transition succeeded
        from_stage: The starting stage
        to_stage: The target stage
        message: Human-readable message about the transition
        readiness: The readiness assessment that led to this result
        timestamp: When the transition was attempted (ISO format)
    """

    success: bool
    from_stage: Stage
    to_stage: Stage
    message: str
    readiness: StageReadiness
    timestamp: str = ""

    def __post_init__(self) -> None:
        """Set timestamp if not provided."""
        if not self.timestamp:
            from datetime import UTC, datetime

            self.timestamp = datetime.now(UTC).isoformat()

    def get_summary(self) -> str:
        """Get human-readable summary of transition result.

        Returns:
            Formatted summary string
        """
        status = "✅ SUCCESS" if self.success else "❌ FAILED"
        summary_lines = [
            f"\n{'=' * 60}",
            f"Stage Transition: {self.from_stage} → {self.to_stage}",
            f"Status: {status}",
            f"Timestamp: {self.timestamp}",
            f"{'=' * 60}",
            f"\n{self.message}",
        ]

        if not self.success:
            summary_lines.append("\nSee readiness assessment for details.")

        summary_lines.append(f"\n{'=' * 60}\n")
        return "\n".join(summary_lines)
