"""Tests for StoryGeneratorPrimitive."""

import pytest

from tta_rebuild import ValidationError
from tta_rebuild.integrations import MockLLMProvider
from tta_rebuild.narrative import (
    DialogueLine,
    GeneratedStory,
    StoryGenerationInput,
    StoryGeneratorPrimitive,
)


class TestStoryGenerationInput:
    """Test StoryGenerationInput dataclass."""

    def test_input_creation(self) -> None:
        """Test creating story input."""
        input_data = StoryGenerationInput(
            theme="courage",
            universe_id="universe-123",
            timeline_position=1,
            active_characters=["hero", "mentor"],
            previous_context="The hero has just arrived...",
            player_preferences={"violence": "low"},
            narrative_style="balanced",
        )

        assert input_data.theme == "courage"
        assert input_data.universe_id == "universe-123"
        assert input_data.timeline_position == 1
        assert len(input_data.active_characters) == 2
        assert input_data.narrative_style == "balanced"


class TestDialogueLine:
    """Test DialogueLine dataclass."""

    def test_dialogue_creation(self) -> None:
        """Test creating dialogue line."""
        dialogue = DialogueLine(
            character_id="hero",
            text="I must find the courage within.",
            emotion="determined",
        )

        assert dialogue.character_id == "hero"
        assert dialogue.text == "I must find the courage within."
        assert dialogue.emotion == "determined"


class TestGeneratedStory:
    """Test GeneratedStory dataclass."""

    def test_story_creation(self) -> None:
        """Test creating generated story."""
        story = GeneratedStory(
            scene_id="scene_1",
            narrative_text="The hero stands at the crossroads...",
            dialogue=[
                DialogueLine("hero", "Which path shall I take?", "uncertain"),
                DialogueLine("mentor", "The choice is yours alone.", "wise"),
            ],
            setting_description="A misty crossroads in an ancient forest",
            emotional_tone="contemplative",
            story_branches=[
                {"choice": "Take the left path", "consequence": "Darkness ahead"},
                {"choice": "Take the right path", "consequence": "Light beckons"},
            ],
            quality_score=0.85,
        )

        assert story.scene_id == "scene_1"
        assert "crossroads" in story.narrative_text
        assert len(story.dialogue) == 2
        assert story.emotional_tone == "contemplative"
        assert len(story.story_branches) == 2
        assert story.quality_score == 0.85


class TestStoryGeneratorPrimitive:
    """Test StoryGeneratorPrimitive."""

    @pytest.fixture
    def story_generator(self, mock_llm_provider: MockLLMProvider) -> StoryGeneratorPrimitive:
        """Create story generator for testing."""
        # Configure mock to return valid JSON
        mock_llm_provider.response = """{
            "scene_id": "scene_test_1",
            "narrative_text": "The brave adventurer stood at the edge of the ancient forest, sunlight filtering through the canopy above. The path ahead was uncertain, but determination burned in their heart. Every step forward was a choice to face the unknown with courage. The mentor watched from the shadows, knowing this journey would test the hero's resolve. Past trials had prepared them, but this moment demanded something more - a leap of faith into their own potential. The forest whispered secrets of those who had walked this path before, some who had triumphed and others who had turned back. But the adventurer had made their choice, and there was no turning back now. With a deep breath, they stepped forward into their destiny.",
            "dialogue": [
                {"character_id": "hero", "text": "I'm ready to face whatever lies ahead.", "emotion": "determined"},
                {"character_id": "mentor", "text": "Remember, courage is not the absence of fear.", "emotion": "wise"}
            ],
            "setting_description": "An ancient forest with towering trees and dappled sunlight creating patterns on the forest floor. A winding path disappears into the depths, while birds sing overhead.",
            "emotional_tone": "hopeful",
            "story_branches": [
                {"choice": "Follow the path deeper into the forest", "consequence": "You will encounter the guardian"},
                {"choice": "Search for signs of previous travelers", "consequence": "You may find helpful clues"},
                {"choice": "Set up camp and prepare", "consequence": "You'll be well-rested for challenges"}
            ]
        }"""
        return StoryGeneratorPrimitive(mock_llm_provider)

    @pytest.fixture
    def valid_input(self) -> StoryGenerationInput:
        """Create valid story input."""
        return StoryGenerationInput(
            theme="courage and self-discovery",
            universe_id="universe-test-123",
            timeline_position=5,
            active_characters=["hero", "mentor"],
            previous_context="The hero has completed their training.",
            player_preferences={"violence": "low", "mature_themes": "off"},
            narrative_style="therapeutic",
        )

    @pytest.mark.asyncio
    async def test_basic_generation(
        self,
        story_generator: StoryGeneratorPrimitive,
        valid_input: StoryGenerationInput,
        test_context,
    ) -> None:
        """Test basic story generation."""
        story = await story_generator.execute(valid_input, test_context)

        assert isinstance(story, GeneratedStory)
        assert story.scene_id == "scene_test_1"
        assert len(story.narrative_text) > 100
        assert "adventurer" in story.narrative_text
        assert len(story.dialogue) == 2
        assert story.dialogue[0].character_id == "hero"
        assert story.emotional_tone == "hopeful"
        assert len(story.story_branches) == 3
        assert 0.0 <= story.quality_score <= 1.0

    @pytest.mark.asyncio
    async def test_validation_empty_theme(
        self,
        story_generator: StoryGeneratorPrimitive,
        test_context,
    ) -> None:
        """Test validation fails with empty theme."""
        invalid_input = StoryGenerationInput(
            theme="",
            universe_id="universe-123",
            timeline_position=1,
            active_characters=["hero"],
            previous_context="",
            player_preferences={},
        )

        with pytest.raises(ValidationError, match="Theme must be at least 3 characters"):
            await story_generator.execute(invalid_input, test_context)

    @pytest.mark.asyncio
    async def test_validation_short_theme(
        self,
        story_generator: StoryGeneratorPrimitive,
        test_context,
    ) -> None:
        """Test validation fails with short theme."""
        invalid_input = StoryGenerationInput(
            theme="ab",
            universe_id="universe-123",
            timeline_position=1,
            active_characters=["hero"],
            previous_context="",
            player_preferences={},
        )

        with pytest.raises(ValidationError, match="Theme must be at least 3 characters"):
            await story_generator.execute(invalid_input, test_context)

    @pytest.mark.asyncio
    async def test_validation_missing_universe(
        self,
        story_generator: StoryGeneratorPrimitive,
        test_context,
    ) -> None:
        """Test validation fails without universe ID."""
        invalid_input = StoryGenerationInput(
            theme="courage",
            universe_id="",
            timeline_position=1,
            active_characters=["hero"],
            previous_context="",
            player_preferences={},
        )

        with pytest.raises(ValidationError, match="Universe ID is required"):
            await story_generator.execute(invalid_input, test_context)

    @pytest.mark.asyncio
    async def test_validation_negative_timeline(
        self,
        story_generator: StoryGeneratorPrimitive,
        test_context,
    ) -> None:
        """Test validation fails with negative timeline."""
        invalid_input = StoryGenerationInput(
            theme="courage",
            universe_id="universe-123",
            timeline_position=-1,
            active_characters=["hero"],
            previous_context="",
            player_preferences={},
        )

        with pytest.raises(ValidationError, match="Timeline position must be non-negative"):
            await story_generator.execute(invalid_input, test_context)

    @pytest.mark.asyncio
    async def test_prompt_includes_metaconcepts(
        self,
        story_generator: StoryGeneratorPrimitive,
        valid_input: StoryGenerationInput,
        test_context,
    ) -> None:
        """Test prompt includes metaconcepts."""
        await story_generator.execute(valid_input, test_context)

        # Check the last prompt sent to LLM
        last_prompt = story_generator.llm_provider.last_prompt
        assert "METACONCEPTS TO FOLLOW:" in last_prompt
        assert "Support Therapeutic Goals" in last_prompt

    @pytest.mark.asyncio
    async def test_prompt_includes_boundaries(
        self,
        story_generator: StoryGeneratorPrimitive,
        valid_input: StoryGenerationInput,
        test_context,
    ) -> None:
        """Test prompt respects player boundaries."""
        await story_generator.execute(valid_input, test_context)

        last_prompt = story_generator.llm_provider.last_prompt
        assert "PLAYER BOUNDARIES:" in last_prompt
        assert "violence: low" in last_prompt
        assert "mature_themes: off" in last_prompt

    @pytest.mark.asyncio
    async def test_quality_assessment_high_quality(
        self,
        story_generator: StoryGeneratorPrimitive,
        valid_input: StoryGenerationInput,
        test_context,
    ) -> None:
        """Test quality assessment for good story."""
        story = await story_generator.execute(valid_input, test_context)

        # Should have high quality score
        assert story.quality_score >= 0.8
        assert story.narrative_text
        assert len(story.dialogue) >= 2
        assert story.setting_description
        assert len(story.story_branches) >= 2

    @pytest.mark.asyncio
    async def test_fallback_parsing(
        self,
        mock_llm_provider: MockLLMProvider,
        valid_input: StoryGenerationInput,
        test_context,
    ) -> None:
        """Test fallback when JSON parsing fails."""
        # Set invalid JSON response
        mock_llm_provider.response = "This is not valid JSON at all!"
        story_generator = StoryGeneratorPrimitive(mock_llm_provider)

        story = await story_generator.execute(valid_input, test_context)

        # Should use fallback
        assert "fallback" in story.scene_id
        assert story.narrative_text == "This is not valid JSON at all!"
        assert len(story.dialogue) == 0
        assert len(story.story_branches) == 1
        # Quality score will be 0.2 because text is short
        assert 0.0 <= story.quality_score <= 0.3

    @pytest.mark.asyncio
    async def test_markdown_json_extraction(
        self,
        mock_llm_provider: MockLLMProvider,
        valid_input: StoryGenerationInput,
        test_context,
    ) -> None:
        """Test extraction of JSON from markdown code blocks."""
        # LLM returns JSON wrapped in markdown
        mock_llm_provider.response = """```json
{
    "scene_id": "markdown_test",
    "narrative_text": "Testing markdown extraction with sufficient length to pass quality checks.",
    "dialogue": [
        {"character_id": "test", "text": "Hello", "emotion": "happy"}
    ],
    "setting_description": "Test setting with description",
    "emotional_tone": "cheerful",
    "story_branches": [
        {"choice": "Choice 1", "consequence": "Result 1"},
        {"choice": "Choice 2", "consequence": "Result 2"}
    ]
}
```"""
        story_generator = StoryGeneratorPrimitive(mock_llm_provider)

        story = await story_generator.execute(valid_input, test_context)

        # Should successfully parse
        assert story.scene_id == "markdown_test"
        assert "markdown extraction" in story.narrative_text
        assert len(story.dialogue) == 1
        assert story.emotional_tone == "cheerful"
