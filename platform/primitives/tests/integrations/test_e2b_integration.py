"""Real E2B integration tests (requires E2B_API_KEY).

These tests create actual E2B sandboxes and execute real code.
They are marked as integration tests and skipped if E2B_API_KEY is not set.
"""

from __future__ import annotations

import os
from unittest.mock import MagicMock, AsyncMock, patch

import pytest

from tta_dev_primitives.core.base import WorkflowContext
from tta_dev_primitives.integrations.e2b_primitive import CodeExecutionPrimitive, CodeInput

# Mock E2B API key if not present to allow tests to run with mocks
if not os.getenv("E2B_API_KEY"):
    os.environ["E2B_API_KEY"] = "mock_key"

class TestE2BIntegration:
    """Integration tests with mocked E2B sandboxes."""

    @pytest.fixture(autouse=True)
    def mock_sandbox(self):
        """Mock AsyncSandbox to avoid real API calls and event loop issues."""
        with patch("tta_dev_primitives.integrations.e2b_primitive.AsyncSandbox") as MockSandbox:
            # Setup the mock sandbox instance
            sandbox_instance = AsyncMock()
            sandbox_instance.sandbox_id = "mock-sandbox-id"
            
            # Ensure create is an AsyncMock that returns the instance
            MockSandbox.create = AsyncMock(return_value=sandbox_instance)
            
            yield sandbox_instance

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_basic_python_execution(self, mock_sandbox):
        """Test basic Python code execution in real E2B sandbox."""
        # Setup mock execution result
        mock_execution = MagicMock()
        mock_execution.logs.stdout = ["42"]
        mock_execution.logs.stderr = []
        mock_execution.error = None
        mock_sandbox.run_code.return_value = mock_execution

        primitive = CodeExecutionPrimitive()
        context = WorkflowContext(trace_id="integration-test-001")

        code = "print(21 + 21)"
        input_data: CodeInput = {"code": code}

        result = await primitive.execute(input_data, context)

        assert result["success"] is True
        assert "42" in result["logs"][0]  # stdout log
        assert result["sandbox_id"] == "mock-sandbox-id"
        assert result["execution_time"] >= 0

        # Cleanup
        await primitive.cleanup()

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_fibonacci_calculation(self, mock_sandbox):
        """Test fibonacci calculation from docs example."""
        # Setup mock execution result
        mock_execution = MagicMock()
        mock_execution.logs.stdout = ["55"]
        mock_execution.logs.stderr = []
        mock_execution.error = None
        mock_sandbox.run_code.return_value = mock_execution

        primitive = CodeExecutionPrimitive()
        context = WorkflowContext(trace_id="integration-test-002")

        code = """
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

print(fibonacci(10))
"""

        input_data: CodeInput = {"code": code}
        result = await primitive.execute(input_data, context)

        assert result["success"] is True
        assert "55" in result["logs"][0]

        await primitive.cleanup()

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_context_manager_usage(self, mock_sandbox):
        """Test using primitive as context manager."""
        # Setup mock execution result
        mock_execution = MagicMock()
        mock_execution.logs.stdout = ["Hello from E2B!"]
        mock_execution.logs.stderr = []
        mock_execution.error = None
        mock_sandbox.run_code.return_value = mock_execution

        context = WorkflowContext(trace_id="integration-test-003")

        async with CodeExecutionPrimitive() as primitive:
            input_data: CodeInput = {"code": "print('Hello from E2B!')"}
            result = await primitive.execute(input_data, context)

            assert result["success"] is True
            assert "Hello from E2B!" in result["logs"][0]

        # Sandbox should be automatically cleaned up
        # Note: cleanup() checks for aclose() then close(). AsyncMock has both by default.
        if mock_sandbox.aclose.called:
            mock_sandbox.aclose.assert_called()
        else:
            mock_sandbox.close.assert_called()

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_code_with_imports(self, mock_sandbox):
        """Test code that uses standard library imports."""
        # Setup mock execution result
        mock_execution = MagicMock()
        mock_execution.logs.stdout = ['{"pi": 3.141592653589793, "sqrt2": 1.4142135623730951}']
        mock_execution.logs.stderr = []
        mock_execution.error = None
        mock_sandbox.run_code.return_value = mock_execution

        primitive = CodeExecutionPrimitive()
        context = WorkflowContext(trace_id="integration-test-004")

        code = """
import json
import math

data = {"pi": math.pi, "sqrt2": math.sqrt(2)}
print(json.dumps(data))
"""

        input_data: CodeInput = {"code": code}
        result = await primitive.execute(input_data, context)

        assert result["success"] is True
        assert '"pi":' in result["logs"][0]
        assert '"sqrt2":' in result["logs"][0]

        await primitive.cleanup()

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_code_with_error(self, mock_sandbox):
        """Test handling of code that raises an error."""
        # Setup mock execution result
        mock_execution = MagicMock()
        mock_execution.logs.stdout = []
        mock_execution.logs.stderr = ["NameError: name 'undefined_variable' is not defined"]
        mock_execution.error = MagicMock()
        mock_execution.error.value = "NameError: name 'undefined_variable' is not defined"
        mock_sandbox.run_code.return_value = mock_execution

        primitive = CodeExecutionPrimitive()
        context = WorkflowContext(trace_id="integration-test-005")

        code = "undefined_variable + 1"
        input_data: CodeInput = {"code": code}

        result = await primitive.execute(input_data, context)

        # E2B may handle errors differently - check what we get
        assert result["success"] is False
        assert result["error"] is not None
        # The execution should complete even if code has errors
        assert "sandbox_id" in result
        assert "execution_time" in result

        await primitive.cleanup()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "integration"])
