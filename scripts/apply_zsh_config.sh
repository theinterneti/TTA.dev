#!/usr/bin/env bash
# Apply TTA.dev Zsh Configuration
# This script applies the agent-managed Zsh configuration and creates user settings

set -euo pipefail

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "============================================================================"
echo "TTA.dev Zsh Configuration Installer"
echo "============================================================================"
echo ""

# Check if Oh My Zsh is installed
if [ ! -d "$HOME/.oh-my-zsh" ]; then
    log_error "Oh My Zsh not installed. Run setup script first:"
    echo "  $SCRIPT_DIR/setup_zsh_environment.sh"
    exit 1
fi

# Check if plugins are installed
if [ ! -d "$HOME/.oh-my-zsh/custom/plugins/zsh-autosuggestions" ]; then
    log_error "Plugins not installed. Run setup script first:"
    echo "  $SCRIPT_DIR/setup_zsh_environment.sh"
    exit 1
fi

log_info "All prerequisites met!"
echo ""

# Backup existing .zshrc
if [ -f "$HOME/.zshrc" ]; then
    BACKUP_FILE="$HOME/.zshrc.backup.$(date +%Y%m%d_%H%M%S)"
    log_info "Backing up existing .zshrc to: $BACKUP_FILE"
    cp "$HOME/.zshrc" "$BACKUP_FILE"
fi

# Apply new .zshrc from template
log_info "Installing agent-managed .zshrc..."
cp "$SCRIPT_DIR/zshrc.template" "$HOME/.zshrc"
log_success ".zshrc installed"

# Create .zsh_local if it doesn't exist
if [ ! -f "$HOME/.zsh_local" ]; then
    log_info "Creating user-managed .zsh_local..."
    cp "$SCRIPT_DIR/zsh_local.template" "$HOME/.zsh_local"
    log_success ".zsh_local created"
    
    log_warn "IMPORTANT: Add secrets to ~/.zsh_local (API keys, tokens, etc.)"
else
    log_info ".zsh_local already exists (not overwriting)"
fi

# Check if .zsh_local is in .gitignore
if [ -f "$HOME/.gitignore" ]; then
    if ! grep -q "^\.zsh_local$" "$HOME/.gitignore"; then
        log_warn "Adding .zsh_local to ~/.gitignore"
        echo ".zsh_local" >> "$HOME/.gitignore"
    fi
else
    log_warn "Creating ~/.gitignore with .zsh_local"
    echo ".zsh_local" > "$HOME/.gitignore"
fi

# Check if Powerlevel10k needs configuration
if [ ! -f "$HOME/.p10k.zsh" ]; then
    log_warn "Powerlevel10k not configured yet"
    P10K_NEEDED=true
else
    P10K_NEEDED=false
fi

echo ""
log_success "Installation complete!"
echo ""

echo "============================================================================"
echo "Next Steps:"
echo "============================================================================"
echo ""

if [ "$P10K_NEEDED" = true ]; then
    echo "1. Configure Powerlevel10k:"
    echo "   ${GREEN}p10k configure${NC}"
    echo ""
fi

echo "2. Add your secrets to ~/.zsh_local:"
echo "   ${BLUE}vim ~/.zsh_local${NC}"
echo "   Example:"
echo "   ${YELLOW}export OPENAI_API_KEY=\"sk-...\"${NC}"
echo "   ${YELLOW}export GITHUB_TOKEN=\"ghp_...\"${NC}"
echo ""

echo "3. Reload your shell:"
echo "   ${GREEN}source ~/.zshrc${NC}"
echo "   Or restart your terminal"
echo ""

echo "4. Test AI features (requires GitHub Copilot CLI):"
echo "   ${GREEN}gh extension install github/gh-copilot${NC}"
echo "   ${GREEN}explain${NC}  (after running a command)"
echo "   ${GREEN}suggest \"search for large files\"${NC}"
echo ""

echo "5. Test performance:"
echo "   ${GREEN}profile-zsh${NC}"
echo "   Target: <200ms"
echo ""

echo "============================================================================"
echo "Documentation:"
echo "============================================================================"
echo ""
echo "Full Guide:       docs/guides/zsh-setup-guide.md"
echo "Quick Reference:  docs/guides/zsh-quick-reference.md"
echo ""
echo "Security Note: ~/.zsh_local contains secrets - never commit it!"
echo "============================================================================"
