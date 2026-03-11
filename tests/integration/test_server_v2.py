"""Integration tests for ObservabilityServer v2 routes — Task 7.

Starts the server in-process using aiohttp's TestClient so no subprocess/port
conflicts. CGC is mocked to avoid spawning real processes.
"""

import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio
from aiohttp.test_utils import TestClient, TestServer

from ttadev.observability.server import ObservabilityServer

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def tmp_data(tmp_path: Path) -> Path:
    return tmp_path / "tta"


@pytest_asyncio.fixture
async def server_client(tmp_data: Path) -> TestClient:  # type: ignore[misc]
    """Spin up ObservabilityServer with mocked CGC using aiohttp TestServer (random port)."""
    with patch(
        "ttadev.observability.server.CGCIntegration.is_available",
        new_callable=AsyncMock,
        return_value=False,  # CGC not available in tests
    ):
        srv = ObservabilityServer(data_dir=tmp_data)
        # _init_state sets up session + CGC probe without binding a TCP port
        await srv._init_state()
        # TestServer manages its own port — no conflict with a running server
        client = TestClient(TestServer(srv.app))
        await client.start_server()
        yield client
        await client.close()
        srv._session_mgr.end_session()


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_health_endpoint(server_client: TestClient) -> None:
    resp = await server_client.get("/api/v2/health")
    assert resp.status == 200
    data = await resp.json()
    assert data["status"] == "ok"
    assert "session_id" in data
    assert isinstance(data["cgc_available"], bool)


# ---------------------------------------------------------------------------
# Sessions
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_sessions_endpoint_returns_list(server_client: TestClient) -> None:
    resp = await server_client.get("/api/v2/sessions")
    assert resp.status == 200
    data = await resp.json()
    assert isinstance(data, list)


@pytest.mark.asyncio
async def test_current_session_exists(server_client: TestClient) -> None:
    resp = await server_client.get("/api/v2/sessions/current")
    assert resp.status == 200
    data = await resp.json()
    assert "id" in data
    assert data["ended_at"] is None


@pytest.mark.asyncio
async def test_session_detail_endpoint(server_client: TestClient) -> None:
    # Get current session id from health
    health = await (await server_client.get("/api/v2/health")).json()
    session_id = health["session_id"]
    assert session_id is not None

    resp = await server_client.get(f"/api/v2/sessions/{session_id}")
    assert resp.status == 200
    data = await resp.json()
    assert data["id"] == session_id
    assert "provider_summary" in data


@pytest.mark.asyncio
async def test_session_detail_not_found(server_client: TestClient) -> None:
    resp = await server_client.get("/api/v2/sessions/nonexistent-id")
    assert resp.status == 404


@pytest.mark.asyncio
async def test_session_spans_empty(server_client: TestClient) -> None:
    health = await (await server_client.get("/api/v2/health")).json()
    session_id = health["session_id"]
    resp = await server_client.get(f"/api/v2/sessions/{session_id}/spans")
    assert resp.status == 200
    data = await resp.json()
    assert isinstance(data, list)


# ---------------------------------------------------------------------------
# CGC (unavailable in test env)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_cgc_live_endpoint(server_client: TestClient) -> None:
    resp = await server_client.get("/api/v2/cgc/live")
    assert resp.status == 200
    data = await resp.json()
    assert "active_primitives" in data


@pytest.mark.asyncio
async def test_cgc_graph_returns_span_graph_when_unavailable(server_client: TestClient) -> None:
    resp = await server_client.get("/api/v2/cgc/architecture")
    assert resp.status == 200
    data = await resp.json()
    # CGC unavailable in tests → span-derived fallback always returns nodes + edges lists
    assert "nodes" in data
    assert "edges" in data
    assert isinstance(data["nodes"], list)
    assert isinstance(data["edges"], list)


# ---------------------------------------------------------------------------
# Primitives catalog
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_primitives_endpoint(server_client: TestClient) -> None:
    resp = await server_client.get("/api/v2/primitives")
    assert resp.status == 200
    data = await resp.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert all("name" in p and "description" in p for p in data)


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_dashboard_served(server_client: TestClient) -> None:
    resp = await server_client.get("/")
    assert resp.status == 200
    text = await resp.text()
    assert "TTA.dev" in text


# ---------------------------------------------------------------------------
# WebSocket
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_websocket_connects_and_receives_initial_state(
    server_client: TestClient,
) -> None:
    async with server_client.ws_connect("/ws") as ws:
        msg = await asyncio.wait_for(ws.receive_json(), timeout=3.0)
        assert msg["type"] == "initial_state"
        assert "session" in msg
        await ws.close()


# ---------------------------------------------------------------------------
# Legacy v1 backward compat
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_v1_traces_still_works(server_client: TestClient) -> None:
    resp = await server_client.get("/api/traces")
    assert resp.status == 200
    data = await resp.json()
    assert "traces" in data
