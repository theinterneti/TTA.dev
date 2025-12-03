#!/bin/bash
# Setup script for Logseq MCP servers
# Installs and validates both ergut/mcp-logseq (Python) and @joelhooks/logseq-mcp-tools (TypeScript)

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

LOGSEQ_GRAPH_PATH="${LOGSEQ_GRAPH_PATH:-/workspaces/TTA.dev/logseq}"

echo -e "${BLUE}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║         Logseq MCP Server Setup for VS Code Copilot          ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Function to check command existence
check_command() {
    if command -v "$1" &> /dev/null; then
        echo -e "  ${GREEN}✓${NC} $1 found: $(command -v "$1")"
        return 0
    else
        echo -e "  ${RED}✗${NC} $1 not found"
        return 1
    fi
}

# Function to validate Logseq graph
validate_logseq_graph() {
    echo -e "\n${YELLOW}[1/5] Validating Logseq Graph${NC}"
    echo "  Graph path: $LOGSEQ_GRAPH_PATH"
    
    if [[ ! -d "$LOGSEQ_GRAPH_PATH" ]]; then
        echo -e "  ${RED}✗${NC} Logseq graph directory not found!"
        exit 1
    fi
    
    if [[ ! -d "$LOGSEQ_GRAPH_PATH/pages" ]]; then
        echo -e "  ${RED}✗${NC} No 'pages' directory found in graph"
        exit 1
    fi
    
    if [[ ! -d "$LOGSEQ_GRAPH_PATH/journals" ]]; then
        echo -e "  ${RED}✗${NC} No 'journals' directory found in graph"
        exit 1
    fi
    
    local page_count=$(find "$LOGSEQ_GRAPH_PATH/pages" -name "*.md" 2>/dev/null | wc -l)
    local journal_count=$(find "$LOGSEQ_GRAPH_PATH/journals" -name "*.md" 2>/dev/null | wc -l)
    
    echo -e "  ${GREEN}✓${NC} Valid Logseq graph found"
    echo -e "    📄 Pages: $page_count"
    echo -e "    📓 Journals: $journal_count"
}

# Function to check prerequisites
check_prerequisites() {
    echo -e "\n${YELLOW}[2/5] Checking Prerequisites${NC}"
    
    local missing=0
    
    check_command "uv" || missing=1
    check_command "npx" || missing=1
    check_command "node" || missing=1
    
    if [[ $missing -eq 1 ]]; then
        echo -e "\n  ${RED}Missing required tools. Please install them first.${NC}"
        exit 1
    fi
    
    echo -e "  ${GREEN}✓${NC} All prerequisites satisfied"
}

# Function to install Python MCP server (ergut/mcp-logseq)
install_python_mcp() {
    echo -e "\n${YELLOW}[3/5] Installing Python MCP Server (ergut/mcp-logseq)${NC}"
    
    # Test if it can be run with uv
    echo "  Testing mcp-logseq installation..."
    
    if uv run --with mcp-logseq python -c "import mcp_logseq; print('OK')" 2>/dev/null; then
        echo -e "  ${GREEN}✓${NC} mcp-logseq package available via uv"
    else
        echo "  Installing mcp-logseq..."
        uv pip install mcp-logseq 2>/dev/null || {
            echo -e "  ${YELLOW}⚠${NC} Direct install failed, will use 'uv run --with' at runtime"
        }
    fi
    
    # Validate it can start (just check help/version)
    echo "  Validating server can start..."
    if timeout 5 uv run --with mcp-logseq mcp-logseq --help &>/dev/null || \
       timeout 5 uv run --with mcp-logseq python -m mcp_logseq --help &>/dev/null; then
        echo -e "  ${GREEN}✓${NC} Python MCP server validated"
    else
        echo -e "  ${YELLOW}⚠${NC} Could not validate help command (may still work)"
    fi
}

# Function to install TypeScript MCP server (@joelhooks/logseq-mcp-tools)
install_typescript_mcp() {
    echo -e "\n${YELLOW}[4/5] Installing TypeScript MCP Server (@joelhooks/logseq-mcp-tools)${NC}"
    
    echo "  Pre-caching @joelhooks/logseq-mcp-tools..."
    
    # Pre-fetch the package to speed up future invocations
    if npx -y @joelhooks/logseq-mcp-tools --help &>/dev/null 2>&1; then
        echo -e "  ${GREEN}✓${NC} TypeScript MCP server cached and validated"
    else
        # Try just fetching without running
        npm cache add @joelhooks/logseq-mcp-tools 2>/dev/null || true
        echo -e "  ${YELLOW}⚠${NC} Pre-cached package (validation skipped)"
    fi
}

# Function to show MCP configuration
show_mcp_config() {
    echo -e "\n${YELLOW}[5/5] MCP Configuration${NC}"
    
    local config_path="$HOME/.vscode-server/data/User/globalStorage/github.copilot/mcp.json"
    local alt_config_path="$HOME/.config/Code/User/mcp.json"
    
    echo ""
    echo -e "  ${BLUE}Add these servers to your VS Code MCP configuration:${NC}"
    echo ""
    echo -e "  ${GREEN}File: vscode-userdata:/User/mcp.json${NC}"
    echo ""
    
    cat << 'EOF'
  Add to "servers" section:

    "logseq-crud": {
      "command": "uv",
      "args": ["run", "--with", "mcp-logseq", "mcp-logseq"],
      "env": {
        "LOGSEQ_GRAPH_PATH": "/workspaces/TTA.dev/logseq"
      },
      "type": "stdio"
    },
    "logseq-analysis": {
      "command": "npx",
      "args": ["-y", "@joelhooks/logseq-mcp-tools"],
      "env": {
        "LOGSEQ_GRAPH_PATH": "/workspaces/TTA.dev/logseq"
      },
      "type": "stdio"
    }
EOF
    echo ""
}

# Function to create validation script
create_validation_script() {
    local script_path="/workspaces/TTA.dev/scripts/validate-logseq-mcp.py"
    
    cat > "$script_path" << 'PYTHON_EOF'
#!/usr/bin/env python3
"""
Validate Logseq MCP server configuration and connectivity.
Run after setup to ensure everything is working.
"""

import json
import subprocess
import sys
from pathlib import Path

# Colors
GREEN = "\033[0;32m"
RED = "\033[0;31m"
YELLOW = "\033[1;33m"
BLUE = "\033[0;34m"
NC = "\033[0m"

def check_logseq_graph(graph_path: str) -> dict:
    """Check Logseq graph structure."""
    path = Path(graph_path)
    result = {
        "valid": False,
        "pages": 0,
        "journals": 0,
        "errors": []
    }
    
    if not path.exists():
        result["errors"].append(f"Graph path does not exist: {graph_path}")
        return result
    
    pages_dir = path / "pages"
    journals_dir = path / "journals"
    
    if not pages_dir.exists():
        result["errors"].append("Missing 'pages' directory")
    else:
        result["pages"] = len(list(pages_dir.glob("*.md")))
    
    if not journals_dir.exists():
        result["errors"].append("Missing 'journals' directory")
    else:
        result["journals"] = len(list(journals_dir.glob("*.md")))
    
    result["valid"] = len(result["errors"]) == 0
    return result

def check_python_mcp() -> dict:
    """Check Python MCP server (mcp-logseq)."""
    result = {"available": False, "version": None, "error": None}
    
    try:
        proc = subprocess.run(
            ["uv", "run", "--with", "mcp-logseq", "python", "-c", 
             "import mcp_logseq; print('OK')"],
            capture_output=True,
            text=True,
            timeout=30
        )
        if proc.returncode == 0 and "OK" in proc.stdout:
            result["available"] = True
            result["version"] = "latest"
    except subprocess.TimeoutExpired:
        result["error"] = "Timeout checking mcp-logseq"
    except Exception as e:
        result["error"] = str(e)
    
    return result

def check_typescript_mcp() -> dict:
    """Check TypeScript MCP server (@joelhooks/logseq-mcp-tools)."""
    result = {"available": False, "version": None, "error": None}
    
    try:
        # Just check if npx can resolve the package
        proc = subprocess.run(
            ["npm", "view", "@joelhooks/logseq-mcp-tools", "version"],
            capture_output=True,
            text=True,
            timeout=30
        )
        if proc.returncode == 0:
            result["available"] = True
            result["version"] = proc.stdout.strip()
    except subprocess.TimeoutExpired:
        result["error"] = "Timeout checking @joelhooks/logseq-mcp-tools"
    except Exception as e:
        result["error"] = str(e)
    
    return result

def check_mcp_config() -> dict:
    """Check if MCP servers are configured in VS Code."""
    result = {"configured": False, "servers": [], "path": None}
    
    # Common locations for MCP config
    possible_paths = [
        Path.home() / ".vscode-server/data/User/globalStorage/github.copilot/mcp.json",
        Path.home() / ".config/Code/User/mcp.json",
        Path("/vscode/data/User/mcp.json"),
    ]
    
    for config_path in possible_paths:
        if config_path.exists():
            result["path"] = str(config_path)
            try:
                with open(config_path) as f:
                    config = json.load(f)
                    servers = config.get("servers", {})
                    result["servers"] = list(servers.keys())
                    result["configured"] = "logseq" in str(servers).lower()
            except Exception as e:
                result["error"] = str(e)
            break
    
    return result

def main():
    print(f"\n{BLUE}╔══════════════════════════════════════════════════════════════╗{NC}")
    print(f"{BLUE}║           Logseq MCP Server Validation                       ║{NC}")
    print(f"{BLUE}╚══════════════════════════════════════════════════════════════╝{NC}\n")
    
    graph_path = "/workspaces/TTA.dev/logseq"
    all_passed = True
    
    # 1. Check Logseq graph
    print(f"{YELLOW}[1/4] Logseq Graph{NC}")
    graph_result = check_logseq_graph(graph_path)
    if graph_result["valid"]:
        print(f"  {GREEN}✓{NC} Valid graph at {graph_path}")
        print(f"    📄 {graph_result['pages']} pages")
        print(f"    📓 {graph_result['journals']} journals")
    else:
        print(f"  {RED}✗{NC} Invalid graph: {', '.join(graph_result['errors'])}")
        all_passed = False
    
    # 2. Check Python MCP
    print(f"\n{YELLOW}[2/4] Python MCP Server (mcp-logseq){NC}")
    python_result = check_python_mcp()
    if python_result["available"]:
        print(f"  {GREEN}✓{NC} Available via uv")
    else:
        print(f"  {RED}✗{NC} Not available: {python_result.get('error', 'Unknown error')}")
        all_passed = False
    
    # 3. Check TypeScript MCP
    print(f"\n{YELLOW}[3/4] TypeScript MCP Server (@joelhooks/logseq-mcp-tools){NC}")
    ts_result = check_typescript_mcp()
    if ts_result["available"]:
        print(f"  {GREEN}✓{NC} Available via npx (version: {ts_result['version']})")
    else:
        print(f"  {YELLOW}⚠{NC} Could not verify: {ts_result.get('error', 'Unknown')}")
    
    # 4. Check MCP config
    print(f"\n{YELLOW}[4/4] VS Code MCP Configuration{NC}")
    config_result = check_mcp_config()
    if config_result["path"]:
        print(f"  📁 Config found: {config_result['path']}")
        print(f"  📦 Servers: {', '.join(config_result['servers']) or 'none'}")
        if config_result["configured"]:
            print(f"  {GREEN}✓{NC} Logseq servers configured")
        else:
            print(f"  {YELLOW}⚠{NC} Logseq servers NOT yet configured")
            print(f"      Run: scripts/setup-logseq-mcp.sh for config instructions")
    else:
        print(f"  {YELLOW}⚠{NC} No MCP config file found")
    
    # Summary
    print(f"\n{BLUE}{'═' * 64}{NC}")
    if all_passed:
        print(f"{GREEN}✓ All core validations passed!{NC}")
        print(f"\n  Next steps:")
        print(f"  1. Add Logseq servers to your VS Code MCP config")
        print(f"  2. Reload VS Code window (Ctrl+Shift+P → 'Reload Window')")
        print(f"  3. Test with Copilot: 'List my Logseq pages'")
    else:
        print(f"{RED}✗ Some validations failed. See above for details.{NC}")
        sys.exit(1)

if __name__ == "__main__":
    main()
PYTHON_EOF

    chmod +x "$script_path"
    echo -e "  ${GREEN}✓${NC} Created validation script: scripts/validate-logseq-mcp.py"
}

# Main execution
main() {
    validate_logseq_graph
    check_prerequisites
    install_python_mcp
    install_typescript_mcp
    create_validation_script
    show_mcp_config
    
    echo -e "${GREEN}╔══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║                    Setup Complete!                           ║${NC}"
    echo -e "${GREEN}╚══════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "  ${BLUE}Next Steps:${NC}"
    echo "  1. Update your VS Code MCP config (see above)"
    echo "  2. Reload VS Code window (Ctrl+Shift+P → 'Reload Window')"
    echo "  3. Validate: uv run python scripts/validate-logseq-mcp.py"
    echo "  4. Test with Copilot: 'Search my Logseq for TODO items'"
    echo ""
}

main "$@"
