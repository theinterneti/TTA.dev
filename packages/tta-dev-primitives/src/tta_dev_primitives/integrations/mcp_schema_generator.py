"""MCP Schema to Python Module Generator.

Generates type-safe Python wrapper modules from MCP server tool schemas.
Enables progressive tool discovery pattern with 98.7% token reduction.

Features:
- Query MCP servers for tool schemas via JSON-RPC
- Generate async Python functions with proper type hints
- Support stdio and HTTP transports
- Create importable module structure for E2B sandbox

Example:
    ```python
    from tta_dev_primitives.integrations.mcp_schema_generator import (
        MCPSchemaFetcher,
        PythonModuleGenerator,
    )

    # Fetch schemas from running MCP server
    fetcher = MCPSchemaFetcher()
    tools = await fetcher.fetch_tools("grafana", transport="http", endpoint="http://localhost:8080")

    # Generate Python modules
    generator = PythonModuleGenerator()
    modules = generator.generate_server_modules("grafana", tools)

    # Write to filesystem
    for path, content in modules.items():
        print(f"Generated: {path}")
    ```
"""

from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import dataclass, field
from typing import Any, Literal

logger = logging.getLogger(__name__)


@dataclass
class MCPToolParameter:
    """Represents a parameter in an MCP tool schema."""

    name: str
    type_hint: str  # Python type hint string
    description: str = ""
    required: bool = True
    default: Any = None


@dataclass
class MCPToolSchema:
    """Represents an MCP tool definition."""

    name: str
    description: str
    parameters: list[MCPToolParameter] = field(default_factory=list)
    return_type: str = "dict[str, Any]"

    @classmethod
    def from_mcp_response(cls, tool_def: dict[str, Any]) -> MCPToolSchema:
        """Create MCPToolSchema from MCP tools/list response."""
        name = tool_def.get("name", "unknown")
        description = tool_def.get("description", "")
        input_schema = tool_def.get("inputSchema", {})

        parameters = []
        properties = input_schema.get("properties", {})
        required_params = set(input_schema.get("required", []))

        for param_name, param_schema in properties.items():
            type_hint = TypeMapper.json_schema_to_python(param_schema)
            param_desc = param_schema.get("description", "")
            is_required = param_name in required_params

            parameters.append(
                MCPToolParameter(
                    name=param_name,
                    type_hint=type_hint,
                    description=param_desc,
                    required=is_required,
                    default=None if is_required else param_schema.get("default"),
                )
            )

        # Sort parameters: required first, then optional
        parameters.sort(key=lambda p: (not p.required, p.name))

        return cls(name=name, description=description, parameters=parameters)


class TypeMapper:
    """Maps JSON Schema types to Python type hints."""

    TYPE_MAP = {
        "string": "str",
        "number": "float",
        "integer": "int",
        "boolean": "bool",
        "null": "None",
        "array": "list",
        "object": "dict[str, Any]",
    }

    @classmethod
    def json_schema_to_python(cls, schema: dict[str, Any]) -> str:
        """Convert JSON Schema type definition to Python type hint."""
        if not schema:
            return "Any"

        # Handle anyOf / oneOf (union types)
        if "anyOf" in schema:
            types = [cls.json_schema_to_python(s) for s in schema["anyOf"]]
            unique_types = list(dict.fromkeys(types))  # Preserve order, remove dupes
            if len(unique_types) == 1:
                return unique_types[0]
            return " | ".join(unique_types)

        if "oneOf" in schema:
            types = [cls.json_schema_to_python(s) for s in schema["oneOf"]]
            unique_types = list(dict.fromkeys(types))
            if len(unique_types) == 1:
                return unique_types[0]
            return " | ".join(unique_types)

        # Handle allOf (intersection - just use first for simplicity)
        if "allOf" in schema and schema["allOf"]:
            return cls.json_schema_to_python(schema["allOf"][0])

        schema_type = schema.get("type")
        if not schema_type:
            return "Any"

        # Handle array with items
        if schema_type == "array":
            items = schema.get("items", {})
            item_type = cls.json_schema_to_python(items)
            return f"list[{item_type}]"

        # Handle object with additionalProperties
        if schema_type == "object":
            add_props = schema.get("additionalProperties")
            if add_props and isinstance(add_props, dict):
                value_type = cls.json_schema_to_python(add_props)
                return f"dict[str, {value_type}]"
            return "dict[str, Any]"

        # Handle basic types
        return cls.TYPE_MAP.get(schema_type, "Any")


class MCPSchemaFetcher:
    """Fetches tool schemas from MCP servers via JSON-RPC.

    Supports both stdio and HTTP transports for connecting to MCP servers.
    """

    def __init__(self, timeout: float = 30.0) -> None:
        """Initialize schema fetcher.

        Args:
            timeout: Timeout for MCP server communication in seconds.
        """
        self.timeout = timeout

    async def fetch_tools(
        self,
        server_name: str,
        transport: Literal["stdio", "http"] = "stdio",
        command: str | None = None,
        args: list[str] | None = None,
        endpoint: str | None = None,
    ) -> list[MCPToolSchema]:
        """Fetch tool schemas from an MCP server.

        Args:
            server_name: Name of the MCP server.
            transport: Transport type ("stdio" or "http").
            command: For stdio transport, the command to run.
            args: For stdio transport, command arguments.
            endpoint: For HTTP transport, the server URL.

        Returns:
            List of tool schemas from the server.

        Raises:
            ValueError: If transport configuration is invalid.
            ConnectionError: If unable to connect to MCP server.
        """
        if transport == "stdio":
            if not command:
                raise ValueError("Command required for stdio transport")
            return await self._fetch_via_stdio(server_name, command, args or [])
        elif transport == "http":
            if not endpoint:
                raise ValueError("Endpoint required for HTTP transport")
            return await self._fetch_via_http(server_name, endpoint)
        else:
            raise ValueError(f"Unsupported transport: {transport}")

    async def _fetch_via_stdio(
        self, server_name: str, command: str, args: list[str]
    ) -> list[MCPToolSchema]:
        """Fetch tools via stdio transport (subprocess)."""
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/list",
            "params": {},
        }

        try:
            proc = await asyncio.create_subprocess_exec(
                command,
                *args,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            # Send request and get response
            request_bytes = json.dumps(request).encode() + b"\n"
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(request_bytes), timeout=self.timeout
            )

            if proc.returncode != 0:
                logger.warning(f"MCP server {server_name} stderr: {stderr.decode()}")

            # Parse response (may be multiple lines, find JSON)
            for line in stdout.decode().split("\n"):
                line = line.strip()
                if line.startswith("{"):
                    response = json.loads(line)
                    break
            else:
                raise ConnectionError(f"No valid JSON response from {server_name}")

            if "error" in response:
                raise ConnectionError(f"MCP error: {response['error']}")

            tools_data = response.get("result", {}).get("tools", [])
            return [MCPToolSchema.from_mcp_response(t) for t in tools_data]

        except TimeoutError:
            raise ConnectionError(f"Timeout connecting to {server_name}") from None
        except Exception as e:
            logger.error(f"Failed to fetch tools from {server_name}: {e}")
            raise

    async def _fetch_via_http(self, server_name: str, endpoint: str) -> list[MCPToolSchema]:
        """Fetch tools via HTTP transport."""
        import aiohttp

        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/list",
            "params": {},
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    endpoint,
                    json=request,
                    timeout=aiohttp.ClientTimeout(total=self.timeout),
                ) as resp:
                    response = await resp.json()

            if "error" in response:
                raise ConnectionError(f"MCP error: {response['error']}")

            tools_data = response.get("result", {}).get("tools", [])
            return [MCPToolSchema.from_mcp_response(t) for t in tools_data]

        except Exception as e:
            logger.error(f"Failed to fetch tools from {server_name}: {e}")
            raise


class PythonModuleGenerator:
    """Generates Python modules from MCP tool schemas.

    Creates importable Python code for use in E2B sandboxes.
    """

    def __init__(self, indent: str = "    ") -> None:
        """Initialize generator.

        Args:
            indent: Indentation string (default: 4 spaces).
        """
        self.indent = indent

    def generate_server_modules(
        self, server_name: str, tools: list[MCPToolSchema], description: str = ""
    ) -> dict[str, str]:
        """Generate all modules for an MCP server.

        Args:
            server_name: Name of the MCP server.
            tools: List of tool schemas.
            description: Server description.

        Returns:
            Dict mapping file paths to Python code content.
        """
        modules: dict[str, str] = {}
        base_path = f"servers/{server_name}"

        # Generate individual tool modules
        for tool in tools:
            tool_path = f"{base_path}/{tool.name}.py"
            modules[tool_path] = self._generate_tool_module(server_name, tool)

        # Generate __init__.py
        init_path = f"{base_path}/__init__.py"
        modules[init_path] = self._generate_init_module(server_name, tools, description)

        return modules

    def _generate_tool_module(self, server_name: str, tool: MCPToolSchema) -> str:
        """Generate Python module for a single tool."""
        lines = [
            f'"""MCP Tool: {server_name}.{tool.name}',
            "",
            f"{tool.description}",
            '"""',
            "",
            "from __future__ import annotations",
            "",
            "from typing import Any",
            "",
            "from mcp_client import call_mcp_tool",
            "",
            "",
        ]

        # Generate function signature
        params = self._generate_parameters(tool.parameters)
        lines.append(f"async def {tool.name}({params}) -> {tool.return_type}:")

        # Generate docstring
        docstring_lines = self._generate_docstring(tool)
        lines.extend([f"{self.indent}{line}" for line in docstring_lines])

        # Generate function body
        body_lines = self._generate_function_body(server_name, tool)
        lines.extend([f"{self.indent}{line}" for line in body_lines])

        return "\n".join(lines)

    def _generate_parameters(self, parameters: list[MCPToolParameter]) -> str:
        """Generate function parameter string."""
        if not parameters:
            return ""

        parts = []
        for param in parameters:
            if param.required:
                parts.append(f"{param.name}: {param.type_hint}")
            else:
                # Make optional type explicit
                type_hint = param.type_hint
                if " | None" not in type_hint:
                    type_hint = f"{type_hint} | None"
                default = "None" if param.default is None else repr(param.default)
                parts.append(f"{param.name}: {type_hint} = {default}")

        return ", ".join(parts)

    def _generate_docstring(self, tool: MCPToolSchema) -> list[str]:
        """Generate docstring lines for a tool function."""
        lines = ['"""' + tool.description]

        if tool.parameters:
            lines.append("")
            lines.append("Args:")
            for param in tool.parameters:
                desc = param.description or "No description"
                optional = "" if param.required else " (optional)"
                lines.append(f"    {param.name}: {desc}{optional}")

        lines.append("")
        lines.append("Returns:")
        lines.append(f"    {tool.return_type}: Tool execution results")
        lines.append('"""')
        return lines

    def _generate_function_body(self, server_name: str, tool: MCPToolSchema) -> list[str]:
        """Generate function body that calls MCP tool."""
        lines = ["input_data = {"]

        for param in tool.parameters:
            lines.append(f'    "{param.name}": {param.name},')

        lines.append("}")
        lines.append("")
        lines.append("return await call_mcp_tool(")
        lines.append(f'    server="{server_name}",')
        lines.append(f'    tool="{tool.name}",')
        lines.append("    input_data=input_data,")
        lines.append(")")
        return lines

    def _generate_init_module(
        self, server_name: str, tools: list[MCPToolSchema], description: str
    ) -> str:
        """Generate __init__.py for server module."""
        lines = [
            f'"""MCP Server: {server_name}',
            "",
            description or "No description available.",
            "",
            "Available tools:",
        ]

        for tool in tools:
            lines.append(f"- {tool.name}: {tool.description}")

        lines.append('"""')
        lines.append("")
        lines.append("from __future__ import annotations")
        lines.append("")

        # Imports
        for tool in tools:
            lines.append(f"from .{tool.name} import {tool.name}")

        lines.append("")

        # __all__
        tool_names = ", ".join(f'"{t.name}"' for t in tools)
        lines.append(f"__all__ = [{tool_names}]")
        lines.append("")

        # Metadata
        lines.append(f'SERVER_NAME = "{server_name}"')
        lines.append(f'SERVER_DESCRIPTION = "{description}"')
        tool_list = [t.name for t in tools]
        lines.append(f"AVAILABLE_TOOLS = {tool_list}")

        return "\n".join(lines)

    def generate_mcp_client_module(self, servers: dict[str, dict[str, Any]]) -> str:
        """Generate the MCP client module for the sandbox.

        Args:
            servers: Dict of server configs from Hypertool.

        Returns:
            Python code for mcp_client.py
        """
        return '''"""MCP Client for E2B sandbox execution.

Provides the bridge between generated tool code and actual MCP servers.
Handles JSON-RPC protocol communication.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import subprocess
from typing import Any

logger = logging.getLogger(__name__)

# Server configurations (injected at generation time)
SERVER_CONFIGS: dict[str, dict[str, Any]] = {}


def set_server_configs(configs: dict[str, dict[str, Any]]) -> None:
    """Set server configurations for MCP communication."""
    global SERVER_CONFIGS
    SERVER_CONFIGS = configs


async def call_mcp_tool(
    server: str,
    tool: str,
    input_data: dict[str, Any],
) -> dict[str, Any]:
    """Call an MCP tool via JSON-RPC.

    Args:
        server: Name of the MCP server.
        tool: Name of the tool to call.
        input_data: Tool input parameters.

    Returns:
        Tool execution results.

    Raises:
        ValueError: If server is not configured.
        ConnectionError: If MCP call fails.
    """
    if server not in SERVER_CONFIGS:
        raise ValueError(f"Unknown server: {server}. Available: {list(SERVER_CONFIGS.keys())}")

    config = SERVER_CONFIGS[server]
    transport = config.get("transport", "stdio")

    request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": tool,
            "arguments": input_data,
        },
    }

    if transport == "http":
        return await _call_via_http(config, request)
    else:
        return await _call_via_stdio(config, request)


async def _call_via_stdio(
    config: dict[str, Any],
    request: dict[str, Any],
) -> dict[str, Any]:
    """Call MCP tool via stdio transport."""
    command = config.get("command", "")
    args = config.get("args", [])

    proc = await asyncio.create_subprocess_exec(
        command,
        *args,
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        env={**os.environ, **config.get("env", {})},
    )

    request_bytes = json.dumps(request).encode() + b"\\n"
    stdout, stderr = await proc.communicate(request_bytes)

    # Parse response
    for line in stdout.decode().split("\\n"):
        line = line.strip()
        if line.startswith("{"):
            response = json.loads(line)
            if "error" in response:
                raise ConnectionError(f"MCP error: {response['error']}")
            return response.get("result", {})

    raise ConnectionError(f"No valid response from MCP server")


async def _call_via_http(
    config: dict[str, Any],
    request: dict[str, Any],
) -> dict[str, Any]:
    """Call MCP tool via HTTP transport."""
    import aiohttp

    endpoint = config.get("endpoint", "")

    async with aiohttp.ClientSession() as session:
        async with session.post(endpoint, json=request) as resp:
            response = await resp.json()

    if "error" in response:
        raise ConnectionError(f"MCP error: {response['error']}")

    return response.get("result", {})
'''


# Export classes
__all__ = [
    "MCPToolParameter",
    "MCPToolSchema",
    "TypeMapper",
    "MCPSchemaFetcher",
    "PythonModuleGenerator",
]
