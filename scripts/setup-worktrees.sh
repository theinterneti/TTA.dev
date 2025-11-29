#!/bin/bash
# TTA.dev Worktree Setup Script
# Configures Git worktrees for multi-agent development

set -e  # Exit on error

MAIN_REPO="$HOME/repos/TTA.dev"
COPILOT_WORKTREE="$HOME/repos/TTA.dev-copilot"
CLINE_WORKTREE="$HOME/repos/TTA.dev-cline"
AUGMENT_WORKTREE="$HOME/repos/TTA.dev-augment"

echo "🚀 TTA.dev Worktree Setup"
echo "=========================="
echo ""

# Check if main repo exists
if [ ! -d "$MAIN_REPO" ]; then
    echo "❌ Main repository not found at $MAIN_REPO"
    exit 1
fi

cd "$MAIN_REPO"

echo "📋 Step 1: Verify worktrees exist"
echo "-----------------------------------"
git worktree list
echo ""

echo "⚙️  Step 2: Configure git settings (per-worktree)"
echo "--------------------------------------------------"

# Configure Copilot worktree
if [ -d "$COPILOT_WORKTREE" ]; then
    echo "Configuring Copilot worktree..."
    cd "$COPILOT_WORKTREE"
    git config --worktree user.email "copilot@tta.dev"
    git config --worktree user.name "GitHub Copilot Agent"
    echo "  ✅ Copilot: copilot@tta.dev"
else
    echo "  ⚠️  Copilot worktree not found at $COPILOT_WORKTREE"
fi

# Configure Cline worktree
if [ -d "$CLINE_WORKTREE" ]; then
    echo "Configuring Cline worktree..."
    cd "$CLINE_WORKTREE"
    git config --worktree user.email "cline@tta.dev"
    git config --worktree user.name "Cline Agent"
    echo "  ✅ Cline: cline@tta.dev"
else
    echo "  ⚠️  Cline worktree not found at $CLINE_WORKTREE"
fi

# Configure Augment worktree
if [ -d "$AUGMENT_WORKTREE" ]; then
    echo "Configuring Augment worktree..."
    cd "$AUGMENT_WORKTREE"
    git config --worktree user.email "augment@tta.dev"
    git config --worktree user.name "Augment Agent"
    echo "  ✅ Augment: augment@tta.dev"
else
    echo "  ⚠️  Augment worktree not found at $AUGMENT_WORKTREE"
fi

echo ""
echo "🔧 Step 3: Create coordination notices"
echo "---------------------------------------"

# Create coordination notice for Copilot
if [ -d "$COPILOT_WORKTREE" ]; then
    cat > "$COPILOT_WORKTREE/.COORDINATION_NOTICE" << 'EOF'
⚠️ COORDINATION NOTICE

This is the GitHub Copilot agent worktree.
Branch: agent/copilot

Before making changes:
1. Check if another agent is working on related code
2. Sync with main: git fetch origin && git rebase origin/main
3. Coordinate via GitHub Issues/PRs

Other Agent Worktrees:
- Cline: ~/repos/TTA.dev-cline
- Augment: ~/repos/TTA.dev-augment
- Main: ~/repos/TTA.dev
EOF
    echo "  ✅ Created notice for Copilot worktree"
fi

# Create coordination notice for Cline
if [ -d "$CLINE_WORKTREE" ]; then
    cat > "$CLINE_WORKTREE/.COORDINATION_NOTICE" << 'EOF'
⚠️ COORDINATION NOTICE

This is the Cline agent worktree.
Branch: agent/cline

Before making changes:
1. Check if another agent is working on related code
2. Sync with main: git fetch origin && git rebase origin/main
3. Coordinate via GitHub Issues/PRs

Other Agent Worktrees:
- Copilot: ~/repos/TTA.dev-copilot
- Augment: ~/repos/TTA.dev-augment
- Main: ~/repos/TTA.dev
EOF
    echo "  ✅ Created notice for Cline worktree"
fi

# Create coordination notice for Augment
if [ -d "$AUGMENT_WORKTREE" ]; then
    cat > "$AUGMENT_WORKTREE/.COORDINATION_NOTICE" << 'EOF'
⚠️ COORDINATION NOTICE

This is the Augment agent worktree.
Branch: agent/augment

Before making changes:
1. Check if another agent is working on related code
2. Sync with main: git fetch origin && git rebase origin/main
3. Coordinate via GitHub Issues/PRs

Other Agent Worktrees:
- Copilot: ~/repos/TTA.dev-copilot
- Cline: ~/repos/TTA.dev-cline
- Main: ~/repos/TTA.dev
EOF
    echo "  ✅ Created notice for Augment worktree"
fi

echo ""
echo "📂 Step 4: Create workspace files"
echo "----------------------------------"

# Create workspace for Copilot
if [ -d "$COPILOT_WORKTREE" ]; then
    cat > "$COPILOT_WORKTREE/workspace.code-workspace" << 'EOF'
{
	"folders": [
		{
			"path": "."
		}
	],
	"settings": {
		"python.defaultInterpreterPath": ".venv/bin/python",
		"github.copilot.enable": {
			"*": true
		}
	},
	"extensions": {
		"recommendations": [
			"github.copilot",
			"ms-python.python",
			"ms-python.vscode-pylance",
			"charliermarsh.ruff"
		]
	}
}
EOF
    echo "  ✅ Created workspace for Copilot"
fi

# Create workspace for Cline
if [ -d "$CLINE_WORKTREE" ]; then
    cat > "$CLINE_WORKTREE/workspace.code-workspace" << 'EOF'
{
	"folders": [
		{
			"path": "."
		}
	],
	"settings": {
		"python.defaultInterpreterPath": ".venv/bin/python",
		"cline.enabled": true
	},
	"extensions": {
		"recommendations": [
			"saoudrizwan.claude-dev",
			"ms-python.python",
			"ms-python.vscode-pylance",
			"charliermarsh.ruff"
		]
	}
}
EOF
    echo "  ✅ Created workspace for Cline"
fi

# Create workspace for Augment
if [ -d "$AUGMENT_WORKTREE" ]; then
    cat > "$AUGMENT_WORKTREE/workspace.code-workspace" << 'EOF'
{
	"folders": [
		{
			"path": "."
		}
	],
	"settings": {
		"python.defaultInterpreterPath": ".venv/bin/python"
	},
	"extensions": {
		"recommendations": [
			"ms-python.python",
			"ms-python.vscode-pylance",
			"charliermarsh.ruff"
		]
	}
}
EOF
    echo "  ✅ Created workspace for Augment"
fi

echo ""
echo "🧹 Step 5: Update .gitignore"
echo "-----------------------------"

cd "$MAIN_REPO"

# Add worktree-specific entries to .gitignore if not already present
GITIGNORE_ENTRIES="
# Worktree-specific files (added by setup-worktrees.sh)
workspace.code-workspace
.COORDINATION_NOTICE
.AGENT_ID

# Agent-specific temp directories
.copilot-temp/
.cline-temp/
.augment-temp/

# Agent configuration caches
.cline/sessions/
.augment/cache/
"

if ! grep -q "setup-worktrees.sh" .gitignore 2>/dev/null; then
    echo "$GITIGNORE_ENTRIES" >> .gitignore
    echo "  ✅ Updated .gitignore"
else
    echo "  ℹ️  .gitignore already configured"
fi

echo ""
echo "✅ Setup Complete!"
echo "=================="
echo ""
echo "Next steps:"
echo "1. Open each worktree in VS Code:"
echo "   code $COPILOT_WORKTREE/workspace.code-workspace"
echo "   code $CLINE_WORKTREE/workspace.code-workspace"
echo "   code $AUGMENT_WORKTREE/workspace.code-workspace"
echo ""
echo "2. Create virtual environments in each worktree:"
echo "   cd $COPILOT_WORKTREE && uv venv && uv sync"
echo "   cd $CLINE_WORKTREE && uv venv && uv sync"
echo "   cd $AUGMENT_WORKTREE && uv venv && uv sync"
echo ""
echo "3. Read the full guide:"
echo "   cat $MAIN_REPO/WORKTREE_SETUP_GUIDE.md"
echo ""
echo "4. Verify configuration:"
echo "   cd $MAIN_REPO && git worktree list"
echo ""
