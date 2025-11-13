"""Real E2B integration tests (requires E2B_API_KEY).

These tests create actual E2B sandboxes and execute real code.
They are marked as integration tests and skipped if E2B_API_KEY is not set.
"""

from __future__ import annotations

import os

import pytest

from tta_dev_primitives.core.base import WorkflowContext
from tta_dev_primitives.integrations.e2b_primitive import CodeExecutionPrimitive

pytestmark = pytest.mark.skipif(
    not os.getenv("E2B_API_KEY"),
    reason="E2B_API_KEY not set - skipping integration tests",
)


class TestE2BIntegration:
    """Integration tests with real E2B sandboxes."""

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_basic_python_execution(self):
        """Test basic Python code execution in real E2B sandbox."""
        primitive = CodeExecutionPrimitive()
        context = WorkflowContext(trace_id="integration-test-001")

        code = "print(21 + 21)"
        input_data = {"code": code}

        result = await primitive.execute(input_data, context)

        assert result["success"] is True
        assert "42" in result["logs"][0]  # stdout log
        assert result["sandbox_id"]  # Has a real sandbox ID
        assert result["execution_time"] > 0

        # Cleanup
        await primitive.cleanup()

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_fibonacci_calculation(self):
        """Test fibonacci calculation from docs example."""
        primitive = CodeExecutionPrimitive()
        context = WorkflowContext(trace_id="integration-test-002")

        code = """
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

print(fibonacci(10))
"""

        input_data = {"code": code}
        result = await primitive.execute(input_data, context)

        assert result["success"] is True
        assert "55" in result["logs"][0]

        await primitive.cleanup()

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_context_manager_usage(self):
        """Test using primitive as context manager."""
        context = WorkflowContext(trace_id="integration-test-003")

        async with CodeExecutionPrimitive() as primitive:
            input_data = {"code": "print('Hello from E2B!')"}
            result = await primitive.execute(input_data, context)

            assert result["success"] is True
            assert "Hello from E2B!" in result["logs"][0]

        # Sandbox should be automatically cleaned up

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_code_with_imports(self):
        """Test code that uses standard library imports."""
        primitive = CodeExecutionPrimitive()
        context = WorkflowContext(trace_id="integration-test-004")

        code = """
import json
import math

data = {"pi": math.pi, "sqrt2": math.sqrt(2)}
print(json.dumps(data))
"""

        input_data = {"code": code}
        result = await primitive.execute(input_data, context)

        assert result["success"] is True
        assert '"pi":' in result["logs"][0]
        assert '"sqrt2":' in result["logs"][0]

        await primitive.cleanup()

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_code_with_error(self):
        """Test handling of code that raises an error."""
        primitive = CodeExecutionPrimitive()
        context = WorkflowContext(trace_id="integration-test-005")

        code = "undefined_variable + 1"
        input_data = {"code": code}

        result = await primitive.execute(input_data, context)

        # E2B may handle errors differently - check what we get
        # The execution should complete even if code has errors
        assert "sandbox_id" in result
        assert "execution_time" in result

        await primitive.cleanup()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "integration"])
