# Serena MCP Server

**MCP Server Entry Point**: `server.py`
**Protocol**: Model Context Protocol (MCP) v1.12.3

## Overview

This directory contains the MCP (Model Context Protocol) server for Serena, which exposes Serena's code search and editing tools to compatible LLM clients.

## Supported Clients

### IDE Integrations
- **Claude Code** - Official Anthropic IDE with native MCP support
- **Claude Desktop** - Desktop application for Claude
- **VSCode** - Via Cline or Roo Code extensions
- **Cursor** - AI-first IDE with MCP integration
- **IntelliJ** - Via MCP plugins

### Terminal Clients
- **Codex** - Terminal-based coding assistant
- **Gemini-CLI** - Google's Gemini in terminal
- **Qwen3-Coder** - Alibaba's coding assistant
- **rovodev** - Development assistant
- **OpenHands CLI** - Collaborative coding tool

### Local Clients
- **OpenWebUI** - Local web interface for LLMs
- **Jan** - Privacy-focused desktop AI
- **Agno** - Agent playground

## Starting the Server

### From Serena Core

```bash
cd platform_tta_dev/components/serena/core
uv run serena-mcp-server
```

### Standalone (from this directory)

```bash
# Requires serena package installed
python server.py
```

## Configuration

MCP clients typically discover the server via configuration files:

### Claude Desktop (`~/.config/claude/config.json`)

```json
{
  "mcpServers": {
    "serena": {
      "command": "uv",
      "args": [
        "run",
        "--directory",
        "/path/to/platform_tta_dev/components/serena/core",
        "serena-mcp-server"
      ]
    }
  }
}
```

### VSCode Cline (`.cline/mcp.json`)

```json
{
  "mcpServers": {
    "serena": {
      "command": "uv",
      "args": ["run", "serena-mcp-server"],
      "cwd": "/path/to/platform_tta_dev/components/serena/core"
    }
  }
}
```

## Exposed Tools

The MCP server exposes the following tools to clients:

### Code Search

- **`find_symbol`** - Search for symbols by name (classes, functions, variables)
  - Parameters: `symbol_name`, `project_path`, `symbol_type` (optional)
  - Returns: List of symbol locations with file paths and line numbers

- **`find_referencing_symbols`** - Find symbols that reference a given symbol
  - Parameters: `symbol_location`, `reference_type` (optional)
  - Returns: List of referencing symbols

- **`find_referencing_code_snippets`** - Find code snippets using a symbol
  - Parameters: `symbol_location`
  - Returns: Code snippets with context

- **`get_symbols_overview`** - Get overview of top-level symbols in a file
  - Parameters: `file_path`
  - Returns: Symbol hierarchy with types and locations

### Code Editing

- **`create_text_file`** - Create or overwrite a file
  - Parameters: `file_path`, `content`
  - Returns: Success confirmation

- **`delete_lines`** - Delete a range of lines from a file
  - Parameters: `file_path`, `start_line`, `end_line`
  - Returns: Modified file content

- **`insert_after_symbol`** - Insert code after a specific symbol
  - Parameters: `symbol_location`, `code_to_insert`
  - Returns: Modified file content

### Project Management

- **`activate_project`** - Activate a project by name
  - Parameters: `project_name`
  - Returns: Activation status

- **`initial_instructions`** - Get initial instructions for current project
  - Returns: Project-specific guidance

### Shell & Memory

- **`execute_shell_command`** - Execute shell commands
  - Parameters: `command`, `cwd` (optional)
  - Returns: Command output

- **`read_memory`** - Read from project memory store
  - Parameters: `memory_key`
  - Returns: Stored value

- **`write_memory`** - Write to project memory store
  - Parameters: `memory_key`, `memory_value`
  - Returns: Write confirmation

- **`delete_memory`** - Delete memory entry
  - Parameters: `memory_key`
  - Returns: Deletion confirmation

### Configuration

- **`get_current_config`** - Print current agent configuration
  - Returns: Active projects, tools, contexts, and modes

- **`check_onboarding_performed`** - Check if project onboarding was done
  - Returns: Boolean status

## Server Protocol

The server implements MCP's `stdio` transport:

- **Input**: JSON-RPC 2.0 messages over stdin
- **Output**: JSON-RPC 2.0 responses over stdout
- **Errors**: Logged to stderr

## Security Considerations

### Tool Restrictions

Configure `.serena/project.yml` to restrict tools:

```yaml
# Disable dangerous tools in production
excluded_tools:
  - execute_shell_command
  - delete_lines
  - create_text_file

# Enable read-only mode
read_only: true
```

### Path Restrictions

The server respects `.gitignore` patterns:

```yaml
# In .serena/project.yml
ignore_all_files_in_gitignore: true

# Additional paths to ignore
ignored_paths:
  - "secrets/**"
  - "*.key"
  - ".env*"
```

## Troubleshooting

### Server Won't Start

```bash
# Check UV installation
uv --version

# Verify serena package
cd ../core
uv run python -c "import serena; print(serena.__version__)"
```

### Client Can't Connect

```bash
# Test server manually
cd ../core
uv run serena-mcp-server

# Send test JSON-RPC request
echo '{"jsonrpc":"2.0","method":"tools/list","id":1}' | uv run serena-mcp-server
```

### Tools Not Available

```bash
# List available tools
cd ../core
uv run scripts/print_tool_overview.py

# Check project configuration
cat .serena/project.yml
```

## Integration with TTA Platform

### Platform Component Integration

Serena MCP server can analyze other TTA platform components:

```python
# Example: Analyze hypertool component
{
  "tool": "find_symbol",
  "arguments": {
    "symbol_name": "MCP",
    "project_path": "platform_tta_dev/components/hypertool"
  }
}
```

### TTA Application Integration

Serena can analyze TTA's therapeutic game codebase:

```python
{
  "tool": "find_referencing_symbols",
  "arguments": {
    "symbol_location": "app_tta/src/agent_orchestration/circuit_breaker.py:CircuitBreaker"
  }
}
```

## Development

### Adding New Tools

1. Implement tool in `../core/src/serena/tools/`
2. Register in tool registry
3. Update MCP server tool list
4. Document in this README

### Testing MCP Server

```bash
cd ../core
uv run pytest test/serena/test_mcp_server.py
```

## References

- [MCP Specification](https://spec.modelcontextprotocol.io/)
- [Serena Documentation](../core/docs/index.md)
- [Tool Implementation Guide](../core/src/serena/tools/README.md)


---
**Logseq:** [[TTA.dev/Platform_tta_dev/Components/Serena/Mcp/Readme]]
