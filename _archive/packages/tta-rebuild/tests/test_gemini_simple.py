#!/usr/bin/env python3
"""Simple test for Gemini LLM Provider with correct API."""

import asyncio
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from tta_rebuild.core.base_primitive import TTAContext
from tta_rebuild.integrations.gemini_provider import GeminiLLMProvider
from tta_rebuild.integrations.llm_provider import LLMConfig


async def test_basic():
    """Test basic generation with Gemini API."""
    print("\n" + "=" * 70)
    print("Testing Gemini LLM Provider - Basic Generation")
    print("=" * 70)

    # Create config
    config = LLMConfig(
        model="models/gemini-2.5-flash",  # Stable fast model
        max_tokens=100,
        temperature=0.7,
    )

    # Initialize provider
    provider = GeminiLLMProvider(config=config)
    print("✅ Provider initialized")

    # Create context
    from datetime import datetime

    context = TTAContext(
        workflow_id="test-gemini-basic",
        correlation_id="test-001",
        timestamp=datetime.now(),
        metaconcepts=["test"],
        player_boundaries={},
    )

    # Test generation
    prompt = (
        "Write one sentence describing a friendly neighborhood investigator who solves puzzles."
    )
    print(f"\n📝 Prompt: {prompt}")

    response = await provider.generate(prompt, context)

    print("\n✅ Generated text:")
    print(f"   {response.text}")
    print("\n📊 Stats:")
    print(f"   Tokens: {response.tokens_used}")
    print(f"   Model: {response.model}")
    print(f"   Cost: ${response.metadata.get('cost_usd', 0):.6f}")

    return True


async def test_json():
    """Test JSON generation."""
    print("\n" + "=" * 70)
    print("Testing Gemini LLM Provider - JSON Generation")
    print("=" * 70)

    # Create config
    config = LLMConfig(
        model="models/gemini-2.5-flash",  # Stable fast model
        max_tokens=200,
        temperature=0.7,
    )

    # Initialize provider
    provider = GeminiLLMProvider(config=config)

    # Create context
    from datetime import datetime

    context = TTAContext(
        workflow_id="test-gemini-json",
        correlation_id="test-002",
        timestamp=datetime.now(),
        metaconcepts=["test"],
        player_boundaries={},
    )

    # Test JSON generation
    prompt = """Generate a character profile with these fields:
- name: A detective's name
- description: One sentence description
- trait: One personality trait"""

    print(f"\n📝 Prompt: {prompt[:100]}...")

    response = await provider.generate_json(prompt, context, max_tokens=200, temperature=0.7)

    print("\n✅ Generated JSON:")
    import json

    print(json.dumps(response, indent=2))

    # Validate structure
    assert "name" in response
    assert "description" in response
    assert "trait" in response
    print("\n✅ JSON structure validated")

    return True


async def main():
    """Run all tests."""
    print("\n🚀 Gemini LLM Provider Test Suite")

    # Check API key
    if not os.getenv("GEMINI_API_KEY"):
        print("\n❌ Error: GEMINI_API_KEY not set in environment")
        print("   Please set: export GEMINI_API_KEY='your-key-here'")
        return

    tests = [
        ("Basic Generation", test_basic),
        ("JSON Generation", test_json),
    ]

    passed = 0
    failed = 0

    for name, test_func in tests:
        try:
            await test_func()
            passed += 1
        except Exception as e:
            print(f"\n❌ Test failed: {e}")
            import traceback

            traceback.print_exc()
            failed += 1

    print("\n" + "=" * 70)
    print("📊 Test Summary")
    print("=" * 70)
    print(f"Passed: {passed}/{len(tests)}")
    print(f"Failed: {failed}/{len(tests)}")

    if failed > 0:
        print("\n❌ Some tests failed")
    else:
        print("\n✅ All tests passed!")


if __name__ == "__main__":
    asyncio.run(main())
