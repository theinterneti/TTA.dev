import json
import argparse
import os
import re
from typing import Any, Dict

# The path should be absolute, as this script could be run from anywhere.
# Using an environment variable or a default is a robust approach.
DEFAULT_CONFIG_PATH = "/home/thein/.vscode-server/data/User/globalStorage/saoudrizwan.claude-dev/settings/cline_mcp_settings.hypertool.json"

def read_config(path: str) -> Dict[str, Any]:
    """Reads the MCP configuration file."""
    if not os.path.exists(path):
        print(f"Configuration file not found at {path}. A new one will be created.")
        return {"mcpServers": {}}
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        print(f"Error reading configuration file: {e}")
        raise

def write_config(path: str, config: Dict[str, Any]):
    """Writes the MCP configuration file."""
    try:
        with open(path, 'w') as f:
            json.dump(config, f, indent=2)
        print(f"Successfully updated configuration at {path}")
    except IOError as e:
        print(f"Error writing configuration file: {e}")
        raise

def add_mcp_server(config_path: str, server_name: str, command: str, args: list[str], server_type: str = "stdio", timeout: int = 60):
    """Adds a new MCP server to the configuration."""
    config = read_config(config_path)
    
    if server_name in config["mcpServers"]:
        print(f"Server '{server_name}' already exists. Overwriting.")

    new_server_config = {
        "autoApprove": [],
        "disabled": False,
        "timeout": timeout,
        "type": server_type,
        "command": command,
        "args": args
    }
    
    config["mcpServers"][server_name] = new_server_config
    
    write_config(config_path, config)

def parse_github_uri(uri: str) -> tuple[str, str]:
    """Parses a GitHub URI to extract owner and repo."""
    # Handles formats like: github.com/owner/repo, https://github.com/owner/repo
    match = re.search(r"github\.com/([\w.-]+)/([\w.-]+)", uri)
    if not match:
        raise ValueError("Invalid GitHub URI format. Expected 'github.com/owner/repo'.")
    owner, repo = match.groups()
    return owner, repo

def main():
    parser = argparse.ArgumentParser(description="Add a new MCP server to the Hypertool configuration.", formatter_class=argparse.RawTextHelpFormatter)
    
    # Mode of operation
    group = parser.add_argument_group('Modes', 'Choose one mode of operation:')
    mode = group.add_mutually_exclusive_group(required=True)
    mode.add_argument("--uri", help="Add server from a GitHub URI (e.g., 'github.com/owner/repo').")
    mode.add_argument("--manual", action='store_true', help="Add server by manually specifying the command.")

    # Arguments for both modes
    parser.add_argument("--name", help="Custom name for the server. If not provided with --uri, it's derived from the URI.")
    parser.add_argument("--config-path", default=DEFAULT_CONFIG_PATH, help=f"Path to the MCP config file. Defaults to {DEFAULT_CONFIG_PATH}")
    parser.add_argument("--type", default="stdio", help="The server type (e.g., 'stdio', 'sse'). Defaults to 'stdio'.")
    parser.add_argument("--timeout", type=int, default=60, help="Timeout in seconds. Defaults to 60.")

    # Manual mode command
    parser.add_argument("manual_command", nargs='*', help="[Manual Mode Only] The full command and its arguments (e.g., npx -y @my-org/my-mcp-tool).")

    args = parser.parse_args()

    if args.uri:
        try:
            owner, repo = parse_github_uri(args.uri)
            server_name = args.name if args.name else f"{owner}/{repo}"
            command = "npx"
            command_args = ["-y", f"@{owner}/{repo.replace('-mcp', '')}-mcp@latest"]
            
            print(f"Derived from URI: name='{server_name}', command='{command}', args={command_args}")

            add_mcp_server(
                config_path=args.config_path,
                server_name=server_name,
                command=command,
                args=command_args,
                server_type=args.type,
                timeout=args.timeout
            )
        except ValueError as e:
            parser.error(str(e))

    elif args.manual:
        if not args.name:
            parser.error("--name is required for manual mode.")
        if not args.manual_command:
            parser.error("The full command is required for manual mode.")
        
        server_name = args.name
        command = args.manual_command[0]
        command_args = args.manual_command[1:]

        add_mcp_server(
            config_path=args.config_path,
            server_name=server_name,
            command=command,
            args=command_args,
            server_type=args.type,
            timeout=args.timeout
        )

if __name__ == "__main__":
    main()
