"""Validation primitives and data structures for lifecycle management.

This module provides the building blocks for creating validation checks
that assess project readiness for stage transitions.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

from tta_dev_primitives.core.base import WorkflowContext, WorkflowPrimitive


class Severity(Enum):
    """Severity level for validation check failures.

    Attributes:
        BLOCKER: Must be fixed before proceeding (blocks transition)
        CRITICAL: Should be fixed before proceeding (strong recommendation)
        WARNING: Should be addressed but doesn't block transition
        INFO: Informational only, no action required
    """

    BLOCKER = "blocker"
    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"

    def __str__(self) -> str:
        """Return human-readable severity name."""
        return self.value.title()

    def __lt__(self, other: Severity) -> bool:
        """Compare severities for ordering (BLOCKER > CRITICAL > WARNING > INFO).

        Args:
            other: Severity to compare against

        Returns:
            True if this severity is less severe than other
        """
        if not isinstance(other, Severity):
            return NotImplemented

        order = [Severity.BLOCKER, Severity.CRITICAL, Severity.WARNING, Severity.INFO]
        return order.index(self) > order.index(other)


@dataclass
class ValidationResult:
    """Result of a validation check.

    Attributes:
        check_name: Name of the validation check
        passed: Whether the check passed
        severity: Severity level if check failed
        message: Human-readable message describing the result
        fix_command: Optional command to fix the issue
        documentation_link: Optional link to documentation
        details: Additional details about the check result
    """

    check_name: str
    passed: bool
    severity: Severity
    message: str
    fix_command: str | None = None
    documentation_link: str | None = None
    details: dict[str, Any] = field(default_factory=dict)

    def __str__(self) -> str:
        """Return human-readable validation result."""
        status = "✅ PASS" if self.passed else f"❌ FAIL ({self.severity})"
        return f"[{status}] {self.check_name}: {self.message}"


@dataclass
class ValidationCheck:
    """Configuration for a validation check.

    Attributes:
        name: Name of the validation check
        description: Human-readable description
        severity: Severity level if check fails
        check_function: Async callable that performs the check
        failure_message: Message to display if check fails
        success_message: Message to display if check passes
        fix_command: Optional command to fix the issue
        documentation_link: Optional link to documentation
    """

    name: str
    description: str
    severity: Severity
    check_function: Callable[[Path, WorkflowContext], Awaitable[bool]]
    failure_message: str
    success_message: str = "Check passed"
    fix_command: str | None = None
    documentation_link: str | None = None

    async def execute(self, project_path: Path, context: WorkflowContext) -> ValidationResult:
        """Execute the validation check.

        Args:
            project_path: Path to project root
            context: Workflow context

        Returns:
            ValidationResult with check outcome
        """
        try:
            passed = await self.check_function(project_path, context)
            message = self.success_message if passed else self.failure_message

            return ValidationResult(
                check_name=self.name,
                passed=passed,
                severity=self.severity,
                message=message,
                fix_command=self.fix_command if not passed else None,
                documentation_link=self.documentation_link,
            )
        except Exception as e:
            return ValidationResult(
                check_name=self.name,
                passed=False,
                severity=Severity.CRITICAL,
                message=f"Check failed with error: {e!s}",
                details={"error": str(e), "error_type": type(e).__name__},
            )


class ValidationPrimitive(WorkflowPrimitive[Path, ValidationResult]):
    """Base class for validation check primitives.

    This primitive wraps a ValidationCheck and provides the workflow
    primitive interface for composability.
    """

    def __init__(self, check: ValidationCheck) -> None:
        """Initialize validation primitive.

        Args:
            check: ValidationCheck configuration
        """
        super().__init__()
        self.check = check

    async def execute(self, context: WorkflowContext, input_data: Path) -> ValidationResult:
        """Execute the validation check.

        Args:
            context: Workflow context
            input_data: Path to project root

        Returns:
            ValidationResult with check outcome
        """
        return await self.check.execute(input_data, context)


@dataclass
class ReadinessCheckResult:
    """Result of a readiness check containing multiple validation results.

    Attributes:
        ready: Whether the project is ready for the target stage
        blockers: List of blocking validation failures
        critical: List of critical validation failures
        warnings: List of warning validation failures
        info: List of informational messages
        all_results: All validation results
    """

    ready: bool
    blockers: list[ValidationResult] = field(default_factory=list)
    critical: list[ValidationResult] = field(default_factory=list)
    warnings: list[ValidationResult] = field(default_factory=list)
    info: list[ValidationResult] = field(default_factory=list)
    all_results: list[ValidationResult] = field(default_factory=list)

    @classmethod
    def from_results(cls, results: list[ValidationResult]) -> ReadinessCheckResult:
        """Create ReadinessCheckResult from validation results.

        Args:
            results: List of validation results

        Returns:
            ReadinessCheckResult with categorized failures
        """
        blockers = [r for r in results if not r.passed and r.severity == Severity.BLOCKER]
        critical = [r for r in results if not r.passed and r.severity == Severity.CRITICAL]
        warnings = [r for r in results if not r.passed and r.severity == Severity.WARNING]
        info = [r for r in results if not r.passed and r.severity == Severity.INFO]

        # Ready only if no blockers
        ready = len(blockers) == 0

        return cls(
            ready=ready,
            blockers=blockers,
            critical=critical,
            warnings=warnings,
            info=info,
            all_results=results,
        )


class ReadinessCheckPrimitive(WorkflowPrimitive[Path, ReadinessCheckResult]):
    """Primitive that runs multiple validation checks in parallel.

    This primitive runs validation checks concurrently for improved performance.
    """

    def __init__(self, checks: list[ValidationCheck]) -> None:
        """Initialize readiness check primitive.

        Args:
            checks: List of validation checks to run
        """
        super().__init__()
        self.checks = checks
        self.validation_primitives = [ValidationPrimitive(check) for check in checks]

    async def execute(self, context: WorkflowContext, input_data: Path) -> ReadinessCheckResult:
        """Execute all validation checks in parallel.

        Args:
            context: Workflow context
            input_data: Path to project root

        Returns:
            ReadinessCheckResult with all validation outcomes
        """
        # Run all validation checks concurrently
        import asyncio

        tasks = [prim.execute(context, input_data) for prim in self.validation_primitives]
        results = await asyncio.gather(*tasks)

        # Create readiness result from individual results
        return ReadinessCheckResult.from_results(list(results))
