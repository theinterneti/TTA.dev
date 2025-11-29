"""Story generation primitive for TTA narrative engine.

This module implements the core story generation primitive that uses
LLMs to create narrative content while respecting metaconcepts and
player boundaries.
"""

import json
from dataclasses import dataclass
from typing import Any

from ..core import TTAContext, TTAPrimitive, ValidationError
from ..integrations import LLMProvider, LLMResponse


@dataclass
class DialogueLine:
    """Single line of dialogue."""

    character_id: str
    text: str
    emotion: str


@dataclass
class StoryGenerationInput:
    """Input data for story generation."""

    theme: str
    universe_id: str
    timeline_position: int
    active_characters: list[str]
    previous_context: str
    player_preferences: dict[str, Any]
    narrative_style: str = "balanced"


@dataclass
class GeneratedStory:
    """Generated story output."""

    scene_id: str
    narrative_text: str
    dialogue: list[DialogueLine]
    setting_description: str
    emotional_tone: str
    story_branches: list[dict[str, str]]
    quality_score: float


class StoryGeneratorPrimitive(TTAPrimitive[StoryGenerationInput, GeneratedStory]):
    """Generate narrative content using LLM with metaconcept awareness.

    This primitive:
    1. Builds prompts incorporating metaconcepts and boundaries
    2. Calls LLM provider for generation
    3. Parses and validates response
    4. Assesses quality and coherence
    """

    def __init__(self, llm_provider: LLMProvider, name: str = "StoryGenerator") -> None:
        """Initialize story generator.

        Args:
            llm_provider: LLM provider for text generation
            name: Name for this primitive instance
        """
        super().__init__(name)
        self.llm_provider = llm_provider

    async def execute(
        self,
        input_data: StoryGenerationInput,
        context: TTAContext,
    ) -> GeneratedStory:
        """Generate story content.

        Args:
            input_data: Story generation parameters
            context: Workflow context with metaconcepts and boundaries

        Returns:
            Generated story with narrative and metadata

        Raises:
            ValidationError: If input is invalid
        """
        # Validate input
        self._validate_input(input_data, context)

        # Build prompt with metaconcepts
        prompt = self._build_prompt(input_data, context)

        # Generate via LLM (use generate_json for better parsing)
        try:
            story_data = await self.llm_provider.generate_json(
                prompt,
                context,
                max_tokens=3000,  # Increased for full JSON response
            )
            story = self._parse_json_response(story_data, input_data)
        except (ValueError, AttributeError):
            # Fallback to old method if generate_json not available
            llm_response = await self.llm_provider.generate(prompt, context)
            story = self._parse_response(llm_response, input_data)

        # Assess quality
        story.quality_score = self._assess_quality(story, context)

        return story

    def _validate_input(
        self,
        input_data: StoryGenerationInput,
        context: TTAContext,
    ) -> None:
        """Validate story generation input.

        Args:
            input_data: Input to validate
            context: Workflow context

        Raises:
            ValidationError: If validation fails
        """
        if not input_data.theme or len(input_data.theme) < 3:
            raise ValidationError(
                primitive_name=self.__class__.__name__,
                context=context,
                message="Theme must be at least 3 characters",
            )

        if not input_data.universe_id:
            raise ValidationError(
                primitive_name=self.__class__.__name__,
                context=context,
                message="Universe ID is required",
            )

        if input_data.timeline_position < 0:
            raise ValidationError(
                primitive_name=self.__class__.__name__,
                context=context,
                message="Timeline position must be non-negative",
            )

    def _build_prompt(
        self,
        input_data: StoryGenerationInput,
        context: TTAContext,
    ) -> str:
        """Build LLM prompt incorporating metaconcepts and boundaries.

        Args:
            input_data: Story parameters
            context: Workflow context with metaconcepts

        Returns:
            Formatted prompt string
        """
        # Extract metaconcept names
        metaconcept_names = [mc.name for mc in context.metaconcepts]

        # Build boundaries section
        boundaries_text = self._format_boundaries(context.player_boundaries)

        # Build prompt
        prompt = f"""You are generating narrative content for a therapeutic storytelling game.

THEME: {input_data.theme}
NARRATIVE STYLE: {input_data.narrative_style}
TIMELINE POSITION: {input_data.timeline_position}

ACTIVE CHARACTERS: {", ".join(input_data.active_characters)}

PREVIOUS CONTEXT:
{input_data.previous_context or "This is the beginning of the story."}

PLAYER BOUNDARIES:
{boundaries_text}

METACONCEPTS TO FOLLOW:
{", ".join(metaconcept_names)}

REQUIREMENTS:
1. Generate a narrative scene (200-400 words)
2. Include dialogue for active characters with emotions
3. Describe the setting vividly
4. Maintain emotional tone appropriate to the theme
5. Provide 2-3 story branch options for player choice
6. Respect all player boundaries
7. Support therapeutic goals through narrative

OUTPUT FORMAT (JSON):
{{
    "scene_id": "unique_scene_identifier",
    "narrative_text": "The narrative description...",
    "dialogue": [
        {{"character_id": "char1", "text": "What they said...", "emotion": "curious"}},
        {{"character_id": "char2", "text": "Their response...", "emotion": "hopeful"}}
    ],
    "setting_description": "Vivid setting details...",
    "emotional_tone": "hopeful/tense/peaceful/etc",
    "story_branches": [
        {{"choice": "Player choice text", "consequence": "Brief consequence hint"}},
        {{"choice": "Alternative choice", "consequence": "Different outcome hint"}}
    ]
}}

Generate the story scene now:"""

        return prompt

    def _format_boundaries(self, boundaries: dict[str, Any]) -> str:
        """Format player boundaries for prompt.

        Args:
            boundaries: Player boundary settings

        Returns:
            Formatted boundary text
        """
        if not boundaries:
            return "No specific boundaries set."

        lines = []
        for key, value in boundaries.items():
            lines.append(f"- {key}: {value}")

        return "\n".join(lines)

    def _parse_json_response(
        self,
        data: dict[str, Any],
        input_data: StoryGenerationInput,
    ) -> GeneratedStory:
        """Parse JSON dict into structured story.

        Args:
            data: Parsed JSON dict from LLM
            input_data: Original input for fallback

        Returns:
            Structured GeneratedStory
        """
        try:
            # Convert dialogue
            dialogue = [
                DialogueLine(
                    character_id=d["character_id"],
                    text=d["text"],
                    emotion=d.get("emotion", "neutral"),
                )
                for d in data.get("dialogue", [])
            ]

            return GeneratedStory(
                scene_id=data.get("scene_id", f"scene_{input_data.timeline_position}"),
                narrative_text=data.get("narrative_text", ""),
                dialogue=dialogue,
                setting_description=data.get("setting_description", ""),
                emotional_tone=data.get("emotional_tone", "neutral"),
                story_branches=data.get("story_branches", []),
                quality_score=0.0,  # Will be assessed separately
            )

        except (KeyError, TypeError):
            # Fallback: create minimal story
            return GeneratedStory(
                scene_id=f"scene_{input_data.timeline_position}_fallback",
                narrative_text=str(data),
                dialogue=[],
                setting_description="Setting details not parsed",
                emotional_tone="neutral",
                story_branches=[{"choice": "Continue", "consequence": "The story continues"}],
                quality_score=0.0,
            )

    def _parse_response(
        self,
        llm_response: LLMResponse,
        input_data: StoryGenerationInput,
    ) -> GeneratedStory:
        """Parse LLM response into structured story.

        Args:
            llm_response: Raw LLM response
            input_data: Original input for fallback

        Returns:
            Structured GeneratedStory
        """
        try:
            # Extract JSON from response
            text = llm_response.text.strip()

            # Handle markdown code blocks
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0].strip()
            elif "```" in text:
                text = text.split("```")[1].split("```")[0].strip()

            # Parse JSON
            data = json.loads(text)

            # Convert dialogue
            dialogue = [
                DialogueLine(
                    character_id=d["character_id"],
                    text=d["text"],
                    emotion=d.get("emotion", "neutral"),
                )
                for d in data.get("dialogue", [])
            ]

            return GeneratedStory(
                scene_id=data.get("scene_id", f"scene_{input_data.timeline_position}"),
                narrative_text=data.get("narrative_text", ""),
                dialogue=dialogue,
                setting_description=data.get("setting_description", ""),
                emotional_tone=data.get("emotional_tone", "neutral"),
                story_branches=data.get("story_branches", []),
                quality_score=0.0,  # Will be assessed separately
            )

        except (json.JSONDecodeError, KeyError, IndexError):
            # Fallback: create story from raw text
            return GeneratedStory(
                scene_id=f"scene_{input_data.timeline_position}_fallback",
                narrative_text=llm_response.text,
                dialogue=[],
                setting_description="Setting details not parsed",
                emotional_tone="neutral",
                story_branches=[
                    {"choice": "Continue", "consequence": "The story continues"},
                ],
                quality_score=0.3,  # Low quality for unparsed
            )

    def _assess_quality(
        self,
        story: GeneratedStory,
        context: TTAContext,
    ) -> float:
        """Assess story quality on 0.0-1.0 scale.

        Args:
            story: Generated story to assess
            context: Workflow context

        Returns:
            Quality score (0.0 = poor, 1.0 = excellent)
        """
        score = 0.0

        # Has narrative text (0.2 points)
        if story.narrative_text and len(story.narrative_text) >= 100:
            score += 0.2

        # Has dialogue (0.2 points)
        if len(story.dialogue) >= 2:
            score += 0.2

        # Has setting (0.2 points)
        if story.setting_description and len(story.setting_description) >= 20:
            score += 0.2

        # Has branches (0.2 points)
        if len(story.story_branches) >= 2:
            score += 0.2

        # Has emotional tone (0.1 points)
        if story.emotional_tone and story.emotional_tone != "neutral":
            score += 0.1

        # Length quality (0.1 points)
        word_count = len(story.narrative_text.split())
        if 200 <= word_count <= 400:
            score += 0.1
        elif 100 <= word_count < 200 or 400 < word_count <= 600:
            score += 0.05

        return min(1.0, score)
