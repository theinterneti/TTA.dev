# MCP Servers

This document provides an overview of the MCP (Model Context Protocol) servers in the TTA project.

## Overview

MCP servers provide a standardized way for AI assistants to access tools and resources. The TTA project includes several MCP servers:

1. **Basic Server** (DEVELOPMENT ONLY)
   - A simple MCP server for development and learning purposes
   - Not intended for production use
   - Located at `examples/mcp/basic_server.py`

2. **Agent Tool Server** (PRODUCTION READY)
   - An MCP server that exposes tools for interacting with TTA agents
   - Designed for production or prototype use
   - Located at `examples/mcp/agent_tool_server.py`

3. **Knowledge Resource Server** (PRODUCTION READY)
   - An MCP server that exposes resources from the TTA knowledge graph
   - Designed for production or prototype use
   - Located at `examples/mcp/knowledge_resource_server.py`

4. **Agent Adapter** (PRODUCTION READY)
   - A utility for creating MCP servers from TTA agents
   - Designed for production or prototype use
   - Located at `src/mcp/agent_adapter.py`

## Running MCP Servers

### Using Docker Compose

The easiest way to run the MCP servers is using Docker Compose:

```bash
# Start all MCP servers
docker-compose -f docker-compose-mcp.yml up -d

# Start a specific MCP server
docker-compose -f docker-compose-mcp.yml up -d agent-tool-mcp-server

# Stop all MCP servers
docker-compose -f docker-compose-mcp.yml down
```

### Using the Management Script

You can also use the `manage_mcp_servers.py` script to start, stop, and test the MCP servers:

```bash
# Start all MCP servers
python3 scripts/manage_mcp_servers.py start

# Start specific MCP servers
python3 scripts/manage_mcp_servers.py start --servers basic agent_tool

# Stop all MCP servers
python3 scripts/manage_mcp_servers.py stop

# Check MCP server status
python3 scripts/manage_mcp_servers.py status

# Test MCP servers
python3 scripts/manage_mcp_servers.py test
```

### Running Manually

You can also run the MCP servers manually:

```bash
# Basic Server (Development Only)
python3 examples/mcp/basic_server.py --host localhost --port 8000

# Agent Tool Server (Production Ready)
python3 examples/mcp/agent_tool_server.py

# Knowledge Resource Server (Production Ready)
python3 examples/mcp/knowledge_resource_server.py
```

## Testing MCP Servers

The TTA project includes several test suites for the MCP servers:

### Unit Tests

```bash
# Run all MCP unit tests
python3 tests/mcp/run_tests.py

# Run specific MCP unit tests
python3 -m pytest tests/mcp/test_basic_server.py
```

### Integration Tests

```bash
# Run all MCP integration tests
python3 tests/integration/run_integration_tests.py

# Run specific MCP integration tests
python3 tests/integration/run_integration_tests.py --test servers
```

### Simulated User Tests

```bash
# Run simulated user tests
python3 tests/mcp/run_user_tests.py
```

## Configuring MCP Servers

MCP servers can be configured using the `config/mcp_config.json` file or by passing command-line arguments.

### Configuration File

The `config/mcp_config.json` file contains configuration for all MCP servers:

```json
{
    "servers": {
        "basic": {
            "enabled": true,
            "host": "localhost",
            "port": 8000,
            "script_path": "examples/mcp/basic_server.py",
            "dependencies": ["fastmcp", "requests"]
        },
        "agent_tool": {
            "enabled": true,
            "host": "localhost",
            "port": 8001,
            "script_path": "examples/mcp/agent_tool_server.py",
            "dependencies": ["fastmcp", "requests", "pydantic"]
        },
        "knowledge_resource": {
            "enabled": true,
            "host": "localhost",
            "port": 8002,
            "script_path": "examples/mcp/knowledge_resource_server.py",
            "dependencies": ["fastmcp", "requests", "neo4j"]
        }
    }
}
```

### Command-Line Arguments

Most MCP servers accept command-line arguments for configuration:

```bash
# Basic Server with custom host and port
python3 examples/mcp/basic_server.py --host 0.0.0.0 --port 8000

# Basic Server with debug logging
python3 examples/mcp/basic_server.py --debug
```

## Creating Custom MCP Servers

You can create custom MCP servers using the `AgentMCPAdapter` class:

```python
from src.mcp import create_agent_mcp_server
from src.agents import create_dynamic_agents
from src.knowledge import get_neo4j_manager

# Create the agent
agents = create_dynamic_agents(neo4j_manager=get_neo4j_manager())

# Get the agent from the registry
agent = agents["wba"]  # World Building Agent

# Create the MCP server
adapter = create_agent_mcp_server(
    agent=agent,
    server_name="World Building MCP Server",
    server_description="MCP server for the World Building Agent",
    dependencies=["fastmcp"]
)

# Run the MCP server
adapter.run()
```

## Integrating with AI Assistants

MCP servers can be integrated with AI assistants using the MCP protocol. The TTA project includes examples of how to do this in the `tests/integration/test_ai_assistant_integration.py` file.

Here's a simple example of how to connect to an MCP server from an AI assistant:

```python
import requests
import json

# Connect to the MCP server
response = requests.post(
    "http://localhost:8001/mcp",
    json={
        "type": "handshake",
        "version": "2025-03-26",
        "capabilities": {
            "transports": ["http"]
        }
    }
)

# Parse the response
response_data = response.json()
session_id = response_data["session_id"]

# List available tools
response = requests.post(
    "http://localhost:8001/mcp",
    json={
        "type": "list_tools",
        "session_id": session_id
    }
)

# Parse the response
response_data = response.json()
tools = response_data["tools"]

# Call a tool
response = requests.post(
    "http://localhost:8001/mcp",
    json={
        "type": "call_tool",
        "session_id": session_id,
        "tool": "list_agents",
        "parameters": {}
    }
)

# Parse the response
response_data = response.json()
result = response_data["content"][0]["text"]
```

## References

- [MCP Protocol Specification](https://github.com/anthropics/anthropic-cookbook/tree/main/mcp)
- [FastMCP Documentation](https://github.com/anthropics/fastmcp)


---
**Logseq:** [[TTA.dev/Docs/Mcp/Mcp_servers]]
