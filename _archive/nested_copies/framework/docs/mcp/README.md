# MCP Servers for TTA

This directory contains documentation for the MCP (Model Context Protocol) servers in the TTA project. These servers are designed to work with AI assistants through Augment to provide enhanced capabilities to LLMs and enable them to interact with your agents and knowledge graph.

## What is MCP?

The [Model Context Protocol (MCP)](https://modelcontextprotocol.io) is a standardized way to provide context and tools to LLMs. MCP servers can:

- Expose data through **Resources** (file-like data that can be read by clients)
- Provide functionality through **Tools** (functions that can be called by the LLM)
- Define interaction patterns through **Prompts** (reusable templates for LLM interactions)

## MCP in TTA

The TTA project uses MCP servers to:

1. **Expose agents as MCP servers**: This allows LLMs to interact with TTA agents through a standardized protocol.
2. **Access the knowledge graph**: This allows LLMs to query and retrieve information from the TTA knowledge graph.
3. **Provide tools for game interactions**: This allows LLMs to interact with the game world and perform actions.

## MCP Architecture

The TTA project implements a modular MCP architecture with the following components:

- **MCPConfig**: Manages configuration for MCP servers
- **MCPServerManager**: Centralized manager for starting and stopping MCP servers
- **MCPServerType**: Enum defining different types of MCP servers
- **AgentMCPAdapter**: Adapter that converts TTA agents into MCP servers

This architecture allows for flexible and extensible MCP integration, making it easy to add new MCP servers and capabilities.

## Available MCP Servers

The TTA project includes several MCP servers, categorized by their intended use:

### Development MCP Servers

These servers are intended for development and testing purposes only:

- **Basic Server**: A simple MCP server demonstrating the core concepts. Use this as a reference implementation when developing new MCP servers.

### Production/Prototype MCP Servers

These servers are designed for use in production or prototype environments:

- **Agent Tool Server**: An MCP server that exposes tools for interacting with TTA agents. This server should be used when you need AI assistants to work with your agents.

- **Knowledge Resource Server**: An MCP server that exposes resources from the TTA knowledge graph. Use this server when you need AI assistants to query your knowledge graph.

## Documentation

- [Usage Guide](usage.md): How to use the MCP servers in the TTA project.
- [Extending Guide](extending.md): How to extend and create new MCP servers for the TTA project.

## Examples

The `examples/mcp` directory contains example MCP server implementations:

### Development Examples

- `basic_server.py`: A simple MCP server demonstrating the core concepts. **For development reference only.**
- `test_*.py`: Test scripts for verifying MCP server functionality. **For development testing only.**

### Production/Prototype Examples

- `agent_tool_server.py`: An MCP server that exposes tools for interacting with TTA agents. **Ready for production/prototype use.**
- `knowledge_resource_server.py`: An MCP server that exposes resources from the TTA knowledge graph. **Ready for production/prototype use.**
- `agent_adapter_example.py`: An example of using the AgentMCPAdapter to expose a TTA agent as an MCP server. **Ready for production/prototype use after customization.**

## References

- [Model Context Protocol Documentation](https://modelcontextprotocol.io)
- [FastMCP Documentation](https://github.com/jlowin/fastmcp)
- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)
- [Augment Documentation](https://docs.augment.dev)
- [VS Code Documentation](https://code.visualstudio.com/docs)


---
**Logseq:** [[TTA.dev/_archive/Nested_copies/Framework/Docs/Mcp/Readme]]
