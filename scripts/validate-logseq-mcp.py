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
