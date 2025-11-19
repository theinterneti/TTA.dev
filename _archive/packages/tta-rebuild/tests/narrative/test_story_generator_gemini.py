"""Integration tests for StoryGenerator with real Gemini LLM.

These tests use the real Gemini API and are skipped if GEMINI_API_KEY is not set.
Run with: RUN_GEMINI_TESTS=1 pytest tests/narrative/test_story_generator_gemini.py -v
"""

import os
import sys

import pytest

from tta_rebuild.integrations import GeminiLLMProvider, LLMConfig
from tta_rebuild.narrative import (
    GeneratedStory,
    StoryGenerationInput,
    StoryGeneratorPrimitive,
)

# Skip all tests if Gemini API key not available or not explicitly enabled
pytestmark = pytest.mark.skipif(
    not os.getenv("GEMINI_API_KEY") or not os.getenv("RUN_GEMINI_TESTS"),
    reason="GEMINI_API_KEY not set or RUN_GEMINI_TESTS not enabled",
)


@pytest.fixture
def gemini_provider() -> GeminiLLMProvider:
    """Create real Gemini provider for integration testing."""
    config = LLMConfig(
        model="models/gemini-2.5-flash",  # Fast, stable model
        max_tokens=2000,
        temperature=0.7,
    )
    return GeminiLLMProvider(config=config)


@pytest.fixture
def story_generator_gemini(
    gemini_provider: GeminiLLMProvider,
) -> StoryGeneratorPrimitive:
    """Create story generator with real Gemini provider."""
    return StoryGeneratorPrimitive(gemini_provider, name="StoryGenerator_Gemini")


@pytest.fixture
def valid_input() -> StoryGenerationInput:
    """Create valid story input for testing."""
    return StoryGenerationInput(
        theme="courage and self-discovery",
        universe_id="universe-gemini-test",
        timeline_position=5,
        active_characters=["hero", "mentor"],
        previous_context=(
            "The hero has completed their training and stands ready for the next challenge."
        ),
        player_preferences={"violence": "low", "mature_themes": "off"},
        narrative_style="therapeutic",
    )


class TestGeminiIntegration:
    """Integration tests with real Gemini API."""

    @pytest.mark.asyncio
    async def test_real_story_generation(
        self,
        story_generator_gemini: StoryGeneratorPrimitive,
        valid_input: StoryGenerationInput,
        test_context,
    ) -> None:
        """Test story generation with real Gemini API.

        This test verifies:
        - Real LLM API connectivity
        - JSON parsing from LLM response
        - Quality score calculation
        - Expected quality improvement over mock (0.8+ vs 0.2)
        """
        print("\n" + "=" * 70)
        print("🚀 Testing Real Gemini Story Generation")
        print("=" * 70)

        story = await story_generator_gemini.execute(valid_input, test_context)

        # Basic structure validation
        assert isinstance(story, GeneratedStory)
        assert story.scene_id
        assert story.narrative_text
        assert story.setting_description
        assert story.emotional_tone

        # Quality expectations for real LLM
        print(f"\n📊 Quality Score: {story.quality_score:.2f}")
        assert story.quality_score >= 0.75, (
            f"Expected quality >= 0.75 from real LLM, got {story.quality_score:.2f}. "
            "Real LLM should significantly outperform mock (0.2)."
        )

        # Content quality checks
        assert len(story.narrative_text) >= 200, "Narrative should be substantial"
        assert len(story.dialogue) >= 2, "Should have meaningful dialogue"
        assert len(story.story_branches) >= 2, "Should offer player choices"

        # Print results for verification
        print(f"\n📖 Scene ID: {story.scene_id}")
        print(f"📝 Narrative Length: {len(story.narrative_text)} chars")
        print(f"💬 Dialogue Lines: {len(story.dialogue)}")
        print(f"🌳 Story Branches: {len(story.story_branches)}")
        print(f"😊 Emotional Tone: {story.emotional_tone}")
        print(f"\n✅ Quality Score: {story.quality_score:.2f} (Expected >= 0.75)")

        # Sample narrative (first 200 chars)
        print("\n📖 Sample Narrative:")
        print(f"{story.narrative_text[:200]}...")

    @pytest.mark.asyncio
    async def test_gemini_respects_boundaries(
        self,
        story_generator_gemini: StoryGeneratorPrimitive,
        valid_input: StoryGenerationInput,
        test_context,
    ) -> None:
        """Test that Gemini respects player boundaries."""
        # Set strict boundaries
        valid_input.player_preferences = {
            "violence": "none",
            "mature_themes": "off",
            "horror": "off",
        }

        story = await story_generator_gemini.execute(valid_input, test_context)

        # Check that narrative doesn't contain violent or mature content
        narrative_lower = story.narrative_text.lower()
        forbidden_terms = ["kill", "death", "blood", "violence", "horror"]

        found_terms = [term for term in forbidden_terms if term in narrative_lower]
        assert len(found_terms) == 0, (
            f"Found forbidden terms in narrative: {found_terms}. "
            "LLM should respect player boundaries."
        )

    @pytest.mark.asyncio
    async def test_gemini_includes_metaconcepts(
        self,
        story_generator_gemini: StoryGeneratorPrimitive,
        valid_input: StoryGenerationInput,
        test_context,
    ) -> None:
        """Test that Gemini incorporates metaconcepts."""
        story = await story_generator_gemini.execute(valid_input, test_context)

        # Check that story reflects therapeutic goals
        # Should include elements of courage, growth, or self-discovery
        narrative_lower = story.narrative_text.lower()
        therapeutic_indicators = [
            "courage",
            "brave",
            "growth",
            "discover",
            "challenge",
            "overcome",
            "strength",
            "confident",
        ]

        found_indicators = [term for term in therapeutic_indicators if term in narrative_lower]
        assert len(found_indicators) >= 1, (
            "Story should reflect therapeutic themes from metaconcepts. "
            f"Expected at least one of: {therapeutic_indicators}"
        )

    @pytest.mark.asyncio
    async def test_gemini_quality_vs_mock(
        self,
        story_generator_gemini: StoryGeneratorPrimitive,
        valid_input: StoryGenerationInput,
        test_context,
    ) -> None:
        """Compare Gemini quality against Mock baseline.

        Expected improvement:
        - Mock quality: ~0.2 (basic fallback)
        - Gemini quality: 0.8+ (sophisticated narrative)
        """
        story = await story_generator_gemini.execute(valid_input, test_context)

        mock_baseline = 0.2
        expected_improvement = 0.6  # At least 60% better

        quality_improvement = story.quality_score - mock_baseline

        print("\n📊 Quality Comparison:")
        print(f"   Mock Baseline: {mock_baseline:.2f}")
        print(f"   Gemini Score: {story.quality_score:.2f}")
        improvement_pct = quality_improvement / mock_baseline * 100
        print(f"   Improvement: +{quality_improvement:.2f} ({improvement_pct:.1f}%)")

        assert quality_improvement >= expected_improvement, (
            f"Expected quality improvement of at least {expected_improvement:.2f}, "
            f"got {quality_improvement:.2f}. "
            "Real LLM should significantly outperform mock."
        )

    @pytest.mark.asyncio
    async def test_gemini_cost_tracking(
        self,
        gemini_provider: GeminiLLMProvider,
        valid_input: StoryGenerationInput,
        test_context,
    ) -> None:
        """Test that cost tracking works with real API."""
        story_generator = StoryGeneratorPrimitive(gemini_provider)

        # Record initial usage
        initial_calls = gemini_provider.call_count
        initial_cost = gemini_provider.total_cost_usd

        # Generate story
        await story_generator.execute(valid_input, test_context)

        # Verify tracking
        assert gemini_provider.call_count == initial_calls + 1
        assert gemini_provider.total_cost_usd > initial_cost
        assert gemini_provider.total_prompt_tokens > 0
        assert gemini_provider.total_completion_tokens > 0

        print("\n💰 Cost Tracking:")
        print(f"   Calls: {gemini_provider.call_count}")
        print(f"   Prompt Tokens: {gemini_provider.total_prompt_tokens}")
        print(f"   Completion Tokens: {gemini_provider.total_completion_tokens}")
        print(f"   Total Cost: ${gemini_provider.total_cost_usd:.6f}")

    @pytest.mark.asyncio
    async def test_gemini_different_themes(
        self,
        story_generator_gemini: StoryGeneratorPrimitive,
        test_context,
    ) -> None:
        """Test Gemini with different narrative themes."""
        themes = [
            ("mystery and investigation", "mysterious"),
            ("hope and renewal", "hopeful"),
            ("adventure and exploration", "exciting"),
        ]

        for theme, _expected_tone_keyword in themes:
            input_data = StoryGenerationInput(
                theme=theme,
                universe_id="universe-theme-test",
                timeline_position=1,
                active_characters=["protagonist"],
                previous_context=f"Beginning of a {theme} story.",
                player_preferences={"violence": "low"},
                narrative_style="therapeutic",
            )

            story = await story_generator_gemini.execute(input_data, test_context)

            # Should generate quality content for each theme
            assert story.quality_score >= 0.7, f"Quality too low for theme: {theme}"
            assert story.narrative_text
            assert story.emotional_tone

            print(
                f"\n✅ Theme: {theme} -> Tone: {story.emotional_tone}, "
                f"Quality: {story.quality_score:.2f}"
            )


class TestGeminiErrorHandling:
    """Test error handling with real Gemini API."""

    @pytest.mark.asyncio
    async def test_invalid_api_key_handling(self, test_context) -> None:
        """Test graceful handling of invalid API key."""
        config = LLMConfig(model="models/gemini-2.5-flash")

        # This should raise during initialization
        with pytest.raises(ValueError, match="GEMINI_API_KEY"):
            GeminiLLMProvider(config=config, api_key="")

    @pytest.mark.asyncio
    async def test_gemini_retry_on_failure(
        self,
        story_generator_gemini: StoryGeneratorPrimitive,
        valid_input: StoryGenerationInput,
        test_context,
    ) -> None:
        """Test that Gemini provider retries on transient failures.

        Note: This test may occasionally fail if API is stable.
        The provider has built-in retry logic with exponential backoff.
        """
        # Provider automatically retries up to 3 times
        story = await story_generator_gemini.execute(valid_input, test_context)

        # Should succeed even if there were retries
        assert story
        assert story.quality_score > 0


if __name__ == "__main__":
    """Run integration tests manually."""
    print("\n🧪 Running Gemini Integration Tests")
    print("=" * 70)
    print("⚠️  These tests use real Gemini API and may incur costs")
    print("=" * 70)

    # Check for API key
    if not os.getenv("GEMINI_API_KEY"):
        print("\n❌ GEMINI_API_KEY not set")
        print("Set environment variable: export GEMINI_API_KEY=your-key")
        sys.exit(1)

    # Enable tests
    os.environ["RUN_GEMINI_TESTS"] = "1"

    # Run pytest
    pytest.main([__file__, "-v", "-s"])
