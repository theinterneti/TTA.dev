"""TTA.dev MCP Server Module.

Model Context Protocol server exposing TTA.dev primitives as tools
for AI agents like Claude, Copilot, and Cline.

Usage:
    # As module
    python -m tta_dev_primitives.mcp_server

    # Via CLI
    tta-dev serve

    # In Claude Desktop config
    {
        "mcpServers": {
            "tta-dev": {
                "command": "uvx",
                "args": ["tta-dev-primitives"]
            }
        }
    }
"""

from tta_dev_primitives.mcp_server.server import create_server, run_server

__all__ = ["run_server", "create_server"]
