#!/bin/bash
# Install git hooks for all agent worktrees

set -e

echo "🔧 Installing TTA.dev Multi-Agent Git Hooks"

# Worktrees to install hooks in
WORKTREES=(
    "/home/thein/repos/TTA.dev"
    "/home/thein/repos/TTA.dev-augment"
    "/home/thein/repos/TTA.dev-cline"
    "/home/thein/repos/TTA.dev-copilot"
)

# Hooks to install
HOOKS=(
    "pre-commit"
    "prepare-commit-msg"
    "post-commit"
)

# Source hooks directory
SOURCE_HOOKS_DIR="/home/thein/repos/TTA.dev/.git-hooks"

for worktree in "${WORKTREES[@]}"; do
    if [ ! -d "$worktree" ]; then
        echo "⚠️  Worktree not found: $worktree (skipping)"
        continue
    fi
    
    echo "📁 Installing hooks for: $worktree"
    
    # For worktrees, .git is a file pointing to the real git dir
    if [ -f "$worktree/.git" ]; then
        # Read the gitdir path from the .git file
        GIT_DIR=$(cat "$worktree/.git" | sed 's/gitdir: //')
        HOOKS_DIR="$GIT_DIR/hooks"
    else
        # Main repo has .git directory
        HOOKS_DIR="$worktree/.git/hooks"
    fi
    
    mkdir -p "$HOOKS_DIR"
    
    for hook in "${HOOKS[@]}"; do
        SOURCE_HOOK="$SOURCE_HOOKS_DIR/$hook"
        TARGET_HOOK="$HOOKS_DIR/$hook"
        
        if [ -f "$SOURCE_HOOK" ]; then
            # Copy hook
            cp "$SOURCE_HOOK" "$TARGET_HOOK"
            chmod +x "$TARGET_HOOK"
            echo "  ✅ Installed $hook"
        else
            echo "  ⚠️  Hook not found: $SOURCE_HOOK"
        fi
    done
    
    echo ""
done

echo "✅ Git hooks installation complete!"
echo ""
echo "📋 Next steps:"
echo "  1. Run: python scripts/agent_oversight.py status"
echo "  2. Make commits from any agent worktree"
echo "  3. Review commits from copilot worktree"
