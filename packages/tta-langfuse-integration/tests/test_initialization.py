"""Tests for Langfuse integration package."""

import os
import sys
from pathlib import Path

import pytest

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from langfuse_integration import (
    initialize_langfuse,
    is_langfuse_enabled,
    shutdown_langfuse,
)


@pytest.fixture(autouse=True)
def reset_langfuse():
    """Reset Langfuse state before each test."""
    # Clear environment variables
    old_env = {}
    for key in ["LANGFUSE_PUBLIC_KEY", "LANGFUSE_SECRET_KEY", "LANGFUSE_HOST", "LANGFUSE_ENABLED"]:
        old_env[key] = os.environ.pop(key, None)
    
    # Shutdown existing client
    shutdown_langfuse()
    
    # Reset global state
    import langfuse_integration.initialization as init_module
    init_module._langfuse_client = None
    init_module._initialized = False
    
    yield
    
    # Restore environment
    for key, value in old_env.items():
        if value is not None:
            os.environ[key] = value
    
    # Shutdown again
    shutdown_langfuse()
    init_module._langfuse_client = None
    init_module._initialized = False


def test_initialize_langfuse_without_credentials():
    """Test initialization without credentials fails gracefully."""
    result = initialize_langfuse(public_key=None, secret_key=None)
    assert result is False
    assert not is_langfuse_enabled()


def test_initialize_langfuse_disabled():
    """Test initialization can be disabled."""
    result = initialize_langfuse(public_key="test", secret_key="test", enabled=False)
    assert result is False
    assert not is_langfuse_enabled()


def test_shutdown_langfuse():
    """Test shutdown works even when not initialized."""
    # Should not raise
    shutdown_langfuse()
