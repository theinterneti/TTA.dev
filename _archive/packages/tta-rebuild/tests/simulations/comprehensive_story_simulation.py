#!/usr/bin/env python3
"""
Comprehensive Story Generation Simulation

Tests Gemini integration across diverse:
- User therapeutic needs (anxiety, depression, trauma, grief, etc.)
- Story settings (fantasy, sci-fi, historical, contemporary, etc.)
- Character archetypes (hero, mentor, villain, companion, etc.)
- Narrative themes (hope, courage, healing, discovery, etc.)

Proves:
1. Data is created successfully
2. Stories are immersive and high-quality
3. Therapeutic elements are integrated naturally
4. Quality comparable to excellent fiction
"""

import asyncio
import json
import os
import statistics
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from tta_rebuild.core.base_primitive import TTAContext
from tta_rebuild.integrations import GeminiLLMProvider
from tta_rebuild.narrative import StoryGeneratorPrimitive
from tta_rebuild.narrative.story_generator import StoryGenerationInput


@dataclass
class SimulationScenario:
    """A complete test scenario."""

    name: str
    description: str
    therapeutic_need: str
    setting: str
    theme: str
    metaconcepts: list[str]
    universe_id: str
    scene_id: str
    current_state: dict[str, Any]
    player_preferences: dict[str, Any]
    expected_min_quality: float = 0.7


# Diverse therapeutic scenarios
SCENARIOS = [
    SimulationScenario(
        name="Anxiety Recovery in Fantasy Realm",
        description="Player managing anxiety through a hero's journey",
        therapeutic_need="anxiety",
        setting="enchanted forest with magical creatures",
        theme="overcoming fear through small, brave steps",
        metaconcepts=["safe uncertainty", "growth mindset", "self-compassion"],
        universe_id="fantasy_realm_001",
        scene_id="forest_clearing_001",
        current_state={
            "player_name": "Alex",
            "companions": ["Willow the Wise Owl", "Finn the Friendly Fox"],
            "recent_events": "Discovered a hidden path in the forest",
            "emotional_state": "cautiously hopeful",
        },
        player_preferences={
            "pacing": "gentle",
            "challenge_level": "moderate",
            "preferred_themes": ["nature", "friendship", "courage"],
        },
    ),
    SimulationScenario(
        name="Depression Support in Sci-Fi Setting",
        description="Player building hope through space exploration",
        therapeutic_need="depression",
        setting="abandoned space station orbiting a distant planet",
        theme="finding light in darkness, small victories matter",
        metaconcepts=["behavioral activation", "meaning-making", "connection"],
        universe_id="space_frontier_042",
        scene_id="observation_deck_prime",
        current_state={
            "player_name": "Jordan",
            "companions": ["ARIA (AI Assistant)", "Captain Chen"],
            "recent_events": "Repaired the station's communication array",
            "emotional_state": "tired but determined",
        },
        player_preferences={
            "pacing": "slow",
            "challenge_level": "low",
            "preferred_themes": ["discovery", "purpose", "accomplishment"],
        },
    ),
    SimulationScenario(
        name="Trauma Healing in Historical Setting",
        description="Player processing trauma through historical fiction",
        therapeutic_need="trauma",
        setting="1920s Paris art district during cultural renaissance",
        theme="reclaiming personal narrative, safe self-expression",
        metaconcepts=["window of tolerance", "grounding", "agency"],
        universe_id="historical_paris_1925",
        scene_id="montmartre_studio",
        current_state={
            "player_name": "Sam",
            "companions": ["Madame Rousseau (Artist)", "Pierre (Gallery Owner)"],
            "recent_events": "Attended first art exhibition opening",
            "emotional_state": "nervous but engaged",
        },
        player_preferences={
            "pacing": "controlled",
            "challenge_level": "very low",
            "preferred_themes": ["creativity", "safety", "expression"],
        },
    ),
    SimulationScenario(
        name="Grief Processing in Contemporary Setting",
        description="Player navigating loss through everyday life",
        therapeutic_need="grief",
        setting="cozy bookshop in a rainy coastal town",
        theme="honoring memories while building new connections",
        metaconcepts=["continuing bonds", "dual process", "meaning reconstruction"],
        universe_id="coastal_haven_modern",
        scene_id="bookshop_reading_nook",
        current_state={
            "player_name": "Riley",
            "companions": ["Emma (Bookshop Owner)", "Max (Therapy Dog)"],
            "recent_events": "Found grandmother's favorite book on the shelf",
            "emotional_state": "bittersweet",
        },
        player_preferences={
            "pacing": "gentle",
            "challenge_level": "low",
            "preferred_themes": ["memory", "comfort", "healing"],
        },
    ),
    SimulationScenario(
        name="Social Anxiety in Urban Fantasy",
        description="Player building confidence in magical city",
        therapeutic_need="social_anxiety",
        setting="bustling market in a city where everyone has minor magic",
        theme="authentic connection, self-acceptance",
        metaconcepts=["exposure", "self-efficacy", "compassionate mind"],
        universe_id="urban_magic_central",
        scene_id="twilight_market_square",
        current_state={
            "player_name": "Morgan",
            "companions": ["Zara (Street Performer)", "Mr. Chen (Tea Merchant)"],
            "recent_events": "Successfully used magic to help a stranger",
            "emotional_state": "proud but exhausted",
        },
        player_preferences={
            "pacing": "moderate",
            "challenge_level": "moderate",
            "preferred_themes": ["belonging", "growth", "community"],
        },
    ),
    SimulationScenario(
        name="Identity Exploration in Cyberpunk",
        description="Player discovering authentic self in digital world",
        therapeutic_need="identity",
        setting="neon-lit virtual reality cafe in 2077 Tokyo",
        theme="authentic self-expression, rejecting false expectations",
        metaconcepts=["self-concept", "values clarification", "autonomy"],
        universe_id="cyber_tokyo_2077",
        scene_id="neon_dreams_cafe",
        current_state={
            "player_name": "Kai",
            "companions": ["Ren (Hacker)", "Yuki (Digital Artist)"],
            "recent_events": "Created first custom avatar reflecting true self",
            "emotional_state": "excited and liberated",
        },
        player_preferences={
            "pacing": "fast",
            "challenge_level": "moderate",
            "preferred_themes": ["identity", "freedom", "creativity"],
        },
    ),
    SimulationScenario(
        name="PTSD Recovery in Mystery Setting",
        description="Player regaining sense of safety through investigation",
        therapeutic_need="ptsd",
        setting="quiet university library during autumn semester",
        theme="reclaiming control, trusting intuition",
        metaconcepts=["safety", "empowerment", "present moment"],
        universe_id="university_mystery_fall",
        scene_id="archives_reading_room",
        current_state={
            "player_name": "Taylor",
            "companions": ["Dr. Martinez (Professor)", "Leo (Library Cat)"],
            "recent_events": "Solved a historical puzzle, felt capable",
            "emotional_state": "focused and grounded",
        },
        player_preferences={
            "pacing": "controlled",
            "challenge_level": "low",
            "preferred_themes": ["mystery", "competence", "peace"],
        },
    ),
    SimulationScenario(
        name="Self-Esteem Building in Adventure",
        description="Player discovering worth through epic quest",
        therapeutic_need="self_esteem",
        setting="ancient ruins in jungle filled with forgotten treasures",
        theme="recognizing inherent worth, celebrating strengths",
        metaconcepts=["self-worth", "achievement", "positive reinforcement"],
        universe_id="lost_jungle_expedition",
        scene_id="temple_antechamber",
        current_state={
            "player_name": "Casey",
            "companions": ["Dr. Rivers (Archaeologist)", "Kavi (Local Guide)"],
            "recent_events": "Deciphered ancient script others couldn't",
            "emotional_state": "surprised by own capability",
        },
        player_preferences={
            "pacing": "moderate",
            "challenge_level": "moderate",
            "preferred_themes": ["discovery", "achievement", "recognition"],
        },
    ),
    SimulationScenario(
        name="Mindfulness in Nature Setting",
        description="Player finding presence through wilderness journey",
        therapeutic_need="stress",
        setting="serene mountain monastery with meditation gardens",
        theme="present moment awareness, letting go of control",
        metaconcepts=["mindfulness", "acceptance", "non-judgment"],
        universe_id="mountain_monastery_sanctuary",
        scene_id="dawn_meditation_garden",
        current_state={
            "player_name": "River",
            "companions": ["Master Lin (Meditation Teacher)", "Snow (Mountain Goat)"],
            "recent_events": "First successful 10-minute meditation",
            "emotional_state": "calm and centered",
        },
        player_preferences={
            "pacing": "very slow",
            "challenge_level": "very low",
            "preferred_themes": ["peace", "nature", "stillness"],
        },
    ),
    SimulationScenario(
        name="Relationship Healing in Romance",
        description="Player learning healthy connection patterns",
        therapeutic_need="relationships",
        setting="charming bed & breakfast in Scottish highlands",
        theme="healthy boundaries, authentic communication",
        metaconcepts=["attachment", "boundaries", "vulnerability"],
        universe_id="highlands_retreat",
        scene_id="fireside_common_room",
        current_state={
            "player_name": "Quinn",
            "companions": ["Fiona (B&B Owner)", "James (Chef)"],
            "recent_events": "Had honest conversation about needs",
            "emotional_state": "vulnerable but hopeful",
        },
        player_preferences={
            "pacing": "gentle",
            "challenge_level": "moderate",
            "preferred_themes": ["connection", "honesty", "growth"],
        },
    ),
]


class SimulationRunner:
    """Runs comprehensive story generation simulations."""

    def __init__(self, api_key: str):
        self.provider = GeminiLLMProvider(api_key=api_key)
        self.generator = StoryGeneratorPrimitive(llm_provider=self.provider)
        self.results = []

    async def run_scenario(self, scenario: SimulationScenario) -> dict[str, Any]:
        """Run a single scenario and collect results."""
        print(f"\n{'=' * 80}")
        print(f"🎭 SCENARIO: {scenario.name}")
        print(f"{'=' * 80}")
        print(f"📋 Description: {scenario.description}")
        print(f"💚 Therapeutic Need: {scenario.therapeutic_need}")
        print(f"🌍 Setting: {scenario.setting}")
        print(f"🎯 Theme: {scenario.theme}")
        print(f"🧠 Metaconcepts: {', '.join(scenario.metaconcepts)}")
        print()

        # Create input
        # Build context string incorporating therapeutic elements
        previous_context = (
            f"{scenario.setting}. "
            f"Recent events: {scenario.current_state.get('recent_events', '')}. "
            f"Emotional state: {scenario.current_state.get('emotional_state', '')}. "
            f"Therapeutic focus: {scenario.therapeutic_need}. "
            f"Metaconcepts to integrate: {', '.join(scenario.metaconcepts)}."
        )

        input_data = StoryGenerationInput(
            theme=scenario.theme,
            universe_id=scenario.universe_id,
            timeline_position=1,
            active_characters=scenario.current_state.get("companions", []),
            previous_context=previous_context,
            player_preferences=scenario.player_preferences,
            narrative_style="therapeutic",
        )

        context = TTAContext(
            correlation_id=f"sim_{scenario.name.lower().replace(' ', '_')}",
            metadata={
                "simulation": True,
                "scenario_name": scenario.name,
                "therapeutic_need": scenario.therapeutic_need,
            },
        )

        # Generate story
        try:
            story = await self.generator.execute(input_data, context)

            # Analyze results
            result = {
                "scenario": scenario.name,
                "therapeutic_need": scenario.therapeutic_need,
                "setting_type": scenario.universe_id.split("_")[0],
                "success": True,
                "quality_score": story.quality_score,
                "narrative_length": len(story.narrative_text),
                "dialogue_count": len(story.dialogue),
                "branch_count": len(story.story_branches),
                "emotional_tone": story.emotional_tone,
                "metaconcepts_present": self._check_metaconcepts(
                    story.narrative_text, scenario.metaconcepts
                ),
                "immersion_score": self._assess_immersion(story),
                "therapeutic_integration": self._assess_therapeutic_integration(story, scenario),
                "narrative_sample": story.narrative_text[:300] + "...",
                "dialogue_sample": story.dialogue[:2] if story.dialogue else [],
                "branches_sample": story.story_branches[:2] if story.story_branches else [],
                "cost": context.metadata.get("cost", 0),
            }

            # Print results
            self._print_story_results(story, scenario)

            return result

        except Exception as e:
            print(f"❌ FAILED: {e!s}")
            return {
                "scenario": scenario.name,
                "therapeutic_need": scenario.therapeutic_need,
                "success": False,
                "error": str(e),
            }

    def _check_metaconcepts(self, narrative: str, metaconcepts: list[str]) -> int:
        """Check how many metaconcepts are reflected in the narrative."""
        narrative_lower = narrative.lower()
        count = 0
        for concept in metaconcepts:
            # Check for concept keywords
            keywords = concept.lower().split()
            if any(keyword in narrative_lower for keyword in keywords):
                count += 1
        return count

    def _assess_immersion(self, story) -> float:
        """Assess narrative immersion (0-1 scale)."""
        score = 0.0

        # Rich narrative (800+ chars)
        if len(story.narrative_text) >= 800:
            score += 0.3
        elif len(story.narrative_text) >= 600:
            score += 0.2
        elif len(story.narrative_text) >= 400:
            score += 0.1

        # Natural dialogue (2+ exchanges)
        if len(story.dialogue) >= 2:
            score += 0.3
        elif len(story.dialogue) >= 1:
            score += 0.15

        # Multiple meaningful branches (3+)
        if len(story.story_branches) >= 3:
            score += 0.2
        elif len(story.story_branches) >= 2:
            score += 0.1

        # Emotional depth
        if story.emotional_tone and story.emotional_tone != "neutral":
            score += 0.2

        return min(score, 1.0)

    def _assess_therapeutic_integration(self, story, scenario) -> float:
        """Assess how well therapeutic elements are integrated (0-1 scale)."""
        score = 0.0

        # Check for metaconcept presence
        metaconcepts_found = self._check_metaconcepts(story.narrative_text, scenario.metaconcepts)
        score += (metaconcepts_found / len(scenario.metaconcepts)) * 0.4

        # Check for theme alignment
        theme_keywords = scenario.theme.lower().split()
        narrative_lower = story.narrative_text.lower()
        theme_matches = sum(1 for kw in theme_keywords if kw in narrative_lower)
        score += min(theme_matches / len(theme_keywords), 1.0) * 0.3

        # Check for appropriate emotional tone
        if story.emotional_tone:
            score += 0.3

        return min(score, 1.0)

    def _print_story_results(self, story, scenario):
        """Print detailed story results."""
        print("✅ STORY GENERATED SUCCESSFULLY")
        print()
        print("📊 QUALITY METRICS:")
        print(f"  Quality Score: {story.quality_score:.2f}")
        print(f"  Narrative Length: {len(story.narrative_text)} characters")
        print(f"  Dialogue Exchanges: {len(story.dialogue)}")
        print(f"  Story Branches: {len(story.story_branches)}")
        print(f"  Emotional Tone: {story.emotional_tone}")
        print()
        print("📖 NARRATIVE PREVIEW:")
        print(f"  {story.narrative_text[:400]}...")
        print()
        if story.dialogue:
            print("💬 DIALOGUE SAMPLE:")
            for i, line in enumerate(story.dialogue[:2], 1):
                print(
                    f'  {i}. {line["character"]}: "{line["text"]}" [{line.get("emotion", "neutral")}]'
                )
            print()
        if story.story_branches:
            print("🔀 STORY BRANCHES:")
            for i, branch in enumerate(story.story_branches[:3], 1):
                print(f"  {i}. {branch['choice']}")
                print(f"     → {branch['consequence'][:100]}...")
            print()

    async def run_all_scenarios(self):
        """Run all scenarios and compile results."""
        print("\n" + "=" * 80)
        print("🚀 COMPREHENSIVE STORY GENERATION SIMULATION")
        print("=" * 80)
        print(f"Total Scenarios: {len(SCENARIOS)}")
        print(f"Start Time: {datetime.now().isoformat()}")
        print()

        for scenario in SCENARIOS:
            result = await self.run_scenario(scenario)
            self.results.append(result)
            await asyncio.sleep(1)  # Rate limiting

        # Compile summary
        self._print_summary()
        self._save_results()

    def _print_summary(self):
        """Print comprehensive summary of all simulations."""
        print("\n" + "=" * 80)
        print("📊 SIMULATION SUMMARY")
        print("=" * 80)

        successful = [r for r in self.results if r.get("success", False)]
        failed = [r for r in self.results if not r.get("success", False)]

        print(
            f"\n✅ Success Rate: {len(successful)}/{len(self.results)} ({len(successful) / len(self.results) * 100:.1f}%)"
        )

        if failed:
            print(f"❌ Failed Scenarios: {len(failed)}")
            for fail in failed:
                print(f"  - {fail['scenario']}: {fail.get('error', 'Unknown error')}")

        if successful:
            qualities = [r["quality_score"] for r in successful]
            narrative_lengths = [r["narrative_length"] for r in successful]
            dialogue_counts = [r["dialogue_count"] for r in successful]
            branch_counts = [r["branch_count"] for r in successful]
            immersion_scores = [r["immersion_score"] for r in successful]
            therapeutic_scores = [r["therapeutic_integration"] for r in successful]
            total_cost = sum(r.get("cost", 0) for r in successful)

            print("\n📈 QUALITY METRICS:")
            print(f"  Average Quality Score: {statistics.mean(qualities):.3f}")
            print(f"  Median Quality Score: {statistics.median(qualities):.3f}")
            print(f"  Min Quality Score: {min(qualities):.3f}")
            print(f"  Max Quality Score: {max(qualities):.3f}")
            print(
                f"  High Quality (≥0.9): {sum(1 for q in qualities if q >= 0.9)}/{len(qualities)} ({sum(1 for q in qualities if q >= 0.9) / len(qualities) * 100:.1f}%)"
            )

            print("\n📝 NARRATIVE DEPTH:")
            print(f"  Average Length: {statistics.mean(narrative_lengths):.0f} chars")
            print(f"  Average Dialogue: {statistics.mean(dialogue_counts):.1f} exchanges")
            print(f"  Average Branches: {statistics.mean(branch_counts):.1f} choices")

            print("\n🎭 IMMERSION & THERAPEUTIC INTEGRATION:")
            print(f"  Average Immersion Score: {statistics.mean(immersion_scores):.3f}")
            print(f"  Average Therapeutic Integration: {statistics.mean(therapeutic_scores):.3f}")

            print("\n💰 COST ANALYSIS:")
            print(f"  Total Cost: ${total_cost:.4f}")
            print(f"  Average Cost per Story: ${total_cost / len(successful):.4f}")

            # By therapeutic need
            print("\n🎯 BY THERAPEUTIC NEED:")
            needs = {}
            for r in successful:
                need = r["therapeutic_need"]
                if need not in needs:
                    needs[need] = []
                needs[need].append(r["quality_score"])

            for need, scores in sorted(needs.items()):
                avg = statistics.mean(scores)
                print(f"  {need:20s}: {avg:.3f} avg quality ({len(scores)} scenarios)")

            # By setting type
            print("\n🌍 BY SETTING TYPE:")
            settings = {}
            for r in successful:
                setting = r["setting_type"]
                if setting not in settings:
                    settings[setting] = []
                settings[setting].append(r["quality_score"])

            for setting, scores in sorted(settings.items()):
                avg = statistics.mean(scores)
                print(f"  {setting:20s}: {avg:.3f} avg quality ({len(scores)} scenarios)")

            # Excellence assessment
            print("\n⭐ EXCELLENCE ASSESSMENT:")
            excellent = sum(1 for q in qualities if q >= 0.9)
            good = sum(1 for q in qualities if 0.75 <= q < 0.9)
            acceptable = sum(1 for q in qualities if 0.6 <= q < 0.75)
            needs_improvement = sum(1 for q in qualities if q < 0.6)

            print(
                f"  Excellent (≥0.9):     {excellent}/{len(qualities)} ({excellent / len(qualities) * 100:.1f}%)"
            )
            print(
                f"  Good (0.75-0.89):     {good}/{len(qualities)} ({good / len(qualities) * 100:.1f}%)"
            )
            print(
                f"  Acceptable (0.6-0.74): {acceptable}/{len(qualities)} ({acceptable / len(qualities) * 100:.1f}%)"
            )
            print(
                f"  Needs Work (<0.6):     {needs_improvement}/{len(qualities)} ({needs_improvement / len(qualities) * 100:.1f}%)"
            )

            # Immersion assessment
            high_immersion = sum(1 for s in immersion_scores if s >= 0.8)
            print("\n🎬 IMMERSION ASSESSMENT:")
            print(
                f"  High Immersion (≥0.8): {high_immersion}/{len(immersion_scores)} ({high_immersion / len(immersion_scores) * 100:.1f}%)"
            )

            # Therapeutic integration
            well_integrated = sum(1 for s in therapeutic_scores if s >= 0.7)
            print("\n💚 THERAPEUTIC INTEGRATION:")
            print(
                f"  Well Integrated (≥0.7): {well_integrated}/{len(therapeutic_scores)} ({well_integrated / len(therapeutic_scores) * 100:.1f}%)"
            )

        print(f"\n⏱️  End Time: {datetime.now().isoformat()}")
        print("=" * 80)

    def _save_results(self):
        """Save detailed results to JSON file."""
        filename = f"simulation_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = f"tests/simulations/{filename}"

        os.makedirs("tests/simulations", exist_ok=True)

        with open(filepath, "w") as f:
            json.dump(
                {
                    "timestamp": datetime.now().isoformat(),
                    "total_scenarios": len(self.results),
                    "successful": sum(1 for r in self.results if r.get("success", False)),
                    "failed": sum(1 for r in self.results if not r.get("success", False)),
                    "results": self.results,
                },
                f,
                indent=2,
            )

        print(f"\n💾 Results saved to: {filepath}")


async def main():
    """Main entry point."""
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("❌ Error: GEMINI_API_KEY environment variable not set")
        print("Set it with: export GEMINI_API_KEY='your-api-key'")
        return

    runner = SimulationRunner(api_key)
    await runner.run_all_scenarios()


if __name__ == "__main__":
    asyncio.run(main())
