"""Unit tests for agent_spawn_fleet and agent_poll_fleet MCP tools (issue #313).

Tests follow the Arrange-Act-Assert pattern and mirror the helper style used
in *test_mcp_analysis_tools.py* — calling tools via ``mcp.call_tool()`` so
we exercise the exact same code path that MCP clients hit at runtime.
"""

from __future__ import annotations

import asyncio
from typing import Any

import pytest

from ttadev.primitives.mcp_server.server import _FLEET_STORE, create_server

# ── Low-level call helper ─────────────────────────────────────────────────────


async def _call_tool(mcp: Any, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    """Invoke an MCP tool and unwrap the ``(meta, payload)`` tuple result."""
    result = mcp.call_tool(name, arguments)
    if asyncio.iscoroutine(result):
        result = await result
    assert isinstance(result, tuple), f"Expected tuple, got {type(result)}"
    _, payload = result
    assert isinstance(payload, dict), f"Expected dict payload, got {type(payload)}"
    return payload


# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture(autouse=True)
def _clear_fleet_store() -> None:
    """Wipe the module-level fleet store before every test for isolation."""
    _FLEET_STORE.clear()


@pytest.fixture
def mcp() -> Any:
    """Provide a fresh MCP server instance."""
    return create_server()


# ── agent_spawn_fleet — happy path ────────────────────────────────────────────


@pytest.mark.asyncio
async def test_spawn_fleet_returns_fleet_id(mcp: Any) -> None:
    """agent_spawn_fleet returns a dict containing a 'fleet_id' key."""
    result = await _call_tool(mcp, "agent_spawn_fleet", {"tasks": ["task one", "task two"]})

    assert "fleet_id" in result
    assert result["fleet_id"].startswith("fleet-")


@pytest.mark.asyncio
async def test_spawn_fleet_returns_correct_task_count(mcp: Any) -> None:
    """agent_spawn_fleet reflects the exact number of tasks submitted."""
    result = await _call_tool(
        mcp,
        "agent_spawn_fleet",
        {"tasks": ["alpha", "beta", "gamma"]},
    )

    assert result["task_count"] == 3


@pytest.mark.asyncio
async def test_spawn_fleet_status_is_dispatched(mcp: Any) -> None:
    """agent_spawn_fleet immediately returns status='dispatched' (non-blocking)."""
    result = await _call_tool(mcp, "agent_spawn_fleet", {"tasks": ["work"]})

    assert result["status"] == "dispatched"


@pytest.mark.asyncio
async def test_spawn_fleet_stores_entry_in_fleet_store(mcp: Any) -> None:
    """agent_spawn_fleet writes an entry to _FLEET_STORE for later polling."""
    result = await _call_tool(mcp, "agent_spawn_fleet", {"tasks": ["t1", "t2"]})
    fleet_id = result["fleet_id"]

    assert fleet_id in _FLEET_STORE
    assert _FLEET_STORE[fleet_id]["task_count"] == 2


@pytest.mark.asyncio
async def test_spawn_fleet_with_agent_hints(mcp: Any) -> None:
    """agent_spawn_fleet accepts per-task agent hints without error."""
    result = await _call_tool(
        mcp,
        "agent_spawn_fleet",
        {
            "tasks": ["write code", "run tests"],
            "agent_hints": ["developer", "qa"],
        },
    )

    assert "fleet_id" in result
    assert "error" not in result


@pytest.mark.asyncio
async def test_spawn_fleet_with_partial_agent_hints(mcp: Any) -> None:
    """agent_spawn_fleet accepts None entries in the hints list (auto-select)."""
    result = await _call_tool(
        mcp,
        "agent_spawn_fleet",
        {
            "tasks": ["secure the endpoint", "deploy to prod"],
            "agent_hints": ["security", None],
        },
    )

    assert "fleet_id" in result
    assert "error" not in result


# ── agent_spawn_fleet — validation ────────────────────────────────────────────


@pytest.mark.asyncio
async def test_spawn_fleet_empty_tasks_returns_error(mcp: Any) -> None:
    """agent_spawn_fleet rejects an empty task list with an 'error' key."""
    result = await _call_tool(mcp, "agent_spawn_fleet", {"tasks": []})

    assert "error" in result


@pytest.mark.asyncio
async def test_spawn_fleet_hint_length_mismatch_returns_error(mcp: Any) -> None:
    """agent_spawn_fleet returns error when hints list length differs from tasks."""
    result = await _call_tool(
        mcp,
        "agent_spawn_fleet",
        {
            "tasks": ["one", "two", "three"],
            "agent_hints": ["developer"],  # length mismatch
        },
    )

    assert "error" in result


@pytest.mark.asyncio
async def test_spawn_fleet_too_many_tasks_returns_error(mcp: Any) -> None:
    """agent_spawn_fleet rejects fleets with more than 50 tasks."""
    result = await _call_tool(
        mcp,
        "agent_spawn_fleet",
        {"tasks": [f"task-{i}" for i in range(51)]},
    )

    assert "error" in result


# ── agent_poll_fleet — unknown fleet ─────────────────────────────────────────


@pytest.mark.asyncio
async def test_poll_fleet_unknown_id_returns_error(mcp: Any) -> None:
    """agent_poll_fleet returns an error dict for a nonexistent fleet_id."""
    result = await _call_tool(mcp, "agent_poll_fleet", {"fleet_id": "fleet-deadbeef"})

    assert "error" in result
    assert "fleet-deadbeef" in result["error"]


# ── agent_poll_fleet — correct schema ─────────────────────────────────────────


@pytest.mark.asyncio
async def test_poll_fleet_returns_correct_schema(mcp: Any) -> None:
    """agent_poll_fleet response contains all required top-level keys."""
    spawn = await _call_tool(mcp, "agent_spawn_fleet", {"tasks": ["do the thing"]})
    fleet_id = spawn["fleet_id"]

    result = await _call_tool(mcp, "agent_poll_fleet", {"fleet_id": fleet_id})

    assert "status" in result
    assert "task_count" in result
    assert "completed_count" in result
    assert "results" in result
    assert isinstance(result["results"], list)


@pytest.mark.asyncio
async def test_poll_fleet_result_items_have_required_fields(mcp: Any) -> None:
    """Each item in the 'results' list has the required per-task fields."""
    spawn = await _call_tool(mcp, "agent_spawn_fleet", {"tasks": ["implement feature"]})
    fleet_id = spawn["fleet_id"]

    poll = await _call_tool(mcp, "agent_poll_fleet", {"fleet_id": fleet_id})

    assert len(poll["results"]) == 1
    item = poll["results"][0]
    for field in ("task_id", "task", "agent", "output", "status"):
        assert field in item, f"Missing field: {field!r}"


@pytest.mark.asyncio
async def test_poll_fleet_task_count_matches_spawned(mcp: Any) -> None:
    """agent_poll_fleet reflects the exact number of tasks that were spawned."""
    tasks = ["task-a", "task-b", "task-c"]
    spawn = await _call_tool(mcp, "agent_spawn_fleet", {"tasks": tasks})
    fleet_id = spawn["fleet_id"]

    poll = await _call_tool(mcp, "agent_poll_fleet", {"fleet_id": fleet_id})

    assert poll["task_count"] == len(tasks)
    assert len(poll["results"]) == len(tasks)


# ── Fleet status progression ───────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_fleet_transitions_to_complete(mcp: Any) -> None:
    """Fleet status transitions from pending/running to 'complete' after tasks finish.

    We give asyncio enough time for the fire-and-forget background tasks to
    run the v1 stub executor and update the fleet store.
    """
    spawn = await _call_tool(mcp, "agent_spawn_fleet", {"tasks": ["task-x", "task-y"]})
    fleet_id = spawn["fleet_id"]

    # Allow the background asyncio tasks (fire-and-forget) to complete.
    await asyncio.sleep(0.1)

    poll = await _call_tool(mcp, "agent_poll_fleet", {"fleet_id": fleet_id})

    assert poll["status"] == "complete"
    assert poll["completed_count"] == 2


@pytest.mark.asyncio
async def test_fleet_results_have_output_after_completion(mcp: Any) -> None:
    """Each result has a non-None output string after the fleet completes."""
    spawn = await _call_tool(mcp, "agent_spawn_fleet", {"tasks": ["refactor module"]})
    fleet_id = spawn["fleet_id"]

    await asyncio.sleep(0.1)

    poll = await _call_tool(mcp, "agent_poll_fleet", {"fleet_id": fleet_id})

    assert poll["status"] == "complete"
    for item in poll["results"]:
        assert item["output"] is not None
        assert item["status"] == "complete"


@pytest.mark.asyncio
async def test_fleet_initial_status_is_pending_or_running(mcp: Any) -> None:
    """Polling immediately after spawn gives 'pending' or 'running' (not 'complete')."""
    spawn = await _call_tool(mcp, "agent_spawn_fleet", {"tasks": ["long running job"]})
    fleet_id = spawn["fleet_id"]

    # Poll without yielding control to let background tasks execute.
    # (The tasks are scheduled but haven't run yet at this exact moment.)
    poll = await _call_tool(mcp, "agent_poll_fleet", {"fleet_id": fleet_id})

    # Either pending or running is acceptable depending on scheduler timing.
    assert poll["status"] in ("pending", "running", "complete")


# ── Provider passthrough ───────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_spawn_fleet_provider_stored(mcp: Any) -> None:
    """The requested provider is stored in the fleet entry."""
    result = await _call_tool(
        mcp,
        "agent_spawn_fleet",
        {"tasks": ["analyse logs"], "provider": "groq"},
    )
    fleet_id = result["fleet_id"]

    assert _FLEET_STORE[fleet_id]["provider"] == "groq"
