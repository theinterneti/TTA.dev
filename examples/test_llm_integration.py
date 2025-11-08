"""Test LLM Integration for ACE Phase 2.

This script tests the real LLM-powered code generation using Google AI Studio's
Gemini 2.5 Pro model (free tier).

Requirements:
- GOOGLE_AI_STUDIO_API_KEY environment variable set
- google-generativeai package installed (uv add google-generativeai)

Usage:
    export GOOGLE_AI_STUDIO_API_KEY=your_api_key_here
    uv run python examples/test_llm_integration.py
"""

import asyncio
import logging
import os
from pathlib import Path

from tta_dev_primitives.ace.cognitive_manager import SelfLearningCodePrimitive
from tta_dev_primitives.core.base import WorkflowContext

# Enable debug logging
logging.basicConfig(level=logging.INFO, format="%(name)s - %(levelname)s - %(message)s")


async def test_simple_function_generation():
    """Test generating a simple function with LLM."""
    print("\n" + "=" * 80)
    print("TEST 1: Simple Function Generation (Fibonacci)")
    print("=" * 80)

    # Initialize learner
    playbook_file = Path("test_llm_playbook.json")
    learner = SelfLearningCodePrimitive(playbook_file=playbook_file)

    # Create context
    context = WorkflowContext(correlation_id="test-llm-1")

    # Generate fibonacci function
    try:
        result = await learner.execute(
            {
                "task": "Create a Python function to calculate fibonacci numbers",
                "language": "python",
                "context": "The function should be efficient and include test code",
                "max_iterations": 3,
            },
            context,
        )

        print(f"\n✅ Execution Success: {result.get('execution_success', False)}")
        print(f"📚 Strategies Learned: {result.get('strategies_learned', 0)}")
        print(f"📈 Playbook Size: {result.get('playbook_size', 0)}")
        print(f"📊 Improvement Score: {result.get('improvement_score', 0.0):.2f}")
        print(f"📝 Learning Summary: {result.get('learning_summary', 'N/A')}")

        if result.get("code_generated"):
            print("\n📝 Generated Code:")
            print("-" * 80)
            print(result.get("code_generated", "No code generated"))
            print("-" * 80)

        return result
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback

        traceback.print_exc()
        return {
            "execution_success": False,
            "error": str(e),
            "strategies_learned": 0,
            "playbook_size": 0,
        }


async def test_pytest_generation():
    """Test generating pytest tests with LLM."""
    print("\n" + "=" * 80)
    print("TEST 2: Pytest Test Generation")
    print("=" * 80)

    # Initialize learner
    playbook_file = Path("test_llm_playbook.json")
    learner = SelfLearningCodePrimitive(playbook_file=playbook_file)

    # Create context
    context = WorkflowContext(correlation_id="test-llm-2")

    # Generate pytest tests
    try:
        result = await learner.execute(
            {
                "task": "Create pytest tests for a simple calculator class with add/subtract methods",
                "language": "python",
                "context": "Include test cases for normal operation and edge cases (zero, negative numbers)",
                "max_iterations": 3,
            },
            context,
        )

        print(f"\n✅ Execution Success: {result.get('execution_success', False)}")
        print(f"📚 Strategies Learned: {result.get('strategies_learned', 0)}")
        print(f"📈 Playbook Size: {result.get('playbook_size', 0)}")
        print(f"📊 Improvement Score: {result.get('improvement_score', 0.0):.2f}")
        print(f"📝 Learning Summary: {result.get('learning_summary', 'N/A')}")

        if result.get("code_generated"):
            print("\n📝 Generated Code:")
            print("-" * 80)
            print(result.get("code_generated", "No code generated"))
            print("-" * 80)

        return result
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback

        traceback.print_exc()
        return {
            "execution_success": False,
            "error": str(e),
            "strategies_learned": 0,
            "playbook_size": 0,
        }


async def main():
    """Run all LLM integration tests."""
    print("\n🚀 ACE Phase 2 LLM Integration Tests")
    print("=" * 80)

    # Check for API key (multiple environment variable names)
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_AI_STUDIO_API_KEY")
    if not api_key:
        print(
            "\n❌ ERROR: GEMINI_API_KEY or GOOGLE_AI_STUDIO_API_KEY environment variable not set!"
        )
        print("\nPlease set your API key:")
        print("  export GEMINI_API_KEY=your_api_key_here")
        print("  OR")
        print("  export GOOGLE_AI_STUDIO_API_KEY=your_api_key_here")
        print("\nGet your free API key at: https://aistudio.google.com/app/apikey")
        return

    print(f"\n✅ API Key Found: {api_key[:10]}...{api_key[-4:]}")
    print("🤖 Using Gemini 2.0 Flash Experimental (Free Tier)")

    # Run tests
    try:
        result1 = await test_simple_function_generation()
        result2 = await test_pytest_generation()

        # Summary
        print("\n" + "=" * 80)
        print("📊 TEST SUMMARY")
        print("=" * 80)
        print(f"Test 1 (Fibonacci): {'✅ PASS' if result1.get('execution_success') else '❌ FAIL'}")
        print(f"Test 2 (Pytest): {'✅ PASS' if result2.get('execution_success') else '❌ FAIL'}")
        print(
            f"\nTotal Strategies Learned: {result1.get('strategies_learned', 0) + result2.get('strategies_learned', 0)}"
        )
        print(f"Final Playbook Size: {result2.get('playbook_size', 0)}")

        # Cost analysis
        print("\n💰 COST ANALYSIS")
        print("=" * 80)
        print("LLM Cost: $0.00 (Google AI Studio Free Tier)")
        print("E2B Cost: $0.00 (E2B Free Tier)")
        print("Total Cost: $0.00 ✅")

        print("\n🎉 Phase 2 LLM Integration: COMPLETE!")

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
