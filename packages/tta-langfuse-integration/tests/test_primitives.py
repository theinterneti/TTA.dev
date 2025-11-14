"""Tests for Langfuse primitives."""

import sys
from pathlib import Path

import pytest

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from tta_dev_primitives.core.base import WorkflowContext

from langfuse_integration import LangfusePrimitive


@pytest.mark.asyncio
async def test_langfuse_primitive_passthrough_when_disabled():
    """Test primitive passes through data when Langfuse is disabled."""
    primitive = LangfusePrimitive(name="test_llm")

    context = WorkflowContext(workflow_id="test", correlation_id="test-123")
    input_data = {"prompt": "Test prompt"}

    # Should pass through without error when Langfuse not initialized
    result = await primitive.execute(input_data, context)

    assert result == input_data


@pytest.mark.asyncio
async def test_langfuse_primitive_with_wrapped_primitive():
    """Test primitive wraps another primitive correctly."""

    # Mock wrapped primitive
    class MockPrimitive:
        async def execute(self, input_data, context):
            return {"response": "Test response", "usage": {"total_tokens": 100}}

    wrapped = MockPrimitive()
    primitive = LangfusePrimitive(primitive=wrapped, name="test_llm")

    context = WorkflowContext(workflow_id="test", correlation_id="test-123")
    input_data = {"prompt": "Test prompt"}

    result = await primitive.execute(input_data, context)

    assert result["response"] == "Test response"
    assert result["usage"]["total_tokens"] == 100
