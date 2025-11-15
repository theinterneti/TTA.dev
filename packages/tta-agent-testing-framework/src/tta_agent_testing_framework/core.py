"""
Core types and classes for the TTA Agent Testing Framework.
"""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Protocol


class WorkspaceType(Enum):
    """AI assistant workspace configurations to test."""

    CLINE = "cline"  # Full-featured with comprehensive MCP servers
    AUGMENT = "augment"  # Speed-optimized for fast iteration
    GITHUB_COPILOT = "github-copilot"  # Quality-focused with extensive integrations

    @property
    def workspace_file(self) -> str:
        """Get the workspace configuration file path for this type."""
        return f"{self.value}.code-workspace"


@dataclass
class ValidationResult:
    """Result of a validation or test operation."""

    success: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def has_issues(self) -> bool:
        """Check if this result has any errors or warnings."""
        return len(self.errors) > 0 or len(self.warnings) > 0


@dataclass
class AgentExecutionMetrics:
    """Performance metrics for agent execution."""

    execution_time: float
    token_usage: dict[str, int] | None = None
    cost_estimate: float | None = None
    success_rate: float | None = None
    error_patterns: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentHandoffState:
    """Standardized state transfer format for agent handoffs."""

    correlation_id: str
    source_workspace: WorkspaceType
    target_workspace: WorkspaceType
    code_context: dict[str, Any]
    conversation_history: list[dict[str, Any]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    timestamp: float | None = None

    def serialize(self) -> bytes:
        """Serialize state for transfer between agents."""
        import json

        data = {
            "correlation_id": self.correlation_id,
            "source_workspace": self.source_workspace.value,
            "target_workspace": self.target_workspace.value,
            "code_context": self.code_context,
            "conversation_history": self.conversation_history,
            "metadata": self.metadata,
            "timestamp": self.timestamp,
        }
        return json.dumps(data).encode("utf-8")

    @classmethod
    def deserialize(cls, data: bytes) -> "AgentHandoffState":
        """Deserialize state from bytes."""
        import json

        dict_data = json.loads(data.decode("utf-8"))

        # Convert string workspace values back to enums
        dict_data["source_workspace"] = WorkspaceType(dict_data["source_workspace"])
        dict_data["target_workspace"] = WorkspaceType(dict_data["target_workspace"])

        return cls(**dict_data)


class BrowserAutomationProvider(Protocol):
    """Protocol for browser automation providers."""

    async def launch_vscode_web(
        self,
        workspace_url: str,
        workspace_type: WorkspaceType,
        timeout: int = 30000,
    ) -> ValidationResult:
        """Launch vscode.dev with specified workspace."""
        ...

    async def wait_for_extension_load(
        self,
        extension_id: str,
        timeout: int = 10000,
    ) -> ValidationResult:
        """Wait for VS Code extension to load."""
        ...

    async def execute_in_terminal(
        self,
        command: str,
        workspace_root: str | None = None,
    ) -> ValidationResult:
        """Execute command in VS Code terminal."""
        ...

    async def capture_screenshot(
        self,
        filename: str | None = None,
        full_page: bool = False,
    ) -> ValidationResult:
        """Capture screenshot of current state."""
        ...


class MCPHealthChecker(Protocol):
    """Protocol for MCP server health checking."""

    async def test_server_connectivity(
        self,
        server_name: str,
        timeout: int = 5000,
    ) -> ValidationResult:
        """Test connectivity to MCP server."""
        ...

    async def validate_server_capabilities(
        self,
        server_name: str,
    ) -> ValidationResult:
        """Validate server offers expected capabilities."""
        ...

    async def benchmark_server_performance(
        self,
        server_name: str,
        iterations: int = 10,
    ) -> ValidationResult:
        """Benchmark MCP server response times."""
        ...


class AgentTestingFramework:
    """Main testing framework for AI agentic coders."""

    def __init__(
        self,
        workspace_root: Path,
        browser_provider: BrowserAutomationProvider | None = None,
        mcp_checker: MCPHealthChecker | None = None,
    ):
        self.workspace_root = workspace_root
        self.browser_provider = browser_provider
        self.mcp_checker = mcp_checker
        self.results: list[ValidationResult] = []

    async def validate_workspace_configuration(
        self,
        workspace_type: WorkspaceType,
    ) -> ValidationResult:
        """Validate workspace configuration is properly structured."""
        workspace_file = self.workspace_root / workspace_type.workspace_file

        result = ValidationResult(
            success=True, metadata={"workspace_type": workspace_type.value}
        )

        if not workspace_file.exists():
            result.success = False
            result.errors.append(f"Workspace file not found: {workspace_file}")
            return result

        # Validate JSON structure
        import json

        try:
            with open(workspace_file) as f:
                workspace_data = json.load(f)

            # Basic structure validation
            required_keys = ["folders", "settings", "extensions"]
            for key in required_keys:
                if key not in workspace_data:
                    result.warnings.append(f"Missing recommended key: {key}")

            # Check for AI extension recommendations
            extensions = workspace_data.get("extensions", {})
            recommendations = extensions.get("recommendations", [])

            if workspace_type == WorkspaceType.CLINE:
                if "saoudrizwan.claude-dev" not in recommendations:
                    result.warnings.append("Cline extension not recommended")
            elif workspace_type == WorkspaceType.GITHUB_COPILOT:
                if "github.copilot" not in recommendations:
                    result.warnings.append("GitHub Copilot extensions not recommended")

        except json.JSONDecodeError as e:
            result.success = False
            result.errors.append(f"Invalid JSON in workspace file: {e}")

        return result

    async def test_agent_initialization(
        self,
        workspace_type: WorkspaceType,
    ) -> ValidationResult:
        """Test that agent initializes properly in workspace."""
        if not self.browser_provider:
            return ValidationResult(
                success=False, errors=["No browser provider configured"]
            )

        return await self.browser_provider.launch_vscode_web(
            workspace_url=f"vscode.dev/{self.workspace_root.name}",
            workspace_type=workspace_type,
        )

    async def validate_mcp_connectivity(
        self,
        workspace_type: WorkspaceType,
    ) -> ValidationResult:
        """Validate MCP server connectivity for workspace."""
        if not self.mcp_checker:
            return ValidationResult(
                success=False, errors=["No MCP health checker configured"]
            )

        # MCP servers vary by workspace
        servers_to_test = {
            WorkspaceType.CLINE: ["context7", "sequential-thinking", "serena"],
            WorkspaceType.AUGMENT: [],  # Augment may not use MCP
            WorkspaceType.GITHUB_COPILOT: [],  # Copilot has native integrations
        }

        result = ValidationResult(
            success=True, metadata={"workspace_type": workspace_type.value}
        )

        for server in servers_to_test[workspace_type]:
            server_result = await self.mcp_checker.test_server_connectivity(server)
            if not server_result.success:
                result.success = False
                result.errors.extend(
                    [f"MCP {server}: {error}" for error in server_result.errors]
                )

        return result

    async def run_comprehensive_test(
        self,
        workspace_type: WorkspaceType,
    ) -> ValidationResult:
        """Run full test suite for workspace."""
        results = []

        # Test workspace configuration
        config_result = await self.validate_workspace_configuration(workspace_type)
        results.append(config_result)

        # Test agent initialization
        if self.browser_provider:
            init_result = await self.test_agent_initialization(workspace_type)
            results.append(init_result)

        # Test MCP connectivity
        if self.mcp_checker:
            mcp_result = await self.validate_mcp_connectivity(workspace_type)
            results.append(mcp_result)

        # Aggregate results
        combined_result = ValidationResult(
            success=all(r.success for r in results),
            metadata={
                "workspace_type": workspace_type.value,
                "test_count": len(results),
            },
        )

        for result in results:
            combined_result.errors.extend(result.errors)
            combined_result.warnings.extend(result.warnings)

        return combined_result
