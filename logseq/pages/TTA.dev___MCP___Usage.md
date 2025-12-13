type:: [[Guide]]
category:: [[MCP]], [[Model Context Protocol]], [[Usage]]
difficulty:: [[Beginner]]
estimated-time:: 15 minutes
target-audience:: [[Developers]], [[AI Agents]]

---

# Using MCP Servers in TTA.dev

**Practical guide for running and integrating MCP servers**

---

## Prerequisites
id:: mcp-usage-prerequisites

Before using MCP servers, you need to:

**1. Install dependencies:**

```bash
# Using uv (recommended for TTA.dev)
uv sync --extra mcp

# Or manually
pip install fastmcp mcp
```

**2. Have a compatible MCP client:**

- AI assistants through Augment (recommended)
- Cline (Claude-powered VS Code extension)
- Custom MCP client implementation

---

## Running MCP Servers
id:: mcp-usage-running

### Development Servers
id:: mcp-dev-servers

#### Basic Server (Development Only)

The basic server demonstrates core MCP concepts. **For learning purposes only.**

```bash
python examples/mcp/basic_server.py
```

**Provides:**

- Simple echo tool
- Calculator tool
- Basic system information resources

### Production/Prototype Servers
id:: mcp-production-servers

#### Agent Tool Server (Production Ready)

Exposes tools for interacting with TTA agents.

```bash
python examples/mcp/agent_tool_server.py
```

**Provides:**

- List available agents
- Get information about specific agents
- Process goals with agents

#### Knowledge Resource Server (Production Ready)

Exposes resources from TTA knowledge graph.

```bash
python examples/mcp/knowledge_resource_server.py
```

**Provides:**

- Access locations, characters, and items in knowledge graph
- Query the knowledge graph directly

---

## Using the Agent Adapter
id:: mcp-agent-adapter

The agent adapter exposes any TTA agent as an MCP server. **Production ready after customization.**

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

This exposes the agent's methods as MCP tools and its data as MCP resources.

### Production Deployment
id:: mcp-production-deployment

**Best practices for production:**

1. **Create dedicated scripts** for each agent you want to expose
2. **Add error handling and logging** for reliability
3. **Consider containerization** for easier deployment

**Example production script:**

```python
import logging
from src.mcp.agent_adapter import create_agent_mcp_server
from src.agents.dynamic_agents import WorldBuildingAgent

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    # Create agent with production config
    agent = WorldBuildingAgent(
        config_path="config/production.yaml"
    )

    # Create MCP server
    adapter = create_agent_mcp_server(
        agent=agent,
        server_name="Production World Building Server",
        server_description="Production MCP server for World Building Agent"
    )

    logger.info("Starting MCP server...")
    adapter.run()

except Exception as e:
    logger.error(f"Failed to start MCP server: {e}")
    raise
```

---

## Integrating with AI Assistants
id:: mcp-ai-assistant-integration

### Using with Augment
id:: mcp-augment-integration

**1. Install and configure Augment:**

Make sure Augment is installed and configured in your environment.

**2. Start MCP servers in separate terminals:**

```bash
# Terminal 1: Basic server (development)
python examples/mcp/basic_server.py

# Terminal 2: Agent tool server
python examples/mcp/agent_tool_server.py

# Terminal 3: Knowledge resource server
python examples/mcp/knowledge_resource_server.py
```

**3. Augment auto-detection:**

Augment automatically detects running MCP servers.

**4. AI assistant capabilities:**

The AI assistant can now:

- Interact with your agents
- Query your knowledge graph
- Access system information
- Use custom tools and resources

### Configuration File
id:: mcp-augment-config

Add to `.augmentrc.json`:

```json
{
  "mcpServers": {
    "tta-agent-tools": {
      "command": "python",
      "args": ["examples/mcp/agent_tool_server.py"]
    },
    "tta-knowledge": {
      "command": "python",
      "args": ["examples/mcp/knowledge_resource_server.py"]
    }
  }
}
```

---

## Programmatic Usage
id:: mcp-programmatic-usage

Use MCP servers in your own code:

```python
from mcp.client import MCPClient

# Create an MCP client
client = MCPClient()

# Connect to an MCP server
client.connect("stdio", command=["python", "examples/mcp/basic_server.py"])

# Call a tool
result = client.call_tool("echo", {"message": "Hello, MCP!"})
print(result)
# Output: "Hello, MCP!"

# Read a resource
resource = client.read_resource("info://server")
print(resource)

# Disconnect from the server
client.disconnect()
```

**This enables:**

- Integration into custom applications
- Workflow automation
- Programmatic agent interaction

---

## Common Use Cases
id:: mcp-use-cases

### Use Case 1: AI Assistant with Agent Access

```text
User: "List all available agents"
AI Assistant: [Uses agent_tool_server]
Response: "Available agents: WorldBuildingAgent, QuestGeneratorAgent, ..."
```

### Use Case 2: Knowledge Graph Query

```text
User: "What locations are in the knowledge graph?"
AI Assistant: [Uses knowledge_resource_server]
Response: "Locations: Castle Thunderforge, Whispering Woods, ..."
```

### Use Case 3: Custom Workflow Integration

```python
# Automate agent interaction
client = MCPClient()
client.connect("stdio", command=["python", "examples/mcp/agent_tool_server.py"])

# Process multiple goals
goals = ["Generate quest", "Create character", "Design location"]
for goal in goals:
    result = client.call_tool("process_goal", {"goal": goal, "agent_name": "WorldBuildingAgent"})
    print(f"Result: {result}")
```

---

## Troubleshooting
id:: mcp-troubleshooting

### Server won't start

**Problem:** `ModuleNotFoundError: No module named 'fastmcp'`

**Solution:**

```bash
uv sync --extra mcp
# Or
pip install fastmcp mcp
```

### Augment can't detect server

**Problem:** Server running but not visible in Augment

**Solutions:**

1. Check server is actually running: `ps aux | grep python`
2. Verify Augment configuration in `.augmentrc.json`
3. Restart Augment after starting servers
4. Check server logs for errors

### Tool calls fail

**Problem:** MCP tool calls return errors

**Solutions:**

1. Verify agent is properly initialized
2. Check tool parameters match expected format
3. Review server logs for detailed error messages
4. Ensure knowledge graph is accessible

---

## Key Takeaways
id:: mcp-usage-summary

**Quick Setup:**

1. Install dependencies: `uv sync --extra mcp`
2. Start servers: `python examples/mcp/agent_tool_server.py`
3. Configure AI assistant: Add to `.augmentrc.json`
4. Use tools through AI assistant or programmatically

**Server Types:**

- **Development**: basic_server.py (learning only)
- **Production**: agent_tool_server.py, knowledge_resource_server.py (production ready)
- **Custom**: Use agent adapter for your own agents

**Best Practices:**

- Use uv for dependency management (consistent with TTA.dev)
- Add error handling for production deployments
- Configure logging for debugging
- Test servers before production use
- Containerize for easier deployment

---

## Related Documentation

- [[TTA.dev/MCP/README]] - MCP overview and architecture
- [[TTA.dev/MCP/Extending]] - Create custom MCP servers
- [[TTA.dev/MCP/Integration]] - Integration patterns with primitives
- [[TTA.dev/MCP/AI Assistant Guide]] - Guide for AI assistants
- [[TTA.dev/Architecture/Component Integration]] - MCP integration analysis
- [Model Context Protocol Documentation](https://modelcontextprotocol.io)

---

**Last Updated:** October 30, 2025
**Status:** Production Ready
**Maintained by:** TTA.dev Team


---
**Logseq:** [[TTA.dev/Logseq/Pages/Tta.dev___mcp___usage]]
