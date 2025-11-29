#!/bin/bash
# TTA.dev Worktree Status Checker
# Shows status of all worktrees at a glance

set -e

MAIN_REPO="$HOME/repos/TTA.dev"

echo "📊 TTA.dev Worktree Status"
echo "=========================="
echo ""

cd "$MAIN_REPO"

echo "🌳 Worktree List"
echo "----------------"
git worktree list
echo ""

echo "📋 Detailed Status"
echo "------------------"

for worktree_path in $(git worktree list --porcelain | grep "^worktree " | cut -d' ' -f2); do
    worktree_name=$(basename "$worktree_path")
    
    echo ""
    echo "=== $worktree_name ==="
    cd "$worktree_path"
    
    # Branch info
    branch=$(git branch --show-current)
    echo "📍 Branch: $branch"
    
    # Worktree config
    if [ -f .git ]; then
        email=$(git config --worktree user.email 2>/dev/null || echo "Not set")
        echo "📧 Agent: $email"
    fi
    
    # Status
    if git diff-index --quiet HEAD 2>/dev/null; then
        echo "✅ Status: Clean"
    else
        echo "⚠️  Status: Uncommitted changes"
        git status -s
    fi
    
    # Sync status
    git fetch origin --quiet 2>/dev/null || true
    LOCAL=$(git rev-parse @ 2>/dev/null || echo "")
    REMOTE=$(git rev-parse @{u} 2>/dev/null || echo "")
    BASE=$(git merge-base @ @{u} 2>/dev/null || echo "")
    
    if [ "$LOCAL" = "$REMOTE" ]; then
        echo "🔄 Sync: Up to date with origin"
    elif [ "$LOCAL" = "$BASE" ]; then
        echo "⬇️  Sync: Behind origin (need to pull)"
    elif [ "$REMOTE" = "$BASE" ]; then
        echo "⬆️  Sync: Ahead of origin (ready to push)"
    else
        echo "🔀 Sync: Diverged from origin"
    fi
    
    echo ""
done

echo "💡 Quick Actions"
echo "----------------"
echo "Sync all:     cd $MAIN_REPO && git pull && for dir in $HOME/repos/TTA.dev-*; do cd \"\$dir\" && git fetch && git rebase origin/\$(git branch --show-current); done"
echo "Open Copilot: code $HOME/repos/TTA.dev-copilot/workspace.code-workspace"
echo "Open Cline:   code $HOME/repos/TTA.dev-cline/workspace.code-workspace"
echo "Open Augment: code $HOME/repos/TTA.dev-augment/workspace.code-workspace"
echo ""
