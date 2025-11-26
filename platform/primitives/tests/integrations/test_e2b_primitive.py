"""Tests for E2B Code Execution Primitive.

Comprehensive test suite covering:
- Basic code execution
- Error handling
- Session rotation (1-hour limit)
- Timeout behavior
- Context manager usage
- Environment variables
- Observability integration
"""

from __future__ import annotations

import asyncio
import os
from unittest.mock import AsyncMock, Mock, patch

import pytest

from tta_dev_primitives.core.base import WorkflowContext
from tta_dev_primitives.integrations.e2b_primitive import CodeExecutionPrimitive


@pytest.fixture
def mock_e2b_api_key():
    """Provide mock E2B API key."""
    return "test-e2b-api-key"


@pytest.fixture
def mock_sandbox():
    """Create mock E2B sandbox."""
    sandbox = AsyncMock()
    sandbox.sandbox_id = "test-sandbox-123"
    sandbox.close = AsyncMock()
    sandbox.aclose = AsyncMock()

    # Mock execution result for run_code method
    mock_result = Mock()
    mock_result.error = None
    mock_result.logs = Mock(stdout=["42"], stderr=[])

    sandbox.run_code = AsyncMock(return_value=mock_result)

    return sandbox


@pytest.fixture
def workflow_context():
    """Create test workflow context."""
    return WorkflowContext(
        trace_id="test-trace-123",
        correlation_id="test-correlation-456",
    )


class TestCodeExecutionPrimitiveInit:
    """Test primitive initialization."""

    def test_init_with_api_key(self, mock_e2b_api_key):
        """Test initialization with explicit API key."""
        primitive = CodeExecutionPrimitive(api_key=mock_e2b_api_key)
        assert primitive.api_key == mock_e2b_api_key
        assert primitive.default_timeout == 30
        assert primitive.session_max_age == 3300  # 55 minutes

    def test_init_from_env_var(self, mock_e2b_api_key):
        """Test initialization from E2B_API_KEY environment variable."""
        with patch.dict(os.environ, {"E2B_API_KEY": mock_e2b_api_key}):
            primitive = CodeExecutionPrimitive()
            assert primitive.api_key == mock_e2b_api_key

    def test_init_without_api_key(self):
        """Test initialization fails without API key."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="E2B API key is required"):
                CodeExecutionPrimitive()

    def test_init_custom_params(self, mock_e2b_api_key):
        """Test initialization with custom parameters."""
        primitive = CodeExecutionPrimitive(
            api_key=mock_e2b_api_key,
            default_timeout=60,
            session_max_age=1800,  # 30 minutes
        )
        assert primitive.default_timeout == 60
        assert primitive.session_max_age == 1800


class TestCodeExecution:
    """Test code execution functionality."""

    @pytest.mark.asyncio
    async def test_basic_python_execution(self, mock_e2b_api_key, mock_sandbox, workflow_context):
        """Test basic Python code execution."""
        with patch(
            "tta_dev_primitives.integrations.e2b_primitive.AsyncSandbox.create",
            new=AsyncMock(return_value=mock_sandbox),
        ):
            primitive = CodeExecutionPrimitive(api_key=mock_e2b_api_key)

            input_data = {"code": "print(21 + 21)"}
            result = await primitive.execute(input_data, workflow_context)

            assert result["success"] is True
            assert result["output"] == "42"
            assert result["error"] is None
            assert result["sandbox_id"] == "test-sandbox-123"
            assert result["execution_time"] > 0
            assert len(result["logs"]) > 0

    @pytest.mark.asyncio
    async def test_code_with_error(self, mock_e2b_api_key, mock_sandbox, workflow_context):
        """Test code execution with errors."""
        # Mock error result
        error_result = Mock()
        error_result.results = []
        error_result.error = Mock(value="NameError: name 'undefined_var' is not defined")
        error_result.logs = Mock(stdout=[], stderr=["error log"])

        mock_sandbox.run_code = AsyncMock(return_value=error_result)

        with patch(
            "tta_dev_primitives.integrations.e2b_primitive.AsyncSandbox.create",
            new=AsyncMock(return_value=mock_sandbox),
        ):
            primitive = CodeExecutionPrimitive(api_key=mock_e2b_api_key)

            input_data = {"code": "print(undefined_var)"}
            result = await primitive.execute(input_data, workflow_context)

            assert result["success"] is False
            assert "NameError" in result["error"]
            assert len(result["logs"]) > 0

    @pytest.mark.asyncio
    async def test_execution_timeout(self, mock_e2b_api_key, mock_sandbox, workflow_context):
        """Test code execution timeout."""

        # Mock slow execution
        async def slow_exec(*args, **kwargs):
            await asyncio.sleep(10)
            return Mock(results=[], error=None, logs=Mock(stdout=[], stderr=[]))

        mock_sandbox.run_code = slow_exec

        with patch(
            "tta_dev_primitives.integrations.e2b_primitive.AsyncSandbox.create",
            new=AsyncMock(return_value=mock_sandbox),
        ):
            primitive = CodeExecutionPrimitive(api_key=mock_e2b_api_key)

            input_data = {"code": "while True: pass", "timeout": 1}

            with pytest.raises(TimeoutError, match="timed out after 1 seconds"):
                await primitive.execute(input_data, workflow_context)

    @pytest.mark.asyncio
    async def test_missing_code_input(self, mock_e2b_api_key, workflow_context):
        """Test execution fails without code."""
        primitive = CodeExecutionPrimitive(api_key=mock_e2b_api_key)

        with pytest.raises(ValueError, match="Code is required"):
            await primitive.execute({}, workflow_context)

    @pytest.mark.asyncio
    async def test_environment_variables(self, mock_e2b_api_key, mock_sandbox, workflow_context):
        """Test setting environment variables."""
        with patch(
            "tta_dev_primitives.integrations.e2b_primitive.AsyncSandbox.create",
            new=AsyncMock(return_value=mock_sandbox),
        ):
            primitive = CodeExecutionPrimitive(api_key=mock_e2b_api_key)

            input_data = {
                "code": "import os; print(os.environ.get('TEST_VAR'))",
                "env_vars": {"TEST_VAR": "test_value"},
            }

            await primitive.execute(input_data, workflow_context)

            # Verify environment variables were set via run_code helper
            run_calls = [call.args[0] for call in mock_sandbox.run_code.call_args_list]
            assert any("TEST_VAR" in c for c in run_calls)
            assert any("os.environ.get('TEST_VAR')" in c for c in run_calls)


class TestSessionManagement:
    """Test sandbox session management."""

    @pytest.mark.asyncio
    async def test_session_rotation(self, mock_e2b_api_key, mock_sandbox, workflow_context):
        """Test automatic session rotation before 1-hour limit."""
        with patch(
            "tta_dev_primitives.integrations.e2b_primitive.AsyncSandbox.create",
            new=AsyncMock(return_value=mock_sandbox),
        ):
            # Set session_max_age to 1 second for testing
            primitive = CodeExecutionPrimitive(api_key=mock_e2b_api_key, session_max_age=1)

            # First execution creates sandbox
            input_data = {"code": "print('first')"}
            await primitive.execute(input_data, workflow_context)

            # Wait for session to age
            await asyncio.sleep(1.1)

            # Second execution should rotate session
            await primitive.execute(input_data, workflow_context)

            # Verify old sandbox was closed
            mock_sandbox.aclose.assert_called()

    @pytest.mark.asyncio
    async def test_manual_cleanup(self, mock_e2b_api_key, mock_sandbox, workflow_context):
        """Test manual sandbox cleanup."""
        with patch(
            "tta_dev_primitives.integrations.e2b_primitive.AsyncSandbox.create",
            new=AsyncMock(return_value=mock_sandbox),
        ):
            primitive = CodeExecutionPrimitive(api_key=mock_e2b_api_key)

            # Create sandbox
            input_data = {"code": "print('test')"}
            await primitive.execute(input_data, workflow_context)

            # Manual cleanup
            await primitive.cleanup()

            # Verify sandbox closed
            mock_sandbox.aclose.assert_called_once()
            assert primitive._sandbox is None

    @pytest.mark.asyncio
    async def test_context_manager(self, mock_e2b_api_key, mock_sandbox, workflow_context):
        """Test using primitive as async context manager."""
        with patch(
            "tta_dev_primitives.integrations.e2b_primitive.AsyncSandbox.create",
            new=AsyncMock(return_value=mock_sandbox),
        ):
            async with CodeExecutionPrimitive(api_key=mock_e2b_api_key) as primitive:
                input_data = {"code": "print('context manager test')"}
                result = await primitive.execute(input_data, workflow_context)
                assert result["success"] is True

            # Verify cleanup happened
            mock_sandbox.aclose.assert_called_once()


class TestObservability:
    """Test observability integration."""

    @pytest.mark.asyncio
    async def test_trace_context_propagation(
        self, mock_e2b_api_key, mock_sandbox, workflow_context
    ):
        """Test that trace context is propagated."""
        with patch(
            "tta_dev_primitives.integrations.e2b_primitive.AsyncSandbox.create",
            new=AsyncMock(return_value=mock_sandbox),
        ):
            primitive = CodeExecutionPrimitive(api_key=mock_e2b_api_key)

            input_data = {"code": "print('trace test')"}
            result = await primitive.execute(input_data, workflow_context)

            # Verify context was used (primitive has InstrumentedPrimitive behavior)
            assert result["success"] is True

    @pytest.mark.asyncio
    async def test_execution_metrics(self, mock_e2b_api_key, mock_sandbox, workflow_context):
        """Test execution time metrics are recorded."""
        with patch(
            "tta_dev_primitives.integrations.e2b_primitive.AsyncSandbox.create",
            new=AsyncMock(return_value=mock_sandbox),
        ):
            primitive = CodeExecutionPrimitive(api_key=mock_e2b_api_key)

            input_data = {"code": "import time; time.sleep(0.01)"}
            result = await primitive.execute(input_data, workflow_context)

            assert "execution_time" in result
            assert result["execution_time"] >= 0


class TestEdgeCases:
    """Test edge cases and error conditions."""

    @pytest.mark.asyncio
    async def test_empty_output(self, mock_e2b_api_key, mock_sandbox, workflow_context):
        """Test code with no output."""
        empty_result = Mock()
        empty_result.results = []
        empty_result.error = None
        empty_result.logs = Mock(stdout=[], stderr=[])

        mock_sandbox.run_code = AsyncMock(return_value=empty_result)

        with patch(
            "tta_dev_primitives.integrations.e2b_primitive.AsyncSandbox.create",
            new=AsyncMock(return_value=mock_sandbox),
        ):
            primitive = CodeExecutionPrimitive(api_key=mock_e2b_api_key)

            input_data = {"code": "x = 1 + 1"}  # No print statement
            result = await primitive.execute(input_data, workflow_context)

            assert result["success"] is True
            assert result["output"] == ""
            assert result["error"] is None

    @pytest.mark.asyncio
    async def test_cleanup_error_handling(self, mock_e2b_api_key, mock_sandbox, workflow_context):
        """Test cleanup handles errors gracefully."""
        mock_sandbox.aclose = AsyncMock(side_effect=Exception("Cleanup error"))

        with patch(
            "tta_dev_primitives.integrations.e2b_primitive.AsyncSandbox.create",
            new=AsyncMock(return_value=mock_sandbox),
        ):
            primitive = CodeExecutionPrimitive(api_key=mock_e2b_api_key)

            input_data = {"code": "print('test')"}
            await primitive.execute(input_data, workflow_context)

            # Cleanup should not raise even if aclose fails
            await primitive.cleanup()
            assert primitive._sandbox is None


class TestIntegrationScenarios:
    """Test real-world integration scenarios."""

    @pytest.mark.asyncio
    async def test_fibonacci_calculation(self, mock_e2b_api_key, mock_sandbox, workflow_context):
        """Test fibonacci calculation scenario from docs."""
        fib_result = Mock()
        fib_result.results = [Mock(text="55")]
        fib_result.error = None
        fib_result.logs = Mock(stdout=["55"], stderr=[])

        mock_sandbox.run_code = AsyncMock(return_value=fib_result)

        with patch(
            "tta_dev_primitives.integrations.e2b_primitive.AsyncSandbox.create",
            new=AsyncMock(return_value=mock_sandbox),
        ):
            primitive = CodeExecutionPrimitive(api_key=mock_e2b_api_key)

            fibonacci_code = """
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

print(fibonacci(10))
"""

            input_data = {"code": fibonacci_code}
            result = await primitive.execute(input_data, workflow_context)

            assert result["success"] is True
            assert "55" in result["output"]

    @pytest.mark.asyncio
    async def test_sequential_executions(self, mock_e2b_api_key, mock_sandbox, workflow_context):
        """Test multiple sequential code executions."""
        with patch(
            "tta_dev_primitives.integrations.e2b_primitive.AsyncSandbox.create",
            new=AsyncMock(return_value=mock_sandbox),
        ):
            primitive = CodeExecutionPrimitive(api_key=mock_e2b_api_key)

            # Execute multiple times
            for i in range(3):
                input_data = {"code": f"print({i})"}
                result = await primitive.execute(input_data, workflow_context)
                assert result["success"] is True

            # Verify same sandbox was reused (no rotation)
            assert mock_sandbox.aclose.call_count == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
