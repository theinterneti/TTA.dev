#!/usr/bin/env python3
"""
Git Workflow Primitive - Apply TTA.dev patterns to git operations.

This script demonstrates how TTA.dev's workflow primitives (ConditionalPrimitive,
RouterPrimitive, FallbackPrimitive) can be applied to non-AI workflows like git
operations. It analyzes local git state and recommends appropriate actions.

**Key Patterns Demonstrated:**
1. ConditionalPrimitive: Binary decision-making (has changes or not)
2. RouterPrimitive: Multi-way routing based on git state
3. FallbackPrimitive: Try preferred actions with graceful degradation

**Use Cases:**
- Diagnose why VS Code commit button is disabled
- Determine appropriate git action based on current state
- Learn TTA.dev primitive patterns through a familiar domain (git)

**Usage:**
    python3 scripts/git_workflow_primitive.py

**Related Primitives:**
- GitHubAPIWrapper: For GitHub API operations (PR creation, merging)
- PRReviewWorkflow: For automated code review
- This script: For local git state analysis

**Author:** TTA.dev Team
**Date:** 2025-11-11
**License:** MIT
"""

import asyncio
import subprocess
from dataclasses import dataclass
from enum import Enum
from typing import Any


class GitAction(Enum):
    """Available git actions."""

    MERGE_TO_MAIN = "merge_to_main"
    MERGE_FROM_MAIN = "merge_from_main"
    REBASE_ON_MAIN = "rebase_on_main"
    CREATE_PR = "create_pr"
    PUSH_CURRENT = "push_current"
    NO_ACTION = "no_action"


@dataclass
class GitContext:
    """Context for git workflow decisions."""

    current_branch: str
    has_changes: bool
    has_staged: bool
    has_commits: bool
    is_ahead: bool
    is_behind: bool
    is_main: bool
    remote_exists: bool


def get_git_context() -> GitContext:
    """Gather git context information."""

    def run_git(cmd: list[str]) -> str:
        """Run git command and return output."""
        try:
            result = subprocess.run(
                ["git"] + cmd,
                capture_output=True,
                text=True,
                check=False,
            )
            return result.stdout.strip()
        except Exception as e:
            print(f"Git command failed: {e}")
            return ""

    current_branch = run_git(["branch", "--show-current"])
    status = run_git(["status", "--porcelain"])
    staged = run_git(["diff", "--cached", "--name-only"])

    # Check if ahead/behind remote
    ahead_behind = run_git(["rev-list", "--left-right", "--count", f"HEAD...origin/{current_branch}"])
    ahead, behind = (0, 0)
    if ahead_behind:
        parts = ahead_behind.split()
        if len(parts) == 2:
            ahead, behind = int(parts[0]), int(parts[1])

    return GitContext(
        current_branch=current_branch,
        has_changes=bool(status),
        has_staged=bool(staged),
        has_commits=ahead > 0,
        is_ahead=ahead > 0,
        is_behind=behind > 0,
        is_main=current_branch in ["main", "master"],
        remote_exists=bool(run_git(["ls-remote", "--heads", "origin", current_branch])),
    )


# ============================================================================
# Pattern 1: Conditional Branching (ConditionalPrimitive equivalent)
# ============================================================================


def conditional_git_workflow(ctx: GitContext) -> GitAction:
    """
    Simple conditional branching - if/else pattern.

    Equivalent to:
        ConditionalPrimitive(
            condition=lambda data, ctx: has_changes(data),
            then_primitive=commit_workflow,
            else_primitive=merge_workflow
        )
    """
    # Condition: Do we have uncommitted changes?
    if ctx.has_changes:
        # Then branch: Handle uncommitted changes
        if ctx.has_staged:
            return GitAction.NO_ACTION  # Let user commit via VS Code
        else:
            return GitAction.NO_ACTION  # Nothing staged to commit
    else:
        # Else branch: No changes, ready for merge operations
        if ctx.is_main:
            return GitAction.NO_ACTION  # Already on main
        else:
            return GitAction.MERGE_FROM_MAIN  # Update feature branch


# ============================================================================
# Pattern 2: Multi-Way Routing (RouterPrimitive equivalent)
# ============================================================================


def router_git_workflow(ctx: GitContext) -> GitAction:
    """
    Multi-way routing based on git state.

    Equivalent to:
        RouterPrimitive(
            routes={
                "no_changes": merge_workflow,
                "uncommitted": commit_workflow,
                "ahead_of_remote": push_workflow,
                "feature_branch": pr_workflow,
            },
            router_fn=select_route,
            default="no_action"
        )
    """
    # Route 1: Uncommitted changes
    if ctx.has_changes:
        if ctx.has_staged:
            return GitAction.NO_ACTION  # Use VS Code commit UI
        return GitAction.NO_ACTION  # Nothing to commit

    # Route 2: On main branch
    if ctx.is_main:
        if ctx.is_behind:
            return GitAction.NO_ACTION  # Pull from remote (git pull)
        return GitAction.NO_ACTION  # All caught up

    # Route 3: Feature branch ahead of remote
    if ctx.is_ahead:
        if ctx.remote_exists:
            return GitAction.PUSH_CURRENT  # Push to remote
        return GitAction.CREATE_PR  # Create PR

    # Route 4: Feature branch behind main
    if ctx.is_behind:
        return GitAction.MERGE_FROM_MAIN  # Update from main

    # Route 5: Feature branch ready to merge
    return GitAction.CREATE_PR  # Ready for PR


# ============================================================================
# Pattern 3: Fallback Chain (FallbackPrimitive equivalent)
# ============================================================================


def fallback_git_workflow(ctx: GitContext) -> tuple[GitAction, str]:
    """
    Try preferred actions, fall back to alternatives.

    Equivalent to:
        FallbackPrimitive(
            primary=git_push,
            fallbacks=[create_pr, merge_locally, manual_intervention]
        )
    """
    reasons = []

    # Try 1: Push current branch
    if not ctx.has_changes and ctx.is_ahead and ctx.remote_exists:
        return (GitAction.PUSH_CURRENT, "Clean state, commits ready to push")

    reasons.append("Cannot push: either has changes, not ahead, or no remote")

    # Try 2: Create PR
    if not ctx.has_changes and not ctx.is_main and ctx.remote_exists:
        return (GitAction.CREATE_PR, "Clean state, feature branch exists remotely")

    reasons.append("Cannot create PR: either has changes, on main, or no remote")

    # Try 3: Merge from main
    if not ctx.has_changes and not ctx.is_main:
        return (
            GitAction.MERGE_FROM_MAIN,
            "Clean state, feature branch can be updated from main",
        )

    reasons.append("Cannot merge: either has changes or already on main")

    # Fallback: Manual intervention
    return (GitAction.NO_ACTION, f"Manual intervention needed. Reasons: {'; '.join(reasons)}")


# ============================================================================
# Execution and Visualization
# ============================================================================


async def execute_git_action(action: GitAction, ctx: GitContext):
    """Execute the determined git action."""
    if action == GitAction.NO_ACTION:
        print("\n✅ No automatic action needed.")
        print("\n💡 Suggestions:")
        if ctx.has_changes:
            print("   - Use VS Code Source Control to commit changes")
            print("   - Or run: git add . && git commit -m 'your message'")
        elif ctx.is_main:
            print("   - You're on main branch")
            if ctx.is_behind:
                print("   - Run: git pull origin main")
        else:
            print("   - Everything is up to date")

    elif action == GitAction.PUSH_CURRENT:
        print(f"\n🚀 Pushing {ctx.current_branch} to remote...")
        subprocess.run(["git", "push", "origin", ctx.current_branch], check=True)
        print("✅ Pushed successfully")

    elif action == GitAction.MERGE_FROM_MAIN:
        print(f"\n🔄 Merging main into {ctx.current_branch}...")
        subprocess.run(["git", "fetch", "origin"], check=True)
        subprocess.run(["git", "merge", "origin/main"], check=True)
        print("✅ Merged successfully")

    elif action == GitAction.CREATE_PR:
        print("\n📋 Ready to create Pull Request")
        print(f"   Branch: {ctx.current_branch}")
        print("   Run: gh pr create --web")

    elif action == GitAction.MERGE_TO_MAIN:
        print("\n⚠️  Merge to main requires review")
        print("   Create a PR instead: gh pr create --web")


def visualize_decision(ctx: GitContext, action: GitAction, reason: str):
    """Visualize the decision tree like a primitive workflow."""
    print("\n" + "=" * 60)
    print("🌳 Git Workflow Decision Tree (TTA.dev Primitive Pattern)")
    print("=" * 60)

    print(f"\n📊 Context:")
    print(f"   Branch: {ctx.current_branch}")
    print(f"   Has changes: {ctx.has_changes}")
    print(f"   Has staged: {ctx.has_staged}")
    print(f"   Ahead of remote: {ctx.is_ahead}")
    print(f"   Behind remote: {ctx.is_behind}")
    print(f"   On main: {ctx.is_main}")

    print(f"\n🎯 Decision: {action.value}")
    print(f"   Reason: {reason}")

    print("\n🔀 Decision Path (Router Pattern):")
    if ctx.has_changes:
        print("   ├─ [HAS_CHANGES] → No Action (use VS Code UI)")
    elif ctx.is_main:
        print("   ├─ [IS_MAIN] → Update from remote")
    elif ctx.is_ahead:
        print("   ├─ [IS_AHEAD] → Push or Create PR")
    elif ctx.is_behind:
        print("   ├─ [IS_BEHIND] → Merge from main")
    else:
        print("   ├─ [READY] → Create PR")

    print("=" * 60)


async def main():
    """Main workflow demonstrating primitive patterns."""
    print("🎯 TTA.dev Git Workflow Primitive Demo\n")

    # Gather context (like WorkflowContext)
    ctx = get_git_context()

    print("Analyzing with different primitive patterns:\n")

    # Pattern 1: Conditional (if/else)
    print("1️⃣  Conditional Pattern (if/else):")
    action1 = conditional_git_workflow(ctx)
    print(f"   → {action1.value}")

    # Pattern 2: Router (multi-way)
    print("\n2️⃣  Router Pattern (multi-way):")
    action2 = router_git_workflow(ctx)
    print(f"   → {action2.value}")

    # Pattern 3: Fallback (try/catch chain)
    print("\n3️⃣  Fallback Pattern (try with alternatives):")
    action3, reason = fallback_git_workflow(ctx)
    print(f"   → {action3.value}")
    print(f"   → Reason: {reason}")

    # Visualize final decision
    visualize_decision(ctx, action3, reason)

    # Execute action
    await execute_git_action(action3, ctx)


if __name__ == "__main__":
    asyncio.run(main())
