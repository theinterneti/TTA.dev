"""Tests for Langfuse pull-back endpoints in the observability server.

Tests verify:
- Graceful degradation when LANGFUSE_PUBLIC_KEY/SECRET_KEY are not set.
- Correct JSON shape when credentials are set (httpx mocked).
- Graceful timeout handling.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from ttadev.observability.server import ObservabilityServer, _estimate_cost, _langfuse_creds

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_server() -> ObservabilityServer:
    """Return a fresh ObservabilityServer with a temp data dir."""
    import tempfile
    from pathlib import Path

    tmp = tempfile.mkdtemp()
    return ObservabilityServer(port=0, data_dir=Path(tmp))


def _make_resp(body: Any, status: int = 200) -> httpx.Response:
    """Build an httpx.Response with a dummy request so raise_for_status() works."""
    req = httpx.Request("GET", "http://langfuse.test/")
    return httpx.Response(status, json=body, request=req)


async def _make_client(server: ObservabilityServer) -> TestClient:
    """Wire up the aiohttp TestClient without starting the TCP listener."""
    runner = web.AppRunner(server.app)
    await runner.setup()
    return TestClient(TestServer(server.app))


# ---------------------------------------------------------------------------
# Helper — _langfuse_creds
# ---------------------------------------------------------------------------


def test_langfuse_creds_returns_none_when_vars_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("LANGFUSE_PUBLIC_KEY", raising=False)
    monkeypatch.delenv("LANGFUSE_SECRET_KEY", raising=False)
    assert _langfuse_creds() is None


def test_langfuse_creds_returns_none_when_only_public_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", "pk-test")
    monkeypatch.delenv("LANGFUSE_SECRET_KEY", raising=False)
    assert _langfuse_creds() is None


def test_langfuse_creds_returns_none_when_only_secret_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("LANGFUSE_PUBLIC_KEY", raising=False)
    monkeypatch.setenv("LANGFUSE_SECRET_KEY", "sk-test")
    assert _langfuse_creds() is None


def test_langfuse_creds_returns_tuple_when_both_set(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", "pk-lf-abc")
    monkeypatch.setenv("LANGFUSE_SECRET_KEY", "sk-lf-xyz")
    monkeypatch.delenv("LANGFUSE_HOST", raising=False)
    result = _langfuse_creds()
    assert result is not None
    host, pk, sk = result
    assert pk == "pk-lf-abc"
    assert sk == "sk-lf-xyz"
    assert host == "https://cloud.langfuse.com"


def test_langfuse_creds_respects_custom_host(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", "pk-lf-abc")
    monkeypatch.setenv("LANGFUSE_SECRET_KEY", "sk-lf-xyz")
    monkeypatch.setenv("LANGFUSE_HOST", "https://my.langfuse.internal")
    host, _, _ = _langfuse_creds()  # type: ignore[misc]
    assert host == "https://my.langfuse.internal"


def test_langfuse_creds_strips_trailing_slash(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", "pk")
    monkeypatch.setenv("LANGFUSE_SECRET_KEY", "sk")
    monkeypatch.setenv("LANGFUSE_HOST", "https://host.example.com/")
    host, _, _ = _langfuse_creds()  # type: ignore[misc]
    assert not host.endswith("/")


# ---------------------------------------------------------------------------
# Helper — _estimate_cost
# ---------------------------------------------------------------------------


def test_estimate_cost_known_model() -> None:
    cost = _estimate_cost("gpt-4o", 1_000_000, 1_000_000)
    assert cost == pytest.approx(2.50 + 10.00, rel=1e-4)


def test_estimate_cost_unknown_model_returns_zero() -> None:
    cost = _estimate_cost("totally-unknown-model-xyz", 100_000, 50_000)
    assert cost == 0.0


def test_estimate_cost_fuzzy_matches_model_substring() -> None:
    # "gpt-4o-mini" should match the "gpt-4o-mini" entry
    cost = _estimate_cost("openai/gpt-4o-mini", 1_000_000, 0)
    assert cost == pytest.approx(0.15, rel=1e-4)


def test_estimate_cost_zero_tokens_returns_zero() -> None:
    assert _estimate_cost("gpt-4o", 0, 0) == 0.0


# ---------------------------------------------------------------------------
# Endpoint — /api/v2/langfuse/trace/{trace_id}
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_langfuse_trace_unavailable_when_no_creds(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("LANGFUSE_PUBLIC_KEY", raising=False)
    monkeypatch.delenv("LANGFUSE_SECRET_KEY", raising=False)
    server = _make_server()
    async with TestClient(TestServer(server.app)) as client:
        resp = await client.get("/api/v2/langfuse/trace/abc123")
        assert resp.status == 200
        data = await resp.json()
        assert data["available"] is False
        assert "reason" in data


@pytest.mark.asyncio
async def test_langfuse_trace_returns_correct_shape(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", "pk-lf")
    monkeypatch.setenv("LANGFUSE_SECRET_KEY", "sk-lf")

    fake_trace = {"id": "abc123", "name": "test-trace"}
    fake_gens: dict[str, Any] = {"data": [{"id": "g1", "usage": {"input": 10, "output": 5}}]}
    fake_scores: dict[str, Any] = {"data": [{"id": "s1", "name": "quality", "value": 0.9}]}

    def _make_response(body: Any) -> httpx.Response:
        return _make_resp(body)

    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.get = AsyncMock(
        side_effect=[
            _make_response(fake_trace),
            _make_response(fake_gens),
            _make_response(fake_scores),
        ]
    )

    with patch("ttadev.observability.server.httpx.AsyncClient", return_value=mock_client):
        server = _make_server()
        async with TestClient(TestServer(server.app)) as client:
            resp = await client.get("/api/v2/langfuse/trace/abc123")
            assert resp.status == 200
            data = await resp.json()
    assert data["available"] is True
    assert "trace" in data
    assert "generations" in data
    assert "scores" in data


@pytest.mark.asyncio
async def test_langfuse_trace_graceful_on_timeout(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", "pk-lf")
    monkeypatch.setenv("LANGFUSE_SECRET_KEY", "sk-lf")

    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.get = AsyncMock(side_effect=httpx.TimeoutException("timed out"))

    with patch("ttadev.observability.server.httpx.AsyncClient", return_value=mock_client):
        server = _make_server()
        async with TestClient(TestServer(server.app)) as client:
            resp = await client.get("/api/v2/langfuse/trace/abc123")
            assert resp.status == 200
            data = await resp.json()
    assert data["available"] is False
    assert "timed out" in data["reason"].lower()


@pytest.mark.asyncio
async def test_langfuse_trace_graceful_on_http_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", "pk-lf")
    monkeypatch.setenv("LANGFUSE_SECRET_KEY", "sk-lf")

    err_response = httpx.Response(401, text="Unauthorized")
    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.get = AsyncMock(
        side_effect=httpx.HTTPStatusError("401", request=MagicMock(), response=err_response)
    )

    with patch("ttadev.observability.server.httpx.AsyncClient", return_value=mock_client):
        server = _make_server()
        async with TestClient(TestServer(server.app)) as client:
            resp = await client.get("/api/v2/langfuse/trace/abc123")
            assert resp.status == 200
            data = await resp.json()
    assert data["available"] is False
    assert "401" in data["reason"]


# ---------------------------------------------------------------------------
# Endpoint — /api/v2/langfuse/session/cost
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_langfuse_session_cost_unavailable_when_no_creds(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("LANGFUSE_PUBLIC_KEY", raising=False)
    monkeypatch.delenv("LANGFUSE_SECRET_KEY", raising=False)
    server = _make_server()
    async with TestClient(TestServer(server.app)) as client:
        resp = await client.get("/api/v2/langfuse/session/cost")
        assert resp.status == 200
        data = await resp.json()
        assert data["available"] is False
        assert "reason" in data


@pytest.mark.asyncio
async def test_langfuse_session_cost_correct_shape(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", "pk-lf")
    monkeypatch.setenv("LANGFUSE_SECRET_KEY", "sk-lf")

    fake_obs = {
        "data": [
            {"model": "gpt-4o", "usage": {"input": 1000, "output": 500}},
            {"model": "gpt-4o-mini", "usage": {"input": 200, "output": 100}},
            {"model": "gpt-4o", "usage": {"input": 300, "output": 150}},
        ]
    }

    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.get = AsyncMock(return_value=_make_resp(fake_obs))

    with patch("ttadev.observability.server.httpx.AsyncClient", return_value=mock_client):
        server = _make_server()
        async with TestClient(TestServer(server.app)) as client:
            resp = await client.get("/api/v2/langfuse/session/cost")
            assert resp.status == 200
            data = await resp.json()

    assert data["available"] is True
    assert data["total_input_tokens"] == 1500
    assert data["total_output_tokens"] == 750
    assert data["total_tokens"] == 2250
    assert isinstance(data["estimated_cost_usd"], float)
    assert isinstance(data["top_models"], list)
    assert len(data["top_models"]) <= 3


@pytest.mark.asyncio
async def test_langfuse_session_cost_top_models_sorted_by_cost(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", "pk-lf")
    monkeypatch.setenv("LANGFUSE_SECRET_KEY", "sk-lf")

    # gpt-4 is very expensive; gpt-4o-mini is cheap
    fake_obs = {
        "data": [
            {"model": "gpt-4", "usage": {"input": 100_000, "output": 50_000}},
            {"model": "gpt-4o-mini", "usage": {"input": 100_000, "output": 50_000}},
        ]
    }
    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.get = AsyncMock(return_value=_make_resp(fake_obs))

    with patch("ttadev.observability.server.httpx.AsyncClient", return_value=mock_client):
        server = _make_server()
        async with TestClient(TestServer(server.app)) as client:
            resp = await client.get("/api/v2/langfuse/session/cost")
            data = await resp.json()

    top = data["top_models"]
    assert top[0]["model"] == "gpt-4"  # highest cost first


@pytest.mark.asyncio
async def test_langfuse_session_cost_graceful_on_timeout(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", "pk-lf")
    monkeypatch.setenv("LANGFUSE_SECRET_KEY", "sk-lf")

    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.get = AsyncMock(side_effect=httpx.TimeoutException("timed out"))

    with patch("ttadev.observability.server.httpx.AsyncClient", return_value=mock_client):
        server = _make_server()
        async with TestClient(TestServer(server.app)) as client:
            resp = await client.get("/api/v2/langfuse/session/cost")
            data = await resp.json()
    assert data["available"] is False


@pytest.mark.asyncio
async def test_langfuse_session_cost_handles_list_response(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Langfuse may return a bare list instead of {data: [...]}."""
    monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", "pk-lf")
    monkeypatch.setenv("LANGFUSE_SECRET_KEY", "sk-lf")

    fake_obs = [{"model": "claude-3-5-sonnet", "usage": {"input": 500, "output": 200}}]
    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.get = AsyncMock(return_value=_make_resp(fake_obs))

    with patch("ttadev.observability.server.httpx.AsyncClient", return_value=mock_client):
        server = _make_server()
        async with TestClient(TestServer(server.app)) as client:
            resp = await client.get("/api/v2/langfuse/session/cost")
            data = await resp.json()
    assert data["available"] is True
    assert data["total_input_tokens"] == 500


@pytest.mark.asyncio
async def test_langfuse_session_cost_handles_missing_usage_fields(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Observations with no usage field must not crash the handler."""
    monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", "pk-lf")
    monkeypatch.setenv("LANGFUSE_SECRET_KEY", "sk-lf")

    fake_obs = {"data": [{"model": "gpt-4o", "usage": None}]}
    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.get = AsyncMock(return_value=_make_resp(fake_obs))

    with patch("ttadev.observability.server.httpx.AsyncClient", return_value=mock_client):
        server = _make_server()
        async with TestClient(TestServer(server.app)) as client:
            resp = await client.get("/api/v2/langfuse/session/cost")
            data = await resp.json()
    assert data["available"] is True
    assert data["total_tokens"] == 0


# ---------------------------------------------------------------------------
# Endpoint — /api/v2/langfuse/scores
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_langfuse_scores_unavailable_when_no_creds(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("LANGFUSE_PUBLIC_KEY", raising=False)
    monkeypatch.delenv("LANGFUSE_SECRET_KEY", raising=False)
    server = _make_server()
    async with TestClient(TestServer(server.app)) as client:
        resp = await client.get("/api/v2/langfuse/scores")
        assert resp.status == 200
        data = await resp.json()
        assert data["available"] is False
        assert "reason" in data


@pytest.mark.asyncio
async def test_langfuse_scores_correct_shape(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", "pk-lf")
    monkeypatch.setenv("LANGFUSE_SECRET_KEY", "sk-lf")

    fake_scores = {
        "data": [
            {"id": "s1", "name": "quality", "value": 0.9, "traceId": "t1"},
            {"id": "s2", "name": "relevance", "value": 0.7, "traceId": "t2"},
        ]
    }
    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.get = AsyncMock(return_value=_make_resp(fake_scores))

    with patch("ttadev.observability.server.httpx.AsyncClient", return_value=mock_client):
        server = _make_server()
        async with TestClient(TestServer(server.app)) as client:
            resp = await client.get("/api/v2/langfuse/scores")
            assert resp.status == 200
            data = await resp.json()

    assert data["available"] is True
    assert isinstance(data["scores"], list)
    assert len(data["scores"]) == 2
    assert data["scores"][0]["name"] == "quality"


@pytest.mark.asyncio
async def test_langfuse_scores_handles_list_response(monkeypatch: pytest.MonkeyPatch) -> None:
    """Langfuse may return a bare list."""
    monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", "pk-lf")
    monkeypatch.setenv("LANGFUSE_SECRET_KEY", "sk-lf")

    fake_scores = [{"id": "s1", "name": "quality", "value": 1.0}]
    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.get = AsyncMock(return_value=_make_resp(fake_scores))

    with patch("ttadev.observability.server.httpx.AsyncClient", return_value=mock_client):
        server = _make_server()
        async with TestClient(TestServer(server.app)) as client:
            resp = await client.get("/api/v2/langfuse/scores")
            data = await resp.json()
    assert data["available"] is True
    assert data["scores"][0]["name"] == "quality"


@pytest.mark.asyncio
async def test_langfuse_scores_graceful_on_timeout(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", "pk-lf")
    monkeypatch.setenv("LANGFUSE_SECRET_KEY", "sk-lf")

    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.get = AsyncMock(side_effect=httpx.TimeoutException("timed out"))

    with patch("ttadev.observability.server.httpx.AsyncClient", return_value=mock_client):
        server = _make_server()
        async with TestClient(TestServer(server.app)) as client:
            resp = await client.get("/api/v2/langfuse/scores")
            data = await resp.json()
    assert data["available"] is False


@pytest.mark.asyncio
async def test_langfuse_scores_graceful_on_http_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", "pk-lf")
    monkeypatch.setenv("LANGFUSE_SECRET_KEY", "sk-lf")

    err_resp = httpx.Response(403, text="Forbidden")
    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.get = AsyncMock(
        side_effect=httpx.HTTPStatusError("403", request=MagicMock(), response=err_resp)
    )

    with patch("ttadev.observability.server.httpx.AsyncClient", return_value=mock_client):
        server = _make_server()
        async with TestClient(TestServer(server.app)) as client:
            resp = await client.get("/api/v2/langfuse/scores")
            data = await resp.json()
    assert data["available"] is False
    assert "403" in data["reason"]


@pytest.mark.asyncio
async def test_langfuse_scores_empty_when_no_scores(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", "pk-lf")
    monkeypatch.setenv("LANGFUSE_SECRET_KEY", "sk-lf")

    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.get = AsyncMock(return_value=_make_resp({"data": []}))

    with patch("ttadev.observability.server.httpx.AsyncClient", return_value=mock_client):
        server = _make_server()
        async with TestClient(TestServer(server.app)) as client:
            resp = await client.get("/api/v2/langfuse/scores")
            data = await resp.json()
    assert data["available"] is True
    assert data["scores"] == []
