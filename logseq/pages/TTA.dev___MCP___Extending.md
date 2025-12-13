type:: [[Guide]]
category:: [[MCP]], [[Development]], [[Extension]]
difficulty:: [[Intermediate]]
estimated-time:: 30 minutes
target-audience:: [[Developers]]

---

# Extending MCP Servers in TTA.dev

**Guide for creating and extending MCP servers**

---

## Development vs Production Servers
id:: mcp-extending-server-types

**Development Servers:**

- Used for testing, learning, and development
- Should NOT be used in production environments
- Example: `basic_server.py`

**Production Servers:**

- Designed for production or prototype environments
- Must be robust, well-tested, and secure
- Examples: `agent_tool_server.py`, `knowledge_resource_server.py`

**Label your servers clearly** as either development or production.

---

## Creating a New MCP Server
id:: mcp-extending-new-server

### Basic Structure
id:: mcp-extending-basic-structure

**1. Import necessary modules:**

```python
from fastmcp import FastMCP, Context
from typing import Dict, List, Any, Optional
```

**2. Create a FastMCP instance:**

```python
mcp = FastMCP(
    "My Server",
    description="My MCP server description",
    dependencies=["fastmcp", "other-dependencies"]
)
```

**3. Define tools, resources, and prompts:**

```python
@mcp.tool()
def my_tool(param: str) -> str:
    """My tool description"""
    return f"Result: {param}"

@mcp.resource("my://resource")
def my_resource() -> str:
    """My resource description"""
    return "Resource content"

@mcp.prompt()
def my_prompt() -> str:
    """My prompt description"""
    return "Prompt content"
```

**4. Run the server:**

```python
if __name__ == "__main__":
    mcp.run()
```

---

## Adding Tools
id:: mcp-extending-tools

Tools are functions that can be called by the LLM.

**Requirements:**

- Clear, descriptive names
- Well-documented parameters and return types
- Detailed docstrings explaining purpose and usage

**Example:**

```python
@mcp.tool()
def search_knowledge_graph(query: str, limit: int = 10) -> str:
    """
    Search the knowledge graph for entities matching the query.

    Args:
        query: The search query
        limit: Maximum number of results to return (default: 10)

    Returns:
        A formatted string containing the search results
    """
    # Implementation...
    results = search_graph(query, limit)
    return format_results(results)
```

---

## Adding Resources
id:: mcp-extending-resources

Resources are file-like data that can be read by clients.

**Requirements:**

- Clear, descriptive URIs
- Return formatted text (Markdown recommended)
- Detailed docstrings explaining purpose and content

**Example:**

```python
@mcp.resource("knowledge://locations/{location_id}")
def get_location(location_id: str) -> str:
    """
    Get information about a specific location in the knowledge graph.

    Args:
        location_id: The ID of the location

    Returns:
        A formatted string containing information about the location
    """
    # Implementation...
    location = fetch_location(location_id)
    return f"""
# {location.name}

**Type:** {location.type}
**Description:** {location.description}

## Characters
{format_characters(location.characters)}

## Items
{format_items(location.items)}
"""
```

---

## Adding Prompts
id:: mcp-extending-prompts

Prompts are reusable templates for LLM interactions.

**Requirements:**

- Clear, descriptive names
- Well-formatted text
- Detailed docstrings explaining purpose and usage

**Example:**

```python
@mcp.prompt()
def location_exploration_prompt(location_name: str) -> str:
    """
    Create a prompt for exploring a location in the game world.

    Args:
        location_name: The name of the location to explore

    Returns:
        A prompt for exploring the location
    """
    return f"""
I'd like to explore {location_name} in the game world.

Please describe what I can see, hear, and experience in this location.
What characters might I encounter? What items might I find?
"""
```

---

## Extending Existing Servers
id:: mcp-extending-existing

### Adding New Capabilities

**1. Import the existing server:**

```python
from examples.mcp.basic_server import mcp
```

**2. Add new tools, resources, or prompts:**

```python
@mcp.tool()
def new_tool() -> str:
    """New tool description"""
    return "New tool result"
```

**3. Run the extended server:**

```python
if __name__ == "__main__":
    mcp.run()
```

### Customizing the Agent Adapter
id:: mcp-extending-adapter

```python
from src.mcp.agent_adapter import AgentMCPAdapter

class CustomAgentMCPAdapter(AgentMCPAdapter):
    def __init__(self, agent, **kwargs):
        super().__init__(agent, **kwargs)

        # Register additional tools
        self._register_custom_tools()

    def _register_custom_tools(self):
        @self.mcp.tool()
        def custom_tool() -> str:
            """Custom tool description"""
            return "Custom tool result"
```

---

## Best Practices
id:: mcp-extending-best-practices

### Security Considerations
id:: mcp-extending-security

**Essential security practices:**

1. **Validate inputs**: Always validate and sanitize inputs to prevent injection attacks
2. **Limit capabilities**: Only expose the minimum necessary capabilities
3. **Use proper authentication**: Implement authentication for sensitive data access
4. **Sanitize outputs**: Ensure sensitive information is not leaked in outputs

**Example input validation:**

```python
@mcp.tool()
def search_database(query: str) -> str:
    """Search database with validation"""
    # Validate input
    if not query or len(query) > 1000:
        raise ValueError("Query must be 1-1000 characters")

    # Sanitize to prevent SQL injection
    safe_query = sanitize_sql(query)

    return execute_search(safe_query)
```

### Performance Considerations
id:: mcp-extending-performance

**Performance optimization:**

1. **Keep tools lightweight**: Tools should execute quickly to avoid timeouts
2. **Cache expensive operations**: Cache results for repeated operations
3. **Use async where appropriate**: For I/O-bound operations, use async functions
4. **Limit resource size**: Return reasonably sized data to avoid overwhelming LLM

**Example caching:**

```python
from functools import lru_cache

@lru_cache(maxsize=100)
def get_cached_location(location_id: str) -> dict:
    """Cached location retrieval"""
    return fetch_location_from_db(location_id)

@mcp.tool()
def get_location_info(location_id: str) -> str:
    """Get location with caching"""
    location = get_cached_location(location_id)
    return format_location(location)
```

### Documentation
id:: mcp-extending-documentation

**Documentation requirements:**

1. **Detailed docstrings**: Include for all tools, resources, and prompts
2. **Usage examples**: Provide examples of how to use your server
3. **Error handling**: Document how errors are handled and error messages
4. **Dependencies**: Clearly document all dependencies and installation
5. **Development/Production Status**: Clearly indicate server status

### Production Readiness
id:: mcp-extending-production

**Production server checklist:**

- [ ] Comprehensive error handling for all possible error conditions
- [ ] Input validation to prevent security issues
- [ ] Proper logging for debugging and monitoring
- [ ] Tests to verify server functionality
- [ ] Clear documentation for users
- [ ] Containerization for easier deployment
- [ ] Health checks and monitoring

**Example production-ready server:**

```python
import logging
from fastmcp import FastMCP

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

mcp = FastMCP("Production Server")

@mcp.tool()
def production_tool(param: str) -> str:
    """Production-ready tool with error handling"""
    try:
        # Validate input
        if not param:
            raise ValueError("Parameter is required")

        # Log operation
        logger.info(f"Processing: {param}")

        # Execute operation
        result = process_param(param)

        # Log success
        logger.info(f"Success: {result}")

        return result

    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise RuntimeError(f"Failed to process: {e}")

if __name__ == "__main__":
    mcp.run()
```

---

## Advanced Topics
id:: mcp-extending-advanced

### Using Context
id:: mcp-extending-context

The `Context` object provides access to MCP capabilities:

```python
@mcp.tool()
async def long_task(files: list[str], ctx: Context) -> str:
    """Process multiple files with progress tracking"""
    for i, file in enumerate(files):
        # Report progress
        ctx.info(f"Processing {file}")
        await ctx.report_progress(i, len(files))

        # Read another resource if needed
        data = await ctx.read_resource(f"file://{file}")

        # Process data...

    return "Processing complete"
```

### Working with Images
id:: mcp-extending-images

FastMCP provides an `Image` class for handling images:

```python
from fastmcp import FastMCP, Image
from PIL import Image as PILImage

@mcp.tool()
def create_thumbnail(image_path: str) -> Image:
    """Create a thumbnail from an image"""
    img = PILImage.open(image_path)
    img.thumbnail((100, 100))

    # FastMCP automatically handles conversion and MIME types
    return Image(data=img.tobytes(), format="png")
```

### Custom Transports
id:: mcp-extending-transports

By default, MCP servers use stdio transport, but you can specify others:

```python
if __name__ == "__main__":
    # HTTP transport
    mcp.run(transport="http", host="localhost", port=8000)

    # Useful for certain integration scenarios
```

---

## Key Takeaways
id:: mcp-extending-summary

**Creating MCP Servers:**

1. **Structure**: FastMCP instance → Define tools/resources/prompts → Run server
2. **Tools**: Functions callable by LLM (clear names, docs, validation)
3. **Resources**: File-like data (URIs, formatted text, detailed docs)
4. **Prompts**: Reusable templates for LLM interactions

**Best Practices:**

- **Security**: Validate inputs, limit capabilities, sanitize outputs
- **Performance**: Keep tools lightweight, cache expensive operations, use async
- **Documentation**: Detailed docstrings, usage examples, error handling docs
- **Production**: Error handling, logging, testing, monitoring, containerization

**Advanced Features:**

- **Context**: Progress tracking, resource reading, info logging
- **Images**: Built-in image handling with automatic conversion
- **Transports**: HTTP alternative to stdio for certain scenarios

---

## Related Documentation

- [[TTA.dev/MCP/README]] - MCP overview and architecture
- [[TTA.dev/MCP/Usage]] - Running and using MCP servers
- [[TTA.dev/MCP/Integration]] - Integration patterns with primitives
- [[TTA.dev/MCP/AI Assistant Guide]] - Guide for AI assistants
- [Model Context Protocol Documentation](https://modelcontextprotocol.io)
- [FastMCP Documentation](https://github.com/jlowin/fastmcp)

---

**Last Updated:** October 30, 2025
**Status:** Production Ready
**Maintained by:** TTA.dev Team


---
**Logseq:** [[TTA.dev/Logseq/Pages/Tta.dev___mcp___extending]]
