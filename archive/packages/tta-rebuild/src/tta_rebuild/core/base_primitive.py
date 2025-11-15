"""Core base primitive and context for TTA rebuild."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Generic, TypeVar

TInput = TypeVar("TInput")
TOutput = TypeVar("TOutput")


@dataclass
class TTAContext:
    """Context passed through all TTA primitives.

    Attributes:
        workflow_id: Unique identifier for the workflow session
        correlation_id: ID for tracing related operations
        timestamp: When this context was created
        metaconcepts: List of active metaconcept names guiding behavior
        player_boundaries: Player's content preferences and boundaries
        session_state: Session-level state shared across primitives
        universe_id: ID of the current universe/timeline (optional)
    """

    workflow_id: str
    correlation_id: str
    timestamp: datetime
    metaconcepts: list[str]
    player_boundaries: dict[str, Any]
    session_state: dict[str, Any] = field(default_factory=dict)
    universe_id: str | None = None

    def with_universe(self, universe_id: str) -> "TTAContext":
        """Create a new context with updated universe_id.

        Args:
            universe_id: New universe ID

        Returns:
            New TTAContext with updated universe_id
        """
        return TTAContext(
            workflow_id=self.workflow_id,
            correlation_id=self.correlation_id,
            timestamp=self.timestamp,
            metaconcepts=self.metaconcepts,
            player_boundaries=self.player_boundaries,
            session_state=self.session_state,
            universe_id=universe_id,
        )

    def with_metaconcepts(self, metaconcepts: list[str]) -> "TTAContext":
        """Create a new context with updated metaconcepts.

        Args:
            metaconcepts: New list of metaconcept names

        Returns:
            New TTAContext with updated metaconcepts
        """
        return TTAContext(
            workflow_id=self.workflow_id,
            correlation_id=self.correlation_id,
            timestamp=self.timestamp,
            metaconcepts=metaconcepts,
            player_boundaries=self.player_boundaries,
            session_state=self.session_state,
            universe_id=self.universe_id,
        )


class TTAPrimitive(ABC, Generic[TInput, TOutput]):
    """Base class for all TTA primitives.

    TTA primitives are composable, async operations that:
    - Accept typed input data
    - Receive context for state and guidance
    - Apply metaconcepts to guide behavior
    - Return typed output data

    Type Parameters:
        TInput: Input data type
        TOutput: Output data type
    """

    def __init__(self, name: str) -> None:
        """Initialize primitive.

        Args:
            name: Human-readable name for this primitive
        """
        self.name = name

    @abstractmethod
    async def execute(
        self,
        input_data: TInput,
        context: TTAContext,
    ) -> TOutput:
        """Execute the primitive with given input and context.

        This is the main entry point for primitive execution.
        Subclasses should implement this method to define primitive behavior.

        Args:
            input_data: Typed input data for this primitive
            context: Execution context with state and guidance

        Returns:
            Typed output data from this primitive

        Raises:
            TTAPrimitiveError: If execution fails
        """

    async def _validate_input(self, input_data: TInput) -> None:
        """Validate input data before execution.

        Override this method to add custom input validation.

        Args:
            input_data: Input data to validate

        Raises:
            ValidationError: If input is invalid
        """
        # Default: no validation

    async def _apply_metaconcepts(
        self,
        context: TTAContext,
    ) -> dict[str, Any]:
        """Apply metaconcepts to guide primitive behavior.

        Override this method to customize how metaconcepts affect behavior.

        Args:
            context: Context containing active metaconcepts

        Returns:
            Dictionary of metaconcept name -> guidance parameters
        """
        # Default: all metaconcepts active
        return dict.fromkeys(context.metaconcepts, True)

    def __repr__(self) -> str:
        """String representation of primitive."""
        return f"{self.__class__.__name__}(name={self.name!r})"


class TTAPrimitiveError(Exception):
    """Base exception for TTA primitive errors."""

    def __init__(
        self,
        message: str,
        primitive_name: str | None = None,
        context: TTAContext | None = None,
    ) -> None:
        """Initialize error.

        Args:
            message: Error message
            primitive_name: Name of primitive that failed (optional)
            context: Execution context when error occurred (optional)
        """
        super().__init__(message)
        self.primitive_name = primitive_name
        self.context = context


class ValidationError(TTAPrimitiveError):
    """Raised when input validation fails."""


class ExecutionError(TTAPrimitiveError):
    """Raised when primitive execution fails."""
