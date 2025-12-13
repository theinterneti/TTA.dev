# TTA.dev MCP Server

Model Context Protocol server exposing TTA.dev primitives as tools for AI assistants.

## Installation

The MCP server is included with the `tta-dev-primitives` package:

```bash
uv add tta-dev-primitives
```

## Running the Server

```bash
# Via entry point
tta-dev-mcp

# Via CLI
tta-dev serve

# Via Python module
python -m tta_dev_primitives.mcp_server
```

## Available Tools

### `analyze_code`

Analyze Python code and detect patterns that could benefit from TTA.dev primitives.

**Parameters:**
- `code` (required): Python code to analyze
- `file_path` (optional): Path for context
- `project_type` (optional): Type of project (api, workflow, cli, library)
- `min_confidence` (optional): Minimum confidence threshold (0.0-1.0)

**Returns:**
```json
{
  "analysis": {
    "patterns": [{"name": "async_operation", "confidence": 0.95}],
    "primitives": [{"name": "RetryPrimitive", "confidence": 0.90}]
  },
  "recommendations": [
    {
      "primitive": "RetryPrimitive",
      "rationale": "Detected async operations that could fail",
      "template": "..."
    }
  ]
}
```

### `get_primitive_info`

Get detailed information about a specific primitive.

**Parameters:**
- `name` (required): Primitive name (e.g., "RetryPrimitive")

**Returns:**
```json
{
  "name": "RetryPrimitive",
  "description": "Automatic retry with exponential backoff",
  "import_path": "from tta_dev_primitives.recovery import RetryPrimitive",
  "category": "recovery",
  "use_cases": ["Handle transient failures", "Retry API calls"],
  "parameters": [
    {"name": "max_retries", "type": "int", "default": "3"}
  ],
  "example": "..."
}
```

### `list_primitives`

List all available TTA.dev primitives.

**Parameters:**
- `category` (optional): Filter by category

**Returns:**
```json
[
  {
    "name": "RetryPrimitive",
    "category": "recovery",
    "description": "Automatic retry with exponential backoff"
  }
]
```

### `search_templates`

Search for code templates matching a query.

**Parameters:**
- `query` (required): Search query

**Returns:**
```json
[
  {
    "name": "retry_with_backoff",
    "description": "Retry pattern with exponential backoff",
    "code": "...",
    "primitives": ["RetryPrimitive"]
  }
]
```

### `get_composition_example`

Generate example code composing multiple primitives.

**Parameters:**
- `primitives` (required): List of primitive names to compose

**Returns:**
```json
{
  "code": "from tta_dev_primitives.recovery import RetryPrimitive...",
  "explanation": "This workflow composes RetryPrimitive and CachePrimitive..."
}
```

## Configuration

### VS Code (GitHub Copilot)

Add to `.vscode/settings.json`:

```json
{
  "mcp.servers": {
    "tta-dev": {
      "command": "uv",
      "args": ["run", "--directory", "${workspaceFolder}/platform/primitives", "tta-dev-mcp"],
      "description": "TTA.dev Primitives"
    }
  }
}
```

### Claude Desktop

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "tta-dev": {
      "command": "uv",
      "args": ["run", "--directory", "/path/to/TTA.dev/platform/primitives", "tta-dev-mcp"]
    }
  }
}
```

## Architecture

The MCP server shares its analysis core with the CLI:

```
mcp_server/
├── server.py       # FastMCP server with tool definitions
analysis/
├── patterns.py     # PatternDetector
├── matcher.py      # PrimitiveMatcher
├── templates.py    # TemplateProvider
├── analyzer.py     # TTAAnalyzer
```

## Observability

The server includes structured logging via `structlog`:

```
tta_dev.mcp.analyze_code    code_length=500 file_path=app.py
tta_dev.mcp.get_primitive   name=RetryPrimitive
tta_dev.mcp.list_primitives category=recovery
```


---
**Logseq:** [[TTA.dev/Platform/Primitives/Src/Tta_dev_primitives/Mcp_server/Readme]]
