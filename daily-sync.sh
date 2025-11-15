#!/bin/bash

# TTA.dev Daily Synchronization Script
# Performs synchronization checks and updates across all worktrees

set -e  # Exit on any error

echo "=== TTA.dev Daily Worktree Synchronization ==="
echo "Date: $(date)"
echo

# Verify all worktrees exist and are accessible
WORKTREES=("TTA.dev" "TTA.dev-cline" "TTA.dev-augment" "TTA.dev-copilot")
MAIN_REPO="$HOME/repos/TTA.dev"

for worktree_name in "${WORKTREES[@]}"; do
    worktree_path="$HOME/repos/$worktree_name"
    if [ ! -d "$worktree_path" ]; then
        echo "❌ Error: Worktree directory not found: $worktree_path"
        exit 1
    fi
done

echo "✅ All worktree directories verified"

# Check git worktree status
echo
echo "📋 Worktree Status:"
git worktree list
echo

# Check for uncommitted changes in each worktree
echo "🔍 Checking for uncommitted changes:"
for worktree_name in "${WORKTREES[@]}"; do
    worktree_path="$HOME/repos/$worktree_name"
    cd "$worktree_path"
    if [ -n "$(git status --porcelain)" ]; then
        echo "⚠️  $worktree_name: HAS uncommitted changes"
        git status --short | head -5
    else
        echo "✅ $worktree_name: Clean working directory"
    fi
done

echo
echo "🔄 Framework directory synchronization status:"
for worktree_name in "${WORKTREES[@]}"; do
    worktree_path="$HOME/repos/$worktree_name"
    if [ -d "$worktree_path/framework" ]; then
        framework_count=$(find "$worktree_path/framework" -type f 2>/dev/null | wc -l)
        echo "✅ $worktree_name: Has framework/ directory ($framework_count files)"
    else
        echo "❌ $worktree_name: Missing framework/ directory"
    fi
done

# Check branch status
echo
echo "🌿 Branch Status:"
for worktree_name in "${WORKTREES[@]}"; do
    worktree_path="$HOME/repos/$worktree_name"
    cd "$worktree_path"
    branch=$(git branch --show-current)
    behind_ahead=$(git rev-list --left-right --count HEAD...origin/$branch 2>/dev/null || echo "N/A")
    echo "📌 $worktree_name: $branch ($behind_ahead)"
done

echo
echo "📊 Summary:"
echo "- Worktrees registered: $(git worktree list | wc -l)"
echo "- Framework synchronization: Check above for details"
echo "- Uncommitted changes: Review warnings above"

echo
echo "🎯 Recommendations:"
if [ -n "$(cd "$MAIN_REPO" && git status --porcelain)" ]; then
    echo "- Main repo has uncommitted changes - consider committing or stashing"
fi

framework_missing=false
for worktree_name in "${WORKTREES[@]}"; do
    worktree_path="$HOME/repos/$worktree_name"
    if [ ! -d "$worktree_path/framework" ]; then
        echo "- $worktree_name missing framework/ directory - run sync-framework.sh"
        framework_missing=true
    fi
done

if [ "$framework_missing" = false ]; then
    echo "- All worktrees have framework/ directory ✅"
fi

echo
echo "📅 Next steps:"
echo "- Run './sync-framework.sh' if framework sync needed"
echo "- Commit changes in worktrees as appropriate"
echo "- Consider merging stable worktree branches to main"

echo
echo "✨ Daily sync check complete!"
