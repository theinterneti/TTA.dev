"""Unit tests for Task 9 — server project routes + ingestion awareness."""

from __future__ import annotations

import json
from datetime import UTC, datetime
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


class TestOwnershipRoutes:
    @pytest.mark.asyncio
    async def test_control_ownership_empty_when_no_active_work(self, tmp_path):
        srv = _make_server(tmp_path)
        async with TestClient(TestServer(srv.app)) as client:
            resp = await client.get("/api/v2/control/ownership")
            assert resp.status == 200
            data = await resp.json()
            assert data == {"active": []}

    @pytest.mark.asyncio
    async def test_control_ownership_returns_linked_records(self, tmp_path, monkeypatch):
        monkeypatch.setattr("ttadev.control_plane.service.get_agent_id", lambda: "agent-1")
        monkeypatch.setattr("ttadev.control_plane.service.get_agent_tool", lambda: "copilot")
        srv = _make_server(tmp_path)
        session_mgr = SessionManager(tmp_path)
        session = session_mgr.start_session()
        session_mgr.add_span(
            session.id,
            ProcessedSpan(
                span_id="span-1",
                trace_id="trace-1",
                parent_span_id=None,
                name="tool_call",
                provider="GitHub Copilot",
                model="claude-sonnet-4.5",
                agent_role="backend-engineer",
                workflow_id=None,
                primitive_type="RetryPrimitive",
                started_at=datetime.now(UTC).isoformat(),
                duration_ms=0.0,
                status="success",
            ),
        )

        from ttadev.control_plane import ControlPlaneService

        service = ControlPlaneService(tmp_path)
        task = service.create_task(
            "Ownership task", project_name="alpha", requested_role="developer"
        )
        claim = service.claim_task(task.id, agent_role="developer", lease_ttl_seconds=60)

        async with TestClient(TestServer(srv.app)) as client:
            resp = await client.get("/api/v2/control/ownership")
            assert resp.status == 200
            data = await resp.json()
            assert len(data["active"]) == 1
            record = data["active"][0]
            assert record["task"]["id"] == task.id
            assert record["run"]["id"] == claim.run.id
            assert record["session"]["id"] == session.id
            assert record["project"]["id"] == task.project_id
            assert record["workflow"] is None
            assert record["telemetry"]["has_recent_activity"] is True
            assert record["telemetry"]["recent_action_types"] == ["tool_call"]

    @pytest.mark.asyncio
    async def test_project_ownership_filters_and_404s(self, tmp_path, monkeypatch):
        monkeypatch.setattr("ttadev.control_plane.service.get_agent_id", lambda: "agent-1")
        monkeypatch.setattr("ttadev.control_plane.service.get_agent_tool", lambda: "copilot")
        srv = _make_server(tmp_path)
        session_mgr = SessionManager(tmp_path)
        session_mgr.start_session()

        from ttadev.control_plane import ControlPlaneService

        service = ControlPlaneService(tmp_path)
        alpha = service.create_task("Alpha work", project_name="alpha")
        beta = service.create_task("Beta work", project_name="beta")
        service.claim_task(alpha.id, lease_ttl_seconds=60)
        service.claim_task(beta.id, lease_ttl_seconds=60)

        async with TestClient(TestServer(srv.app)) as client:
            alpha_resp = await client.get(f"/api/v2/projects/{alpha.project_id}/ownership")
            assert alpha_resp.status == 200
            alpha_data = await alpha_resp.json()
            assert alpha_data["project_id"] == alpha.project_id
            assert [record["task"]["id"] for record in alpha_data["active"]] == [alpha.id]

            missing = await client.get("/api/v2/projects/missing/ownership")
            assert missing.status == 404

    @pytest.mark.asyncio
    async def test_session_ownership_filters_and_404s(self, tmp_path, monkeypatch):
        monkeypatch.setattr("ttadev.control_plane.service.get_agent_id", lambda: "agent-1")
        monkeypatch.setattr("ttadev.control_plane.service.get_agent_tool", lambda: "copilot")
        srv = _make_server(tmp_path)
        session_mgr = SessionManager(tmp_path)
        session = session_mgr.start_session()

        from ttadev.control_plane import ControlPlaneService

        service = ControlPlaneService(tmp_path)
        task = service.create_task("Session-owned work")
        service.claim_task(task.id, lease_ttl_seconds=60)

        async with TestClient(TestServer(srv.app)) as client:
            resp = await client.get(f"/api/v2/sessions/{session.id}/ownership")
            assert resp.status == 200
            data = await resp.json()
            assert data["session_id"] == session.id
            assert len(data["active"]) == 1
            assert data["active"][0]["task"]["id"] == task.id
            assert data["active"][0]["workflow"] is None
            assert "telemetry" in data["active"][0]

            missing = await client.get("/api/v2/sessions/missing/ownership")
            assert missing.status == 404

    @pytest.mark.asyncio
    async def test_ownership_telemetry_is_null_without_linked_session(self, tmp_path, monkeypatch):
        monkeypatch.setattr("ttadev.control_plane.service.get_agent_id", lambda: "agent-1")
        monkeypatch.setattr("ttadev.control_plane.service.get_agent_tool", lambda: "copilot")
        srv = _make_server(tmp_path)

        from ttadev.control_plane import ControlPlaneService

        service = ControlPlaneService(tmp_path)
        service._get_active_session = lambda: None  # type: ignore[method-assign]
        task = service.create_task("Unlinked work")
        service.claim_task(task.id, lease_ttl_seconds=60)

        async with TestClient(TestServer(srv.app)) as client:
            resp = await client.get("/api/v2/control/ownership")
            assert resp.status == 200
            data = await resp.json()
            assert len(data["active"]) == 1
            assert data["active"][0]["session"] is None
            assert data["active"][0]["workflow"] is None
            assert data["active"][0]["telemetry"] is None

    @pytest.mark.asyncio
    async def test_ownership_routes_include_workflow_summary_for_tracked_runs(
        self, tmp_path, monkeypatch
    ):
        monkeypatch.setattr("ttadev.control_plane.service.get_agent_id", lambda: "agent-1")
        monkeypatch.setattr("ttadev.control_plane.service.get_agent_tool", lambda: "copilot")
        srv = _make_server(tmp_path)
        session_mgr = SessionManager(tmp_path)
        session = session_mgr.start_session()

        from ttadev.control_plane import ControlPlaneService
        from ttadev.control_plane.models import WorkflowGateDecisionOutcome

        service = ControlPlaneService(tmp_path)
        claim = service.start_tracked_workflow(
            workflow_name="feature_dev",
            workflow_goal="ship auth",
            step_agents=["developer", "qa"],
            project_name="alpha",
        )
        service.mark_workflow_step_running(claim.task.id, step_index=0)
        service.record_workflow_step_result(
            claim.task.id,
            step_index=0,
            result_summary="developer output",
            confidence=0.9,
        )
        service.record_workflow_gate_outcome(
            claim.task.id,
            step_index=0,
            decision=WorkflowGateDecisionOutcome.CONTINUE,
            summary="approved",
        )
        service.mark_workflow_step_running(claim.task.id, step_index=1)

        async with TestClient(TestServer(srv.app)) as client:
            control_resp = await client.get("/api/v2/control/ownership")
            assert control_resp.status == 200
            control_data = await control_resp.json()
            assert len(control_data["active"]) == 1
            assert control_data["active"][0]["session"]["id"] == session.id
            workflow = control_data["active"][0]["workflow"]
            assert workflow["workflow_name"] == "feature_dev"
            assert workflow["current_step_number"] == 2
            assert workflow["current_step"]["agent_name"] == "qa"

            project_resp = await client.get(f"/api/v2/projects/{claim.task.project_id}/ownership")
            assert project_resp.status == 200
            project_data = await project_resp.json()
            assert project_data["active"][0]["workflow"]["workflow_goal"] == "ship auth"

            session_resp = await client.get(f"/api/v2/sessions/{session.id}/ownership")
            assert session_resp.status == 200
            session_data = await session_resp.json()
            assert session_data["active"][0]["workflow"]["workflow_status"] == "running"
