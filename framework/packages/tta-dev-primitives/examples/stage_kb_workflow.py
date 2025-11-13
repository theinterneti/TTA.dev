"""Stage + Knowledge Base Integration Example.

This example demonstrates how the KB integration enhances stage management
by providing contextual guidance during transitions.

Features demonstrated:
1. KB queries for best practices, common mistakes, and examples
2. KB-aware stage validation with pre-defined criteria
3. Complete transition workflow with KB guidance
4. Graceful degradation when KB is unavailable

Author: TTA.dev Team
Date: 2025-10-31
"""

import asyncio
from pathlib import Path

from tta_dev_primitives import WorkflowContext
from tta_dev_primitives.knowledge import KnowledgeBasePrimitive
from tta_dev_primitives.lifecycle import (
    STAGE_CRITERIA_MAP,
    Stage,
    StageManager,
    StageRequest,
)


async def demo_basic_kb_queries() -> None:
    """Demonstrate basic KnowledgeBasePrimitive queries."""
    print("=" * 70)
    print("DEMO 1: Basic Knowledge Base Queries")
    print("=" * 70)

    # Note: LogSeq MCP is only available in VS Code with MCP configured
    # This example shows graceful degradation when unavailable
    kb = KnowledgeBasePrimitive(logseq_available=False)

    context = WorkflowContext(correlation_id="demo-kb-001")

    # Query 1: Best practices for testing
    print("\n📚 Query: Testing Best Practices")
    result = await kb.query_best_practices(
        topic="testing",
        stage="testing",
        max_results=3,
        context=context,
    )

    print(f"  Source: {result.source}")
    print(f"  Found: {result.total_found} pages")
    print(f"  Query time: {result.query_time_ms:.2f}ms")

    if result.pages:
        for page in result.pages:
            print(f"  📄 {page.title}")
            print(f"     Tags: {', '.join(page.tags)}")
    else:
        print("  ℹ️  No pages found (LogSeq MCP not available)")

    # Query 2: Common mistakes
    print("\n⚠️  Query: Common Testing Mistakes")
    result = await kb.query_common_mistakes(
        topic="testing",
        stage="testing",
        context=context,
    )

    print(f"  Found: {result.total_found} pages")
    if result.pages:
        for page in result.pages:
            print(f"  ⚠️  {page.title}")

    # Query 3: Examples
    print("\n💡 Query: Stage Transition Examples")
    result = await kb.query_examples(
        topic="stage-transitions",
        context=context,
    )

    print(f"  Found: {result.total_found} pages")
    if result.pages:
        for page in result.pages:
            print(f"  💡 {page.title}")

    # Query 4: Search by tags
    print("\n🏷️  Query: Pages tagged with #testing #best-practices")
    result = await kb.search_by_tags(
        tags=["testing", "best-practices"],
        max_results=5,
        context=context,
    )

    print(f"  Found: {result.total_found} pages")
    if result.pages:
        for page in result.pages:
            print(f"  📄 {page.title}")

    print("\n✅ KB queries completed successfully")
    print("   Note: When LogSeq MCP is available, results will include actual pages")


async def demo_kb_aware_validation() -> None:
    """Demonstrate KB-enhanced stage validation."""
    print("\n" + "=" * 70)
    print("DEMO 2: KB-Enhanced Stage Validation")
    print("=" * 70)

    # Create KB primitive
    kb = KnowledgeBasePrimitive(logseq_available=False)

    # Create stage manager with pre-defined criteria
    manager = StageManager(stage_criteria_map=STAGE_CRITERIA_MAP)

    # Scenario: Check readiness to transition TESTING → STAGING
    print("\n🔍 Checking readiness: TESTING → STAGING (with KB integration)")

    context = WorkflowContext(correlation_id="demo-validation-001")

    request = StageRequest(
        project_path=Path(__file__).parent.parent.parent,  # tta-dev-primitives root
        current_stage=Stage.TESTING,
        target_stage=Stage.STAGING,
    )

    # Check readiness WITH KB integration
    readiness = await manager.check_readiness(
        current_stage=request.current_stage,
        target_stage=request.target_stage,
        project_path=request.project_path,
        context=context,
        kb=kb,  # Pass KB primitive for contextual guidance
    )

    print(f"\n  Ready: {readiness.ready}")
    print(f"  Stage: {request.current_stage.value} → {request.target_stage.value}")

    if readiness.blockers:
        print(f"\n  Blockers: {len(readiness.blockers)}")
        for blocker in readiness.blockers[:3]:  # Show first 3
            print(f"    • {blocker.message}")

    # Show KB recommendations if available
    if readiness.kb_recommendations:
        print(f"\n  📚 KB Recommendations: {len(readiness.kb_recommendations)}")
        for rec in readiness.kb_recommendations:
            rec_type = rec.get("type", "general")
            title = rec.get("title", "Unknown")
            print(f"    • [{rec_type.upper()}] {title}")
    else:
        print("\n  ℹ️  No KB recommendations (LogSeq MCP not available)")

    # Query KB for best practices for target stage
    print("\n📚 Querying KB for STAGING best practices...")
    kb_result = await kb.query_best_practices(
        topic="staging",
        stage="staging",
        max_results=3,
        context=context,
    )

    print(f"  Found {kb_result.total_found} best practice pages")

    if kb_result.pages:
        print("\n  Recommended reading:")
        for page in kb_result.pages:
            print(f"    📄 {page.title}")
            if page.content:
                # Show first 100 chars of content
                preview = page.content[:100].replace("\n", " ")
                print(f"       {preview}...")
    else:
        print("  ℹ️  Enable LogSeq MCP in VS Code to see recommendations")

    # Query for common mistakes
    print("\n⚠️  Querying KB for common STAGING mistakes...")
    mistakes = await kb.query_common_mistakes(
        topic="staging",
        stage="staging",
        context=context,
    )

    if mistakes.pages:
        print("  Common mistakes to avoid:")
        for page in mistakes.pages:
            print(f"    ⚠️  {page.title}")

    print("\n✅ Validation with KB recommendations complete")


async def main() -> None:
    """Run all demos."""
    print("\n" + "=" * 70)
    print("🎯 TTA.dev Stage-Based Workflow with Knowledge Base")
    print("=" * 70)

    # Demo 1: Basic KB queries
    await demo_basic_kb_queries()

    # Demo 2: KB-enhanced validation with pre-defined criteria
    await demo_kb_aware_validation()

    print("\n" + "=" * 70)
    print("✅ All demos complete!")
    print("=" * 70)

    print("\n💡 Key Takeaways:")
    print("  1. KnowledgeBasePrimitive provides contextual guidance")
    print("  2. KB queries work with graceful degradation")
    print("  3. StageManager uses STAGE_CRITERIA_MAP for validation")
    print("  4. Query by topic, stage, or tags for relevant content")

    print("\n🔧 To enable full KB functionality:")
    print("  1. Configure LogSeq MCP in VS Code")
    print("  2. Set logseq_available=True in KnowledgeBasePrimitive")
    print("  3. Create KB pages following TTA.dev taxonomy")

    print("\n📚 See documentation:")
    print("  • docs/architecture/KNOWLEDGE_BASE_INTEGRATION.md")
    print("  • logseq/pages/TTA.dev/Best Practices/")
    print("  • logseq/pages/TTA.dev/Stage Guides/")


if __name__ == "__main__":
    asyncio.run(main())
