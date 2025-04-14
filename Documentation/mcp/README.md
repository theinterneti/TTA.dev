# MCP Servers for TTA.dev

This directory contains documentation for the MCP (Model Context Protocol) servers in the TTA.dev framework. These servers are designed to work with AI assistants through Augment to provide enhanced capabilities to LLMs and enable them to interact with your agents and knowledge graph.

## What is MCP?

The [Model Context Protocol (MCP)](https://modelcontextprotocol.io) is a standardized way to provide context and tools to LLMs. MCP servers can:

- Expose data through **Resources** (file-like data that can be read by clients)
- Provide functionality through **Tools** (functions that can be called by the LLM)
- Define interaction patterns through **Prompts** (reusable templates for LLM interactions)

## MCP in TTA.dev

The TTA.dev framework uses MCP servers to:

1. **Expose agents as MCP servers**: This allows LLMs to interact with TTA.dev agents through a standardized protocol.
2. **Access the knowledge graph**: This allows LLMs to query and retrieve information from the knowledge graph.
3. **Provide tools for agent interactions**: This allows LLMs to interact with agents and perform actions.

## MCP Architecture

The TTA.dev framework implements a modular MCP architecture with the following components:

- **MCPConfig**: Manages configuration for MCP servers
- **MCPServerManager**: Centralized manager for starting and stopping MCP servers
- **MCPServerType**: Enum defining different types of MCP servers
- **AgentMCPAdapter**: Adapter that converts TTA.dev agents into MCP servers

This architecture allows for flexible and extensible MCP integration, making it easy to add new MCP servers and capabilities.

## Available MCP Servers

The TTA.dev framework includes several MCP servers, categorized by their intended use:

### Development MCP Servers

These servers are intended for development and testing purposes only:

- **Basic Server**: A simple MCP server demonstrating the core concepts. Use this as a reference implementation when developing new MCP servers.

### Production MCP Servers

These servers are designed for use in production environments:

- **Agent Tool Server**: An MCP server that exposes tools for interacting with TTA.dev agents. This server should be used when you need AI assistants to work with your agents.

- **Knowledge Resource Server**: An MCP server that exposes resources from the knowledge graph. Use this server when you need AI assistants to query your knowledge graph.

## Documentation

- [Usage Guide](usage.md): How to use the MCP servers in the TTA.dev framework.
- [Extending Guide](extending.md): How to extend and create new MCP servers for the TTA.dev framework.
- [Integration Guide](integration.md): How to integrate MCP servers with AI assistants.
- [Examples](examples.md): Examples of using MCP servers in the TTA.dev framework.

## Examples

The `examples/mcp` directory contains example MCP server implementations:

### Development Examples

- `basic_server.py`: A simple MCP server demonstrating the core concepts. **For development reference only.**
- `test_*.py`: Test scripts for verifying MCP server functionality. **For development testing only.**

### Production Examples

- `agent_tool_server.py`: An MCP server that exposes tools for interacting with TTA.dev agents. **Ready for production use.**
- `knowledge_resource_server.py`: An MCP server that exposes resources from the knowledge graph. **Ready for production use.**
- `agent_adapter_example.py`: An example of using the AgentMCPAdapter to expose a TTA.dev agent as an MCP server. **Ready for production use after customization.**

## References

- [Model Context Protocol Documentation](https://modelcontextprotocol.io)
- [FastMCP Documentation](https://github.com/jlowin/fastmcp)
- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)
- [Augment Documentation](https://docs.augment.dev)
