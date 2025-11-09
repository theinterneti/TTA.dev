"""Pytest configuration and shared fixtures."""

from datetime import UTC, datetime

import pytest

from tta_rebuild import MetaconceptRegistry, TTAContext
from tta_rebuild.integrations import LLMConfig, MockLLMProvider


@pytest.fixture
def test_context() -> TTAContext:
    """Create a test TTAContext.

    Returns:
        TTAContext configured for testing
    """
    return TTAContext(
        workflow_id="test-workflow",
        correlation_id="test-correlation",
        timestamp=datetime.now(UTC),
        metaconcepts=MetaconceptRegistry.get_all(),
        player_boundaries={"violence": "low", "mature_themes": "off"},
        session_state={"player_name": "TestPlayer", "progress": 0},
    )


@pytest.fixture
def mock_llm_provider() -> MockLLMProvider:
    """Create a mock LLM provider for testing.

    Returns:
        MockLLMProvider with default configuration
    """
    return MockLLMProvider(
        config=LLMConfig(model="mock-model", max_tokens=1000),
        response="This is a generated story about a brave adventurer...",
        latency_ms=50,
    )


@pytest.fixture
def failing_mock_llm() -> MockLLMProvider:
    """Create a mock LLM that fails.

    Returns:
        MockLLMProvider configured to fail
    """
    return MockLLMProvider(
        config=LLMConfig(model="mock-model"),
        response="Never returned",
        should_fail=True,
    )
