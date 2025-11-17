#!/bin/bash
#
# MCP Auto-Integration Setup Script
#
# This script sets up automatic MCP integration for both VS Code Copilot and Cline.
#
# What it does:
# 1. Parses .hypertool/mcp_servers.json
# 2. Generates ~/.config/mcp/mcp_settings.json (VS Code + Cline)
# 3. Creates .vscode/copilot-persona.json (persona auto-activation for Copilot)
# 4. Creates .cline/persona-config.json (persona auto-activation for Cline)
# 5. Validates file discovery paths
#

set -euo pipefail

WORKSPACE_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
SCRIPTS_DIR="$WORKSPACE_ROOT/scripts/mcp"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${BLUE}ℹ${NC}  $1"
}

log_success() {
    echo -e "${GREEN}✅${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}⚠${NC}  $1"
}

log_error() {
    echo -e "${RED}❌${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."

    if [ ! -f "$WORKSPACE_ROOT/.hypertool/mcp_servers.json" ]; then
        log_error "Hypertool MCP configuration not found: .hypertool/mcp_servers.json"
        exit 1
    fi

    if ! command -v python3 &> /dev/null; then
        log_error "Python 3 is required but not installed"
        exit 1
    fi

    log_success "Prerequisites check passed"
}

# Step 1: Parse Hypertool config and generate agent configs
generate_mcp_configs() {
    log_info "Generating MCP configurations for agents..."

    python3 "$SCRIPTS_DIR/config_parser.py" \
        --workspace "$WORKSPACE_ROOT" \
        --generate

    if [ $? -eq 0 ]; then
        log_success "MCP configurations generated"
    else
        log_error "Failed to generate MCP configurations"
        exit 1
    fi
}

# Step 2: Generate persona activation configs
generate_persona_configs() {
    log_info "Generating persona activation configurations..."

    python3 "$SCRIPTS_DIR/persona_activator.py" \
        --workspace "$WORKSPACE_ROOT" \
        --generate

    if [ $? -eq 0 ]; then
        log_success "Persona activation configs generated"
    else
        log_error "Failed to generate persona configs"
        exit 1
    fi
}

# Step 3: Validate file discovery
validate_file_discovery() {
    log_info "Validating file discovery paths..."

    local all_good=true

    # VS Code MCP config
    if [ -f "$HOME/.config/mcp/mcp_settings.json" ]; then
        log_success "VS Code MCP config: ~/.config/mcp/mcp_settings.json"
    else
        log_error "VS Code MCP config not found"
        all_good=false
    fi

    # VS Code persona config
    if [ -f "$WORKSPACE_ROOT/.vscode/copilot-persona.json" ]; then
        log_success "VS Code persona config: .vscode/copilot-persona.json"
    else
        log_warning "VS Code persona config not found"
    fi

    # Cline persona config
    if [ -f "$WORKSPACE_ROOT/.cline/persona-config.json" ]; then
        log_success "Cline persona config: .cline/persona-config.json"
    else
        log_warning "Cline persona config not found"
    fi

    if [ "$all_good" = false ]; then
        log_error "File discovery validation failed"
        exit 1
    fi

    log_success "File discovery validation passed"
}

# Step 4: Show configuration summary
show_summary() {
    log_info "Configuration Summary"
    echo ""

    # MCP servers count
    local mcp_count=$(jq '.mcpServers | length' "$HOME/.config/mcp/mcp_settings.json")
    echo "  MCP Servers configured: $mcp_count"

    # Selected persona
    local persona=$(jq -r '.selected_persona' "$WORKSPACE_ROOT/.vscode/copilot-persona.json" 2>/dev/null || echo "none")
    echo "  Auto-activated persona: $persona"

    # MCP tools for persona
    local tools=$(jq -r '.mcp_tools | join(", ")' "$WORKSPACE_ROOT/.vscode/copilot-persona.json" 2>/dev/null || echo "none")
    echo "  MCP tools available: $tools"

    echo ""
    log_info "File Locations:"
    echo "  VS Code MCP:     ~/.config/mcp/mcp_settings.json"
    echo "  VS Code Persona: .vscode/copilot-persona.json"
    echo "  Cline Persona:   .cline/persona-config.json"
    echo "  AGENTS.md:       AGENTS.md"
    echo ""
}

# Step 5: Instructions for agent activation
show_activation_instructions() {
    log_info "Next Steps for Agent Activation"
    echo ""
    echo "  1. Reload VS Code window:"
    echo "     Command Palette → 'Developer: Reload Window'"
    echo ""
    echo "  2. Test Copilot with MCP tools:"
    echo "     @workspace #tta-agent-dev"
    echo "     Show me documentation for the RetryPrimitive class"
    echo ""
    echo "  3. Verify persona auto-activation:"
    echo "     Check that Copilot assumes the $persona persona"
    echo ""
    echo "  4. Test Cline integration:"
    echo "     Open Cline sidebar and verify MCP tools are available"
    echo ""
}

# Main execution
main() {
    echo ""
    log_info "TTA.dev MCP Auto-Integration Setup"
    echo ""

    check_prerequisites
    generate_mcp_configs
    generate_persona_configs
    validate_file_discovery
    show_summary
    show_activation_instructions

    log_success "Auto-integration setup complete!"
}

main "$@"
