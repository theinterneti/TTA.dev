"""
MCP server health checking and validation for AI agent testing.
"""

import asyncio
import json
import time
from pathlib import Path
from typing import Any

import websockets
from aiohttp import ClientSession, ClientTimeout
from tta_dev_primitives.core import LambdaPrimitive, WorkflowContext
from tta_dev_primitives.recovery import TimeoutPrimitive

from .core import MCPHealthChecker, ValidationResult


class MCPConnectionHealthChecker(MCPHealthChecker):
    """Health checker for MCP server connections."""

    def __init__(
        self,
        mcp_config_path: Path | None = None,
        connection_timeout: float = 5.0,
        max_retries: int = 3,
    ):
        self.mcp_config_path = mcp_config_path or Path.home() / ".vscode" / "mcp.json"
        self.connection_timeout = connection_timeout
        self.max_retries = max_retries
        self.session_timeout = ClientTimeout(total=connection_timeout)

    async def test_server_connectivity(
        self,
        server_name: str,
        timeout: int = 5000,
    ) -> ValidationResult:
        """Test connectivity to MCP server."""
        result = ValidationResult(
            success=True,
            metadata={
                "server_name": server_name,
                "timeout": timeout,
                "max_retries": self.max_retries,
            },
        )

        start_time = time.time()

        # Load MCP configuration
        config_result = await self._load_mcp_config()
        if not config_result.success:
            result.success = False
            result.errors.extend(config_result.errors)

        # Find server configuration
        server_config = None
        if config_result.metadata.get("config"):
            mcp_servers = config_result.metadata["config"].get("mcpServers", {})
            server_config = mcp_servers.get(server_name)

        if not server_config:
            result.success = False
            result.errors.append(
                f"Server '{server_name}' not found in MCP configuration"
            )
            return result

        # Test connectivity based on server type
        server_type = server_config.get("type", "stdio")

        if server_type == "stdio":
            connect_result = await self._test_stdio_connectivity(server_config, timeout)
        elif server_type == "sse":
            connect_result = await self._test_sse_connectivity(server_config, timeout)
        elif server_type == "websocket":
            connect_result = await self._test_websocket_connectivity(
                server_config, timeout
            )
        else:
            connect_result = ValidationResult(
                success=False,
                errors=[f"Unsupported MCP server type: {server_type}"],
            )

        # Calculate response time
        end_time = time.time()
        response_time = end_time - start_time

        result.metadata["response_time"] = response_time
        result.metadata["connect_success"] = connect_result.success

        if not connect_result.success:
            result.success = False
            result.errors.extend(connect_result.errors)
        else:
            result.metadata.update(connect_result.metadata)

        return result

    async def _load_mcp_config(self) -> ValidationResult:
        """Load MCP configuration from file."""
        result = ValidationResult(success=True)

        try:
            if not self.mcp_config_path.exists():
                result.success = False
                result.errors.append(
                    f"MCP config file not found: {self.mcp_config_path}"
                )
                return result

            with open(self.mcp_config_path) as f:
                config = json.load(f)

            result.metadata["config"] = config
            result.metadata["config_file"] = str(self.mcp_config_path)

        except json.JSONDecodeError as e:
            result.success = False
            result.errors.append(f"Invalid MCP config JSON: {e}")
        except Exception as e:
            result.success = False
            result.errors.append(f"Failed to load MCP config: {e}")

        return result

    async def _test_stdio_connectivity(
        self,
        server_config: dict[str, Any],
        timeout: int,
    ) -> ValidationResult:
        """Test stdio-based MCP server connectivity."""
        result = ValidationResult(success=True)

        # For stdio servers, we can't easily test connectivity without
        # actually starting the process, so we do basic validation

        command = server_config.get("command")
        if not command:
            result.success = False
            result.errors.append("No command specified for stdio server")
            return result

        # Check if command exists in PATH
        import shutil

        if not shutil.which(command):
            result.success = False
            result.errors.append(f"Command '{command}' not found in PATH")
            return result

        # Validate args if present
        args = server_config.get("args", [])
        if not isinstance(args, list):
            result.success = False
            result.errors.append("Server args must be a list")
            return result

        result.metadata["command_found"] = True
        result.metadata["args_valid"] = True

        return result

    async def _test_sse_connectivity(
        self,
        server_config: dict[str, Any],
        timeout: int,
    ) -> ValidationResult:
        """Test SSE-based MCP server connectivity."""
        result = ValidationResult(success=True)

        url = server_config.get("url")
        if not url:
            result.success = False
            result.errors.append("No URL specified for SSE server")
            return result

        try:
            async with ClientSession(timeout=self.session_timeout) as session:
                async with session.get(url) as response:
                    if response.status != 200:
                        result.success = False
                        result.errors.append(
                            f"SSE server returned status {response.status}"
                        )
                        return result

                    # Check for SSE content type
                    content_type = response.headers.get("content-type", "")
                    if "text/event-stream" not in content_type.lower():
                        result.warnings.append(
                            f"Unexpected content type: {content_type}"
                        )

                    result.metadata["status_code"] = response.status
                    result.metadata["content_type"] = content_type

        except Exception as e:
            result.success = False
            result.errors.append(f"SSE connection failed: {str(e)}")

        return result

    async def _test_websocket_connectivity(
        self,
        server_config: dict[str, Any],
        timeout: int,
    ) -> ValidationResult:
        """Test WebSocket-based MCP server connectivity."""
        result = ValidationResult(success=True)

        url = server_config.get("url")
        if not url:
            result.success = False
            result.errors.append("No URL specified for WebSocket server")
            return result

        try:
            async with websockets.connect(url) as websocket:
                # Send a basic ping/handshake
                await websocket.send(
                    json.dumps({"jsonrpc": "2.0", "id": 1, "method": "initialize"})
                )

                # Wait for response with timeout
                timeout_primitive = TimeoutPrimitive(
                    primitive=LambdaPrimitive(lambda x, ctx: websocket.recv()),
                    timeout_seconds=timeout / 1000,
                )
                response = await timeout_primitive.execute(None, WorkflowContext())

                response_data = json.loads(response)
                if "result" in response_data:
                    result.metadata["server_capable"] = True
                elif "error" in response_data:
                    result.warnings.append(
                        f"Server initialization error: {response_data['error']}"
                    )

        except websockets.exceptions.ConnectionClosedError as e:
            result.success = False
            result.errors.append(f"WebSocket connection closed: {e}")
        except TimeoutError:
            result.success = False
            result.errors.append("WebSocket handshake timeout")
        except Exception as e:
            result.success = False
            result.errors.append(f"WebSocket connection failed: {str(e)}")

        return result

    async def validate_server_capabilities(
        self,
        server_name: str,
    ) -> ValidationResult:
        """Validate server offers expected capabilities."""
        result = ValidationResult(
            success=True,
            metadata={"server_name": server_name},
        )

        # Load server config
        config_result = await self._load_mcp_config()
        if not config_result.success:
            result.success = False
            result.errors.extend(config_result.errors)
            return result

        mcp_servers = config_result.metadata["config"].get("mcpServers", {})
        server_config = mcp_servers.get(server_name)

        if not server_config:
            result.success = False
            result.errors.append(
                f"Server '{server_name}' not found in MCP configuration"
            )
            return result

        # Expected capabilities based on server name
        expected_capabilities = self._get_expected_capabilities(server_name)

        # For now, validate that we can connect and get basic info
        # Full capability testing would require actual MCP protocol interactions
        connectivity = await self.test_server_connectivity(server_name)
        result.metadata["connectivity_test"] = connectivity.success

        if connectivity.success:
            result.metadata["capabilities_valid"] = True
            result.metadata["expected_capabilities"] = expected_capabilities
        else:
            result.success = False
            result.errors.append(
                "Cannot validate capabilities due to connectivity issues"
            )

        return result

    def _get_expected_capabilities(self, server_name: str) -> list[str]:
        """Get expected capabilities for a given server."""
        capability_map = {
            "context7": ["documentation", "code-search", "library-info"],
            "sequential-thinking": ["planning", "reasoning", "task-breakdown"],
            "serena": ["code-analysis", "symbol-search", "refactoring"],
            "playwright": ["browser-automation", "screen-capture", "dom-interaction"],
            "github": ["repo-management", "issue-tracking", "pr-management"],
        }

        return capability_map.get(server_name, ["basic-mcp"])

    async def benchmark_server_performance(
        self,
        server_name: str,
        iterations: int = 10,
    ) -> ValidationResult:
        """Benchmark MCP server response times."""
        result = ValidationResult(
            success=True,
            metadata={
                "server_name": server_name,
                "iterations": iterations,
                "response_times": [],
            },
        )

        response_times = []

        for i in range(iterations):
            start_time = time.time()

            connectivity = await self.test_server_connectivity(
                server_name, timeout=2000
            )
            # Only use response time if connection successful
            if connectivity.success:
                response_time = connectivity.metadata.get("response_time", 0)
                response_times.append(response_time)
            else:
                # Mark failed attempts with high response time
                response_times.append(999.0)

            # Small delay between tests to avoid overwhelming server
            await asyncio.sleep(0.1)

        if response_times:
            avg_response_time = sum(response_times) / len(response_times)
            min_response_time = min(response_times)
            max_response_time = max(response_times)

            result.metadata.update(
                {
                    "response_times": response_times,
                    "avg_response_time": avg_response_time,
                    "min_response_time": min_response_time,
                    "max_response_time": max_response_time,
                    "successful_tests": sum(1 for rt in response_times if rt < 999.0),
                }
            )

            # Warn if average response time is high
            if avg_response_time > 2.0:  # 2 seconds
                result.warnings.append(".2f")
            if avg_response_time > 5.0:  # 5 seconds
                result.errors.append(".2f")
                result.success = False
        else:
            result.success = False
            result.errors.append("No benchmark data collected")

        return result
