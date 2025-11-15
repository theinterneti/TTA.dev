#!/bin/bash
# scripts/check-environment.sh
# 
# Verification script for TTA.dev development environment
# Tests that all required tools and dependencies are properly installed
#
# Usage:
#   ./scripts/check-environment.sh          # Run all checks
#   ./scripts/check-environment.sh --quick  # Run basic checks only
#   ./scripts/check-environment.sh --help   # Show usage

# Don't exit on error - we want to collect all check results
set +e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Counters
CHECKS_PASSED=0
CHECKS_FAILED=0
CHECKS_WARNED=0

# Function to print colored output
print_status() {
    local status=$1
    local message=$2
    case "$status" in
        "PASS")
            echo -e "${GREEN}✓${NC} $message"
            ((CHECKS_PASSED++))
            ;;
        "FAIL")
            echo -e "${RED}✗${NC} $message"
            ((CHECKS_FAILED++))
            ;;
        "WARN")
            echo -e "${YELLOW}⚠${NC} $message"
            ((CHECKS_WARNED++))
            ;;
        "INFO")
            echo -e "${BLUE}ℹ${NC} $message"
            ;;
    esac
}

# Function to check command availability
check_command() {
    local cmd=$1
    local name=$2
    local required=${3:-true}
    
    if command -v "$cmd" &> /dev/null; then
        local version=$($cmd --version 2>&1 | head -n1)
        print_status "PASS" "$name is installed: $version"
        return 0
    else
        if [ "$required" = true ]; then
            print_status "FAIL" "$name is not installed"
            return 1
        else
            print_status "WARN" "$name is not installed (optional)"
            return 0
        fi
    fi
}

# Function to check Python version
check_python_version() {
    local python_cmd=""
    
    # Try python3 first (Linux/Mac), then python (Windows/some systems)
    if command -v python3 &> /dev/null; then
        python_cmd="python3"
    elif command -v python &> /dev/null; then
        python_cmd="python"
    else
        print_status "FAIL" "Python is not installed (tried 'python' and 'python3')"
        return 1
    fi
    
    local version=$($python_cmd --version 2>&1 | grep -oP '\d+\.\d+')
    local major=$(echo "$version" | cut -d. -f1)
    local minor=$(echo "$version" | cut -d. -f2)
    
    if [ "$major" -eq 3 ] && [ "$minor" -ge 11 ]; then
        print_status "PASS" "Python version $version meets requirement (≥3.11) [using $python_cmd]"
        return 0
    else
        print_status "FAIL" "Python version $version is too old (need ≥3.11)"
        return 1
    fi
}

# Function to check uv is available
check_uv() {
    if command -v uv &> /dev/null; then
        local version=$(uv --version 2>&1)
        local uv_path=$(command -v uv)
        print_status "PASS" "uv is installed: $version (at $uv_path)"
        
        # Check if common uv locations are in PATH
        if [[ ":$PATH:" == *":$HOME/.cargo/bin:"* ]] || [[ ":$PATH:" == *":$HOME/.local/bin:"* ]]; then
            print_status "PASS" "uv is in PATH"
        else
            print_status "WARN" "uv found but common install directories not in PATH"
        fi
        return 0
    else
        print_status "FAIL" "uv is not installed (install: curl -LsSf https://astral.sh/uv/install.sh | sh)"
        return 1
    fi
}

# Function to check virtual environment
check_venv() {
    if [ -d ".venv" ]; then
        print_status "PASS" "Virtual environment exists (.venv)"
        
        # Check if venv has packages
        if [ -d ".venv/lib/python3.11/site-packages" ] || [ -d ".venv/lib/python3.12/site-packages" ]; then
            local pkg_count=$(ls .venv/lib/python*/site-packages | wc -l)
            print_status "PASS" "Virtual environment has packages installed (~$pkg_count items)"
        else
            print_status "WARN" "Virtual environment exists but may be empty"
        fi
        return 0
    else
        print_status "WARN" "Virtual environment not found (.venv) - run 'uv sync --all-extras'"
        return 1
    fi
}

# Function to check dependencies are installed
check_dependencies() {
    if ! check_venv; then
        print_status "FAIL" "Cannot check dependencies without virtual environment"
        return 1
    fi
    
    # Check key packages
    local packages=("pytest" "ruff" "structlog" "opentelemetry-api")
    local all_found=true
    
    for pkg in "${packages[@]}"; do
        if uv run python -c "import ${pkg//-/_}" 2>/dev/null; then
            print_status "PASS" "Package '$pkg' is installed"
        else
            print_status "FAIL" "Package '$pkg' is not installed"
            all_found=false
        fi
    done
    
    if [ "$all_found" = true ]; then
        return 0
    else
        print_status "INFO" "Run 'uv sync --all-extras' to install missing packages"
        return 1
    fi
}

# Function to check if tests can run
check_test_runner() {
    if [ ! -d ".venv" ]; then
        print_status "WARN" "Skipping test runner check (no venv)"
        return 1
    fi
    
    # Try to run pytest --collect-only (doesn't run tests, just collects them)
    if uv run pytest --collect-only -q &>/dev/null; then
        local test_count=$(uv run pytest --collect-only -q 2>/dev/null | grep -c "test_" || echo "0")
        print_status "PASS" "Test runner works (found ~$test_count tests)"
        return 0
    else
        print_status "FAIL" "Test runner failed (try: uv run pytest -v)"
        return 1
    fi
}

# Function to check code quality tools
check_quality_tools() {
    if [ ! -d ".venv" ]; then
        print_status "WARN" "Skipping quality tools check (no venv)"
        return 1
    fi
    
    # Check ruff
    if uv run ruff --version &>/dev/null; then
        print_status "PASS" "Ruff (linter/formatter) works"
    else
        print_status "FAIL" "Ruff is not working"
        return 1
    fi
    
    # Check pyright (via uvx)
    if command -v uvx &> /dev/null; then
        print_status "PASS" "uvx is available (for pyright type checking)"
    else
        print_status "WARN" "uvx not found (may not be able to run pyright)"
    fi
    
    return 0
}

# Function to check Git repository status
check_git() {
    if [ -d ".git" ]; then
        print_status "PASS" "Git repository initialized"
        
        local branch=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "unknown")
        print_status "INFO" "Current branch: $branch"
        
        # Check for uncommitted changes
        if git diff-index --quiet HEAD -- 2>/dev/null; then
            print_status "PASS" "Working directory is clean"
        else
            print_status "WARN" "You have uncommitted changes"
        fi
        return 0
    else
        print_status "FAIL" "Not a Git repository"
        return 1
    fi
}

# Function to check workspace structure
check_workspace() {
    local required_dirs=("packages" "docs" "scripts" "tests")
    local all_found=true
    
    for dir in "${required_dirs[@]}"; do
        if [ -d "$dir" ]; then
            print_status "PASS" "Directory '$dir' exists"
        else
            print_status "FAIL" "Directory '$dir' not found"
            all_found=false
        fi
    done
    
    # Check for key files
    local required_files=("pyproject.toml" "README.md" "AGENTS.md")
    for file in "${required_files[@]}"; do
        if [ -f "$file" ]; then
            print_status "PASS" "File '$file' exists"
        else
            print_status "FAIL" "File '$file' not found"
            all_found=false
        fi
    done
    
    [ "$all_found" = true ]
}

# Function to show summary
show_summary() {
    echo ""
    echo "=========================================="
    echo "Environment Check Summary"
    echo "=========================================="
    echo -e "${GREEN}Passed:${NC}  $CHECKS_PASSED"
    echo -e "${RED}Failed:${NC}  $CHECKS_FAILED"
    echo -e "${YELLOW}Warnings:${NC} $CHECKS_WARNED"
    echo "=========================================="
    
    if [ $CHECKS_FAILED -eq 0 ]; then
        echo -e "${GREEN}✓ Environment is ready for development!${NC}"
        return 0
    else
        echo -e "${RED}✗ Environment has issues that need fixing${NC}"
        echo ""
        echo "Quick fixes:"
        echo "  - Install uv: curl -LsSf https://astral.sh/uv/install.sh | sh"
        echo "  - Sync dependencies: uv sync --all-extras"
        echo "  - Check PATH: echo \$PATH should include ~/.cargo/bin"
        return 1
    fi
}

# Function to show usage
show_usage() {
    cat << EOF
Usage: $0 [OPTIONS]

Verification script for TTA.dev development environment.

Options:
  --quick     Run basic checks only (faster)
  --full      Run all checks including tests (default)
  --help      Show this help message

Examples:
  $0                  # Run full checks
  $0 --quick          # Run basic checks only
  ./scripts/check-environment.sh

This script checks:
  - Python version (≥3.11)
  - uv package manager
  - Virtual environment
  - Dependencies installation
  - Test runner (pytest)
  - Code quality tools (ruff, pyright)
  - Git repository status
  - Workspace structure

Exit codes:
  0 - All checks passed
  1 - One or more checks failed

EOF
}

# Main execution
main() {
    local quick_mode=false
    
    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --quick)
                quick_mode=true
                shift
                ;;
            --full)
                quick_mode=false
                shift
                ;;
            --help|-h)
                show_usage
                exit 0
                ;;
            *)
                echo "Unknown option: $1"
                show_usage
                exit 1
                ;;
        esac
    done
    
    echo "=========================================="
    echo "TTA.dev Environment Verification"
    echo "=========================================="
    echo ""
    
    # Always run basic checks
    echo "=== Basic Environment ==="
    check_python_version
    check_uv
    check_venv
    check_git
    check_workspace
    echo ""
    
    if [ "$quick_mode" = false ]; then
        echo "=== Dependencies ==="
        check_dependencies
        echo ""
        
        echo "=== Development Tools ==="
        check_quality_tools
        check_test_runner
        echo ""
    fi
    
    show_summary
}

# Run main function
main "$@"
