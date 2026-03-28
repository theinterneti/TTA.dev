"""TTA.dev MCP Server Module.

Model Context Protocol server exposing TTA.dev primitives as tools
for AI agents like Claude, Copilot, and Cline.

Usage:
    # As module
    python -m ttadev.primitives.mcp_server

    # Via historical package-local CLI wrapper
    tta-dev serve

    # In Claude Desktop config
    {
        "mcpServers": {
            "tta-dev": {
                "command": "uv",
                "args": ["run", "python", "-m", "ttadev.primitives.mcp_server"]
            }
        }
    }
"""

from ttadev.primitives.mcp_server.server import create_server, run_server

__all__ = ["run_server", "create_server"]
