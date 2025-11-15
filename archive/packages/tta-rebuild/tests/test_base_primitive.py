"""Tests for core base primitive and context."""

from datetime import datetime

import pytest

from tta_rebuild.core import (
    TTAContext,
    TTAPrimitive,
)


class TestTTAContext:
    """Tests for TTAContext dataclass."""

    def test_context_creation(self) -> None:
        """Test basic context creation."""
        context = TTAContext(
            workflow_id="test-workflow",
            correlation_id="test-123",
            timestamp=datetime.now(),
            metaconcepts=["Test Metaconcept"],
            player_boundaries={},
            session_state={},
        )

        assert context.workflow_id == "test-workflow"
        assert context.correlation_id == "test-123"
        assert context.universe_id is None
        assert len(context.metaconcepts) == 1

    def test_with_universe(self) -> None:
        """Test creating context with updated universe_id."""
        original = TTAContext(
            workflow_id="test-workflow",
            correlation_id="test-123",
            timestamp=datetime.now(),
            metaconcepts=[],
            player_boundaries={},
            session_state={},
        )

        updated = original.with_universe("universe-001")

        assert updated.universe_id == "universe-001"
        assert updated.workflow_id == original.workflow_id
        assert original.universe_id is None  # Original unchanged

    def test_with_metaconcepts(self) -> None:
        """Test creating context with updated metaconcepts."""
        original = TTAContext(
            workflow_id="test-workflow",
            correlation_id="test-123",
            timestamp=datetime.now(),
            metaconcepts=["Original"],
            player_boundaries={},
            session_state={},
        )

        updated = original.with_metaconcepts(["New1", "New2"])

        assert len(updated.metaconcepts) == 2
        assert "New1" in updated.metaconcepts
        assert len(original.metaconcepts) == 1  # Original unchanged


class SimplePrimitive(TTAPrimitive[str, str]):
    """Simple test primitive."""

    async def execute(self, input_data: str, context: TTAContext) -> str:
        """Echo input data with prefix."""
        return f"Processed: {input_data}"


class TestTTAPrimitive:
    """Tests for TTAPrimitive base class."""

    @pytest.mark.asyncio
    async def test_primitive_execution(self) -> None:
        """Test basic primitive execution."""
        primitive = SimplePrimitive(name="TestPrimitive")
        context = TTAContext(
            workflow_id="test",
            correlation_id="test-123",
            timestamp=datetime.now(),
            metaconcepts=[],
            player_boundaries={},
            session_state={},
        )

        result = await primitive.execute("test input", context)

        assert result == "Processed: test input"
        assert primitive.name == "TestPrimitive"

    def test_primitive_repr(self) -> None:
        """Test primitive string representation."""
        primitive = SimplePrimitive(name="Test")
        repr_str = repr(primitive)

        assert "SimplePrimitive" in repr_str
        assert "Test" in repr_str
