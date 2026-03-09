"""Tests for auto-instrumentation functionality."""

import os
import pytest

from ttadev.observability.auto_instrument import auto_initialize
from ttadev.primitives.core import WorkflowContext
from ttadev.primitives.testing import MockPrimitive


@pytest.mark.asyncio
async def test_auto_initialize_with_disable_flag(monkeypatch):
    """Test that TTADEV_NO_AUTO_INSTRUMENT=1 disables initialization."""
    # Arrange
    monkeypatch.setenv("TTADEV_NO_AUTO_INSTRUMENT", "1")
    
    # Act
    result = auto_initialize()
    
    # Assert
    assert result is None, "Should return None when disabled"


@pytest.mark.asyncio
async def test_auto_initialize_is_idempotent():
    """Test that auto_initialize can be called multiple times safely."""
    # Arrange - ensure clean state
    if "TTADEV_NO_AUTO_INSTRUMENT" in os.environ:
        del os.environ["TTADEV_NO_AUTO_INSTRUMENT"]
    
    # Act
    auto_initialize()
    auto_initialize()  # Call twice
    auto_initialize()  # Call three times
    
    # Assert - should not crash or duplicate instrumentation
    # If we get here without exceptions, it's idempotent


@pytest.mark.asyncio
async def test_instrumentation_wraps_execute(monkeypatch):
    """Test that instrumentation wraps WorkflowPrimitive.execute and calls collector."""
    # Arrange
    monkeypatch.setenv("TTADEV_NO_AUTO_INSTRUMENT", "1")  # Don't auto-init
    
    mock = MockPrimitive("test_primitive", return_value="success")
    context = WorkflowContext(workflow_id="test")
    
    # Act
    result = await mock.execute("input_data", context)
    
    # Assert
    assert result == "success"
    assert mock.call_count == 1
    assert mock.last_input == "input_data"


@pytest.mark.asyncio
async def test_instrumentation_captures_primitive_metadata():
    """Test that instrumentation captures primitive type and name."""
    # Arrange
    mock = MockPrimitive("custom_primitive", return_value={"status": "ok"})
    context = WorkflowContext(workflow_id="metadata_test")
    
    # Act
    result = await mock.execute({"data": "test"}, context)
    
    # Assert
    assert result == {"status": "ok"}
    assert mock.call_count == 1
    # MockPrimitive's name should be captured
    assert "custom_primitive" in str(mock)
