"""
Example: Multi-Agent Git Collaboration with Enforced Best Practices

This example demonstrates using GitCollaborationPrimitive to enforce
high-frequency integration and exemplary git hygiene for AI agents.

Based on Martin Fowler's "Patterns for Managing Source Code Branches"
and State of DevOps Report findings.
"""

import asyncio
from pathlib import Path

from tta_dev_primitives.collaboration import (
    AgentIdentity,
    CommitFrequencyPolicy,
    GitCollaborationPrimitive,
    IntegrationFrequency,
)
from tta_dev_primitives.core import WorkflowContext


async def example_basic_agent_workflow():
    """Example: Basic agent workflow with git hygiene."""

    # Configure agent identity
    copilot_agent = AgentIdentity(
        name="GitHub Copilot",
        email="copilot@tta.dev",
        branch_prefix="agent/copilot",
        worktree_path=Path.home() / "repos" / "TTA.dev-copilot",
    )

    # Create collaboration primitive with daily integration requirement
    git_collab = GitCollaborationPrimitive(
        agent_identity=copilot_agent,
        integration_frequency=IntegrationFrequency.DAILY,
        repository_path=Path.home() / "repos" / "TTA.dev",
        enforce_hygiene=True,
    )

    # Create workflow context
    context = WorkflowContext(workflow_id="copilot-session-001")

    # 1. Check branch health before starting work
    print("📊 Checking branch health...")
    health = await git_collab.execute({"action": "status"}, context)

    if health["healthy"]:
        print("✅ Branch is healthy!")
    else:
        print("⚠️  Health issues detected:")
        for issue in health["health_issues"]:
            print(f"   • {issue}")
        print(f"\n💡 Recommendation: {health['recommendation']}")

    # 2. Sync with main before starting work
    print("\n🔄 Syncing with main branch...")
    sync_result = await git_collab.execute({"action": "sync"}, context)

    if sync_result["success"]:
        if sync_result["synced"]:
            print("✅ Already up to date with main")
        else:
            print(f"✅ Synced! Pulled {sync_result['commits_behind']} commits")

    # 3. Make changes and commit frequently (example: after adding new feature)
    print("\n💻 Working on new feature...")
    print("   (Agent implements CachePrimitive with tests)")

    # Commit with conventional commits format
    print("\n📝 Committing work...")
    try:
        commit_result = await git_collab.execute(
            {
                "action": "commit",
                "message": "feat: Add CachePrimitive with LRU and TTL support",
                "files": [
                    "src/tta_dev_primitives/performance/cache.py",
                    "tests/test_cache.py",
                ],
            },
            context,
        )

        if commit_result["success"]:
            print("✅ Commit successful!")
            print(f"   Files committed: {commit_result['files_committed']}")
    except ValueError as e:
        print(f"❌ Commit rejected: {e}")
        print("   Fix hygiene issues and try again")

    # 4. Enforce commit frequency (checks time since last commit)
    print("\n⏰ Checking commit frequency...")
    try:
        freq_check = await git_collab.execute({"action": "enforce_frequency"}, context)
        if freq_check["healthy"]:
            print("✅ Commit frequency is excellent!")
    except ValueError as e:
        print(f"⚠️  {e}")

    # 5. Create integration PR when feature is complete
    print("\n🎯 Creating integration PR...")
    pr_result = await git_collab.execute(
        {
            "action": "integrate",
            "title": "feat: Add CachePrimitive for performance optimization",
            "body": """
## Overview
Implements CachePrimitive with LRU eviction and TTL support.

## Changes
- Added CachePrimitive class with async interface
- Implemented LRU eviction policy
- Added TTL (time-to-live) support
- Comprehensive test coverage (100%)

## Testing
- Unit tests pass
- Integration tests pass
- Performance benchmarks included

## Performance Impact
- 40-60% cost reduction in LLM workflows
- 100x latency reduction on cache hits
            """,
        },
        context,
    )

    if pr_result["success"]:
        print("✅ Ready to create PR!")
        print(f"   Branch: {pr_result['branch']}")
        print(f"   Target: {pr_result['target']}")
        print(f"\n💡 {pr_result['recommendation']}")


async def example_strict_hourly_integration():
    """Example: Strict hourly integration for continuous delivery."""

    agent = AgentIdentity(
        name="Cline",
        email="cline@tta.dev",
        branch_prefix="agent/cline",
    )

    # Configure for hourly integration (elite team practice)
    git_collab = GitCollaborationPrimitive(
        agent_identity=agent,
        integration_frequency=IntegrationFrequency.HOURLY,
        commit_policy=CommitFrequencyPolicy(
            max_uncommitted_changes=25,  # Smaller batches
            max_uncommitted_time_minutes=30,  # More frequent commits
            require_tests_before_commit=True,
        ),
        repository_path=Path.home() / "repos" / "TTA.dev",
        enforce_hygiene=True,
    )

    context = WorkflowContext(workflow_id="cline-session-001")

    print("🚀 Running strict hourly integration workflow...\n")

    # Simulate work over an hour
    for iteration in range(1, 4):
        print(f"⏰ Iteration {iteration} (every 20 minutes)")

        # Check health
        health = await git_collab.execute({"action": "status"}, context)
        print(f"   Health: {'✅ Healthy' if health['healthy'] else '⚠️  Issues'}")

        # Make small commit
        try:
            await git_collab.execute(
                {
                    "action": "commit",
                    "message": f"feat: Incremental improvement iteration {iteration}",
                    "files": [f"src/module_{iteration}.py"],
                },
                context,
            )
            print(f"   ✅ Committed iteration {iteration}")
        except ValueError as e:
            print(f"   ❌ {e}")

        print()


async def example_relaxed_daily_integration():
    """Example: Daily integration for teams learning continuous delivery."""

    agent = AgentIdentity(
        name="Augment",
        email="augment@tta.dev",
        branch_prefix="agent/augment",
    )

    # Daily integration - good starting point
    git_collab = GitCollaborationPrimitive(
        agent_identity=agent,
        integration_frequency=IntegrationFrequency.DAILY,
        commit_policy=CommitFrequencyPolicy(
            max_uncommitted_changes=50,
            max_uncommitted_time_minutes=120,  # 2 hours
            require_tests_before_commit=True,
        ),
        repository_path=Path.home() / "repos" / "TTA.dev",
        enforce_hygiene=False,  # Warning mode, not blocking
    )

    context = WorkflowContext(workflow_id="augment-session-001")

    print("📅 Running daily integration workflow...\n")

    # Morning: Sync with main
    print("🌅 Morning: Sync with main")
    sync = await git_collab.execute({"action": "sync"}, context)
    print(f"   Synced: {sync['synced']}")

    # Work during the day...
    print("\n💼 Working during the day...")
    print("   (Making multiple commits...)")

    # Evening: Check health and integrate
    print("\n🌆 Evening: Health check and integration")
    health = await git_collab.execute({"action": "status"}, context)

    if not health["healthy"]:
        print("⚠️  Health issues (warning mode):")
        for issue in health["health_issues"]:
            print(f"   • {issue}")
        print(f"\n💡 {health['recommendation']}")

    # Create PR if ready
    print("\n📤 Creating integration PR...")
    pr = await git_collab.execute(
        {
            "action": "integrate",
            "title": "feat: Daily integration - observability improvements",
            "body": "Daily integration following best practices",
        },
        context,
    )
    print(f"   {'✅ Ready for PR' if pr['success'] else '❌ Not ready'}")


async def example_workflow_with_all_features():
    """Example: Complete workflow showing all features."""

    agent = AgentIdentity(
        name="GitHub Copilot",
        email="copilot@tta.dev",
        branch_prefix="agent/copilot",
        worktree_path=Path.home() / "repos" / "TTA.dev-copilot",
    )

    git_collab = GitCollaborationPrimitive(
        agent_identity=agent,
        integration_frequency=IntegrationFrequency.DAILY,
        repository_path=Path.home() / "repos" / "TTA.dev",
        enforce_hygiene=True,
    )

    context = WorkflowContext(workflow_id="full-demo")

    print("🎓 COMPLETE GIT COLLABORATION WORKFLOW\n")
    print("=" * 60)

    # Step 1: Health check
    print("\n1️⃣  HEALTH CHECK")
    print("-" * 60)
    health = await git_collab.execute({"action": "status"}, context)
    print(f"Status: {'✅ Healthy' if health['healthy'] else '⚠️  Needs attention'}")
    print(f"Uncommitted files: {health['uncommitted_files']}")
    print(f"Time since last commit: {health['time_since_commit_hours']:.1f}h")
    print(f"Commits behind main: {health['commits_behind_main']}")

    # Step 2: Sync
    print("\n2️⃣  SYNC WITH MAIN")
    print("-" * 60)
    sync = await git_collab.execute({"action": "sync"}, context)
    if sync["success"]:
        print(f"Synced: {sync['synced']}")
        print(f"Behind: {sync['commits_behind']}, Ahead: {sync['commits_ahead']}")

    # Step 3: Commit work
    print("\n3️⃣  COMMIT CHANGES")
    print("-" * 60)
    try:
        commit = await git_collab.execute(
            {
                "action": "commit",
                "message": "feat: Implement GitCollaborationPrimitive with best practices",
                "files": ["src/collaboration/git_integration.py"],
            },
            context,
        )
        print(f"✅ Committed {commit.get('files_committed', 0)} files")
    except ValueError as e:
        print(f"❌ Commit validation failed: {e}")

    # Step 4: Frequency check
    print("\n4️⃣  FREQUENCY ENFORCEMENT")
    print("-" * 60)
    try:
        await git_collab.execute({"action": "enforce_frequency"}, context)
        print("✅ Frequency policy satisfied")
    except ValueError as e:
        print(f"⚠️  Frequency warning: {e}")

    # Step 5: Integration
    print("\n5️⃣  CREATE INTEGRATION PR")
    print("-" * 60)
    pr = await git_collab.execute(
        {
            "action": "integrate",
            "title": "feat: Add GitCollaborationPrimitive",
            "body": "Implements best practices from Martin Fowler's research",
        },
        context,
    )
    if pr["success"]:
        print(f"✅ Ready to integrate: {pr['branch']} -> {pr['target']}")
        print(f"💡 {pr['recommendation']}")

    print("\n" + "=" * 60)
    print("✨ Workflow complete!\n")


async def main():
    """Run all examples."""
    print("🎯 GIT COLLABORATION PRIMITIVE EXAMPLES\n")
    print("=" * 70)

    examples = [
        ("Basic Agent Workflow", example_basic_agent_workflow),
        ("Strict Hourly Integration", example_strict_hourly_integration),
        ("Relaxed Daily Integration", example_relaxed_daily_integration),
        ("Complete Feature Demo", example_workflow_with_all_features),
    ]

    for i, (name, example_func) in enumerate(examples, 1):
        print(f"\n\n{'=' * 70}")
        print(f"EXAMPLE {i}: {name}")
        print("=" * 70)

        try:
            await example_func()
        except Exception as e:
            print(f"\n❌ Example error (expected in demo): {e}")

        if i < len(examples):
            print("\n⏸️  Press Enter to continue to next example...")
            # input()  # Uncomment for interactive mode


if __name__ == "__main__":
    asyncio.run(main())
