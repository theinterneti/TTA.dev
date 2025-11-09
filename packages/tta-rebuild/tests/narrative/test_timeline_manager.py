"""Tests for TimelineManagerPrimitive."""

from datetime import UTC, datetime

import pytest

from tta_rebuild.core import TTAContext, ValidationError
from tta_rebuild.narrative.timeline_manager import (
    TimelineManagerPrimitive,
    TimelineUpdate,
)


@pytest.fixture
def context():
    """Create test context."""
    return TTAContext(
        workflow_id="test-timeline",
        correlation_id="test-correlation",
        timestamp=datetime.now(UTC),
        metaconcepts=["Ensure Narrative Quality"],
        player_boundaries={},
    )


@pytest.fixture
def timeline_manager():
    """Create timeline manager instance."""
    return TimelineManagerPrimitive()


class TestTimelineManagerBasics:
    """Test basic timeline operations."""

    @pytest.mark.asyncio
    async def test_add_event_to_empty_timeline(self, timeline_manager, context):
        """Test adding first event to timeline."""
        update = TimelineUpdate(
            universe_id="universe-001",
            event_type="story_beat",
            event_data={"description": "Story begins"},
            timestamp=0,
        )

        state = await timeline_manager.execute(update, context)

        assert state.universe_id == "universe-001"
        assert state.current_position == 1
        assert len(state.event_history) == 1
        assert state.event_history[0].event_type == "story_beat"
        assert state.timeline_coherence_score == 1.0
        assert len(state.inconsistencies) == 0

    @pytest.mark.asyncio
    async def test_add_multiple_events_in_order(self, timeline_manager, context):
        """Test adding events in chronological order."""
        # First event
        update1 = TimelineUpdate(
            universe_id="universe-001",
            event_type="story_beat",
            event_data={"description": "Event 1"},
            timestamp=0,
        )
        await timeline_manager.execute(update1, context)

        # Second event
        update2 = TimelineUpdate(
            universe_id="universe-001",
            event_type="story_beat",
            event_data={"description": "Event 2"},
            timestamp=1,
        )
        state = await timeline_manager.execute(update2, context)

        assert len(state.event_history) == 2
        assert state.current_position == 2
        assert state.event_history[0].timestamp == 0
        assert state.event_history[1].timestamp == 1


class TestCausalityValidation:
    """Test causality and consistency checking."""

    @pytest.mark.asyncio
    async def test_valid_causal_link(self, timeline_manager, context):
        """Test event with valid causal dependency."""
        # First event
        update1 = TimelineUpdate(
            universe_id="universe-001",
            event_type="story_beat",
            event_data={"description": "Cause"},
            timestamp=0,
        )
        state1 = await timeline_manager.execute(update1, context)
        event1_id = state1.event_history[0].event_id

        # Second event referencing first
        update2 = TimelineUpdate(
            universe_id="universe-001",
            event_type="consequence",
            event_data={"description": "Effect"},
            timestamp=1,
            causal_links=[event1_id],
        )
        state2 = await timeline_manager.execute(update2, context)

        assert state2.timeline_coherence_score == 1.0
        assert len(state2.inconsistencies) == 0

    @pytest.mark.asyncio
    async def test_invalid_causal_link_nonexistent(self, timeline_manager, context):
        """Test event referencing non-existent event."""
        update = TimelineUpdate(
            universe_id="universe-001",
            event_type="consequence",
            event_data={"description": "Effect"},
            timestamp=1,
            causal_links=["nonexistent_event"],
        )

        state = await timeline_manager.execute(update, context)

        assert len(state.inconsistencies) > 0
        assert "non-existent" in state.inconsistencies[0]
        assert state.timeline_coherence_score < 1.0

    @pytest.mark.asyncio
    async def test_invalid_causal_link_time_paradox(self, timeline_manager, context):
        """Test event depending on future event (time paradox)."""
        # Add future event first
        update1 = TimelineUpdate(
            universe_id="universe-001",
            event_type="story_beat",
            event_data={"description": "Future"},
            timestamp=2,
        )
        state1 = await timeline_manager.execute(update1, context)
        future_event_id = state1.event_history[0].event_id

        # Try to add past event that depends on future
        update2 = TimelineUpdate(
            universe_id="universe-001",
            event_type="consequence",
            event_data={"description": "Past"},
            timestamp=1,
            causal_links=[future_event_id],
        )
        state2 = await timeline_manager.execute(update2, context)

        assert len(state2.inconsistencies) > 0
        assert "cause must come before effect" in state2.inconsistencies[0]


class TestBranchPointDetection:
    """Test branch point tracking."""

    @pytest.mark.asyncio
    async def test_detect_branch_from_choice(self, timeline_manager, context):
        """Test branch point creation from choice event."""
        update = TimelineUpdate(
            universe_id="universe-001",
            event_type="choice",
            event_data={
                "description": "Choose your path",
                "choices": [
                    {"id": "choice_a", "text": "Go left"},
                    {"id": "choice_b", "text": "Go right"},
                ],
            },
            timestamp=0,
        )

        state = await timeline_manager.execute(update, context)

        assert len(state.available_branches) == 1
        branch = state.available_branches[0]
        assert branch.position == 0
        assert len(branch.available_choices) == 2

    @pytest.mark.asyncio
    async def test_multiple_branch_points(self, timeline_manager, context):
        """Test tracking multiple branch points."""
        # First choice
        update1 = TimelineUpdate(
            universe_id="universe-001",
            event_type="choice",
            event_data={
                "choices": [
                    {"id": "c1", "text": "Option 1"},
                    {"id": "c2", "text": "Option 2"},
                ]
            },
            timestamp=0,
        )
        await timeline_manager.execute(update1, context)

        # Second choice
        update2 = TimelineUpdate(
            universe_id="universe-001",
            event_type="choice",
            event_data={
                "choices": [
                    {"id": "c3", "text": "Option 3"},
                    {"id": "c4", "text": "Option 4"},
                ]
            },
            timestamp=2,
        )
        state = await timeline_manager.execute(update2, context)

        assert len(state.available_branches) == 2


class TestMultipleUniverses:
    """Test independent universe tracking."""

    @pytest.mark.asyncio
    async def test_independent_universes(self, timeline_manager, context):
        """Test that universes are tracked independently."""
        # Add event to universe 1
        update1 = TimelineUpdate(
            universe_id="universe-001",
            event_type="story_beat",
            event_data={"description": "Universe 1"},
            timestamp=0,
        )
        await timeline_manager.execute(update1, context)

        # Add event to universe 2
        update2 = TimelineUpdate(
            universe_id="universe-002",
            event_type="story_beat",
            event_data={"description": "Universe 2"},
            timestamp=0,
        )
        state2 = await timeline_manager.execute(update2, context)

        # Each universe should have only its own events
        timeline1 = timeline_manager.get_timeline("universe-001")
        timeline2 = timeline_manager.get_timeline("universe-002")

        assert len(timeline1) == 1
        assert len(timeline2) == 1
        assert timeline1[0].event_data["description"] == "Universe 1"
        assert timeline2[0].event_data["description"] == "Universe 2"


class TestValidation:
    """Test input validation."""

    @pytest.mark.asyncio
    async def test_reject_empty_universe_id(self, timeline_manager, context):
        """Test that empty universe_id is rejected."""
        update = TimelineUpdate(
            universe_id="",
            event_type="story_beat",
            event_data={},
            timestamp=0,
        )

        with pytest.raises(ValidationError, match="universe_id is required"):
            await timeline_manager.execute(update, context)

    @pytest.mark.asyncio
    async def test_reject_negative_timestamp(self, timeline_manager, context):
        """Test that negative timestamp is rejected."""
        update = TimelineUpdate(
            universe_id="universe-001",
            event_type="story_beat",
            event_data={},
            timestamp=-1,
        )

        with pytest.raises(ValidationError, match="timestamp must be >= 0"):
            await timeline_manager.execute(update, context)

    @pytest.mark.asyncio
    async def test_reject_invalid_event_type(self, timeline_manager, context):
        """Test that invalid event type is rejected."""
        update = TimelineUpdate(
            universe_id="universe-001",
            event_type="invalid_type",
            event_data={},
            timestamp=0,
        )

        with pytest.raises(ValidationError, match="event_type must be one of"):
            await timeline_manager.execute(update, context)


class TestCoherenceScoring:
    """Test coherence score calculation."""

    @pytest.mark.asyncio
    async def test_perfect_coherence(self, timeline_manager, context):
        """Test timeline with perfect causality gets score 1.0."""
        # Event 1
        update1 = TimelineUpdate(
            universe_id="universe-001",
            event_type="story_beat",
            event_data={"description": "Cause"},
            timestamp=0,
        )
        state1 = await timeline_manager.execute(update1, context)

        # Event 2 properly linked
        update2 = TimelineUpdate(
            universe_id="universe-001",
            event_type="consequence",
            event_data={"description": "Effect"},
            timestamp=1,
            causal_links=[state1.event_history[0].event_id],
        )
        state2 = await timeline_manager.execute(update2, context)

        assert state2.timeline_coherence_score == 1.0

    @pytest.mark.asyncio
    async def test_imperfect_coherence(self, timeline_manager, context):
        """Test timeline with issues gets score < 1.0."""
        update = TimelineUpdate(
            universe_id="universe-001",
            event_type="consequence",
            event_data={"description": "Effect"},
            timestamp=0,
            causal_links=["nonexistent"],
        )
        state = await timeline_manager.execute(update, context)

        assert state.timeline_coherence_score < 1.0


class TestUtilityMethods:
    """Test utility/helper methods."""

    @pytest.mark.asyncio
    async def test_get_timeline(self, timeline_manager, context):
        """Test retrieving timeline."""
        update = TimelineUpdate(
            universe_id="universe-001",
            event_type="story_beat",
            event_data={},
            timestamp=0,
        )
        await timeline_manager.execute(update, context)

        timeline = timeline_manager.get_timeline("universe-001")
        assert len(timeline) == 1

    @pytest.mark.asyncio
    async def test_get_position(self, timeline_manager, context):
        """Test getting current position."""
        update = TimelineUpdate(
            universe_id="universe-001",
            event_type="story_beat",
            event_data={},
            timestamp=5,
        )
        await timeline_manager.execute(update, context)

        position = timeline_manager.get_position("universe-001")
        assert position == 6  # Next position after timestamp 5

    @pytest.mark.asyncio
    async def test_get_branches(self, timeline_manager, context):
        """Test retrieving branch points."""
        update = TimelineUpdate(
            universe_id="universe-001",
            event_type="choice",
            event_data={"choices": [{"id": "c1", "text": "Choice"}]},
            timestamp=0,
        )
        await timeline_manager.execute(update, context)

        branches = timeline_manager.get_branches("universe-001")
        assert len(branches) == 1


class TestCharacterTracking:
    """Test character involvement tracking."""

    @pytest.mark.asyncio
    async def test_track_characters_in_event(self, timeline_manager, context):
        """Test that character IDs are tracked in events."""
        update = TimelineUpdate(
            universe_id="universe-001",
            event_type="story_beat",
            event_data={"description": "Character scene"},
            timestamp=0,
            character_ids=["char_001", "char_002"],
        )

        state = await timeline_manager.execute(update, context)

        assert len(state.event_history[0].character_ids) == 2
        assert "char_001" in state.event_history[0].character_ids
        assert "char_002" in state.event_history[0].character_ids


class TestSuggestedFixes:
    """Test fix suggestions for inconsistencies."""

    @pytest.mark.asyncio
    async def test_suggest_fix_for_missing_event(self, timeline_manager, context):
        """Test fix suggestion for non-existent causal link."""
        update = TimelineUpdate(
            universe_id="universe-001",
            event_type="consequence",
            event_data={},
            timestamp=0,
            causal_links=["missing_event"],
        )

        state = await timeline_manager.execute(update, context)

        assert len(state.suggested_fixes) > 0
        assert any(
            "invalid causal link" in fix.lower() for fix in state.suggested_fixes
        )

    @pytest.mark.asyncio
    async def test_suggest_fix_for_time_paradox(self, timeline_manager, context):
        """Test fix suggestion for temporal inconsistency."""
        # Future event
        update1 = TimelineUpdate(
            universe_id="universe-001",
            event_type="story_beat",
            event_data={},
            timestamp=2,
        )
        state1 = await timeline_manager.execute(update1, context)

        # Past event depending on future
        update2 = TimelineUpdate(
            universe_id="universe-001",
            event_type="consequence",
            event_data={},
            timestamp=1,
            causal_links=[state1.event_history[0].event_id],
        )
        state2 = await timeline_manager.execute(update2, context)

        assert len(state2.suggested_fixes) > 0
        assert any("timestamp" in fix.lower() for fix in state2.suggested_fixes)
