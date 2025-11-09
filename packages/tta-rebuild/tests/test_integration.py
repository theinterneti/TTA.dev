#!/usr/bin/env python3
"""Quick integration test for Gemini + StoryGenerator.

This script demonstrates the integration working end-to-end.
Run with: GEMINI_API_KEY=your-key python test_integration.py
"""

import asyncio
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from datetime import UTC, datetime

from tta_rebuild import MetaconceptRegistry, TTAContext
from tta_rebuild.integrations import GeminiLLMProvider, LLMConfig
from tta_rebuild.narrative import (
    StoryGenerationInput,
    StoryGeneratorPrimitive,
)


async def main():
    """Run integration test."""
    print("\n" + "=" * 70)
    print("🚀 Gemini + StoryGenerator Integration Test")
    print("=" * 70)

    # Check API key
    if not os.getenv("GEMINI_API_KEY"):
        print("\n❌ Error: GEMINI_API_KEY environment variable not set")
        print("Set it with: export GEMINI_API_KEY=your-key-here")
        return 1

    # Step 1: Create Gemini provider
    print("\n1️⃣  Creating Gemini LLM Provider...")
    config = LLMConfig(
        model="models/gemini-2.5-flash",
        max_tokens=2000,
        temperature=0.7,
    )
    gemini_provider = GeminiLLMProvider(config=config)
    print(f"   ✅ Provider initialized: {config.model}")

    # Step 2: Create StoryGenerator with Gemini
    print("\n2️⃣  Creating StoryGenerator with Gemini...")
    story_generator = StoryGeneratorPrimitive(
        llm_provider=gemini_provider,
        name="StoryGenerator_Gemini_Integration",
    )
    print("   ✅ StoryGenerator ready")

    # Step 3: Prepare test data
    print("\n3️⃣  Preparing test data...")
    context = TTAContext(
        workflow_id="integration-test",
        correlation_id="test-001",
        timestamp=datetime.now(UTC),
        metaconcepts=MetaconceptRegistry.get_all(),
        player_boundaries={"violence": "low", "mature_themes": "off"},
        session_state={"player_name": "TestPlayer"},
    )

    story_input = StoryGenerationInput(
        theme="courage and self-discovery",
        universe_id="integration-test-universe",
        timeline_position=1,
        active_characters=["hero", "mentor"],
        previous_context="The hero begins their journey of self-discovery.",
        player_preferences={"violence": "low", "mature_themes": "off"},
        narrative_style="therapeutic",
    )
    print("   ✅ Test data ready")

    # Step 4: Generate story with real Gemini API
    print("\n4️⃣  Generating story with Gemini API...")
    print("   (This may take 5-10 seconds...)")

    story = await story_generator.execute(story_input, context)

    print("\n   ✅ Story generated successfully!")

    # Step 5: Verify results
    print("\n5️⃣  Verifying results...")

    checks = [
        ("Scene ID", story.scene_id, bool(story.scene_id)),
        (
            "Narrative text",
            f"{len(story.narrative_text)} chars",
            len(story.narrative_text) >= 200,
        ),
        ("Dialogue lines", len(story.dialogue), len(story.dialogue) >= 2),
        ("Story branches", len(story.story_branches), len(story.story_branches) >= 2),
        ("Quality score", f"{story.quality_score:.2f}", story.quality_score >= 0.75),
    ]

    all_passed = True
    for name, value, passed in checks:
        status = "✅" if passed else "❌"
        print(f"   {status} {name}: {value}")
        all_passed = all_passed and passed

    # Step 6: Display sample output
    print("\n6️⃣  Sample Output:")
    print(f"\n   Scene: {story.scene_id}")
    print(f"   Tone: {story.emotional_tone}")
    print(f"   Quality: {story.quality_score:.2f}")
    print("\n   Narrative (first 300 chars):")
    print(f"   {story.narrative_text[:300]}...")

    print(f"\n   Dialogue ({len(story.dialogue)} lines):")
    for i, line in enumerate(story.dialogue[:3], 1):
        print(f'   {i}. {line.character_id}: "{line.text}" ({line.emotion})')

    print(f"\n   Branches ({len(story.story_branches)} choices):")
    for i, branch in enumerate(story.story_branches[:3], 1):
        print(f"   {i}. {branch['choice']}")

    # Step 7: Cost tracking
    print("\n7️⃣  Cost Tracking:")
    print(f"   Total calls: {gemini_provider.call_count}")
    print(f"   Prompt tokens: {gemini_provider.total_prompt_tokens}")
    print(f"   Completion tokens: {gemini_provider.total_completion_tokens}")
    print(f"   Total cost: ${gemini_provider.total_cost_usd:.6f}")

    # Final verdict
    print("\n" + "=" * 70)
    if all_passed:
        print("✅ INTEGRATION TEST PASSED")
        print("\nGemini provider successfully integrated with StoryGenerator!")
        print("Quality score significantly higher than mock (expected 0.8+ vs 0.2)")
        return 0
    print("❌ INTEGRATION TEST FAILED")
    print("\nSome checks did not pass. See details above.")
    return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
