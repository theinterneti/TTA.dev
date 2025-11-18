#!/bin/bash
# scripts/setup/github-actions-agent.sh
# Setup for GitHub Actions Coding Agent context

set -euo pipefail

log_info() { echo -e "\033[0;34mℹ️  $1\033[0m"; }
log_success() { echo -e "\033[0;32m✅ $1\033[0m"; }
log_warning() { echo -e "\033[1;33m⚠️  $1\033[0m"; }

log_info "Setting up GitHub Actions Coding Agent workspace..."

# Verify we're in GitHub Actions
if [ -z "${GITHUB_ACTIONS:-}" ]; then
    log_warning "Not in GitHub Actions environment, but proceeding with setup"
fi

# Environment information
log_info "Environment: GitHub Actions Runner"
log_info "OS: $(uname -s)"
log_info "Architecture: $(uname -m)"
log_info "Available CPU cores: $(nproc)"
log_info "Available memory: $(free -h | awk '/^Mem:/ {print $2}')"

# Verify environment variables
log_info "Checking environment variables..."
env_vars=(
    "PYTHONPATH"
    "PYTHONUTF8"
    "PYTHONDONTWRITEBYTECODE"
    "UV_CACHE_DIR"
)

for var in "${env_vars[@]}"; do
    if [ -n "${!var:-}" ]; then
        log_success "$var=${!var}"
    else
        log_warning "$var not set"
    fi
done

# Verify Python setup
log_info "Verifying Python environment..."
if uv run python --version >/dev/null 2>&1; then
    PYTHON_VERSION=$(uv run python --version)
    log_success "Python: $PYTHON_VERSION"

    # Check Python path
    PYTHON_PATH=$(uv run python -c "import sys; print(sys.executable)")
    log_info "Python executable: $PYTHON_PATH"
else
    log_warning "Python environment issues detected"
fi

# Verify package installation
log_info "Checking TTA.dev packages..."
packages=(
    "tta_dev_primitives"
    "observability_integration"
    "universal_agent_context"
)

for pkg in "${packages[@]}"; do
    if uv run python -c "import $pkg as pkg_module; print('✅ ' + pkg_module.__name__ + ' imported')" 2>/dev/null; then
        log_success "$pkg package available"
    else
        log_warning "$pkg package not importable"
    fi
done

# Verify development tools
log_info "Checking development tools..."
tools=(
    "pytest"
    "ruff"
    "pyright"
)

for tool in "${tools[@]}"; do
    if [ "$tool" = "pyright" ]; then
        if uvx pyright --version >/dev/null 2>&1; then
            VERSION=$(uvx pyright --version 2>/dev/null | head -1)
            log_success "$tool: $VERSION"
        else
            log_warning "$tool not available via uvx"
        fi
    else
        if uv run $tool --version >/dev/null 2>&1; then
            VERSION=$(uv run $tool --version 2>/dev/null | head -1)
            log_success "$tool: $VERSION"
        else
            log_warning "$tool not available"
        fi
    fi
done

# Check workspace structure
log_info "Verifying workspace structure..."
required_dirs=(
    "packages/tta-dev-primitives/src"
    "packages/tta-observability-integration/src"
    "packages/universal-agent-context/src"
    "tests"
    "scripts"
    "docs"
)

for dir in "${required_dirs[@]}"; do
    if [ -d "$dir" ]; then
        log_success "Directory exists: $dir"
    else
        log_warning "Directory missing: $dir"
    fi
done

# Check configuration files
log_info "Checking configuration files..."
config_files=(
    "pyproject.toml"
    "pyrightconfig.json"
    ".github/workflows"
)

for file in "${config_files[@]}"; do
    if [ -e "$file" ]; then
        log_success "Config exists: $file"
    else
        log_warning "Config missing: $file"
    fi
done

# Test basic functionality
log_info "Testing basic functionality..."

# Test import of core modules
if uv run python -c "
from tta_dev_primitives import WorkflowPrimitive, WorkflowContext
from tta_dev_primitives.core import SequentialPrimitive, ParallelPrimitive
print('✅ Core primitives import successful')
" 2>/dev/null; then
    log_success "Core primitives importable"
else
    log_warning "Core primitives import failed"
fi

# Test running a simple test
log_info "Running quick test suite validation..."
if uv run pytest packages/tta-dev-primitives/tests/ -x -q --tb=no >/dev/null 2>&1; then
    log_success "Test suite can run (at least partially)"
else
    log_warning "Test suite has issues"
fi

# GitHub Actions specific setup
log_info "Configuring GitHub Actions specific settings..."

# Set git configuration for commits (if needed)
if command -v git >/dev/null 2>&1; then
    git config --global user.name "GitHub Actions"
    git config --global user.email "actions@github.com"
    log_success "Git configuration set for actions"
fi

# Create GitHub Actions specific environment info
cat > /tmp/gh-actions-env.txt << EOF
GitHub Actions Environment Information
=====================================
Runner OS: $(uname -s)
Runner Arch: $(uname -m)
Python: $(uv run python --version 2>/dev/null || echo "Not available")
uv: $(uv --version 2>/dev/null || echo "Not available")
Workspace: ${GITHUB_WORKSPACE:-$(pwd)}
Repository: ${GITHUB_REPOSITORY:-"Unknown"}
Ref: ${GITHUB_REF:-"Unknown"}
Commit: ${GITHUB_SHA:-"Unknown"}
Run ID: ${GITHUB_RUN_ID:-"Unknown"}
EOF

log_info "Environment info saved to /tmp/gh-actions-env.txt"

log_success "GitHub Actions Coding Agent setup complete!"
log_info "Key reminders:"
log_info "  • No MCP servers available (VS Code only)"
log_info "  • No Copilot toolsets (use direct commands)"
log_info "  • Ephemeral environment (60min timeout)"
log_info "  • Use 'uv run' for all Python commands"
