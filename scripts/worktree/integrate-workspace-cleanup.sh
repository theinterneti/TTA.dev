#!/bin/bash
# Worktree Coordination: Workspace Cleanup Integration
# Run this script in each worktree to integrate the workspace cleanup changes

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo "🔄 TTA.dev Worktree Coordination: Workspace Cleanup"
echo "=================================================="
echo ""
echo "📍 Current worktree: $(pwd)"
echo "🌿 Current branch: $(git branch --show-current)"
echo ""

# Check if we're in a TTA.dev worktree
if [ ! -f "$REPO_ROOT/AGENTS.md" ]; then
    echo "❌ Error: Not in a TTA.dev repository"
    exit 1
fi

# Show workspace cleanup commit
echo "📝 Workspace Cleanup Commit:"
echo "----------------------------"
git log --oneline --grep="reorganize workspace" -1 2>/dev/null || echo "  (Not yet available in this worktree)"
echo ""

# Check for uncommitted changes
if [ -n "$(git status --porcelain)" ]; then
    echo "⚠️  Warning: You have uncommitted changes"
    echo ""
    echo "Options:"
    echo "  1. Commit or stash your changes first"
    echo "  2. Run: git stash"
    echo "  3. Then merge the workspace cleanup changes"
    echo ""
    read -p "Stash changes now? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        git stash push -m "Pre-workspace-cleanup stash $(date +%Y-%m-%d-%H%M%S)"
        echo "✅ Changes stashed"
    else
        echo "❌ Aborting. Commit or stash your changes first."
        exit 1
    fi
fi

# Fetch latest changes
echo "🔄 Fetching latest changes..."
git fetch origin

# Check if workspace-cleanup changes are available
if git rev-parse origin/experimental/workflow-agent-integrations >/dev/null 2>&1; then
    echo "✅ Workspace cleanup branch found"
    echo ""
    echo "🔀 Merge options:"
    echo "  1. Merge into current branch (recommended for active development)"
    echo "  2. Cherry-pick cleanup commit only"
    echo "  3. Rebase onto cleanup changes"
    echo "  4. Skip for now"
    echo ""
    read -p "Choose option (1-4): " -n 1 -r
    echo

    case $REPLY in
        1)
            echo "🔀 Merging workspace cleanup changes..."
            git merge origin/experimental/workflow-agent-integrations -m "merge: integrate workspace cleanup changes"
            echo "✅ Merge complete"
            ;;
        2)
            echo "🍒 Cherry-picking cleanup commit..."
            CLEANUP_SHA=$(git log origin/experimental/workflow-agent-integrations --grep="reorganize workspace" --format="%H" -1)
            if [ -n "$CLEANUP_SHA" ]; then
                git cherry-pick $CLEANUP_SHA
                echo "✅ Cherry-pick complete"
            else
                echo "❌ Could not find cleanup commit"
                exit 1
            fi
            ;;
        3)
            echo "🔄 Rebasing onto cleanup changes..."
            git rebase origin/experimental/workflow-agent-integrations
            echo "✅ Rebase complete"
            ;;
        4)
            echo "⏭️  Skipping integration for now"
            ;;
        *)
            echo "❌ Invalid option"
            exit 1
            ;;
    esac
else
    echo "⚠️  Workspace cleanup branch not yet pushed to remote"
    echo ""
    echo "Action needed:"
    echo "  1. Push from main worktree: git push origin experimental/workflow-agent-integrations"
    echo "  2. Then run this script again"
    exit 1
fi

echo ""
echo "📋 Post-Integration Checklist:"
echo "  ✓ Workspace cleanup changes integrated"
echo "  □ Review new organization: docs/WORKSPACE_ORGANIZATION.md"
echo "  □ Update any local scripts referencing old file locations"
echo "  □ Run: ./scripts/cleanup_workspace.sh (if needed)"
echo ""
echo "✅ Coordination complete!"
