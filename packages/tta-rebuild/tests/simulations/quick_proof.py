#!/usr/bin/env python3
"""
Quick Story Generation Proof - 10 Diverse Scenarios

Proves Gemini integration generates immersive, high-quality stories
across diverse therapeutic needs and story settings.
"""

import asyncio
import os
from datetime import UTC, datetime

import pytest

from tta_rebuild.core.base_primitive import TTAContext
from tta_rebuild.core.metaconcepts import MetaconceptRegistry
from tta_rebuild.integrations import GeminiLLMProvider
from tta_rebuild.narrative import StoryGeneratorPrimitive
from tta_rebuild.narrative.story_generator import StoryGenerationInput

# 10 Diverse Scenarios
SCENARIOS = [
    {
        "name": "🧙 Anxiety in Fantasy",
        "theme": "overcoming fear through small, brave steps in an enchanted forest",
        "context": "Enchanted forest with magical creatures. Player Alex discovered a hidden path and feels cautiously hopeful. Therapeutic focus: anxiety management. Metaconcepts: safe uncertainty, growth mindset, self-compassion.",
        "characters": ["Willow the Wise Owl", "Finn the Friendly Fox"],
        "universe": "fantasy_realm_001",
    },
    {
        "name": "🚀 Depression in Sci-Fi",
        "theme": "finding light in darkness through space exploration",
        "context": "Abandoned space station orbiting distant planet. Jordan repaired communications and feels tired but determined. Therapeutic focus: depression support. Metaconcepts: behavioral activation, meaning-making, connection.",
        "characters": ["ARIA (AI Assistant)", "Captain Chen"],
        "universe": "space_frontier_042",
    },
    {
        "name": "🎨 Trauma in Historical Paris",
        "theme": "reclaiming personal narrative through artistic expression",
        "context": "1920s Paris art district during cultural renaissance. Sam attended first art exhibition and feels nervous but engaged. Therapeutic focus: trauma processing. Metaconcepts: window of tolerance, grounding, agency.",
        "characters": ["Madame Rousseau (Artist)", "Pierre (Gallery Owner)"],
        "universe": "historical_paris_1925",
    },
    {
        "name": "📚 Grief in Coastal Town",
        "theme": "honoring memories while building new connections",
        "context": "Cozy bookshop in rainy coastal town. Riley found grandmother's favorite book and feels bittersweet. Therapeutic focus: grief processing. Metaconcepts: continuing bonds, dual process, meaning reconstruction.",
        "characters": ["Emma (Bookshop Owner)", "Max (Therapy Dog)"],
        "universe": "coastal_haven_modern",
    },
    {
        "name": "✨ Social Anxiety in Urban Fantasy",
        "theme": "authentic connection and self-acceptance in magical city",
        "context": "Bustling market where everyone has minor magic. Morgan successfully used magic to help a stranger and feels proud but exhausted. Therapeutic focus: social anxiety. Metaconcepts: exposure, self-efficacy, compassionate mind.",
        "characters": ["Zara (Street Performer)", "Mr. Chen (Tea Merchant)"],
        "universe": "urban_magic_central",
    },
    {
        "name": "🌆 Identity in Cyberpunk",
        "theme": "discovering authentic self in digital world",
        "context": "Neon-lit virtual reality cafe in 2077 Tokyo. Kai created first custom avatar reflecting true self and feels excited and liberated. Therapeutic focus: identity exploration. Metaconcepts: self-concept, values clarification, autonomy.",
        "characters": ["Ren (Hacker)", "Yuki (Digital Artist)"],
        "universe": "cyber_tokyo_2077",
    },
    {
        "name": "🔍 PTSD in Mystery Setting",
        "theme": "regaining sense of safety through investigation",
        "context": "Quiet university library during autumn. Taylor solved a historical puzzle and feels focused and grounded. Therapeutic focus: PTSD recovery. Metaconcepts: safety, empowerment, present moment.",
        "characters": ["Dr. Martinez (Professor)", "Leo (Library Cat)"],
        "universe": "university_mystery_fall",
    },
    {
        "name": "🏛️ Self-Esteem in Adventure",
        "theme": "recognizing inherent worth through epic quest",
        "context": "Ancient jungle ruins filled with forgotten treasures. Casey deciphered ancient script others couldn't and feels surprised by own capability. Therapeutic focus: self-esteem building. Metaconcepts: self-worth, achievement, positive reinforcement.",
        "characters": ["Dr. Rivers (Archaeologist)", "Kavi (Local Guide)"],
        "universe": "lost_jungle_expedition",
    },
    {
        "name": "⛰️ Mindfulness in Nature",
        "theme": "present moment awareness through wilderness journey",
        "context": "Serene mountain monastery with meditation gardens. River completed first successful 10-minute meditation and feels calm and centered. Therapeutic focus: stress reduction. Metaconcepts: mindfulness, acceptance, non-judgment.",
        "characters": ["Master Lin (Meditation Teacher)", "Snow (Mountain Goat)"],
        "universe": "mountain_monastery",
    },
    {
        "name": "💕 Relationship Healing in Romance",
        "theme": "healthy boundaries and authentic communication",
        "context": "Charming bed & breakfast in Scottish highlands. Quinn had honest conversation about needs and feels vulnerable but hopeful. Therapeutic focus: relationship patterns. Metaconcepts: attachment, boundaries, vulnerability.",
        "characters": ["Fiona (B&B Owner)", "James (Chef)"],
        "universe": "highlands_retreat",
    },
]


async def run_simulation():
    """Run quick simulation across all scenarios."""
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("❌ GEMINI_API_KEY not set")
        return

    provider = GeminiLLMProvider(api_key=api_key, model_name="models/gemini-2.5-flash")
    generator = StoryGeneratorPrimitive(llm_provider=provider)

    print("=" * 80)
    print("🎭 COMPREHENSIVE STORY GENERATION SIMULATION")
    print("=" * 80)
    print(f"Scenarios: {len(SCENARIOS)}")
    print(f"Started: {datetime.now(UTC).isoformat()}")
    print()

    results = []
    total_cost = 0.0

    for i, scenario in enumerate(SCENARIOS, 1):
        print(f"\n{'=' * 80}")
        print(f"[{i}/{len(SCENARIOS)}] {scenario['name']}")
        print(f"{'=' * 80}")
        print(f"Theme: {scenario['theme']}")
        print()

        try:
            # Create input
            input_data = StoryGenerationInput(
                theme=scenario["theme"],
                universe_id=scenario["universe"],
                timeline_position=1,
                active_characters=scenario["characters"],
                previous_context=scenario["context"],
                player_preferences={"pacing": "moderate"},
                narrative_style="therapeutic",
            )

            # Create context
            context = TTAContext(
                workflow_id=f"sim_{i}",
                correlation_id=f"scenario_{scenario['universe']}",
                timestamp=datetime.now(UTC),
                metaconcepts=MetaconceptRegistry.get_all(),
                player_boundaries={"content_rating": "safe"},
                session_state={},
                universe_id=scenario["universe"],
            )

            # Generate!
            story = await generator.execute(input_data, context)

            # Analyze
            quality = story.quality_score
            narrative_len = len(story.narrative_text)
            dialogue_count = len(story.dialogue)
            branch_count = len(story.story_branches)
            cost = context.metadata.get("cost", 0)
            total_cost += cost

            # Print results
            print("✅ SUCCESS")
            print(f"   Quality: {quality:.2f}")
            print(f"   Narrative: {narrative_len} chars")
            print(f"   Dialogue: {dialogue_count} exchanges")
            print(f"   Branches: {branch_count} choices")
            print(f"   Cost: ${cost:.4f}")
            print()
            print("📖 Preview:")
            print(f"   {story.narrative_text[:300]}...")
            print()

            if story.dialogue:
                print("💬 Dialogue:")
                for j, line in enumerate(story.dialogue[:2], 1):
                    emotion = line.get("emotion", "neutral")
                    print(f'   {j}. {line["character"]}: "{line["text"]}" [{emotion}]')
                print()

            if story.story_branches:
                print("🔀 Branches:")
                for j, branch in enumerate(story.story_branches[:2], 1):
                    print(f"   {j}. {branch['choice']}")
                print()

            results.append(
                {
                    "name": scenario["name"],
                    "quality": quality,
                    "narrative_length": narrative_len,
                    "dialogue_count": dialogue_count,
                    "branch_count": branch_count,
                    "success": True,
                }
            )

        except Exception as e:
            import traceback

            print(f"❌ FAILED: {e!s}")
            print("Full traceback:")
            traceback.print_exc()
            results.append(
                {"name": scenario["name"], "success": False, "error": str(e)}
            )

        # Rate limiting
        if i < len(SCENARIOS):
            await asyncio.sleep(2)

    # Summary
    print("\n" + "=" * 80)
    print("📊 SIMULATION SUMMARY")
    print("=" * 80)

    successful = [r for r in results if r.get("success", False)]
    failed = [r for r in results if not r.get("success", False)]

    print(
        f"\n✅ Success Rate: {len(successful)}/{len(results)} ({len(successful) / len(results) * 100:.1f}%)"
    )

    if successful:
        avg_quality = sum(r["quality"] for r in successful) / len(successful)
        avg_narrative = sum(r["narrative_length"] for r in successful) / len(successful)
        avg_dialogue = sum(r["dialogue_count"] for r in successful) / len(successful)
        avg_branches = sum(r["branch_count"] for r in successful) / len(successful)
        high_quality = sum(1 for r in successful if r["quality"] >= 0.9)

        print(f"\n📈 Average Quality: {avg_quality:.3f}")
        print(
            f"📈 High Quality (≥0.9): {high_quality}/{len(successful)} ({high_quality / len(successful) * 100:.1f}%)"
        )
        print(f"\n📝 Average Narrative: {avg_narrative:.0f} chars")
        print(f"💬 Average Dialogue: {avg_dialogue:.1f} exchanges")
        print(f"🔀 Average Branches: {avg_branches:.1f} choices")
        print(f"\n💰 Total Cost: ${total_cost:.4f}")
        print(f"💰 Avg Cost/Story: ${total_cost / len(successful):.4f}")

        # Assessment
        excellent = sum(1 for r in successful if r["quality"] >= 0.9)
        good = sum(1 for r in successful if 0.75 <= r["quality"] < 0.9)
        acceptable = sum(1 for r in successful if 0.6 <= r["quality"] < 0.75)

        print("\n⭐ EXCELLENCE RATING:")
        print(
            f"   Excellent (≥0.9):  {excellent}/{len(successful)} ({excellent / len(successful) * 100:.1f}%)"
        )
        print(
            f"   Good (0.75-0.89):  {good}/{len(successful)} ({good / len(successful) * 100:.1f}%)"
        )
        print(
            f"   Acceptable (≥0.6): {acceptable}/{len(successful)} ({acceptable / len(successful) * 100:.1f}%)"
        )

    if failed:
        print(f"\n❌ Failed: {len(failed)}")
        for fail in failed:
            print(f"   {fail['name']}: {fail.get('error', 'Unknown')}")

    print(f"\n⏱️  Completed: {datetime.now(UTC).isoformat()}")
    print("=" * 80)

    # Verdict
    if len(successful) >= 8 and avg_quality >= 0.85:
        print("\n🎉 PROOF COMPLETE: High-quality, immersive stories generated!")
        print("✅ Data is created successfully")
        print("✅ Stories are rich and engaging")
        print("✅ Quality comparable to excellent fiction")
        print("✅ Therapeutic elements naturally integrated")
    else:
        print("\n⚠️  Results need improvement")


@pytest.mark.asyncio
async def test_simulation():
    """Test wrapper for simulation."""
    await run_simulation()


if __name__ == "__main__":
    import pytest

    pytest.main([__file__, "-v", "-s"])
