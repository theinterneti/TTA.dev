"""Tests for LangFuse integration."""

from typing import Any
from unittest.mock import Mock

import pytest
from ttadev.primitives.core.base import WorkflowContext
from ttadev.primitives.testing import MockPrimitive

from tta_apm_langfuse.integration import LangFuseIntegration, auto_instrument


@pytest.mark.asyncio
async def test_integration_disabled():
    """Test that disabled integration does not instrument."""
    # Arrange
    integration = LangFuseIntegration(public_key="test", secret_key="test", enabled=False)
    primitive = MockPrimitive("test", return_value="result")

    # Act
    instrumented = integration.instrument(primitive)
    context = WorkflowContext(workflow_id="test")
    result = await instrumented.execute("input", context)

    # Assert
    assert result == "result"
    assert primitive.call_count == 1


@pytest.mark.asyncio
async def test_integration_handles_errors():
    """Test that integration captures errors."""
    # Arrange
    integration = LangFuseIntegration(public_key="pk_test", secret_key="sk_test", enabled=False)

    async def raise_error(data: Any, ctx: Any) -> Any:
        raise ValueError("Test error")

    primitive = MockPrimitive("test", side_effect=raise_error)

    # Act & Assert
    instrumented = integration.instrument(primitive)
    context = WorkflowContext(workflow_id="test")

    with pytest.raises(ValueError, match="Test error"):
        await instrumented.execute("input", context)


@pytest.mark.asyncio
async def test_auto_instrument():
    """Test automatic instrumentation of multiple primitives."""
    # Arrange
    integration = LangFuseIntegration(public_key="test", secret_key="test", enabled=False)
    primitives = [
        MockPrimitive("p1", return_value="r1"),
        MockPrimitive("p2", return_value="r2"),
        MockPrimitive("p3", return_value="r3"),
    ]

    # Act
    instrumented = auto_instrument(primitives, integration)
    context = WorkflowContext(workflow_id="test")

    # Assert
    assert len(instrumented) == 3
    for i, prim in enumerate(instrumented):
        result = await prim.execute("input", context)
        assert result == f"r{i + 1}"


def test_create_generation():
    """Test generation recording."""
    # Arrange
    mock_client = Mock()
    integration = LangFuseIntegration(public_key="test", secret_key="test", enabled=False)
    integration.client = mock_client
    integration.enabled = True

    # Act
    integration.create_generation(
        name="test_gen",
        model="gpt-4",
        input="prompt",
        output="response",
        metadata={"key": "value"},
    )

    # Assert
    mock_client.start_as_current_observation.assert_called_once()


def test_flush():
    """Test synchronous flush."""
    # Arrange
    mock_client = Mock()
    integration = LangFuseIntegration(public_key="test", secret_key="test", enabled=False)
    integration.client = mock_client
    integration.enabled = True

    # Act
    integration.flush()

    # Assert
    mock_client.flush.assert_called_once()


@pytest.mark.asyncio
async def test_aflush():
    """Test asynchronous flush."""
    # Arrange
    mock_client = Mock()
    integration = LangFuseIntegration(public_key="test", secret_key="test", enabled=False)
    integration.client = mock_client
    integration.enabled = True

    # Act
    await integration.aflush()

    # Assert
    mock_client.flush.assert_called_once()
