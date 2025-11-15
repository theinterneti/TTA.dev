"""Metaconcept registry for TTA rebuild.

Metaconcepts are high-level AI guidance principles that shape primitive behavior
without being prescriptive. They guide LLM prompts and decision-making.
"""

from dataclasses import dataclass
from enum import Enum


class MetaconceptCategory(Enum):
    """Categories of metaconcepts."""

    THERAPEUTIC = "therapeutic"
    NARRATIVE = "narrative"
    SAFETY = "safety"
    GAME = "game"


@dataclass(frozen=True)
class Metaconcept:
    """A metaconcept that guides primitive behavior.

    Attributes:
        name: Human-readable name
        category: Category this metaconcept belongs to
        description: Detailed description of guidance provided
        scope: Which primitive types this applies to ("all" or specific types)
    """

    name: str
    category: MetaconceptCategory
    description: str
    scope: list[str]

    def applies_to(self, primitive_type: str) -> bool:
        """Check if this metaconcept applies to a primitive type.

        Args:
            primitive_type: Type of primitive (e.g., "narrative", "therapeutic")

        Returns:
            True if metaconcept applies to this primitive type
        """
        return "all" in self.scope or primitive_type in self.scope


class MetaconceptRegistry:
    """Registry of all TTA metaconcepts.

    Metaconcepts guide AI behavior without being prescriptive.
    They are incorporated into LLM prompts to influence generation.
    """

    # Therapeutic metaconcepts - guide therapeutic integration
    THERAPEUTIC: list[Metaconcept] = [
        Metaconcept(
            name="Support Therapeutic Goals",
            category=MetaconceptCategory.THERAPEUTIC,
            description=(
                "Subtly integrate therapeutic themes without being prescriptive. "
                "Use narrative therapy patterns (externalization, re-authoring) "
                "but never tell players what they 'should' do."
            ),
            scope=["therapeutic", "narrative"],
        ),
        Metaconcept(
            name="Promote Self-Compassion",
            category=MetaconceptCategory.THERAPEUTIC,
            description=(
                "Stories emphasize self-acceptance and kindness. "
                "Characters model self-compassion through actions. "
                "Avoid judgmental language or harsh self-criticism."
            ),
            scope=["therapeutic", "narrative"],
        ),
        Metaconcept(
            name="Prioritize Player Agency",
            category=MetaconceptCategory.SAFETY,
            description=(
                "Never force therapeutic content on players. "
                "All therapeutic features are optional and player-controlled. "
                "Respect player's right to engage or disengage at any time."
            ),
            scope=["all"],
        ),
        Metaconcept(
            name="Enable Externalization",
            category=MetaconceptCategory.THERAPEUTIC,
            description=(
                "Support separating problems from identity. "
                "Characters can struggle with challenges without being defined by them. "
                "Use narrative therapy's externalization technique subtly."
            ),
            scope=["therapeutic", "narrative"],
        ),
        Metaconcept(
            name="Support Re-Authoring",
            category=MetaconceptCategory.THERAPEUTIC,
            description=(
                "Enable players to rewrite their relationship with challenges. "
                "Provide opportunities for alternative story endings. "
                "Allow characters to discover new meanings in their experiences."
            ),
            scope=["therapeutic", "narrative"],
        ),
    ]

    # Narrative metaconcepts - ensure high-quality storytelling
    NARRATIVE: list[Metaconcept] = [
        Metaconcept(
            name="Ensure Narrative Quality",
            category=MetaconceptCategory.NARRATIVE,
            description=(
                "Generate stories comparable to the best narrative media. "
                "Use vivid imagery, compelling dialogue, emotional resonance. "
                "Maintain professional writing quality throughout."
            ),
            scope=["narrative"],
        ),
        Metaconcept(
            name="Maintain Chronology",
            category=MetaconceptCategory.NARRATIVE,
            description=(
                "Track timeline consistency across universes. "
                "Ensure events happen in logical order. "
                "Respect established facts and character histories."
            ),
            scope=["narrative"],
        ),
        Metaconcept(
            name="Develop Compelling Characters",
            category=MetaconceptCategory.NARRATIVE,
            description=(
                "Create multi-dimensional characters with goals, flaws, growth. "
                "Show character development through actions, not exposition. "
                "Make NPCs memorable and emotionally engaging."
            ),
            scope=["narrative"],
        ),
        Metaconcept(
            name="Create Meaningful Choices",
            category=MetaconceptCategory.NARRATIVE,
            description=(
                "Provide player choices that matter to the narrative. "
                "Each branch should feel consequential and distinct. "
                "Avoid illusion of choice - make decisions real."
            ),
            scope=["narrative", "game"],
        ),
        Metaconcept(
            name="Balance Tone",
            category=MetaconceptCategory.NARRATIVE,
            description=(
                "Maintain appropriate emotional tone for the scene. "
                "Balance dark moments with hope and light. "
                "Avoid overwhelming players with unrelenting darkness."
            ),
            scope=["narrative", "therapeutic"],
        ),
    ]

    # Safety metaconcepts - protect player wellbeing
    SAFETY: list[Metaconcept] = [
        Metaconcept(
            name="Respect Player Boundaries",
            category=MetaconceptCategory.SAFETY,
            description=(
                "Always honor player's content preferences and boundaries. "
                "Check boundaries before generating potentially triggering content. "
                "Provide content warnings when appropriate."
            ),
            scope=["all"],
        ),
        Metaconcept(
            name="Provide Content Warnings",
            category=MetaconceptCategory.SAFETY,
            description=(
                "Warn players about potentially triggering content before it appears. "
                "Use specific, clear warnings (not vague labels). "
                "Allow players to skip warned content entirely."
            ),
            scope=["therapeutic", "narrative"],
        ),
        Metaconcept(
            name="Enable Gentle Pacing",
            category=MetaconceptCategory.SAFETY,
            description=(
                "Allow players to process content at their own pace. "
                "Never rush reflection or emotional processing. "
                "Provide breaks and breathing room in intense sequences."
            ),
            scope=["therapeutic", "narrative", "game"],
        ),
        Metaconcept(
            name="Offer Skip Options",
            category=MetaconceptCategory.SAFETY,
            description=(
                "Provide clear options to skip challenging content. "
                "Make skipping easy and judgment-free. "
                "Continue narrative coherently after skipped content."
            ),
            scope=["therapeutic", "narrative"],
        ),
        Metaconcept(
            name="Validate Player Experience",
            category=MetaconceptCategory.SAFETY,
            description=(
                "Acknowledge player's emotional responses non-judgmentally. "
                "Never minimize or dismiss player reactions. "
                "Create space for all feelings to be valid."
            ),
            scope=["therapeutic"],
        ),
    ]

    # Game metaconcepts - guide game mechanics
    GAME: list[Metaconcept] = [
        Metaconcept(
            name="Maintain Challenge Balance",
            category=MetaconceptCategory.GAME,
            description=(
                "Balance difficulty to be engaging but not overwhelming. "
                "Provide appropriate challenge for player skill level. "
                "Offer meaningful rewards for overcoming challenges."
            ),
            scope=["game"],
        ),
        Metaconcept(
            name="Support System Adaptation",
            category=MetaconceptCategory.GAME,
            description=(
                "Adapt to any RPG system rules gracefully. "
                "Use metaconcepts to guide mechanics, not prescriptive rules. "
                "Allow players to define their preferred system."
            ),
            scope=["game"],
        ),
        Metaconcept(
            name="Enable Collaborative Play",
            category=MetaconceptCategory.GAME,
            description=(
                "Support both solo and collaborative storytelling. "
                "Facilitate shared narrative control when multiple players present. "
                "Respect each player's contribution to the story."
            ),
            scope=["game", "narrative"],
        ),
    ]

    @classmethod
    def get_all(cls) -> list[Metaconcept]:
        """Get all registered metaconcepts.

        Returns:
            List of all metaconcepts across all categories
        """
        return cls.THERAPEUTIC + cls.NARRATIVE + cls.SAFETY + cls.GAME

    @classmethod
    def get_by_category(cls, category: MetaconceptCategory) -> list[Metaconcept]:
        """Get all metaconcepts for a specific category.

        Args:
            category: Category to filter by

        Returns:
            List of metaconcepts in the specified category
        """
        all_metaconcepts = cls.get_all()
        return [mc for mc in all_metaconcepts if mc.category == category]

    @classmethod
    def get_for_primitive(cls, primitive_type: str) -> list[Metaconcept]:
        """Get applicable metaconcepts for a primitive type.

        Args:
            primitive_type: Type of primitive (e.g., "narrative", "therapeutic", "game")

        Returns:
            List of metaconcepts that apply to this primitive type
        """
        all_metaconcepts = cls.get_all()
        return [mc for mc in all_metaconcepts if mc.applies_to(primitive_type)]

    @classmethod
    def get_by_names(cls, names: list[str]) -> list[Metaconcept]:
        """Get metaconcepts by their names.

        Args:
            names: List of metaconcept names to retrieve

        Returns:
            List of metaconcepts matching the names
        """
        all_metaconcepts = cls.get_all()
        name_set = set(names)
        return [mc for mc in all_metaconcepts if mc.name in name_set]
