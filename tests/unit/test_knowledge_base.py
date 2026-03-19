import pytest

from ttadev.primitives.core.base import WorkflowContext
from ttadev.primitives.knowledge import KBQuery, KnowledgeBasePrimitive


def test_initialization_defaults_backend_to_unavailable() -> None:
    # Arrange / Act
    primitive = KnowledgeBasePrimitive()

    # Assert
    assert primitive.backend_available is False


@pytest.mark.asyncio
async def test_execute_returns_fallback_result_without_backend() -> None:
    # Arrange
    primitive = KnowledgeBasePrimitive()
    query = KBQuery(query_type="best_practices", topic="testing")
    context = WorkflowContext()

    # Act
    result = await primitive.execute(query, context)

    # Assert
    assert result.pages == []
    assert result.total_found == 0
    assert result.source == "fallback"


@pytest.mark.asyncio
async def test_execute_uses_backend_source_when_backend_is_available() -> None:
    # Arrange
    primitive = KnowledgeBasePrimitive(backend_available=True)
    query = KBQuery(query_type="examples", topic="testing")
    context = WorkflowContext()

    # Act
    result = await primitive.execute(query, context)

    # Assert
    assert result.pages == []
    assert result.total_found == 0
    assert result.source == "backend"
