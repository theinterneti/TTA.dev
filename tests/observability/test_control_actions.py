"""Tests for the 4 new agent management POST endpoints (#343).

Tests:
- POST /api/v2/control/gates/{task_id}/{gate_id}/approve → 404 for unknown task
- POST /api/v2/control/gates/{task_id}/{gate_id}/reject  → 404 for unknown task
- POST /api/v2/control/runs/{run_id}/release             → 404 for unknown run
- POST /api/v2/control/leases/{run_id}/release           → 404 for unknown run
"""

import asyncio
import socket
import tempfile
from pathlib import Path

import aiohttp
import pytest

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
async def action_server():
    """Ephemeral ObservabilityServer with an isolated temp data dir."""
    from ttadev.observability.server import ObservabilityServer

    port = _free_port()
    with tempfile.TemporaryDirectory() as tmp:
        server = ObservabilityServer(port=port, data_dir=Path(tmp))
        tasks_before = set(asyncio.all_tasks())
        await server.start()
        await asyncio.sleep(0.3)
        tasks_after = set(asyncio.all_tasks())
        server_tasks = tasks_after - tasks_before

        yield server

        await server.stop()
        for task in server_tasks:
            task.cancel()
        if server_tasks:
            await asyncio.gather(*server_tasks, return_exceptions=True)


@pytest.fixture
async def base_url(action_server):
    return f"http://localhost:{action_server.port}"


# ---------------------------------------------------------------------------
# Tests — gate approve
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_gate_approve_unknown_task_returns_404(base_url):
    url = f"{base_url}/api/v2/control/gates/no-such-task/no-such-gate/approve"
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json={}) as resp:
            assert resp.status == 404
            body = await resp.json()
            assert "error" in body


@pytest.mark.asyncio
async def test_gate_approve_no_body_still_works(base_url):
    """Sending no JSON body should default gracefully (still 404 for unknown task)."""
    url = f"{base_url}/api/v2/control/gates/ghost-task/ghost-gate/approve"
    async with aiohttp.ClientSession() as session:
        async with session.post(url) as resp:
            assert resp.status == 404


# ---------------------------------------------------------------------------
# Tests — gate reject
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_gate_reject_unknown_task_returns_404(base_url):
    url = f"{base_url}/api/v2/control/gates/no-such-task/no-such-gate/reject"
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json={"decided_by": "ci"}) as resp:
            assert resp.status == 404
            body = await resp.json()
            assert "error" in body


@pytest.mark.asyncio
async def test_gate_reject_no_body_still_works(base_url):
    url = f"{base_url}/api/v2/control/gates/ghost-task/ghost-gate/reject"
    async with aiohttp.ClientSession() as session:
        async with session.post(url) as resp:
            assert resp.status == 404


# ---------------------------------------------------------------------------
# Tests — run release
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_run_release_unknown_run_returns_404(base_url):
    url = f"{base_url}/api/v2/control/runs/no-such-run/release"
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json={"reason": "test"}) as resp:
            assert resp.status == 404
            body = await resp.json()
            assert "error" in body


@pytest.mark.asyncio
async def test_run_release_no_body_still_works(base_url):
    url = f"{base_url}/api/v2/control/runs/ghost-run/release"
    async with aiohttp.ClientSession() as session:
        async with session.post(url) as resp:
            assert resp.status == 404


# ---------------------------------------------------------------------------
# Tests — lease release
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_lease_release_unknown_run_returns_404(base_url):
    url = f"{base_url}/api/v2/control/leases/no-such-run/release"
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json={"reason": "test"}) as resp:
            assert resp.status == 404
            body = await resp.json()
            assert "error" in body


@pytest.mark.asyncio
async def test_lease_release_no_body_still_works(base_url):
    url = f"{base_url}/api/v2/control/leases/ghost-run/release"
    async with aiohttp.ClientSession() as session:
        async with session.post(url) as resp:
            assert resp.status == 404


# ---------------------------------------------------------------------------
# Tests — response shape
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_approve_response_is_json(base_url):
    """All error responses must be JSON with an 'error' key."""
    for path in [
        "/api/v2/control/gates/x/y/approve",
        "/api/v2/control/gates/x/y/reject",
        "/api/v2/control/runs/x/release",
        "/api/v2/control/leases/x/release",
    ]:
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{base_url}{path}", json={}) as resp:
                assert resp.content_type == "application/json", f"Not JSON for {path}"
                body = await resp.json()
                assert "error" in body, f"No 'error' key for {path}"
