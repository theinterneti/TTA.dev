#!/usr/bin/env bash
# TTA.dev Zsh Environment Setup Script
# This script installs and configures an AI-agent-friendly Zsh environment
# Based on: Agent-Centric Zsh Optimization Plan

set -euo pipefail

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Oh My Zsh is installed
if [ ! -d "$HOME/.oh-my-zsh" ]; then
    log_error "Oh My Zsh is not installed. Please install it first:"
    echo "  sh -c \"\$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)\""
    exit 1
fi

log_info "Starting Zsh environment setup..."

# Install zsh-autosuggestions
if [ ! -d "$HOME/.oh-my-zsh/custom/plugins/zsh-autosuggestions" ]; then
    log_info "Installing zsh-autosuggestions..."
    git clone https://github.com/zsh-users/zsh-autosuggestions \
        "$HOME/.oh-my-zsh/custom/plugins/zsh-autosuggestions"
    log_success "zsh-autosuggestions installed"
else
    log_info "zsh-autosuggestions already installed"
fi

# Install zsh-syntax-highlighting
if [ ! -d "$HOME/.oh-my-zsh/custom/plugins/zsh-syntax-highlighting" ]; then
    log_info "Installing zsh-syntax-highlighting..."
    git clone https://github.com/zsh-users/zsh-syntax-highlighting.git \
        "$HOME/.oh-my-zsh/custom/plugins/zsh-syntax-highlighting"
    log_success "zsh-syntax-highlighting installed"
else
    log_info "zsh-syntax-highlighting already installed"
fi

# Install Powerlevel10k
if [ ! -d "$HOME/.oh-my-zsh/custom/themes/powerlevel10k" ]; then
    log_info "Installing Powerlevel10k theme..."
    git clone --depth=1 https://github.com/romkatv/powerlevel10k.git \
        "$HOME/.oh-my-zsh/custom/themes/powerlevel10k"
    log_success "Powerlevel10k installed"
else
    log_info "Powerlevel10k already installed"
fi

# Check and install fzf
if ! command -v fzf &> /dev/null; then
    log_info "Installing fzf..."
    if command -v apt-get &> /dev/null; then
        sudo apt-get update && sudo apt-get install -y fzf
    elif command -v brew &> /dev/null; then
        brew install fzf
    else
        log_warn "Could not install fzf automatically. Please install manually:"
        echo "  https://github.com/junegunn/fzf#installation"
    fi
else
    log_info "fzf already installed"
fi

# Check and install zoxide
if ! command -v zoxide &> /dev/null; then
    log_info "Installing zoxide..."
    if command -v curl &> /dev/null; then
        curl -sS https://raw.githubusercontent.com/ajeetdsouza/zoxide/main/install.sh | bash
        log_success "zoxide installed"
    else
        log_warn "Could not install zoxide automatically. Please install manually:"
        echo "  https://github.com/ajeetdsouza/zoxide#installation"
    fi
else
    log_info "zoxide already installed"
fi

# Check GitHub CLI
if ! command -v gh &> /dev/null; then
    log_warn "GitHub CLI (gh) not found. Please install it:"
    echo "  https://cli.github.com/manual/installation"
else
    log_info "GitHub CLI (gh) already installed"
fi

# Backup existing .zshrc if it exists
if [ -f "$HOME/.zshrc" ]; then
    BACKUP_FILE="$HOME/.zshrc.backup.$(date +%Y%m%d_%H%M%S)"
    log_info "Backing up existing .zshrc to $BACKUP_FILE"
    cp "$HOME/.zshrc" "$BACKUP_FILE"
fi

log_success "Plugin installation complete!"
echo ""
log_info "Next steps:"
echo "  1. Review and apply the new .zshrc configuration"
echo "  2. Create your .zsh_local file for secrets and personal settings"
echo "  3. Run 'p10k configure' to set up Powerlevel10k"
echo "  4. Restart your terminal or run: source ~/.zshrc"
