"""Integration tests for PTC (Programmatic Tool Calling) with Hypertool.

End-to-end tests demonstrating the complete flow:
1. Load Hypertool persona
2. Generate Python modules from MCP schemas
3. Create E2B sandbox files
4. Validate code imports against persona permissions
5. Execute code with persona restrictions

These tests use mocks for external services (E2B, MCP servers).
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from tta_dev_primitives.integrations.e2b_template_config import (
    E2BTemplateConfig,
    create_mcp_sandbox_files,
)
from tta_dev_primitives.integrations.hypertool_bridge import (
    HypertoolLoader,
    HypertoolMCPConfig,
    HypertoolMCPExecutor,
    HypertoolPersona,
)
from tta_dev_primitives.integrations.mcp_schema_generator import (
    MCPToolParameter,
    MCPToolSchema,
    PythonModuleGenerator,
)


@pytest.fixture
def sample_persona():
    """Create a sample persona for testing."""
    return HypertoolPersona(
        name="test-engineer",
        display_name="Test Engineer",
        description="Test persona for integration tests",
        icon="🧪",
        token_budget=1500,
        allowed_servers=["context7", "github"],
        allowed_tools={
            "context7": ["resolve-library-id", "get-library-docs"],
            "github": ["github_get_file_contents"],
        },
    )


@pytest.fixture
def sample_servers():
    """Create sample MCP server configs."""
    return {
        "context7": HypertoolMCPConfig(
            name="context7",
            command="/usr/bin/npx",
            args=["-y", "@upstash/context7-mcp@latest"],
            description="Library documentation",
        ),
        "github": HypertoolMCPConfig(
            name="github",
            command="/usr/bin/docker",
            args=["run", "-i", "ghcr.io/github/github-mcp-server"],
            env={"GITHUB_TOKEN": "${GITHUB_TOKEN}"},
            description="GitHub operations",
        ),
    }


@pytest.fixture
def sample_tool_schemas():
    """Create sample tool schemas."""
    return {
        "context7": [
            MCPToolSchema(
                name="resolve_library_id",
                description="Resolve library name to ID",
                parameters=[
                    MCPToolParameter(
                        name="library_name",
                        type_hint="str",
                        description="Library name",
                        required=True,
                    ),
                ],
            ),
            MCPToolSchema(
                name="get_library_docs",
                description="Get library documentation",
                parameters=[
                    MCPToolParameter(
                        name="library_id",
                        type_hint="str",
                        description="Library ID",
                        required=True,
                    ),
                    MCPToolParameter(
                        name="topic",
                        type_hint="str",
                        description="Topic to focus on",
                        required=False,
                    ),
                ],
            ),
        ],
        "github": [
            MCPToolSchema(
                name="github_get_file_contents",
                description="Get file contents from GitHub",
                parameters=[
                    MCPToolParameter(
                        name="repo",
                        type_hint="str",
                        description="Repository name",
                        required=True,
                    ),
                    MCPToolParameter(
                        name="path",
                        type_hint="str",
                        description="File path",
                        required=True,
                    ),
                ],
            ),
        ],
    }


class TestE2BTemplateConfig:
    """Test E2B template configuration."""

    def test_default_config(self):
        """Test default configuration values."""
        config = E2BTemplateConfig()

        assert config.template_id == "base"
        assert config.python_version == "3.11"
        assert config.timeout_seconds == 60
        assert "aiohttp" in config.pip_packages

    def test_to_e2b_options(self):
        """Test conversion to E2B options dict."""
        config = E2BTemplateConfig(
            template_id="custom-template",
            timeout_seconds=120,
            memory_mb=1024,
        )

        options = config.to_e2b_options()

        assert options["template"] == "custom-template"
        assert options["timeout"] == 120
        assert options["metadata"]["memory_mb"] == 1024


class TestSandboxFileGeneration:
    """Test sandbox file generation."""

    def test_create_mcp_sandbox_files(self, sample_persona, sample_servers, sample_tool_schemas):
        """Test creating sandbox files for MCP execution."""
        files = create_mcp_sandbox_files(
            persona=sample_persona,
            servers=sample_servers,
            tool_schemas=sample_tool_schemas,
        )

        # Check expected files
        paths = [f.path for f in files]

        assert "servers/__init__.py" in paths
        assert "mcp_client.py" in paths
        assert "persona_info.py" in paths
        assert "servers/context7/__init__.py" in paths
        assert "servers/context7/resolve_library_id.py" in paths
        assert "servers/github/__init__.py" in paths

    def test_mcp_client_has_server_configs(
        self, sample_persona, sample_servers, sample_tool_schemas
    ):
        """Test that MCP client includes server configurations."""
        files = create_mcp_sandbox_files(
            persona=sample_persona,
            servers=sample_servers,
            tool_schemas=sample_tool_schemas,
        )

        mcp_client = next(f for f in files if f.path == "mcp_client.py")

        # Check server configs are injected
        assert "context7" in mcp_client.content
        assert "github" in mcp_client.content
        assert "call_mcp_tool" in mcp_client.content

    def test_persona_info_file(self, sample_persona, sample_servers):
        """Test persona info file generation."""
        files = create_mcp_sandbox_files(
            persona=sample_persona,
            servers=sample_servers,
        )

        persona_file = next(f for f in files if f.path == "persona_info.py")

        assert sample_persona.name in persona_file.content
        assert sample_persona.display_name in persona_file.content


class TestEndToEndFlow:
    """Test complete PTC flow from persona to execution."""

    def test_full_flow_with_mocks(self, sample_persona, sample_servers, sample_tool_schemas):
        """Test complete flow: persona → schema → modules → sandbox files."""
        # Step 1: Generate Python modules from schemas
        generator = PythonModuleGenerator()
        all_modules: dict[str, str] = {}

        for server_name, tools in sample_tool_schemas.items():
            if server_name in sample_servers:
                modules = generator.generate_server_modules(
                    server_name, tools, sample_servers[server_name].description
                )
                all_modules.update(modules)

        # Verify modules generated
        assert "servers/context7/__init__.py" in all_modules
        assert "servers/context7/resolve_library_id.py" in all_modules
        assert "servers/github/github_get_file_contents.py" in all_modules

        # Step 2: Create sandbox files
        files = create_mcp_sandbox_files(
            persona=sample_persona,
            servers=sample_servers,
            tool_schemas=sample_tool_schemas,
        )

        # Verify sandbox structure
        assert (
            len(files) >= 5
        )  # At least: servers/__init__, mcp_client, persona_info, + server modules

        # Step 3: Verify code validation
        with patch.object(HypertoolLoader, "load_mcp_servers") as mock_servers:
            mock_servers.return_value = sample_servers

            executor = HypertoolMCPExecutor(
                persona=sample_persona,
                hypertool_dir="/tmp/fake",
            )

            # Valid code should pass
            valid_code = """
from servers.context7 import get_library_docs
result = await get_library_docs("pandas")
"""
            errors = executor.validate_code_imports(valid_code)
            assert errors == []

            # Invalid code should fail
            invalid_code = """
from servers.grafana import query_prometheus  # Not allowed!
"""
            errors = executor.validate_code_imports(invalid_code)
            assert len(errors) == 1
            assert "grafana" in errors[0]

    def test_generated_code_is_valid_python(
        self, sample_persona, sample_servers, sample_tool_schemas
    ):
        """Test that generated code is syntactically valid Python."""
        import ast

        files = create_mcp_sandbox_files(
            persona=sample_persona,
            servers=sample_servers,
            tool_schemas=sample_tool_schemas,
        )

        for f in files:
            if f.path.endswith(".py"):
                try:
                    ast.parse(f.content)
                except SyntaxError as e:
                    pytest.fail(f"Invalid Python in {f.path}: {e}")


class TestHypertoolIntegration:
    """Test Hypertool integration with real config files."""

    @pytest.fixture
    def temp_hypertool_dir(self, sample_persona):
        """Create temporary .hypertool directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            hypertool_dir = Path(tmpdir) / ".hypertool"
            personas_dir = hypertool_dir / "personas"
            personas_dir.mkdir(parents=True)

            # Write persona
            persona_json = {
                "name": sample_persona.name,
                "displayName": sample_persona.display_name,
                "description": sample_persona.description,
                "allowedServers": sample_persona.allowed_servers,
                "allowedTools": sample_persona.allowed_tools,
            }
            with open(personas_dir / f"{sample_persona.name}.json", "w") as f:
                json.dump(persona_json, f)

            # Write MCP servers
            servers_json = {
                "mcpServers": {
                    "context7": {
                        "command": "/usr/bin/npx",
                        "args": ["-y", "@upstash/context7-mcp@latest"],
                    },
                    "github": {
                        "command": "/usr/bin/docker",
                        "args": ["run", "-i", "ghcr.io/github/github-mcp-server"],
                    },
                    "grafana": {
                        "url": "http://localhost:8080/mcp",
                    },
                }
            }
            with open(hypertool_dir / "mcp_servers.json", "w") as f:
                json.dump(servers_json, f)

            yield hypertool_dir

    def test_load_and_filter_servers(self, temp_hypertool_dir, sample_persona):
        """Test loading persona and filtering servers."""
        loader = HypertoolLoader(temp_hypertool_dir)

        # Load persona
        persona = loader.load_persona(sample_persona.name)
        assert persona.name == sample_persona.name

        # Get filtered servers
        servers = loader.get_persona_servers(persona)

        # Only allowed servers should be present
        assert "context7" in servers
        assert "github" in servers
        assert "grafana" not in servers  # Not in allowedServers


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
