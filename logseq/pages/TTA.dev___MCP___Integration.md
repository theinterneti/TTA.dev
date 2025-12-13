type:: [[Guide]]
category:: [[MCP]], [[Integration]], [[Configuration]]
difficulty:: [[Intermediate]]
estimated-time:: 20 minutes
target-audience:: [[Developers]]

---

# MCP Integration with TTA.dev

**Comprehensive guide for integrating MCP into TTA primitives**

---

## Overview
id:: mcp-integration-overview

The TTA.dev MCP integration enables:

1. **Server Management** - Start and manage MCP servers programmatically
2. **Agent Exposure** - Expose agents as MCP servers for external access
3. **Knowledge Graph Access** - Query knowledge graph through MCP resources
4. **Tool Orchestration** - Provide game interaction tools through MCP

---

## Getting Started
id:: mcp-integration-getting-started

### Starting MCP Servers
id:: mcp-integration-starting-servers

**Using the startup script:**

```bash
# Start all servers
python scripts/start_mcp_servers.py

# Start specific servers
python scripts/start_mcp_servers.py --servers basic agent_tool knowledge_resource
```

**Available servers:**
- `basic` - Development/testing server
- `agent_tool` - Agent interaction server
- `knowledge_resource` - Knowledge graph access server

### Starting Servers Programmatically
id:: mcp-integration-programmatic-start

```python
from src.mcp import MCPServerManager, MCPConfig, MCPServerType

# Create MCP configuration
config = MCPConfig()

# Create server manager
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

**Key parameters:**
- `server_type` - Server to start (BASIC, AGENT_TOOL, KNOWLEDGE_RESOURCE)
- `wait` - Block until server is ready
- `timeout` - Maximum wait time in seconds

---

## Exposing Agents as MCP Servers
id:: mcp-integration-exposing-agents

### Using Server Manager
id:: mcp-integration-server-manager

**Expose any BaseAgent as MCP server:**

```python
from src.agents import WorldBuildingAgent
from src.mcp import MCPServerManager

# Create an agent
agent = WorldBuildingAgent(
    neo4j_manager=neo4j_manager,
    tools=tools
)

# Create server manager
server_manager = MCPServerManager()

# Start agent server
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

### Using Agent Method
id:: mcp-integration-agent-method

**Direct agent-to-MCP conversion:**

```python
from src.agents import WorldBuildingAgent

# Create an agent
agent = WorldBuildingAgent(
    neo4j_manager=neo4j_manager,
    tools=tools
)

# Convert to MCP server
adapter = agent.to_mcp_server()

# Run the MCP server
adapter.run()
```

**Benefits of `to_mcp_server()`:**
- Automatic tool registration
- Resource exposure
- Built-in error handling
- Seamless agent interaction

---

## Configuration
id:: mcp-integration-configuration

### Configuration File
id:: mcp-integration-config-file

**Location:** `config/mcp_config.json`

**Configuration includes:**

- **Server type** - Basic, agent tool, knowledge resource
- **Host and port** - Network configuration
- **Dependencies** - Required packages
- **Script path** - Server executable location
- **Enabled/disabled status** - Control server availability

**Example configuration:**

```json
{
  "servers": {
    "basic": {
      "type": "basic",
      "host": "localhost",
      "port": 8000,
      "dependencies": ["fastmcp"],
      "script_path": "examples/mcp/basic_server.py",
      "enabled": true
    },
    "agent_tool": {
      "type": "agent_tool",
      "host": "localhost",
      "port": 8001,
      "dependencies": ["fastmcp", "agents"],
      "script_path": "examples/mcp/agent_tool_server.py",
      "enabled": true
    }
  }
}
```

### Command Line Options
id:: mcp-integration-cli-options

**Available MCP options:**

```bash
MCP Options:
  --mcp-config MCP_CONFIG
                        Path to MCP configuration file
  --start-mcp-servers   Start MCP servers
  --mcp-servers {basic,agent_tool,knowledge_resource,all} [...]
                        MCP servers to start (default: all)
```

**Usage examples:**

```bash
# Start all servers
python -m src.core.main --start-mcp-servers

# Start specific servers
python -m src.core.main --start-mcp-servers --mcp-servers basic agent_tool

# Custom config file
python -m src.core.main --start-mcp-servers --mcp-config custom_config.json
```

---

## Advanced Usage
id:: mcp-integration-advanced

### Creating Custom MCP Servers
id:: mcp-integration-custom-servers

**Extend existing server types:**

1. Create new server script in `examples/mcp/`
2. Follow MCP server structure (see [[TTA.dev/MCP/Extending]])
3. Add configuration to `config/mcp_config.json`
4. Use `MCPServerManager` to start server

**Example structure:**

```python
from fastmcp import FastMCP

mcp = FastMCP("Custom Server")

@mcp.tool()
def custom_tool() -> str:
    """Custom tool implementation"""
    return "Custom result"

if __name__ == "__main__":
    mcp.run()
```

**Add to configuration:**

```json
{
  "custom": {
    "type": "custom",
    "host": "localhost",
    "port": 8002,
    "script_path": "examples/mcp/custom_server.py",
    "enabled": true
  }
}
```

### Integrating with AI Assistants
id:: mcp-integration-ai-assistants

**Using MCP servers with Augment:**

**1. Start MCP servers:**

```bash
python scripts/start_mcp_servers.py
```

**2. Configure Augment:**

Add to `.augmentrc.json`:

```json
{
  "mcpServers": {
    "tta-agent-tools": {
      "command": "python",
      "args": ["-m", "examples.mcp.agent_tool_server"]
    },
    "tta-knowledge": {
      "command": "python",
      "args": ["-m", "examples.mcp.knowledge_resource_server"]
    }
  }
}
```

**3. Use MCP tools and resources:**

Augment will automatically detect and use available tools and resources.

**Available capabilities:**
- List and interact with agents
- Query knowledge graph
- Access system information
- Use custom tools

---

## Integration with TTA Primitives
id:: mcp-integration-primitives

### Using MCP with Workflow Primitives
id:: mcp-integration-workflow-primitives

**Integrate MCP servers into workflows:**

```python
from tta_dev_primitives import SequentialPrimitive
from src.mcp import MCPServerManager, MCPServerType

# Start MCP server
server_manager = MCPServerManager()
server_manager.start_server(MCPServerType.AGENT_TOOL)

# Create workflow with MCP-exposed agent
workflow = (
    input_processor >>
    mcp_agent_call >>
    result_formatter
)

result = await workflow.execute(context, input_data)
```

### Observability Integration
id:: mcp-integration-observability

**MCP servers with observability:**

```python
from observability_integration import initialize_observability
from src.mcp import MCPServerManager

# Initialize observability
initialize_observability(
    service_name="mcp-servers",
    enable_prometheus=True
)

# Start MCP servers (automatically instrumented)
server_manager = MCPServerManager()
server_manager.start_all_servers()
```

**Metrics available:**
- Server startup/shutdown events
- Tool call counts and latency
- Resource access patterns
- Error rates

---

## Troubleshooting
id:: mcp-integration-troubleshooting

### Common Issues
id:: mcp-integration-common-issues

**Port conflicts:**

```bash
# Error: Port 8000 already in use

# Solution 1: Change port in config
# Edit config/mcp_config.json, change "port": 8001

# Solution 2: Kill existing process
lsof -ti:8000 | xargs kill
```

**Missing dependencies:**

```bash
# Error: ModuleNotFoundError: No module named 'fastmcp'

# Solution: Install MCP dependencies
uv sync --extra mcp
```

**Server not starting:**

```bash
# Check logs for errors
python -m src.core.main --debug --start-mcp-servers

# Verify configuration
cat config/mcp_config.json

# Test individual server
python examples/mcp/basic_server.py
```

**Agent server initialization failures:**

```python
# Error: Agent not initialized

# Solution: Ensure agent dependencies ready
agent = WorldBuildingAgent(
    neo4j_manager=neo4j_manager,  # Must be initialized
    tools=tools  # Must be provided
)
```

### Logging
id:: mcp-integration-logging

**Enable debug logging:**

```bash
# Detailed MCP logs
python -m src.core.main --debug --start-mcp-servers

# Check server output
tail -f logs/mcp_server.log
```

**Programmatic logging:**

```python
import logging

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)

# Start servers with debug output
server_manager = MCPServerManager()
server_manager.start_server(MCPServerType.BASIC)
```

---

## Key Takeaways
id:: mcp-integration-summary

**Server Management:**

- Start all servers: `python scripts/start_mcp_servers.py`
- Start specific servers: `--servers basic agent_tool`
- Programmatic control: `MCPServerManager`

**Agent Exposure:**

- **Server manager**: `start_agent_server(agent=agent)`
- **Direct method**: `agent.to_mcp_server()`
- Automatic tool/resource registration

**Configuration:**

- **File**: `config/mcp_config.json`
- **CLI**: `--mcp-config`, `--start-mcp-servers`, `--mcp-servers`
- **Customization**: Host, port, dependencies, script path

**Integration:**

- Works with TTA workflow primitives
- Built-in observability support
- AI assistant compatible (Augment, Cline)

**Troubleshooting:**

- Port conflicts: Change port or kill process
- Missing dependencies: `uv sync --extra mcp`
- Debug logging: `--debug` flag

---

## Related Documentation

- [[TTA.dev/MCP/README]] - MCP overview and architecture
- [[TTA.dev/MCP/Usage]] - Running and using servers
- [[TTA.dev/MCP/Extending]] - Creating custom servers
- [[TTA.dev/MCP/AI Assistant Guide]] - AI assistant integration
- [[TTA.dev/Architecture/Component Integration]] - System integration patterns
- [[TTA.dev/Guides/Observability]] - Observability setup

---

**Last Updated:** October 30, 2025
**Status:** Production Ready
**Maintained by:** TTA.dev Team


---
**Logseq:** [[TTA.dev/Logseq/Pages/Tta.dev___mcp___integration]]
