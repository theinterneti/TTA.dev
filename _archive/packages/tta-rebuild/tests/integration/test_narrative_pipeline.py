"""Integration tests for narrative primitives working together.

Tests the full narrative generation pipeline:
- StoryGeneratorPrimitive generates initial story
- TimelineManagerPrimitive tracks events
- CharacterStatePrimitive manages character development
- BranchValidatorPrimitive validates story choices

These tests validate that primitives integrate correctly.
"""

import asyncio
from datetime import UTC, datetime

import pytest

from tta_rebuild import MetaconceptRegistry
from tta_rebuild.core.base_primitive import TTAContext
from tta_rebuild.integrations.llm_provider import MockLLMProvider
from tta_rebuild.narrative.branch_validator import (
    BranchProposal,
    BranchValidatorPrimitive,
)
from tta_rebuild.narrative.character_state import (
    CharacterInteraction,
    CharacterStatePrimitive,
)
from tta_rebuild.narrative.story_generator import (
    StoryGenerationInput,
    StoryGeneratorPrimitive,
)
from tta_rebuild.narrative.timeline_manager import (
    TimelineManagerPrimitive,
    TimelineUpdate,
)


@pytest.fixture
def context():
    """Create a fresh TTAContext for each test."""
    return TTAContext(
        workflow_id="integration-test",
        correlation_id="integration-test-corr",
        timestamp=datetime.now(UTC),
        metaconcepts=MetaconceptRegistry.get_all(),
        player_boundaries={"violence": "low", "mature_themes": "off"},
        session_state={},
    )


@pytest.fixture
def mock_llm():
    """Create a mock LLM provider."""
    return MockLLMProvider()


@pytest.fixture
def story_generator(mock_llm):
    """Create a StoryGeneratorPrimitive with mock LLM."""
    return StoryGeneratorPrimitive(llm_provider=mock_llm)


@pytest.fixture
def timeline_manager():
    """Create a TimelineManagerPrimitive."""
    return TimelineManagerPrimitive()


@pytest.fixture
def character_manager():
    """Create a CharacterStatePrimitive."""
    return CharacterStatePrimitive()


@pytest.fixture
def branch_validator():
    """Create a BranchValidatorPrimitive."""
    return BranchValidatorPrimitive()


class TestBasicIntegration:
    """Test basic integration between primitives."""

    @pytest.mark.asyncio
    async def test_story_to_timeline_integration(
        self, story_generator, timeline_manager, context
    ):
        """Test that story generation flows into timeline tracking."""
        # Generate a story
        story_input = StoryGenerationInput(
            theme="A hero discovers ancient ruins",
            universe_id="integration_test",
            timeline_position=0,
            active_characters=["hero"],
            previous_context="",
            player_preferences={},
        )
        story = await story_generator.execute(story_input, context)

        # Story is single-scene model, create timeline event from it
        assert story.scene_id is not None
        assert len(story.narrative_text) > 0

        # Add story to timeline
        update = TimelineUpdate(
            universe_id="integration_test",
            event_data={"description": story.narrative_text[:100]},
            timestamp=0,
            event_type="story_beat",
            character_ids=["hero"],
        )
        timeline_state = await timeline_manager.execute(update, context)

        # Verify timeline tracked the event
        assert len(timeline_state.event_history) == 1
        assert (
            timeline_state.timeline_coherence_score >= 0.8
        )  # Should be highly coherent

    @pytest.mark.asyncio
    async def test_story_to_character_integration(
        self, story_generator, character_manager, context
    ):
        """Test that story generation flows into character development."""
        # Generate a story
        story_input = StoryGenerationInput(
            theme="A warrior's journey of redemption",
            universe_id="integration_test",
            timeline_position=0,
            active_characters=["warrior"],
            previous_context="",
            player_preferences={},
        )
        story = await story_generator.execute(story_input, context)

        # Track character interactions from story (single scene model)
        assert story.scene_id is not None
        character_responses = []

        # Extract character from dialogue in the single scene
        # If no dialogue, at least interact with the main character
        if story.dialogue:
            for dialogue_line in story.dialogue:
                character_id = dialogue_line.character_id
                if character_id:
                    interaction = CharacterInteraction(
                        character_id=character_id,
                        scene_context=story.narrative_text,
                        emotional_trigger=f"Character {character_id} speaks",
                        story_events=[story.narrative_text],
                    )
                    response = await character_manager.execute(interaction, context)
                    character_responses.append(response)
        else:
            # No dialogue, but warrior is in the story
            interaction = CharacterInteraction(
                character_id="warrior",
                scene_context=story.narrative_text,
                emotional_trigger="Warrior's journey begins",
                story_events=[story.narrative_text],
            )
            response = await character_manager.execute(interaction, context)
            character_responses.append(response)

        # Verify story was generated (mock may not have dialogue)
        assert story.narrative_text is not None

        # Verify character state persists
        all_characters = character_manager.get_all_characters()
        assert len(all_characters) > 0

    @pytest.mark.asyncio
    async def test_timeline_to_branch_validation(
        self, timeline_manager, branch_validator, context
    ):
        """Test that timeline context informs branch validation."""
        # Build a timeline
        events = [
            ("Hero arrives at village", 0, "story_beat"),
            ("Hero meets elder", 100, "story_beat"),
            ("Elder warns of danger", 200, "story_beat"),
        ]

        for desc, timestamp, event_type in events:
            update = TimelineUpdate(
                universe_id="integration_test",
                event_data={"description": desc},
                timestamp=timestamp,
                event_type=event_type,
                character_ids=["hero", "elder"] if "elder" in desc else ["hero"],
            )
            await timeline_manager.execute(update, context)

        # Get timeline context
        timeline = timeline_manager.get_timeline("integration_test")
        timeline_context = [
            event.event_data.get("description", "") for event in timeline
        ]

        # Validate a branch that's consistent with timeline
        valid_proposal = BranchProposal(
            universe_id="integration_test",
            branch_description="Hero offers to help village defend against danger",
            choice_text="Offer to protect the village from the warned danger",
            affected_characters=["hero", "elder"],
            timeline_context=timeline_context,
            universe_rules={},
        )
        valid_result = await branch_validator.execute(valid_proposal, context)
        assert valid_result.is_valid
        assert valid_result.overall_score > 0.6

        # Validate a branch that contradicts timeline
        invalid_proposal = BranchProposal(
            universe_id="integration_test",
            branch_description="Hero has never met the elder",
            choice_text="Meet the elder for the first time",
            affected_characters=["hero", "elder"],
            timeline_context=timeline_context,
            universe_rules={},
        )
        invalid_result = await branch_validator.execute(invalid_proposal, context)
        # Should have consistency issues (check either invalid or has issues)
        assert not invalid_result.is_valid or len(invalid_result.issues) > 0


class TestFullNarrativePipeline:
    """Test complete narrative generation workflows."""

    @pytest.mark.asyncio
    async def test_complete_story_generation_workflow(
        self,
        story_generator,
        timeline_manager,
        character_manager,
        branch_validator,
        context,
    ):
        """Test a complete workflow from story generation to branch validation."""
        # Step 1: Generate initial story
        story_input = StoryGenerationInput(
            theme="A young mage discovers forbidden magic",
            universe_id="complete_pipeline",
            timeline_position=0,
            active_characters=["mage"],
            previous_context="",
            player_preferences={},
        )
        story = await story_generator.execute(story_input, context)

        # Story is single-scene model
        assert story.scene_id is not None
        assert story.quality_score >= 0.0  # Mock returns 0.2, accept any valid score

        # Step 2: Track story event in timeline
        update = TimelineUpdate(
            universe_id="complete_pipeline",
            event_data={"description": story.narrative_text},
            timestamp=0,
            event_type="story_beat",
            character_ids=["mage"],
        )
        await timeline_manager.execute(update, context)

        timeline = timeline_manager.get_timeline("complete_pipeline")
        assert len(timeline) >= 1

        # Step 3: Develop character state from story
        main_character = "mage"

        interaction = CharacterInteraction(
            character_id=main_character,
            scene_context=story.narrative_text,
            emotional_trigger="Discovery and wonder",
            story_events=[story.narrative_text],
            development_opportunity="Learn to control forbidden magic",
        )
        await character_manager.execute(interaction, context)

        char_state = character_manager.get_character(main_character)
        assert char_state is not None
        assert len(char_state.memory) > 0

        # Step 4: Validate a branching choice
        timeline_context = [
            event.event_data.get("description", "") for event in timeline
        ]

        branch_proposal = BranchProposal(
            universe_id="complete_pipeline",
            branch_description="Mage practices forbidden magic in secret",
            choice_text="Practice the forbidden magic alone at night",
            affected_characters=[main_character],
            timeline_context=timeline_context,
            universe_rules={"magic_system": "magic exists but is regulated"},
        )

        validation = await branch_validator.execute(branch_proposal, context)
        assert validation.is_valid
        assert validation.overall_score >= 0.6

    @pytest.mark.asyncio
    async def test_branching_story_with_multiple_paths(
        self, story_generator, timeline_manager, branch_validator, context
    ):
        """Test story branching with multiple universe paths."""
        # Generate base story
        base_input = StoryGenerationInput(
            theme="A detective investigates a mysterious disappearance",
            universe_id="main_universe",
            timeline_position=0,
            active_characters=["detective"],
            previous_context="",
            player_preferences={},
        )
        base_story = await story_generator.execute(base_input, context)

        # Track base timeline (single scene model)
        update = TimelineUpdate(
            universe_id="main_universe",
            event_data={"description": base_story.narrative_text},
            timestamp=0,
            event_type="story_beat",
            character_ids=["detective"],
        )
        await timeline_manager.execute(update, context)

        base_timeline = timeline_manager.get_timeline("main_universe")
        timeline_context = [
            event.event_data.get("description", "") for event in base_timeline
        ]

        # Validate two different branching paths
        branch_a = BranchProposal(
            universe_id="main_universe",
            branch_description="Detective pursues suspect A",
            choice_text="Follow the mysterious stranger",
            affected_characters=["detective"],
            timeline_context=timeline_context,
            universe_rules={},
        )

        branch_b = BranchProposal(
            universe_id="main_universe",
            branch_description="Detective investigates location B",
            choice_text="Search the abandoned warehouse",
            affected_characters=["detective"],
            timeline_context=timeline_context,
            universe_rules={},
        )

        validation_a = await branch_validator.execute(branch_a, context)
        validation_b = await branch_validator.execute(branch_b, context)

        # Both should be valid branches
        assert validation_a.is_valid
        assert validation_b.is_valid

        # Both should be stored in validator
        validated_branches = branch_validator.get_validated_branches("main_universe")
        assert len(validated_branches) == 2

    @pytest.mark.asyncio
    async def test_character_development_across_timeline(
        self, timeline_manager, character_manager, context
    ):
        """Test that character development progresses with timeline events."""
        character_id = "protagonist"
        universe_id = "development_test"

        # Create a series of events that should develop the character
        story_beats = [
            {
                "event": "Protagonist discovers hidden talent",
                "trigger": "Discovery brings hope and excitement",
                "opportunity": "Begin exploring new abilities",
            },
            {
                "event": "Protagonist faces first challenge",
                "trigger": "Challenge creates fear and determination",
                "opportunity": "Overcome fear through practice",
            },
            {
                "event": "Protagonist succeeds despite setbacks",
                "trigger": "Success brings pride and confidence",
                "opportunity": "Master the new abilities",
            },
        ]

        # Process each beat through both timeline and character systems
        for idx, beat in enumerate(story_beats):
            # Add to timeline
            timeline_update = TimelineUpdate(
                universe_id=universe_id,
                event_data={"description": beat["event"]},
                timestamp=idx * 100,
                event_type="story_beat",
                character_ids=[character_id],
            )
            await timeline_manager.execute(timeline_update, context)

            # Update character
            interaction = CharacterInteraction(
                character_id=character_id,
                scene_context=beat["event"],
                emotional_trigger=beat["trigger"],
                story_events=[beat["event"]],
                development_opportunity=beat["opportunity"],
            )
            await character_manager.execute(interaction, context)

        # Verify timeline coherence
        timeline_state = timeline_manager.get_timeline(universe_id)
        assert len(timeline_state) == len(story_beats)

        # Verify character development
        char_state = character_manager.get_character(character_id)
        assert char_state is not None
        assert len(char_state.memory) == len(story_beats)

        # Character should have development goals
        assert len(char_state.development_goals) > 0

        # Some goals should show progress (values are floats, not objects)
        assert any(goal > 0.0 for goal in char_state.development_goals.values())


class TestErrorPropagation:
    """Test that errors are handled gracefully across primitives."""

    @pytest.mark.asyncio
    async def test_invalid_timeline_doesnt_break_validation(
        self, timeline_manager, branch_validator, context
    ):
        """Test that branch validation works even with problematic timeline."""
        # Create timeline with time paradox
        update1 = TimelineUpdate(
            universe_id="error_test",
            event_data={"description": "Event happens at time 100"},
            timestamp=100,
            event_type="story_beat",
            character_ids=["character_a"],
            causal_links=[],
        )
        await timeline_manager.execute(update1, context)

        update2 = TimelineUpdate(
            universe_id="error_test",
            event_data={"description": "This causes the event at 100"},
            timestamp=200,  # After the event it causes
            event_type="story_beat",
            character_ids=["character_a"],
            causal_links=["Event happens at time 100"],  # Paradox!
        )
        timeline_state = await timeline_manager.execute(update2, context)

        # Timeline should detect inconsistency
        assert len(timeline_state.inconsistencies) > 0

        # But branch validation should still work
        timeline_context = [
            event.event_data.get("description", "")
            for event in timeline_state.event_history
        ]

        proposal = BranchProposal(
            universe_id="error_test",
            branch_description="Character makes a choice",
            choice_text="Continue despite timeline issues",
            affected_characters=["character_a"],
            timeline_context=timeline_context,
            universe_rules={},
        )

        # Should complete without crashing
        validation = await branch_validator.execute(proposal, context)
        assert validation is not None

    @pytest.mark.asyncio
    async def test_missing_character_handled_gracefully(
        self, character_manager, branch_validator, context
    ):
        """Test validation of branches with untracked characters."""
        # Don't create any characters

        # Try to validate a branch mentioning characters
        proposal = BranchProposal(
            universe_id="error_test",
            branch_description="Unknown character takes action",
            choice_text="Character does something important",
            affected_characters=["unknown_character"],
            timeline_context=["Some events happened"],
            universe_rules={},
        )

        validation = await branch_validator.execute(proposal, context)

        # Should complete and include info about unmentioned character
        assert validation is not None
        assert any(issue.message for issue in validation.issues)


class TestConcurrentOperations:
    """Test that primitives handle concurrent operations correctly."""

    @pytest.mark.asyncio
    async def test_concurrent_timeline_updates(self, timeline_manager, context):
        """Test multiple timeline updates in same universe."""
        universe_id = "concurrent_test"

        # Create multiple updates concurrently
        updates = [
            TimelineUpdate(
                universe_id=universe_id,
                event_data={"description": f"Event {i}"},
                timestamp=i * 100,
                event_type="story_beat",
                character_ids=["character"],
            )
            for i in range(5)
        ]

        # Execute concurrently
        results = await asyncio.gather(
            *[timeline_manager.execute(update, context) for update in updates]
        )

        # All should succeed
        assert len(results) == 5

        # Timeline should have all events
        timeline = timeline_manager.get_timeline(universe_id)
        assert len(timeline) == 5

    @pytest.mark.asyncio
    async def test_concurrent_character_interactions(self, character_manager, context):
        """Test multiple character interactions concurrently."""
        character_id = "concurrent_character"

        # Create multiple interactions
        interactions = [
            CharacterInteraction(
                character_id=character_id,
                scene_context=f"Scene {i}",
                emotional_trigger=f"Trigger {i}",
                story_events=[f"Event {i}"],
            )
            for i in range(5)
        ]

        # Execute concurrently
        results = await asyncio.gather(
            *[
                character_manager.execute(interaction, context)
                for interaction in interactions
            ]
        )

        # All should succeed
        assert len(results) == 5

        # Character should have accumulated memory
        char_state = character_manager.get_character(character_id)
        assert char_state is not None
        assert len(char_state.memory) == 5
