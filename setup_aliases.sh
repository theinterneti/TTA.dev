#!/bin/bash
# 🎯 Lazy Dev Shell Aliases Setup Script
#
# Run this to add lazy dev aliases to your shell configuration
# Usage: ./setup_aliases.sh

set -e

echo "🚀 Setting up Lazy Dev aliases..."
echo ""

# Detect shell
SHELL_CONFIG=""
if [ -f "$HOME/.zshrc" ]; then
    SHELL_CONFIG="$HOME/.zshrc"
    SHELL_NAME="zsh"
elif [ -f "$HOME/.bashrc" ]; then
    SHELL_CONFIG="$HOME/.bashrc"
    SHELL_NAME="bash"
else
    echo "❌ Could not find ~/.bashrc or ~/.zshrc"
    echo "Please add aliases manually to your shell config"
    exit 1
fi

echo "📝 Detected shell: $SHELL_NAME"
echo "📁 Config file: $SHELL_CONFIG"
echo ""

# Check if aliases already exist
if grep -q "# Lazy Dev Aliases" "$SHELL_CONFIG" 2>/dev/null; then
    echo "⚠️  Lazy Dev aliases already configured in $SHELL_CONFIG"
    echo ""
    read -p "Overwrite? (y/N) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Cancelled."
        exit 0
    fi
    # Remove old aliases
    sed -i '/# Lazy Dev Aliases/,/# End Lazy Dev Aliases/d' "$SHELL_CONFIG"
fi

# Get repo root directory
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Add aliases
cat >> "$SHELL_CONFIG" << 'EOF'

# Lazy Dev Aliases - Auto-generated
export LAZY_DEV_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || echo $PWD)"

# Core commands
alias work='$LAZY_DEV_ROOT/scripts/lazy_dev.py work-on'
alias pr='$LAZY_DEV_ROOT/scripts/lazy_dev.py pr'
alias status='$LAZY_DEV_ROOT/scripts/lazy_dev.py status'
alias lazy='$LAZY_DEV_ROOT/scripts/lazy_dev.py'

# Advanced commands
alias ship='git add . && git commit -m "update" && $LAZY_DEV_ROOT/scripts/lazy_dev.py pr'
alias milestone='$LAZY_DEV_ROOT/scripts/issue_manager.py progress'
alias label='$LAZY_DEV_ROOT/scripts/issue_manager.py auto-label'

# Git shortcuts (lazy style)
alias st='git status --short'
alias co='git checkout'
alias pull='git pull origin $(git branch --show-current)'
alias push='git push origin $(git branch --show-current)'

# End Lazy Dev Aliases
EOF

echo "✅ Aliases added to $SHELL_CONFIG"
echo ""
echo "🎉 Setup complete! Available aliases:"
echo ""
echo "  Core Commands:"
echo "    work 'feature'   - Create new branch"
echo "    pr               - Create AI-powered PR"
echo "    status           - Check repo status"
echo "    lazy             - Interactive mode"
echo ""
echo "  Advanced:"
echo "    ship             - Commit all + create PR"
echo "    milestone        - Show milestone progress"
echo "    label <number>   - Auto-label issue"
echo ""
echo "  Git Shortcuts:"
echo "    st               - Git status (short)"
echo "    co <branch>      - Git checkout"
echo "    pull / push      - Pull/push current branch"
echo ""
echo "🔄 Reload your shell to activate:"
echo ""
echo "    source $SHELL_CONFIG"
echo ""
echo "Or start a new terminal session."
