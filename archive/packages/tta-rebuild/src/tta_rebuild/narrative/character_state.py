"""Character state management primitive for TTA narrative engine.

This module implements character development tracking, relationship management,
and character-specific content generation.
"""

from dataclasses import dataclass, field
from datetime import datetime

from ..core import TTAContext, TTAPrimitive, ValidationError


@dataclass
class CharacterState:
    """Current state of a character."""

    character_id: str
    name: str
    personality_traits: dict[str, float]  # trait -> strength (0.0-1.0)
    emotional_state: str  # "hopeful", "fearful", "conflicted", etc.
    development_goals: dict[str, float]  # goal -> progress (0.0-1.0)
    relationships: dict[str, float]  # character_id -> relationship (-1.0 to 1.0)
    memory: list[str]  # Important story events affecting character
    arc_stage: str  # "setup", "development", "climax", "resolution"
    last_updated: datetime = field(default_factory=datetime.now)


@dataclass
class CharacterInteraction:
    """Input for character interaction."""

    character_id: str
    scene_context: str
    emotional_trigger: str | None = None
    interacting_with: list[str] = field(default_factory=list)
    story_events: list[str] = field(default_factory=list)
    development_opportunity: str | None = None


@dataclass
class CharacterResponse:
    """Output from character interaction."""

    character_id: str
    dialogue: str
    internal_monologue: str
    emotion: str
    development_progress: dict[str, float]
    relationship_changes: dict[str, float]
    suggested_arc_direction: str
    consistency_score: float  # 0.0-1.0
    personality_alignment: float  # 0.0-1.0


class CharacterStatePrimitive(TTAPrimitive[CharacterInteraction, CharacterResponse]):
    """Manage character development and generate character-specific content.

    This primitive:
    1. Tracks character state across all interactions
    2. Maintains relationship graphs between characters
    3. Measures arc progression toward goals
    4. Validates consistency with established personality
    5. Generates character-specific dialogue and responses

    Features:
    - Persistent character state
    - Relationship evolution
    - Arc progression tracking
    - Personality-based validation
    - Memory management
    """

    def __init__(self, name: str = "CharacterState") -> None:
        """Initialize character state manager.

        Args:
            name: Name for this primitive instance
        """
        super().__init__(name)
        # Storage for all character states
        self._characters: dict[str, CharacterState] = {}
        # Relationship symmetry tracking (for validation)
        self._relationship_graph: dict[str, dict[str, float]] = {}

    async def execute(
        self,
        input_data: CharacterInteraction,
        context: TTAContext,
    ) -> CharacterResponse:
        """Process character interaction and update state.

        Args:
            input_data: Character interaction details
            context: Workflow context

        Returns:
            Character response with updated state

        Raises:
            ValidationError: If interaction is invalid
        """
        # Validate input
        self._validate_interaction(input_data)

        # Get or create character state
        character = self._get_or_create_character(input_data.character_id)

        # Update emotional state if triggered
        if input_data.emotional_trigger:
            character = self._update_emotion(character, input_data.emotional_trigger)

        # Update memory with new story events
        character = self._update_memory(character, input_data.story_events)

        # Process relationship changes
        relationship_changes = self._process_relationships(
            character,
            input_data.interacting_with,
            input_data.scene_context,
        )

        # Update development progress
        development_progress = self._update_development(
            character,
            input_data.development_opportunity,
        )

        # Generate character-specific dialogue
        dialogue = self._generate_dialogue(character, input_data)

        # Generate internal monologue
        internal_monologue = self._generate_internal_monologue(character, input_data)

        # Calculate consistency score
        consistency_score = self._calculate_consistency(character, dialogue)

        # Calculate personality alignment
        personality_alignment = self._calculate_personality_alignment(
            character, input_data
        )

        # Suggest arc direction
        suggested_arc = self._suggest_arc_direction(character)

        # Update character state
        character.last_updated = datetime.now()
        self._characters[character.character_id] = character

        # Return response
        return CharacterResponse(
            character_id=character.character_id,
            dialogue=dialogue,
            internal_monologue=internal_monologue,
            emotion=character.emotional_state,
            development_progress=development_progress,
            relationship_changes=relationship_changes,
            suggested_arc_direction=suggested_arc,
            consistency_score=consistency_score,
            personality_alignment=personality_alignment,
        )

    def _validate_interaction(self, interaction: CharacterInteraction) -> None:
        """Validate interaction input.

        Args:
            interaction: Interaction to validate

        Raises:
            ValidationError: If interaction is invalid
        """
        if not interaction.character_id:
            raise ValidationError("character_id is required")

        if not interaction.scene_context:
            raise ValidationError("scene_context is required")

    def _get_or_create_character(self, character_id: str) -> CharacterState:
        """Get existing character or create new one.

        Args:
            character_id: Character identifier

        Returns:
            Character state
        """
        if character_id in self._characters:
            return self._characters[character_id]

        # Create new character with default state
        return CharacterState(
            character_id=character_id,
            name=character_id.replace("_", " ").title(),
            personality_traits={
                "courage": 0.5,
                "compassion": 0.5,
                "wisdom": 0.5,
                "humor": 0.5,
            },
            emotional_state="neutral",
            development_goals={},
            relationships={},
            memory=[],
            arc_stage="setup",
        )

    def _update_emotion(
        self, character: CharacterState, trigger: str
    ) -> CharacterState:
        """Update character's emotional state.

        Args:
            character: Character to update
            trigger: Emotional trigger description

        Returns:
            Updated character state
        """
        # Simple emotion mapping (could be LLM-based in production)
        emotion_keywords = {
            "hope": "hopeful",
            "fear": "fearful",
            "anger": "angry",
            "sad": "sorrowful",
            "joy": "joyful",
            "conflict": "conflicted",
            "determination": "determined",
        }

        for keyword, emotion in emotion_keywords.items():
            if keyword in trigger.lower():
                character.emotional_state = emotion
                break

        return character

    def _update_memory(
        self, character: CharacterState, events: list[str]
    ) -> CharacterState:
        """Update character's memory with new events.

        Args:
            character: Character to update
            events: New story events

        Returns:
            Updated character state
        """
        # Add new events to memory
        character.memory.extend(events)

        # Keep only recent memories (last 10 events)
        if len(character.memory) > 10:
            character.memory = character.memory[-10:]

        return character

    def _process_relationships(
        self,
        character: CharacterState,
        interacting_with: list[str],
        context: str,
    ) -> dict[str, float]:
        """Process relationship changes from interaction.

        Args:
            character: Character processing relationships
            interacting_with: Other character IDs
            context: Scene context

        Returns:
            Relationship changes (character_id -> delta)
        """
        changes: dict[str, float] = {}

        for other_id in interacting_with:
            # Get current relationship or default to neutral
            current = character.relationships.get(other_id, 0.0)

            # Calculate change based on context (simplified)
            delta = 0.0
            if "positive" in context.lower() or "help" in context.lower():
                delta = 0.1
            elif "negative" in context.lower() or "conflict" in context.lower():
                delta = -0.1

            # Update relationship
            new_value = max(-1.0, min(1.0, current + delta))
            character.relationships[other_id] = new_value
            changes[other_id] = delta

            # Update relationship graph for symmetry
            if character.character_id not in self._relationship_graph:
                self._relationship_graph[character.character_id] = {}
            self._relationship_graph[character.character_id][other_id] = new_value

        return changes

    def _update_development(
        self, character: CharacterState, opportunity: str | None
    ) -> dict[str, float]:
        """Update character development progress.

        Args:
            character: Character to update
            opportunity: Development opportunity description

        Returns:
            Current development progress
        """
        if opportunity:
            # Create goal if it doesn't exist
            if opportunity not in character.development_goals:
                character.development_goals[opportunity] = 0.0

            # Increment progress
            character.development_goals[opportunity] = min(
                1.0, character.development_goals[opportunity] + 0.1
            )

        return character.development_goals.copy()

    def _generate_dialogue(
        self, character: CharacterState, interaction: CharacterInteraction
    ) -> str:
        """Generate character-specific dialogue.

        Args:
            character: Character speaking
            interaction: Interaction context

        Returns:
            Generated dialogue
        """
        # Simplified dialogue generation (would use LLM in production)
        personality_desc = self._describe_personality(character)
        emotion_desc = character.emotional_state

        return (
            f"[{character.name} - {emotion_desc}] "
            f"Speaking with {personality_desc} in response to: "
            f"{interaction.scene_context[:50]}..."
        )

    def _generate_internal_monologue(
        self, character: CharacterState, interaction: CharacterInteraction
    ) -> str:
        """Generate character's internal thoughts.

        Args:
            character: Character thinking
            interaction: Interaction context

        Returns:
            Internal monologue
        """
        # Consider recent memories and goals
        active_goals = [
            goal
            for goal, progress in character.development_goals.items()
            if progress < 1.0
        ]

        if active_goals:
            primary_goal = active_goals[0]
            return f"I must focus on {primary_goal}. This situation might help."
        return f"I'm feeling {character.emotional_state} about this."

    def _calculate_consistency(self, character: CharacterState, dialogue: str) -> float:
        """Calculate how consistent dialogue is with character.

        Args:
            character: Character to check
            dialogue: Generated dialogue

        Returns:
            Consistency score 0.0-1.0
        """
        # Simplified consistency check
        # In production, would compare against personality traits more deeply
        score = 1.0

        # Check if emotion matches dialogue tone
        if (
            character.emotional_state == "fearful" and "confident" in dialogue.lower()
        ) or (character.emotional_state == "joyful" and "sad" in dialogue.lower()):
            score -= 0.3

        return max(0.0, score)

    def _calculate_personality_alignment(
        self, character: CharacterState, interaction: CharacterInteraction
    ) -> float:
        """Calculate how well interaction aligns with personality.

        Args:
            character: Character to check
            interaction: Interaction details

        Returns:
            Alignment score 0.0-1.0
        """
        # Check if actions align with traits
        score = 0.8  # Default good alignment

        # Courageous characters should engage with challenges
        if character.personality_traits.get("courage", 0.5) > 0.7:
            if "challenge" in interaction.scene_context.lower():
                score = 1.0

        return score

    def _suggest_arc_direction(self, character: CharacterState) -> str:
        """Suggest next arc direction for character.

        Args:
            character: Character to analyze

        Returns:
            Suggested arc direction
        """
        # Check arc stage progression
        if character.arc_stage == "setup":
            return "Establish character's ordinary world and call to adventure"
        if character.arc_stage == "development":
            return "Face challenges that test character's beliefs and goals"
        if character.arc_stage == "climax":
            return "Confront the ultimate challenge and make defining choice"
        # resolution
        return "Show character's transformation and new equilibrium"

    def _describe_personality(self, character: CharacterState) -> str:
        """Create personality description from traits.

        Args:
            character: Character to describe

        Returns:
            Personality description
        """
        dominant_traits = [
            trait
            for trait, value in character.personality_traits.items()
            if value > 0.7
        ]

        if dominant_traits:
            return f"high {', '.join(dominant_traits)}"
        return "balanced personality"

    def get_character(self, character_id: str) -> CharacterState | None:
        """Get character state by ID.

        Args:
            character_id: Character identifier

        Returns:
            Character state or None if not found
        """
        return self._characters.get(character_id)

    def get_all_characters(self) -> list[CharacterState]:
        """Get all tracked characters.

        Returns:
            List of all character states
        """
        return list(self._characters.values())

    def get_relationship(self, char1_id: str, char2_id: str) -> float:
        """Get relationship value between two characters.

        Args:
            char1_id: First character ID
            char2_id: Second character ID

        Returns:
            Relationship value (-1.0 to 1.0), 0.0 if no relationship
        """
        char1 = self._characters.get(char1_id)
        if char1:
            return char1.relationships.get(char2_id, 0.0)
        return 0.0

    def set_development_goal(
        self, character_id: str, goal: str, initial_progress: float = 0.0
    ) -> None:
        """Set a development goal for a character.

        Args:
            character_id: Character identifier
            goal: Goal description
            initial_progress: Starting progress (0.0-1.0)
        """
        character = self._get_or_create_character(character_id)
        character.development_goals[goal] = max(0.0, min(1.0, initial_progress))
        self._characters[character_id] = character

    def update_arc_stage(self, character_id: str, stage: str) -> None:
        """Update character's arc stage.

        Args:
            character_id: Character identifier
            stage: New arc stage ("setup", "development", "climax", "resolution")

        Raises:
            ValidationError: If stage is invalid
        """
        valid_stages = {"setup", "development", "climax", "resolution"}
        if stage not in valid_stages:
            raise ValidationError(
                f"Invalid arc stage '{stage}'. Must be one of {valid_stages}"
            )

        character = self._get_or_create_character(character_id)
        character.arc_stage = stage
        self._characters[character_id] = character
