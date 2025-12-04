"""Tests for Hypertool Bridge integration.

Comprehensive test suite covering:
- Persona loading from JSON files
- MCP server configuration loading
- Persona-based server filtering
- Code import validation
- HypertoolMCPExecutor integration
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from tta_dev_primitives.core.base import WorkflowContext
from tta_dev_primitives.integrations.hypertool_bridge import (
    HypertoolLoader,
    HypertoolMCPConfig,
    HypertoolMCPExecutor,
    HypertoolPersona,
)


@pytest.fixture
def sample_persona_json():
    """Sample persona JSON data."""
    return {
        "name": "test-engineer",
        "displayName": "Test Engineer",
        "description": "Test persona for unit tests",
        "icon": "🧪",
        "tokenBudget": 1500,
        "allowedServers": ["context7", "github"],
        "allowedTools": {
            "context7": ["resolve-library-id", "get-library-docs"],
            "github": ["github_get_file_contents"],
        },
        "restrictedPaths": ["**/node_modules/**"],
        "context": {"primaryLanguage": "Python"},
        "security": {"allowEnvironmentAccess": ["GITHUB_TOKEN"]},
        "workflows": {"default": "testing"},
    }


@pytest.fixture
def sample_mcp_servers_json():
    """Sample MCP servers JSON data."""
    return {
        "mcpServers": {
            "context7": {
                "command": "/usr/bin/npx",
                "args": ["-y", "@upstash/context7-mcp@latest"],
                "description": "Library documentation",
                "tags": ["documentation"],
            },
            "github": {
                "command": "/usr/bin/docker",
                "args": ["run", "-i", "ghcr.io/github/github-mcp-server"],
                "env": {"GITHUB_TOKEN": "${GITHUB_TOKEN}"},
                "description": "GitHub operations",
                "tags": ["vcs"],
            },
            "grafana": {
                "url": "http://localhost:8080/mcp",
                "description": "Observability",
                "tags": ["monitoring"],
            },
        }
    }


@pytest.fixture
def temp_hypertool_dir(sample_persona_json, sample_mcp_servers_json):
    """Create temporary .hypertool directory with test data."""
    with tempfile.TemporaryDirectory() as tmpdir:
        hypertool_dir = Path(tmpdir) / ".hypertool"
        personas_dir = hypertool_dir / "personas"
        personas_dir.mkdir(parents=True)

        # Write persona file
        with open(personas_dir / "test-engineer.json", "w") as f:
            json.dump(sample_persona_json, f)

        # Write MCP servers config
        with open(hypertool_dir / "mcp_servers.json", "w") as f:
            json.dump(sample_mcp_servers_json, f)

        yield hypertool_dir


class TestHypertoolPersona:
    """Test HypertoolPersona dataclass."""

    def test_from_json(self, sample_persona_json):
        """Test creating persona from JSON."""
        persona = HypertoolPersona.from_json(sample_persona_json)

        assert persona.name == "test-engineer"
        assert persona.display_name == "Test Engineer"
        assert persona.token_budget == 1500
        assert "context7" in persona.allowed_servers
        assert "github" in persona.allowed_servers
        assert len(persona.allowed_tools) == 2

    def test_from_json_defaults(self):
        """Test persona with minimal JSON uses defaults."""
        minimal = {"name": "minimal"}
        persona = HypertoolPersona.from_json(minimal)

        assert persona.name == "minimal"
        assert persona.token_budget == 2000
        assert persona.icon == "🔧"
        assert persona.allowed_servers == []


class TestHypertoolMCPConfig:
    """Test HypertoolMCPConfig dataclass."""

    def test_stdio_transport(self):
        """Test stdio transport detection."""
        config = HypertoolMCPConfig(
            name="test",
            command="/usr/bin/npx",
            args=["some-mcp-server"],
        )
        assert config.transport == "stdio"

    def test_http_transport(self):
        """Test HTTP transport detection."""
        config = HypertoolMCPConfig(
            name="test",
            url="http://localhost:8080/mcp",
        )
        assert config.transport == "http"

    def test_from_json(self):
        """Test creating config from JSON."""
        data = {
            "command": "/usr/bin/npx",
            "args": ["-y", "mcp-server"],
            "env": {"API_KEY": "secret"},
            "description": "Test server",
            "tags": ["test"],
        }
        config = HypertoolMCPConfig.from_json("test-server", data)

        assert config.name == "test-server"
        assert config.command == "/usr/bin/npx"
        assert config.args == ["-y", "mcp-server"]
        assert config.env == {"API_KEY": "secret"}


class TestHypertoolLoader:
    """Test HypertoolLoader functionality."""

    def test_load_persona(self, temp_hypertool_dir):
        """Test loading persona from file."""
        loader = HypertoolLoader(temp_hypertool_dir)
        persona = loader.load_persona("test-engineer")

        assert persona.name == "test-engineer"
        assert "context7" in persona.allowed_servers

    def test_load_persona_not_found(self, temp_hypertool_dir):
        """Test loading non-existent persona raises error."""
        loader = HypertoolLoader(temp_hypertool_dir)

        with pytest.raises(FileNotFoundError, match="Persona not found"):
            loader.load_persona("non-existent")

    def test_list_personas(self, temp_hypertool_dir):
        """Test listing available personas."""
        loader = HypertoolLoader(temp_hypertool_dir)
        personas = loader.list_personas()

        assert "test-engineer" in personas

    def test_load_mcp_servers(self, temp_hypertool_dir):
        """Test loading MCP server configurations."""
        loader = HypertoolLoader(temp_hypertool_dir)
        servers = loader.load_mcp_servers()

        assert "context7" in servers
        assert "github" in servers
        assert "grafana" in servers
        assert servers["grafana"].transport == "http"

    def test_get_persona_servers(self, temp_hypertool_dir):
        """Test filtering servers by persona permissions."""
        loader = HypertoolLoader(temp_hypertool_dir)
        persona = loader.load_persona("test-engineer")
        servers = loader.get_persona_servers(persona)

        # Only allowed servers should be returned
        assert "context7" in servers
        assert "github" in servers
        assert "grafana" not in servers  # Not in allowedServers

    def test_persona_caching(self, temp_hypertool_dir):
        """Test that personas are cached."""
        loader = HypertoolLoader(temp_hypertool_dir)

        persona1 = loader.load_persona("test-engineer")
        persona2 = loader.load_persona("test-engineer")

        assert persona1 is persona2  # Same object from cache


class TestHypertoolMCPExecutor:
    """Test HypertoolMCPExecutor integration."""

    def test_validate_code_imports_allowed(self, temp_hypertool_dir):
        """Test validation passes for allowed server imports."""
        persona = HypertoolPersona(
            name="test",
            display_name="Test",
            description="Test",
            allowed_servers=["context7", "github"],
        )

        with patch.object(HypertoolLoader, "load_mcp_servers") as mock_servers:
            mock_servers.return_value = {
                "context7": HypertoolMCPConfig(name="context7", command="npx"),
                "github": HypertoolMCPConfig(name="github", command="docker"),
            }

            executor = HypertoolMCPExecutor(persona=persona, hypertool_dir=temp_hypertool_dir)

            code = """
from servers.context7 import get_library_docs
from servers.github import github_get_file_contents
"""
            errors = executor.validate_code_imports(code)
            assert errors == []

    def test_validate_code_imports_unauthorized(self, temp_hypertool_dir):
        """Test validation fails for unauthorized server imports."""
        persona = HypertoolPersona(
            name="test",
            display_name="Test",
            description="Test",
            allowed_servers=["context7"],  # Only context7 allowed
        )

        with patch.object(HypertoolLoader, "load_mcp_servers") as mock_servers:
            mock_servers.return_value = {
                "context7": HypertoolMCPConfig(name="context7", command="npx"),
            }

            executor = HypertoolMCPExecutor(persona=persona, hypertool_dir=temp_hypertool_dir)

            code = """
from servers.context7 import get_library_docs
from servers.grafana import query_prometheus  # Not allowed!
"""
            errors = executor.validate_code_imports(code)
            assert len(errors) == 1
            assert "grafana" in errors[0]
            assert "Unauthorized" in errors[0]

    def test_init_requires_persona(self, temp_hypertool_dir):
        """Test that either persona or persona_name is required."""
        with pytest.raises(ValueError, match="Either persona or persona_name"):
            HypertoolMCPExecutor(hypertool_dir=temp_hypertool_dir)

    @pytest.mark.asyncio
    async def test_execute_validates_imports(self, temp_hypertool_dir):
        """Test that execute validates imports before running."""
        persona = HypertoolPersona(
            name="test",
            display_name="Test",
            description="Test",
            allowed_servers=["context7"],
        )

        with patch.object(HypertoolLoader, "load_mcp_servers") as mock_servers:
            mock_servers.return_value = {
                "context7": HypertoolMCPConfig(name="context7", command="npx"),
            }

            executor = HypertoolMCPExecutor(persona=persona, hypertool_dir=temp_hypertool_dir)

            context = WorkflowContext(correlation_id="test")
            input_data = {"code": "from servers.unauthorized import tool"}

            with pytest.raises(PermissionError, match="Code validation failed"):
                await executor.execute(input_data, context)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
