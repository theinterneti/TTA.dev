"""Phase 1: Foundation Tests - Stable Server & Basic Data Flow."""

import asyncio
import socket
from pathlib import Path

import aiohttp
import pytest


def _free_port() -> int:
    """Return a free TCP port on localhost."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture
async def observability_server():
    """Fixture that starts and stops the observability server on a free port."""
    from ttadev.observability.collector import TraceCollector
    from ttadev.observability.server import ObservabilityServer

    collector = TraceCollector()
    port = _free_port()
    server = ObservabilityServer(collector=collector, port=port)
    await server.start()

    # Wait for server to be ready
    await asyncio.sleep(0.5)

    yield server

    await server.stop()


@pytest.fixture
async def server_url(observability_server):
    """Fixture providing the observability server URL."""
    return f"http://localhost:{observability_server.port}"


@pytest.mark.asyncio
async def test_server_starts_and_responds(server_url):
    """Test that server starts and responds to HTTP requests."""
    async with aiohttp.ClientSession() as session, session.get(server_url) as response:
        assert response.status == 200
        text = await response.text()
        assert "TTA.dev Observability" in text


@pytest.mark.asyncio
async def test_websocket_connection(server_url):
    """Test that WebSocket connections work."""
    ws_url = server_url.replace("http://", "ws://") + "/ws"  # nosemgrep: detect-insecure-websocket
    async with aiohttp.ClientSession() as session, session.ws_connect(ws_url) as ws:
        # Should connect successfully
        assert not ws.closed

        # Should receive initial state
        msg = await asyncio.wait_for(ws.receive_json(), timeout=5.0)
        assert msg["type"] in ["initial_state", "ping"]


@pytest.mark.asyncio
async def test_trace_collection_to_file():
    """Test that traces are written to filesystem."""
    from ttadev.observability.collector import TraceCollector

    collector = TraceCollector()

    # Create test trace
    trace_data = {
        "trace_id": "test-123",
        "spans": [
            {
                "name": "test_span",
                "start_time": "2026-03-09T21:00:00Z",
                "end_time": "2026-03-09T21:00:01Z",
                "attributes": {"test": "value"},
            }
        ],
    }

    # Collect trace
    await collector.collect_trace(trace_data)

    # Verify file was created
    trace_file = Path(".observability/traces/test-123.json")
    assert trace_file.exists()

    # Verify content
    import json

    with open(trace_file) as f:
        saved_trace = json.load(f)
    assert saved_trace["trace_id"] == "test-123"


@pytest.mark.asyncio
async def test_api_serves_collected_traces(server_url):
    """Test that API endpoint serves collected traces."""
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{server_url}/api/traces") as response:
            assert response.status == 200
            data = await response.json()
            assert "traces" in data
            assert isinstance(data["traces"], list)


@pytest.mark.asyncio
async def test_realtime_trace_broadcast(observability_server):
    """Test that new traces are broadcast via WebSocket."""
    collector = observability_server.collector
    ws_url = f"ws://localhost:{observability_server.port}/ws"

    async with aiohttp.ClientSession() as session, session.ws_connect(ws_url) as ws:
        # Consume initial state message
        await ws.receive_json()

        # Send a new trace
        trace_data = {"trace_id": "broadcast-test", "spans": [{"name": "broadcast_span"}]}
        await collector.collect_trace(trace_data)

        # Should receive broadcast within 2 seconds
        msg = await asyncio.wait_for(ws.receive_json(), timeout=2.0)
        assert msg["type"] == "new_trace"
        assert msg["trace"]["trace_id"] == "broadcast-test"
