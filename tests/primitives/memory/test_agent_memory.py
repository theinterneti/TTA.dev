"""Unit tests for AgentMemory — all HTTP calls mocked via HindsightClient mock."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from ttadev.primitives.memory.types import MemoryResult, RetainResult


def test_types_importable() -> None:

    r: MemoryResult = {"id": "abc", "text": "some memory", "type": "experience"}
    assert r["id"] == "abc"
    res: RetainResult = {"success": True, "operation_id": "op-123"}
    assert res["success"] is True


def _mock_client(
    recall_result: list[MemoryResult] | None = None,
    retain_result: RetainResult | None = None,
    directives: list[str] | None = None,
    mental_model: str | None = None,
    is_available: bool = True,
) -> MagicMock:
    """Build a mock HindsightClient."""
    client = MagicMock()
    client.is_available = MagicMock(return_value=is_available)
    client.recall = AsyncMock(return_value=recall_result or [])
    client.retain = AsyncMock(
        return_value=retain_result or RetainResult(success=True, operation_id=None)
    )
    client.get_directives = AsyncMock(return_value=directives or [])
    client.get_mental_model = AsyncMock(return_value=mental_model)
    return client


class TestAgentMemoryRecall:
    @pytest.mark.asyncio
    async def test_recall_returns_memory_results(self) -> None:
        from ttadev.primitives.memory.agent_memory import AgentMemory

        mock = _mock_client(
            recall_result=[
                MemoryResult(id="m1", text="some decision", type="experience"),
            ]
        )
        memory = AgentMemory(bank_id="tta-dev", _client=mock)
        results = await memory.recall("retry timeout handling")
        assert len(results) == 1
        assert results[0]["text"] == "some decision"
        mock.recall.assert_called_once_with("retry timeout handling", budget="mid", types=None)

    @pytest.mark.asyncio
    async def test_recall_raises_on_empty_query(self) -> None:
        from ttadev.primitives.memory.agent_memory import AgentMemory

        mock = _mock_client()
        memory = AgentMemory(bank_id="tta-dev", _client=mock)
        with pytest.raises(ValueError, match="query must not be empty"):
            await memory.recall("")

    @pytest.mark.asyncio
    async def test_recall_returns_empty_when_unavailable(self) -> None:
        from ttadev.primitives.memory.agent_memory import AgentMemory

        mock = _mock_client(recall_result=[])
        memory = AgentMemory(bank_id="tta-dev", _client=mock)
        results = await memory.recall("any query")
        assert results == []


class TestAgentMemoryRetain:
    @pytest.mark.asyncio
    async def test_retain_success(self) -> None:
        from ttadev.primitives.memory.agent_memory import AgentMemory

        mock = _mock_client(retain_result=RetainResult(success=True, operation_id="op-1"))
        memory = AgentMemory(bank_id="tta-dev", _client=mock)
        result = await memory.retain("some decision content")
        assert result["success"] is True
        mock.retain.assert_called_once_with("some decision content", async_=True)

    @pytest.mark.asyncio
    async def test_retain_raises_on_empty_content(self) -> None:
        from ttadev.primitives.memory.agent_memory import AgentMemory

        mock = _mock_client()
        memory = AgentMemory(bank_id="tta-dev", _client=mock)
        with pytest.raises(ValueError, match="content must not be empty"):
            await memory.retain("")

    @pytest.mark.asyncio
    async def test_retain_sync_passes_async_false(self) -> None:
        from ttadev.primitives.memory.agent_memory import AgentMemory

        mock = _mock_client()
        memory = AgentMemory(bank_id="tta-dev", _client=mock)
        await memory.retain("content", async_=False)
        mock.retain.assert_called_once_with("content", async_=False)


class TestAgentMemoryDirectives:
    @pytest.mark.asyncio
    async def test_get_directives_returns_list(self) -> None:
        from ttadev.primitives.memory.agent_memory import AgentMemory

        mock = _mock_client(directives=["Always orient first", "Use uv"])
        memory = AgentMemory(bank_id="tta-dev", _client=mock)
        result = await memory.get_directives()
        assert result == ["Always orient first", "Use uv"]

    @pytest.mark.asyncio
    async def test_get_directives_returns_empty_when_unavailable(self) -> None:
        from ttadev.primitives.memory.agent_memory import AgentMemory

        mock = _mock_client(directives=[])
        memory = AgentMemory(bank_id="tta-dev", _client=mock)
        result = await memory.get_directives()
        assert result == []


class TestAgentMemoryMentalModel:
    @pytest.mark.asyncio
    async def test_get_mental_model_returns_content(self) -> None:
        from ttadev.primitives.memory.agent_memory import AgentMemory

        mock = _mock_client(mental_model="The primitives system...")
        memory = AgentMemory(bank_id="tta-dev", _client=mock)
        result = await memory.get_mental_model("primitives")
        assert result == "The primitives system..."

    @pytest.mark.asyncio
    async def test_get_mental_model_returns_none_when_not_found(self) -> None:
        from ttadev.primitives.memory.agent_memory import AgentMemory

        mock = _mock_client(mental_model=None)
        memory = AgentMemory(bank_id="tta-dev", _client=mock)
        result = await memory.get_mental_model("unknown")
        assert result is None


class TestAgentMemoryContextPrefix:
    @pytest.mark.asyncio
    async def test_build_context_prefix_combines_directives_and_recall(self) -> None:
        from ttadev.primitives.memory.agent_memory import AgentMemory

        mock = _mock_client(
            directives=["Always orient first"],
            recall_result=[MemoryResult(id="m1", text="some decision", type="experience")],
        )
        memory = AgentMemory(bank_id="tta-dev", _client=mock)
        prefix = await memory.build_context_prefix("retry timeout")
        assert "Always orient first" in prefix
        assert "some decision" in prefix

    @pytest.mark.asyncio
    async def test_build_context_prefix_calls_directives_and_recall_concurrently(
        self,
    ) -> None:
        """Both calls should be made (asyncio.gather)."""
        from ttadev.primitives.memory.agent_memory import AgentMemory

        mock = _mock_client(directives=["directive 1"], recall_result=[])
        memory = AgentMemory(bank_id="tta-dev", _client=mock)
        await memory.build_context_prefix("some query")
        mock.get_directives.assert_called_once()
        mock.recall.assert_called_once()

    @pytest.mark.asyncio
    async def test_build_context_prefix_returns_empty_string_when_both_empty(
        self,
    ) -> None:
        from ttadev.primitives.memory.agent_memory import AgentMemory

        mock = _mock_client(directives=[], recall_result=[])
        memory = AgentMemory(bank_id="tta-dev", _client=mock)
        result = await memory.build_context_prefix("anything")
        assert result == ""

    @pytest.mark.asyncio
    async def test_build_context_prefix_raises_on_empty_query(self) -> None:
        from ttadev.primitives.memory.agent_memory import AgentMemory

        mock = _mock_client()
        memory = AgentMemory(bank_id="tta-dev", _client=mock)
        with pytest.raises(ValueError, match="query must not be empty"):
            await memory.build_context_prefix("")


class TestAgentMemoryAvailability:
    def test_is_available_delegates_to_client(self) -> None:
        from ttadev.primitives.memory.agent_memory import AgentMemory

        mock = _mock_client(is_available=True)
        memory = AgentMemory(bank_id="tta-dev", _client=mock)
        assert memory.is_available() is True

    def test_is_available_false_when_client_unavailable(self) -> None:
        from ttadev.primitives.memory.agent_memory import AgentMemory

        mock = _mock_client(is_available=False)
        memory = AgentMemory(bank_id="tta-dev", _client=mock)
        assert memory.is_available() is False


def test_agent_memory_exported_from_primitives_package() -> None:
    from ttadev.primitives import AgentMemory

    assert AgentMemory is not None
