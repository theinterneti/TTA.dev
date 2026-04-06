"""Unit tests for L0 control-plane dashboard API routes (GitHub issue #340).

Covers:
- GET /api/v2/control/tasks   returns 200 with {"tasks": [...]}
- GET /api/v2/control/runs    returns 200 with {"runs": [...]}
- GET /api/v2/control/locks   returns 200 with {"locks": [...]}
- GET /api/v2/control/workflows returns 200 with {"workflows": [...]}
- All routes return empty lists when .tta/ dir has no data — never 404
- Tasks endpoint includes workflow data when present
"""

from __future__ import annotations

import time
from pathlib import Path

import pytest
from aiohttp.test_utils import TestClient, TestServer

from ttadev.control_plane.models import (
    LockRecord,
    LockScopeType,
    RunRecord,
    RunStatus,
    TaskRecord,
    TaskStatus,
    WorkflowStepRecord,
    WorkflowStepStatus,
    WorkflowTrackingRecord,
    WorkflowTrackingStatus,
)
from ttadev.control_plane.store import ControlPlaneStore
from ttadev.observability.server import ObservabilityServer

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def tmp_data_dir(tmp_path: Path) -> Path:
    d = tmp_path / "data"
    d.mkdir()
    return d


@pytest.fixture
async def test_client(tmp_data_dir: Path) -> TestClient:
    """Spin up an ObservabilityServer backed by a temp data directory."""
    server = ObservabilityServer(data_dir=tmp_data_dir)

    async def _noop_init() -> None:
        server._current_session = server._session_mgr.start_session()

    server._init_state = _noop_init  # type: ignore[method-assign]
    ts = TestServer(server.app)
    client = TestClient(ts)
    await client.start_server()
    yield client
    await client.close()


def _store(data_dir: Path) -> ControlPlaneStore:
    return ControlPlaneStore(data_dir=data_dir)


def _make_task(task_id: str = "task-001", title: str = "Test task") -> TaskRecord:
    now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    return TaskRecord(
        id=task_id,
        title=title,
        description="A test task",
        created_at=now,
        updated_at=now,
        status=TaskStatus.IN_PROGRESS,
    )


def _make_run(run_id: str = "run-001", task_id: str = "task-001") -> RunRecord:
    now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    return RunRecord(
        id=run_id,
        task_id=task_id,
        agent_id="agent-test",
        agent_tool="copilot",
        started_at=now,
        updated_at=now,
        agent_role="backend-engineer",
        status=RunStatus.ACTIVE,
    )


def _make_lock(lock_id: str = "lock-001", run_id: str = "run-001") -> LockRecord:
    now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    return LockRecord(
        id=lock_id,
        run_id=run_id,
        task_id="task-001",
        agent_id="agent-test",
        scope_type=LockScopeType.WORKSPACE,
        scope_value="/home/user/project",
        acquired_at=now,
        updated_at=now,
    )


# ---------------------------------------------------------------------------
# /api/v2/control/tasks
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_control_tasks_returns_200(test_client: TestClient) -> None:
    resp = await test_client.get("/api/v2/control/tasks")
    assert resp.status == 200


@pytest.mark.asyncio
async def test_control_tasks_empty_state(test_client: TestClient) -> None:
    """Empty store must return {"tasks": []} — never a 404."""
    resp = await test_client.get("/api/v2/control/tasks")
    body = await resp.json()
    assert "tasks" in body
    assert isinstance(body["tasks"], list)
    assert body["tasks"] == []


@pytest.mark.asyncio
async def test_control_tasks_returns_stored_task(
    test_client: TestClient, tmp_data_dir: Path
) -> None:
    store = _store(tmp_data_dir)
    store.put_task(_make_task("task-abc", "My important task"))

    resp = await test_client.get("/api/v2/control/tasks")
    body = await resp.json()
    assert len(body["tasks"]) == 1
    task = body["tasks"][0]
    assert task["id"] == "task-abc"
    assert task["title"] == "My important task"
    assert task["status"] == "in_progress"


@pytest.mark.asyncio
async def test_control_tasks_content_type(test_client: TestClient) -> None:
    resp = await test_client.get("/api/v2/control/tasks")
    assert "application/json" in resp.content_type


# ---------------------------------------------------------------------------
# /api/v2/control/runs
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_control_runs_returns_200(test_client: TestClient) -> None:
    resp = await test_client.get("/api/v2/control/runs")
    assert resp.status == 200


@pytest.mark.asyncio
async def test_control_runs_empty_state(test_client: TestClient) -> None:
    resp = await test_client.get("/api/v2/control/runs")
    body = await resp.json()
    assert "runs" in body
    assert isinstance(body["runs"], list)
    assert body["runs"] == []


@pytest.mark.asyncio
async def test_control_runs_returns_stored_run(test_client: TestClient, tmp_data_dir: Path) -> None:
    store = _store(tmp_data_dir)
    store.put_task(_make_task("task-001"))
    store.put_run(_make_run("run-xyz", "task-001"))

    resp = await test_client.get("/api/v2/control/runs")
    body = await resp.json()
    assert len(body["runs"]) == 1
    run = body["runs"][0]
    assert run["id"] == "run-xyz"
    assert run["task_id"] == "task-001"
    assert run["agent_role"] == "backend-engineer"
    assert run["status"] == "active"


@pytest.mark.asyncio
async def test_control_runs_content_type(test_client: TestClient) -> None:
    resp = await test_client.get("/api/v2/control/runs")
    assert "application/json" in resp.content_type


# ---------------------------------------------------------------------------
# /api/v2/control/locks
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_control_locks_returns_200(test_client: TestClient) -> None:
    resp = await test_client.get("/api/v2/control/locks")
    assert resp.status == 200


@pytest.mark.asyncio
async def test_control_locks_empty_state(test_client: TestClient) -> None:
    resp = await test_client.get("/api/v2/control/locks")
    body = await resp.json()
    assert "locks" in body
    assert isinstance(body["locks"], list)
    assert body["locks"] == []


@pytest.mark.asyncio
async def test_control_locks_returns_stored_lock(
    test_client: TestClient, tmp_data_dir: Path
) -> None:
    store = _store(tmp_data_dir)
    store.put_lock(_make_lock("lock-abc", "run-001"))

    resp = await test_client.get("/api/v2/control/locks")
    body = await resp.json()
    assert len(body["locks"]) == 1
    lock = body["locks"][0]
    assert lock["id"] == "lock-abc"
    assert lock["run_id"] == "run-001"
    assert lock["scope_type"] == "workspace"


@pytest.mark.asyncio
async def test_control_locks_content_type(test_client: TestClient) -> None:
    resp = await test_client.get("/api/v2/control/locks")
    assert "application/json" in resp.content_type


# ---------------------------------------------------------------------------
# /api/v2/control/workflows
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_control_workflows_returns_200(test_client: TestClient) -> None:
    resp = await test_client.get("/api/v2/control/workflows")
    assert resp.status == 200


@pytest.mark.asyncio
async def test_control_workflows_empty_state(test_client: TestClient) -> None:
    resp = await test_client.get("/api/v2/control/workflows")
    body = await resp.json()
    assert "workflows" in body
    assert isinstance(body["workflows"], list)
    assert body["workflows"] == []


@pytest.mark.asyncio
async def test_control_workflows_skips_tasks_without_workflow(
    test_client: TestClient, tmp_data_dir: Path
) -> None:
    """Tasks without workflow tracking data must not appear in the response."""
    store = _store(tmp_data_dir)
    store.put_task(_make_task("task-no-wf"))

    resp = await test_client.get("/api/v2/control/workflows")
    body = await resp.json()
    assert body["workflows"] == []


@pytest.mark.asyncio
async def test_control_workflows_returns_task_with_workflow(
    test_client: TestClient, tmp_data_dir: Path
) -> None:
    store = _store(tmp_data_dir)
    step = WorkflowStepRecord(
        step_index=0,
        agent_name="backend-engineer",
        status=WorkflowStepStatus.RUNNING,
    )
    wf = WorkflowTrackingRecord(
        workflow_name="feature-dev",
        workflow_goal="ship the thing",
        total_steps=1,
        status=WorkflowTrackingStatus.RUNNING,
        steps=[step],
    )
    task = _make_task("task-wf")
    task = TaskRecord(
        id=task.id,
        title=task.title,
        description=task.description,
        created_at=task.created_at,
        updated_at=task.updated_at,
        status=task.status,
        workflow=wf,
    )
    store.put_task(task)

    resp = await test_client.get("/api/v2/control/workflows")
    body = await resp.json()
    assert len(body["workflows"]) == 1
    entry = body["workflows"][0]
    assert entry["task_id"] == "task-wf"
    assert entry["task_title"] == "Test task"
    assert entry["workflow"]["workflow_name"] == "feature-dev"
    assert entry["workflow"]["workflow_goal"] == "ship the thing"
    assert len(entry["workflow"]["steps"]) == 1
    assert entry["workflow"]["steps"][0]["agent_name"] == "backend-engineer"


@pytest.mark.asyncio
async def test_control_workflows_content_type(test_client: TestClient) -> None:
    resp = await test_client.get("/api/v2/control/workflows")
    assert "application/json" in resp.content_type
