import json
import argparse
import os
from typing import Any, Dict

DEFAULT_CONFIG_PATH = "/home/thein/.vscode-server/data/User/globalStorage/saoudrizwan.claude-dev/settings/cline_mcp_settings.hypertool.json"

def read_config(path: str) -> Dict[str, Any]:
    """Reads the MCP configuration file."""
    if not os.path.exists(path):
        print(f"Configuration file not found at {path}.")
        raise FileNotFoundError
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

def remove_mcp_server(config_path: str, server_name: str):
    """Removes an MCP server from the configuration."""
    config = read_config(config_path)
    
    if server_name not in config["mcpServers"]:
        print(f"Server '{server_name}' not found in the configuration.")
        return

    del config["mcpServers"][server_name]
    print(f"Server '{server_name}' has been removed.")
    
    write_config(config_path, config)

def main():
    parser = argparse.ArgumentParser(description="Remove an MCP server from the Hypertool configuration.")
    parser.add_argument("server_name", help="The name of the MCP server to remove.")
    parser.add_argument("--config-path", default=DEFAULT_CONFIG_PATH, help=f"Path to the MCP config file. Defaults to {DEFAULT_CONFIG_PATH}")

    args = parser.parse_args()

    remove_mcp_server(
        config_path=args.config_path,
        server_name=args.server_name
    )

if __name__ == "__main__":
    main()
