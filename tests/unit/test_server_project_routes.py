"""Unit tests for Task 9 — server project routes + ingestion awareness."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from aiohttp.test_utils import TestClient, TestServer

from ttadev.observability.project_session import ProjectSessionManager
from ttadev.observability.server import ObservabilityServer
from ttadev.observability.session_manager import SessionManager
from ttadev.observability.span_processor import ProcessedSpan

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_server(tmp_path: Path) -> ObservabilityServer:
    """Create an ObservabilityServer wired to a temp data dir."""
    return ObservabilityServer(data_dir=tmp_path)


def _make_span(
    span_id: str = "s1",
    agent_id: str | None = None,
    project_id: str | None = None,
) -> ProcessedSpan:
    return ProcessedSpan(
        span_id=span_id,
        trace_id="t1",
        parent_span_id=None,
        name="test.span",
        provider="TTA.dev",
        model="primitives",
        agent_role=None,
        workflow_id=None,
        primitive_type=None,
        started_at="2026-01-01T00:00:00+00:00",
        duration_ms=10.0,
        status="success",
        agent_id=agent_id,
        agent_tool="claude-code",
        project_id=project_id,
    )


# ---------------------------------------------------------------------------
# GET /api/v2/projects — list projects
# ---------------------------------------------------------------------------


class TestProjectsListRoute:
    @pytest.mark.asyncio
    async def test_empty_when_no_projects(self, tmp_path):
        srv = _make_server(tmp_path)
        async with TestClient(TestServer(srv.app)) as client:
            resp = await client.get("/api/v2/projects")
            assert resp.status == 200
            data = await resp.json()
            assert data == []

    @pytest.mark.asyncio
    async def test_returns_projects_after_create(self, tmp_path):
        srv = _make_server(tmp_path)
        mgr = ProjectSessionManager(tmp_path)
        mgr.create("alpha")
        mgr.create("beta")
        async with TestClient(TestServer(srv.app)) as client:
            resp = await client.get("/api/v2/projects")
            assert resp.status == 200
            data = await resp.json()
            names = [p["name"] for p in data]
            assert "alpha" in names
            assert "beta" in names

    @pytest.mark.asyncio
    async def test_response_schema(self, tmp_path):
        srv = _make_server(tmp_path)
        mgr = ProjectSessionManager(tmp_path)
        mgr.create("gamma")
        async with TestClient(TestServer(srv.app)) as client:
            resp = await client.get("/api/v2/projects")
            data = await resp.json()
            assert len(data) == 1
            proj = data[0]
            assert "id" in proj
            assert "name" in proj
            assert "created_at" in proj
            assert "member_agent_ids" in proj
            assert "role_assignments" in proj


# ---------------------------------------------------------------------------
# GET /api/v2/projects/{id} — project detail
# ---------------------------------------------------------------------------


class TestProjectDetailRoute:
    @pytest.mark.asyncio
    async def test_404_for_unknown_id(self, tmp_path):
        srv = _make_server(tmp_path)
        async with TestClient(TestServer(srv.app)) as client:
            resp = await client.get("/api/v2/projects/nonexistent-uuid")
            assert resp.status == 404

    @pytest.mark.asyncio
    async def test_returns_project_by_id(self, tmp_path):
        srv = _make_server(tmp_path)
        mgr = ProjectSessionManager(tmp_path)
        proj = mgr.create("delta")
        async with TestClient(TestServer(srv.app)) as client:
            resp = await client.get(f"/api/v2/projects/{proj.id}")
            assert resp.status == 200
            data = await resp.json()
            assert data["id"] == proj.id
            assert data["name"] == "delta"


# ---------------------------------------------------------------------------
# GET /api/v2/projects/{id}/sessions — sessions grouped by project
# ---------------------------------------------------------------------------


class TestProjectSessionsRoute:
    @pytest.mark.asyncio
    async def test_returns_empty_for_project_with_no_sessions(self, tmp_path):
        srv = _make_server(tmp_path)
        mgr = ProjectSessionManager(tmp_path)
        proj = mgr.create("epsilon")
        async with TestClient(TestServer(srv.app)) as client:
            resp = await client.get(f"/api/v2/projects/{proj.id}/sessions")
            assert resp.status == 200
            data = await resp.json()
            assert data == []

    @pytest.mark.asyncio
    async def test_returns_sessions_matching_project_id(self, tmp_path):
        srv = _make_server(tmp_path)
        mgr = ProjectSessionManager(tmp_path)
        proj = mgr.create("zeta")

        # Manually seed two sessions: one matching, one not
        session_mgr = SessionManager(tmp_path)
        s_match = session_mgr.start_session()
        # patch project_id on the session (workaround: edit JSON directly)
        meta = tmp_path / "sessions" / f"{s_match.id}.json"
        data = json.loads(meta.read_text())
        data["project_id"] = proj.id
        meta.write_text(json.dumps(data))

        s_other = session_mgr.start_session()

        async with TestClient(TestServer(srv.app)) as client:
            resp = await client.get(f"/api/v2/projects/{proj.id}/sessions")
            assert resp.status == 200
            result = await resp.json()
            ids = [s["id"] for s in result]
            assert s_match.id in ids
            assert s_other.id not in ids

    @pytest.mark.asyncio
    async def test_404_for_unknown_project(self, tmp_path):
        srv = _make_server(tmp_path)
        async with TestClient(TestServer(srv.app)) as client:
            resp = await client.get("/api/v2/projects/does-not-exist/sessions")
            assert resp.status == 404


# ---------------------------------------------------------------------------
# GET /api/v2/sessions — project_id included in response
# ---------------------------------------------------------------------------


class TestSessionsIncludeProjectId:
    @pytest.mark.asyncio
    async def test_sessions_list_includes_project_id_field(self, tmp_path):
        srv = _make_server(tmp_path)
        session_mgr = SessionManager(tmp_path)
        session_mgr.start_session()
        async with TestClient(TestServer(srv.app)) as client:
            resp = await client.get("/api/v2/sessions")
            assert resp.status == 200
            sessions = await resp.json()
            assert len(sessions) >= 1
            # project_id field must be present (may be None)
            assert "project_id" in sessions[0]
