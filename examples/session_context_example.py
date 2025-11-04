#!/usr/bin/env python3
"""
SessionContextBuilder Example Usage

This script demonstrates how to use SessionContextBuilder to generate
synthetic context for AI agent workflows with minimal input.

Run with: uv run python examples/session_context_example.py
"""

import asyncio
import sys
from pathlib import Path

# Add packages to path for development
repo_root = Path(__file__).parent.parent
sys.path.insert(0, str(repo_root / "packages" / "tta-kb-automation" / "src"))
sys.path.insert(0, str(repo_root / "packages" / "tta-dev-primitives" / "src"))

# ruff: noqa: E402
from tta_kb_automation.tools import SessionContextBuilder


async def example_1_basic_usage():
    """Example 1: Basic usage - Get context for CachePrimitive."""
    print("=" * 80)
    print("Example 1: Basic Usage - CachePrimitive Context")
    print("=" * 80)

    builder = SessionContextBuilder()

    # Build context for CachePrimitive
    result = await builder.build_context(topic="CachePrimitive")

    # Display summary
    print("\n📋 Generated Summary:")
    print("-" * 80)
    print(result["summary"])
    print("-" * 80)

    # Show statistics
    print("\n📊 Context Statistics:")
    print(f"  - KB Pages Found: {len(result['kb_pages'])}")
    print(f"  - Code Files Found: {len(result['code_files'])}")
    print(f"  - TODOs Found: {len(result['todos'])}")
    print(f"  - Test Files Found: {len(result['tests'])}")
    print(f"  - Related Topics: {len(result['related_topics'])}")

    # Show top KB page
    if result["kb_pages"]:
        print("\n📄 Top KB Page:")
        top_page = result["kb_pages"][0]
        print(f"  Title: {top_page['title']}")
        # relevance_score may not be present; default to 0.0
        print(f"  Relevance: {top_page.get('relevance_score', 0.0):.2f}")
        print(f"  Excerpt: {top_page['excerpt'][:100]}...")

    print("\n✅ Example 1 Complete\n")


async def example_2_selective_inclusion():
    """Example 2: Selective inclusion - Only KB and code, skip TODOs and tests."""
    print("\n" + "=" * 80)
    print("Example 2: Selective Inclusion - KB + Code Only")
    print("=" * 80)

    builder = SessionContextBuilder()

    # Build context with only KB pages and code files
    result = await builder.build_context(
        topic="RouterPrimitive",
        include_kb=True,
        include_code=True,
        include_todos=False,
        include_tests=False,
    )


async def example_3_custom_configuration():
    """Example 3: Custom configuration - Adjust limits for larger context."""
    print("\n" + "=" * 80)
    print("Example 3: Custom Configuration - Increased Limits")
    print("=" * 80)

    # Create builder with custom limits
    builder = SessionContextBuilder(
        max_kb_pages=10,
        max_code_files=15,
        max_todos=25,
        max_tests=8,
    )

    # Build context with custom configuration
    result = await builder.build_context(topic="RetryPrimitive")


async def example_4_code_review_prep():
    """Example 4: Code review preparation - Get comprehensive context."""
    print("\n" + "=" * 80)
    print("Example 4: Code Review Preparation Workflow")
    print("=" * 80)

    builder = SessionContextBuilder()

    # Simulate preparing for code review of RouterPrimitive PR
    print("\n📝 Preparing context for PR review: RouterPrimitive enhancements\n")

    result = await builder.build_context(
        topic="RouterPrimitive",
        include_kb=True,  # Get documentation
        include_code=True,  # Get implementation
        include_todos=True,  # Check if related TODOs addressed
        include_tests=True,  # Verify test coverage
    )


async def example_5_learning_path():
    """Example 5: Learning path generation - Context for onboarding."""
    print("\n" + "=" * 80)
    print("Example 5: Learning Path Generation")
    print("=" * 80)

    builder = SessionContextBuilder(
        max_kb_pages=8,  # More KB pages for learning resources
        max_code_files=5,  # Fewer code files (focusing on docs)
    )

    # Build context for learning about primitives
    print("\n📚 Generating learning resources for new developers\n")

    result = await builder.build_context(
        topic="TTA Primitives",
        include_kb=True,  # Learning materials
        include_code=True,  # Example implementations
        include_todos=False,  # Skip TODOs for learning
        include_tests=True,  # Show test examples
    )


async def example_6_multi_topic():
    """Example 6: Multi-topic context - Combine contexts for related features."""
    print("\n" + "=" * 80)
    print("Example 6: Multi-Topic Context Building")
    print("=" * 80)

    builder = SessionContextBuilder()

    # Build context for multiple related topics
    topics = ["CachePrimitive", "RouterPrimitive", "RetryPrimitive"]
    print(f"\n🔗 Building combined context for: {', '.join(topics)}\n")

    combined_result = {
        "topics": topics,
        "contexts": [],
        "all_related_topics": set(),
    }

    for topic in topics:
        result = await builder.build_context(topic=topic)


async def main():
    """Run all examples."""
    print("\n")
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 15 + "SessionContextBuilder - Example Usage" + " " * 24 + "║")
    print(
        "║"
        + " " * 10
        + "Synthetic Context Generation for AI Agent Workflows"
        + " " * 15
        + "║"
    )
    print("╚" + "=" * 78 + "╝")
    print("\n")

    try:
        # Run all examples
        await example_1_basic_usage()
        await asyncio.sleep(0.5)  # Brief pause between examples

        await example_2_selective_inclusion()
        await asyncio.sleep(0.5)

        await example_3_custom_configuration()
        await asyncio.sleep(0.5)

        await example_4_code_review_prep()
        await asyncio.sleep(0.5)

        await example_5_learning_path()
        await asyncio.sleep(0.5)

        await example_6_multi_topic()

        # Final summary
        print("=" * 80)
        print("🎉 All Examples Complete!")
        print("=" * 80)
        print("\n💡 Key Takeaways:")
        print(
            "  1. SessionContextBuilder generates rich context from minimal input (just a topic)"
        )
        print(
            "  2. Supports selective inclusion of content types (KB, code, TODOs, tests)"
        )
        print("  3. Configurable limits for controlling result size")
        print(
            "  4. Multiple use cases: agent prep, code review, learning paths, documentation"
        )
        print("  5. Can combine multiple topics for comprehensive context")
        print("\n📚 Learn More:")
        print(
            "  - Documentation: logseq/pages/TTA KB Automation___SessionContextBuilder.md"
        )
        print(
            "  - Source Code: packages/tta-kb-automation/src/tta_kb_automation/tools/"
        )
        print(
            "  - Tests: packages/tta-kb-automation/tests/test_session_context_builder.py"
        )
        print("\n")

    except Exception as e:
        print(f"\n❌ Error running examples: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
