#!/bin/bash

# TTA.dev Agent Workspace Setup
# Complete automated setup for all agent contexts with role-specific guidance

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Script configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
SETUP_DIR="${SCRIPT_DIR}/setup"

# Default configuration
FORCE_SETUP=false
SPECIFIED_CONTEXT=""

show_help() {
    cat << EOF
TTA.dev Agent Workspace Setup

USAGE:
    $0 [OPTIONS]

OPTIONS:
    --force             Force setup even if already configured
    --context CONTEXT   Specify agent context manually
    --help, -h          Show this help message

CONTEXTS:
    vscode-local        VS Code Extension (local development)
    github-actions      GitHub Actions Coding Agent (ephemeral)
    cline-local         Cline Extension (local development)
    github-cli          GitHub CLI (terminal)

EXAMPLES:
    $0                                  # Auto-detect context and setup
    $0 --force                          # Force complete re-setup
    $0 --context vscode-local           # Setup for VS Code specifically
    $0 --context github-actions         # Setup for GitHub Actions environment

EOF
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --force)
            FORCE_SETUP=true
            shift
            ;;
        --context)
            SPECIFIED_CONTEXT="$2"
            shift 2
            ;;
        --help|-h)
            show_help
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Context detection functions
detect_agent_context() {
    local context=""

    # Check for GitHub Actions environment
    if [[ -n "${GITHUB_ACTIONS:-}" ]]; then
        context="github-actions"

    # Check for VS Code environment
    elif [[ -n "${VSCODE_PID:-}" ]] || [[ -n "${TERM_PROGRAM:-}" && "${TERM_PROGRAM}" == "vscode" ]]; then
        context="vscode-local"

    # Check for Cline-specific indicators
    elif [[ -f "${PROJECT_ROOT}/.cline/instructions.md" ]] && [[ -n "${VSCODE_PID:-}" ]]; then
        context="cline-local"

    # Check for terminal with GitHub CLI
    elif command -v gh >/dev/null 2>&1; then
        context="github-cli"

    # Default to VS Code if uncertain
    else
        context="vscode-local"
    fi

    echo "$context"
}

# Common setup functions
setup_uv() {
    log_info "Setting up uv package manager..."

    if ! command -v uv >/dev/null 2>&1; then
        log_warning "uv not found, installing..."
        curl -LsSf https://astral.sh/uv/install.sh | sh
        export PATH="$HOME/.cargo/bin:$PATH"
    fi

    log_success "uv is available: $(uv --version)"
}

setup_python_environment() {
    log_info "Setting up Python environment..."

    cd "$PROJECT_ROOT"

    # Sync dependencies
    log_info "Syncing Python dependencies..."
    uv sync --all-extras

    # Verify core imports
    log_info "Verifying core imports..."
    if uv run python -c "import tta_dev_primitives; print('✅ tta-dev-primitives loaded successfully')" 2>/dev/null; then
        log_success "Core imports verified"
    else
        log_error "Core imports failed - dependency issue detected"
        return 1
    fi
}

setup_git_hooks() {
    log_info "Setting up Git hooks..."

    local hooks_dir="${PROJECT_ROOT}/.git/hooks"
    local post_commit_hook="${hooks_dir}/post-commit"

    # Create post-commit hook for activity tracking
    if [[ ! -f "$post_commit_hook" ]]; then
        cat > "$post_commit_hook" << 'EOF'
#!/bin/bash
# TTA.dev activity tracker hook
if command -v systemctl >/dev/null 2>&1; then
    systemctl --user restart tta-activity-tracker.service 2>/dev/null || true
fi
EOF
        chmod +x "$post_commit_hook"
        log_success "Git post-commit hook installed"
    fi
}

validate_setup() {
    log_info "Validating setup..."

    local validation_errors=0

    # Check Python environment
    if ! uv run python -c "import tta_dev_primitives" 2>/dev/null; then
        log_error "Python environment validation failed"
        ((validation_errors++))
    fi

    # Check Git repository
    if ! git rev-parse --git-dir >/dev/null 2>&1; then
        log_error "Not in a Git repository"
        ((validation_errors++))
    fi

    # Check project structure
    local required_dirs=("packages" "scripts" "docs" "logseq")
    for dir in "${required_dirs[@]}"; do
        if [[ ! -d "${PROJECT_ROOT}/${dir}" ]]; then
            log_error "Missing required directory: $dir"
            ((validation_errors++))
        fi
    done

    if [[ $validation_errors -eq 0 ]]; then
        log_success "Setup validation passed"
        return 0
    else
        log_error "Setup validation failed with $validation_errors errors"
        return 1
    fi
}

# Context-specific setup orchestration
setup_context() {
    local context="$1"
    local setup_script=""

    # Map context names to script names
    case "$context" in
        "vscode-local")
            setup_script="${SETUP_DIR}/vscode-agent.sh"
            ;;
        "github-actions")
            setup_script="${SETUP_DIR}/github-actions-agent.sh"
            ;;
        "cline-local")
            setup_script="${SETUP_DIR}/cline-agent.sh"
            ;;
        "github-cli")
            log_info "GitHub CLI context detected - manual setup required"
            show_cli_setup_instructions
            return 0
            ;;
        *)
            log_error "Unknown context: $context"
            return 1
            ;;
    esac

    if [[ -f "$setup_script" ]]; then
        log_info "Running context-specific setup: $context"
        bash "$setup_script" ${FORCE_SETUP:+--force}
    else
        log_warning "Setup script not found: $setup_script"
        log_info "Continuing with basic setup..."
        return 0
    fi
}

show_cli_setup_instructions() {
    cat << EOF

📋 GitHub CLI Setup Instructions:

1. Install GitHub CLI:
   curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo gpg --dearmor -o /usr/share/keyrings/githubcli-archive-keyring.gpv
   echo "deb [arch=\$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null
   sudo apt update && sudo apt install gh

2. Authenticate:
   gh auth login

3. Configure for TTA.dev:
   gh repo clone theinterneti/TTA.dev
   cd TTA.dev

4. Use standard CLI commands:
   gh copilot suggest "How to run tests"
   gh copilot explain "git log --oneline"

EOF
}

show_role_selection_guide() {
    cat << EOF

🎯 Agent Role Selection Guide:

Choose your role based on experience and focus:

📝 Documentation Writer (Beginner)
   • Best for: New to TTA.dev, documentation focus
   • Toolsets: #tta-docs, #tta-minimal
   • Start with: README updates, basic guides

🔧 Package Developer (Intermediate)
   • Best for: Python experience, feature development
   • Toolsets: #tta-package-dev, #tta-testing
   • Start with: Simple primitive modifications

📊 Observability Engineer (Advanced)
   • Best for: Production systems experience
   • Toolsets: #tta-observability, #tta-troubleshoot
   • Start with: Basic metrics implementation

🧠 Agent Coordinator (Expert)
   • Best for: Multi-agent workflow expertise
   • Toolsets: #tta-agent-dev, #tta-mcp-integration
   • Start with: Basic agent coordination

EOF
}

show_next_steps() {
    local context="$1"

    cat << EOF

🚀 Setup Complete! Next Steps:

EOF

    case "$context" in
        "vscode-local")
            cat << EOF
VS Code Extension Setup:
1. Reload VS Code window: Ctrl+Shift+P → "Developer: Reload Window"
2. Choose your role and test setup:
   @workspace #tta-docs
   Help me understand TTA.dev architecture and suggest next steps

3. Available toolsets:
   • #tta-docs - Documentation work
   • #tta-package-dev - Core development
   • #tta-observability - Tracing & metrics
   • #tta-agent-dev - Multi-agent workflows

EOF
            ;;
        "github-actions")
            cat << EOF
GitHub Actions Environment:
1. Test environment:
   uv run pytest -v

2. Remember limitations:
   ❌ No MCP servers
   ❌ No Copilot toolsets
   ✅ Standard development tools

3. Use direct commands:
   uv run pytest --cov=packages
   uv run ruff check . --fix

EOF
            ;;
        "cline-local")
            cat << EOF
Cline Extension Setup:
1. Enhanced MCP integration ready
2. Use Cline's chat interface with full MCP capabilities
3. Collaborative features enabled

EOF
            ;;
    esac

    cat << EOF
📚 Documentation:
   • Agent Instructions: .github/copilot-instructions.md
   • TODO Management: logseq/pages/TODO Management System.md
   • Setup Troubleshooting: scripts/setup-agent-workspace.sh --help

EOF
}

# Main execution flow
main() {
    log_info "TTA.dev Agent Workspace Setup Starting..."

    # Create setup directory if it doesn't exist
    mkdir -p "$SETUP_DIR"

    # Determine context
    local context=""
    if [[ -n "$SPECIFIED_CONTEXT" ]]; then
        context="$SPECIFIED_CONTEXT"
        log_info "Using specified context: $context"
    else
        context=$(detect_agent_context)
        log_info "Detected context: $context"
    fi

    # Common setup steps
    log_info "Running common setup steps..."
    setup_uv || { log_error "uv setup failed"; exit 1; }
    setup_python_environment || { log_error "Python environment setup failed"; exit 1; }
    setup_git_hooks || { log_warning "Git hooks setup failed"; }

    # Context-specific setup
    log_info "Setting up context: $context"
    setup_context "$context" || { log_error "Context-specific setup failed"; exit 1; }

    # Final validation
    if validate_setup; then
        log_success "TTA.dev Agent Workspace Setup Complete!"
        show_role_selection_guide
        show_next_steps "$context"
        exit 0
    else
        log_error "Setup validation failed. Please check the errors above."
        exit 1
    fi
}

# Run main function with all arguments
main "$@"
