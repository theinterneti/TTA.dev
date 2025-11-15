#!/bin/bash

# TTA.dev Framework Synchronization Script
# Synchronizes framework/ directory across all worktrees using main repo as source of truth

set -e  # Exit on any error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MAIN_REPO="$HOME/repos/TTA.dev"

# All worktrees that should have the framework directory
WORKTREES=(
    "$MAIN_REPO"
    "$HOME/repos/TTA.dev-cline"
    "$HOME/repos/TTA.dev-augment"
    "$HOME/repos/TTA.dev-copilot"
)

echo "=== TTA.dev Framework Synchronization ==="
echo "Source of truth: $MAIN_REPO/framework/"
echo "Target worktrees: ${WORKTREES[*]//$MAIN_REPO/TTA.dev}"
echo

# Verify main repo exists and has framework directory
if [ ! -d "$MAIN_REPO" ]; then
    echo "❌ Error: Main repo directory not found: $MAIN_REPO"
    exit 1
fi

if [ ! -d "$MAIN_REPO/framework" ]; then
    echo "❌ Error: Framework directory not found in main repo"
    echo "Run this script from a worktree that has the framework content first."
    exit 1
fi

# Verify all worktree directories exist
for worktree in "${WORKTREES[@]}"; do
    if [ ! -d "$worktree" ]; then
        echo "❌ Error: Worktree directory not found: $worktree"
        exit 1
    fi
done

echo "✅ All worktree directories verified"

# Check for uncommitted changes that might conflict
echo
echo "🔍 Checking for uncommitted framework changes..."
framework_conflicts=false
for worktree in "${WORKTREES[@]}"; do
    cd "$worktree"
    if [ -d "framework" ] && [ -n "$(git status --porcelain framework/)" ]; then
        worktree_name="${worktree##*/}"
        echo "⚠️  $worktree_name: Has uncommitted changes in framework/"
        git status --short framework/ | head -3
        framework_conflicts=true
    fi
done

if [ "$framework_conflicts" = true ]; then
    echo
    echo "⚠️  Warning: Framework conflicts detected in worktrees"
    echo "Uncommitted changes in framework/ will be overwritten."
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Synchronization cancelled."
        exit 0
    fi
fi

# Perform synchronization from main to all worktrees
echo "🔄 Synchronizing framework/ directory to all worktrees..."
main_framework_files=$(find "$MAIN_REPO/framework" -type f | wc -l)
echo "Main repo framework files: $main_framework_files"

for worktree in "${WORKTREES[@]}"; do
    if [ "$worktree" = "$MAIN_REPO" ]; then
        worktree_name="TTA.dev (main)"
    else
        worktree_name="${worktree##*/TTA.dev-}"  # Remove prefix for cleaner name
        worktree_name="TTA.dev-${worktree_name}"
    fi

    echo "  → Syncing to $worktree_name..."
    rsync -a --delete --exclude='.git' \
        "$MAIN_REPO/framework/" "$worktree/framework/"

    sync_result=$?
    if [ $sync_result -eq 0 ]; then
        worktree_framework_files=$(find "$worktree/framework" -type f 2>/dev/null | wc -l)
        echo "    ✅ Complete ($worktree_framework_files files)"
    else
        echo "    ❌ Failed (rsync error $sync_result)"
        exit 1
    fi
done

echo
echo "✅ Framework synchronization complete!"
echo

# Show final status
echo "📊 Final framework status:"
for worktree in "${WORKTREES[@]}"; do
    if [ "$worktree" = "$MAIN_REPO" ]; then
        worktree_name="TTA.dev (main)"
    else
        worktree_name="${worktree##*/}"
    fi

    if [ -d "$worktree/framework" ]; then
        framework_count=$(find "$worktree/framework" -type f 2>/dev/null | wc -l)
        echo "  ✅ $worktree_name: $framework_count files"
    else
        echo "  ❌ $worktree_name: Missing framework directory"
    fi
done

echo
echo "🎉 All worktrees now have synchronized framework content!"
echo
echo "📝 Next steps:"
echo "1. Commit any framework changes in worktrees as needed"
echo "2. Consider merging stable worktree branches to main when ready"
echo
echo "💡 Remember: Framework/ should be identical across all worktrees for shared resources"
