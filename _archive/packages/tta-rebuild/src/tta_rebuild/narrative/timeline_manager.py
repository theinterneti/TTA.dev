"""Timeline management primitive for TTA narrative engine.

This module implements timeline tracking, consistency validation,
and branch point management for story progression.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from ..core import TTAContext, TTAPrimitive, ValidationError


@dataclass
class TimelineEvent:
    """Single event in the timeline."""

    event_id: str
    event_type: str  # "story_beat", "choice", "consequence", "branch_point"
    event_data: dict[str, Any]
    timestamp: int  # Position in timeline (0-based)
    causal_links: list[str]  # Event IDs this event depends on
    character_ids: list[str]  # Characters involved
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class BranchPoint:
    """Point where narrative can diverge."""

    branch_id: str
    position: int
    description: str
    available_choices: list[dict[str, Any]]
    requires_events: list[str]  # Events that must occur before this branch


@dataclass
class TimelineUpdate:
    """Input for timeline update operations."""

    universe_id: str
    event_type: str
    event_data: dict[str, Any]
    timestamp: int
    causal_links: list[str] = field(default_factory=list)
    character_ids: list[str] = field(default_factory=list)


@dataclass
class TimelineState:
    """Current state of a timeline."""

    universe_id: str
    current_position: int
    event_history: list[TimelineEvent]
    available_branches: list[BranchPoint]
    timeline_coherence_score: float  # 0.0-1.0
    inconsistencies: list[str]
    suggested_fixes: list[str]


class TimelineManagerPrimitive(TTAPrimitive[TimelineUpdate, TimelineState]):
    """Manage story timelines with consistency validation.

    This primitive:
    1. Tracks story events across timeline
    2. Validates causal relationships
    3. Identifies branch points for player choices
    4. Detects and reports timeline inconsistencies
    5. Suggests fixes for detected issues

    Features:
    - Multi-universe support
    - Causality validation
    - Coherence scoring
    - Branch point tracking
    """

    def __init__(self, name: str = "TimelineManager") -> None:
        """Initialize timeline manager.

        Args:
            name: Name for this primitive instance
        """
        super().__init__(name)
        # Storage for all universe timelines
        self._timelines: dict[str, list[TimelineEvent]] = {}
        # Current positions per universe
        self._positions: dict[str, int] = {}
        # Detected branch points per universe
        self._branches: dict[str, list[BranchPoint]] = {}

    async def execute(
        self,
        input_data: TimelineUpdate,
        context: TTAContext,
    ) -> TimelineState:
        """Update timeline and return current state.

        Args:
            input_data: Timeline update information
            context: Workflow context

        Returns:
            Current timeline state with validation results

        Raises:
            ValidationError: If update violates timeline consistency
        """
        # Validate input
        self._validate_update(input_data)

        # Initialize universe if new
        if input_data.universe_id not in self._timelines:
            self._timelines[input_data.universe_id] = []
            self._positions[input_data.universe_id] = 0
            self._branches[input_data.universe_id] = []

        # Create timeline event
        event = self._create_event(input_data)

        # Validate causality
        inconsistencies = self._validate_causality(input_data.universe_id, event)

        # Add event to timeline
        self._add_event(input_data.universe_id, event)

        # Update position
        self._positions[input_data.universe_id] = max(
            self._positions[input_data.universe_id],
            event.timestamp + 1,
        )

        # Detect branch points
        if event.event_type == "choice":
            self._detect_branch_point(input_data.universe_id, event)

        # Calculate coherence score
        coherence_score = self._calculate_coherence(input_data.universe_id)

        # Generate suggested fixes
        suggested_fixes = self._generate_fixes(inconsistencies)

        # Build and return state
        return TimelineState(
            universe_id=input_data.universe_id,
            current_position=self._positions[input_data.universe_id],
            event_history=self._timelines[input_data.universe_id].copy(),
            available_branches=self._branches[input_data.universe_id].copy(),
            timeline_coherence_score=coherence_score,
            inconsistencies=inconsistencies,
            suggested_fixes=suggested_fixes,
        )

    def _validate_update(self, update: TimelineUpdate) -> None:
        """Validate update input.

        Args:
            update: Update to validate

        Raises:
            ValidationError: If update is invalid
        """
        if not update.universe_id:
            raise ValidationError("universe_id is required")

        if update.timestamp < 0:
            raise ValidationError(f"timestamp must be >= 0, got {update.timestamp}")

        valid_event_types = {"story_beat", "choice", "consequence", "branch_point"}
        if update.event_type not in valid_event_types:
            raise ValidationError(
                f"event_type must be one of {valid_event_types}, got {update.event_type}"
            )

    def _create_event(self, update: TimelineUpdate) -> TimelineEvent:
        """Create timeline event from update.

        Args:
            update: Update data

        Returns:
            Timeline event
        """
        # Generate unique event ID
        event_id = f"{update.universe_id}_t{update.timestamp}_{update.event_type}"

        return TimelineEvent(
            event_id=event_id,
            event_type=update.event_type,
            event_data=update.event_data,
            timestamp=update.timestamp,
            causal_links=update.causal_links,
            character_ids=update.character_ids,
        )

    def _validate_causality(self, universe_id: str, event: TimelineEvent) -> list[str]:
        """Validate causal relationships.

        Args:
            universe_id: Universe to check
            event: Event being added

        Returns:
            List of inconsistency descriptions (empty if valid)
        """
        inconsistencies: list[str] = []
        timeline = self._timelines[universe_id]

        # Check each causal link
        for link in event.causal_links:
            # Find the linked event
            linked_event = next(
                (e for e in timeline if e.event_id == link),
                None,
            )

            if linked_event is None:
                inconsistencies.append(
                    f"Event {event.event_id} references non-existent event {link}"
                )
            elif linked_event.timestamp >= event.timestamp:
                inconsistencies.append(
                    f"Event {event.event_id} at t={event.timestamp} "
                    f"depends on {link} at t={linked_event.timestamp} "
                    "(cause must come before effect)"
                )

        return inconsistencies

    def _add_event(self, universe_id: str, event: TimelineEvent) -> None:
        """Add event to timeline in chronological order.

        Args:
            universe_id: Universe timeline
            event: Event to add
        """
        timeline = self._timelines[universe_id]

        # Insert in sorted position
        insert_pos = 0
        for i, existing in enumerate(timeline):
            if existing.timestamp <= event.timestamp:
                insert_pos = i + 1
            else:
                break

        timeline.insert(insert_pos, event)

    def _detect_branch_point(self, universe_id: str, event: TimelineEvent) -> None:
        """Detect and create branch point from choice event.

        Args:
            universe_id: Universe timeline
            event: Choice event
        """
        # Extract choices from event data
        choices = event.event_data.get("choices", [])

        if not choices:
            return

        branch = BranchPoint(
            branch_id=f"branch_{event.event_id}",
            position=event.timestamp,
            description=event.event_data.get("description", "Player choice point"),
            available_choices=choices,
            requires_events=event.causal_links,
        )

        self._branches[universe_id].append(branch)

    def _calculate_coherence(self, universe_id: str) -> float:
        """Calculate timeline coherence score.

        Args:
            universe_id: Universe to score

        Returns:
            Coherence score 0.0-1.0 (1.0 = perfect)
        """
        timeline = self._timelines[universe_id]

        if not timeline:
            return 1.0

        # Count valid vs total causal relationships
        total_links = 0
        valid_links = 0

        for event in timeline:
            total_links += len(event.causal_links)

            for link in event.causal_links:
                linked_event = next(
                    (e for e in timeline if e.event_id == link),
                    None,
                )

                if linked_event and linked_event.timestamp < event.timestamp:
                    valid_links += 1

        # Score based on causality validity
        if total_links == 0:
            return 1.0

        return valid_links / total_links

    def _generate_fixes(self, inconsistencies: list[str]) -> list[str]:
        """Generate suggested fixes for inconsistencies.

        Args:
            inconsistencies: List of detected issues

        Returns:
            List of suggested fixes
        """
        fixes: list[str] = []

        for issue in inconsistencies:
            if "non-existent event" in issue:
                fixes.append("Remove invalid causal link or add missing prerequisite event")
            elif "cause must come before effect" in issue:
                fixes.append("Adjust event timestamp to respect causal ordering")

        return fixes

    def get_timeline(self, universe_id: str) -> list[TimelineEvent]:
        """Get complete timeline for a universe.

        Args:
            universe_id: Universe to retrieve

        Returns:
            List of timeline events in chronological order
        """
        return self._timelines.get(universe_id, []).copy()

    def get_position(self, universe_id: str) -> int:
        """Get current position in timeline.

        Args:
            universe_id: Universe to check

        Returns:
            Current timeline position (0 if universe doesn't exist)
        """
        return self._positions.get(universe_id, 0)

    def get_branches(self, universe_id: str) -> list[BranchPoint]:
        """Get available branch points for a universe.

        Args:
            universe_id: Universe to check

        Returns:
            List of branch points
        """
        return self._branches.get(universe_id, []).copy()
