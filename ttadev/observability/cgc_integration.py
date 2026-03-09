"""CodeGraphContext integration for observability dashboard."""

import asyncio
import json
from typing import Any
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


class CGCIntegration:
    """Integration with CodeGraphContext MCP server."""
    
    def __init__(self):
        self.server_params = StdioServerParameters(
            command='uv',
            args=['run', '--python', '3.12', 'cgc', 'mcp', 'start'],
            env=None
        )
    
    async def get_repository_stats(self) -> dict[str, Any]:
        """Get statistics about the indexed repository."""
        async with stdio_client(self.server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                
                result = await session.call_tool('get_repository_stats', {})
                return json.loads(result.content[0].text)
    
    async def find_code(self, keyword: str) -> list[dict[str, Any]]:
        """Find code snippets related to a keyword."""
        async with stdio_client(self.server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                
                result = await session.call_tool('find_code', {'keyword': keyword})
                return json.loads(result.content[0].text)
    
    async def analyze_relationships(self, query_type: str, target: str) -> dict[str, Any]:
        """Analyze code relationships."""
        async with stdio_client(self.server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                
                result = await session.call_tool('analyze_code_relationships', {
                    'query_type': query_type,
                    'target': target
                })
                return json.loads(result.content[0].text)
    
    async def get_graph_visualization(self, cypher_query: str) -> str:
        """Get a URL to visualize a Cypher query."""
        async with stdio_client(self.server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                
                result = await session.call_tool('visualize_graph_query', {
                    'query': cypher_query
                })
                return result.content[0].text
    
    async def get_primitives_graph(self) -> dict[str, Any]:
        """Get graph data for all primitives in the codebase."""
        # Query for all primitive classes and their relationships
        cypher = """
        MATCH (c:Class)
        WHERE c.name CONTAINS 'Primitive'
        OPTIONAL MATCH (c)-[r:CALLS|INHERITS]->(related)
        RETURN c, r, related
        LIMIT 100
        """
        
        async with stdio_client(self.server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                
                result = await session.call_tool('execute_cypher_query', {
                    'query': cypher
                })
                return json.loads(result.content[0].text)
    
    async def get_agent_files(self) -> list[dict[str, Any]]:
        """Get all files related to agents."""
        async with stdio_client(self.server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                
                result = await session.call_tool('find_code', {'keyword': 'agent'})
                return json.loads(result.content[0].text)
    
    async def get_workflow_files(self) -> list[dict[str, Any]]:
        """Get all files related to workflows."""
        async with stdio_client(self.server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                
                result = await session.call_tool('find_code', {'keyword': 'workflow'})
                return json.loads(result.content[0].text)
