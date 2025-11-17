#!/usr/bin/env python3
"""Demo: Complete narrative workflow with all primitives.

Shows end-to-end usage:
- Story generation
- Timeline tracking
- Character development
- Branch validation

Run: python examples/complete_workflow_demo.py
"""

import asyncio
from datetime import UTC, datetime

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


def print_section(title: str):
    """Print a section header."""
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)


async def main():
    """Run complete narrative workflow demo."""
    print_section("TTA Narrative Engine - Complete Workflow Demo")

    # Setup
    context = TTAContext(
        workflow_id="complete-demo",
        correlation_id="demo-001",
        timestamp=datetime.now(UTC),
        metaconcepts=MetaconceptRegistry.get_all(),
        player_boundaries={"violence": "low"},
        session_state={},
    )

    print("\n✓ Initializing primitives...")
    llm = MockLLMProvider()
    story_gen = StoryGeneratorPrimitive(llm_provider=llm)
    timeline = TimelineManagerPrimitive()
    characters = CharacterStatePrimitive()
    validator = BranchValidatorPrimitive()
    print("✓ All primitives ready!\n")

    # === 1. GENERATE STORY ===
    print_section("1. Generate Story")

    story_input = StoryGenerationInput(
        theme="A detective investigates strange disappearances",
        universe_id="mystery_case",
        timeline_position=0,
        active_characters=["Detective Morgan"],
        previous_context="",
        player_preferences={"genre": "mystery"},
    )

    story = await story_gen.execute(story_input, context)
    print("✓ Story generated!")
    print(f"  Scene: {story.scene_id}")
    print(f"  Setting: {story.setting_description[:60]}...")
    print(f"  Quality: {story.quality_score:.2f}")

    # === 2. TRACK IN TIMELINE ===
    print_section("2. Track Events in Timeline")

    # Add first event
    event1 = TimelineUpdate(
        universe_id="mystery_case",
        event_type="story_beat",
        event_data={"description": "Detective Morgan arrives at crime scene"},
        timestamp=0,
        character_ids=["Detective Morgan"],
    )
    state = await timeline.execute(event1, context)
    print("✓ Event 1 added: Crime scene arrival")
    print(f"  Coherence: {state.timeline_coherence_score:.2f}")

    # Add second event
    event2 = TimelineUpdate(
        universe_id="mystery_case",
        event_type="story_beat",
        event_data={"description": "Morgan finds mysterious symbol"},
        timestamp=100,
        character_ids=["Detective Morgan"],
        causal_links=["Detective Morgan arrives at crime scene"],
    )
    state = await timeline.execute(event2, context)
    print("✓ Event 2 added: Symbol discovery")
    print(f"  Total events: {len(state.event_history)}")
    print(f"  Coherence: {state.timeline_coherence_score:.2f}")

    # === 3. DEVELOP CHARACTER ===
    print_section("3. Develop Character")

    interaction1 = CharacterInteraction(
        character_id="Detective Morgan",
        scene_context="Morgan examines crime scene with concern",
        emotional_trigger="Evidence suggests something supernatural",
        story_events=["Arrived at scene", "Found strange symbol"],
        development_opportunity="Face fear of the unknown",
    )

    response = await characters.execute(interaction1, context)
    print("✓ Character interaction processed")
    print(f"  Emotion: {response.emotion}")
    print(f'  Dialogue: "{response.dialogue}"')
    print(f"  Thoughts: {response.internal_monologue[:60]}...")

    # Set goal
    characters.set_development_goal(
        "Detective Morgan",
        "Uncover the truth behind disappearances",
        0.1,  # 10% initial progress
    )
    print("✓ Development goal set: solve mystery")

    # === 4. VALIDATE BRANCHES ===
    print_section("4. Validate Story Branches")

    # Get timeline for context
    events = timeline.get_timeline("mystery_case")
    timeline_ctx = [e.event_data.get("description", "") for e in events]

    # Valid branch
    valid_branch = BranchProposal(
        universe_id="mystery_case",
        branch_description="Morgan investigates the symbol's meaning",
        choice_text="Research the mysterious symbol in police archives",
        affected_characters=["Detective Morgan"],
        timeline_context=timeline_ctx,
        universe_rules={"realistic": "mostly realistic with subtle mystery"},
    )

    result = await validator.execute(valid_branch, context)
    print("\n✓ Branch validated: VALID")
    print(f"  Score: {result.overall_score:.2f}")
    print(f"  Issues: {len(result.issues)}")

    # Invalid branch
    invalid_branch = BranchProposal(
        universe_id="mystery_case",
        branch_description="Morgan uses magic",
        choice_text="Cast spell",  # Too vague + violates rules
        affected_characters=["Detective Morgan"],
        timeline_context=timeline_ctx,
        universe_rules={"realistic": "mostly realistic", "no_magic": "true"},
    )

    result2 = await validator.execute(invalid_branch, context)
    print("\n✗ Branch validated: INVALID")
    print(f"  Score: {result2.overall_score:.2f}")
    print(f"  Issues: {len(result2.issues)}")
    for issue in result2.issues[:2]:
        print(f"    - [{issue.severity.value}] {issue.message}")

    # === 5. CONTINUE DEVELOPMENT ===
    print_section("5. Continue Character Journey")

    interaction2 = CharacterInteraction(
        character_id="Detective Morgan",
        scene_context="Morgan discovers connection to ancient cult",
        emotional_trigger="Revelation brings determination and unease",
        story_events=["Researched symbol", "Found cult reference"],
        development_opportunity="Confront deeper conspiracy",
    )

    response2 = await characters.execute(interaction2, context)
    print("✓ Second interaction")
    print(f"  Emotion shift: {response2.emotion}")
    print(f'  New dialogue: "{response2.dialogue}"')

    # Check progress
    morgan = characters.get_character("Detective Morgan")
    if morgan:
        for name, progress in morgan.development_goals.items():
            print(f"  Goal '{name}': {progress:.0%} progress")
        print(f"  Arc stage: {morgan.arc_stage}")

    # === SUMMARY ===
    print_section("SUMMARY")

    print(f"\n📅 Timeline: {len(timeline.get_timeline('mystery_case'))} events")
    print(f"👤 Characters: {len(characters.get_all_characters())}")
    print(
        f"🌿 Validated Branches: {len(validator.get_validated_branches('mystery_case'))}"
    )

    print_section("Demo Complete!")
    print("\nAll primitives demonstrated:")
    print("  ✓ StoryGeneratorPrimitive")
    print("  ✓ TimelineManagerPrimitive")
    print("  ✓ CharacterStatePrimitive")
    print("  ✓ BranchValidatorPrimitive")
    print("\nReady for production use!")


if __name__ == "__main__":
    asyncio.run(main())
