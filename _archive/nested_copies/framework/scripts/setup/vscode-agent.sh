#!/bin/bash
# scripts/setup/vscode-agent.sh
# Setup for VS Code Extension agent context

set -euo pipefail

log_info() { echo -e "\033[0;34mℹ️  $1\033[0m"; }
log_success() { echo -e "\033[0;32m✅ $1\033[0m"; }
log_warning() { echo -e "\033[1;33m⚠️  $1\033[0m"; }

log_info "Setting up VS Code Agent workspace..."

# Check VS Code availability
if ! command -v code >/dev/null 2>&1; then
    log_warning "VS Code not found in PATH, some features may not work"
fi

# Install recommended extensions
if command -v code >/dev/null 2>&1; then
    log_info "Installing recommended VS Code extensions..."

    extensions=(
        "github.copilot"
        "github.copilot-chat"
        "ms-python.python"
        "ms-python.pylance"
        "charliermarsh.ruff"
        "ms-vscode.vscode-json"
        "redhat.vscode-yaml"
    )

    for ext in "${extensions[@]}"; do
        if ! code --list-extensions | grep -q "$ext"; then
            log_info "Installing $ext..."
            code --install-extension "$ext" --force
        else
            log_success "$ext already installed"
        fi
    done
fi

# Setup MCP server configuration
log_info "Configuring MCP servers..."

# Ensure MCP configuration directory exists
mkdir -p ~/.config/mcp

# Create or update MCP settings
cat > ~/.config/mcp/mcp_settings.json << 'EOF'
{
  "mcpServers": {
    "context7": {
      "command": "npx",
      "args": ["-y", "@context7/mcp-server"]
    },
    "grafana": {
      "command": "docker",
      "args": [
        "run", "--rm", "-i",
        "--network=host",
        "mcp-grafana"
      ]
    }
  }
}
EOF

log_success "MCP servers configured"

# Setup VS Code workspace settings for TTA.dev
log_info "Configuring VS Code workspace settings..."

# Ensure .vscode directory exists
mkdir -p .vscode

# Update settings.json with TTA.dev specific configuration
if [ ! -f .vscode/settings.json ]; then
    cat > .vscode/settings.json << 'EOF'
{
  "python.defaultInterpreterPath": "./.venv/bin/python",
  "python.linting.enabled": true,
  "python.linting.ruffEnabled": true,
  "python.formatting.provider": "none",
  "[python]": {
    "editor.formatOnSave": true,
    "editor.defaultFormatter": "charliermarsh.ruff",
    "editor.codeActionsOnSave": {
      "source.fixAll.ruff": true,
      "source.organizeImports.ruff": true
    }
  },
  "github.copilot.enable": {
    "*": true,
    "yaml": true,
    "plaintext": false,
    "markdown": true,
    "python": true
  },
  "files.associations": {
    "*.md": "markdown",
    "copilot-instructions.md": "markdown",
    "AGENTS.md": "markdown"
  },
  "files.exclude": {
    "**/__pycache__": true,
    "**/*.pyc": true,
    ".pytest_cache": true,
    ".ruff_cache": true
  }
}
EOF
    log_success "VS Code settings configured"
else
    log_info "VS Code settings already exist, skipping"
fi

# Verify toolsets configuration
if [ -f .vscode/copilot-toolsets.jsonc ]; then
    log_success "Copilot toolsets configuration found"
else
    log_warning "Copilot toolsets not found - some features may be limited"
fi

# Test MCP server connectivity (best effort)
log_info "Testing MCP server connectivity..."

# This is a best-effort test since MCP servers are managed by VS Code
if command -v npx >/dev/null 2>&1; then
    log_success "Node.js/npx available for Context7 MCP server"
else
    log_warning "Node.js/npx not found - Context7 MCP server may not work"
fi

if command -v docker >/dev/null 2>&1; then
    log_success "Docker available for containerized MCP servers"
else
    log_warning "Docker not found - some MCP servers may not work"
fi

log_success "VS Code Agent setup complete!"
log_info "Next: Reload VS Code window and test: @workspace #tta-package-dev"
