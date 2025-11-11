---
type: [[Guide]]
category: [[MCP]], [[AI Assistants]], [[Best Practices]]
difficulty: [[Beginner]]
estimated-time: 15 minutes
target-audience: [[AI Assistants]], [[Developers]]
---

# AI Assistant Guide to TTA MCP Servers

**Guide for AI assistants using TTA MCP servers through Augment/Cline**

---

## Overview
id:: mcp-ai-assistant-overview

This guide helps AI assistants (Claude, GPT-4, etc.) effectively use TTA MCP servers for:

- **Agent interaction** - Process goals with TTA agents
- **Knowledge graph access** - Query Neo4j knowledge graph
- **System information** - Access environment and configuration
- **Development tools** - Testing and debugging capabilities

**Target audience:** AI assistants integrated through Augment or Cline

---

## Available MCP Servers
id:: mcp-ai-assistant-servers

### Development MCP Servers
id:: mcp-ai-assistant-dev-servers

**⚠️ For development and testing only - NOT for production**

#### Basic Server (Development Only)
id:: mcp-ai-assistant-basic-server

**Simple utilities for testing:**

**Tools:**

- **`echo(message: str) -> str`**
  - Echoes message back
  - Use for: Testing MCP connectivity

- **`calculate(expression: str) -> str`**
  - Safely evaluates math expressions
  - Use for: Testing tool execution

**Resources:**

- `info://server` - Server information
- `info://system` - System information
- `info://environment/{var_name}` - Environment variables

**When to use:** Development, connectivity testing, MCP debugging

**When NOT to use:** Production tasks, real agent interaction

---

### Production/Prototype MCP Servers
id:: mcp-ai-assistant-production-servers

**✅ Production-ready servers for real tasks**

#### Agent Tool Server (Production Ready)
id:: mcp-ai-assistant-agent-server

**Interact with TTA agents:**

**Tools:**

- **`list_agents() -> str`**
  - Returns: List of all available agents with IDs and descriptions
  - Use for: Discovering available agents, agent selection

- **`get_agent_info(agent_id: str) -> str`**
  - Returns: Detailed agent information (capabilities, tools, configuration)
  - Use for: Understanding agent capabilities before use

- **`process_with_agent(agent_id: str, goal: str, context: Optional[Dict[str, Any]]) -> str`**
  - Returns: Agent's response to goal with context
  - Use for: Executing tasks through agents (world building, character creation, etc.)

**Resources:**

- `agents://list` - List of all agents
- `agents://{agent_id}/info` - Specific agent information

**Example usage:**

```python
# List available agents
agents = list_agents()

# Get world building agent info
info = get_agent_info("world_building")

# Create new location with context
result = process_with_agent(
    agent_id="world_building",
    goal="Create a new location",
    context={
        "location_type": "forest",
        "atmosphere": "mysterious",
        "size": "large"
    }
)
```

#### Knowledge Resource Server (Production Ready)
id:: mcp-ai-assistant-knowledge-server

**Access TTA knowledge graph:**

**Tools:**

- **`query_knowledge_graph(query: str, params: Optional[Dict[str, Any]]) -> str`**
  - Returns: Cypher query results from Neo4j
  - Use for: Complex queries, custom data retrieval

- **`get_entity_by_name(entity_type: str, name: str) -> str`**
  - Returns: Entity information from knowledge graph
  - Use for: Retrieving specific entities (locations, characters, items)

**Resources:**

- `knowledge://locations` - All locations
- `knowledge://characters` - All characters
- `knowledge://items` - All items
- `knowledge://{entity_type}/{name}` - Specific entity information

**Example usage:**

```python
# Query all forest locations
locations = query_knowledge_graph(
    query="MATCH (l:Location {type: $type}) RETURN l",
    params={"type": "forest"}
)

# Get specific character
character = get_entity_by_name("Character", "Elara")

# Read all characters resource
all_characters = read_resource("knowledge://characters")
```

---

## How to Use These Servers
id:: mcp-ai-assistant-usage

### Focus on Production Servers
id:: mcp-ai-assistant-focus-production

**Priority order:**

1. **Production servers** (Agent Tool, Knowledge Resource)
   - For: Real user tasks, production workflows
   - Examples: Creating content, querying data, agent interaction

2. **Development servers** (Basic)
   - For: Testing connectivity, debugging MCP
   - Examples: Echo tests, environment checks

**Decision tree:**

```
User Task
│
├─ Requires agent interaction?
│  └─ Use: Agent Tool Server (production)
│
├─ Requires knowledge graph data?
│  └─ Use: Knowledge Resource Server (production)
│
├─ Testing MCP connectivity?
│  └─ Use: Basic Server (development only)
│
└─ Other task?
   └─ Use: Appropriate TTA primitive or tool
```

### Task Workflow
id:: mcp-ai-assistant-workflow

**When user requests a task:**

**Step 1: Identify the appropriate server and tool**

- Agent interaction → Agent Tool Server
- Knowledge graph query → Knowledge Resource Server
- MCP testing → Basic Server (dev only)

**Step 2: Prepare the request**

- Gather required parameters
- Format context appropriately
- Validate inputs

**Step 3: Execute the tool or read the resource**

- Call tool with parameters
- Read resource with appropriate URI
- Handle errors gracefully

**Step 4: Present results naturally**

- Format output for user
- Explain what was done
- Suggest next steps if appropriate

---

## Usage Examples
id:: mcp-ai-assistant-examples

### Example 1: Creating a New Location
id:: mcp-ai-assistant-example-location

**User request:** "Create a mysterious forest location with ancient ruins"

**Your approach:**

```python
# 1. Identify server: Agent Tool Server (production)
# 2. Prepare request
agent_id = "world_building"
goal = "Create a new location"
context = {
    "location_type": "forest",
    "atmosphere": "mysterious",
    "features": ["ancient ruins"],
    "size": "large"
}

# 3. Execute
result = process_with_agent(
    agent_id=agent_id,
    goal=goal,
    context=context
)

# 4. Present results
# "I've created a mysterious forest location with ancient ruins using the world building agent. Here's what was generated: [result]"
```

### Example 2: Querying Characters
id:: mcp-ai-assistant-example-characters

**User request:** "Show me all warrior characters"

**Your approach:**

```python
# Option 1: Use query tool for complex filtering
result = query_knowledge_graph(
    query="MATCH (c:Character {class: $class}) RETURN c",
    params={"class": "warrior"}
)

# Option 2: Read all characters and filter
all_characters = read_resource("knowledge://characters")
# Filter warrior characters from response

# Option 3: Get specific character
warrior = get_entity_by_name("Character", "warrior_name")
```

### Example 3: Agent Discovery
id:: mcp-ai-assistant-example-discovery

**User request:** "What agents are available?"

**Your approach:**

```python
# 1. List all agents
agents = list_agents()

# 2. Get detailed info for interesting agents
info = get_agent_info("world_building")

# 3. Present results
# "Available agents: [list]. The world building agent can help you create locations, characters, and world lore."
```

---

## Best Practices
id:: mcp-ai-assistant-best-practices

### Production vs Development
id:: mcp-ai-assistant-best-practices-production

**✅ DO:**

- Use production servers (Agent Tool, Knowledge Resource) for real tasks
- Use development servers (Basic) only for testing/debugging
- Clearly communicate which server you're using

**❌ DON'T:**

- Use Basic Server for production tasks
- Rely on development servers for user-facing features
- Mix development and production in same workflow

### Transparency
id:: mcp-ai-assistant-best-practices-transparency

**✅ DO:**

- Tell users when you're using MCP servers
- Explain what you're doing: "I'll query the knowledge graph for that information"
- Be clear about limitations: "The agent may take a moment to process this"

**❌ DON'T:**

- Hide MCP usage from users
- Present MCP results without context
- Over-promise agent capabilities

### Error Handling
id:: mcp-ai-assistant-best-practices-errors

**✅ DO:**

```python
try:
    result = process_with_agent(agent_id, goal, context)
    # Present result
except Exception as e:
    # Graceful fallback
    "I encountered an issue with the agent. Let me try an alternative approach..."
```

**❌ DON'T:**

- Crash on MCP server unavailability
- Show raw error messages to users
- Give up without trying alternatives

### Context Provision
id:: mcp-ai-assistant-best-practices-context

**✅ DO:**

- Provide rich context to agents:
  ```python
  context = {
      "user_preference": "high fantasy",
      "previous_locations": [...],
      "world_theme": "medieval"
  }
  ```

**❌ DON'T:**

- Send minimal or no context
- Assume agents know user preferences
- Omit relevant information

### Tool Selection
id:: mcp-ai-assistant-best-practices-tools

**Choose the right tool for the task:**

| Task | Best Tool | Why |
|------|-----------|-----|
| Create content | `process_with_agent` | Leverages agent capabilities |
| Query data | `query_knowledge_graph` | Direct database access |
| Get entity | `get_entity_by_name` | Optimized for single entities |
| List entities | Read resource | Efficient for lists |
| Test MCP | `echo` | Simple connectivity check |

### Result Formatting
id:: mcp-ai-assistant-best-practices-formatting

**✅ DO:**

```
"I've created a mysterious forest location using the world building agent.

**Location Details:**
- Name: Elderwood Forest
- Type: Ancient Forest
- Atmosphere: Mysterious and foreboding
- Features: Ancient ruins, glowing mushrooms, hidden pathways

Would you like me to add any characters or items to this location?"
```

**❌ DON'T:**

```
"{'status': 'success', 'data': {'location': {'name': 'Elderwood Forest', 'type': 'forest', ...}}}"
```

---

## Limitations
id:: mcp-ai-assistant-limitations

### Server Availability
id:: mcp-ai-assistant-limitations-availability

**Limitation:** MCP servers must be running for access

**Handling:**

```python
# Always check server availability
try:
    result = list_agents()
except Exception:
    "The agent server isn't currently running. You can start it with: python scripts/start_mcp_servers.py"
```

### Operation Duration
id:: mcp-ai-assistant-limitations-duration

**Limitation:** Some operations take time to complete

**Handling:**

- Inform users: "Processing with the agent, this may take a moment..."
- Set realistic expectations
- Provide progress updates if possible

### Knowledge Graph Completeness
id:: mcp-ai-assistant-limitations-knowledge

**Limitation:** Knowledge graph may not contain all information

**Handling:**

- Acknowledge gaps: "I don't see that character in the knowledge graph yet"
- Suggest alternatives: "Would you like me to create this character?"
- Don't assume completeness

### Agent Capabilities
id:: mcp-ai-assistant-limitations-agents

**Limitation:** Agents have specific capabilities and limitations

**Handling:**

- Use `get_agent_info` to understand capabilities
- Choose appropriate agent for task
- Fallback to other tools if agent can't help

---

## Key Takeaways
id:: mcp-ai-assistant-summary

**Server Priority:**

1. **Production servers** (Agent Tool, Knowledge Resource) for real tasks
2. **Development servers** (Basic) for testing only

**Usage Workflow:**

1. Identify appropriate server/tool
2. Prepare request with context
3. Execute and handle errors
4. Present results naturally

**Best Practices:**

- **Transparency**: Tell users what you're doing
- **Error handling**: Graceful fallbacks, no crashes
- **Context**: Provide rich context to agents
- **Tool selection**: Choose optimal tool for task
- **Formatting**: User-friendly results

**Production Tools:**

- `list_agents()` - Discover agents
- `get_agent_info(agent_id)` - Agent capabilities
- `process_with_agent(agent_id, goal, context)` - Execute with agent
- `query_knowledge_graph(query, params)` - Cypher queries
- `get_entity_by_name(type, name)` - Single entity retrieval

---

## Related Documentation

- [[TTA.dev/MCP/README]] - MCP overview and architecture
- [[TTA.dev/MCP/Usage]] - Running and using servers
- [[TTA.dev/MCP/Integration]] - Integration patterns
- [[TTA.dev/MCP/Extending]] - Creating custom servers
- [[TTA.dev/Primitives Catalog]] - Available TTA primitives

---

**Last Updated:** October 30, 2025
**Status:** Production Ready
**Maintained by:** TTA.dev Team
**Target:** AI Assistants (Claude, GPT-4, etc.)

- [[Project Hub]]