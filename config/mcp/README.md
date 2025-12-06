# TTA.dev MCP Server Configuration

## VS Code (GitHub Copilot)

The TTA.dev MCP server is already configured in `.vscode/settings.json`:

```json
"mcp.servers": {
    "tta-dev": {
        "command": "uv",
        "args": [
            "run",
            "--directory",
            "${workspaceFolder}/platform/primitives",
            "tta-dev-mcp"
        ],
        "description": "TTA.dev Primitives - Code analysis and primitive recommendations"
    }
}
```

## Claude Desktop

Add to your Claude Desktop config (`~/Library/Application Support/Claude/claude_desktop_config.json` on macOS):

```json
{
  "mcpServers": {
    "tta-dev": {
      "command": "uv",
      "args": [
        "run",
        "--directory",
        "/absolute/path/to/TTA.dev/platform/primitives",
        "tta-dev-mcp"
      ]
    }
  }
}
```

**Note:** Replace `/absolute/path/to/TTA.dev` with your actual path.

## Available Tools

| Tool | Description |
|------|-------------|
| `analyze_code` | Analyze Python code and detect patterns that could use TTA.dev primitives |
| `get_primitive_info` | Get detailed information about a specific primitive |
| `list_primitives` | List all available TTA.dev primitives |
| `search_templates` | Search for code templates matching a query |
| `get_composition_example` | Generate example code composing multiple primitives |

## CLI Alternative

You can also use the CLI directly:

```bash
# Analyze code
tta-dev analyze path/to/file.py

# List primitives
tta-dev primitives

# Get primitive docs
tta-dev docs RetryPrimitive

# Start MCP server manually
tta-dev serve
```
