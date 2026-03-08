"""Skill-specific error types."""

from __future__ import annotations


class SkillError(Exception):
    """Base exception for skill-related errors."""


class SkillNotFoundError(SkillError):
    """Raised when a requested skill is not registered."""

    def __init__(self, name: str) -> None:
        """Initialize with the missing skill name.

        Args:
            name: The skill name that was not found.
        """
        self.name = name
        super().__init__(f"Skill not found: {name}")


class SkillValidationError(SkillError):
    """Raised when a SKILL.md or SkillDescriptor fails validation."""

    def __init__(self, message: str, field: str | None = None) -> None:
        """Initialize with details about the validation failure.

        Args:
            message: Description of the validation error.
            field: Optional name of the invalid field.
        """
        self.field = field
        super().__init__(message)


class SkillLoadError(SkillError):
    """Raised when a SKILL.md file cannot be parsed."""

    def __init__(self, path: str, reason: str) -> None:
        """Initialize with path and parse failure reason.

        Args:
            path: Path to the SKILL.md file that failed to load.
            reason: Description of why loading failed.
        """
        self.path = path
        self.reason = reason
        super().__init__(f"Failed to load {path}: {reason}")
