"""Hypertool Bridge for PTC Integration.

Bridges Hypertool's persona-based tool filtering with MCPCodeExecutionPrimitive.
Provides security boundaries and access control for code execution.

Features:
- Load Hypertool persona configurations
- Extract allowed MCP servers and tools per persona
- Validate code imports against persona permissions
- Pass filtered server configs to MCPCodeExecutionPrimitive

Example:
    ```python
    from tta_dev_primitives.integrations.hypertool_bridge import (
        HypertoolLoader,
        HypertoolMCPExecutor,
    )

    # Load persona
    loader = HypertoolLoader(".hypertool")
    persona = loader.load_persona("tta-backend-engineer")

    # Create executor with persona restrictions
    executor = HypertoolMCPExecutor(persona=persona)

    # Execute code (only allowed servers accessible)
    result = await executor.execute({
        "code": "from servers.context7 import get_library_docs"
    }, context)
    ```
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from tta_dev_primitives.core.base import WorkflowContext
from tta_dev_primitives.integrations.e2b_primitive import CodeOutput
from tta_dev_primitives.integrations.mcp_code_execution_primitive import (
    MCPCodeExecutionInput,
    MCPCodeExecutionPrimitive,
    MCPServerConfig,
)

logger = logging.getLogger(__name__)


@dataclass
class HypertoolPersona:
    """Represents a Hypertool persona configuration."""

    name: str
    display_name: str
    description: str
    icon: str = "🔧"
    token_budget: int = 2000
    allowed_servers: list[str] = field(default_factory=list)
    allowed_tools: dict[str, list[str]] = field(default_factory=dict)
    restricted_paths: list[str] = field(default_factory=list)
    context: dict[str, Any] = field(default_factory=dict)
    security: dict[str, Any] = field(default_factory=dict)
    workflows: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> HypertoolPersona:
        """Create persona from JSON configuration."""
        return cls(
            name=data.get("name", "unknown"),
            display_name=data.get("displayName", data.get("name", "Unknown")),
            description=data.get("description", ""),
            icon=data.get("icon", "🔧"),
            token_budget=data.get("tokenBudget", 2000),
            allowed_servers=data.get("allowedServers", []),
            allowed_tools=data.get("allowedTools", {}),
            restricted_paths=data.get("restrictedPaths", []),
            context=data.get("context", {}),
            security=data.get("security", {}),
            workflows=data.get("workflows", {}),
        )


@dataclass
class HypertoolMCPConfig:
    """MCP server configuration from Hypertool."""

    name: str
    command: str | None = None
    args: list[str] = field(default_factory=list)
    env: dict[str, str] = field(default_factory=dict)
    url: str | None = None  # For remote MCP servers
    description: str = ""
    tags: list[str] = field(default_factory=list)

    @property
    def transport(self) -> str:
        """Determine transport type from config."""
        if self.url:
            return "http"
        return "stdio"

    def to_mcp_server_config(self) -> MCPServerConfig:
        """Convert to MCPServerConfig for code execution primitive."""
        return MCPServerConfig(
            name=self.name,
            transport=self.transport,
            endpoint=self.url,
            description=self.description,
            tools=[],  # Will be populated from schema fetching
        )

    @classmethod
    def from_json(cls, name: str, data: dict[str, Any]) -> HypertoolMCPConfig:
        """Create config from Hypertool mcp_servers.json entry."""
        return cls(
            name=name,
            command=data.get("command"),
            args=data.get("args", []),
            env=data.get("env", {}),
            url=data.get("url"),
            description=data.get("description", ""),
            tags=data.get("tags", []),
        )


class HypertoolLoader:
    """Loads Hypertool configuration files."""

    def __init__(self, hypertool_dir: str | Path = ".hypertool") -> None:
        """Initialize loader.

        Args:
            hypertool_dir: Path to .hypertool directory.
        """
        self.hypertool_dir = Path(hypertool_dir)
        self._personas_cache: dict[str, HypertoolPersona] = {}
        self._mcp_servers_cache: dict[str, HypertoolMCPConfig] | None = None

    def load_persona(self, persona_name: str) -> HypertoolPersona:
        """Load a persona configuration by name.

        Args:
            persona_name: Name of the persona (e.g., "tta-backend-engineer").

        Returns:
            HypertoolPersona instance.

        Raises:
            FileNotFoundError: If persona file doesn't exist.
            ValueError: If persona file is invalid JSON.
        """
        if persona_name in self._personas_cache:
            return self._personas_cache[persona_name]

        persona_file = self.hypertool_dir / "personas" / f"{persona_name}.json"
        if not persona_file.exists():
            raise FileNotFoundError(f"Persona not found: {persona_file}")

        try:
            with open(persona_file) as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in {persona_file}: {e}") from e

        persona = HypertoolPersona.from_json(data)
        self._personas_cache[persona_name] = persona
        return persona

    def list_personas(self) -> list[str]:
        """List available persona names.

        Returns:
            List of persona names (without .json extension).
        """
        personas_dir = self.hypertool_dir / "personas"
        if not personas_dir.exists():
            return []

        return [f.stem for f in personas_dir.glob("*.json") if f.is_file()]

    def load_mcp_servers(self) -> dict[str, HypertoolMCPConfig]:
        """Load MCP server configurations.

        Returns:
            Dict mapping server names to their configurations.

        Raises:
            FileNotFoundError: If mcp_servers.json doesn't exist.
        """
        if self._mcp_servers_cache is not None:
            return self._mcp_servers_cache

        servers_file = self.hypertool_dir / "mcp_servers.json"
        if not servers_file.exists():
            raise FileNotFoundError(f"MCP servers config not found: {servers_file}")

        with open(servers_file) as f:
            data = json.load(f)

        servers_data = data.get("mcpServers", {})
        self._mcp_servers_cache = {
            name: HypertoolMCPConfig.from_json(name, config)
            for name, config in servers_data.items()
        }

        return self._mcp_servers_cache

    def get_persona_servers(self, persona: HypertoolPersona) -> dict[str, HypertoolMCPConfig]:
        """Get MCP server configs filtered by persona permissions.

        Args:
            persona: The persona to filter by.

        Returns:
            Dict of allowed server configurations.
        """
        all_servers = self.load_mcp_servers()
        return {
            name: config for name, config in all_servers.items() if name in persona.allowed_servers
        }


class HypertoolMCPExecutor:
    """Bridges Hypertool personas with MCPCodeExecutionPrimitive.

    Provides secure code execution with persona-based access control.
    Only servers and tools allowed by the persona can be accessed.
    """

    def __init__(
        self,
        persona: HypertoolPersona | None = None,
        persona_name: str | None = None,
        hypertool_dir: str | Path = ".hypertool",
        **mcp_kwargs: Any,
    ) -> None:
        """Initialize executor with persona restrictions.

        Args:
            persona: HypertoolPersona instance (takes precedence).
            persona_name: Name of persona to load.
            hypertool_dir: Path to .hypertool directory.
            **mcp_kwargs: Additional args for MCPCodeExecutionPrimitive.

        Raises:
            ValueError: If neither persona nor persona_name provided.
        """
        self.loader = HypertoolLoader(hypertool_dir)

        if persona:
            self.persona = persona
        elif persona_name:
            self.persona = self.loader.load_persona(persona_name)
        else:
            raise ValueError("Either persona or persona_name must be provided")

        # Get allowed servers for this persona
        self.allowed_servers = self.loader.get_persona_servers(self.persona)

        # Create MCP code execution primitive with restrictions
        self._executor = MCPCodeExecutionPrimitive(
            available_servers=list(self.allowed_servers.keys()),
            mcp_servers_config=self._build_mcp_config(),
            **mcp_kwargs,
        )

    def _build_mcp_config(self) -> dict[str, MCPServerConfig]:
        """Build MCPServerConfig dict from Hypertool configs."""
        return {
            name: config.to_mcp_server_config() for name, config in self.allowed_servers.items()
        }

    def validate_code_imports(self, code: str) -> list[str]:
        """Validate that code only imports from allowed servers.

        Args:
            code: Python code to validate.

        Returns:
            List of validation errors (empty if valid).
        """
        errors = []

        # Pattern to match "from servers.X import ..." or "import servers.X"
        import_pattern = re.compile(r"(?:from\s+servers\.(\w+)\s+import|import\s+servers\.(\w+))")

        for match in import_pattern.finditer(code):
            server_name = match.group(1) or match.group(2)
            if server_name not in self.allowed_servers:
                errors.append(
                    f"Unauthorized server access: '{server_name}'. "
                    f"Allowed servers for {self.persona.name}: {list(self.allowed_servers.keys())}"
                )

        return errors

    async def execute(
        self,
        input_data: MCPCodeExecutionInput,
        context: WorkflowContext,
        validate_imports: bool = True,
    ) -> CodeOutput:
        """Execute code with persona restrictions.

        Args:
            input_data: Code execution input.
            context: Workflow context.
            validate_imports: Whether to validate imports before execution.

        Returns:
            Code execution output.

        Raises:
            PermissionError: If code tries to access unauthorized servers.
        """
        code = input_data.get("code", "")

        if validate_imports:
            errors = self.validate_code_imports(code)
            if errors:
                raise PermissionError(
                    f"Code validation failed for persona '{self.persona.name}':\n"
                    + "\n".join(f"  - {e}" for e in errors)
                )

        # Override available_servers with persona's allowed servers
        input_data["available_servers"] = list(self.allowed_servers.keys())

        logger.info(
            f"Executing code with persona '{self.persona.name}', "
            f"allowed servers: {list(self.allowed_servers.keys())}"
        )

        return await self._executor.execute(input_data, context)

    async def cleanup(self) -> None:
        """Cleanup executor resources."""
        await self._executor.cleanup()

    async def __aenter__(self) -> HypertoolMCPExecutor:
        """Async context manager entry."""
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: object | None,
    ) -> None:
        """Async context manager exit."""
        await self.cleanup()


# Export classes
__all__ = [
    "HypertoolPersona",
    "HypertoolMCPConfig",
    "HypertoolLoader",
    "HypertoolMCPExecutor",
]
