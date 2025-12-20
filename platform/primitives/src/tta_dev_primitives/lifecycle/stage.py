"""Stage enumeration and stage management for the development lifecycle.

This module defines the software development lifecycle stages and provides
stage management primitives for validating project readiness and transitions.
"""

from __future__ import annotations

from enum import Enum


class Stage(Enum):
    """Software development lifecycle stages.

    Each stage represents a phase in the development lifecycle, with specific
    entry and exit criteria that must be met before transitioning.

    Attributes:
        EXPERIMENTATION: Rapid prototyping and idea validation
        TESTING: Automated testing and validation
        STAGING: Pre-production validation
        DEPLOYMENT: Production deployment and release
        PRODUCTION: Live monitoring and maintenance
    """

    EXPERIMENTATION = "experimentation"
    TESTING = "testing"
    STAGING = "staging"
    DEPLOYMENT = "deployment"
    PRODUCTION = "production"

    def __str__(self) -> str:
        """Return human-readable stage name."""
        return self.value.title()

    def __lt__(self, other: Stage) -> bool:
        """Compare stages for ordering.

        Args:
            other: Stage to compare against

        Returns:
            True if this stage comes before other stage
        """
        if not isinstance(other, Stage):
            return NotImplemented

        order = [
            Stage.EXPERIMENTATION,
            Stage.TESTING,
            Stage.STAGING,
            Stage.DEPLOYMENT,
            Stage.PRODUCTION,
        ]
        return order.index(self) < order.index(other)

    @classmethod
    def from_string(cls, value: str) -> Stage:
        """Create Stage from string value.

        Args:
            value: String representation of stage

        Returns:
            Stage enum value

        Raises:
            ValueError: If value is not a valid stage
        """
        try:
            return cls(value.lower())
        except ValueError as e:
            valid_values = [s.value for s in cls]
            raise ValueError(
                f"Invalid stage '{value}'. Must be one of: {', '.join(valid_values)}"
            ) from e


# Legacy alias for backward compatibility
DevelopmentStage = Stage


class StageTransitionError(Exception):
    """Raised when a stage transition fails validation."""

    def __init__(self, message: str, blockers: list[str] | None = None) -> None:
        """Initialize stage transition error.

        Args:
            message: Error message
            blockers: List of blocking issues preventing transition
        """
        super().__init__(message)
        self.blockers = blockers or []
