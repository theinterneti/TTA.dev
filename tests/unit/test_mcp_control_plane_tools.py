"""Unit tests for MCP-exposed L0 control-plane tools."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

import pytest

from ttadev.control_plane.models import GateStatus
from ttadev.observability import agent_identity
from ttadev.observability.session_manager import SessionManager
from ttadev.primitives.mcp_server.server import create_server


async def _call_tool(mcp: Any, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    """Call an MCP tool and return its structured payload."""
    result = mcp.call_tool(name, arguments)
    if asyncio.iscoroutine(result):
        result = await result
    assert isinstance(result, tuple)
    _, payload = result
    assert isinstance(payload, dict)
    return payload


async def _list_tool_names(mcp: Any) -> list[str]:
    """List MCP tool names from the server."""
    tools = mcp.list_tools()
    if asyncio.iscoroutine(tools):
        tools = await tools
    return [tool.name for tool in tools]


def _set_agent_identity(
    monkeypatch: pytest.MonkeyPatch,
    *,
    agent_id: str,
    agent_tool: str = "copilot",
) -> None:
    """Pin the process agent identity for control-plane tests."""
    monkeypatch.setattr(agent_identity, "_AGENT_ID", agent_id)
    monkeypatch.setenv("TTA_AGENT_TOOL", agent_tool)


@pytest.mark.asyncio
async def test_control_plane_tools_are_registered() -> None:
    """Register the L0 control-plane MCP tools."""
    mcp = create_server()

    tool_names = await _list_tool_names(mcp)

    assert "control_create_task" in tool_names
    assert "control_list_tasks" in tool_names
    assert "control_get_task" in tool_names
    assert "control_claim_task" in tool_names
    assert "control_list_runs" in tool_names
    assert "control_get_run" in tool_names
    assert "control_heartbeat_run" in tool_names
    assert "control_complete_run" in tool_names
    assert "control_release_run" in tool_names
    assert "control_decide_gate" in tool_names
    assert "control_reopen_gate" in tool_names
    assert "control_list_locks" in tool_names
    assert "control_acquire_workspace_lock" in tool_names
    assert "control_acquire_file_lock" in tool_names
    assert "control_release_lock" in tool_names
    assert "control_list_ownership" in tool_names
    assert "control_list_project_ownership" in tool_names
    assert "control_list_session_ownership" in tool_names


@pytest.mark.asyncio
async def test_control_task_tools_round_trip(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Create, list, inspect, and claim tasks through MCP."""
    _set_agent_identity(monkeypatch, agent_id="agent-test")
    mcp = create_server()

    created = await _call_tool(
        mcp,
        "control_create_task",
        {
            "title": "Implement MCP bridge",
            "description": "Expose L0 task lifecycle",
            "project_name": "alpha",
            "requested_role": "backend-engineer",
            "priority": "high",
            "data_dir": str(tmp_path),
        },
    )
    task = created["task"]
    assert task["title"] == "Implement MCP bridge"
    assert task["project_name"] == "alpha"
    assert task["requested_role"] == "backend-engineer"
    assert task["priority"] == "high"
    assert task["status"] == "pending"

    listed = await _call_tool(
        mcp,
        "control_list_tasks",
        {
            "status": "pending",
            "project_name": "alpha",
            "data_dir": str(tmp_path),
        },
    )
    assert len(listed["tasks"]) == 1
    assert listed["tasks"][0]["id"] == task["id"]

    fetched = await _call_tool(
        mcp,
        "control_get_task",
        {"task_id": task["id"], "data_dir": str(tmp_path)},
    )
    assert fetched["task"]["id"] == task["id"]

    claimed = await _call_tool(
        mcp,
        "control_claim_task",
        {
            "task_id": task["id"],
            "agent_role": "backend-engineer",
            "lease_ttl_seconds": 120.0,
            "data_dir": str(tmp_path),
        },
    )
    assert claimed["task"]["status"] == "in_progress"
    assert claimed["run"]["status"] == "active"
    assert claimed["lease"]["holder_agent_id"] == "agent-test"


@pytest.mark.asyncio
async def test_control_task_gates_and_decision_round_trip(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Expose gate state and decisions through MCP task payloads."""
    _set_agent_identity(monkeypatch, agent_id="agent-test")
    mcp = create_server()

    created = await _call_tool(
        mcp,
        "control_create_task",
        {
            "title": "Gate-enabled task",
            "gates": [
                {
                    "id": "approval",
                    "gate_type": "approval",
                    "label": "Human approval",
                    "required": True,
                    "assigned_role": "reviewer",
                    "assigned_decider": "reviewer-1",
                }
            ],
            "data_dir": str(tmp_path),
        },
    )
    assert created["task"]["gates"][0]["id"] == "approval"
    assert created["task"]["gates"][0]["status"] == GateStatus.PENDING.value
    assert created["task"]["gates"][0]["assigned_role"] == "reviewer"
    assert created["task"]["gates"][0]["assigned_decider"] == "reviewer-1"

    decided = await _call_tool(
        mcp,
        "control_decide_gate",
        {
            "task_id": created["task"]["id"],
            "gate_id": "approval",
            "status": GateStatus.APPROVED.value,
            "decided_by": "reviewer-1",
            "decision_role": "reviewer",
            "summary": "approved",
            "data_dir": str(tmp_path),
        },
    )
    assert decided["task"]["gates"][0]["status"] == GateStatus.APPROVED.value
    assert decided["task"]["gates"][0]["decided_by"] == "reviewer-1"


@pytest.mark.asyncio
async def test_control_gate_lifecycle_requires_reopen_after_changes_requested(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Gate lifecycle supports changes_requested and explicit reopen through MCP."""
    _set_agent_identity(monkeypatch, agent_id="agent-test")
    mcp = create_server()

    created = await _call_tool(
        mcp,
        "control_create_task",
        {
            "title": "Lifecycle gate task",
            "gates": [
                {
                    "id": "review",
                    "gate_type": "review",
                    "label": "Code review",
                    "required": True,
                }
            ],
            "data_dir": str(tmp_path),
        },
    )
    claimed = await _call_tool(
        mcp,
        "control_claim_task",
        {"task_id": created["task"]["id"], "data_dir": str(tmp_path)},
    )

    changes = await _call_tool(
        mcp,
        "control_decide_gate",
        {
            "task_id": created["task"]["id"],
            "gate_id": "review",
            "status": GateStatus.CHANGES_REQUESTED.value,
            "summary": "needs revision",
            "data_dir": str(tmp_path),
        },
    )
    assert changes["task"]["gates"][0]["status"] == GateStatus.CHANGES_REQUESTED.value
    assert len(changes["task"]["gates"][0]["history"]) == 1
    assert changes["task"]["gates"][0]["history"][0]["action"] == "decision"
    assert changes["task"]["gates"][0]["history"][0]["from_status"] == GateStatus.PENDING.value
    assert (
        changes["task"]["gates"][0]["history"][0]["to_status"] == GateStatus.CHANGES_REQUESTED.value
    )

    blocked_direct_approve = await _call_tool(
        mcp,
        "control_decide_gate",
        {
            "task_id": created["task"]["id"],
            "gate_id": "review",
            "status": GateStatus.APPROVED.value,
            "data_dir": str(tmp_path),
        },
    )
    assert blocked_direct_approve["error_type"] == "TaskGateError"
    assert "without reopen" in blocked_direct_approve["error"]

    fetched_after_block = await _call_tool(
        mcp,
        "control_get_task",
        {"task_id": created["task"]["id"], "data_dir": str(tmp_path)},
    )
    assert len(fetched_after_block["task"]["gates"][0]["history"]) == 1

    reopened = await _call_tool(
        mcp,
        "control_reopen_gate",
        {
            "task_id": created["task"]["id"],
            "gate_id": "review",
            "data_dir": str(tmp_path),
        },
    )
    assert reopened["task"]["gates"][0]["status"] == GateStatus.PENDING.value
    assert len(reopened["task"]["gates"][0]["history"]) == 2
    assert reopened["task"]["gates"][0]["history"][1]["action"] == "reopened"
    assert (
        reopened["task"]["gates"][0]["history"][1]["from_status"]
        == GateStatus.CHANGES_REQUESTED.value
    )
    assert reopened["task"]["gates"][0]["history"][1]["to_status"] == GateStatus.PENDING.value

    approved = await _call_tool(
        mcp,
        "control_decide_gate",
        {
            "task_id": created["task"]["id"],
            "gate_id": "review",
            "status": GateStatus.APPROVED.value,
            "data_dir": str(tmp_path),
        },
    )
    assert approved["task"]["gates"][0]["status"] == GateStatus.APPROVED.value
    assert len(approved["task"]["gates"][0]["history"]) == 3
    assert approved["task"]["gates"][0]["history"][2]["action"] == "decision"
    assert approved["task"]["gates"][0]["history"][2]["from_status"] == GateStatus.PENDING.value
    assert approved["task"]["gates"][0]["history"][2]["to_status"] == GateStatus.APPROVED.value

    completed = await _call_tool(
        mcp,
        "control_complete_run",
        {"run_id": claimed["run"]["id"], "summary": "done", "data_dir": str(tmp_path)},
    )
    assert completed["run"]["status"] == "completed"


@pytest.mark.asyncio
async def test_control_reopen_gate_returns_structured_error_for_invalid_state(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Invalid reopen attempts return structured TaskGateError payloads."""
    _set_agent_identity(monkeypatch, agent_id="agent-test")
    mcp = create_server()

    created = await _call_tool(
        mcp,
        "control_create_task",
        {
            "title": "Invalid reopen task",
            "gates": [
                {
                    "id": "review",
                    "gate_type": "review",
                    "label": "Code review",
                }
            ],
            "data_dir": str(tmp_path),
        },
    )

    blocked = await _call_tool(
        mcp,
        "control_reopen_gate",
        {
            "task_id": created["task"]["id"],
            "gate_id": "review",
            "data_dir": str(tmp_path),
        },
    )
    assert blocked["error_type"] == "TaskGateError"
    assert "not in changes_requested" in blocked["error"]


@pytest.mark.asyncio
async def test_control_decide_gate_returns_structured_error_for_wrong_gate_owner(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Return a structured error when the acting gate owner does not match."""
    _set_agent_identity(monkeypatch, agent_id="agent-test")
    mcp = create_server()

    created = await _call_tool(
        mcp,
        "control_create_task",
        {
            "title": "Protected gate task",
            "gates": [
                {
                    "id": "review",
                    "gate_type": "review",
                    "label": "Protected review",
                    "required": True,
                    "assigned_agent_id": "agent-owner",
                }
            ],
            "data_dir": str(tmp_path),
        },
    )

    blocked = await _call_tool(
        mcp,
        "control_decide_gate",
        {
            "task_id": created["task"]["id"],
            "gate_id": "review",
            "status": GateStatus.APPROVED.value,
            "data_dir": str(tmp_path),
        },
    )
    assert blocked["error_type"] == "TaskGateError"
    assert "agent-owner" in blocked["error"]


@pytest.mark.asyncio
async def test_control_task_locks_and_manual_lock_round_trip(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Expose declared and manual lock flows through MCP tools."""
    _set_agent_identity(monkeypatch, agent_id="agent-test")
    mcp = create_server()

    created = await _call_tool(
        mcp,
        "control_create_task",
        {
            "title": "Lock-enabled task",
            "workspace_locks": ["alpha-workspace"],
            "file_locks": ["./src\\main.py"],
            "data_dir": str(tmp_path),
        },
    )
    assert created["task"]["workspace_locks"] == ["alpha-workspace"]
    assert created["task"]["file_locks"] == ["src/main.py"]

    claimed = await _call_tool(
        mcp,
        "control_claim_task",
        {"task_id": created["task"]["id"], "data_dir": str(tmp_path)},
    )

    listed = await _call_tool(mcp, "control_list_locks", {"data_dir": str(tmp_path)})
    assert len(listed["locks"]) == 2
    assert {lock["scope_value"] for lock in listed["locks"]} == {"alpha-workspace", "src/main.py"}

    manual = await _call_tool(
        mcp,
        "control_acquire_workspace_lock",
        {
            "task_id": created["task"]["id"],
            "run_id": claimed["run"]["id"],
            "workspace_name": "secondary-workspace",
            "data_dir": str(tmp_path),
        },
    )
    assert manual["lock"]["scope_type"] == "workspace"
    assert manual["lock"]["scope_value"] == "secondary-workspace"

    released = await _call_tool(
        mcp,
        "control_release_lock",
        {"lock_id": manual["lock"]["id"], "data_dir": str(tmp_path)},
    )
    assert released["released_lock_id"] == manual["lock"]["id"]


@pytest.mark.asyncio
async def test_control_claim_returns_structured_error_for_lock_conflicts(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Return a structured lock error when claim-time lock acquisition conflicts."""
    _set_agent_identity(monkeypatch, agent_id="agent-one")
    mcp = create_server()

    first = await _call_tool(
        mcp,
        "control_create_task",
        {
            "title": "First lock holder",
            "workspace_locks": ["shared-workspace"],
            "data_dir": str(tmp_path),
        },
    )
    first_claim = await _call_tool(
        mcp,
        "control_claim_task",
        {"task_id": first["task"]["id"], "data_dir": str(tmp_path)},
    )
    assert first_claim["run"]["status"] == "active"

    _set_agent_identity(monkeypatch, agent_id="agent-two")
    second = await _call_tool(
        mcp,
        "control_create_task",
        {
            "title": "Second lock holder",
            "workspace_locks": ["shared-workspace"],
            "data_dir": str(tmp_path),
        },
    )
    blocked = await _call_tool(
        mcp,
        "control_claim_task",
        {"task_id": second["task"]["id"], "data_dir": str(tmp_path)},
    )
    assert blocked["error_type"] == "TaskLockError"
    assert "shared-workspace" in blocked["error"]


@pytest.mark.asyncio
async def test_control_run_tools_round_trip(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Inspect, heartbeat, complete, and release runs through MCP."""
    _set_agent_identity(monkeypatch, agent_id="agent-test")
    mcp = create_server()

    created = await _call_tool(
        mcp,
        "control_create_task",
        {"title": "Run lifecycle", "data_dir": str(tmp_path)},
    )
    claimed = await _call_tool(
        mcp,
        "control_claim_task",
        {"task_id": created["task"]["id"], "data_dir": str(tmp_path)},
    )
    run_id = claimed["run"]["id"]
    expires_at = claimed["lease"]["expires_at"]

    listed = await _call_tool(
        mcp, "control_list_runs", {"status": "active", "data_dir": str(tmp_path)}
    )
    assert len(listed["runs"]) == 1
    assert listed["runs"][0]["id"] == run_id

    fetched = await _call_tool(
        mcp, "control_get_run", {"run_id": run_id, "data_dir": str(tmp_path)}
    )
    assert fetched["run"]["id"] == run_id
    assert fetched["lease"]["run_id"] == run_id

    heartbeated = await _call_tool(
        mcp,
        "control_heartbeat_run",
        {"run_id": run_id, "lease_ttl_seconds": 240.0, "data_dir": str(tmp_path)},
    )
    assert heartbeated["lease"]["expires_at"] != expires_at

    completed = await _call_tool(
        mcp,
        "control_complete_run",
        {"run_id": run_id, "summary": "done", "data_dir": str(tmp_path)},
    )
    assert completed["run"]["status"] == "completed"
    assert completed["run"]["summary"] == "done"

    created_again = await _call_tool(
        mcp,
        "control_create_task",
        {"title": "Release lifecycle", "data_dir": str(tmp_path)},
    )
    claimed_again = await _call_tool(
        mcp,
        "control_claim_task",
        {"task_id": created_again["task"]["id"], "data_dir": str(tmp_path)},
    )
    released = await _call_tool(
        mcp,
        "control_release_run",
        {
            "run_id": claimed_again["run"]["id"],
            "reason": "handoff",
            "data_dir": str(tmp_path),
        },
    )
    assert released["run"]["status"] == "released"
    assert released["run"]["summary"] == "handoff"

    pending_tasks = await _call_tool(
        mcp,
        "control_list_tasks",
        {"status": "pending", "data_dir": str(tmp_path)},
    )
    assert any(task["id"] == created_again["task"]["id"] for task in pending_tasks["tasks"])


@pytest.mark.asyncio
async def test_control_complete_run_is_blocked_until_required_gates_resolve(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Return a structured error when required gates are unresolved."""
    _set_agent_identity(monkeypatch, agent_id="agent-test")
    mcp = create_server()

    created = await _call_tool(
        mcp,
        "control_create_task",
        {
            "title": "Blocked completion",
            "gates": [
                {
                    "id": "review",
                    "gate_type": "review",
                    "label": "Code review",
                    "required": True,
                },
                {
                    "id": "optional-policy",
                    "gate_type": "policy",
                    "label": "Optional policy",
                    "required": False,
                },
            ],
            "data_dir": str(tmp_path),
        },
    )
    claimed = await _call_tool(
        mcp,
        "control_claim_task",
        {"task_id": created["task"]["id"], "data_dir": str(tmp_path)},
    )

    blocked = await _call_tool(
        mcp,
        "control_complete_run",
        {"run_id": claimed["run"]["id"], "summary": "done", "data_dir": str(tmp_path)},
    )
    assert blocked["error_type"] == "TaskGateError"

    decided = await _call_tool(
        mcp,
        "control_decide_gate",
        {
            "task_id": created["task"]["id"],
            "gate_id": "review",
            "status": GateStatus.APPROVED.value,
            "data_dir": str(tmp_path),
        },
    )
    assert decided["task"]["gates"][0]["status"] == GateStatus.APPROVED.value

    completed = await _call_tool(
        mcp,
        "control_complete_run",
        {"run_id": claimed["run"]["id"], "summary": "done", "data_dir": str(tmp_path)},
    )
    assert completed["run"]["status"] == "completed"


@pytest.mark.asyncio
async def test_control_plane_tools_return_structured_errors(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Return explicit error payloads for invalid control-plane operations."""
    _set_agent_identity(monkeypatch, agent_id="agent-one")
    mcp = create_server()

    missing_task = await _call_tool(
        mcp,
        "control_get_task",
        {"task_id": "task_missing", "data_dir": str(tmp_path)},
    )
    assert missing_task["error_type"] == "TaskNotFoundError"

    created = await _call_tool(
        mcp,
        "control_create_task",
        {"title": "Claim conflict", "data_dir": str(tmp_path)},
    )
    first_claim = await _call_tool(
        mcp,
        "control_claim_task",
        {"task_id": created["task"]["id"], "data_dir": str(tmp_path)},
    )
    assert first_claim["run"]["status"] == "active"

    _set_agent_identity(monkeypatch, agent_id="agent-two")
    conflict = await _call_tool(
        mcp,
        "control_claim_task",
        {"task_id": created["task"]["id"], "data_dir": str(tmp_path)},
    )
    assert conflict["error_type"] == "TaskClaimError"

    bad_ttl = await _call_tool(
        mcp,
        "control_claim_task",
        {
            "task_id": created["task"]["id"],
            "lease_ttl_seconds": 0.0,
            "data_dir": str(tmp_path),
        },
    )
    assert bad_ttl["error_type"] == "TaskClaimError"

    missing_run = await _call_tool(
        mcp,
        "control_heartbeat_run",
        {"run_id": "run_missing", "data_dir": str(tmp_path)},
    )
    assert missing_run["error_type"] == "RunNotFoundError"

    monkeypatch.delenv("TTA_AGENT_TOOL", raising=False)


@pytest.mark.asyncio
async def test_control_list_ownership_returns_active_records(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """List active ownership with nested task/run/lease/session/project/telemetry fields."""
    _set_agent_identity(monkeypatch, agent_id="agent-test")
    session_manager = SessionManager(tmp_path)
    session = session_manager.start_session()
    mcp = create_server()

    created = await _call_tool(
        mcp,
        "control_create_task",
        {
            "title": "Ownership-visible task",
            "project_name": "alpha",
            "data_dir": str(tmp_path),
        },
    )
    claimed = await _call_tool(
        mcp,
        "control_claim_task",
        {"task_id": created["task"]["id"], "data_dir": str(tmp_path)},
    )

    listed = await _call_tool(mcp, "control_list_ownership", {"data_dir": str(tmp_path)})

    assert len(listed["active"]) == 1
    record = listed["active"][0]
    assert set(record) == {"task", "run", "lease", "session", "project", "telemetry"}
    assert record["task"]["id"] == created["task"]["id"]
    assert record["run"]["id"] == claimed["run"]["id"]
    assert record["lease"]["run_id"] == claimed["run"]["id"]
    assert record["session"]["id"] == session.id
    assert record["project"]["id"] == created["task"]["project_id"]
    assert record["telemetry"] == {
        "has_recent_activity": False,
        "recent_span_count": 0,
        "recent_action_types": [],
        "recent_agent_roles": [],
        "recent_primitive_types": [],
    }


@pytest.mark.asyncio
async def test_control_list_ownership_preserves_unlinked_session_and_telemetry(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Preserve explicit None values when an active run has no linked session."""
    _set_agent_identity(monkeypatch, agent_id="agent-test")
    mcp = create_server()

    created = await _call_tool(
        mcp,
        "control_create_task",
        {"title": "Unlinked ownership", "data_dir": str(tmp_path)},
    )
    claimed = await _call_tool(
        mcp,
        "control_claim_task",
        {"task_id": created["task"]["id"], "data_dir": str(tmp_path)},
    )

    listed = await _call_tool(mcp, "control_list_ownership", {"data_dir": str(tmp_path)})

    assert len(listed["active"]) == 1
    record = listed["active"][0]
    assert record["task"]["id"] == created["task"]["id"]
    assert record["run"]["id"] == claimed["run"]["id"]
    assert record["session"] is None
    assert record["telemetry"] is None


@pytest.mark.asyncio
async def test_control_list_project_ownership_filters_and_returns_envelope(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Filter ownership by project and include the project_id envelope field."""
    _set_agent_identity(monkeypatch, agent_id="agent-test")
    SessionManager(tmp_path).start_session()
    mcp = create_server()

    alpha = await _call_tool(
        mcp,
        "control_create_task",
        {
            "title": "Alpha ownership task",
            "project_name": "alpha",
            "data_dir": str(tmp_path),
        },
    )
    await _call_tool(
        mcp,
        "control_claim_task",
        {"task_id": alpha["task"]["id"], "data_dir": str(tmp_path)},
    )

    beta = await _call_tool(
        mcp,
        "control_create_task",
        {
            "title": "Beta ownership task",
            "project_name": "beta",
            "data_dir": str(tmp_path),
        },
    )
    await _call_tool(
        mcp,
        "control_claim_task",
        {"task_id": beta["task"]["id"], "data_dir": str(tmp_path)},
    )

    listed = await _call_tool(
        mcp,
        "control_list_project_ownership",
        {"project_id": alpha["task"]["project_id"], "data_dir": str(tmp_path)},
    )

    assert listed["project_id"] == alpha["task"]["project_id"]
    assert len(listed["active"]) == 1
    assert listed["active"][0]["task"]["id"] == alpha["task"]["id"]
    assert listed["active"][0]["project"]["id"] == alpha["task"]["project_id"]


@pytest.mark.asyncio
async def test_control_list_session_ownership_filters_and_returns_envelope(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Filter ownership by session and include the session_id envelope field."""
    _set_agent_identity(monkeypatch, agent_id="agent-test")
    session_manager = SessionManager(tmp_path)
    first_session = session_manager.start_session()
    mcp = create_server()

    first_task = await _call_tool(
        mcp,
        "control_create_task",
        {"title": "First session task", "data_dir": str(tmp_path)},
    )
    first_claim = await _call_tool(
        mcp,
        "control_claim_task",
        {"task_id": first_task["task"]["id"], "data_dir": str(tmp_path)},
    )

    session_manager.end_session_by_id(first_session.id)
    session_manager.start_session()

    second_task = await _call_tool(
        mcp,
        "control_create_task",
        {"title": "Second session task", "data_dir": str(tmp_path)},
    )
    await _call_tool(
        mcp,
        "control_claim_task",
        {"task_id": second_task["task"]["id"], "data_dir": str(tmp_path)},
    )

    listed = await _call_tool(
        mcp,
        "control_list_session_ownership",
        {"session_id": first_session.id, "data_dir": str(tmp_path)},
    )

    assert listed["session_id"] == first_session.id
    assert len(listed["active"]) == 1
    assert listed["active"][0]["run"]["id"] == first_claim["run"]["id"]
    assert listed["active"][0]["session"]["id"] == first_session.id


@pytest.mark.asyncio
async def test_control_ownership_tools_return_structured_errors_for_missing_scope_ids(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Return structured error payloads for unknown project and session IDs."""
    _set_agent_identity(monkeypatch, agent_id="agent-test")
    mcp = create_server()

    missing_project = await _call_tool(
        mcp,
        "control_list_project_ownership",
        {"project_id": "project-missing", "data_dir": str(tmp_path)},
    )
    assert missing_project["error_type"] == "ControlPlaneError"
    assert missing_project["error"] == "Project not found: project-missing"

    missing_session = await _call_tool(
        mcp,
        "control_list_session_ownership",
        {"session_id": "session-missing", "data_dir": str(tmp_path)},
    )
    assert missing_session["error_type"] == "ControlPlaneError"
    assert missing_session["error"] == "Session not found: session-missing"


@pytest.mark.asyncio
async def test_control_list_tasks_returns_pagination_metadata(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """list_tasks response includes total_count, has_more, and next_offset."""
    _set_agent_identity(monkeypatch, agent_id="agent-test")
    mcp = create_server()

    for i in range(3):
        await _call_tool(
            mcp,
            "control_create_task",
            {"title": f"Task {i}", "data_dir": str(tmp_path)},
        )

    # First page — 2 of 3
    page1 = await _call_tool(
        mcp,
        "control_list_tasks",
        {"limit": 2, "offset": 0, "data_dir": str(tmp_path)},
    )
    assert len(page1["tasks"]) == 2
    assert page1["total_count"] == 3
    assert page1["has_more"] is True
    assert page1["next_offset"] == 2

    # Second page — 1 of 3
    page2 = await _call_tool(
        mcp,
        "control_list_tasks",
        {"limit": 2, "offset": 2, "data_dir": str(tmp_path)},
    )
    assert len(page2["tasks"]) == 1
    assert page2["total_count"] == 3
    assert page2["has_more"] is False
    assert page2["next_offset"] is None


@pytest.mark.asyncio
async def test_control_list_runs_returns_pagination_metadata(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """list_runs response includes total_count and has_more."""
    _set_agent_identity(monkeypatch, agent_id="agent-test")
    mcp = create_server()

    created = await _call_tool(
        mcp,
        "control_create_task",
        {"title": "Run list test", "data_dir": str(tmp_path)},
    )
    await _call_tool(
        mcp,
        "control_claim_task",
        {"task_id": created["task"]["id"], "data_dir": str(tmp_path)},
    )

    listed = await _call_tool(
        mcp,
        "control_list_runs",
        {"status": "active", "limit": 10, "offset": 0, "data_dir": str(tmp_path)},
    )
    assert "total_count" in listed
    assert "has_more" in listed
    assert listed["total_count"] >= 1
    assert listed["has_more"] is False


@pytest.mark.asyncio
async def test_control_list_tools_carry_read_only_annotation() -> None:
    """Read-only list tools expose readOnlyHint=True in their MCP annotations."""
    mcp = create_server()
    tools_result = mcp.list_tools()
    if asyncio.iscoroutine(tools_result):
        tools_result = await tools_result
    tool_map = {t.name: t for t in tools_result}

    read_only_tools = [
        "control_list_tasks",
        "control_list_runs",
        "control_list_locks",
        "control_list_ownership",
        "control_get_task",
        "control_get_run",
    ]
    for name in read_only_tools:
        ann = tool_map[name].annotations
        assert ann is not None, f"{name} has no annotations"
        assert ann.readOnlyHint is True, f"{name} should have readOnlyHint=True"


@pytest.mark.asyncio
async def test_control_mutating_tools_carry_non_destructive_annotation() -> None:
    """Mutating control-plane tools declare destructiveHint=False."""
    mcp = create_server()
    tools_result = mcp.list_tools()
    if asyncio.iscoroutine(tools_result):
        tools_result = await tools_result
    tool_map = {t.name: t for t in tools_result}

    mutating_tools = [
        "control_create_task",
        "control_claim_task",
        "control_decide_gate",
        "control_complete_run",
        "control_release_run",
    ]
    for name in mutating_tools:
        ann = tool_map[name].annotations
        assert ann is not None, f"{name} has no annotations"
        assert ann.destructiveHint is False, f"{name} should have destructiveHint=False"
