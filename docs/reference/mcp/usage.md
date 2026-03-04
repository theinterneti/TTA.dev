# Using MCP Servers in TTA

This guide explains how to use the MCP servers in the TTA project.

## Prerequisites

Before using the MCP servers, you need to:

1. Install the required dependencies:
   ```bash
   pip install fastmcp mcp
   ```

2. Make sure you have a compatible MCP client. These servers are designed to be used with AI assistants through Augment.

## Running MCP Servers

### Development Servers

#### Basic Server (Development Only)

The basic server demonstrates the core concepts of MCP. This server is intended for development and learning purposes only.

```bash
python examples/mcp/basic_server.py
```

This server provides:
- A simple echo tool
- A calculator tool
- Basic system information resources

### Production/Prototype Servers

#### Agent Tool Server (Production Ready)

The agent tool server exposes tools for interacting with TTA agents. This server is designed for production or prototype use.

```bash
python examples/mcp/agent_tool_server.py
```

This server provides:
- Tools for listing available agents
- Tools for getting information about specific agents
- Tools for processing goals with agents

#### Knowledge Resource Server (Production Ready)

The knowledge resource server exposes resources from the TTA knowledge graph. This server is designed for production or prototype use.

```bash
python examples/mcp/knowledge_resource_server.py
```

This server provides:
- Resources for accessing locations, characters, and items in the knowledge graph
- Tools for querying the knowledge graph directly

## Using the Agent Adapter (Production Ready)

The agent adapter allows you to expose any TTA agent as an MCP server. This adapter is designed for production or prototype use after customization for your specific agents.

```python
from src.mcp.agent_adapter import create_agent_mcp_server
from src.agents.dynamic_agents import WorldBuildingAgent

# Create your agent
agent = WorldBuildingAgent(...)

# Create an MCP server for the agent
adapter = create_agent_mcp_server(
    agent=agent,
    server_name="World Building MCP Server",
    server_description="MCP server for the World Building Agent"
)

# Run the MCP server
adapter.run()
```

This will expose the agent's methods as MCP tools and its data as MCP resources.

### Production Deployment

For production deployment, you should:

1. Create a dedicated script for each agent you want to expose
2. Add proper error handling and logging
3. Consider containerizing the server for easier deployment

## Integrating with AI Assistants through Augment

To use your MCP servers with AI assistants through Augment:

1. Make sure you have Augment installed and configured.

2. Start your MCP servers in separate terminals:

   ```bash
   python examples/mcp/basic_server.py
   python examples/mcp/agent_tool_server.py
   python examples/mcp/knowledge_resource_server.py
   ```

3. Augment will automatically detect these running MCP servers.

4. When you interact with an AI assistant through Augment, the assistant will be able to use these MCP servers to access your agents, knowledge graph, and other capabilities.

5. The AI assistant can then use these servers to perform tasks like:
   - Interacting with your agents
   - Querying your knowledge graph
   - Accessing system information

## Using MCP Servers in Your Code

You can also use MCP servers programmatically in your code:

```python
from mcp.client import MCPClient

# Create an MCP client
client = MCPClient()

# Connect to an MCP server
client.connect("stdio", command=["python", "examples/mcp/basic_server.py"])

# Call a tool
result = client.call_tool("echo", {"message": "Hello, MCP!"})
print(result)

# Read a resource
resource = client.read_resource("info://server")
print(resource)

# Disconnect from the server
client.disconnect()
```

This allows you to integrate MCP servers into your own applications and workflows.


---
**Logseq:** [[TTA.dev/Docs/Mcp/Usage]]
