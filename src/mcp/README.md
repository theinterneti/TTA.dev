# MCP Module

This module provides MCP (Model Context Protocol) server implementations and utilities for the TTA.dev framework. It allows agents to be exposed as MCP servers, making them accessible to AI assistants and other systems.

## Components

- **AgentMCPAdapter**: Adapter that converts a TTA.dev agent into an MCP server
- **MCPConfig**: Configuration manager for MCP servers
- **MCPServerManager**: Centralized manager for starting and stopping MCP servers
- **MCPServerType**: Enum defining different types of MCP servers

## Usage

### Creating an MCP Server for an Agent

```python
from tta.dev.agents import BaseAgent
from tta.dev.mcp import create_agent_mcp_server

# Create an agent
agent = BaseAgent(
    name="MyAgent",
    description="A simple agent for demonstration"
)

# Create an MCP server for the agent
server = create_agent_mcp_server(
    agent=agent,
    server_name="My Agent Server",
    server_description="MCP server for my agent"
)

# Run the server
server.run(host="localhost", port=8000)
```

### Managing MCP Servers

```python
from tta.dev.mcp import MCPServerManager, MCPServerType

# Create a server manager
manager = MCPServerManager()

# Start a server
success, pid = manager.start_server(MCPServerType.BASIC, wait=True)

# Start an agent server
success, pid = manager.start_agent_server(agent, wait=True)

# Stop a server
manager.stop_server(MCPServerType.BASIC)

# Stop an agent server
manager.stop_agent_server(agent.name)

# Stop all servers
manager.stop_all_servers()
```

## Integration with AI Assistants

MCP servers can be used with AI assistants like Augment to provide enhanced capabilities:

1. **Tools**: MCP servers expose agent methods as tools that can be called by AI assistants
2. **Resources**: MCP servers expose agent data as resources that can be accessed by AI assistants
3. **Prompts**: MCP servers provide prompts for AI assistants to use when interacting with agents

For more information, see the [MCP documentation](../../Documentation/mcp/README.md).
