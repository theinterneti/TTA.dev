"""MCP Code Execution Primitive.

Revolutionary MCP integration using code execution for 98.7% token reduction.
Based on Anthropic research: https://www.anthropic.com/engineering/code-execution-with-mcp

This primitive extends CodeExecutionPrimitive to provide:
- Progressive tool discovery via filesystem exploration
- Context-efficient results (filter/transform in execution environment)
- Skills persistence and reuse
- State management across operations
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime
from typing import Any, TypedDict

from tta_dev_primitives.core.base import WorkflowContext
from tta_dev_primitives.integrations.e2b_primitive import (
    CodeExecutionPrimitive,
    CodeInput,
    CodeOutput,
)

logger = logging.getLogger(__name__)


class MCPServerConfig(TypedDict, total=False):
    """Configuration for an MCP server."""

    name: str
    tools: list[dict[str, Any]]
    transport: str  # "stdio", "http", etc.
    endpoint: str | None
    description: str


class MCPCodeExecutionInput(CodeInput, total=False):
    """Extended input for MCP code execution."""

    available_servers: list[str] | None
    enable_skills: bool
    workspace_data: dict[str, Any] | None


class MCPCodeExecutionPrimitive(CodeExecutionPrimitive):
    """Code execution with MCP server integration.

    Features:
    - Progressive MCP tool discovery via filesystem
    - 98.7% token reduction for complex workflows
    - Skills persistence for reusable patterns
    - State management across operations
    - Context-efficient data processing

    Example:
        ```python
        executor = MCPCodeExecutionPrimitive(
            available_servers=["context7", "grafana"],
            enable_skills=True
        )

        # Agent writes code to interact with MCP servers
        code = '''
        from servers.grafana import query_prometheus

        # Query metrics efficiently
        metrics = await query_prometheus({
            'query': 'http_requests_total[5m]'
        })

        # Filter in execution environment (not model context)
        high_traffic = [m for m in metrics if m['value'] > 1000]

        # Only summary to model
        print(f"Found {len(high_traffic)} high-traffic endpoints")
        '''

        result = await executor.execute({"code": code}, context)
        ```
    """

    def __init__(
        self,
        available_servers: list[str] | None = None,
        enable_skills: bool = True,
        skills_dir: str = "./skills",
        workspace_dir: str = "./workspace",
        mcp_servers_config: dict[str, MCPServerConfig] | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize MCP code execution primitive.

        Args:
            available_servers: List of MCP servers to make available
            enable_skills: Whether to enable skills persistence
            skills_dir: Directory for skill storage in execution environment
            workspace_dir: Directory for state persistence
            mcp_servers_config: Configuration for MCP servers
            **kwargs: Additional arguments passed to CodeExecutionPrimitive
        """
        super().__init__(**kwargs)

        self.available_servers = available_servers or ["context7", "grafana", "pylance"]
        self.enable_skills = enable_skills
        self.skills_dir = skills_dir
        self.workspace_dir = workspace_dir

        # Default MCP server configurations
        self.mcp_servers_config = mcp_servers_config or self._get_default_server_config()

        # Track generated filesystem for cleanup
        self._generated_files: list[str] = []

    def _get_default_server_config(self) -> dict[str, MCPServerConfig]:
        """Get default configuration for known MCP servers."""
        return {
            "context7": {
                "name": "context7",
                "description": "Library documentation lookup",
                "transport": "http",
                "tools": [
                    {
                        "name": "resolve_library_id",
                        "description": "Find library ID from name",
                        "parameters": {"library_name": "string"},
                    },
                    {
                        "name": "get_library_docs",
                        "description": "Get documentation for library",
                        "parameters": {"context7_compatible_library_id": "string"},
                    },
                ],
            },
            "grafana": {
                "name": "grafana",
                "description": "Observability and monitoring",
                "transport": "http",
                "tools": [
                    {
                        "name": "query_prometheus",
                        "description": "Execute PromQL query",
                        "parameters": {"query": "string", "time_range": "string"},
                    },
                    {
                        "name": "get_dashboard",
                        "description": "Retrieve dashboard configuration",
                        "parameters": {"dashboard_uid": "string"},
                    },
                    {
                        "name": "query_loki",
                        "description": "Execute LogQL query for logs",
                        "parameters": {"query": "string", "time_range": "string"},
                    },
                ],
            },
            "pylance": {
                "name": "pylance",
                "description": "Python language analysis",
                "transport": "http",
                "tools": [
                    {
                        "name": "check_syntax",
                        "description": "Check Python syntax errors",
                        "parameters": {"file_path": "string"},
                    },
                    {
                        "name": "run_code_snippet",
                        "description": "Execute Python code snippet",
                        "parameters": {"code": "string"},
                    },
                    {
                        "name": "analyze_imports",
                        "description": "Analyze import dependencies",
                        "parameters": {"file_path": "string"},
                    },
                ],
            },
            "github_pr": {
                "name": "github_pr",
                "description": "GitHub pull request operations",
                "transport": "http",
                "tools": [
                    {
                        "name": "get_active_pr",
                        "description": "Get current active pull request",
                        "parameters": {},
                    },
                    {
                        "name": "create_pr_comment",
                        "description": "Create comment on pull request",
                        "parameters": {"comment": "string", "pr_number": "number"},
                    },
                ],
            },
        }

    async def _execute_impl(
        self, input_data: MCPCodeExecutionInput, context: WorkflowContext
    ) -> CodeOutput:
        """Execute code with MCP server integration.

        Sets up MCP filesystem structure, skills directory, and workspace
        before executing the provided code.
        """
        # Update available servers from input if provided
        if input_data.get("available_servers"):
            self.available_servers = input_data["available_servers"]

        # Update skills setting if provided
        if "enable_skills" in input_data:
            self.enable_skills = input_data["enable_skills"]

        # Setup MCP environment before execution
        await self._setup_mcp_environment(input_data.get("workspace_data"))

        try:
            # Execute code with MCP capabilities
            result = await super()._execute_impl(input_data, context)

            # Enhance result with MCP context
            enhanced_result = dict(result)
            enhanced_result["mcp_servers"] = self.available_servers
            enhanced_result["skills_enabled"] = self.enable_skills

            return enhanced_result

        finally:
            # Cleanup generated files if needed
            await self._cleanup_generated_files()

    async def _setup_mcp_environment(self, workspace_data: dict[str, Any] | None = None) -> None:
        """Setup MCP execution environment.

        Creates:
        - servers/ directory with MCP tool modules
        - skills/ directory for persistent skills
        - workspace/ directory for state management
        """
        if not self._sandbox:
            await self._create_sandbox()

        if not self._sandbox:
            raise RuntimeError("Failed to create sandbox for MCP setup")

        # Generate MCP filesystem structure
        mcp_filesystem = await self._generate_mcp_filesystem()

        # Create server directories and tool files
        for file_path, content in mcp_filesystem.items():
            await self._create_file_in_sandbox(file_path, content)

        # Setup skills directory
        if self.enable_skills:
            await self._setup_skills_directory()

        # Setup workspace directory
        await self._setup_workspace_directory(workspace_data)

        logger.info(
            f"MCP environment setup complete: {len(self.available_servers)} servers, "
            f"skills={'enabled' if self.enable_skills else 'disabled'}"
        )

    async def _generate_mcp_filesystem(self) -> dict[str, str]:
        """Generate filesystem structure for MCP servers.

        Returns:
            dict: Mapping of file paths to Python code content
        """
        filesystem: dict[str, str] = {}

        # Create base MCP client
        filesystem["mcp_client.py"] = self._generate_mcp_client_code()

        # Generate server directories and tools
        for server_name in self.available_servers:
            if server_name not in self.mcp_servers_config:
                logger.warning(f"Unknown MCP server: {server_name}")
                continue

            server_config = self.mcp_servers_config[server_name]
            server_base = f"servers/{server_name}"

            # Generate tool files
            for tool in server_config["tools"]:
                tool_file = f"{server_base}/{tool['name']}.py"
                filesystem[tool_file] = self._generate_tool_code(server_name, tool)

            # Generate server index
            filesystem[f"{server_base}/__init__.py"] = self._generate_server_index(
                server_name, server_config
            )

        # Generate search_tools utility (progressive discovery)
        filesystem["search_tools.py"] = self._generate_search_tools_code()

        return filesystem

    def _generate_mcp_client_code(self) -> str:
        """Generate the base MCP client code."""
        return '''"""MCP Client for code execution environment.

This module provides the bridge between generated tool code and actual MCP servers.
It handles the protocol communication and error handling.
"""

import asyncio
import json
import logging
from typing import Any

logger = logging.getLogger(__name__)

# In a real implementation, this would connect to actual MCP servers
# For now, we'll simulate the responses for demonstration

async def call_mcp_tool(server: str, tool: str, input_data: dict[str, Any]) -> dict[str, Any]:
    """Call MCP tool via appropriate transport.

    Args:
        server: Name of MCP server
        tool: Name of tool to call
        input_data: Tool input parameters

    Returns:
        Tool execution results

    Raises:
        ConnectionError: If MCP server is unreachable
        ValueError: If tool or server not found
    """
    logger.info(f"Calling MCP tool: {server}.{tool}")

    try:
        # Simulate MCP protocol communication
        # In real implementation, this would use stdio, http, or other transport

        if server == "context7":
            return await _handle_context7_call(tool, input_data)
        elif server == "grafana":
            return await _handle_grafana_call(tool, input_data)
        elif server == "pylance":
            return await _handle_pylance_call(tool, input_data)
        elif server == "github_pr":
            return await _handle_github_pr_call(tool, input_data)
        else:
            raise ValueError(f"Unknown MCP server: {server}")

    except Exception as e:
        logger.error(f"MCP call failed: {server}.{tool} - {e}")
        raise

async def _handle_context7_call(tool: str, input_data: dict[str, Any]) -> dict[str, Any]:
    """Handle Context7 MCP server calls."""
    if tool == "resolve_library_id":
        # Mock implementation
        library_name = input_data.get("library_name", "")
        return {
            "library_id": f"/org/{library_name.lower()}",
            "success": True
        }
    elif tool == "get_library_docs":
        # Mock implementation
        return {
            "documentation": f"Documentation for {input_data.get('context7_compatible_library_id', 'unknown')}",
            "success": True
        }
    else:
        raise ValueError(f"Unknown Context7 tool: {tool}")

async def _handle_grafana_call(tool: str, input_data: dict[str, Any]) -> dict[str, Any]:
    """Handle Grafana MCP server calls."""
    if tool == "query_prometheus":
        # Mock Prometheus response
        return {
            "results": [
                {"metric": {"job": "api"}, "value": [1699123456, "123.45"]},
                {"metric": {"job": "web"}, "value": [1699123456, "67.89"]}
            ],
            "success": True
        }
    elif tool == "query_loki":
        # Mock Loki response
        return {
            "logs": [
                {"timestamp": "2024-11-10T10:00:00Z", "line": "INFO: Request processed"},
                {"timestamp": "2024-11-10T10:01:00Z", "line": "ERROR: Database timeout"}
            ],
            "success": True
        }
    elif tool == "get_dashboard":
        # Mock dashboard response
        return {
            "dashboard": {
                "title": "API Metrics",
                "panels": [{"title": "Request Rate", "type": "graph"}]
            },
            "success": True
        }
    else:
        raise ValueError(f"Unknown Grafana tool: {tool}")

async def _handle_pylance_call(tool: str, input_data: dict[str, Any]) -> dict[str, Any]:
    """Handle Pylance MCP server calls."""
    if tool == "check_syntax":
        # Mock syntax check
        return {
            "errors": [],
            "warnings": [],
            "success": True
        }
    elif tool == "run_code_snippet":
        # Mock code execution
        return {
            "output": "Code executed successfully",
            "success": True
        }
    elif tool == "analyze_imports":
        # Mock import analysis
        return {
            "imports": ["os", "sys", "json"],
            "missing": [],
            "success": True
        }
    else:
        raise ValueError(f"Unknown Pylance tool: {tool}")

async def _handle_github_pr_call(tool: str, input_data: dict[str, Any]) -> dict[str, Any]:
    """Handle GitHub PR MCP server calls."""
    if tool == "get_active_pr":
        # Mock active PR
        return {
            "pr": {
                "number": 42,
                "title": "Add new feature",
                "author": "developer"
            },
            "success": True
        }
    elif tool == "create_pr_comment":
        # Mock comment creation
        return {
            "comment_id": 12345,
            "success": True
        }
    else:
        raise ValueError(f"Unknown GitHub PR tool: {tool}")
'''

    def _generate_tool_code(self, server_name: str, tool: dict[str, Any]) -> str:
        """Generate Python code for an MCP tool."""
        tool_name = tool["name"]
        description = tool.get("description", "")
        parameters = tool.get("parameters", {})

        # Generate parameter documentation
        param_docs = []
        for param_name, param_type in parameters.items():
            param_docs.append(f"        {param_name} ({param_type}): Parameter description")

        param_doc_str = "\n".join(param_docs) if param_docs else "        No parameters"

        return f'''"""Generated MCP tool: {server_name}.{tool_name}"""

from ..mcp_client import call_mcp_tool

async def {tool_name}(input_data: dict) -> dict:
    """{description}

    Args:
{param_doc_str}

    Returns:
        dict: Tool execution results

    Example:
        result = await {tool_name}({{"param": "value"}})
        print(result["success"])
    """
    return await call_mcp_tool(
        server="{server_name}",
        tool="{tool_name}",
        input_data=input_data
    )
'''

    def _generate_server_index(self, server_name: str, server_config: MCPServerConfig) -> str:
        """Generate __init__.py for MCP server module."""
        tools = server_config.get("tools", [])
        tool_imports = []
        tool_exports = []

        for tool in tools:
            tool_name = tool["name"]
            tool_imports.append(f"from .{tool_name} import {tool_name}")
            tool_exports.append(f'"{tool_name}"')

        imports_str = "\n".join(tool_imports)
        exports_str = ", ".join(tool_exports)

        return f'''"""MCP Server: {server_name}

{server_config.get("description", "No description available")}

Available tools:
{chr(10).join(f"- {tool['name']}: {tool.get('description', 'No description')}" for tool in tools)}
"""

{imports_str}

__all__ = [{exports_str}]

# Server metadata
SERVER_NAME = "{server_name}"
SERVER_DESCRIPTION = "{server_config.get("description", "")}"
AVAILABLE_TOOLS = {[tool["name"] for tool in tools]}
'''

    def _generate_search_tools_code(self) -> str:
        """Generate search_tools utility for progressive discovery."""
        return '''"""Progressive MCP tool discovery utilities.

This module provides functions for discovering available MCP tools
without loading all definitions upfront - enabling the 98.7% token reduction.
"""

import os
from typing import Any

def search_tools(query: str = "", detail_level: str = "name") -> list[dict[str, Any]]:
    """Search available MCP tools.

    Args:
        query: Search query (matches tool names and descriptions)
        detail_level: Level of detail to return
            - "name": Just tool names
            - "description": Names and descriptions
            - "full": Full tool definitions with parameters

    Returns:
        List of matching tools with requested detail level

    Example:
        # Find Grafana tools
        grafana_tools = search_tools("grafana", detail_level="description")

        # Find all monitoring tools
        monitoring_tools = search_tools("monitoring", detail_level="name")
    """
    tools = []

    # Scan servers directory
    servers_dir = "./servers"
    if not os.path.exists(servers_dir):
        return tools

    for server_name in os.listdir(servers_dir):
        server_path = f"{servers_dir}/{server_name}"
        if not os.path.isdir(server_path):
            continue

        # Skip if query doesn't match server name
        if query and query.lower() not in server_name.lower():
            continue

        # Find tools in server directory
        for file_name in os.listdir(server_path):
            if not file_name.endswith(".py") or file_name.startswith("__"):
                continue

            tool_name = file_name[:-3]  # Remove .py extension

            # Skip if query doesn't match tool name
            if query and query.lower() not in tool_name.lower():
                continue

            tool_info = {
                "server": server_name,
                "name": tool_name,
                "path": f"{server_path}/{file_name}"
            }

            if detail_level in ["description", "full"]:
                # Read description from docstring
                try:
                    with open(f"{server_path}/{file_name}", 'r') as f:
                        content = f.read()
                        # Extract docstring description
                        if '"""' in content:
                            start = content.find('"""') + 3
                            end = content.find('"""', start)
                            if end > start:
                                docstring = content[start:end].strip()
                                first_line = docstring.split('\\n')[0]
                                tool_info["description"] = first_line
                except Exception:
                    tool_info["description"] = "No description available"

            if detail_level == "full":
                # Add parameter information
                tool_info["parameters"] = "See tool file for parameters"

            tools.append(tool_info)

    return tools

def list_servers() -> list[str]:
    """List all available MCP servers.

    Returns:
        List of server names
    """
    servers_dir = "./servers"
    if not os.path.exists(servers_dir):
        return []

    return [
        name for name in os.listdir(servers_dir)
        if os.path.isdir(f"{servers_dir}/{name}")
    ]

def get_server_tools(server_name: str) -> list[str]:
    """Get all tools for a specific server.

    Args:
        server_name: Name of the MCP server

    Returns:
        List of tool names for the server
    """
    server_path = f"./servers/{server_name}"
    if not os.path.exists(server_path):
        return []

    tools = []
    for file_name in os.listdir(server_path):
        if file_name.endswith(".py") and not file_name.startswith("__"):
            tools.append(file_name[:-3])  # Remove .py extension

    return tools
'''

    async def _setup_skills_directory(self) -> None:
        """Setup skills directory for persistent code patterns."""
        if not self._sandbox:
            return

        # Create skills directory structure
        skills_init = '''"""Skills - Persistent MCP code patterns.

This directory contains reusable code patterns discovered and saved
by agents working with MCP servers. Each skill is a self-contained
function that can be imported and reused.

Example:
    from skills.analyze_error_spike import analyze_error_spike
    result = await analyze_error_spike('user-service', '2h')
"""

import os
from typing import Any

def list_skills() -> list[str]:
    """List all available skills."""
    skills_dir = os.path.dirname(__file__)
    skills = []

    for filename in os.listdir(skills_dir):
        if filename.endswith('.py') and not filename.startswith('__'):
            skills.append(filename[:-3])  # Remove .py extension

    return skills

def search_skills(query: str) -> list[dict[str, Any]]:
    """Search skills by name or description."""
    skills = []
    skills_dir = os.path.dirname(__file__)

    for filename in os.listdir(skills_dir):
        if not filename.endswith('.py') or filename.startswith('__'):
            continue

        skill_name = filename[:-3]
        if query.lower() in skill_name.lower():
            skills.append({
                'name': skill_name,
                'file': filename,
                'description': 'See skill file for description'
            })

    return skills
'''

        await self._create_file_in_sandbox("skills/__init__.py", skills_init)

        # Create example skill
        example_skill = '''"""Example Skill: Simple Grafana Query

This is an example of a reusable skill that can be saved and reused
across different agent sessions.
"""

from servers.grafana import query_prometheus

async def get_error_rate(service_name: str, time_window: str = "5m") -> dict:
    """Get error rate for a service.

    Args:
        service_name: Name of the service to check
        time_window: Time window for the query (e.g., "5m", "1h")

    Returns:
        dict: Error rate information
    """
    query = f'rate(http_requests_total{{service="{service_name}",status=~"5.."}[{time_window}])'

    result = await query_prometheus({
        'query': query,
        'time_range': '1h'
    })

    if result.get('success'):
        metrics = result.get('results', [])
        if metrics:
            error_rate = float(metrics[0]['value'][1])
            return {
                'service': service_name,
                'error_rate': error_rate,
                'status': 'high' if error_rate > 0.1 else 'normal',
                'time_window': time_window
            }

    return {
        'service': service_name,
        'error_rate': 0.0,
        'status': 'unknown',
        'time_window': time_window
    }
'''

        await self._create_file_in_sandbox("skills/example_error_rate.py", example_skill)

    async def _setup_workspace_directory(
        self, workspace_data: dict[str, Any] | None = None
    ) -> None:
        """Setup workspace directory for state persistence."""
        if not self._sandbox:
            return

        # Create workspace directory structure
        workspace_structure = {
            "workspace/README.md": """# Workspace Directory

This directory provides persistent state across MCP code execution sessions.

## Structure
- session_state.json - Current session state
- intermediate_results/ - Temporary data storage
- cached_data/ - Cached API responses
- logs/ - Execution logs

## Usage
```python
import json

# Load session state
with open('./workspace/session_state.json', 'r') as f:
    state = json.load(f)

# Save intermediate results
with open('./workspace/intermediate_results/analysis.json', 'w') as f:
    json.dump(analysis_data, f)
```
""",
            "workspace/session_state.json": json.dumps(
                {
                    "session_id": workspace_data.get("session_id", "unknown")
                    if workspace_data
                    else "unknown",
                    "created_at": datetime.now().isoformat(),
                    "data": workspace_data or {},
                },
                indent=2,
            ),
            "workspace/intermediate_results/.gitkeep": "",
            "workspace/cached_data/.gitkeep": "",
            "workspace/logs/.gitkeep": "",
        }

        for file_path, content in workspace_structure.items():
            await self._create_file_in_sandbox(file_path, content)

    async def _create_file_in_sandbox(self, file_path: str, content: str) -> None:
        """Create a file in the E2B sandbox."""
        if not self._sandbox:
            raise RuntimeError("Sandbox not available")

        # Create directory structure if needed
        dir_path = os.path.dirname(file_path)
        if dir_path and dir_path != ".":
            create_dir_code = f"""
import os
os.makedirs('{dir_path}', exist_ok=True)
"""
            await self._sandbox.run_code(create_dir_code)

        # Write file content
        write_file_code = f"""
with open('{file_path}', 'w') as f:
    f.write('''{content}''')
"""
        await self._sandbox.run_code(write_file_code)

        # Track for cleanup
        self._generated_files.append(file_path)

    async def _cleanup_generated_files(self) -> None:
        """Cleanup generated files if needed."""
        # For E2B sandboxes, files are automatically cleaned up when sandbox is destroyed
        # This method is here for future extensibility
        self._generated_files.clear()


# Export the new primitive
__all__ = ["MCPCodeExecutionPrimitive", "MCPServerConfig", "MCPCodeExecutionInput"]
