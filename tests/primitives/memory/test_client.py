"""Unit tests for HindsightClient — all HTTP calls mocked."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ttadev.primitives.memory.client import HindsightClient


def _make_response(json_data: dict | list, status_code: int = 200) -> MagicMock:
    """Build a mock httpx.Response."""
    resp = MagicMock()
    resp.status_code = status_code
    resp.json.return_value = json_data
    resp.raise_for_status = MagicMock()
    return resp


class TestHindsightClientRecall:
    @pytest.mark.asyncio
    async def test_recall_returns_memory_results(self) -> None:
        client = HindsightClient(bank_id="tta-dev")
        mock_resp = _make_response(
            {
                "results": [
                    {"id": "m1", "text": "some memory", "type": "experience"},
                    {"id": "m2", "text": "another", "type": None},
                ]
            }
        )
        with patch.object(client._http, "post", new=AsyncMock(return_value=mock_resp)):
            results = await client.recall("test query")
        assert len(results) == 2
        assert results[0]["id"] == "m1"
        assert results[0]["text"] == "some memory"
        assert results[0]["type"] == "experience"
        assert results[1]["type"] is None

    @pytest.mark.asyncio
    async def test_recall_returns_empty_on_http_error(self) -> None:
        client = HindsightClient(bank_id="tta-dev")
        with patch.object(
            client._http, "post", new=AsyncMock(side_effect=Exception("conn refused"))
        ):
            results = await client.recall("test query")
        assert results == []

    @pytest.mark.asyncio
    async def test_recall_passes_budget_and_types(self) -> None:
        client = HindsightClient(bank_id="tta-dev")
        mock_resp = _make_response({"results": []})
        with patch.object(client._http, "post", new=AsyncMock(return_value=mock_resp)) as mock_post:
            await client.recall("query", budget="high", types=["experience"])
        call_kwargs = mock_post.call_args
        assert "high" in str(call_kwargs)
        assert "experience" in str(call_kwargs)

    @pytest.mark.asyncio
    async def test_recall_omits_types_when_none(self) -> None:
        client = HindsightClient(bank_id="tta-dev")
        mock_resp = _make_response({"results": []})
        with patch.object(client._http, "post", new=AsyncMock(return_value=mock_resp)) as mock_post:
            await client.recall("query")
        call_kwargs = mock_post.call_args
        body = call_kwargs.kwargs.get("json", {})
        assert "types" not in body

    @pytest.mark.asyncio
    async def test_recall_returns_empty_list_on_empty_results(self) -> None:
        client = HindsightClient(bank_id="tta-dev")
        mock_resp = _make_response({"results": []})
        with patch.object(client._http, "post", new=AsyncMock(return_value=mock_resp)):
            results = await client.recall("query")
        assert results == []


class TestHindsightClientRetain:
    @pytest.mark.asyncio
    async def test_retain_returns_success(self) -> None:
        client = HindsightClient(bank_id="tta-dev")
        mock_resp = _make_response({"success": True, "operation_id": "op-123", "async": True})
        with patch.object(client._http, "post", new=AsyncMock(return_value=mock_resp)):
            result = await client.retain("some content")
        assert result["success"] is True
        assert result["operation_id"] == "op-123"

    @pytest.mark.asyncio
    async def test_retain_returns_failure_on_error(self) -> None:
        client = HindsightClient(bank_id="tta-dev")
        with patch.object(client._http, "post", new=AsyncMock(side_effect=Exception("timeout"))):
            result = await client.retain("some content")
        assert result["success"] is False
        assert result["operation_id"] is None

    @pytest.mark.asyncio
    async def test_retain_sends_async_flag(self) -> None:
        client = HindsightClient(bank_id="tta-dev")
        mock_resp = _make_response({"success": True, "operation_id": None})
        with patch.object(client._http, "post", new=AsyncMock(return_value=mock_resp)) as mock_post:
            await client.retain("content", async_=False)
        body = mock_post.call_args.kwargs.get("json", {})
        assert body.get("async") is False


class TestHindsightClientDirectives:
    @pytest.mark.asyncio
    async def test_get_directives_returns_list_of_strings(self) -> None:
        client = HindsightClient(bank_id="tta-dev")
        mock_resp = _make_response(
            {
                "directives": [
                    {"content": "Always orient first"},
                    {"content": "Use uv"},
                ]
            }
        )
        with patch.object(client._http, "get", new=AsyncMock(return_value=mock_resp)):
            result = await client.get_directives()
        assert result == ["Always orient first", "Use uv"]

    @pytest.mark.asyncio
    async def test_get_directives_handles_list_response(self) -> None:
        """Handles a bare list response (not wrapped in dict)."""
        client = HindsightClient(bank_id="tta-dev")
        mock_resp = _make_response([{"content": "Do X"}, {"content": "Do Y"}])
        mock_resp.json.return_value = [{"content": "Do X"}, {"content": "Do Y"}]
        with patch.object(client._http, "get", new=AsyncMock(return_value=mock_resp)):
            result = await client.get_directives()
        assert result == ["Do X", "Do Y"]

    @pytest.mark.asyncio
    async def test_get_directives_returns_empty_on_error(self) -> None:
        client = HindsightClient(bank_id="tta-dev")
        with patch.object(
            client._http, "get", new=AsyncMock(side_effect=Exception("conn refused"))
        ):
            result = await client.get_directives()
        assert result == []


class TestHindsightClientMentalModels:
    @pytest.mark.asyncio
    async def test_get_mental_model_returns_content(self) -> None:
        client = HindsightClient(bank_id="tta-dev")
        mock_resp = _make_response(
            {
                "mental_models": [
                    {"name": "primitives", "content": "The primitives system..."},
                    {"name": "other", "content": "Other stuff"},
                ]
            }
        )
        with patch.object(client._http, "get", new=AsyncMock(return_value=mock_resp)):
            result = await client.get_mental_model("primitives")
        assert result == "The primitives system..."

    @pytest.mark.asyncio
    async def test_get_mental_model_returns_none_when_not_found(self) -> None:
        client = HindsightClient(bank_id="tta-dev")
        mock_resp = _make_response({"mental_models": []})
        with patch.object(client._http, "get", new=AsyncMock(return_value=mock_resp)):
            result = await client.get_mental_model("unknown")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_mental_model_returns_none_on_error(self) -> None:
        client = HindsightClient(bank_id="tta-dev")
        with patch.object(client._http, "get", new=AsyncMock(side_effect=Exception("timeout"))):
            result = await client.get_mental_model("primitives")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_mental_model_handles_list_response(self) -> None:
        """Handles a bare list response (not wrapped in dict)."""
        client = HindsightClient(bank_id="tta-dev")
        mock_resp = MagicMock()
        mock_resp.raise_for_status = MagicMock()
        mock_resp.json.return_value = [{"name": "primitives", "content": "System..."}]
        with patch.object(client._http, "get", new=AsyncMock(return_value=mock_resp)):
            result = await client.get_mental_model("primitives")
        assert result == "System..."


class TestHindsightClientAvailability:
    def test_is_available_returns_true_when_healthy(self) -> None:
        client = HindsightClient(bank_id="tta-dev")
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        with patch("httpx.get", return_value=mock_resp):
            result = client.is_available()
        assert result is True

    def test_is_available_returns_false_on_error(self) -> None:
        client = HindsightClient(bank_id="tta-dev")
        with patch("httpx.get", side_effect=Exception("conn refused")):
            result = client.is_available()
        assert result is False

    def test_is_available_returns_false_on_non_200(self) -> None:
        client = HindsightClient(bank_id="tta-dev")
        mock_resp = MagicMock()
        mock_resp.status_code = 503
        with patch("httpx.get", return_value=mock_resp):
            result = client.is_available()
        assert result is False
