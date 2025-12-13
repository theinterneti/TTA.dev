type:: [[Documentation]]
category:: [[MCP]], [[Model Context Protocol]], [[AI Integration]]
difficulty:: [[Intermediate]]
target-audience:: [[Developers]], [[AI Agents]]

---

# MCP Servers for TTA.dev

**Model Context Protocol integration for enhanced AI assistant capabilities**

This namespace contains documentation for MCP (Model Context Protocol) servers in TTA.dev. These servers enable AI assistants to interact with agents, access knowledge graphs, and perform actions through a standardized protocol.

---

## What is MCP?
id:: mcp-overview

The [Model Context Protocol (MCP)](https://modelcontextprotocol.io) is a standardized way to provide context and tools to LLMs. MCP servers can:

- **Resources**: Expose file-like data that can be read by clients
- **Tools**: Provide functions that can be called by the LLM
- **Prompts**: Define reusable templates for LLM interactions

---

## MCP in TTA.dev
id:: mcp-tta-usage

The TTA.dev project uses MCP servers to:

1. **Expose agents as MCP servers**: Allows LLMs to interact with TTA agents through standardized protocol
2. **Access the knowledge graph**: Enables LLMs to query and retrieve information from TTA knowledge graph
3. **Provide tools for game interactions**: Allows LLMs to interact with the game world and perform actions

---

## MCP Architecture
id:: mcp-architecture

The TTA.dev project implements a modular MCP architecture with the following components:

- **MCPConfig**: Manages configuration for MCP servers
- **MCPServerManager**: Centralized manager for starting and stopping MCP servers
- **MCPServerType**: Enum defining different types of MCP servers
- **AgentMCPAdapter**: Adapter that converts TTA agents into MCP servers

This architecture allows for flexible and extensible MCP integration, making it easy to add new MCP servers and capabilities.

---

## Available MCP Servers
id:: mcp-available-servers

### Development MCP Servers

**For development and testing purposes only:**

- **Basic Server**: Simple MCP server demonstrating core concepts
  - Use as reference implementation when developing new MCP servers
  - Located in `examples/mcp/basic_server.py`

### Production/Prototype MCP Servers

**Ready for production or prototype environments:**

- **Agent Tool Server**: Exposes tools for interacting with TTA agents
  - Use when AI assistants need to work with your agents
  - Located in `examples/mcp/agent_tool_server.py`

- **Knowledge Resource Server**: Exposes resources from TTA knowledge graph
  - Use when AI assistants need to query your knowledge graph
  - Located in `examples/mcp/knowledge_resource_server.py`

- **Agent Adapter**: Uses AgentMCPAdapter to expose TTA agent as MCP server
  - Ready for production after customization
  - Located in `examples/mcp/agent_adapter_example.py`

---

## Documentation
id:: mcp-documentation

- [[TTA.dev/MCP/Usage]] - How to use MCP servers in TTA.dev
- [[TTA.dev/MCP/Extending]] - How to extend and create new MCP servers
- [[TTA.dev/MCP/Integration]] - Integration patterns with TTA.dev primitives
- [[TTA.dev/MCP/AI Assistant Guide]] - Guide for AI assistants using MCP

---

## Examples Directory
id:: mcp-examples

**Location:** `examples/mcp/`

### Development Examples

- `basic_server.py`: Core concepts demonstration (development reference only)
- `test_*.py`: Test scripts for verifying functionality (development testing only)

### Production/Prototype Examples

- `agent_tool_server.py`: Agent interaction tools (production ready)
- `knowledge_resource_server.py`: Knowledge graph access (production ready)
- `agent_adapter_example.py`: Agent adapter pattern (requires customization)

---

## Quick Start
id:: mcp-quickstart

### 1. Install MCP Dependencies

```bash
# Using uv (recommended)
uv sync --extra mcp

# Verify installation
python -c "import fastmcp; print('MCP installed')"
```

### 2. Start an MCP Server

```python
from fastmcp import FastMCP

# Create server
mcp = FastMCP("My TTA Server")

# Add a tool
@mcp.tool()
def hello_world() -> str:
    """Say hello"""
    return "Hello from TTA.dev!"

# Run server
if __name__ == "__main__":
    mcp.run()
```

### 3. Configure AI Assistant

Add to your AI assistant configuration (e.g., `.augmentrc.json`):

```json
{
  "mcpServers": {
    "tta-server": {
      "command": "python",
      "args": ["examples/mcp/agent_tool_server.py"]
    }
  }
}
```

---

## Key Takeaways
id:: mcp-summary

**MCP Integration Benefits:**

- **Standardized protocol** for AI assistant integration
- **Flexible architecture** with modular components
- **Production-ready** examples and adapters
- **Easy extension** for new capabilities

**Common Use Cases:**

- Expose TTA agents as tools for AI assistants
- Provide knowledge graph access to LLMs
- Enable game world interactions
- Create custom tools and resources

**Best Practices:**

- Use development servers for learning and testing
- Use production servers for deployments
- Customize adapters for specific needs
- Follow MCP protocol standards

---

## Related Documentation

- [[TTA.dev/Architecture/Component Integration]] - How MCP integrates with primitives
- [[TTA.dev/Guides/Copilot Toolsets]] - Copilot toolsets include MCP tools
- [[TTA.dev/Primitives Catalog]] - Available primitives for MCP integration
- [Model Context Protocol Documentation](https://modelcontextprotocol.io)
- [FastMCP Documentation](https://github.com/jlowin/fastmcp)
- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)

---

**Last Updated:** October 30, 2025
**Status:** Production Ready
**Maintained by:** TTA.dev Team


---
**Logseq:** [[TTA.dev/Logseq/Pages/Tta.dev___mcp___readme]]
