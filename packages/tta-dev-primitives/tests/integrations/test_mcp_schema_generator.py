"""Tests for MCP Schema to Python Module Generator.

Comprehensive test suite covering:
- JSON Schema to Python type mapping
- Tool schema parsing from MCP responses
- Python module code generation
- MCP client code generation
"""

from __future__ import annotations

import pytest

from tta_dev_primitives.integrations.mcp_schema_generator import (
    MCPToolParameter,
    MCPToolSchema,
    PythonModuleGenerator,
    TypeMapper,
)


class TestTypeMapper:
    """Test JSON Schema to Python type mapping."""

    def test_basic_types(self):
        """Test basic type mappings."""
        assert TypeMapper.json_schema_to_python({"type": "string"}) == "str"
        assert TypeMapper.json_schema_to_python({"type": "number"}) == "float"
        assert TypeMapper.json_schema_to_python({"type": "integer"}) == "int"
        assert TypeMapper.json_schema_to_python({"type": "boolean"}) == "bool"
        assert TypeMapper.json_schema_to_python({"type": "null"}) == "None"

    def test_array_types(self):
        """Test array type mappings."""
        # Array without items defaults to list[Any]
        assert TypeMapper.json_schema_to_python({"type": "array"}) == "list[Any]"
        assert (
            TypeMapper.json_schema_to_python({"type": "array", "items": {"type": "string"}})
            == "list[str]"
        )
        assert (
            TypeMapper.json_schema_to_python({"type": "array", "items": {"type": "integer"}})
            == "list[int]"
        )

    def test_object_types(self):
        """Test object type mappings."""
        assert TypeMapper.json_schema_to_python({"type": "object"}) == "dict[str, Any]"
        assert (
            TypeMapper.json_schema_to_python(
                {"type": "object", "additionalProperties": {"type": "string"}}
            )
            == "dict[str, str]"
        )

    def test_union_types(self):
        """Test anyOf/oneOf union type mappings."""
        assert (
            TypeMapper.json_schema_to_python({"anyOf": [{"type": "string"}, {"type": "null"}]})
            == "str | None"
        )
        assert (
            TypeMapper.json_schema_to_python({"oneOf": [{"type": "string"}, {"type": "integer"}]})
            == "str | int"
        )

    def test_empty_schema(self):
        """Test empty schema returns Any."""
        assert TypeMapper.json_schema_to_python({}) == "Any"
        assert TypeMapper.json_schema_to_python(None) == "Any"

    def test_unknown_type(self):
        """Test unknown type returns Any."""
        assert TypeMapper.json_schema_to_python({"type": "unknown"}) == "Any"


class TestMCPToolSchema:
    """Test MCP tool schema parsing."""

    def test_from_mcp_response_basic(self):
        """Test parsing basic MCP tool response."""
        tool_def = {
            "name": "query_prometheus",
            "description": "Execute PromQL query",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "PromQL query"},
                    "time_range": {"type": "string", "description": "Time range"},
                },
                "required": ["query"],
            },
        }

        schema = MCPToolSchema.from_mcp_response(tool_def)

        assert schema.name == "query_prometheus"
        assert schema.description == "Execute PromQL query"
        assert len(schema.parameters) == 2

        # Check required parameter comes first
        assert schema.parameters[0].name == "query"
        assert schema.parameters[0].required is True
        assert schema.parameters[0].type_hint == "str"

        # Check optional parameter
        assert schema.parameters[1].name == "time_range"
        assert schema.parameters[1].required is False

    def test_from_mcp_response_no_schema(self):
        """Test parsing MCP response without input schema."""
        tool_def = {"name": "get_status", "description": "Get system status"}

        schema = MCPToolSchema.from_mcp_response(tool_def)

        assert schema.name == "get_status"
        assert schema.parameters == []

    def test_from_mcp_response_complex_types(self):
        """Test parsing MCP response with complex types."""
        tool_def = {
            "name": "search_logs",
            "description": "Search logs",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "filters": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                    "options": {
                        "type": "object",
                        "additionalProperties": {"type": "boolean"},
                    },
                },
                "required": ["filters"],
            },
        }

        schema = MCPToolSchema.from_mcp_response(tool_def)

        assert schema.parameters[0].type_hint == "list[str]"
        assert schema.parameters[1].type_hint == "dict[str, bool]"


class TestPythonModuleGenerator:
    """Test Python module code generation."""

    @pytest.fixture
    def generator(self):
        """Create generator instance."""
        return PythonModuleGenerator()

    @pytest.fixture
    def sample_tools(self):
        """Create sample tool schemas."""
        return [
            MCPToolSchema(
                name="query_prometheus",
                description="Execute PromQL query",
                parameters=[
                    MCPToolParameter(
                        name="query",
                        type_hint="str",
                        description="PromQL query string",
                        required=True,
                    ),
                    MCPToolParameter(
                        name="time_range",
                        type_hint="str",
                        description="Time range",
                        required=False,
                    ),
                ],
            ),
            MCPToolSchema(
                name="get_dashboard",
                description="Get dashboard by UID",
                parameters=[
                    MCPToolParameter(
                        name="uid",
                        type_hint="str",
                        description="Dashboard UID",
                        required=True,
                    ),
                ],
            ),
        ]

    def test_generate_server_modules(self, generator, sample_tools):
        """Test generating all modules for a server."""
        modules = generator.generate_server_modules("grafana", sample_tools, "Grafana MCP Server")

        # Check expected files generated
        assert "servers/grafana/__init__.py" in modules
        assert "servers/grafana/query_prometheus.py" in modules
        assert "servers/grafana/get_dashboard.py" in modules

    def test_generate_tool_module_content(self, generator, sample_tools):
        """Test tool module content structure."""
        modules = generator.generate_server_modules("grafana", sample_tools)

        tool_code = modules["servers/grafana/query_prometheus.py"]

        # Check imports
        assert "from mcp_client import call_mcp_tool" in tool_code
        assert "from typing import Any" in tool_code

        # Check function signature
        assert "async def query_prometheus(" in tool_code
        assert "query: str" in tool_code
        assert "time_range: str | None = None" in tool_code

        # Check docstring
        assert '"""Execute PromQL query' in tool_code
        assert "PromQL query string" in tool_code

        # Check function body
        assert 'server="grafana"' in tool_code
        assert 'tool="query_prometheus"' in tool_code

    def test_generate_init_module_content(self, generator, sample_tools):
        """Test __init__.py module content."""
        modules = generator.generate_server_modules(
            "grafana", sample_tools, "Grafana observability"
        )

        init_code = modules["servers/grafana/__init__.py"]

        # Check docstring
        assert '"""MCP Server: grafana' in init_code
        assert "Grafana observability" in init_code
        assert "- query_prometheus:" in init_code
        assert "- get_dashboard:" in init_code

        # Check imports
        assert "from .query_prometheus import query_prometheus" in init_code
        assert "from .get_dashboard import get_dashboard" in init_code

        # Check __all__
        assert '__all__ = ["query_prometheus", "get_dashboard"]' in init_code

        # Check metadata
        assert 'SERVER_NAME = "grafana"' in init_code
        assert "AVAILABLE_TOOLS = ['query_prometheus', 'get_dashboard']" in init_code

    def test_generate_mcp_client_module(self, generator):
        """Test MCP client module generation."""
        client_code = generator.generate_mcp_client_module({})

        # Check imports
        assert "import asyncio" in client_code
        assert "import json" in client_code

        # Check main function
        assert "async def call_mcp_tool(" in client_code
        assert "server: str" in client_code
        assert "tool: str" in client_code

        # Check transport handlers
        assert "async def _call_via_stdio(" in client_code
        assert "async def _call_via_http(" in client_code

    def test_generate_parameters_empty(self, generator):
        """Test parameter generation with no parameters."""
        params = generator._generate_parameters([])
        assert params == ""

    def test_generate_parameters_with_defaults(self, generator):
        """Test parameter generation with default values."""
        params = [
            MCPToolParameter(name="limit", type_hint="int", required=False, default=10),
        ]

        result = generator._generate_parameters(params)
        assert "limit: int | None = 10" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
