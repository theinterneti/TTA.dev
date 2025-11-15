# Extending MCP Servers in TTA

This guide explains how to extend and create new MCP servers for the TTA project.

## Development vs. Production Servers

When creating MCP servers, it's important to distinguish between development and production servers:

- **Development Servers**: Used for testing, learning, and development purposes. These servers should not be used in production environments.

- **Production Servers**: Designed for use in production or prototype environments. These servers should be robust, well-tested, and secure.

The examples in this guide can be used for both development and production servers, but you should clearly label your servers as either development or production.

## Creating a New MCP Server

### Basic Structure

To create a new MCP server, you need to:

1. Import the necessary modules:
   ```python
   from fastmcp import FastMCP, Context
   from typing import Dict, List, Any, Optional
   ```

2. Create a FastMCP instance:
   ```python
   mcp = FastMCP(
       "My Server",
       description="My MCP server description",
       dependencies=["fastmcp", "other-dependencies"]
   )
   ```

3. Define tools, resources, and prompts:
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

4. Run the server:
   ```python
   if __name__ == "__main__":
       mcp.run()
   ```

### Adding Tools

Tools are functions that can be called by the LLM. They should:

- Have clear, descriptive names
- Have well-documented parameters and return types
- Include detailed docstrings explaining their purpose and usage

Example:

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
    return results
```

### Adding Resources

Resources are file-like data that can be read by clients. They should:

- Have clear, descriptive URIs
- Return formatted text (Markdown is recommended)
- Include detailed docstrings explaining their purpose and content

Example:

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
    return formatted_location_info
```

### Adding Prompts

Prompts are reusable templates for LLM interactions. They should:

- Have clear, descriptive names
- Return well-formatted text
- Include detailed docstrings explaining their purpose and usage

Example:

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

## Extending Existing MCP Servers

### Adding New Capabilities

To add new capabilities to an existing MCP server:

1. Import the existing server:
   ```python
   from examples.mcp.basic_server import mcp
   ```

2. Add new tools, resources, or prompts:
   ```python
   @mcp.tool()
   def new_tool() -> str:
       """New tool description"""
       return "New tool result"
   ```

3. Run the extended server:
   ```python
   if __name__ == "__main__":
       mcp.run()
   ```

### Customizing the Agent Adapter

The `AgentMCPAdapter` can be customized to expose additional agent capabilities:

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

## Best Practices

### Security Considerations

When creating MCP servers, consider these security best practices:

1. **Validate inputs**: Always validate and sanitize inputs to prevent injection attacks.
2. **Limit capabilities**: Only expose the minimum necessary capabilities.
3. **Use proper authentication**: If your server accesses sensitive data, implement proper authentication.
4. **Sanitize outputs**: Ensure that sensitive information is not leaked in outputs.

### Performance Considerations

To ensure good performance:

1. **Keep tools lightweight**: Tools should execute quickly to avoid timeouts.
2. **Cache expensive operations**: If a tool performs expensive operations, consider caching results.
3. **Use async where appropriate**: For I/O-bound operations, use async functions.
4. **Limit resource size**: Resources should return reasonably sized data to avoid overwhelming the LLM.

### Documentation

Good documentation is essential:

1. **Detailed docstrings**: Include detailed docstrings for all tools, resources, and prompts.
2. **Usage examples**: Provide examples of how to use your server.
3. **Error handling**: Document how errors are handled and what error messages mean.
4. **Dependencies**: Clearly document all dependencies and how to install them.
5. **Development/Production Status**: Clearly indicate whether the server is intended for development or production use.

### Production Readiness

For production servers, ensure:

1. **Comprehensive error handling**: All possible error conditions should be handled gracefully.
2. **Input validation**: Validate all inputs to prevent security issues.
3. **Logging**: Implement proper logging for debugging and monitoring.
4. **Testing**: Write tests to verify server functionality.
5. **Documentation**: Provide clear documentation for users.
6. **Containerization**: Consider containerizing the server for easier deployment.
7. **Monitoring**: Implement health checks and monitoring.

## Advanced Topics

### Using Context

The `Context` object provides access to MCP capabilities:

```python
@mcp.tool()
async def long_task(files: list[str], ctx: Context) -> str:
    """Process multiple files with progress tracking"""
    for i, file in enumerate(files):
        ctx.info(f"Processing {file}")
        await ctx.report_progress(i, len(files))

        # Read another resource if needed
        data = await ctx.read_resource(f"file://{file}")

    return "Processing complete"
```

### Working with Images

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

By default, MCP servers use the stdio transport, but you can specify other transports:

```python
if __name__ == "__main__":
    mcp.run(transport="http", host="localhost", port=8000)
```

This allows you to expose your MCP server over HTTP, which can be useful for certain integration scenarios.
