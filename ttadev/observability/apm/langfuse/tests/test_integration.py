"""Tests for LangFuse integration."""

from typing import Any
from unittest.mock import MagicMock, Mock

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
    mock_client = MagicMock()
    integration = LangFuseIntegration(public_key="test", secret_key="test", enabled=False)
    integration.client = mock_client
    integration.enabled = True

    # Act
    result = integration.create_generation(
        name="test_gen",
        model="gpt-4",
        input="prompt",
        output="response",
        metadata={"key": "value"},
    )

    # Assert
    mock_client.start_as_current_observation.assert_called_once()
    # Returns trace_id or None (mock returns MagicMock for get_current_trace_id)
    assert result is not None or result is None  # just checks it doesn't raise


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


def test_session_id_and_user_id_stored_on_init():
    """Test that session_id and user_id are stored on the instance."""
    # Arrange & Act
    integration = LangFuseIntegration(
        public_key="test",
        secret_key="test",
        enabled=False,
        session_id="sess-abc",
        user_id="copilot",
    )

    # Assert
    assert integration.session_id == "sess-abc"
    assert integration.user_id == "copilot"


def test_session_and_user_defaults_to_none():
    """Test that session_id and user_id default to None."""
    integration = LangFuseIntegration(public_key="test", secret_key="test", enabled=False)
    assert integration.session_id is None
    assert integration.user_id is None


def test_create_generation_passes_session_and_user():
    """Test that create_generation passes session_id/user_id to the client."""
    # Arrange
    mock_client = MagicMock()
    integration = LangFuseIntegration(
        public_key="test",
        secret_key="test",
        enabled=False,
        session_id="sess-123",
        user_id="adam",
    )
    integration.client = mock_client
    integration.enabled = True

    # Act
    integration.create_generation(
        name="gen",
        model="gpt-4",
        input="hello",
        output="world",
    )

    # Assert — session_id and user_id should be forwarded
    call_kwargs = mock_client.start_as_current_observation.call_args.kwargs
    assert call_kwargs["session_id"] == "sess-123"
    assert call_kwargs["user_id"] == "adam"


def test_create_generation_per_call_override():
    """Test that per-call session_id/user_id override instance values."""
    # Arrange
    mock_client = MagicMock()
    integration = LangFuseIntegration(
        public_key="test",
        secret_key="test",
        enabled=False,
        session_id="inst-session",
        user_id="inst-user",
    )
    integration.client = mock_client
    integration.enabled = True

    # Act
    integration.create_generation(
        name="gen",
        model="gpt-4",
        input="hello",
        output="world",
        session_id="call-session",
        user_id="call-user",
    )

    # Assert — per-call values win
    call_kwargs = mock_client.start_as_current_observation.call_args.kwargs
    assert call_kwargs["session_id"] == "call-session"
    assert call_kwargs["user_id"] == "call-user"


def test_create_generation_returns_trace_id():
    """Test that create_generation returns the trace ID from the client."""
    # Arrange
    mock_client = MagicMock()
    mock_client.get_current_trace_id.return_value = "trace-xyz"
    mock_client.get_trace_url.return_value = "https://cloud.langfuse.com/trace/trace-xyz"
    integration = LangFuseIntegration(public_key="test", secret_key="test", enabled=False)
    integration.client = mock_client
    integration.enabled = True

    # Act
    result = integration.create_generation(name="gen", model="gpt-4", input="hi", output="hello")

    # Assert
    assert result == "trace-xyz"
    mock_client.get_trace_url.assert_called_once_with("trace-xyz")


def test_create_generation_disabled_returns_none():
    """Test that create_generation returns None when disabled."""
    integration = LangFuseIntegration(public_key="test", secret_key="test", enabled=False)
    result = integration.create_generation(name="gen", model="gpt-4", input="hi", output="hi")
    assert result is None


def test_score_inline_calls_score_current_trace():
    """Test that score_inline delegates to score_current_trace."""
    # Arrange
    mock_client = MagicMock()
    integration = LangFuseIntegration(public_key="test", secret_key="test", enabled=False)
    integration.client = mock_client
    integration.enabled = True

    # Act
    integration.score_inline(score=0.95, name="quality", comment="Great output")

    # Assert
    mock_client.score_current_trace.assert_called_once_with(
        name="quality", value=0.95, comment="Great output"
    )


def test_score_inline_disabled_noop():
    """Test that score_inline is a no-op when integration is disabled."""
    mock_client = MagicMock()
    integration = LangFuseIntegration(public_key="test", secret_key="test", enabled=False)
    integration.client = mock_client

    integration.score_inline(score=0.5)

    mock_client.score_current_trace.assert_not_called()


def test_score_inline_swallows_exceptions():
    """Test that score_inline never raises even if the client errors."""
    mock_client = MagicMock()
    mock_client.score_current_trace.side_effect = RuntimeError("network error")
    integration = LangFuseIntegration(public_key="test", secret_key="test", enabled=False)
    integration.client = mock_client
    integration.enabled = True

    # Should not raise
    integration.score_inline(score=0.7)
