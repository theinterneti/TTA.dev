"""Tests for CharacterStatePrimitive."""

from datetime import UTC, datetime

import pytest

from tta_rebuild.core import TTAContext, ValidationError
from tta_rebuild.narrative.character_state import (
    CharacterInteraction,
    CharacterStatePrimitive,
)


@pytest.fixture
def character_primitive():
    """Create CharacterStatePrimitive for testing."""
    return CharacterStatePrimitive()


@pytest.fixture
def test_context():
    """Create test context."""
    return TTAContext(
        workflow_id="test-workflow",
        correlation_id="test-correlation",
        timestamp=datetime.now(UTC),
        metaconcepts=["character_development"],
        player_boundaries={},
    )


class TestCharacterStateBasics:
    """Test basic character state operations."""

    @pytest.mark.asyncio
    async def test_create_new_character(
        self, character_primitive: CharacterStatePrimitive, test_context: TTAContext
    ):
        """Test creating a new character."""
        interaction = CharacterInteraction(
            character_id="hero",
            scene_context="Hero enters the village",
        )

        response = await character_primitive.execute(interaction, test_context)

        assert response.character_id == "hero"
        assert response.emotion == "neutral"  # Default emotion
        assert response.consistency_score >= 0.0
        assert response.personality_alignment >= 0.0

    @pytest.mark.asyncio
    async def test_character_persists(
        self, character_primitive: CharacterStatePrimitive, test_context: TTAContext
    ):
        """Test character state persists across interactions."""
        # First interaction
        interaction1 = CharacterInteraction(
            character_id="hero",
            scene_context="Hero finds a sword",
        )
        await character_primitive.execute(interaction1, test_context)

        # Second interaction
        interaction2 = CharacterInteraction(
            character_id="hero",
            scene_context="Hero faces an enemy",
        )
        response2 = await character_primitive.execute(interaction2, test_context)

        # Character should exist
        character = character_primitive.get_character("hero")
        assert character is not None
        assert character.character_id == "hero"


class TestEmotionalState:
    """Test emotional state tracking."""

    @pytest.mark.asyncio
    async def test_emotion_update_from_trigger(
        self, character_primitive: CharacterStatePrimitive, test_context: TTAContext
    ):
        """Test emotion updates based on triggers."""
        interaction = CharacterInteraction(
            character_id="hero",
            scene_context="A tense situation",
            emotional_trigger="Hero feels fear from the approaching danger",
        )

        response = await character_primitive.execute(interaction, test_context)

        assert response.emotion == "fearful"

    @pytest.mark.asyncio
    async def test_multiple_emotion_triggers(
        self, character_primitive: CharacterStatePrimitive, test_context: TTAContext
    ):
        """Test emotion changes across interactions."""
        # Fear
        interaction1 = CharacterInteraction(
            character_id="hero",
            scene_context="Danger approaches",
            emotional_trigger="fear grips the hero",
        )
        response1 = await character_primitive.execute(interaction1, test_context)
        assert response1.emotion == "fearful"

        # Hope
        interaction2 = CharacterInteraction(
            character_id="hero",
            scene_context="Ally arrives",
            emotional_trigger="hope returns to the hero",
        )
        response2 = await character_primitive.execute(interaction2, test_context)
        assert response2.emotion == "hopeful"


class TestRelationshipTracking:
    """Test relationship management."""

    @pytest.mark.asyncio
    async def test_relationship_initialization(
        self, character_primitive: CharacterStatePrimitive, test_context: TTAContext
    ):
        """Test relationships start at neutral."""
        interaction = CharacterInteraction(
            character_id="hero",
            scene_context="Hero meets ally",
            interacting_with=["ally"],
        )

        await character_primitive.execute(interaction, test_context)

        relationship = character_primitive.get_relationship("hero", "ally")
        # Should be neutral (0.0) or slightly modified
        assert -1.0 <= relationship <= 1.0

    @pytest.mark.asyncio
    async def test_positive_relationship_change(
        self, character_primitive: CharacterStatePrimitive, test_context: TTAContext
    ):
        """Test positive interactions improve relationships."""
        interaction = CharacterInteraction(
            character_id="hero",
            scene_context="Hero receives help from ally",
            interacting_with=["ally"],
        )

        response = await character_primitive.execute(interaction, test_context)

        # Should have positive relationship change
        assert "ally" in response.relationship_changes
        assert response.relationship_changes["ally"] >= 0.0

    @pytest.mark.asyncio
    async def test_negative_relationship_change(
        self, character_primitive: CharacterStatePrimitive, test_context: TTAContext
    ):
        """Test negative interactions harm relationships."""
        interaction = CharacterInteraction(
            character_id="hero",
            scene_context="Hero has a negative conflict with rival",
            interacting_with=["rival"],
        )

        response = await character_primitive.execute(interaction, test_context)

        # Should have negative relationship change
        assert "rival" in response.relationship_changes
        assert response.relationship_changes["rival"] <= 0.0

    @pytest.mark.asyncio
    async def test_relationship_bounds(
        self, character_primitive: CharacterStatePrimitive, test_context: TTAContext
    ):
        """Test relationships stay within bounds."""
        # Many positive interactions
        for _ in range(20):
            interaction = CharacterInteraction(
                character_id="hero",
                scene_context="Hero receives positive help from ally",
                interacting_with=["ally"],
            )
            await character_primitive.execute(interaction, test_context)

        relationship = character_primitive.get_relationship("hero", "ally")
        assert -1.0 <= relationship <= 1.0


class TestDevelopmentGoals:
    """Test character development tracking."""

    @pytest.mark.asyncio
    async def test_development_goal_creation(
        self, character_primitive: CharacterStatePrimitive, test_context: TTAContext
    ):
        """Test development goals are created."""
        interaction = CharacterInteraction(
            character_id="hero",
            scene_context="Hero begins training",
            development_opportunity="Learn swordsmanship",
        )

        response = await character_primitive.execute(interaction, test_context)

        assert "Learn swordsmanship" in response.development_progress
        assert response.development_progress["Learn swordsmanship"] > 0.0

    @pytest.mark.asyncio
    async def test_development_progress_increments(
        self, character_primitive: CharacterStatePrimitive, test_context: TTAContext
    ):
        """Test development goals progress over time."""
        goal = "Master magic"

        # First interaction
        interaction1 = CharacterInteraction(
            character_id="mage",
            scene_context="Mage studies spells",
            development_opportunity=goal,
        )
        response1 = await character_primitive.execute(interaction1, test_context)
        initial_progress = response1.development_progress[goal]

        # Second interaction
        interaction2 = CharacterInteraction(
            character_id="mage",
            scene_context="Mage practices more",
            development_opportunity=goal,
        )
        response2 = await character_primitive.execute(interaction2, test_context)
        final_progress = response2.development_progress[goal]

        assert final_progress > initial_progress

    @pytest.mark.asyncio
    async def test_development_goal_completion(
        self, character_primitive: CharacterStatePrimitive, test_context: TTAContext
    ):
        """Test development goals cap at 1.0."""
        goal = "Short goal"

        # Many interactions
        for _ in range(15):
            interaction = CharacterInteraction(
                character_id="hero",
                scene_context="Hero works on goal",
                development_opportunity=goal,
            )
            await character_primitive.execute(interaction, test_context)

        character = character_primitive.get_character("hero")
        assert character is not None
        assert character.development_goals[goal] <= 1.0


class TestMemoryManagement:
    """Test character memory tracking."""

    @pytest.mark.asyncio
    async def test_memory_stores_events(
        self, character_primitive: CharacterStatePrimitive, test_context: TTAContext
    ):
        """Test character remembers events."""
        interaction = CharacterInteraction(
            character_id="hero",
            scene_context="Important scene",
            story_events=["Hero finds magical artifact", "Hero meets mentor"],
        )

        await character_primitive.execute(interaction, test_context)

        character = character_primitive.get_character("hero")
        assert character is not None
        assert "Hero finds magical artifact" in character.memory
        assert "Hero meets mentor" in character.memory

    @pytest.mark.asyncio
    async def test_memory_accumulates(
        self, character_primitive: CharacterStatePrimitive, test_context: TTAContext
    ):
        """Test memory grows over interactions."""
        # First interaction
        interaction1 = CharacterInteraction(
            character_id="hero",
            scene_context="Scene 1",
            story_events=["Event 1"],
        )
        await character_primitive.execute(interaction1, test_context)

        # Second interaction
        interaction2 = CharacterInteraction(
            character_id="hero",
            scene_context="Scene 2",
            story_events=["Event 2"],
        )
        await character_primitive.execute(interaction2, test_context)

        character = character_primitive.get_character("hero")
        assert character is not None
        assert "Event 1" in character.memory
        assert "Event 2" in character.memory

    @pytest.mark.asyncio
    async def test_memory_pruning(
        self, character_primitive: CharacterStatePrimitive, test_context: TTAContext
    ):
        """Test old memories are pruned."""
        # Add many events
        for i in range(15):
            interaction = CharacterInteraction(
                character_id="hero",
                scene_context=f"Scene {i}",
                story_events=[f"Event {i}"],
            )
            await character_primitive.execute(interaction, test_context)

        character = character_primitive.get_character("hero")
        assert character is not None
        # Should keep only recent memories (10)
        assert len(character.memory) == 10
        # Old events should be gone
        assert "Event 0" not in character.memory
        # Recent events should remain
        assert "Event 14" in character.memory


class TestArcProgression:
    """Test character arc tracking."""

    @pytest.mark.asyncio
    async def test_default_arc_stage(
        self, character_primitive: CharacterStatePrimitive, test_context: TTAContext
    ):
        """Test new characters start in setup stage."""
        interaction = CharacterInteraction(
            character_id="hero",
            scene_context="Beginning of story",
        )

        await character_primitive.execute(interaction, test_context)

        character = character_primitive.get_character("hero")
        assert character is not None
        assert character.arc_stage == "setup"

    @pytest.mark.asyncio
    async def test_arc_stage_suggestions(
        self, character_primitive: CharacterStatePrimitive, test_context: TTAContext
    ):
        """Test arc suggestions match current stage."""
        interaction = CharacterInteraction(
            character_id="hero",
            scene_context="Hero's ordinary world",
        )

        response = await character_primitive.execute(interaction, test_context)

        # Setup stage should suggest establishing ordinary world
        assert "ordinary world" in response.suggested_arc_direction.lower()

    @pytest.mark.asyncio
    async def test_update_arc_stage(
        self, character_primitive: CharacterStatePrimitive, test_context: TTAContext
    ):
        """Test manual arc stage updates."""
        # Create character
        interaction = CharacterInteraction(
            character_id="hero",
            scene_context="Start",
        )
        await character_primitive.execute(interaction, test_context)

        # Update arc stage
        character_primitive.update_arc_stage("hero", "development")

        character = character_primitive.get_character("hero")
        assert character is not None
        assert character.arc_stage == "development"

    @pytest.mark.asyncio
    async def test_invalid_arc_stage_raises_error(
        self, character_primitive: CharacterStatePrimitive, test_context: TTAContext
    ):
        """Test invalid arc stage raises ValidationError."""
        # Create character
        interaction = CharacterInteraction(
            character_id="hero",
            scene_context="Start",
        )
        await character_primitive.execute(interaction, test_context)

        # Try invalid stage
        with pytest.raises(ValidationError, match="Invalid arc stage"):
            character_primitive.update_arc_stage("hero", "invalid_stage")


class TestValidation:
    """Test input validation."""

    @pytest.mark.asyncio
    async def test_empty_character_id_raises_error(
        self, character_primitive: CharacterStatePrimitive, test_context: TTAContext
    ):
        """Test empty character_id raises ValidationError."""
        interaction = CharacterInteraction(
            character_id="",
            scene_context="Some scene",
        )

        with pytest.raises(ValidationError, match="character_id is required"):
            await character_primitive.execute(interaction, test_context)

    @pytest.mark.asyncio
    async def test_empty_scene_context_raises_error(
        self, character_primitive: CharacterStatePrimitive, test_context: TTAContext
    ):
        """Test empty scene_context raises ValidationError."""
        interaction = CharacterInteraction(
            character_id="hero",
            scene_context="",
        )

        with pytest.raises(ValidationError, match="scene_context is required"):
            await character_primitive.execute(interaction, test_context)


class TestUtilityMethods:
    """Test utility methods."""

    @pytest.mark.asyncio
    async def test_get_character(
        self, character_primitive: CharacterStatePrimitive, test_context: TTAContext
    ):
        """Test getting character by ID."""
        # Create character
        interaction = CharacterInteraction(
            character_id="hero",
            scene_context="Scene",
        )
        await character_primitive.execute(interaction, test_context)

        # Get character
        character = character_primitive.get_character("hero")
        assert character is not None
        assert character.character_id == "hero"

    @pytest.mark.asyncio
    async def test_get_nonexistent_character(self, character_primitive: CharacterStatePrimitive):
        """Test getting nonexistent character returns None."""
        character = character_primitive.get_character("nonexistent")
        assert character is None

    @pytest.mark.asyncio
    async def test_get_all_characters(
        self, character_primitive: CharacterStatePrimitive, test_context: TTAContext
    ):
        """Test getting all characters."""
        # Create multiple characters
        for char_id in ["hero", "villain", "mentor"]:
            interaction = CharacterInteraction(
                character_id=char_id,
                scene_context="Scene",
            )
            await character_primitive.execute(interaction, test_context)

        # Get all
        characters = character_primitive.get_all_characters()
        assert len(characters) == 3
        char_ids = {c.character_id for c in characters}
        assert char_ids == {"hero", "villain", "mentor"}

    @pytest.mark.asyncio
    async def test_set_development_goal(
        self, character_primitive: CharacterStatePrimitive, test_context: TTAContext
    ):
        """Test manually setting development goals."""
        # Create character
        interaction = CharacterInteraction(
            character_id="hero",
            scene_context="Start",
        )
        await character_primitive.execute(interaction, test_context)

        # Set goal
        character_primitive.set_development_goal("hero", "Save the kingdom", 0.3)

        character = character_primitive.get_character("hero")
        assert character is not None
        assert "Save the kingdom" in character.development_goals
        assert character.development_goals["Save the kingdom"] == 0.3


class TestDialogueGeneration:
    """Test dialogue and internal monologue generation."""

    @pytest.mark.asyncio
    async def test_dialogue_includes_character_name(
        self, character_primitive: CharacterStatePrimitive, test_context: TTAContext
    ):
        """Test dialogue includes character name."""
        interaction = CharacterInteraction(
            character_id="hero",
            scene_context="Hero speaks",
        )

        response = await character_primitive.execute(interaction, test_context)

        assert "Hero" in response.dialogue

    @pytest.mark.asyncio
    async def test_internal_monologue_reflects_goals(
        self, character_primitive: CharacterStatePrimitive, test_context: TTAContext
    ):
        """Test internal monologue reflects active goals."""
        # Set a goal
        character_primitive.set_development_goal("hero", "Find the artifact", 0.5)

        interaction = CharacterInteraction(
            character_id="hero",
            scene_context="Hero explores",
        )

        response = await character_primitive.execute(interaction, test_context)

        # Should mention the goal
        assert "artifact" in response.internal_monologue.lower()


class TestConsistencyScoring:
    """Test consistency and alignment scoring."""

    @pytest.mark.asyncio
    async def test_consistency_score_in_range(
        self, character_primitive: CharacterStatePrimitive, test_context: TTAContext
    ):
        """Test consistency score is 0.0-1.0."""
        interaction = CharacterInteraction(
            character_id="hero",
            scene_context="Normal scene",
        )

        response = await character_primitive.execute(interaction, test_context)

        assert 0.0 <= response.consistency_score <= 1.0

    @pytest.mark.asyncio
    async def test_personality_alignment_in_range(
        self, character_primitive: CharacterStatePrimitive, test_context: TTAContext
    ):
        """Test personality alignment is 0.0-1.0."""
        interaction = CharacterInteraction(
            character_id="hero",
            scene_context="Normal scene",
        )

        response = await character_primitive.execute(interaction, test_context)

        assert 0.0 <= response.personality_alignment <= 1.0
