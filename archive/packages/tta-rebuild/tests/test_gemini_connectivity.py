#!/usr/bin/env python3
"""Test Gemini LLM Provider connectivity and basic functionality."""

import asyncio
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from tta_rebuild.integrations.gemini_provider import GeminiLLMProvider


async def test_basic_generation():
    """Test basic text generation."""
    print("=" * 60)
    print("Testing Gemini LLM Provider - Basic Generation")
    print("=" * 60)

    try:
        # Initialize provider
        provider = GeminiLLMProvider(
            api_key=os.getenv("GEMINI_API_KEY"), temperature=0.7
        )
        print("✅ Provider initialized")

        # Test basic generation
        prompt = "Write a one-sentence description of a mysterious detective."
        print(f"\n📝 Prompt: {prompt}")

        response = await provider.generate(prompt, max_tokens=100)
        print(f"\n🤖 Response: {response}")

        # Show usage stats
        stats = provider.get_usage_stats()
        print("\n📊 Usage Stats:")
        print(f"   Calls: {stats['call_count']}")
        print(f"   Total Tokens: {stats['total_tokens']}")
        print(f"   Cost: ${stats['total_cost_usd']:.6f}")

        print("\n✅ Basic generation test PASSED")
        return True

    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False


async def test_json_generation():
    """Test JSON generation."""
    print("\n" + "=" * 60)
    print("Testing Gemini LLM Provider - JSON Generation")
    print("=" * 60)

    try:
        provider = GeminiLLMProvider()

        prompt = """Generate a character profile with these fields:
- name: A detective's name
- description: One sentence description
- personality_traits: List of 3 traits
- motivation: One sentence about their goal

Return as JSON only."""

        print(f"\n📝 Prompt: {prompt[:100]}...")

        response = await provider.generate_json(prompt, max_tokens=300)
        print("\n🤖 Response (JSON):")
        import json

        print(json.dumps(response, indent=2))

        # Validate structure
        required_fields = ["name", "description", "personality_traits", "motivation"]
        for field in required_fields:
            assert field in response, f"Missing field: {field}"

        print("\n✅ JSON generation test PASSED")
        return True

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback

        traceback.print_exc()
        return False


async def test_narrative_generation():
    """Test narrative story generation (Week 4 use case)."""
    print("\n" + "=" * 60)
    print("Testing Gemini LLM Provider - Narrative Generation")
    print("=" * 60)

    try:
        provider = GeminiLLMProvider(temperature=0.8)

        prompt = """Create a short narrative scene (2-3 paragraphs) with this theme:
"A warrior discovers an ancient artifact that changes their destiny"

Include:
- Vivid setting description
- Character emotions and reactions
- A moment of revelation or discovery

Write in an engaging, descriptive style."""

        print("\n📝 Generating narrative...")

        response = await provider.generate(prompt, max_tokens=500)
        print("\n📖 Generated Narrative:\n")
        print(response)

        # Check quality
        assert len(response) > 100, "Response too short"
        assert any(
            word in response.lower() for word in ["warrior", "artifact", "ancient"]
        ), "Missing key elements"

        stats = provider.get_usage_stats()
        print("\n📊 This call:")
        print(f"   Tokens: ~{stats['total_tokens']}")
        print(f"   Cost: ${stats['total_cost_usd']:.6f}")

        print("\n✅ Narrative generation test PASSED")
        return True

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback

        traceback.print_exc()
        return False


async def main():
    """Run all tests."""
    print("🚀 Gemini LLM Provider Test Suite\n")

    # Check API key
    if not os.getenv("GEMINI_API_KEY"):
        print("❌ ERROR: GEMINI_API_KEY not set in environment")
        print("   Set it with: export GEMINI_API_KEY=your_key_here")
        return False

    results = []

    # Run tests
    results.append(await test_basic_generation())
    results.append(await test_json_generation())
    results.append(await test_narrative_generation())

    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Summary")
    print("=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"Passed: {passed}/{total}")

    if passed == total:
        print("\n✅ ALL TESTS PASSED! Gemini integration is working! 🎉")
        return True
    print(f"\n❌ {total - passed} test(s) failed")
    return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
