#!/bin/bash
# Setup Git Hooks for TTA.dev
#
# This script installs git hooks to enforce TTA.dev best practices.
# Run during onboarding or project setup.

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
HOOKS_DIR="$PROJECT_ROOT/.git/hooks"

echo "🔧 Setting up TTA.dev git hooks..."
echo ""

# Check if in git repository
if [ ! -d "$PROJECT_ROOT/.git" ]; then
    echo "❌ Error: Not in a git repository"
    echo "   Current directory: $PROJECT_ROOT"
    exit 1
fi

# Make pre-commit hook executable
if [ -f "$HOOKS_DIR/pre-commit" ]; then
    chmod +x "$HOOKS_DIR/pre-commit"
    echo "✅ Pre-commit hook installed and made executable"
else
    echo "⚠️  Warning: pre-commit hook not found at $HOOKS_DIR/pre-commit"
    echo "   Expected file to exist but it doesn't"
fi

# Verify hooks are set up
echo ""
echo "📋 Current git hooks:"
ls -lh "$HOOKS_DIR" | grep -v ".sample" | grep -v "^total" | grep -v "^d" || echo "   (none installed)"

echo ""
echo "✅ Git hooks setup complete!"
echo ""
echo "💡 The pre-commit hook will now:"
echo "   - Validate TTA.dev primitive usage before commits"
echo "   - Check for anti-patterns (asyncio.gather, etc.)"
echo "   - Prevent commits with direct asyncio orchestration"
echo ""
echo "🚫 To bypass the hook (not recommended):"
echo "   git commit --no-verify"
echo ""
echo "📚 References:"
echo "   - Checklist: .github/AGENT_CHECKLIST.md"
echo "   - Templates: .vscode/tta-prompts.md"
echo "   - Validator: scripts/validate-primitive-usage.py"
