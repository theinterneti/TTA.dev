# MCP Integration Guide

This guide explains how to integrate MCP into your TTA project.

## Overview

The TTA project provides a comprehensive MCP integration that allows you to:

1. Start and manage MCP servers
2. Expose agents as MCP servers
3. Access the knowledge graph through MCP
4. Provide tools for game interactions through MCP

## Getting Started

### Starting MCP Servers

The easiest way to start MCP servers is to use the `start_mcp_servers.py` script:

```bash
python scripts/start_mcp_servers.py
```

This will start all available MCP servers. You can also specify which servers to start:

```bash
python scripts/start_mcp_servers.py --servers basic agent_tool knowledge_resource
```

### Starting MCP Servers Programmatically

You can also start MCP servers programmatically using the `MCPServerManager`:

```python
from src.mcp import MCPServerManager, MCPConfig, MCPServerType

# Create MCP configuration
config = MCPConfig()

# Create MCP server manager
server_manager = MCPServerManager(config=config)

# Start a specific server
success, process_id = server_manager.start_server(
    server_type=MCPServerType.BASIC,
    wait=True,
    timeout=5
)

if success:
    print(f"Started server (PID: {process_id})")
else:
    print("Failed to start server")
```

### Exposing Agents as MCP Servers

You can expose any agent that inherits from `BaseAgent` as an MCP server:

```python
from src.agents import WorldBuildingAgent
from src.mcp import MCPServerManager

# Create an agent
agent = WorldBuildingAgent(
    neo4j_manager=neo4j_manager,
    tools=tools
)

# Create MCP server manager
server_manager = MCPServerManager()

# Start an agent server
success, process_id = server_manager.start_agent_server(
    agent=agent,
    wait=True,
    timeout=5
)

if success:
    print(f"Started agent server (PID: {process_id})")
else:
    print("Failed to start agent server")
```

You can also use the `to_mcp_server` method on any agent:

```python
from src.agents import WorldBuildingAgent

# Create an agent
agent = WorldBuildingAgent(
    neo4j_manager=neo4j_manager,
    tools=tools
)

# Convert the agent to an MCP server
adapter = agent.to_mcp_server()

# Run the MCP server
adapter.run()
```

## Configuration

### MCP Configuration File

The MCP integration uses a configuration file located at `config/mcp_config.json`. This file contains configuration for all MCP servers, including:

- Server type
- Host and port
- Dependencies
- Script path
- Enabled/disabled status

You can modify this file to customize the MCP servers.

### Command Line Options

The main entry point (`src.core.main`) provides several command line options for MCP:

```
MCP Options:
  --mcp-config MCP_CONFIG
                        Path to MCP configuration file
  --start-mcp-servers   Start MCP servers
  --mcp-servers {basic,agent_tool,knowledge_resource,all} [{basic,agent_tool,knowledge_resource,all} ...]
                        MCP servers to start (default: all)
```

You can use these options to customize the MCP integration when running the game:

```bash
python -m src.core.main --start-mcp-servers --mcp-servers basic agent_tool
```

## Advanced Usage

### Creating Custom MCP Servers

You can create custom MCP servers by extending the existing MCP server types or creating new ones. See the `examples/mcp` directory for examples.

### Integrating with AI Assistants

To use your MCP servers with AI assistants through Augment:

1. Start your MCP servers
2. Configure Augment to connect to your MCP servers
3. Use the MCP tools and resources in your AI assistant

## Troubleshooting

### Common Issues

- **Port conflicts**: If you encounter port conflicts, you can change the port in the MCP configuration file.
- **Missing dependencies**: Make sure you have all the required dependencies installed.
- **Server not starting**: Check the logs for error messages.

### Logging

The MCP integration uses Python's logging module. You can enable debug logging to get more detailed information:

```bash
python -m src.core.main --debug --start-mcp-servers
```


---
**Logseq:** [[TTA.dev/_archive/Nested_copies/Framework/Docs/Mcp/Integration]]
