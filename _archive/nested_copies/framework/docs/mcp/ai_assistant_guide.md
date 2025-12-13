# AI Assistant Guide to Using TTA MCP Servers

This guide is intended for AI assistants (like Claude) that will be using the TTA MCP servers through Augment.

## Available MCP Servers

The TTA project provides several MCP servers that you can use, categorized by their intended use:

### Development MCP Servers

These servers are for development and testing only and should not be used in production:

#### Basic Server (Development Only)

The basic server provides simple utilities for development and testing:

- **Echo Tool**: Echoes a message back to you
  - Usage: `echo(message: str) -> str`

- **Calculate Tool**: Safely evaluates a mathematical expression
  - Usage: `calculate(expression: str) -> str`

- **Resources**:
  - `info://server`: Information about the server
  - `info://system`: Basic system information
  - `info://environment/{var_name}`: Access to environment variables

### Production/Prototype MCP Servers

These servers are designed for use in production or prototype environments:

#### Agent Tool Server (Production Ready)

The agent tool server allows you to interact with TTA agents:

- **List Agents Tool**: Lists all available agents
  - Usage: `list_agents() -> str`

- **Get Agent Info Tool**: Gets detailed information about a specific agent
  - Usage: `get_agent_info(agent_id: str) -> str`

- **Process With Agent Tool**: Processes a goal using a specific agent
  - Usage: `process_with_agent(agent_id: str, goal: str, context: Optional[Dict[str, Any]]) -> str`

- **Resources**:
  - `agents://list`: List of all available agents
  - `agents://{agent_id}/info`: Information about a specific agent

#### Knowledge Resource Server (Production Ready)

The knowledge resource server allows you to access the TTA knowledge graph:

- **Query Knowledge Graph Tool**: Executes a Cypher query against the knowledge graph
  - Usage: `query_knowledge_graph(query: str, params: Optional[Dict[str, Any]]) -> str`

- **Get Entity By Name Tool**: Gets an entity from the knowledge graph by its name
  - Usage: `get_entity_by_name(entity_type: str, name: str) -> str`

- **Resources**:
  - `knowledge://locations`: List of all locations
  - `knowledge://characters`: List of all characters
  - `knowledge://items`: List of all items
  - `knowledge://{entity_type}/{name}`: Information about a specific entity

## How to Use These Servers

### Focus on Production Servers

As an AI assistant, you should primarily use the production-ready servers:
- Agent Tool Server
- Knowledge Resource Server

The Basic Server should only be used for development and testing purposes, not in production environments.

When a user asks you to perform a task that requires accessing TTA agents or the knowledge graph, you should:

1. **Identify the appropriate production server and tool/resource** for the task
2. **Use the tool or resource** to accomplish the task
3. **Present the results** to the user in a natural way

### Example: Creating a New Location

If a user asks you to create a new location:

1. Identify that you need to use the agent tool server's `process_with_agent` tool
2. Call the tool with:
   - `agent_id`: "world_building"
   - `goal`: "Create a new location"
   - `context`: Information about the desired location

3. Present the results to the user

### Example: Querying the Knowledge Graph

If a user asks about a character in the game:

1. Identify that you need to use the knowledge resource server
2. Either:
   - Read the `knowledge://characters` resource to get all characters
   - Read the `knowledge://{entity_type}/{name}` resource to get a specific character
   - Use the `query_knowledge_graph` tool for more complex queries

3. Present the results to the user

## Best Practices

1. **Use production servers** for real tasks, not development servers
2. **Be transparent** about using the MCP servers
3. **Handle errors gracefully** if a server or tool is not available
4. **Provide context** about what you're doing and why
5. **Use the most appropriate tool** for the task
6. **Format results** in a user-friendly way

## Limitations

1. MCP servers must be running for you to access them
2. Some operations may take time to complete
3. The knowledge graph may not contain all information
4. Agents may have limitations in what they can do

By following this guide, you'll be able to effectively use the TTA MCP servers to help users interact with the TTA project's agents and knowledge graph.


---
**Logseq:** [[TTA.dev/_archive/Nested_copies/Framework/Docs/Mcp/Ai_assistant_guide]]
